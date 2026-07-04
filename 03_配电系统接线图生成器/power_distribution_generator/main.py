"""
配电系统图智能生成器 - 入口文件

参照《氛围化编程指令书_配电系统图生成器.md》第10章项目文件结构定义。

启动流程：
1. 确保sys.path正确（兼容各种启动方式）
2. 初始化日志系统
3. 创建QApplication
4. 初始化FloatingWindow悬浮窗
5. 自动尝试连接AutoCAD（后台监控）
6. 加载示例Excel数据（如存在）
7. 进入事件循环

用法：
    python main.py                  # 启动GUI
    python main.py --cli <excel>    # CLI模式测试读取
"""

import sys
import os
import logging
import argparse

# 确保项目根目录（power_distribution_generator/）在 sys.path 中
# 这样所有裸导入（from models import ...）和包导入（from ui.xxx import ...）都能正常工作
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
if _PACKAGE_DIR not in sys.path:
    sys.path.insert(0, _PACKAGE_DIR)


def _setup_logging():
    """配置日志系统

    输出到控制台，级别INFO，方便诊断CAD连接和计算问题。
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.floating_window import FloatingWindow
from excel_reader import read_panel_from_excel, print_panel_data


def run_cli(excel_path: str):
    """命令行模式：读取Excel并打印结果

    参照《氛围化编程指令书_配电系统图生成器.md》阶段1。
    """
    panels = read_panel_from_excel(excel_path)
    if panels:
        print_panel_data(panels)
    else:
        print("未读取到有效数据，请检查Excel格式。")
        print("工作要求：存在'低压配电系统'工作表，"
              "行2开始依次为开关柜编号、柜型、尺寸等属性。")
    return 0


def run_gui():
    """GUI模式：启动悬浮窗界面"""
    # 初始化日志（必须在导入PySide6之后，确保所有模块的logger生效）
    _setup_logging()

    # 高DPI缩放支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 创建悬浮窗
    window = FloatingWindow()
    window.show()

    sys.exit(app.exec())


def main():
    parser = argparse.ArgumentParser(
        description="配电系统图智能生成器 "
                    "（《氛围化编程指令书_配电系统图生成器.md》）"
    )
    parser.add_argument(
        "--cli", metavar="EXCEL_PATH", type=str,
        help="CLI模式：读取Excel并打印解析结果"
    )
    parser.add_argument(
        "--excel", metavar="EXCEL_PATH", type=str,
        help="GUI模式：指定启动时加载的Excel文件"
    )

    args = parser.parse_args()

    if args.cli:
        return run_cli(args.cli)
    else:
        run_gui()


if __name__ == "__main__":
    main()
