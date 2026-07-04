# -*- coding: utf-8 -*-
"""常用设备需要系数和功率因数参考数据库"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class KxReference:
    """需要系数参考值"""
    equipment_name: str
    kx_range: str
    cos_phi_range: str
    tan_phi_range: str
    kx_avg: float
    cos_phi_avg: float
    tan_phi_avg: float


def parse_range_range(r: str) -> Tuple[float, float]:
    """解析 '0.8~0.9' 格式的范围字符串"""
    parts = r.split("~")
    if len(parts) == 1:
        v = float(parts[0])
        return v, v
    return float(parts[0]), float(parts[1])


def parse_range_avg(r: str) -> float:
    """获取范围的中值"""
    lo, hi = parse_range_range(r)
    return (lo + hi) / 2


# ========== 标准需要系数参考表 ==========
STANDARD_KX_TABLE = [
    KxReference("取水泵和加压泵、污水提升泵",     "0.8~0.9",  "0.8~0.85", "0.75~0.62", 0.85, 0.83, 0.68),
    KxReference("搅拌机、吸刮泥机",               "0.8",      "0.8",      "0.75",      0.80, 0.80, 0.75),
    KxReference("投药机械",                       "0.5~0.7",  "0.8",      "0.75",      0.60, 0.80, 0.75),
    KxReference("冲洗泵",                         "0.5~0.7",  "0.8~0.85", "0.75~0.62", 0.60, 0.83, 0.68),
    KxReference("鼓风机、通风机",                 "0.7",      "0.8~0.85", "0.75~0.62", 0.70, 0.83, 0.68),
    KxReference("电动阀门",                       "0.2",      "0.8",      "0.75",      0.20, 0.80, 0.75),
    KxReference("真空泵",                         "0.5",      "0.8",      "0.75",      0.50, 0.80, 0.75),
    KxReference("起重机",                         "0.2",      "0.5",      "1.73",      0.20, 0.50, 1.73),
    KxReference("排水泵",                         "0.3",      "0.8",      "0.75",      0.30, 0.80, 0.75),
    KxReference("消毒设备(紫外线、加氯机)",       "0.8~0.9",  "0.5",      "1.73",      0.85, 0.50, 1.73),
    KxReference("格栅机、皮带机、压榨机",         "0.5~0.6",  "0.75",     "0.88",      0.55, 0.75, 0.88),
    KxReference("除臭设备",                       "0.6~0.7",  "0.8",      "0.75",      0.65, 0.80, 0.75),
    KxReference("化验室",                         "0.5",      "0.9",      "0.48",      0.50, 0.90, 0.48),
    KxReference("机械车间",                       "0.4",      "0.8",      "0.75",      0.40, 0.80, 0.75),
    KxReference("污泥脱水设备",                   "0.7",      "0.7~0.8", "0.8~0.75",  0.70, 0.75, 0.78),
    KxReference("污泥干化设备",                   "0.8",      "0.8~0.9", "0.48",      0.80, 0.85, 0.48),
    KxReference("干污泥输送设备",                 "0.6~0.7",  "0.8",      "0.75",      0.65, 0.80, 0.75),
    KxReference("计算机主机外部设备",             "0.4~0.5",  "0.5",      "1.73",      0.45, 0.50, 1.73),
    KxReference("各类仪表",                       "0.1~0.2",  "0.7",      "1.02",      0.15, 0.70, 1.02),
    KxReference("变配电所、厂房、综合楼照明",     "0.8~1",    "0.9",      "0.48",      0.90, 0.90, 0.48),
    KxReference("厂区照明",                       "0.9~1",    "0.9",      "0.48",      0.95, 0.90, 0.48),
    KxReference("MCR系统",                        "0.5~0.8",  "0.85~0.95", "0.62~0.33", 0.65, 0.90, 0.48),
    KxReference("Fenton系统",                     "0.7~0.8",  "0.85~0.95", "0.62~0.33", 0.75, 0.90, 0.48),
    KxReference("循环水泵",                       "0.8~0.9",  "0.8~0.85", "0.75~0.62", 0.85, 0.83, 0.68),
    KxReference("冷却风机",                       "0.7~0.8",  "0.8~0.85", "0.75~0.62", 0.75, 0.83, 0.68),
    KxReference("离心机",                         "0.7~0.8",  "0.8~0.85", "0.75~0.62", 0.75, 0.83, 0.68),
    KxReference("蒸发结晶系统",                   "0.8~1.0",  "0.8~0.85", "0.75~0.62", 0.90, 0.83, 0.68),
    KxReference("MCR系统水泵类",                  "0.5~0.8",  "0.85~0.95", "0.62~0.33", 0.65, 0.90, 0.48),
    KxReference("MCR系统搅拌机",                  "0.7~0.8",  "0.85",     "0.62",      0.75, 0.85, 0.62),
]


class KxDatabase:
    """需要系数数据库"""

    def __init__(self):
        self._table = {ref.equipment_name: ref for ref in STANDARD_KX_TABLE}

    @property
    def all_names(self) -> List[str]:
        return list(self._table.keys())

    def update(self, name: str, kx_range: str, cos_phi_range: str, tan_phi_range: str):
        """更新或添加Kx参考值"""
        def avg_of_range(r):
            parts = r.split("~")
            vals = [float(p.strip()) for p in parts]
            return sum(vals) / len(vals)
        kx_avg = avg_of_range(kx_range)
        cos_avg = avg_of_range(cos_phi_range)
        tan_avg = avg_of_range(tan_phi_range)
        self._table[name] = KxReference(
            equipment_name=name,
            kx_range=kx_range,
            cos_phi_range=cos_phi_range,
            tan_phi_range=tan_phi_range,
            kx_avg=kx_avg,
            cos_phi_avg=cos_avg,
            tan_phi_avg=tan_avg,
        )

    def fuzzy_search(self, keyword: str, top_n: int = 5) -> List[KxReference]:
        """模糊搜索，按匹配度排序"""
        keyword = keyword.lower()
        scored = []
        for ref in self._table.values():
            name_lower = ref.equipment_name.lower()
            if keyword in name_lower:
                score = 100 + len(keyword) / max(len(name_lower), 1)
            else:
                common = sum(1 for c in keyword if c in name_lower)
                if common == 0:
                    continue
                score = common / max(len(keyword), 1) * 50
            scored.append((score, ref))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ref for _, ref in scored[:top_n]]

    def search(self, keyword: str) -> List[KxReference]:
        """根据关键字搜索"""
        keyword = keyword.lower()
        return [ref for ref in self._table.values()
                if keyword in ref.equipment_name.lower()]

    def get(self, name: str) -> KxReference:
        return self._table.get(name)

    def suggest_kx(self, name: str) -> float:
        ref = self._table.get(name)
        return ref.kx_avg if ref else 0.8

    def suggest_cos_phi(self, name: str) -> float:
        ref = self._table.get(name)
        return ref.cos_phi_avg if ref else 0.8

    def suggest_tan_phi(self, name: str) -> float:
        ref = self._table.get(name)
        return ref.tan_phi_avg if ref else 0.75


# 全局单例
KX_DB = KxDatabase()
