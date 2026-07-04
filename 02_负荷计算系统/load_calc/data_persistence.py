# -*- coding: utf-8 -*-
"""数据持久化 - 保存/加载运行时数据"""

import os
import pickle

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_data.pkl")


def save_data(hv_system):
    """保存HVSystem数据到文件"""
    try:
        with open(SAVE_FILE, "wb") as f:
            pickle.dump(hv_system, f, protocol=pickle.HIGHEST_PROTOCOL)
        return True
    except Exception as e:
        print(f"保存数据失败: {e}")
        return False


def load_data():
    """从文件加载HVSystem数据，失败返回None"""
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None


def clear_saved_data():
    """删除保存的数据文件"""
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
    except Exception:
        pass
