"""标准编号/名称正则提取 + OCR纠错 + 去重"""

from __future__ import annotations

import dataclasses
import logging
import re

from config import (
    DIGIT_CORRECTIONS,
    STANDARD_NAME_PATTERN,
    STANDARD_NUMBER_PATTERN,
)
from models import MergedTextLine, StandardRef

logger = logging.getLogger("standard_checker")


def fix_ocr_digits(text: str) -> str:
    """
    修正OCR在标准编号数字区域的常见误识别。

    策略：找到前缀字母后面的数字区域，在该区域内做字母→数字替换。
    例: "GB 5OOl6-2014" → "GB 50016-2014"
    """

    # 匹配前缀后的数字区域
    def _fix_digit_zone(match):
        prefix = match.group(1)  # 如 "GB/T "
        digits = match.group(2)  # 如 "5OOl6"
        fixed = ""
        for ch in digits:
            if ch in DIGIT_CORRECTIONS:
                fixed += DIGIT_CORRECTIONS[ch]
            else:
                fixed += ch
        return prefix + fixed

    # 匹配：前缀字母 + 空格 + 混合字母数字的区域
    pattern = re.compile(r"([A-Z]{1,4}(?:/[A-Z])?\s+)([0-9A-Za-z]+)(?=\s*[-—－]\s*\d{4})")
    return pattern.sub(_fix_digit_zone, text)


def normalize_standard_number(raw: str) -> str:
    """
    规范化标准编号：统一空格和连字符格式。

    例: "GB/T50352—2019" → "GB/T 50352-2019"
         "JGJ／T 3—2010" → "JGJ/T 3-2010"
    """
    # 替换各种连字符为 ASCII 连字符
    normalized = raw.replace("—", "-").replace("－", "-").replace("–", "-")

    # 替换全角斜杠
    normalized = normalized.replace("／", "/")

    # 确保前缀和数字之间有且仅有一个空格
    normalized = re.sub(
        r"([A-Z]{1,4}(?:/[A-Z])?)\s*(\d)",
        r"\1 \2",
        normalized,
    )

    # 压缩多余空格
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def extract_standard_name_after(text: str, match_end: int) -> str:
    """从标准编号匹配结束位置之后提取标准名称"""
    remaining = text[match_end:]
    m = STANDARD_NAME_PATTERN.match(remaining)
    if m:
        return m.group(1).strip()
    return ""


def extract_standards(lines: list[MergedTextLine], source_file: str) -> list[StandardRef]:
    """
    从合并后的文本行中提取标准编号和名称。

    策略：
    1. 先做OCR数字纠错
    2. 用正则匹配标准编号
    3. 编号后紧跟的名称直接提取
    4. 若编号后无名称，尝试从下一行获取（跨行匹配）
    """
    refs: list[StandardRef] = []
    all_texts = [line.text for line in lines]

    for i, line in enumerate(lines):
        # 先做OCR纠错
        corrected = fix_ocr_digits(line.text)

        # 查找所有标准编号匹配
        for match in STANDARD_NUMBER_PATTERN.finditer(corrected):
            raw_number = match.group(1)
            number = normalize_standard_number(raw_number)

            # 提取标准名称
            name = extract_standard_name_after(corrected, match.end())

            # 跨行匹配：当前行没有名称时，看下一行
            if not name and i + 1 < len(all_texts):
                next_text = all_texts[i + 1].strip()
                # 下一行应以中文开头且不含标准编号
                if (
                    next_text
                    and re.match(r"[\u4e00-\u9fff]", next_text)
                    and not STANDARD_NUMBER_PATTERN.search(next_text)
                ):
                    # 取下一行的中文文本作为名称
                    name_match = re.match(
                        r"([\u4e00-\u9fff][\u4e00-\u9fff\w\s（）()、·/]{0,50}[\u4e00-\u9fff）)\w])",
                        next_text,
                    )
                    if name_match:
                        name = name_match.group(1).strip()

            # 清理名称末尾可能的多余字符
            name = re.sub(r"[。，；,;:\s]+$", "", name)

            refs.append(
                StandardRef(
                    number=number,
                    name=name,
                    source_files=[source_file],
                    confidence=line.confidence,
                    raw_text=line.text,
                )
            )
            logger.debug(f"提取: {number} | {name} | 来源: {source_file}")

    return refs


