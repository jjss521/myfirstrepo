"""属性构建器单元测试"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_model import CircuitRecord, BlockDefinition, LoadType
from src.attribute_builder import build_attributes, build_all_attributes, CircuitWithBlock


def _make_circuit(
    load_type=LoadType.POWER,
    vfd_model=None,
    vfd_power_kw=None,
    remark=None,
) -> CircuitRecord:
    return CircuitRecord(
        row_number=2,
        circuit_id="L1",
        circuit_name="测试回路",
        load_type=load_type,
        rated_power_kw=15.0,
        rated_current_a=28.5,
        breaker_model="NSX100N",
        breaker_poles=3,
        breaker_trip_current_a=32.0,
        ct_ratio="50/5A",
        cable_type="YJV",
        cable_section="4x25+1x16",
        vfd_model=vfd_model,
        vfd_power_kw=vfd_power_kw,
        remark=remark,
    )


class TestBuildAttributes:
    """属性构建测试"""

    def test_basic_attributes(self):
        """基本属性构建"""
        circuit = _make_circuit()
        attrs = build_attributes(circuit, None)
        assert attrs["CIRCUIT_ID"] == "L1"
        assert attrs["CIRCUIT_NAME"] == "测试回路"
        assert attrs["BREAKER_MODEL"] == "NSX100N"
        assert attrs["BREAKER_POLES"] == "3P"
        assert attrs["BREAKER_Ir"] == "32.0A"
        assert attrs["LOAD_POWER"] == "15.00kW"
        assert attrs["LOAD_CURRENT"] == "28.50A"
        assert attrs["CT_RATIO"] == "50/5A"

    def test_vfd_attributes(self):
        """变频器回路属性"""
        circuit = _make_circuit(
            load_type=LoadType.VFD,
            vfd_model="ATV320",
            vfd_power_kw=30.0,
        )
        attrs = build_attributes(circuit, None)
        assert attrs["VFD_MODEL"] == "ATV320"
        assert attrs["VFD_POWER"] == "30.00kW"

    def test_no_vfd_for_power(self):
        """动力回路不应有 VFD 属性"""
        circuit = _make_circuit(load_type=LoadType.POWER)
        attrs = build_attributes(circuit, None)
        assert "VFD_MODEL" not in attrs
        assert "VFD_POWER" not in attrs

    def test_remark_attribute(self):
        """有备注时包含 REMARK"""
        circuit = _make_circuit(remark="双电源")
        attrs = build_attributes(circuit, None)
        assert attrs["REMARK"] == "双电源"

    def test_no_remark(self):
        """无备注时不包含 REMARK"""
        circuit = _make_circuit()
        attrs = build_attributes(circuit, None)
        assert "REMARK" not in attrs

    def test_with_block_def_filter(self):
        """有图块定义时只返回指定属性"""
        circuit = _make_circuit()
        block_def = BlockDefinition(
            name="LOOP_POWER_A",
            description="测试",
            applicable={},
            attributes=["CIRCUIT_ID", "BREAKER_MODEL"],
        )
        attrs = build_attributes(circuit, block_def)
        assert set(attrs.keys()) == {"CIRCUIT_ID", "BREAKER_MODEL"}


class TestBuildAllAttributes:
    """批量属性构建测试"""

    def test_batch_build(self):
        circuits = [
            _make_circuit(),
            _make_circuit(load_type=LoadType.VFD, vfd_model="ATV320", vfd_power_kw=30.0),
        ]
        mapped = [
            CircuitWithBlock(record=c, block_name="TEST_BLOCK")
            for c in circuits
        ]
        build_all_attributes(mapped)
        assert mapped[0].attributes["CIRCUIT_ID"] == "L1"
        assert "VFD_MODEL" in mapped[1].attributes
