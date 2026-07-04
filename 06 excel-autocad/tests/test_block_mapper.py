"""图块映射器单元测试"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_model import (
    CircuitRecord,
    LoadType,
    BlockMappingConfig,
    BlockMappingRule,
)
from src.block_mapper import map_circuits


def _make_circuit(
    circuit_id="L1",
    load_type=LoadType.POWER,
    poles=3,
    breaker_trip=32.0,
) -> CircuitRecord:
    return CircuitRecord(
        row_number=2,
        circuit_id=circuit_id,
        circuit_name="测试回路",
        load_type=load_type,
        rated_power_kw=15.0,
        rated_current_a=28.5,
        breaker_model="NSX100N",
        breaker_poles=poles,
        breaker_trip_current_a=breaker_trip,
        ct_ratio="50/5A",
        cable_type="YJV",
        cable_section="4x25+1x16",
    )


@pytest.fixture
def mapping_cfg():
    return BlockMappingConfig(
        rules=[
            BlockMappingRule(match={"breaker_max_current": 400}, block="LOOP_POWER_A"),
            BlockMappingRule(match={"breaker_min_current": 401}, block="LOOP_POWER_B"),
        ],
        default_block="LOOP_POWER_A",
    )


class TestBlockMapper:
    """图块映射测试"""

    def test_match_small_breaker(self, mapping_cfg):
        """≤400A 断路器匹配 LOOP_POWER_A"""
        circuit = _make_circuit(breaker_trip=32.0)
        mapped, warnings = map_circuits([circuit], mapping_cfg)
        assert mapped[0].block_name == "LOOP_POWER_A"
        assert len(warnings) == 0

    def test_match_large_breaker(self, mapping_cfg):
        """>400A 断路器匹配 LOOP_POWER_B"""
        circuit = _make_circuit(breaker_trip=630.0)
        mapped, warnings = map_circuits([circuit], mapping_cfg)
        assert mapped[0].block_name == "LOOP_POWER_B"
        assert len(warnings) == 0

    def test_match_boundary_400(self, mapping_cfg):
        """恰好 400A 匹配 LOOP_POWER_A"""
        circuit = _make_circuit(breaker_trip=400.0)
        mapped, _ = map_circuits([circuit], mapping_cfg)
        assert mapped[0].block_name == "LOOP_POWER_A"

    def test_match_boundary_401(self, mapping_cfg):
        """401A 匹配 LOOP_POWER_B"""
        circuit = _make_circuit(breaker_trip=401.0)
        mapped, _ = map_circuits([circuit], mapping_cfg)
        assert mapped[0].block_name == "LOOP_POWER_B"

    def test_no_match_uses_default(self):
        """无匹配规则时使用默认图块"""
        # 空规则列表，强制走默认
        cfg = BlockMappingConfig(rules=[], default_block="LOOP_POWER_A")
        circuit = _make_circuit(breaker_trip=32.0)
        mapped, warnings = map_circuits([circuit], cfg)
        assert mapped[0].block_name == "LOOP_POWER_A"
        assert len(warnings) == 1
        assert "无匹配规则" in warnings[0].error_message

    def test_multiple_circuits(self, mapping_cfg):
        """多回路批量映射"""
        circuits = [
            _make_circuit("L1", LoadType.POWER, 3, breaker_trip=32.0),
            _make_circuit("L2", LoadType.VFD, 3, breaker_trip=250.0),
            _make_circuit("L3", LoadType.LIGHTING, 1, breaker_trip=16.0),
            _make_circuit("L4", LoadType.POWER, 3, breaker_trip=630.0),
        ]
        mapped, warnings = map_circuits(circuits, mapping_cfg)
        assert len(mapped) == 4
        assert len(warnings) == 0
        assert mapped[0].block_name == "LOOP_POWER_A"
        assert mapped[1].block_name == "LOOP_POWER_A"
        assert mapped[2].block_name == "LOOP_POWER_A"
        assert mapped[3].block_name == "LOOP_POWER_B"
