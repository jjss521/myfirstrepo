"""
电气计算引擎模块

参照《氛围化编程指令书_配电系统图生成器.md》第3章全部规则实现。
包括：计算电流、断路器选型、脱扣器选型、单元空间判定、
CT变比、监控信号、保护整定值计算。
"""

from models import CircuitData

import logging

logger = logging.getLogger(__name__)


# 脱扣器额定电流标准序列（第3.3节）
STANDARD_IN_RATINGS = [
    16, 25, 32, 40, 50, 63, 100, 125, 140, 160,
    175, 200, 225, 250, 280, 320, 360, 400,
    450, 500, 570, 630,
]

# CT变比标准序列（第3.5节）
STANDARD_CT_RATINGS = [
    20, 30, 40, 50, 60, 75, 100, 150, 200, 250,
    300, 400, 500, 600, 750, 1000,
]

# 断路器壳架电流选型规则（第3.2节）
FRAME_CURRENT_RULES = [
    (63, 100),
    (125, 160),
    (225, 250),
    (360, 400),
    (600, 630),
]


def calc_ic_current(pe_power: float) -> float:
    """计算电流 Ic = Pe × 2（第3.1节）

    参照《氛围化编程指令书_配电系统图生成器.md》第3.1节。

    Args:
        pe_power: 设备功率（kW）

    Returns:
        计算电流（A）
    """
    # 当前Excel简化公式
    # 后续可扩展为需要系数法：Ic = Pe × Kx / (√3 × Un × cosφ)
    return round(pe_power * 2, 1)


def calc_frame_current(ic_current: float) -> int:
    """断路器壳架电流选型（第3.2节）

    参照《氛围化编程指令书_配电系统图生成器.md》第3.2节。

    Args:
        ic_current: 计算电流（A）

    Returns:
        壳架电流（A），超出范围时返回0
    """
    for threshold, frame in FRAME_CURRENT_RULES:
        if ic_current <= threshold:
            return frame
    return 0  # "超出区间"


def select_standard_rating(value: float, ratings: list) -> int:
    """从标准序列中选择 >= value 的最小值"""
    for r in ratings:
        if r >= value:
            return r
    return ratings[-1]


def calc_in_rated(ic_current: float, frame_current: int) -> int:
    """脱扣器额定电流In选型（第3.3节）

    参照《氛围化编程指令书_配电系统图生成器.md》第3.3节。

    Args:
        ic_current: 计算电流（A）
        frame_current: 壳架电流（A）

    Returns:
        脱扣器额定电流（A）
    """
    # 步骤1：计算基准电流 Ibase
    if ic_current <= 100:
        ibase = ic_current * 1.25
    elif ic_current <= 200:
        ibase = ic_current * 1.15
    else:
        ibase = ic_current * 1.12

    # 步骤2：从标准序列中选择 >= Ibase 的最小值
    selected = select_standard_rating(ibase, STANDARD_IN_RATINGS)

    # 步骤3：最终 In = MIN(选型结果, 壳架电流)
    return min(selected, frame_current)


def calc_unit_space(panel_type: str, frame_current: int) -> str:
    """单元空间判定（第3.4节）

    参照《氛围化编程指令书_配电系统图生成器.md》第3.4节。

    Args:
        panel_type: 柜型
        frame_current: 壳架电流（A）

    Returns:
        单元空间描述
    """
    if panel_type in ("XL21", "GGD"):
        return "/"

    if frame_current <= 160:
        return "8E/2"
    elif frame_current <= 250:
        return "8E"
    elif frame_current <= 400:
        return "16E"
    else:  # >= 630
        return "24E"


def calc_ct_ratio(ic_current: float, circuit_usage: str) -> str:
    """电流互感器变比（第3.5节）

    参照《氛围化编程指令书_配电系统图生成器.md》第3.5节。

    Args:
        ic_current: 计算电流（A）
        circuit_usage: 回路用途

    Returns:
        CT变比字符串，如"150/5"或"/"
    """
    # 特殊回路不装CT
    no_ct_keywords = ["插座箱", "阀", "备用", "起重机"]
    for kw in no_ct_keywords:
        if kw in circuit_usage:
            return "/"

    # 从标准序列中选择 >= Ic × 1.3 的最小值
    target = ic_current * 1.3
    selected = select_standard_rating(target, STANDARD_CT_RATINGS)
    return f"{selected}/5"


def calc_monitor(ct_ratio: str) -> str:
    """电力监控信号（第3.6节）

    参照《氛围化编程指令书_配电系统图生成器.md》第3.6节。

    Args:
        ct_ratio: CT变比

    Returns:
        监控信号描述
    """
    if ct_ratio == "/":
        return "/"
    return "三相电流,有功电度,合/分,故障"


def calc_protection_settings(circuit_usage: str, in_rated: int) -> tuple:
    """保护整定值计算（第3.7节）

    参照《氛围化编程指令书_配电系统图生成器.md》第3.7节。

    Args:
        circuit_usage: 回路用途
        in_rated: 脱扣器额定电流（A）

    Returns:
        (is1, is2, is3) 元组
    """
    is1 = round(in_rated * 1.0, 1)  # 长延时 = In × 1.0

    is_incoming = "进线" in circuit_usage
    is2 = round(in_rated * (6 if is_incoming else 3), 1)  # 短延时
    is3 = round(in_rated * (12 if is_incoming else 8), 1)  # 瞬动

    return is1, is2, is3


def determine_block_type(circuit_usage: str) -> str:
    """判断图块类型

    参照《氛围化编程指令书_配电系统图生成器.md》第4.1节。

    Args:
        circuit_usage: 回路用途

    Returns:
        图块类型：进线回路/馈线回路/备用回路
    """
    if "进线" in circuit_usage:
        return "进线回路"
    elif "备用" in circuit_usage:
        return "备用回路"
    else:
        return "馈线回路"


def calculate_circuit(circuit: CircuitData, panel_type: str) -> CircuitData:
    """对一个回路执行全部电气计算

    参照《氛围化编程指令书_配电系统图生成器.md》第3章全部规则，
    填充 CircuitData 中由计算得到的字段。

    Args:
        circuit: 待计算的回路数据（需包含 pe_power 和 circuit_usage）
        panel_type: 开关柜柜型

    Returns:
        计算完成后的回路数据
    """
    # 3.1 计算电流
    circuit.ic_current = calc_ic_current(circuit.pe_power)

    # 3.2 壳架电流
    circuit.frame_current = calc_frame_current(circuit.ic_current)

    # 3.3 脱扣器额定电流
    circuit.in_rated = calc_in_rated(circuit.ic_current, circuit.frame_current)

    # 3.4 单元空间
    circuit.unit_space = calc_unit_space(panel_type, circuit.frame_current)

    # 3.5 CT变比
    circuit.ct_ratio = calc_ct_ratio(circuit.ic_current, circuit.circuit_usage)

    # 3.6 监控信号
    circuit.monitor = calc_monitor(circuit.ct_ratio)

    # 3.7 保护整定
    is1, is2, is3 = calc_protection_settings(circuit.circuit_usage, circuit.in_rated)
    circuit.is1 = is1
    circuit.is2 = is2
    circuit.is3 = is3

    # 图块类型
    circuit.block_type = determine_block_type(circuit.circuit_usage)

    return circuit
