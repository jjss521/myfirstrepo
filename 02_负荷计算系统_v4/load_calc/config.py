# -*- coding: utf-8 -*-
"""全局配置和常量"""

import os
import sys

# 应用信息
APP_NAME = "污水厂负荷计算系统"
APP_VERSION = "4.0.0"
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
TARGET_POWER_FACTOR_DIST = 0.96

# 同时系数
SIMULTANEOUS_KP = 0.9
SIMULTANEOUS_KQ = 0.95

# 变压器损耗估算
TRANSFORMER_LOSS_P = 0.01
TRANSFORMER_LOSS_Q = 0.05

# 默认计算参数
DEFAULT_KX = 0.8
DEFAULT_COS_PHI = 0.8
DEFAULT_TAN_PHI = 0.75

# ═══════════════════════════════════════════════════════════════
# Apple 简约素雅高级风格 (Apple Light Elegant Theme)
# ═══════════════════════════════════════════════════════════════

TTK_THEME = "litera"  # ttkbootstrap 浅色基础主题

# 主色调 - Apple HIG 风格
THEME = {
    "BG_DARK":      "#E5E5EA",   # 最底层背景 (窗口底色)
    "BG_MAIN":      "#F2F2F7",   # 主背景 (Apple系统灰)
    "BG_CARD":      "#FFFFFF",   # 卡片/面板背景 (纯白)
    "BG_CARD_ALT":  "#F9F9FB",   # 卡片备选 (微灰)
    "BG_INPUT":     "#FFFFFF",   # 输入框背景
    "BG_HOVER":     "#E8E8ED",   # 悬停背景
    "BG_ACTIVE":    "#D1D1D6",   # 激活/选中背景
    "BG_NAV":       "#FFFFFF",   # 导航栏背景

    "FG_PRIMARY":   "#1C1C1E",   # 主文字 (近黑)
    "FG_SECONDARY": "#6E6E73",   # 次要文字
    "FG_MUTED":     "#AEAEB2",   # 弱化文字

    "ACCENT_CYAN":  "#5AC8FA",   # 辅助强调-青
    "ACCENT_BLUE":  "#007AFF",   # 主强调色-系统蓝
    "ACCENT_GREEN": "#34C759",   # 成功/达标
    "ACCENT_ORANGE":"#FF9500",   # 警告
    "ACCENT_RED":   "#FF3B30",   # 危险/未达标
    "ACCENT_PURPLE":"#AF52DE",   # 辅助强调-紫
    "ACCENT_TEAL":  "#5856D6",   # 辅助强调-靛

    "BORDER":       "#D1D1D6",   # 边框色
    "BORDER_GLOW":  "#007AFF22", # 聚焦边框
    "GLOW_CYAN":    "#5AC8FA",   # 辉光
    "SEPARATOR":    "#C6C6C8",   # 分隔线
}

# 兼容旧代码的 COLORS 字典
COLORS = {
    "PRIMARY":   THEME["ACCENT_BLUE"],
    "SUCCESS":   THEME["ACCENT_GREEN"],
    "WARNING":   THEME["ACCENT_ORANGE"],
    "DANGER":    THEME["ACCENT_RED"],
    "INFO":      THEME["ACCENT_CYAN"],
    "DARK":      THEME["BG_DARK"],
    "LIGHT":     THEME["FG_PRIMARY"],
    "WHITE":     "#FFFFFF",
}

SYSTEM_COLORS = {
    "10KV":       "#007AFF",
    "DIST1":      "#34C759",
    "DIST2":      "#FF9500",
    "BIOCHEM":    "#5AC8FA",
    "MBR":        "#AF52DE",
    "DEWATER":    "#8E8E93",
    "BLOWER":     "#FFCC00",
    "SEDIMENT":   "#30D158",
    "AUX":        "#636366",
    "WATER":      "#64D2FF",
    "MCR":        "#FF2D55",
    "PUMP":       "#5856D6",
}

# 饼图配色 - Apple 系统色
PIE_COLORS = [
    "#007AFF", "#FF9500", "#34C759", "#AF52DE", "#5AC8FA",
    "#FFCC00", "#FF3B30", "#5856D6", "#8E8E93", "#64D2FF",
    "#FF2D55", "#30D158", "#636366", "#00C7BE", "#FF6B35",
    "#28CD41", "#AEAEB2", "#BF5AF2", "#0A84FF", "#32D74B",
    "#AC8E68", "#00D4AA",
]


