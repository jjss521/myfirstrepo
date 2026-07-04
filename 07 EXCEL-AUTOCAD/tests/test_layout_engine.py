"""布局引擎单元测试 — 水平布局"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_model import (
    CircuitRecord,
    CircuitWithBlock,
    LayoutConfig,
    LoadType,
    SortConfig,
    PaperConfig,
    PaperSizeDef,
    MarginsConfig,
)
from src.layout_engine import compute, _natural_sort_key, _select_paper_horizontal


def _make_cwb(circuit_id="L1", load_type=LoadType.POWER, poles=3) -> CircuitWithBlock:
    record = CircuitRecord(
        row_number=2,
        circuit_id=circuit_id,
        circuit_name="测试回路",
        load_type=load_type,
        rated_power_kw=15.0,
        rated_current_a=28.5,
        breaker_model="NSX100N",
        breaker_poles=poles,
        breaker_trip_current_a=32.0,
        ct_ratio="50/5A",
        cable_type="YJV",
        cable_section="4x25+1x16",
    )
    return CircuitWithBlock(
        record=record,
        block_name=f"LOOP_TEST_{poles}P",
        attributes={"CIRCUIT_ID": circuit_id},
    )


@pytest.fixture
def layout_cfg():
    return LayoutConfig(
        paper=PaperConfig(sizes=[
            PaperSizeDef("A2", 594, 420),
            PaperSizeDef("A1", 841, 594),
            PaperSizeDef("A0", 1189, 841),
        ]),
        bus_x=100,
        bus_y=780,
        block_offset_x=0,
        horizontal_spacing=2140.5407,
        table_enabled=True,
        table_row_height=7,
        table_label_col_width=30,
        table_gap_from_schematic=50,
        margins=MarginsConfig(left=25, right=25, top=15, bottom=30),
    )


@pytest.fixture
def sort_cfg():
    return SortConfig(
        group_by="load_type",
        group_order=["动力", "变频", "空调", "照明", "插座", "备用", "电容补偿"],
        group_separator_enabled=True,
        group_separator_text="{type} 配电",
    )


class TestLayoutEngine:
    """水平布局计算测试"""

    def test_basic_layout(self, layout_cfg, sort_cfg):
        """基本布局：5 个回路从左到右排列"""
        circuits = [_make_cwb(f"L{i}") for i in range(1, 6)]
        result = compute(circuits, layout_cfg, sort_cfg)

        assert len(result.placements) == 5
        # X 坐标递增
        for i in range(len(result.placements) - 1):
            assert result.placements[i].x < result.placements[i + 1].x
        # 所有回路 Y 相同 (水平母线)
        for p in result.placements:
            assert p.y == 780

    def test_spacing(self, layout_cfg, sort_cfg):
        """相邻回路间距 = horizontal_spacing"""
        circuits = [_make_cwb(f"L{i}") for i in range(1, 4)]
        result = compute(circuits, layout_cfg, sort_cfg)

        for i in range(len(result.placements) - 1):
            dx = result.placements[i + 1].x - result.placements[i].x
            assert abs(dx - 2140.5407) < 0.01

    def test_bus_line_horizontal(self, layout_cfg, sort_cfg):
        """水平母线坐标正确"""
        circuits = [_make_cwb(f"L{i}") for i in range(1, 4)]
        result = compute(circuits, layout_cfg, sort_cfg)

        assert result.bus_line.direction == "horizontal"
        assert result.bus_line.bus_y == 780
        assert result.bus_line.x_start == 100
        # 最后一个回路 X = 100 + 2 * 2140.5407
        expected_end = 100 + 2 * 2140.5407
        assert abs(result.bus_line.x_end - expected_end) < 0.01

    def test_table_generated(self, layout_cfg, sort_cfg):
        """参数表格生成"""
        circuits = [_make_cwb(f"L{i}") for i in range(1, 4)]
        result = compute(circuits, layout_cfg, sort_cfg)

        assert result.table is not None
        assert len(result.table.headers) == 3
        assert len(result.table.rows) == 12  # TABLE_ROW_DEFS 定义的行数
        assert result.table.row_labels[0] == "回路编号"

    def test_table_disabled(self, sort_cfg):
        """禁用表格"""
        layout_cfg = LayoutConfig(table_enabled=False)
        circuits = [_make_cwb(f"L{i}") for i in range(1, 3)]
        result = compute(circuits, layout_cfg, sort_cfg)
        assert result.table is None

    def test_group_separator(self, layout_cfg, sort_cfg):
        """分组标签"""
        circuits = [
            _make_cwb("L1", LoadType.POWER),
            _make_cwb("L2", LoadType.LIGHTING),
        ]
        result = compute(circuits, layout_cfg, sort_cfg)
        assert len(result.group_labels) == 2

    def test_no_separator(self, layout_cfg):
        """禁用分组标签"""
        sort_cfg = SortConfig(group_separator_enabled=False)
        circuits = [
            _make_cwb("L1", LoadType.POWER),
            _make_cwb("L2", LoadType.LIGHTING),
        ]
        result = compute(circuits, layout_cfg, sort_cfg)
        assert len(result.group_labels) == 0

    def test_group_order(self, layout_cfg, sort_cfg):
        """分组顺序正确：动力在照明之前 (X 更小, 更靠左)"""
        circuits = [
            _make_cwb("L1", LoadType.LIGHTING),
            _make_cwb("L2", LoadType.POWER),
        ]
        result = compute(circuits, layout_cfg, sort_cfg)
        # 动力回路排在左侧 (X 更小)
        assert result.placements[0].circuit_id == "L2"
        assert result.placements[1].circuit_id == "L1"
        assert result.placements[0].x < result.placements[1].x

    def test_empty_circuits(self, layout_cfg, sort_cfg):
        """空回路列表应抛异常"""
        with pytest.raises(ValueError):
            compute([], layout_cfg, sort_cfg)


class TestNaturalSortKey:
    """自然排序键测试"""

    def test_simple(self):
        items = ["L10", "L2", "L1", "L20"]
        sorted_items = sorted(items, key=_natural_sort_key)
        assert sorted_items == ["L1", "L2", "L10", "L20"]

    def test_mixed(self):
        items = ["PE1", "L3", "L1", "PE10", "L2"]
        sorted_items = sorted(items, key=_natural_sort_key)
        assert sorted_items[0] == "L1"
        assert sorted_items[-1] == "PE10"


class TestSelectPaperHorizontal:
    """幅面选择测试 (水平布局)"""

    def test_small_dimensions(self):
        """小尺寸选最小幅面"""
        sizes = [PaperSizeDef("A2", 594, 420), PaperSizeDef("A1", 841, 594)]
        result = _select_paper_horizontal(300, 300, sizes)
        assert result.name == "A2"

    def test_needs_landscape(self):
        """宽度超出竖放时需要横放"""
        sizes = [PaperSizeDef("A2", 594, 420), PaperSizeDef("A1", 841, 594)]
        result = _select_paper_horizontal(500, 500, sizes)
        # A2 横放: 420x594 → 宽420<500 不够; A1 横放: 594x841 → 宽594≥500, 高841≥500
        assert "A1" in result.name

    def test_exceeds_all(self):
        """超出所有幅面仍返回最大幅面"""
        sizes = [PaperSizeDef("A2", 594, 420)]
        result = _select_paper_horizontal(9999, 9999, sizes)
        assert "A2" in result.name
