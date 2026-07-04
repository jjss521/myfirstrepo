"""PDSG 配置加载器

从 YAML 文件加载配置并转换为 AppConfig 数据类。
支持默认值、校验、以及缺失字段的友好提示。
"""
import os
import logging
from typing import Any, Dict, List, Optional

import yaml

from .data_model import (
    AcadConfig,
    AppConfig,
    BlockLibraryConfig,
    BlockMappingConfig,
    BlockMappingRule,
    ExcelConfig,
    LayoutConfig,
    MarginsConfig,
    OutputConfig,
    PaperConfig,
    PaperSizeDef,
    SortConfig,
    TextStyleConfig,
    TitleBlockConfig,
)
from .errors import ConfigError

logger = logging.getLogger(__name__)


def load_config(path: str) -> AppConfig:
    """从 YAML 文件加载应用配置

    Args:
        path: 配置文件路径

    Returns:
        AppConfig 实例

    Raises:
        ConfigError: 配置文件不存在或解析失败
    """
    if not os.path.isfile(path):
        raise ConfigError(f"配置文件不存在: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"配置文件解析失败: {e}")

    if raw is None:
        raw = {}

    return _build_app_config(raw)


def _build_app_config(raw: Dict[str, Any]) -> AppConfig:
    """将原始 YAML 字典转换为 AppConfig"""

    cfg = AppConfig()

    # AutoCAD 连接
    acad_raw = raw.get("autocad", {})
    cfg.autocad = AcadConfig(
        progids=acad_raw.get("progids", cfg.autocad.progids),
        visible=acad_raw.get("visible", cfg.autocad.visible),
    )

    # 图块库
    lib_raw = raw.get("block_library", {})
    cfg.block_library = BlockLibraryConfig(
        path=lib_raw.get("path", cfg.block_library.path),
        catalog=lib_raw.get("catalog", cfg.block_library.catalog),
        title_block_path=lib_raw.get("title_block_path", cfg.block_library.title_block_path),
        default_block=lib_raw.get("default_block", cfg.block_library.default_block),
    )

    # Excel
    excel_raw = raw.get("excel", {})
    cfg.excel = ExcelConfig(
        sheet_name=excel_raw.get("sheet_name", cfg.excel.sheet_name),
        header_row=excel_raw.get("header_row", cfg.excel.header_row),
        data_start_row=excel_raw.get("data_start_row", cfg.excel.data_start_row),
        column_aliases=excel_raw.get("column_aliases", cfg.excel.column_aliases),
        min_match_ratio=excel_raw.get("min_match_ratio", cfg.excel.min_match_ratio),
        # v1.1 新增
        format_auto_detect=excel_raw.get("format_auto_detect", cfg.excel.format_auto_detect),
        transposed_column_aliases=excel_raw.get("transposed_column_aliases", cfg.excel.transposed_column_aliases),
        default_breaker_model=excel_raw.get("default_breaker_model", cfg.excel.default_breaker_model),
    )

    # 图块映射
    mapping_raw = raw.get("block_mapping", {})
    rules: List[BlockMappingRule] = []
    for rule_raw in mapping_raw.get("rules", []):
        match = rule_raw.get("match", {})
        block = rule_raw.get("block", "")
        if match and block:
            rules.append(BlockMappingRule(match=match, block=block))
    cfg.block_mapping = BlockMappingConfig(
        rules=rules,
        default_block=mapping_raw.get("default_block", cfg.block_library.default_block),
    )

    # 布局
    layout_raw = raw.get("layout", {})
    paper_raw = layout_raw.get("paper", {})
    sizes = []
    for s in paper_raw.get("sizes", []):
        sizes.append(PaperSizeDef(
            name=s.get("name", ""),
            width=float(s.get("width", 0)),
            height=float(s.get("height", 0)),
        ))
    if not sizes:
        sizes = cfg.layout.paper.sizes
    paper_cfg = PaperConfig(
        sizes=sizes,
        auto_select=paper_raw.get("auto_select", True),
    )
    margins_raw = layout_raw.get("margins", {})
    margins_cfg = MarginsConfig(
        left=float(margins_raw.get("left", 25)),
        right=float(margins_raw.get("right", 25)),
        top=float(margins_raw.get("top", 15)),
        bottom=float(margins_raw.get("bottom", 30)),
    )
    cfg.layout = LayoutConfig(
        paper=paper_cfg,
        bus_x=float(layout_raw.get("bus_x", 100)),
        bus_y=float(layout_raw.get("bus_y", 780)),
        block_offset_x=float(layout_raw.get("block_offset_x", 0)),
        vertical_spacing=float(layout_raw.get("vertical_spacing", 70)),
        vertical_spacing_auto=layout_raw.get("vertical_spacing_auto", True),
        horizontal_spacing=float(layout_raw.get("horizontal_spacing", 2140.5407)),
        table_enabled=layout_raw.get("table_enabled", True),
        table_row_height=float(layout_raw.get("table_row_height", 7)),
        table_label_col_width=float(layout_raw.get("table_label_col_width", 30)),
        table_gap_from_schematic=float(layout_raw.get("table_gap_from_schematic", 50)),
        margins=margins_cfg,
    )

    # 排序
    sort_raw = raw.get("sort", {})
    cfg.sort = SortConfig(
        group_by=sort_raw.get("group_by", cfg.sort.group_by),
        group_order=sort_raw.get("group_order", cfg.sort.group_order),
        group_separator_enabled=sort_raw.get("group_separator_enabled", cfg.sort.group_separator_enabled),
        group_separator_text=sort_raw.get("group_separator_text", cfg.sort.group_separator_text),
    )

    # 输出
    output_raw = raw.get("output", {})
    cfg.output = OutputConfig(
        dwg_path=output_raw.get("dwg_path", cfg.output.dwg_path),
        report_path=output_raw.get("report_path", cfg.output.report_path),
        log_path=output_raw.get("log_path", cfg.output.log_path),
        log_level=output_raw.get("log_level", cfg.output.log_level),
    )

    # 文字样式
    text_raw = raw.get("text_style", {})
    cfg.text_style = TextStyleConfig(
        font=text_raw.get("font", cfg.text_style.font),
        height=float(text_raw.get("height", cfg.text_style.height)),
    )

    # 图框
    title_raw = raw.get("title_block", {})
    cfg.title_block = TitleBlockConfig(
        enabled=title_raw.get("enabled", cfg.title_block.enabled),
        insert_at_x=float(title_raw.get("insert_at_x", 0)),
        insert_at_y=float(title_raw.get("insert_at_y", 0)),
        attributes=title_raw.get("attributes", cfg.title_block.attributes),
    )

    logger.debug("配置加载完成: %s", path if 'path' in dir() else "<memory>")
    return cfg
