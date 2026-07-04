"""PDSG 布局引擎

计算图块放置坐标、母线位置、参数表格和图纸幅面。

水平布局 (默认):
- 回路从左到右排列，间距 horizontal_spacing
- 水平母线在顶部 (bus_y)
- 参数表格在原理图下方

坐标系: (0,0)=图纸左下角, X轴向右, Y轴向上。
"""
import logging
import re
from typing import Dict, List, Optional, Tuple

from .data_model import (
    BusLine,
    CircuitWithBlock,
    GroupLabel,
    LayoutConfig,
    LayoutResult,
    LoadType,
    LOAD_TYPE_ORDER,
    PaperSize,
    Placement,
    SortConfig,
    PaperSizeDef,
    MarginsConfig,
    TableLayout,
)

logger = logging.getLogger(__name__)

# 参数表格行定义 (行标签, 字段提取函数)
TABLE_ROW_DEFS = [
    ("回路编号",  lambda r: r.circuit_id),
    ("回路名称",  lambda r: r.circuit_name),
    ("负荷类型",  lambda r: r.load_type.value),
    ("功率(kW)",  lambda r: f"{r.rated_power_kw:.1f}" if r.rated_power_kw else ""),
    ("电流(A)",   lambda r: f"{r.rated_current_a:.1f}" if r.rated_current_a else ""),
    ("断路器型号", lambda r: r.breaker_model),
    ("极数",      lambda r: f"{r.breaker_poles}P" if r.breaker_poles else ""),
    ("脱扣器(A)", lambda r: f"{r.breaker_trip_current_a:.0f}" if r.breaker_trip_current_a else ""),
    ("CT变比",    lambda r: r.ct_ratio if r.ct_ratio else ""),
    ("电缆型号",  lambda r: r.cable_type if r.cable_type else ""),
    ("电缆截面",  lambda r: r.cable_section if r.cable_section else ""),
    ("备注",      lambda r: r.remark if r.remark else ""),
]


def compute(
    circuits: List[CircuitWithBlock],
    layout_cfg: LayoutConfig,
    sort_cfg: SortConfig,
) -> LayoutResult:
    """计算水平布局

    回路从左到右排列:
    - 第 i 个回路的 X = bus_x + i * horizontal_spacing
    - 所有回路的 Y = bus_y (水平母线高度)
    - 水平母线从第一个回路延伸到最后一个回路
    - 参数表格在原理图下方
    """
    if not circuits:
        raise ValueError("无有效回路数据，无法计算布局")

    # 分组排序
    groups = _group_and_sort(circuits, sort_cfg)

    # 扁平化排序后的回路列表
    ordered: List[CircuitWithBlock] = []
    for group_name, items in groups:
        ordered.extend(items)

    total_circuits = len(ordered)
    spacing = layout_cfg.horizontal_spacing
    margins = layout_cfg.margins

    # 计算各回路放置坐标 (水平排列)
    placements: List[Placement] = []
    first_x = layout_cfg.bus_x
    bus_y = layout_cfg.bus_y

    for i, cwb in enumerate(ordered):
        x = first_x + i * spacing
        placements.append(Placement(
            block_name=cwb.block_name,
            x=x,
            y=bus_y,
            attributes=cwb.attributes,
            circuit_id=cwb.record.circuit_id,
        ))

    # 水平母线: 从第一个回路到最后一个回路
    last_x = first_x + (total_circuits - 1) * spacing if total_circuits > 1 else first_x
    bus_line = BusLine(
        direction="horizontal",
        bus_y=bus_y,
        x_start=first_x,
        x_end=last_x,
        # 兼容旧字段
        x=first_x,
        y_start=bus_y,
        y_end=bus_y,
    )

    # 参数表格
    table = None
    if layout_cfg.table_enabled:
        table = _compute_table(ordered, placements, layout_cfg, margins)

    # 分组标签 (水平布局中标签放在每组第一个回路上方)
    group_labels: List[GroupLabel] = []
    if sort_cfg.group_separator_enabled:
        idx = 0
        for group_name, items in groups:
            if items:
                p = placements[idx]
                group_labels.append(GroupLabel(
                    text=sort_cfg.group_separator_text.replace("{type}", group_name),
                    x=p.x,
                    y=bus_y + 30,
                ))
            idx += len(items)

    # 计算所需图纸尺寸
    needed_width = (
        margins.left
        + last_x
        + spacing  # 右边留一个间距
        + margins.right
    )
    # 表格底边 Y
    table_bottom = margins.bottom
    if table:
        n_rows = len(TABLE_ROW_DEFS) + 1  # +1 for header
        table_bottom = table.y - n_rows * layout_cfg.table_row_height
    needed_height = bus_y + 50 + margins.top  # 上方留余量
    if table_bottom < margins.bottom:
        needed_height = max(needed_height, bus_y + abs(table_bottom) + margins.top + margins.bottom)

    # 选择幅面 (需要足够宽)
    paper = _select_paper_horizontal(needed_width, needed_height, layout_cfg.paper.sizes)

    logger.info(
        "%s 幅面 %d 回路 水平间距 %.2fmm 母线Y=%.0f",
        paper.name, total_circuits, spacing, bus_y,
    )

    return LayoutResult(
        placements=placements,
        bus_line=bus_line,
        group_labels=group_labels,
        paper_size=paper,
        table=table,
    )


