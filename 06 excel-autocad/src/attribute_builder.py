"""PDSG 属性构建器

将回路数据转换为图块属性键值对。
"""
import logging
from typing import Dict, Optional

from .data_model import (
    BlockDefinition,
    CircuitRecord,
    CircuitWithBlock,
    LoadType,
)

logger = logging.getLogger(__name__)


def build_attributes(
    circuit: CircuitRecord,
    block_def: Optional[BlockDefinition],
) -> Dict[str, str]:
    """为单个回路构建图块属性

    Args:
        circuit: 回路记录
        block_def: 图块定义（若为 None，则构建全量属性）

    Returns:
        属性字典 {Tag: 值字符串}
    """
    # 全量属性映射（Tag -> 取值函数）
    all_attrs: Dict[str, str] = {
        "CIRCUIT_ID": circuit.circuit_id,
        "CIRCUIT_NAME": circuit.circuit_name,
        "BREAKER_MODEL": circuit.breaker_model,
        "BREAKER_POLES": f"{circuit.breaker_poles}P",
        "BREAKER_Ir": f"{circuit.breaker_trip_current_a:.1f}A",
        "CABLE_TYPE": circuit.cable_type,
        "CABLE_SECTION": circuit.cable_section,
        "LOAD_POWER": f"{circuit.rated_power_kw:.2f}kW",
        "LOAD_CURRENT": f"{circuit.rated_current_a:.2f}A",
        "LOAD_TYPE": circuit.load_type.value,
        "CT_RATIO": circuit.ct_ratio,
    }

    # --- v1.1 新增属性（可选字段） ---
    if circuit.cabinet_code:
        all_attrs["CABINET_CODE"] = circuit.cabinet_code
    if circuit.distribution_type:
        all_attrs["DISTRIBUTION_TYPE"] = circuit.distribution_type
    if circuit.operation_mode:
        all_attrs["OPERATION_MODE"] = circuit.operation_mode
    if circuit.breaker_frame_current_a is not None:
        all_attrs["BREAKER_FRAME"] = f"{circuit.breaker_frame_current_a:.0f}A"
    if circuit.contactor:
        all_attrs["CONTACTOR"] = circuit.contactor
    if circuit.thermal_relay:
        all_attrs["THERMAL_RELAY"] = circuit.thermal_relay
    if circuit.power_monitoring:
        all_attrs["POWER_MONITORING"] = circuit.power_monitoring
    if circuit.cable_number:
        all_attrs["CABLE_NUMBER"] = circuit.cable_number

    # 可选属性：变频器
    if circuit.load_type == LoadType.VFD:
        all_attrs["VFD_MODEL"] = circuit.vfd_model or ""
        if circuit.vfd_power_kw is not None:
            all_attrs["VFD_POWER"] = f"{circuit.vfd_power_kw:.2f}kW"
        else:
            all_attrs["VFD_POWER"] = ""

    # 可选属性：备注
    if circuit.remark:
        all_attrs["REMARK"] = circuit.remark

    # 若图块定义指定了属性子集，只返回子集
    if block_def and block_def.attributes:
        return {
            tag: all_attrs.get(tag, "")
            for tag in block_def.attributes
        }

    return all_attrs


def build_all_attributes(
    mapped_circuits: list,
    catalog=None,
) -> None:
    """批量为所有已映射回路构建属性（就地写入 attributes 字段）

    Args:
        mapped_circuits: List[CircuitWithBlock]
        catalog: BlockCatalog 实例（可选）
    """
    for cwb in mapped_circuits:
        block_def = None
        if catalog:
            block_def = catalog.find(cwb.block_name)
        cwb.attributes = build_attributes(cwb.record, block_def)
