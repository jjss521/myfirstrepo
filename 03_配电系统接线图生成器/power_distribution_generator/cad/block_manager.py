"""
图块加载与属性管理模块

参照《氛围化编程指令书_配电系统图生成器.md》第4章和第6.6节。
管理DWG图块的加载、属性映射和回路编号生成。
"""

import os
from pathlib import Path

# 图块文件目录
BLOCKS_DIR = Path(__file__).resolve().parent.parent / "blocks"

# 图块文件名映射
BLOCK_FILE_MAP = {
    "进线回路": "进线回路.dwg",
    "馈线回路": "馈线回路.dwg",
    "备用回路": "备用回路.dwg",
}


def get_block_dwg_path(block_type: str) -> str:
    """获取图块DWG文件的完整路径

    Args:
        block_type: 图块类型（进线回路/馈线回路/备用回路）

    Returns:
        DWG文件完整路径
    """
    filename = BLOCK_FILE_MAP.get(block_type, "馈线回路.dwg")
    return str(BLOCKS_DIR / filename)


def block_file_exists(block_type: str) -> bool:
    """检查图块DWG文件是否存在

    Args:
        block_type: 图块类型

    Returns:
        文件是否存在
    """
    return os.path.exists(get_block_dwg_path(block_type))


def get_block_attributes(circuit) -> dict:
    """从CircuitData构建图块属性字典

    参照《氛围化编程指令书_配电系统图生成器.md》第4.2节。

    Args:
        circuit: CircuitData实例

    Returns:
        属性标签->属性值的字典，用于插入图块或增量更新
    """
    return {
        "CIRCUIT_NAME": circuit.circuit_usage,
        "CIRCUIT_NO": circuit.circuit_no,
        "PE_POWER": f"{circuit.pe_power}kW",
        "IC_CURRENT": f"{circuit.ic_current}A",
        "FRAME_CURRENT": f"{circuit.frame_current}A",
        "IN_RATED": f"{circuit.in_rated}A",
        "IS1": f"{circuit.is1}A",
        "IS2": f"{circuit.is2}A",
        "IS3": f"{circuit.is3}A",
        "CT_RATIO": circuit.ct_ratio,
        "MONITOR": circuit.monitor,
        "CABLE_SPEC": circuit.cable_spec,
        "CABLE_NO": circuit.cable_no,
        "UNIT_SPACE": circuit.unit_space,
    }


def detect_attribute_changes(circuit) -> dict:
    """对比当前数据与上次CAD同步快照，返回变化的属性

    参照《氛围化编程指令书_配电系统图生成器.md》第7.2节。

    Args:
        circuit: CircuitData实例

    Returns:
        变化的 {标签: 新值} 字典
    """
    current_attrs = get_block_attributes(circuit)

    if circuit.last_synced is None:
        return current_attrs  # 首次同步，全部属性都需要更新

    changed = {}
    for key, value in current_attrs.items():
        if circuit.last_synced.get(key) != value:
            changed[key] = value

    return changed


def update_sync_snapshot(circuit):
    """更新CAD同步快照

    Args:
        circuit: 要更新快照的回路
    """
    circuit.last_synced = get_block_attributes(circuit)