def _compute_table(
    circuits: List[CircuitWithBlock],
    placements: List[Placement],
    layout_cfg: LayoutConfig,
    margins: MarginsConfig,
) -> TableLayout:
    """计算参数表格布局

    表格位于原理图下方:
    - 列: 左侧标签列 + 每个回路一列
    - 行: 各参数行
    - 列宽 = horizontal_spacing (与回路间距一致)
    """
    spacing = layout_cfg.horizontal_spacing
    col_width = spacing
    label_w = layout_cfg.table_label_col_width
    row_h = layout_cfg.table_row_height

    # 表格 X 起点: 标签列在第一个回路左侧
    table_x = layout_cfg.bus_x - label_w
    # 表格顶部 Y: 母线 Y 下方一定距离
    table_top_y = layout_cfg.bus_y - layout_cfg.table_gap_from_schematic

    # 列头: 回路编号
    headers = [cwb.record.circuit_id for cwb in circuits]

    # 行数据
    row_labels = [rd[0] for rd in TABLE_ROW_DEFS]
    rows = []
    for label, extractor in TABLE_ROW_DEFS:
        row_data = []
        for cwb in circuits:
            try:
                val = extractor(cwb.record)
            except Exception:
                val = ""
            row_data.append(str(val) if val else "")
        rows.append(row_data)

    return TableLayout(
        x=table_x,
        y=table_top_y,
        col_width=col_width,
        row_height=row_h,
        headers=headers,
        rows=rows,
        row_labels=row_labels,
    )


def _group_and_sort(
    circuits: List[CircuitWithBlock],
    sort_cfg: SortConfig,
) -> List[Tuple[str, List[CircuitWithBlock]]]:
    """分组并排序"""
    order_map: Dict[str, int] = {}
    for i, name in enumerate(sort_cfg.group_order):
        order_map[name] = i

    groups: Dict[str, List[CircuitWithBlock]] = {}
    for cwb in circuits:
        lt = cwb.record.load_type.value
        if lt not in groups:
            groups[lt] = []
        groups[lt].append(cwb)

    for lt in groups:
        groups[lt].sort(key=lambda c: _natural_sort_key(c.record.circuit_id))

    sorted_groups = sorted(
        groups.items(),
        key=lambda item: order_map.get(item[0], 999),
    )

    return sorted_groups


def _natural_sort_key(s: str):
    """自然排序键（数字部分按数值比较）"""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", s)
    ]


def _select_paper_horizontal(
    needed_width: float,
    needed_height: float,
    sizes: List[PaperSizeDef],
) -> PaperSize:
    """选择能容纳所需宽度和高度的最小幅面

    水平布局主要受宽度限制，可能需要横向使用幅面。
    """
    best = None
    for s in sorted(sizes, key=lambda x: x.width * x.height):
        # 正常使用 (宽×高)
        if needed_width <= s.width and needed_height <= s.height:
            return PaperSize(name=s.name, width=s.width, height=s.height)
        # 横向使用 (高→宽, 宽→高)
        if needed_width <= s.height and needed_height <= s.width:
            return PaperSize(name=s.name + "横", width=s.height, height=s.width)
        best = s

    # 使用最大幅面 (横向)
    largest = max(sizes, key=lambda x: x.width * x.height)
    if needed_width > largest.height:
        logger.warning(
            "所需宽度 %.0fmm 超出最大幅面 %s (%.0fmm)，仍使用最大幅面横向",
            needed_width, largest.name, largest.height,
        )
    return PaperSize(
        name=largest.name + "横",
        width=largest.height,
        height=largest.width,
    )
