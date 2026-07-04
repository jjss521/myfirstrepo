# -*- coding: utf-8 -*-
"""数据持久化 — JSON格式存储（替代pickle，安全可读）"""

import json
import os
import logging

from .config import SAVES_DIR
from .models import Equipment, EquipmentGroup, Subsystem, HVSystem, VoltageLevel

logger = logging.getLogger(__name__)

SAVE_FILE = os.path.join(SAVES_DIR, "project_data.json")


def _ensure_saves_dir():
    """确保保存目录存在"""
    os.makedirs(SAVES_DIR, exist_ok=True)


def _equipment_to_dict(eq: Equipment) -> dict:
    return {
        "name": eq.name,
        "rated_power": eq.rated_power,
        "installed_count": eq.installed_count,
        "working_count": eq.working_count,
        "kx": eq.kx,
        "cos_phi": eq.cos_phi,
        "tan_phi": eq.tan_phi,
        "remark": eq.remark,
        "is_subtotal": eq.is_subtotal,
        "comp_qc": eq.comp_qc,
        "load_level": eq.load_level,
    }


def _dict_to_equipment(d: dict) -> Equipment:
    return Equipment(
        name=d.get("name", ""),
        rated_power=d.get("rated_power", 0.0),
        installed_count=d.get("installed_count", 1),
        working_count=d.get("working_count", 1),
        kx=d.get("kx", 0.8),
        cos_phi=d.get("cos_phi", 0.8),
        tan_phi=d.get("tan_phi", 0.75),
        remark=d.get("remark", ""),
        is_subtotal=d.get("is_subtotal", False),
        comp_qc=d.get("comp_qc", 0.0),
        load_level=d.get("load_level", "二级负荷"),
    )


def _group_to_dict(g: EquipmentGroup) -> dict:
    return {
        "name": g.name,
        "kp": g.kp,
        "kq": g.kq,
        "equipment_list": [_equipment_to_dict(e) for e in g.equipment_list],
    }


def _dict_to_group(d: dict) -> EquipmentGroup:
    return EquipmentGroup(
        name=d.get("name", ""),
        kp=d.get("kp", 1.0),
        kq=d.get("kq", 1.0),
        equipment_list=[_dict_to_equipment(e) for e in d.get("equipment_list", [])],
    )


def _subsystem_to_dict(sub: Subsystem) -> dict:
    return {
        "name": sub.name,
        "voltage": sub.voltage.value,
        "compensation_qc": sub.compensation_qc,
        "transformer_rating": sub.transformer_rating,
        "transformer_count": sub.transformer_count,
        "transformer_operation_mode": sub.transformer_operation_mode,
        "target_power_factor": sub.target_power_factor,
        "groups": [_group_to_dict(g) for g in sub.groups],
    }


def _dict_to_subsystem(d: dict) -> Subsystem:
    voltage_str = d.get("voltage", "0.4kV")
    try:
        voltage = next(v for v in VoltageLevel if v.value == voltage_str)
    except StopIteration:
        voltage = VoltageLevel.LV_380V

    return Subsystem(
        name=d.get("name", ""),
        voltage=voltage,
        compensation_qc=d.get("compensation_qc", 0.0),
        transformer_rating=d.get("transformer_rating", 0.0),
        transformer_count=d.get("transformer_count", 0),
        transformer_operation_mode=d.get("transformer_operation_mode", "同时运行"),
        target_power_factor=d.get("target_power_factor", 0.95),
        groups=[_dict_to_group(g) for g in d.get("groups", [])],
    )


def hvsystem_to_dict(hv: HVSystem) -> dict:
    return {
        "name": hv.name,
        "subsystems": [_subsystem_to_dict(s) for s in hv.subsystems],
    }


def dict_to_hvsystem(d: dict) -> HVSystem:
    return HVSystem(
        name=d.get("name", "二期全厂10KV负荷"),
        subsystems=[_dict_to_subsystem(s) for s in d.get("subsystems", [])],
    )


def save_data(hv_system: HVSystem) -> bool:
    """保存HVSystem数据到JSON文件"""
    _ensure_saves_dir()
    try:
        data = hvsystem_to_dict(hv_system)
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存: {SAVE_FILE}")
        return True
    except Exception as e:
        logger.exception(f"保存数据失败: {e}")
        return False


def load_data() -> HVSystem:
    """从JSON文件加载HVSystem数据，失败返回None"""
    if not os.path.exists(SAVE_FILE):
        logger.info("无保存数据，使用预设数据")
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        hv = dict_to_hvsystem(data)
        logger.info(f"数据已加载: {SAVE_FILE}")
        return hv
    except Exception as e:
        logger.exception(f"加载数据失败: {e}")
        return None


def load_preset(preset_path: str = None) -> HVSystem:
    """从预设JSON文件加载数据"""
    from .config import DEFAULT_PROJECT_FILE
    path = preset_path or DEFAULT_PROJECT_FILE
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        hv = dict_to_hvsystem(data)
        logger.info(f"预设数据已加载: {path}")
        return hv
    except FileNotFoundError:
        logger.error(f"预设文件不存在: {path}")
        return None
    except Exception as e:
        logger.exception(f"加载预设数据失败: {e}")
        return None


def clear_saved_data():
    """删除保存的数据文件"""
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
            logger.info(f"已删除: {SAVE_FILE}")
    except Exception as e:
        logger.warning(f"删除失败: {e}")
