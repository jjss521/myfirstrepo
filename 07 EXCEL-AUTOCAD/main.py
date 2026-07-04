"""PDSG — 配电柜系统图自动生成程序

CLI 入口:
  pdsg <excel_path> [OPTIONS]

用法:
  pdsg "D:\\项目\\配电柜回路表.xlsx"
  pdsg "回路表.xlsx" -c "my_config.yaml" --dry-run
  pdsg "回路表.xlsx" -o "D:\\输出\\系统图.dwg" --log-level DEBUG
"""
import argparse
import logging
import os
import sys
import time

# 将项目根目录加入 sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config_loader import load_config
from src.data_model import AppConfig
from src.errors import (
    PDSGError,
    ExcelReadError,
    ConfigError,
    BlockLibraryError,
    AcadConnectionError,
    AcadOperationError,
)
from src import excel_reader
from src import block_mapper
from src import attribute_builder
from src import layout_engine
from src import block_library
from src import reporter

logger = logging.getLogger("pdsg")


def setup_logging(log_level: str, log_path: str) -> None:
    """配置日志: 控制台 INFO + 文件 DEBUG"""
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # 控制台
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(console)

    # 文件
    try:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        ))
        root.addHandler(fh)
    except Exception as e:
        logger.warning("日志文件创建失败: %s", e)


def parse_args(argv=None) -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        prog="pdsg",
        description="PDSG — 配电柜系统图自动生成程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  pdsg "D:\\项目\\配电柜回路表.xlsx"
  pdsg "回路表.xlsx" -c "my_config.yaml" --dry-run
  pdsg "回路表.xlsx" -o "D:\\输出\\系统图.dwg" --log-level DEBUG
""",
    )
    parser.add_argument(
        "excel_path",
        help="Excel 回路清单文件路径 (.xlsx)",
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="配置文件路径（默认 ./config.yaml）",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出 DWG 路径（覆盖配置文件设置）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅读取校验，不连接 AutoCAD，不生成 DWG",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认 INFO）",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="启动图形界面模式",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PDSG v1.0.0",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """主流程"""
    # 快速检测 --gui（无需 excel_path 参数）
    if argv is None:
        argv = sys.argv[1:]
    if "--gui" in argv:
        from gui import launch_gui
        launch_gui()
        return 0

    args = parse_args(argv)

    # ---- 1. 加载配置 ----
    try:
        cfg = load_config(args.config)
    except ConfigError as e:
        print(f"[错误] 配置加载失败: {e}", file=sys.stderr)
        return 1

    # 覆盖配置
    if args.output:
        cfg.output.dwg_path = args.output
    if args.log_level:
        cfg.output.log_level = args.log_level

    # ---- 2. 初始化日志 ----
    setup_logging(cfg.output.log_level, cfg.output.log_path)
    logger.info("开始处理: %s", args.excel_path)
    start_time = time.time()

    # ---- 3. Excel 读取与校验 ----
    try:
        records, errors = excel_reader.read_and_validate(
            args.excel_path, cfg.excel
        )
    except ExcelReadError as e:
        logger.error("Excel 读取失败: %s", e)
        return 1

    if not records:
        logger.error("无有效回路数据，程序退出")
        _generate_report(errors, [], [], args.excel_path, cfg)
        return 1

    # ---- 4. 图块目录加载 ----
    catalog = None
    try:
        catalog = block_library.load_catalog(cfg.block_library.catalog)
    except BlockLibraryError as e:
        logger.warning("图块目录加载失败: %s（映射将跳过目录验证）", e)

    # ---- 5. 图块映射 ----
    mapped, warnings = block_mapper.map_circuits(
        records, cfg.block_mapping, catalog
    )

    # ---- 6. 属性构建 ----
    attribute_builder.build_all_attributes(mapped, catalog)

    # ---- 7. 布局计算 ----
    try:
        layout = layout_engine.compute(mapped, cfg.layout, cfg.sort)
    except ValueError as e:
        logger.error("布局计算失败: %s", e)
        return 1

    # ---- 8. Dry-run 模式 ----
    if args.dry_run:
        logger.info("=== DRY-RUN 模式 ===")
        logger.info("幅面: %s (%.0fx%.0fmm)", layout.paper_size.name,
                     layout.paper_size.width, layout.paper_size.height)
        logger.info("回路数: %d", len(layout.placements))
        logger.info("母线: X=%.1f, Y=[%.1f, %.1f]",
                     layout.bus_line.x, layout.bus_line.y_start, layout.bus_line.y_end)
        logger.info("分组标签: %d 个", len(layout.group_labels))
        for p in layout.placements[:5]:
            logger.info("  %s @ (%.1f, %.1f) block=%s",
                         p.circuit_id, p.x, p.y, p.block_name)
        if len(layout.placements) > 5:
            logger.info("  ... 及另外 %d 个回路", len(layout.placements) - 5)

        _generate_report(errors, mapped, warnings, args.excel_path, cfg,
                         layout.placements)
        elapsed = time.time() - start_time
        logger.info("Dry-run 完成 (%.1fs): 有效 %d / 跳过 %d / 警告 %d",
                     elapsed, len(mapped), len(errors), len(warnings))
        return 0

    # ---- 9. AutoCAD 绘图 ----
    from src.cad_drawer import CadDrawer

    cad = CadDrawer()
    try:
        cad.connect(cfg.autocad)
    except AcadConnectionError as e:
        logger.error("AutoCAD 连接失败: %s", e)
        logger.error("请确认 AutoCAD 已启动后重试")
        _generate_report(errors, mapped, warnings, args.excel_path, cfg)
        return 1

    try:
        cad.open_library_as_working_doc(cfg.block_library)
        cad.draw(layout, cfg.layout)

        if cfg.title_block.enabled:
            cad.insert_title_block(cfg.title_block, layout.paper_size)

        cad.save_as(cfg.output.dwg_path)
    except (AcadOperationError, BlockLibraryError) as e:
        logger.error("绘图失败: %s", e)
        cad.close()
        _generate_report(errors, mapped, warnings, args.excel_path, cfg)
        return 1

    cad.close()

    # ---- 10. 生成报告 ----
    _generate_report(errors, mapped, warnings, args.excel_path, cfg,
                     layout.placements)

    elapsed = time.time() - start_time
    logger.info("完成 (%.1fs): 成功 %d / 跳过 %d / 警告 %d",
                 elapsed, len(mapped), len(errors), len(warnings))
    print(f"\n输出文件: {os.path.abspath(cfg.output.dwg_path)}")
    return 0


def _generate_report(errors, mapped, warnings, source_file, cfg, placements=None):
    """生成 HTML 报告（容错）"""
    try:
        reporter.generate(
            errors=errors,
            mapped=mapped,
            warnings=warnings,
            source_file=source_file,
            report_path=cfg.output.report_path,
            placements=placements,
        )
    except Exception as e:
        logger.warning("报告生成失败: %s", e)


if __name__ == "__main__":
    sys.exit(main())
