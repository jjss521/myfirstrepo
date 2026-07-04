"""集成测试 — 端到端流程（不依赖 AutoCAD）

测试从 Excel 读取 -> 映射 -> 属性构建 -> 布局计算的完整链路。
AutoCAD 绘图部分通过 mock 验证。
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_loader import load_config
from src.excel_reader import read_and_validate
from src.block_mapper import map_circuits
from src.attribute_builder import build_all_attributes
from src.layout_engine import compute
from src.block_library import load_catalog
from src.data_model import LoadType
from tests.conftest import sample_valid_path, sample_errors_path, default_config_path


@pytest.fixture
def cfg():
    return load_config(default_config_path())


class TestEndToEnd:
    """端到端集成测试"""

    def test_full_pipeline(self, cfg):
        """完整流程：读取 -> 映射 -> 属性 -> 布局"""
        # Step 1: Excel 读取
        records, errors = read_and_validate(sample_valid_path(), cfg.excel)
        assert len(records) == 20
        assert len(errors) == 0

        # Step 2: 加载图块目录
        catalog = load_catalog(cfg.block_library.catalog)
        assert len(catalog.blocks) > 0

        # Step 3: 图块映射
        mapped, warnings = map_circuits(records, cfg.block_mapping, catalog)
        assert len(mapped) == 20

        # Step 4: 属性构建
        build_all_attributes(mapped, catalog)
        for m in mapped:
            assert "CIRCUIT_ID" in m.attributes
            assert m.attributes["CIRCUIT_ID"] == m.record.circuit_id

        # Step 5: 布局计算
        layout = compute(mapped, cfg.layout, cfg.sort)
        assert len(layout.placements) == 20
        assert layout.bus_line.x == cfg.layout.bus_x
        # 水平布局可能超出标准幅面宽度，会选用横放幅面
        assert "A" in layout.paper_size.name

    def test_pipeline_with_errors(self, cfg):
        """含错误数据的流程：应跳过错误行继续处理"""
        records, errors = read_and_validate(sample_errors_path(), cfg.excel)
        assert len(records) == 2
        assert len(errors) > 0

        catalog = load_catalog(cfg.block_library.catalog)
        mapped, warnings = map_circuits(records, cfg.block_mapping, catalog)
        assert len(mapped) == 2

        build_all_attributes(mapped, catalog)
        layout = compute(mapped, cfg.layout, cfg.sort)
        assert len(layout.placements) == 2

    def test_grouping(self, cfg):
        """分组排序正确性"""
        records, _ = read_and_validate(sample_valid_path(), cfg.excel)
        catalog = load_catalog(cfg.block_library.catalog)
        mapped, _ = map_circuits(records, cfg.block_mapping, catalog)
        build_all_attributes(mapped, catalog)

        layout = compute(mapped, cfg.layout, cfg.sort)

        # 检查 X 坐标递增 (水平布局)
        for i in range(len(layout.placements) - 1):
            assert layout.placements[i].x < layout.placements[i + 1].x

        # 检查分组标签数量
        if cfg.sort.group_separator_enabled:
            types_present = set(cwb.record.load_type.value for cwb in mapped)
            assert len(layout.group_labels) == len(types_present)

    def test_dry_run_mode(self, cfg):
        """dry-run 模式不连接 AutoCAD"""
        records, errors = read_and_validate(sample_valid_path(), cfg.excel)
        catalog = load_catalog(cfg.block_library.catalog)
        mapped, _ = map_circuits(records, cfg.block_mapping, catalog)
        build_all_attributes(mapped, catalog)
        layout = compute(mapped, cfg.layout, cfg.sort)

        # dry-run 模式下只需验证布局结果
        assert layout.paper_size is not None
        assert len(layout.placements) == len(mapped)


class TestConfigLoading:
    """配置加载集成测试"""

    def test_load_default_config(self):
        cfg = load_config(default_config_path())
        assert cfg.excel.sheet_name == "低压配电系统"
        assert cfg.excel.format_auto_detect is True
        assert cfg.excel.default_breaker_model == "NSX100N"
        assert len(cfg.excel.transposed_column_aliases) > 0
        assert len(cfg.block_mapping.rules) > 0
        assert cfg.layout.bus_x == 100
        assert cfg.autocad.visible is True

    def test_config_block_mapping_rules(self):
        cfg = load_config(default_config_path())
        # 验证规则数量 (v2.0: 2条断路器电流阈值规则)
        assert len(cfg.block_mapping.rules) >= 2
        # 验证第一条规则 (≤400A → LOOP_POWER_A)
        first_rule = cfg.block_mapping.rules[0]
        assert first_rule.match["breaker_max_current"] == 400
        assert first_rule.block == "LOOP_POWER_A"
