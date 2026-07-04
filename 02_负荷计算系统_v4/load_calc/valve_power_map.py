# -*- coding: utf-8 -*-
"""阀门功率映射模块 - 根据阀门类型和公称通径(DN)推断电机功率"""

import json
import os
import re
import logging

from .config import VALVE_POWER_MAP_FILE

logger = logging.getLogger(__name__)

# 支持的阀门关键词（匹配时忽略空格、大小写）
VALVE_KEYWORDS = [
    "电动蝶阀",
    "电动闸阀",
    "电动调节阀",
    "电动阀门",
]


def normalize_valve_type(name: str) -> str:
    """归一化阀门类型名称：去空格、转小写"""
    return name.replace(" ", "").replace("　", "").lower()


def parse_dn_from_text(text: str):
    """从文本中提取公称通径 DN 数值（整数）

    支持格式：DN100、DN 100、100mm、公称通径100 等
    返回 int 或 None
    """
    if not text:
        return None
    try:
        # 1) 匹配 "DNxxx" 格式（允许 DN 后有空格、冒号等）
        m = re.search(r'[Dd][Nn]\s*[:：=]?\s*(\d+)', text)
        if m:
            return int(m.group(1))
        # 2) 匹配 "xxxmm" 格式
        m = re.search(r'(\d+)\s*mm', text, re.IGNORECASE)
        if m:
            return int(m.group(1))
        # 3) 匹配 "公称通径 xxx" 格式
        m = re.search(r'公称通径\s*[:：=]?\s*(\d+)', text)
        if m:
            return int(m.group(1))
        # 4) 兜底：匹配独立的数字（如规格列仅写"100"），在阀门上下文中可能是DN
        # 但此匹配太宽泛，仅在阀门已确认时才用，这里不单独使用
    except (ValueError, TypeError):
        pass
    return None


def identify_valve_type(equip_name: str):
    """检查设备名称是否包含阀门关键词，返回匹配到的阀门类型（归一化后）

    返回 (原始关键词, 归一化后类型名) 或 (None, None)
    """
    if not equip_name:
        return None, None
    norm_name = normalize_valve_type(equip_name)
    for kw in VALVE_KEYWORDS:
        norm_kw = normalize_valve_type(kw)
        if norm_kw in norm_name:
            return kw, norm_kw
    return None, None


