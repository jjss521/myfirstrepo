"""csres.com 搜索和详情页抓取"""
import logging
import re
from typing import List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from config import (
    CSRES_BASE_URL, CSRES_SEARCH_URL, STATUS_TEXT_MAP,
    STANDARD_NUMBER_PATTERN,
)
from models import (
    StandardRef, StandardStatus, SearchResult,
    ReplacementInfo, ValidatedStandard,
)
from utils import RateLimiter, retry_request

logger = logging.getLogger("standard_checker")


def _parse_status(text: str, font_color: str = "") -> StandardStatus:
    """根据状态文本或字体颜色解析标准状态"""
    text = text.strip()
    if text in STATUS_TEXT_MAP:
        return StandardStatus[STATUS_TEXT_MAP[text]]
    # 颜色判断
    if font_color and font_color.upper() == "#FF0000":
        return StandardStatus.ABOLISHED
    return StandardStatus.UNKNOWN


def _match_score(query: str, candidate: str) -> float:
    """
    计算两个标准编号的匹配度（0~1）。
    规范化后做字符级比较。
    """
    def _norm(s):
        s = s.lower().replace(' ', '').replace('-', '').replace('—', '')
        return re.sub(r'[^a-z0-9/]', '', s)

    q = _norm(query)
    c = _norm(candidate)

    if q == c:
        return 1.0

    # 简单相似度：公共前缀长度 / 最大长度
    common = 0
    for a, b in zip(q, c):
        if a == b:
            common += 1
        else:
            break
    max_len = max(len(q), len(c))
    return common / max_len if max_len > 0 else 0.0


def parse_search_results(html: str, query_number: str) -> List[dict]:
    """
    解析csres.com搜索结果页面，提取所有标准条目。

    返回: [{"number", "name", "status", "font_color", "detail_url", "department", "date"}, ...]
    """
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table', class_='heng')
    if not table:
        logger.debug("未找到搜索结果表 (table.heng)")
        return []

    rows = table.find_all('tr')
    if len(rows) < 2:
        return []

    results = []
    for row in rows[1:]:  # 跳过表头
        tds = row.find_all('td')
        if len(tds) < 5:
            continue

        # 第1列：标准编号 + 详情链接
        td0 = tds[0]
        link = td0.find('a')
        detail_url = ""
        if link and link.get('href'):
            href = link['href']
            if href.startswith('/'):
                detail_url = CSRES_BASE_URL + href
            elif href.startswith('http'):
                detail_url = href

        number_text = td0.get_text(strip=True)
        font0 = td0.find('font')
        font_color = ""
        if font0 and font0.get('color'):
            font_color = font0['color']

        # 第2列：标准名称
        name_text = tds[1].get_text(strip=True)

        # 第3列：发布部门
        dept_text = tds[2].get_text(strip=True)

        # 第4列：实施日期
        date_text = tds[3].get_text(strip=True)

        # 第5列：状态
        status_text = tds[4].get_text(strip=True)

        results.append({
            "number": number_text,
            "name": name_text,
            "status_text": status_text,
            "font_color": font_color,
            "detail_url": detail_url,
            "department": dept_text,
            "date": date_text,
        })

    return results


def search_standard(
    standard_ref: StandardRef,
    session: requests.Session,
    rate_limiter: RateLimiter,
) -> Optional[SearchResult]:
    """
    在csres.com搜索单条标准，返回最佳匹配结果。
    """
    # 用标准编号作为搜索关键词
    keyword = standard_ref.number
    url = f"{CSRES_SEARCH_URL}?keyword={quote(keyword)}&pageNum=1"

    resp = retry_request(url, session, rate_limiter, logger=logger)
    if resp is None:
        logger.warning(f"搜索失败: {keyword}")
        return None

    # 尝试检测编码（中文JSP站点可能是 GBK 或 UTF-8）
    detected = resp.apparent_encoding or resp.encoding or 'utf-8'
    resp.encoding = detected
    html = resp.text

    # 如果解析出的内容乱码严重，回退到 GBK
    if '标准' not in html and '工标网' not in html:
        for fallback_enc in ('gbk', 'gb2312', 'utf-8'):
            try:
                resp.encoding = fallback_enc
                html = resp.text
                if '标准' in html or '工标网' in html:
                    break
            except Exception:
                continue

    candidates = parse_search_results(html, keyword)
    if not candidates:
        logger.warning(f"未找到搜索结果: {keyword}")
        return None

    # 找最佳匹配
    best = None
    best_score = 0
    for cand in candidates:
        score = _match_score(keyword, cand["number"])
        if score > best_score:
            best_score = score
            best = cand

    if best is None or best_score < 0.7:
        # 如果没有高匹配度，取第一条
        best = candidates[0]
        logger.debug(f"低匹配度 ({best_score:.2f})，使用第一条结果")

    status = _parse_status(best["status_text"], best["font_color"])

    return SearchResult(
        standard_ref=standard_ref,
        status=status,
        csres_number=best["number"],
        csres_name=best["name"],
        detail_url=best["detail_url"],
        department=best["department"],
        effective_date=best["date"],
    )


