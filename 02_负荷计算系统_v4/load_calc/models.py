# -*- coding: utf-8 -*-
"""数据模型定义"""

from math import sqrt
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


TRANSFORMER_OPERATION_MODES = ["同时运行", "一用一备", "两用一备", "三台同时运行"]

# 变压器标准容量档位 (IEC 60076, kVA)
TRANSFORMER_GRADES = [
    50, 63, 80, 100, 125, 160, 200, 250, 315, 400,
    500, 630, 800, 1000, 1250, 1600, 2000, 2500
]

# 负荷等级
LOAD_LEVEL_SECONDARY = "二级负荷"
LOAD_LEVEL_TERTIARY = "三级负荷"
LOAD_LEVEL_CHOICES = [LOAD_LEVEL_SECONDARY, LOAD_LEVEL_TERTIARY]

# 三级负荷自动识别关键词
THIRD_LEVEL_KEYWORDS = ["照明", "吊车", "行车", "空调", "暖通", "插座"]


class VoltageLevel(Enum):
    """电压等级"""
    HV_10KV = "10kV"
    LV_380V = "0.4kV"
    LV_220V = "220V"


@dataclass
class Equipment:
    """单个用电设备"""
    name: str
    rated_power: float = 0.0
    installed_count: int = 1
    working_count: int = 1
    kx: float = 0.8
    cos_phi: float = 0.8
    tan_phi: float = 0.75
    remark: str = ""
    is_subtotal: bool = False
    comp_qc: float = 0.0
    load_level: str = "二级负荷"

    def __post_init__(self):
        """初始化后自动检测负荷等级"""
        if self.load_level == "二级负荷" and not self.is_subtotal:
            for kw in THIRD_LEVEL_KEYWORDS:
                if kw in self.name:
                    self.load_level = LOAD_LEVEL_TERTIARY
                    break

    @property
    def device_power(self) -> float:
        return self.rated_power * self.installed_count if not self.is_subtotal else 0.0

    @property
    def pc(self) -> float:
        return self.rated_power * self.working_count * self.kx

    @property
    def qc(self) -> float:
        return max(0, self.pc * self.tan_phi - self.comp_qc)

    @property
    def sc(self) -> float:
        return sqrt(self.pc ** 2 + self.qc ** 2)


@dataclass
class EquipmentGroup:
    """设备组（一个工艺单元内的设备集合）"""
    name: str
    equipment_list: List[Equipment] = field(default_factory=list)
    kp: float = 1.0
    kq: float = 1.0

    def add_equipment(self, eq: Equipment):
        self.equipment_list.append(eq)

    @property
    def total_device_power(self) -> float:
        return sum(e.device_power for e in self.equipment_list if not e.is_subtotal)

    @property
    def subtotal_pc(self) -> float:
        return sum(e.pc for e in self.equipment_list if not e.is_subtotal)

    @property
    def subtotal_qc(self) -> float:
        return sum(e.qc for e in self.equipment_list if not e.is_subtotal)

    @property
    def subtotal_sc(self) -> float:
        return sqrt(self.subtotal_pc ** 2 + self.subtotal_qc ** 2)

    @property
    def computed_pc(self) -> float:
        return self.subtotal_pc * self.kp

    @property
    def computed_qc(self) -> float:
        return self.subtotal_qc * self.kq

    @property
    def computed_sc(self) -> float:
        return sqrt(self.computed_pc ** 2 + self.computed_qc ** 2)

    @property
    def power_factor(self) -> float:
        if self.computed_sc == 0:
            return 0.0
        return self.computed_pc / self.computed_sc


@dataclass
class Subsystem:
    """单个配电子系统"""
    name: str
    groups: List[EquipmentGroup] = field(default_factory=list)
    voltage: VoltageLevel = VoltageLevel.LV_380V
    compensation_qc: float = 0.0
    transformer_rating: float = 0.0
    transformer_count: int = 0
    transformer_operation_mode: str = "同时运行"
    target_power_factor: float = 0.95

    def add_group(self, group: EquipmentGroup):
        self.groups.append(group)

    @property
    def total_pc(self) -> float:
        return sum(g.computed_pc for g in self.groups)

    @property
    def total_qc(self) -> float:
        return sum(g.computed_qc for g in self.groups)

    @property
    def total_sc(self) -> float:
        return sqrt(self.total_pc ** 2 + self.total_qc ** 2)

    @property
    def power_factor_before(self) -> float:
        if self.total_sc == 0:
            return 0.0
        return self.total_pc / self.total_sc

    @property
    def compensated_pc(self) -> float:
        return self.total_pc

    @property
    def compensated_qc(self) -> float:
        return max(0, self.total_qc - self.compensation_qc)

    @property
    def compensated_sc(self) -> float:
        return sqrt(self.compensated_pc ** 2 + self.compensated_qc ** 2)

    @property
    def power_factor_after(self) -> float:
        if self.compensated_sc == 0:
            return 0.0
        return self.compensated_pc / self.compensated_sc

    @property
    def total_transformer_capacity(self) -> float:
        return self.transformer_rating * self.transformer_count

    @property
    def effective_transformer_capacity(self) -> float:
        if self.transformer_operation_mode == "同时运行":
            return self.transformer_rating * self.transformer_count
        elif self.transformer_operation_mode == "一用一备":
            return self.transformer_rating
        elif self.transformer_operation_mode == "两用一备" and self.transformer_count >= 3:
            return self.transformer_rating * 2
        elif self.transformer_operation_mode == "三台同时运行" and self.transformer_count >= 3:
            return self.transformer_rating * self.transformer_count
        else:
            return self.transformer_rating * self.transformer_count

    @property
    def transformer_load_rate(self) -> float:
        if self.effective_transformer_capacity == 0:
            return 0.0
        return self.compensated_sc / self.effective_transformer_capacity

    @property
    def transformer_loss_p(self) -> float:
        return self.compensated_sc * 0.01

    @property
    def transformer_loss_q(self) -> float:
        return self.compensated_sc * 0.05

    @property
    def hv_side_pc(self) -> float:
        return self.compensated_pc + self.transformer_loss_p

    @property
    def hv_side_qc(self) -> float:
        return self.compensated_qc + self.transformer_loss_q

    @property
    def hv_side_sc(self) -> float:
        return sqrt(self.hv_side_pc ** 2 + self.hv_side_qc ** 2)

    @property
    def hv_side_pf(self) -> float:
        if self.hv_side_sc == 0:
            return 0.0
        return self.hv_side_pc / self.hv_side_sc


@dataclass
class HVSystem:
    """10kV高压系统（全厂汇总）"""
    name: str = "二期全厂10KV负荷"
    subsystems: List[Subsystem] = field(default_factory=list)

    def add_subsystem(self, sub: Subsystem):
        self.subsystems.append(sub)

    @property
    def total_pc(self) -> float:
        return sum(s.hv_side_pc for s in self.subsystems)

    @property
    def total_qc(self) -> float:
        return sum(s.hv_side_qc for s in self.subsystems)

    @property
    def total_sc(self) -> float:
        return sqrt(self.total_pc ** 2 + self.total_qc ** 2)

    @property
    def power_factor(self) -> float:
        if self.total_sc == 0:
            return 0.0
        return self.total_pc / self.total_sc
