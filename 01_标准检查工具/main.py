"""
工程建设标准有效性检查工具 - 主入口

功能：
1. 从文本输入中批量解析标准编号和名称
2. 自动查询 csres.com 验证标准有效性
3. 对过期标准标注替代信息
4. 输出 TXT 检查报告

用法：
    python main.py --gui                                 # 启动图形界面
    python main.py --text "GB 50016-2014 建筑设计防火规范"    # 直接输入标准文本
    python main.py --text-file standards.txt              # 从文本文件读取标准列表
    python main.py --text "..." --skip-web                # 仅解析不查网
    python main.py --text "..." --debug                   # 调试模式
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from config import (
    DEFAULT_OUTPUT_DIR,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
)
from models import StandardRef, ValidatedStandard
from report_generator import generate_report, save_report
from utils import setup_logging
from web_scraper import validate_standards

logger: logging.Logger | None = None  # 在 main() 中初始化

CACHE_FILE = "standards_cache.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="工程建设标准有效性检查工具 - 文本输入并查询标准状态"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"报告输出路径 (默认: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=REQUEST_DELAY_MIN,
        help=f"最小请求间隔秒数 (默认: {REQUEST_DELAY_MIN})",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=REQUEST_DELAY_MAX,
        help=f"最大请求间隔秒数 (默认: {REQUEST_DELAY_MAX})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试日志",
    )
    parser.add_argument(
        "--skip-web",
        action="store_true",
        help="仅运行解析，跳过网站查询",
    )
    parser.add_argument(
        "-t",
        "--text",
        type=str,
        default=None,
        help="直接输入标准文本（每行一条：编号 名称）",
    )
    parser.add_argument(
        "--text-file",
        type=str,
        default=None,
        help="从文本文件读取标准列表（每行一条）",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="启动图形界面 (GUI) 模式",
    )
    return parser.parse_args()


def save_cache(standards: list[StandardRef], output_dir: str) -> str:
    """将提取的标准保存为JSON缓存"""
    cache_path = os.path.join(output_dir, CACHE_FILE)
    data = []
    for ref in standards:
        data.append(
            {
                "number": ref.number,
                "name": ref.name,
                "source_files": ref.source_files,
                "confidence": ref.confidence,
                "raw_text": ref.raw_text,
            }
        )
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"标准缓存已保存: {cache_path} ({len(data)} 条)")
    return cache_path


def run_web_phase(
    standards: list[StandardRef], delay_min: float, delay_max: float
) -> list[ValidatedStandard]:
    """网站查询阶段：逐条查询标准有效性"""
    logger.info(f"开始查询 {len(standards)} 条标准的有效性...")
    return validate_standards(standards, delay_min, delay_max)


def main() -> None:
    global logger
    args = parse_args()

    # GUI 模式
    if args.gui:
        from gui_app import launch

        launch()
        return

    # 需要文本输入
    if not args.text and not args.text_file:
        print("请提供标准列表输入方式:")
        print("  --gui               启动图形界面")
        print('  --text "..."         直接输入标准文本')
        print("  --text-file file.txt 从文件读取")
        sys.exit(0)

    # 初始化日志
    logger = setup_logging(args.output, args.debug)

    logger.info("=" * 50)
    logger.info("工程建设标准有效性检查工具")
    logger.info("=" * 50)

    # 读取文本
    text = ""
    source_name = "文本输入"
    if args.text_file:
        if not os.path.isfile(args.text_file):
            logger.error(f"文本文件不存在: {args.text_file}")
            sys.exit(1)
        with open(args.text_file, encoding="utf-8") as f:
            text = f.read()
        source_name = os.path.basename(args.text_file)
        logger.info(f"从文件读取标准列表: {args.text_file}")
    elif args.text:
        text = args.text.replace("\\n", "\n")
        logger.info("直接文本输入模式")

    from standard_parser import parse_standards_from_text

    standards = parse_standards_from_text(text, source=source_name)
    total_count = len(standards)

    if not standards:
        logger.error("未能从文本中解析出任何标准编号")
        logger.error("请确保每行至少包含一个标准编号，如: GB 50016-2014 建筑设计防火规范")
        sys.exit(1)

    # 保存缓存
    save_cache(standards, args.output)

    # 网站查询
    if args.skip_web:
        logger.info("已跳过网站查询 (--skip-web)")
        validated = []
        for ref in standards:
            validated.append(ValidatedStandard(standard_ref=ref))
    else:
        validated = run_web_phase(standards, args.delay_min, args.delay_max)

    # 生成报告
    source_filenames = [source_name]
    report = generate_report(validated, source_filenames, total_count)
    report_path = save_report(report, args.output)

    # 统计
    logger.info("=" * 50)
    logger.info("处理完成！")
    logger.info(f"报告文件: {report_path}")
    expired = sum(
        1 for v in validated if v.search_result and v.search_result.status.value in ("作废", "废止")
    )
    active = sum(1 for v in validated if v.search_result and v.search_result.status.value == "现行")
    unknown = sum(
        1 for v in validated if v.search_result is None or v.search_result.status.value == "未知"
    )
    logger.info(f"  现行有效: {active} 项")
    logger.info(f"  已过期:   {expired} 项")
    logger.info(f"  未确认:   {unknown} 项")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
