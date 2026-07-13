"""TXT报告生成"""

from __future__ import annotations

import logging
import os
from datetime import datetime

from models import StandardStatus, ValidatedStandard

logger = logging.getLogger("standard_checker")


def generate_report(
    validated: list[ValidatedStandard],
    source_files: list[str],
    total_ocr_count: int,
) -> str:
    """
    生成TXT格式的检查报告。

    报告分三部分：
    1. 作废/废止标准及替代信息
    2. 现行有效标准
    3. 无法确认的标准
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 分类统计
    expired = []
    active = []
    upcoming = []
    unknown = []

    for v in validated:
        if v.search_result is None:
            unknown.append(v)
        elif v.search_result.status in (StandardStatus.ABOLISHED, StandardStatus.REPEALED):
            expired.append(v)
        elif v.search_result.status == StandardStatus.ACTIVE:
            active.append(v)
        elif v.search_result.status == StandardStatus.UPCOMING:
            upcoming.append(v)
        else:
            unknown.append(v)

    lines = []
    w = lines.append

    w("=" * 60)
    w("        工程建设标准有效性检查报告")
    w("=" * 60)
    w(f"生成时间: {now}")
    w(f"输入方式: 文本输入 (共 {len(source_files)} 个来源)")
    w(f"解析标准总数: {total_ocr_count} (去重后: {len(validated)})")
    w("")
    w("=" * 60)
    w("  摘要")
    w("=" * 60)
    w(f"  现行有效 (Active):    {len(active)} 项")
    w(f"  作废/废止 (Expired):  {len(expired)} 项")
    if upcoming:
        w(f"  即将实施 (Upcoming):  {len(upcoming)} 项")
    w(f"  无法确认 (Unknown):   {len(unknown)} 项")
    w("")

    # ===== 第一部分：过期标准 =====
    if expired:
        w("=" * 60)
        w("  一、作废/废止标准及替代信息 (Expired Standards)")
        w("=" * 60)
        w("")

        for idx, v in enumerate(expired, 1):
            ref = v.standard_ref
            sr = v.search_result
            rp = v.replacement_info

            w(f"  [{idx}] {ref.number} {ref.name}")
            w(f"      状态: [X] {sr.status.value}")
            w(f"      来源: {', '.join(ref.source_files)}")

            # 网站上的信息
            if sr.csres_name and sr.csres_name != ref.name:
                w(f"      网站名称: {sr.csres_name}")

            if rp:
                if rp.abolished_date:
                    w(f"      作废日期: {rp.abolished_date}")
                if rp.replacement_number:
                    w(f"      >>> 替代标准: {rp.replacement_number} {rp.replacement_name}")
                elif rp.replacement_notes:
                    w(f"      >>> 替代说明: {rp.replacement_notes}")
                else:
                    w("      >>> 替代情况: 未获取到明确替代信息")
            else:
                w("      >>> 替代信息: 未能获取（详情页访问失败）")

            w("")

    # ===== 第二部分：现行有效标准 =====
    if active:
        w("=" * 60)
        w("  二、现行有效标准 (Active Standards)")
        w("=" * 60)
        w("")

        for idx, v in enumerate(active, 1):
            ref = v.standard_ref
            sr = v.search_result

            w(f"  [{idx}] {ref.number} {ref.name}")
            w("      状态: [OK] 现行")
            w(f"      来源: {', '.join(ref.source_files)}")

            if sr.csres_name and sr.csres_name != ref.name:
                w(f"      网站名称: {sr.csres_name}")

            w("")

    # ===== 即将实施的标准 =====
    if upcoming:
        w("=" * 60)
        w("  三、即将实施的标准 (Upcoming)")
        w("=" * 60)
        w("")

        for idx, v in enumerate(upcoming, 1):
            ref = v.standard_ref
            sr = v.search_result

            w(f"  [{idx}] {ref.number} {ref.name}")
            w(f"      状态: [~] {sr.status.value}")
            w(f"      来源: {', '.join(ref.source_files)}")
            if sr.effective_date:
                w(f"      实施日期: {sr.effective_date}")
            w("")

    # ===== 无法确认的标准 =====
    if unknown:
        w("=" * 60)
        section_num = "四" if upcoming else "三"
        w(f"  {section_num}、无法确认的标准 (Unknown)")
        w("=" * 60)
        w("")

        for idx, v in enumerate(unknown, 1):
            ref = v.standard_ref

            w(f"  [{idx}] {ref.number} {ref.name}")
            w("      状态: [?] 未能确认")
            w(f"      来源: {', '.join(ref.source_files)}")
            w("      建议: 请手动查询确认")
            if ref.raw_text:
                w(f"      原始文本: {ref.raw_text}")
            w("")

    w("=" * 60)
    w("  报告结束")
    w("=" * 60)

    return "\n".join(lines)


def save_report(report_text: str, output_dir: str) -> str:
    """保存报告到TXT文件，返回文件路径"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"standard_check_report_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)

    # 使用 UTF-8 BOM 编码，确保 Windows 记事本正常显示中文
    with open(filepath, "w", encoding="utf-8-sig") as f:
        f.write(report_text)

    logger.info(f"报告已保存: {filepath}")
    return filepath
