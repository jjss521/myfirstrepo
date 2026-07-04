"""PyInstaller 专用入口 - 启动 PySide6 GUI"""
import os
import sys

# PyInstaller 打包后，确保路径正确
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    os.chdir(base_dir)
    sys.path.insert(0, base_dir)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_dir)

from gui_app_pyside6 import launch


if __name__ == "__main__":
    launch()
