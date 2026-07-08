#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS 风格配色方案 — Big Sur / Ventura 风格
"""


class MacColors:
    """macOS Big Sur / Ventura 风格配色"""
    # ── 主色调 ──
    BG = "#F5F5F7"              # 窗口背景
    CONTROL_BG = "#F0F0F3"      # 控件背景
    SIDEBAR_BG = "#E8E8ED"      # 侧边栏背景
    CARD_BG = "#FFFFFF"         # 卡片背景
    TITLEBAR_BG = "#F5F5F7"     # 标题栏背景

    # ── 交互状态 ──
    SELECTED_BG = "#E3F2FD"     # 选中/高亮背景
    HOVER_BG = "#EBEBF0"        # 悬停背景

    # ── 强调色 ──
    ACCENT = "#007AFF"          # macOS 蓝色
    ACCENT_HOVER = "#0056CC"    # 深蓝悬停

    # ── 语义色 ──
    SUCCESS = "#34C759"         # 绿色
    WARNING = "#FF9500"         # 橙色
    DANGER = "#FF3B30"          # 红色

    # ── 文字层级 ──
    TEXT_PRIMARY = "#1D1D1F"    # 主文字 (近黑)
    TEXT_SECONDARY = "#86868B"  # 次文字 (灰)
    TEXT_TERTIARY = "#AEAEB2"   # 三级文字 (浅灰)

    # ── 边框与分隔 ──
    BORDER = "#D2D2D7"          # 边框
    SEPARATOR = "#C6C6C8"       # 分隔线
    HIGHLIGHT = "#E3F2FD"       # 高亮背景
    SUBTLE_BORDER = "#E5E5E7"   # 细分隔线

    # ── 标题栏 ──
    TITLEBAR_HEIGHT = 38        # 标题栏高度

    # ── 阴影 ──
    SHADOW_LIGHT = "#00000010"  # 浅阴影
    SHADOW_DARK = "#00000020"   # 深阴影

    # ── 字体族 ──
    FONT_FAMILY = (".AppleSystemUIFont", "SF Pro Text", "Helvetica Neue", "Segoe UI")

    # ── 交通灯按钮颜色 ──
    TRAFFIC_CLOSE = "#FF5F57"   # 红 (关闭)
    TRAFFIC_MINIMIZE = "#FEBC2E"  # 黄 (最小化)
    TRAFFIC_MAXIMIZE = "#28C840"  # 绿 (最大化)

    # ── 章节颜色 ──
    CH1 = "#FF6B6B"  # 向量 - 红
    CH2 = "#4ECDC4"  # 曲面 - 青
    CH3 = "#45B7D1"  # 直线平面 - 蓝
    CH4 = "#96CEB4"  # 极限 - 绿
    CH5 = "#FFEAA7"  # 导数 - 黄
    CH6 = "#DDA0DD"  # 多元 - 紫
    CH7 = "#98D8C8"  # 应用 - 薄荷
    CH8 = "#F7DC6F"  # 练习 - 金
