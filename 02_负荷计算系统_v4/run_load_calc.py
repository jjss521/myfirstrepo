# -*- coding: utf-8 -*-
"""污水厂负荷计算程序 - 入口点"""

import sys
import os
import logging

# 确保可以导入 load_calc 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_calc.main_window import MainWindow
from load_calc.config import APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)


def main():
    print("=" * 50)
    print(f"  {APP_NAME} v{APP_VERSION}")
    print("  Wastewater Treatment Plant Load Calculation")
    print("  JSON持久化 · logging日志 · 标准化项目结构")
    print("=" * 50)
    print()

    logger.info("正在启动...")
    app = MainWindow()
    print("启动界面...")
    app.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        # 写入崩溃日志
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
        print(f"\n程序崩溃！错误已写入: {log_path}")
        print(error_msg)
        input("按回车键退出...")