def hex_to_rgb(hex_color: str):
    """将 hex 颜色转为 (r, g, b) 元组"""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def blend_color(fg_hex: str, bg_hex: str, alpha: float) -> str:
    """模拟半透明叠加：fg 以 alpha 不透明度叠在 bg 上"""
    fg = hex_to_rgb(fg_hex)
    bg = hex_to_rgb(bg_hex)
    r = int(fg[0] * alpha + bg[0] * (1 - alpha))
    g = int(fg[1] * alpha + bg[1] * (1 - alpha))
    b = int(fg[2] * alpha + bg[2] * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"


# ═══════════════════════════════════════════════════════════════
# 字体配置 - Apple 风格字体系统（静态常量，无需 Tk 实例）
# ═══════════════════════════════════════════════════════════════

# UI 主字体：微软雅黑 UI 支持完整中文，Segoe UI 在 Tkinter 下无中文回退
FONT_UI = "Microsoft YaHei UI"
# 展示字体（大标题）
FONT_DISPLAY = "Microsoft YaHei UI"
# 等宽字体（Consolas 在所有 Windows 系统可用）
FONT_MONO = "Consolas"
# 图表字体（matplotlib 用）
FONT_CHART = "Microsoft YaHei"

# matplotlib 字体回退列表
MATPLOTLIB_FONT_FAMILY = [FONT_CHART, "SimHei", "Microsoft YaHei"]

# 字号映射（比原始尺寸统一缩小，更紧凑精致）
FS = {
    20: 16,    # 仪表盘大标题
    18: 14,    # 页面标题
    16: 13,    # 指标卡片数值
    15: 12,    # 应用标题
    14: 11,    # 对话框标题
    12: 10,    # 对话框副标题
    11: 9,     # 导航项 / 卡片标题
    10: 9,     # 正文 / 默认
    9:  8,     # 次要标签 / 表格
    8:  7,     # 提示 / 辅助
}


def apply_dark_theme(root):
    """为 ttkbootstrap 窗口应用 Apple 简约高级主题样式"""
    import ttkbootstrap as tb
    from ttkbootstrap import Style

    style = Style(theme=TTK_THEME)

    # ── Frame ──
    style.configure("TFrame", background=THEME["BG_MAIN"])
    style.configure("Card.TFrame", background=THEME["BG_CARD"])

    # ── Label ──
    style.configure("TLabel",
                     background=THEME["BG_MAIN"],
                     foreground=THEME["FG_PRIMARY"],
                     font=(FONT_UI, FS[10]))

    # ── Button ──
    style.configure("TButton",
                     background=THEME["BG_CARD"],
                     foreground=THEME["FG_PRIMARY"],
                     bordercolor=THEME["BORDER"],
                     focusthickness=0,
                     font=(FONT_UI, FS[10]))
    style.map("TButton",
              background=[("active", THEME["BG_HOVER"]),
                          ("pressed", THEME["BG_ACTIVE"])],
              foreground=[("active", THEME["ACCENT_BLUE"])])

    # 成功按钮
    style.configure("success.TButton",
                     background=blend_color(THEME["ACCENT_GREEN"], THEME["BG_CARD"], 0.15),
                     foreground=THEME["ACCENT_GREEN"],
                     bordercolor=blend_color(THEME["ACCENT_GREEN"], THEME["BORDER"], 0.4))
    style.map("success.TButton",
              background=[("active", blend_color(THEME["ACCENT_GREEN"], THEME["BG_HOVER"], 0.2))])

    # ── Entry ──
    style.configure("TEntry",
                     fieldbackground=THEME["BG_INPUT"],
                     foreground=THEME["FG_PRIMARY"],
                     bordercolor=THEME["BORDER"],
                     lightcolor=THEME["BORDER"],
                     darkcolor=THEME["BORDER"],
                     insertcolor=THEME["FG_PRIMARY"])
    style.map("TEntry",
              fieldbackground=[("focus", THEME["BG_CARD"])],
              bordercolor=[("focus", THEME["ACCENT_BLUE"])])

    # ── Combobox ──
    style.configure("TCombobox",
                     fieldbackground=THEME["BG_INPUT"],
                     foreground=THEME["FG_PRIMARY"],
                     bordercolor=THEME["BORDER"],
                     arrowcolor=THEME["FG_SECONDARY"])
    style.map("TCombobox",
              fieldbackground=[("readonly", THEME["BG_INPUT"]),
                               ("focus", THEME["BG_CARD"])],
              bordercolor=[("focus", THEME["ACCENT_BLUE"])])

    # ── Treeview ──
    style.configure("Treeview",
                     background=THEME["BG_CARD"],
                     foreground=THEME["FG_PRIMARY"],
                     fieldbackground=THEME["BG_CARD"],
                     bordercolor=THEME["BORDER"],
                     lightcolor=THEME["BORDER"],
                     darkcolor=THEME["BORDER"],
                     rowheight=26,
                     font=(FONT_UI, FS[9]))
    style.configure("Treeview.Heading",
                     background=THEME["BG_DARK"],
                     foreground=THEME["FG_SECONDARY"],
                     bordercolor=THEME["BORDER"],
                     font=(FONT_UI, FS[9], "bold"))
    style.map("Treeview",
              background=[("selected", blend_color(THEME["ACCENT_BLUE"], THEME["BG_CARD"], 0.12))],
              foreground=[("selected", THEME["ACCENT_BLUE"])])

    # ── Notebook ──
    style.configure("TNotebook",
                     background=THEME["BG_MAIN"],
                     bordercolor=THEME["BORDER"],
                     lightcolor=THEME["BORDER"],
                     darkcolor=THEME["BORDER"])
    style.configure("TNotebook.Tab",
                     background=THEME["BG_DARK"],
                     foreground=THEME["FG_SECONDARY"],
                     padding=(14, 7),
                     font=(FONT_UI, FS[9]))
    style.map("TNotebook.Tab",
              background=[("selected", THEME["BG_CARD"])],
              foreground=[("selected", THEME["ACCENT_BLUE"])],
              bordercolor=[("selected", THEME["ACCENT_BLUE"])])

    # ── Separator ──
    style.configure("TSeparator",
                     background=THEME["SEPARATOR"],
                     bordercolor=THEME["SEPARATOR"])

    # ── LabelFrame ──
    style.configure("TLabelframe",
                     background=THEME["BG_MAIN"],
                     foreground=THEME["FG_SECONDARY"],
                     bordercolor=THEME["BORDER"])
    style.configure("TLabelframe.Label",
                     background=THEME["BG_MAIN"],
                     foreground=THEME["ACCENT_BLUE"],
                     font=(FONT_UI, FS[9]))

    # ── PanedWindow ──
    style.configure("TPanedwindow",
                     background=THEME["BORDER"])

    # ── Scrollbar ──
    try:
        style.configure("TScrollbar",
                         background=THEME["BG_DARK"],
                         bordercolor=THEME["BORDER"],
                         arrowcolor=THEME["FG_SECONDARY"],
                         troughcolor=THEME["BG_MAIN"])
        style.map("TScrollbar",
                  background=[("active", THEME["BG_HOVER"]),
                              ("!active", THEME["BG_DARK"])])
    except Exception:
        pass  # ttkbootstrap may raise duplicate element error on some versions

    # ── Progressbar ──
    style.configure("TProgressbar",
                     background=THEME["ACCENT_BLUE"],
                     troughcolor=THEME["BG_DARK"],
                     bordercolor=THEME["BORDER"])

    return style

# 项目根目录（兼容 PyInstaller 打包和源码运行）
def _get_base_dir():
    """获取项目根目录，兼容 PyInstaller 打包环境"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，sys._MEIPASS 是临时解压目录
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = _get_base_dir()

# 数据目录
DATA_DIR = os.path.join(ROOT_DIR, "data")
PRESETS_DIR = os.path.join(DATA_DIR, "presets")
SAVES_DIR = os.path.join(DATA_DIR, "saves")

# Excel文件路径（原始数据）
EXCEL_PATH = os.path.join(ROOT_DIR, "load_calc.xls")

# 预设数据文件
DEFAULT_PROJECT_FILE = os.path.join(PRESETS_DIR, "default_project.json")

# 阀门功率映射文件
VALVE_POWER_MAP_FILE = os.path.join(PRESETS_DIR, "valve_power_map.json")

# 日志配置
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
