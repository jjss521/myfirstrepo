# -*- coding: utf-8 -*-
"""污水厂负荷计算程序 - 入口点"""

import sys
import os

# 确保可以导入 load_calc 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_calc.main_window import MainWindow


def main():
    print("=" * 50)
    print("  污水厂负荷计算系统 v3.0")
    print("  Wastewater Treatment Plant Load Calculation")
    print("=" * 50)
    print()
    print("正在加载数据...")

    app = MainWindow()
    print("启动界面...")
    app.run()


if __name__ == "__main__":
    main()
