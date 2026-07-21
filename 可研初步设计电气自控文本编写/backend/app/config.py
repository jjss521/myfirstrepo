# -*- coding: utf-8 -*-
"""全局配置：路径与常量。"""
import os

# 项目根目录：本文件位于 backend/app/config.py，向上三级为项目根
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RULES_DIR = os.path.join(BASE_DIR, 'backend', 'data', 'rules')
OUTPUT_DIR = os.path.join(BASE_DIR, 'backend', 'output', 'generated')
UPLOAD_DIR = os.path.join(BASE_DIR, 'backend', 'uploads')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'backend', 'data', 'templates')
DB_PATH = os.path.join(BASE_DIR, 'backend', 'data', 'app.db')

os.makedirs(RULES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# 四种工程类型代码
PROJECT_TYPES = {
    'water_supply': '给水工程',
    'drainage': '排水工程',
    'road': '道路交通工程',
    'sanitation': '环境卫生工程',
}

# 设计阶段（中文） -> rules 文件名后缀
STAGE_CODE = {
    '初步设计': 'preliminary',
    '可研': 'feasibility',
}

# 四种 Word 模板
DOC_TEMPLATES = ['standard', 'compact', 'report', 'modern']