class ValvePowerDB:
    """阀门功率映射数据库 — 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}  # {valve_type_norm: {dn: power}}
            cls._instance._loaded = False
        return cls._instance

    def _ensure_loaded(self):
        """确保数据已加载（延迟加载）"""
        if not self._loaded:
            self.load()

    def load(self) -> bool:
        """从 JSON 文件加载阀门功率映射表"""
        if not os.path.exists(VALVE_POWER_MAP_FILE):
            logger.info(f"阀门功率映射文件不存在: {VALVE_POWER_MAP_FILE}")
            self._loaded = True
            return False
        try:
            with open(VALVE_POWER_MAP_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # raw 格式: {"电动蝶阀": [{"dn": 50, "power": 0.06}, ...], ...}
            self._data = {}
            for valve_type, entries in raw.items():
                norm_type = normalize_valve_type(valve_type)
                self._data[norm_type] = {}
                for entry in entries:
                    self._data[norm_type][entry["dn"]] = entry["power"]
            self._loaded = True
            logger.info(f"阀门功率映射已加载，共 {sum(len(v) for v in self._data.values())} 条记录")
            return True
        except Exception as e:
            logger.exception(f"加载阀门功率映射失败: {e}")
            self._loaded = True
            return False

    def save(self) -> bool:
        """保存阀门功率映射表到 JSON 文件"""
        try:
            out = {}
            # 找到原始关键词（从 VALVE_KEYWORDS 反查）
            norm_to_original = {}
            for kw in VALVE_KEYWORDS:
                norm_to_original[normalize_valve_type(kw)] = kw
            # 也记录所有实际存储的类型
            for kw in VALVE_KEYWORDS:
                norm_to_original[normalize_valve_type(kw)] = kw

            for norm_type, dns in self._data.items():
                # 尝试找原始名称
                display_name = norm_to_original.get(norm_type, norm_type)
                entries = [{"dn": dn, "power": power} for dn, power in sorted(dns.items())]
                out[display_name] = entries

            os.makedirs(os.path.dirname(VALVE_POWER_MAP_FILE), exist_ok=True)
            with open(VALVE_POWER_MAP_FILE, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            logger.info(f"阀门功率映射已保存: {VALVE_POWER_MAP_FILE}")
            return True
        except Exception as e:
            logger.exception(f"保存阀门功率映射失败: {e}")
            return False

    def query(self, valve_type_norm: str, dn: int):
        """查询指定阀门类型和DN的电机功率(kW)，未找到返回None"""
        self._ensure_loaded()
        dns = self._data.get(valve_type_norm, {})
        # 精确匹配
        if dn in dns:
            return dns[dn]
        # 近似匹配：找最接近的DN（允许±10mm容差）
        if dns:
            closest = min(dns.keys(), key=lambda x: abs(x - dn))
            if abs(closest - dn) <= 10:
                logger.info(f"阀门DN近似匹配: DN{dn} -> DN{closest} ({dns[closest]}kW)")
                return dns[closest]
        return None

    def get_all(self):
        """获取所有阀门功率条目，返回列表 [{valve_type, dn, power}, ...]"""
        self._ensure_loaded()
        result = []
        for norm_type, dns in self._data.items():
            for dn, power in sorted(dns.items()):
                result.append({"valve_type": norm_type, "dn": dn, "power": power})
        return result

    def add(self, valve_type_norm: str, dn: int, power: float):
        """添加或更新一条映射"""
        self._ensure_loaded()
        if valve_type_norm not in self._data:
            self._data[valve_type_norm] = {}
        self._data[valve_type_norm][dn] = power
        return self.save()

    def update(self, valve_type_norm: str, old_dn: int, new_dn: int, new_power: float):
        """更新一条映射（可能修改DN和power）"""
        self._ensure_loaded()
        if valve_type_norm in self._data and old_dn in self._data[valve_type_norm]:
            del self._data[valve_type_norm][old_dn]
        if valve_type_norm not in self._data:
            self._data[valve_type_norm] = {}
        self._data[valve_type_norm][new_dn] = new_power
        return self.save()

    def delete(self, valve_type_norm: str, dn: int) -> bool:
        """删除一条映射"""
        self._ensure_loaded()
        if valve_type_norm in self._data and dn in self._data[valve_type_norm]:
            del self._data[valve_type_norm][dn]
            if not self._data[valve_type_norm]:
                del self._data[valve_type_norm]
            return self.save()
        return False

    def get_valve_types(self):
        """获取所有已存储的阀门类型列表（归一化名称）"""
        self._ensure_loaded()
        return list(self._data.keys())


# 全局单例
VALVE_DB = ValvePowerDB()


def infer_valve_power(equip_name: str, spec_text: str = ""):
    """智能推断阀门功率：识别阀门类型 -> 提取DN -> 查表返回功率(kW)

    返回 float 或 None
    """
    if not equip_name:
        return None

    # 1) 识别阀门类型
    orig_keyword, norm_type = identify_valve_type(equip_name)
    if not norm_type:
        return None

    # 2) 提取 DN：优先从规格列，其次从设备名称
    dn = None
    if spec_text:
        dn = parse_dn_from_text(spec_text)
    if dn is None:
        dn = parse_dn_from_text(equip_name)

    if dn is None:
        logger.debug(f"阀门「{equip_name}」未提取到DN，无法推断功率")
        return None

    # 3) 查表
    power = VALVE_DB.query(norm_type, dn)
    if power is not None:
        logger.info(f"阀门功率推断: {equip_name} (DN{dn}) -> {power}kW")
    else:
        logger.debug(f"阀门「{equip_name}」(DN{dn}) 在映射表中未找到匹配")
    return power
