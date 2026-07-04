# -*- coding: utf-8 -*-
"""全局配置和常量"""

import os

# 应用信息
APP_NAME = "污水厂负荷计算系统"
APP_VERSION = "3.0.0"
APP_SUBTITLE = "Wastewater Treatment Plant Load Calculation System"

# 基础电压等级
VOLTAGE_LEVELS = {
    "10KV_SYSTEM": "10kV",
    "380V_SYSTEM": "0.4kV",
    "220V_SYSTEM": "220V",
}

# 配电系统名称
DISTRIBUTION_SYSTEMS = {
    "DIST1": "水厂二期1#配电系统380V负荷",
    "DIST2": "水厂二期2#配电系统(蒸发系统)380V负荷",
    "10KV_SYSTEM": "二期全厂10KV负荷",
}

# 功率因数目标值
TARGET_POWER_FACTOR = 0.95
TARGET_POWER_FACTOR_DIST = 0.96  # 蒸发系统目标功率因数

# 同时系数
SIMULTANEOUS_KP = 0.9  # 有功同时系数
SIMULTANEOUS_KQ = 0.95  # 无功同时系数

# 变压器损耗估算
TRANSFORMER_LOSS_P = 0.01  # 有功损耗系数 (1%)
TRANSFORMER_LOSS_Q = 0.05  # 无功损耗系数 (5%)

# 默认计算参数
DEFAULT_KX = 0.8
DEFAULT_COS_PHI = 0.8
DEFAULT_TAN_PHI = 0.75

# 颜色方案
COLORS = {
    "PRIMARY": "#2196F3",
    "SUCCESS": "#4CAF50",
    "WARNING": "#FF9800",
    "DANGER": "#F44336",
    "INFO": "#00BCD4",
    "DARK": "#263238",
    "LIGHT": "#ECEFF1",
    "WHITE": "#FFFFFF",
}

SYSTEM_COLORS = {
    "10KV": "#1565C0",
    "DIST1": "#2E7D32",
    "DIST2": "#E65100",
    "BIOCHEM": "#00838F",
    "MBR": "#6A1B9A",
    "DEWATER": "#4E342E",
    "BLOWER": "#F57F17",
    "SEDIMENT": "#1B5E20",
    "AUX": "#37474F",
    "WATER": "#00695C",
    "MCR": "#AD1457",
    "PUMP": "#283593",
}

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Excel文件路径（原始数据）
EXCEL_PATH = os.path.join(os.path.dirname(ROOT_DIR), "load_calc.xls")
