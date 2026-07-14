"""配置文件"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据库配置
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'app.db')}"

# 文件存储
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
RULES_DIR = os.path.join(BASE_DIR, 'data', 'rules')

# 规范深度要求JSON种子文件
RULES_FILES = {
    'water_supply': os.path.join(RULES_DIR, 'water_supply.json'),
    'drainage': os.path.join(RULES_DIR, 'drainage.json'),
    'road': os.path.join(RULES_DIR, 'road.json'),
    'sanitation': os.path.join(RULES_DIR, 'sanitation.json'),
}

# 支持的上传文件类型
ALLOWED_DOC_EXTENSIONS = {'.docx', '.doc', '.xlsx', '.xls', '.pdf', '.txt', '.csv'}

# 设计阶段
DESIGN_STAGES = ['可研', '初步设计', '施工图']

# 工程类型映射
PROJECT_TYPES = {
    'water_supply': '给水工程',
    'drainage': '排水工程',
    'road': '道路交通工程',
    'sanitation': '环境卫生工程',
}