def deduplicate_standards(standards: list[StandardRef]) -> list[StandardRef]:
    """
    跨截图去重：按规范化编号去重，保留最高置信度的条目，
    合并所有来源文件。
    """
    seen: dict[str, StandardRef] = {}

    for ref in standards:
        # 去重键：小写前缀 + 编号 + 年份
        key = ref.number.lower().replace(" ", "")

        if key not in seen:
            seen[key] = ref
        else:
            existing = seen[key]
            # 合并来源文件（不修改现有 frozen 对象）
            merged_files = existing.source_files + [
                f for f in ref.source_files if f not in existing.source_files
            ]
            # 保留更高置信度，创建新的 frozen 实例替换旧的
            seen[key] = dataclasses.replace(
                existing,
                source_files=merged_files,
                confidence=max(existing.confidence, ref.confidence),
                raw_text=ref.raw_text
                if ref.confidence > existing.confidence
                else existing.raw_text,
                name=ref.name if not existing.name and ref.name else existing.name,
            )

    result = list(seen.values())
    logger.info(f"去重: {len(standards)} → {len(result)} 条标准")
    return result


def split_standard_entries(text: str) -> list[str]:
    """按换行、分号、多空格灵活分割标准条目

    支持的分隔方式：
    - 换行符（\\n, \\r\\n）
    - 中英文分号（; 或 ；）
    - 连续2个以上空格
    - 逗号+空格（, 或 ，）
    """
    # 用正则分割：换行 | 中英文分号 | 2+空格 | 逗号+空格
    parts = re.split(r"[\n\r]+|[;；]\s*|\s{2,}|[,，]\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def parse_standards_from_text(
    text: str,
    source: str = "文本输入",
) -> list[StandardRef]:
    """
    从纯文本中解析标准引用，支持灵活的输入格式。

    用法示例：
        GB 50016-2014 建筑设计防火规范
        JGJ/T 3-2010 高层建筑混凝土结构技术规程
        GB 50016-2014, GB 50222-2017  （逗号分隔多条）
        GB/T 50352-2019（仅编号）

    支持换行、分号、多空格等灵活分隔符自动识别。
    支持书名号、冒号等常见分隔符自动清洗。
    """
    refs: list[StandardRef] = []
    seen_numbers: set = set()

    # 使用灵活分割替代简单的换行分割
    entries = split_standard_entries(text)

    for line in entries:
        line = line.strip()
        if not line:
            continue

        # 先做 OCR 数字纠错（文本粘贴可能也有输入错误）
        corrected = fix_ocr_digits(line)

        # 查找所有标准编号匹配
        for match in STANDARD_NUMBER_PATTERN.finditer(corrected):
            raw_number = match.group(1)
            number = normalize_standard_number(raw_number)

            # 去重
            key = number.lower().replace(" ", "")
            if key in seen_numbers:
                continue
            seen_numbers.add(key)

            # 提取标准名称（清洗前导分隔符）
            remaining = corrected[match.end() :]
            remaining = re.sub(r"^[\s：:：《》〈〉、，,。；;}\]]+", "", remaining)
            name = extract_standard_name_after(corrected, match.end())
            if not name and remaining:
                # 如果标准名称提取失败（有可能没有前导空格），
                # 尝试直接匹配中文文本
                name_m = re.match(
                    r"([\u4e00-\u9fff][\u4e00-\u9fff\w\s（）()、·/《》-]{0,80})",
                    remaining,
                )
                if name_m:
                    name = name_m.group(1).strip()

            refs.append(
                StandardRef(
                    number=number,
                    name=name or "",
                    source_files=[source],
                    confidence=1.0,  # 文本输入，置信度 100%
                    raw_text=line,
                )
            )
            logger.debug(f"文本解析: [{number}] {name or '(无名称)'}")

    logger.info(f"文本解析完成: {len(refs)} 条标准")
    return refs


def extract_standards_from_all_images(
    image_results: list[tuple[str, list[MergedTextLine]]],
) -> list[StandardRef]:
    """
    从所有图片的OCR结果中提取并去重标准。

    参数: image_results - [(source_file, merged_lines), ...]
    """
    all_refs = []
    for source_file, lines in image_results:
        refs = extract_standards(lines, source_file)
        all_refs.extend(refs)

    return deduplicate_standards(all_refs)
