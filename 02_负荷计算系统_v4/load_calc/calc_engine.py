# -*- coding: utf-8 -*-
"""核心计算引擎"""

from math import sqrt, acos, cos, ceil
from typing import List, Optional, Tuple
from dataclasses import dataclass

from .models import (
    Equipment, EquipmentGroup, Subsystem, HVSystem, VoltageLevel
)
from .config import (
    SIMULTANEOUS_KP, SIMULTANEOUS_KQ,
    TARGET_POWER_FACTOR, TRANSFORMER_LOSS_P, TRANSFORMER_LOSS_Q
)


HV_TARGET_POWER_FACTOR = 0.95


@dataclass
class CompensationResult:
    """无功补偿计算结果"""
    power_factor_before: float
    power_factor_after: float
    required_qc: float
    actual_qc: float
    compensated_pc: float
    compensated_qc: float
    compensated_sc: float


def calc_equipment_power(eq: Equipment) -> Tuple[float, float, float]:
    """计算单个设备的有功、无功、视在功率"""
    pc = eq.rated_power * eq.working_count * eq.kx
    qc = pc * eq.tan_phi
    sc = sqrt(pc ** 2 + qc ** 2)
    return pc, qc, sc


def calc_group_subtotal(group: EquipmentGroup) -> Tuple[float, float, float]:
    """计算设备组小计（不计同时系数）"""
    total_pc = sum(e.pc for e in group.equipment_list if not e.is_subtotal)
    total_qc = sum(e.qc for e in group.equipment_list if not e.is_subtotal)
    total_sc = sqrt(total_pc ** 2 + total_qc ** 2)
    return total_pc, total_qc, total_sc


def calc_group_computed(group: EquipmentGroup) -> Tuple[float, float, float]:
    """计算设备组计算负荷（计入同时系数）"""
    total_pc, total_qc, _ = calc_group_subtotal(group)
    computed_pc = total_pc * group.kp
    computed_qc = total_qc * group.kq
    computed_sc = sqrt(computed_pc ** 2 + computed_qc ** 2)
    return computed_pc, computed_qc, computed_sc


def calc_qc_for_hv_pf_target(
    total_pc: float,
    total_qc: float,
    target_hv_pf: float = HV_TARGET_POWER_FACTOR
) -> float:
    """
    计算使高压侧功率因数达到目标值所需的最小无功补偿容量(kvar)。
    使用二分法迭代求解。
    """
    if total_pc <= 0 or total_qc <= 0:
        return 0.0
    low, high = 0.0, total_qc * 2.0
    for _ in range(50):
        mid = (low + high) / 2.0
        q_comp = max(0, total_qc - mid)
        s_comp = sqrt(total_pc ** 2 + q_comp ** 2)
        if s_comp <= 0:
            return 0.0
        loss_p = s_comp * TRANSFORMER_LOSS_P
        loss_q = s_comp * TRANSFORMER_LOSS_Q
        hv_p = total_pc + loss_p
        hv_q = q_comp + loss_q
        hv_s = sqrt(hv_p ** 2 + hv_q ** 2)
        hv_pf_val = hv_p / hv_s if hv_s > 0 else 0
        if hv_pf_val >= target_hv_pf:
            high = mid
        else:
            low = mid
    return ceil(high / 10) * 10


def calc_compensation(
    total_pc: float,
    total_qc: float,
    target_pf: float = TARGET_POWER_FACTOR
) -> CompensationResult:
    """计算无功补偿"""
    before_sc = sqrt(total_pc ** 2 + total_qc ** 2)
    pf_before = total_pc / before_sc if before_sc > 0 else 0

    tan_before = total_qc / total_pc if total_pc > 0 else 0
    tan_after = sqrt(1 - target_pf ** 2) / target_pf if target_pf > 0 else 0
    required_qc_lv = max(0, total_pc * (tan_before - tan_after)) if total_pc > 0 else 0

    required_qc_hv = calc_qc_for_hv_pf_target(total_pc, total_qc, HV_TARGET_POWER_FACTOR)
    required_qc = max(required_qc_lv, required_qc_hv)
    actual_qc = max(0, round(required_qc / 10) * 10)

    compensated_qc = max(0, total_qc - actual_qc)
    compensated_sc = sqrt(total_pc ** 2 + compensated_qc ** 2)
    pf_after = total_pc / compensated_sc if compensated_sc > 0 else 0

    return CompensationResult(
        power_factor_before=pf_before,
        power_factor_after=pf_after,
        required_qc=required_qc,
        actual_qc=actual_qc,
        compensated_pc=total_pc,
        compensated_qc=compensated_qc,
        compensated_sc=compensated_sc,
    )


