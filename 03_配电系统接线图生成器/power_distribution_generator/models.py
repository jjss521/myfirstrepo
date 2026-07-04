"""
数据模型模块

参照《氛围化编程指令书_配电系统图生成器.md》第7.1节定义。
提供 PanelData 和 CircuitData 两个核心数据类，存储从Excel读取的
配电回路数据以及CAD同步状态。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CircuitData:
    """单个回路的数据模型

    参照《氛围化编程指令书_配电系统图生成器.md》第7.1节。
    """
    column_index: int           # Excel列索引（C=3, D=4, ...）
    circuit_usage: str          # 回路用途（行6）
    pe_power: float = 0.0      # 设备功率kW（行7）
    ic_current: float = 0.0    # 计算电流A（行8）
    frame_current: int = 0     # 壳架电流A（行9）
    in_rated: int = 0          # 脱扣器额定电流A（行10）
    is1: float = 0.0           # 长延时整定A（行11）
    is2: float = 0.0           # 短延时整定A（行12）
    is3: float = 0.0           # 瞬动整定A（行13）
    ct_ratio: str = ""          # CT变比（行14）
    monitor: str = ""           # 监控信号（行15）
    cable_spec: str = ""        # 线缆型号（行16）
    cable_section: str = ""     # 线缆截面（行17，预留）
    cable_no: str = ""          # 线缆编号（行18）
    unit_space: str = ""        # 单元空间（行5）
    circuit_no: str = ""        # 完整回路编号（自动生成）
    block_type: str = ""        # 图块类型（进线/馈线/备用，自动判定）

    # CAD同步状态
    cad_handle: Optional[str] = None   # 图块句柄（首次插入后记录）
    last_synced: Optional[dict] = None # 上次同步到CAD的属性快照


@dataclass
class PanelData:
    """一个开关柜的数据模型

    参照《氛围化编程指令书_配电系统图生成器.md》第7.1节。
    """
    panel_no: str                     # 开关柜编号（行2，去除前导=）
    panel_type: str = ""              # 柜型（行3）
    panel_size: str = ""              # 尺寸（行4）
    circuits: list = field(default_factory=list)  # CircuitData列表（最多8个）

    # CAD同步状态
    busbar_handle: Optional[str] = None  # 母线句柄
    base_point: Optional[tuple] = None   # 基准点坐标
