# -*- coding: utf-8 -*-
"""预设数据加载器 - 从JSON文件加载预设设备数据"""

import logging

from .models import HVSystem
from . import data_persistence


logger = logging.getLogger(__name__)


def build_project_data() -> HVSystem:
    """从预设JSON文件构建完整的项目数据"""
    logger.info("加载预设数据...")
    hv = data_persistence.load_preset()
    if hv is None:
        logger.warning("预设数据加载失败，返回空系统")
        hv = HVSystem("二期全厂10KV负荷")
    return hv