def calc_compensation_with_actual_qc(
    total_pc: float,
    total_qc: float,
    actual_qc: float
) -> CompensationResult:
    """根据给定的实际补偿容量计算补偿后参数"""
    before_sc = sqrt(total_pc ** 2 + total_qc ** 2)
    pf_before = total_pc / before_sc if before_sc > 0 else 0

    compensated_qc = max(0, total_qc - actual_qc)
    compensated_sc = sqrt(total_pc ** 2 + compensated_qc ** 2)
    pf_after = total_pc / compensated_sc if compensated_sc > 0 else 0

    return CompensationResult(
        power_factor_before=pf_before,
        power_factor_after=pf_after,
        required_qc=max(0, total_qc - total_pc * sqrt(1 - 0.95 ** 2) / 0.95),
        actual_qc=actual_qc,
        compensated_pc=total_pc,
        compensated_qc=compensated_qc,
        compensated_sc=compensated_sc,
    )


def calc_transformer_loss(sc: float) -> Tuple[float, float]:
    """估算变压器损耗"""
    loss_p = sc * TRANSFORMER_LOSS_P
    loss_q = sc * TRANSFORMER_LOSS_Q
    return loss_p, loss_q


def calc_subsystem_summary(subsystem: Subsystem) -> dict:
    """计算子系统汇总"""
    total_pc = subsystem.total_pc
    total_qc = subsystem.total_qc
    actual_qc = subsystem.compensation_qc
    target_pf = subsystem.target_power_factor

    before_sc = sqrt(total_pc ** 2 + total_qc ** 2)
    pf_before = total_pc / before_sc if before_sc > 0 else 0

    tan_before = total_qc / total_pc if total_pc > 0 else 0
    tan_after = sqrt(1 - target_pf ** 2) / target_pf if target_pf > 0 else 0
    required_qc_lv = max(0, total_pc * (tan_before - tan_after)) if total_pc > 0 else 0

    required_qc_hv = calc_qc_for_hv_pf_target(total_pc, total_qc, HV_TARGET_POWER_FACTOR)
    required_qc = max(required_qc_lv, required_qc_hv)

    compensated_qc = max(0, total_qc - actual_qc)
    compensated_sc = sqrt(total_pc ** 2 + compensated_qc ** 2)
    pf_after = total_pc / compensated_sc if compensated_sc > 0 else 0

    loss_p, loss_q = calc_transformer_loss(compensated_sc)

    hv_pc = total_pc + loss_p
    hv_qc = compensated_qc + loss_q
    hv_sc = sqrt(hv_pc ** 2 + hv_qc ** 2)
    hv_pf = hv_pc / hv_sc if hv_sc > 0 else 0

    additional_qc_needed = max(0, required_qc_hv - actual_qc)

    return {
        "pc": total_pc,
        "qc": total_qc,
        "sc": sqrt(total_pc ** 2 + total_qc ** 2),
        "pf_before": pf_before,
        "required_qc": required_qc,
        "required_qc_hv": required_qc_hv,
        "additional_qc_needed": additional_qc_needed,
        "actual_qc": actual_qc,
        "pf_after": pf_after,
        "compensated_pc": total_pc,
        "compensated_qc": compensated_qc,
        "compensated_sc": compensated_sc,
        "transformer_loss_p": loss_p,
        "transformer_loss_q": loss_q,
        "hv_pc": hv_pc,
        "hv_qc": hv_qc,
        "hv_sc": hv_sc,
        "hv_pf": hv_pf,
        "transformer_capacity": subsystem.total_transformer_capacity,
        "load_rate": subsystem.transformer_load_rate,
    }


def calc_hv_system_summary(hv_system: HVSystem) -> dict:
    """计算10kV高压系统汇总"""
    total_pc = hv_system.total_pc
    total_qc = hv_system.total_qc
    total_sc = hv_system.total_sc
    pf = hv_system.power_factor

    sub_details = []
    for sub in hv_system.subsystems:
        summary = calc_subsystem_summary(sub)
        sub_details.append({
            "name": sub.name,
            "summary": summary,
        })

    return {
        "total_pc": total_pc,
        "total_qc": total_qc,
        "total_sc": total_sc,
        "power_factor": pf,
        "subsystems": sub_details,
    }


def format_number(n: float, decimals: int = 2) -> str:
    """格式化数字显示"""
    return f"{n:,.{decimals}f}"
