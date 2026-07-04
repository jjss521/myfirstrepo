"""PDSG 图块编辑器 — 独立启动脚本

用法:
    python run_block_editor.py
"""
import logging
import os
import sys

# 确保项目根目录在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# 启动图块编辑器
from block_editor_gui import launch_block_editor

if __name__ == "__main__":
    launch_block_editor()
