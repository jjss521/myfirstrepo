# -*- coding: utf-8 -*-
"""数据模型定义"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


TRANSFORMER_OPERATION_MODES = ["同时运行", "一用一备", "两用一备", "三台同时运行"]

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
    name: str                           # 设备名称
    rated_power: float = 0.0            # 额定功率(kW)
    installed_count: int = 1            # 安装台数
    working_count: int = 1              # 工作台数
    kx: float = 0.8                     # 需要系数
    cos_phi: float = 0.8                # 功率因数
    tan_phi: float = 0.75               # tan值
    remark: str = ""                    # 备注
    is_subtotal: bool = False           # 是否为小计行
    comp_qc: float = 0.0                # 设备无功补偿率(kvar)
    load_level: str = "二级负荷"          # 负荷等级：二级负荷/三级负荷

    def __post_init__(self):
        """初始化后自动检测负荷等级"""
        if self.load_level == "二级负荷" and not self.is_subtotal:
            for kw in THIRD_LEVEL_KEYWORDS:
                if kw in self.name:
                    self.load_level = LOAD_LEVEL_TERTIARY
                    break

    @property
    def device_power(self) -> float:
        """设备功率 (额定功率 × 安装台数)"""
        return self.rated_power * self.installed_count if not self.is_subtotal else 0.0

    @property
    def pc(self) -> float:
        """有功计算功率 Pc = Pe × Kx"""
        return self.rated_power * self.working_count * self.kx

    @property
    def qc(self) -> float:
        """无功计算功率 Qc = max(0, Pc x tanφ - comp_qc)"""
        return max(0, self.pc * self.tan_phi - self.comp_qc)

    @property
    def sc(self) -> float:
        """视在功率 Sc = √(Pc² + Qc²)"""
        from math import sqrt
        return sqrt(self.pc ** 2 + self.qc ** 2)


@dataclass
class EquipmentGroup:
    """设备组（一个工艺单元内的设备集合）"""
    name: str                           # 设备组名称（如"1#生物池"）
    equipment_list: List[Equipment] = field(default_factory=list)
    kp: float = 1.0                     # 有功同时系数 K∑p（默认1.0，即不计同时系数）
    kq: float = 1.0                     # 无功同时系数 K∑q（默认1.0，即不计同时系数）

    def add_equipment(self, eq: Equipment):
        self.equipment_list.append(eq)

    @property
    def total_device_power(self) -> float:
        return sum(e.device_power for e in self.equipment_list if not e.is_subtotal)

    @property
    def subtotal_pc(self) -> float:
        """设备组计算有功小计"""
        return sum(e.pc for e in self.equipment_list if not e.is_subtotal)

    @property
    def subtotal_qc(self) -> float:
        """设备组计算无功小计"""
        return sum(e.qc for e in self.equipment_list if not e.is_subtotal)

    @property
    def subtotal_sc(self) -> float:
        from math import sqrt
        return sqrt(self.subtotal_pc ** 2 + self.subtotal_qc ** 2)

    @property
    def computed_pc(self) -> float:
        """计入同时系数后的有功功率"""
        return self.subtotal_pc * self.kp

    @property
    def computed_qc(self) -> float:
        """计入同时系数后的无功功率"""
        return self.subtotal_qc * self.kq

    @property
    def computed_sc(self) -> float:
        from math import sqrt
        return sqrt(self.computed_pc ** 2 + self.computed_qc ** 2)

    @property
    def power_factor(self) -> float:
        if self.computed_sc == 0:
            return 0.0
        return self.computed_pc / self.computed_sc


@dataclass
class Subsystem:
    """单个配电子系统（如 1#配电系统380V负荷）"""
    name: str                           # 系统名称
    groups: List[EquipmentGroup] = field(default_factory=list)
    voltage: VoltageLevel = VoltageLevel.LV_380V

    # 补偿参数
    compensation_qc: float = 0.0        # 电容器补偿容量(kvar)

    # 变压器参数
    transformer_rating: float = 0.0     # 单台变压器额定容量(kVA)
    transformer_count: int = 0          # 变压器台数
    transformer_operation_mode: str = "同时运行"  # 运行方式
    target_power_factor: float = 0.95   # 目标功率因数

    def add_group(self, group: EquipmentGroup):
        self.groups.append(group)

    @property
    def total_pc(self) -> float:
        """系统总有功功率"""
        return sum(g.computed_pc for g in self.groups)

    @property
    def total_qc(self) -> float:
        """系统总无功功率"""
        return sum(g.computed_qc for g in self.groups)

    @property
    def total_sc(self) -> float:
        from math import sqrt
        return sqrt(self.total_pc ** 2 + self.total_qc ** 2)

    @property
    def power_factor_before(self) -> float:
        """补偿前功率因数"""
        if self.total_sc == 0:
            return 0.0
        return self.total_pc / self.total_sc

    @property
    def compensated_pc(self) -> float:
        """补偿后有功功率（不变）"""
        return self.total_pc

    @property
    def compensated_qc(self) -> float:
        """补偿后无功功率"""
        return max(0, self.total_qc - self.compensation_qc)

    @property
    def compensated_sc(self) -> float:
        from math import sqrt
        return sqrt(self.compensated_pc ** 2 + self.compensated_qc ** 2)

    @property
    def power_factor_after(self) -> float:
        """补偿后功率因数"""
        if self.compensated_sc == 0:
            return 0.0
        return self.compensated_pc / self.compensated_sc

    @property
    def total_transformer_capacity(self) -> float:
        return self.transformer_rating * self.transformer_count

    @property
    def effective_transformer_capacity(self) -> float:
        """根据运行方式计算有效变压器容量"""
        if self.transformer_operation_mode == "同时运行":
            return self.transformer_rating * self.transformer_count
        elif self.transformer_operation_mode == "一用一备":
            return self.transformer_rating  # 只有1台运行
        elif self.transformer_operation_mode == "两用一备" and self.transformer_count >= 3:
            return self.transformer_rating * 2
        elif self.transformer_operation_mode == "三台同时运行" and self.transformer_count >= 3:
            return self.transformer_rating * self.transformer_count
        else:
            return self.transformer_rating * self.transformer_count

    @property
    def transformer_load_rate(self) -> float:
        """变压器负载率（使用有效容量）"""
        if self.effective_transformer_capacity == 0:
            return 0.0
        return self.compensated_sc / self.effective_transformer_capacity

    @property
    def transformer_loss_p(self) -> float:
        """变压器有功损耗（估算）"""
        return self.compensated_sc * 0.01

    @property
    def transformer_loss_q(self) -> float:
        """变压器无功损耗（估算）"""
        return self.compensated_sc * 0.05

    @property
    def hv_side_pc(self) -> float:
        """折算至10kV侧有功"""
        return self.compensated_pc + self.transformer_loss_p

    @property
    def hv_side_qc(self) -> float:
        """折算至10kV侧无功"""
        return self.compensated_qc + self.transformer_loss_q

    @property
    def hv_side_sc(self) -> float:
        from math import sqrt
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
        from math import sqrt
        return sqrt(self.total_pc ** 2 + self.total_qc ** 2)

    @property
    def power_factor(self) -> float:
        if self.total_sc == 0:
            return 0.0
        return self.total_pc / self.total_sc