def fetch_replacement_info(
    detail_url: str,
    old_number: str,
    old_name: str,
    session: requests.Session,
    rate_limiter: RateLimiter,
) -> Optional[ReplacementInfo]:
    """
    访问标准详情页，提取替代信息。
    """
    if not detail_url:
        return None

    resp = retry_request(detail_url, session, rate_limiter, logger=logger)
    if resp is None:
        logger.warning(f"详情页获取失败: {detail_url}")
        return None

    # 编码检测（同 search_standard）
    detected = resp.apparent_encoding or resp.encoding or 'utf-8'
    resp.encoding = detected
    html = resp.text
    if '标准' not in html and '工标网' not in html:
        for fallback_enc in ('gbk', 'gb2312', 'utf-8'):
            try:
                resp.encoding = fallback_enc
                html = resp.text
                if '标准' in html or '工标网' in html:
                    break
            except Exception:
                continue
    soup = BeautifulSoup(html, 'lxml')

    replacement_number = ""
    replacement_name = ""
    abolished_date = ""
    replacement_notes = ""

    # 策略1：查找包含 "替代情况" 的文本节点
    all_text = soup.get_text()

    # 提取替代情况
    replace_match = re.search(
        r'替代情况[：:]\s*(.+?)(?:\n|$)',
        all_text
    )
    if replace_match:
        replacement_notes = replace_match.group(1).strip()
        # 从替代说明中提取标准编号
        std_match = STANDARD_NUMBER_PATTERN.search(replacement_notes)
        if std_match:
            replacement_number = std_match.group(1)
            # 提取编号后的名称
            after = replacement_notes[std_match.end():]
            name_match = re.match(
                r'[\s ]*([\u4e00-\u9fff][\u4e00-\u9fff\w\s（）()、·/]{1,50})',
                after
            )
            if name_match:
                replacement_name = name_match.group(1).strip()

    # 提取作废日期 / 废止日期
    date_match = re.search(r'(?:作废|废止)日期[：:]\s*([\d\-/年.]+)', all_text)
    if date_match:
        abolished_date = date_match.group(1).strip()

    # 策略2：用BeautifulSoup查找table中的字段
    if not replacement_notes:
        for td in soup.find_all('td'):
            text = td.get_text(strip=True)
            if '替代情况' in text:
                next_td = td.find_next_sibling('td')
                if next_td:
                    replacement_notes = next_td.get_text(strip=True)
                    std_match = STANDARD_NUMBER_PATTERN.search(replacement_notes)
                    if std_match:
                        replacement_number = std_match.group(1)
                break

    if not abolished_date:
        for td in soup.find_all('td'):
            text = td.get_text(strip=True)
            if '作废日期' in text or '废止日期' in text:
                next_td = td.find_next_sibling('td')
                if next_td:
                    abolished_date = next_td.get_text(strip=True)
                break

    return ReplacementInfo(
        old_number=old_number,
        old_name=old_name,
        replacement_number=replacement_number,
        replacement_name=replacement_name,
        abolished_date=abolished_date,
        replacement_notes=replacement_notes,
    )


def validate_standards(
    standards: List[StandardRef],
    delay_min: float,
    delay_max: float,
) -> List[ValidatedStandard]:
    """
    批量验证标准有效性：搜索 + 过期标准获取替代信息。
    """
    session = requests.Session()
    rate_limiter = RateLimiter(delay_min, delay_max)
    results: List[ValidatedStandard] = []
    total = len(standards)

    for i, ref in enumerate(standards, 1):
        logger.info(f"[{i}/{total}] 查询: {ref.number} {ref.name}")

        # 搜索
        search_result = search_standard(ref, session, rate_limiter)

        replacement_info = None

        # 如果是过期标准，获取替代信息
        if search_result and search_result.status in (
            StandardStatus.ABOLISHED, StandardStatus.REPEALED
        ):
            logger.info(f"  → {search_result.status.value}，获取替代信息...")
            replacement_info = fetch_replacement_info(
                search_result.detail_url,
                ref.number,
                ref.name,
                session,
                rate_limiter,
            )

        results.append(ValidatedStandard(
            standard_ref=ref,
            search_result=search_result,
            replacement_info=replacement_info,
        ))

    return results
