#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式数学教学程序 - Mac 风格 GUI 版本
空间解析几何 & 微分学
"""
import sys
import os
import math

sys.stdout.reconfigure(encoding='utf-8')

try:
    import customtkinter as ctk
    from customtkinter import CTk, CTkFrame, CTkLabel, CTkButton, CTkTextbox, CTkScrollableFrame
except ImportError:
    print("请先安装 customtkinter: pip install customtkinter")
    sys.exit(1)

try:
    import sympy as sp
    from sympy import symbols, sqrt, sin, cos, tan, ln, exp, pi, oo, limit, diff, integrate, simplify, Matrix, Rational, Function, Eq, solve
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

try:
    import numpy as np
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import cm
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi']
    matplotlib.rcParams['axes.unicode_minus'] = False
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

# ══════════════════════════════════════════════════════════════
#  macOS 风格配色方案
# ══════════════════════════════════════════════════════════════

class MacColors:
    """macOS 风格配色"""
    # 主色调
    BG = "#F5F5F7"           # 浅灰背景
    SIDEBAR_BG = "#E8E8ED"   # 侧边栏背景
    CARD_BG = "#FFFFFF"       # 卡片背景
    ACCENT = "#007AFF"        # macOS 蓝色
    ACCENT_HOVER = "#0056CC"  # 深蓝悬停
    SUCCESS = "#34C759"       # 绿色
    WARNING = "#FF9500"       # 橙色
    DANGER = "#FF3B30"        # 红色
    TEXT_PRIMARY = "#1D1D1F"  # 主文字
    TEXT_SECONDARY = "#86868B" # 次文字
    TEXT_TERTIARY = "#AEAEB2" # 三级文字
    BORDER = "#D2D2D7"        # 边框
    SEPARATOR = "#C6C6C8"     # 分隔线
    HIGHLIGHT = "#E3F2FD"     # 高亮背景

    # 章节颜色
    CH1 = "#FF6B6B"  # 向量 - 红
    CH2 = "#4ECDC4"  # 曲面 - 青
    CH3 = "#45B7D1"  # 直线平面 - 蓝
    CH4 = "#96CEB4"  # 极限 - 绿
    CH5 = "#FFEAA7"  # 导数 - 黄
    CH6 = "#DDA0DD"  # 多元 - 紫
    CH7 = "#98D8C8"  # 应用 - 薄荷
    CH8 = "#F7DC6F"  # 练习 - 金


# ══════════════════════════════════════════════════════════════
#  主窗口
# ══════════════════════════════════════════════════════════════

class MathTutorApp(CTk):
    def __init__(self):
        super().__init__()

        # 窗口配置
        self.title("数学教学程序 - 空间解析几何 & 微分学")
        self.geometry("1200x750")
        self.minsize(1000, 600)
        self.configure(fg_color=MacColors.BG)

        # 设置主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 当前章节
        self.current_chapter = None

        # 构建界面
        self._build_ui()

    def _build_ui(self):
        """构建主界面"""

        # 主容器
        self.main_frame = CTkFrame(self, fg_color=MacColors.BG, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)

        # 左侧边栏
        self._build_sidebar()

        # 右侧内容区
        self._build_content_area()

    def _build_sidebar(self):
        """构建 macOS 风格侧边栏"""
        self.sidebar = CTkFrame(
            self.main_frame,
            width=260,
            fg_color=MacColors.SIDEBAR_BG,
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo 区域
        logo_frame = CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(20, 5))

        CTkLabel(
            logo_frame,
            text="📐 数学教学",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY
        ).pack(anchor="w")

        CTkLabel(
            logo_frame,
            text="空间解析几何 & 微分学",
            font=ctk.CTkFont(size=12),
            text_color=MacColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        # 分隔线
        CTkFrame(self.sidebar, height=1, fg_color=MacColors.SEPARATOR).pack(
            fill="x", padx=20, pady=15
        )

        # 章节标签
        CTkLabel(
            self.sidebar,
            text="章节",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=MacColors.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(0, 8))

        # 章节按钮
        self.chapter_buttons = []
        chapters = [
            ("1", "向量代数", MacColors.CH1),
            ("2", "空间曲面", MacColors.CH2),
            ("3", "直线与平面", MacColors.CH3),
            ("4", "极限与连续", MacColors.CH4),
            ("5", "导数与微分", MacColors.CH5),
            ("6", "多元函数微分", MacColors.CH6),
            ("7", "微分学应用", MacColors.CH7),
            ("8", "练习题", MacColors.CH8),
        ]

        for num, name, color in chapters:
            btn = self._create_chapter_button(num, name, color)
            self.chapter_buttons.append(btn)

        # 底部设置区
        CTkFrame(self.sidebar, height=1, fg_color=MacColors.SEPARATOR).pack(
            fill="x", padx=20, pady=15, side="bottom"
        )

        settings_frame = CTkFrame(self.sidebar, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20, pady=(0, 20), side="bottom")

        CTkButton(
            settings_frame,
            text="📊 查看状态",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=MacColors.ACCENT,
            hover_color=MacColors.HIGHLIGHT,
            height=32,
            command=self._show_status
        ).pack(fill="x")

    def _create_chapter_button(self, num, name, color):
        """创建章节按钮"""
        btn_frame = CTkFrame(self.sidebar, fg_color="transparent", height=40)
        btn_frame.pack(fill="x", padx=12, pady=2)
        btn_frame.pack_propagate(False)

        # 颜色指示条
        indicator = CTkFrame(btn_frame, width=4, fg_color=color, corner_radius=2)
        indicator.pack(side="left", padx=(0, 10), pady=8)

        # 按钮
        btn = CTkButton(
            btn_frame,
            text=f"{num}. {name}",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color=MacColors.TEXT_PRIMARY,
            hover_color=MacColors.HIGHLIGHT,
            anchor="w",
            height=36,
            corner_radius=8,
            command=lambda n=num: self._show_chapter(n)
        )
        btn.pack(fill="x", expand=True)

        return btn

    def _build_content_area(self):
        """构建内容区域"""
        self.content_frame = CTkFrame(
            self.main_frame,
            fg_color=MacColors.BG,
            corner_radius=0
        )
        self.content_frame.pack(side="right", fill="both", expand=True)

        # 默认显示欢迎页
        self._show_welcome()

    def _show_welcome(self):
        """显示欢迎页面"""
        self._clear_content()

        welcome = CTkScrollableFrame(
            self.content_frame,
            fg_color=MacColors.BG,
            corner_radius=0
        )
        welcome.pack(fill="both", expand=True, padx=40, pady=30)

        # 欢迎标题
        CTkLabel(
            welcome,
            text="👋 欢迎使用数学教学程序",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 10))

        CTkLabel(
            welcome,
            text="基于 PDF 教材内容，以最浅显的教学方法帮助你完全掌握",
            font=ctk.CTkFont(size=14),
            text_color=MacColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 30))

        # 功能卡片
        cards_frame = CTkFrame(welcome, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 20))

        card_data = [
            ("📐", "空间解析几何", "向量代数、空间曲面、直线与平面", MacColors.CH1),
            ("📊", "微分学", "极限、导数、多元函数微分、应用", MacColors.CH6),
            ("🧠", "交互式学习", "可视化图形 + 符号运算演示", MacColors.ACCENT),
            ("✏️", "练习题", "8道精选题，含详细提示", MacColors.SUCCESS),
        ]

        for i, (icon, title, desc, color) in enumerate(card_data):
            card = self._create_card(cards_frame, icon, title, desc, color)
            card.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="nsew")

        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)

        # 快速开始按钮
        CTkButton(
            welcome,
            text="🚀 快速开始：向量代数",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=MacColors.ACCENT,
            hover_color=MacColors.ACCENT_HOVER,
            height=44,
            corner_radius=10,
            command=lambda: self._show_chapter("1")
        ).pack(pady=(20, 0))

    def _create_card(self, parent, icon, title, desc, color):
        """创建卡片组件"""
        card = CTkFrame(
            parent,
            fg_color=MacColors.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=MacColors.BORDER
        )

        # 顶部颜色条
        CTkFrame(card, height=4, fg_color=color, corner_radius=2).pack(
            fill="x", padx=15, pady=(15, 10)
        )

        CTkLabel(
            card,
            text=f"{icon} {title}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=15)

        CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=12),
            text_color=MacColors.TEXT_SECONDARY
        ).pack(anchor="w", padx=15, pady=(5, 15))

        return card

    def _clear_content(self):
        """清空内容区域"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_chapter(self, chapter_num):
        """显示章节内容"""
        self.current_chapter = chapter_num
        self._clear_content()

        # 章节标题映射
        titles = {
            "1": ("向量代数", MacColors.CH1),
            "2": ("空间曲面", MacColors.CH2),
            "3": ("直线与平面", MacColors.CH3),
            "4": "极限与连续",
            "5": "导数与微分",
            "6": "多元函数微分",
            "7": "微分学应用",
            "8": "练习题",
        }

        title, color = titles[chapter_num]

        # 内容滚动框架
        content = CTkScrollableFrame(
            self.content_frame,
            fg_color=MacColors.BG,
            corner_radius=0
        )
        content.pack(fill="both", expand=True, padx=40, pady=30)

        # 章节标题
        header = CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        CTkFrame(header, width=6, height=36, fg_color=color, corner_radius=3).pack(
            side="left", padx=(0, 12)
        )

        CTkLabel(
            header,
            text=f"第{chapter_num}章: {title}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY
        ).pack(side="left")

        # 根据章节显示内容
        content_generators = {
            "1": self._content_vector_algebra,
            "2": self._content_surfaces,
            "3": self._content_lines_planes,
            "4": self._content_limits,
            "5": self._content_derivatives,
            "6": self._content_multivariable,
            "7": self._content_calculus_apps,
            "8": self._content_exercises,
        }

        content_generators[chapter_num](content)

    def _content_vector_algebra(self, parent):
        """向量代数内容"""
        # 1.1 向量的概念
        self._render_one_section(parent, "1.1 向量的概念", [
            "向量 = 既有大小又有方向的量",
            "",
            "• 向量的模：向量的长度（大小）",
            "• 单位向量：模为 1 的向量",
            "• 零向量：模为 0，方向不固定",
            "• 相等向量：大小相等，方向相同",
            "• 负向量：大小相同，方向相反",
        ])
        if HAS_PLOT:
            self._add_inline_demo(parent, "📐 查看图形解释", self._demo_vector_concept, MacColors.CH1)

        # 1.1.1 向量几何意义详解（新增）
        self._render_one_section(parent, "1.1.1 向量几何意义详解 ⭐", [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📌 一句话总结：",
            "向量 a = 3i + 2j 在平面上就是一条「带箭头的线段」，",
            "从原点 (0,0) 出发，指向点 (3, 2)",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📍 拆开看每个部分：",
            "┌─────────┬─────────────────────────────┬────────────┐",
            "│  符号   │  几何含义                  │  图中颜色  │",
            "├─────────┼─────────────────────────────┼────────────┤",
            "│    i    │  x轴方向单位向量(向右走1格)│    红色    │",
            "│    j    │  y轴方向单位向量(向上走1格)│    青绿    │",
            "│   3i    │  向右走3格                  │  红色箭头  │",
            "│   2j    │  向上走2格                  │  青绿箭头  │",
            "│ a=3i+2j │  先向右走3、再向上走2       │  蓝色粗箭头│",
            "└─────────┴─────────────────────────────┴────────────┘",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "🔄 三种等价理解方式：",
            "",
            "1️⃣ 坐标理解：",
            "   a 就是点 (3, 2) 的位置向量",
            '   → "从原点到 (3,2) 怎么走"',
            "",
            "2️⃣ 分解理解：",
            "   a = 水平分量 + 竖直分量",
            "   = 3i（横着走 3）+ 2j（竖着走 2）",
            "",
            "3️⃣ 物理理解：",
            "   从原点出发：",
            "   • 先向东走 3 步 → 到达 (3, 0)",
            "   • 再向北走 2 步 → 到达 (3, 2)",
            "   这条直达路径就是向量 a",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "💡 为什么写成 i 和 j？",
            "• i = (1, 0) → x方向的标准「尺子」，长度为1",
            "• j = (0, 1) → y方向的标准「尺子」，长度为1",
            "任何平面向量都可以用这两个「基础方向」拼出来。",
            '就像你说"向东3公里再向北2公里"比说',
            '"往东北偏北方向走√13公里"更直观一样。',
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📊 坐标表示对照：",
            "┌─────────┬──────────────────────┐",
            "│  标注   │  实际含义            │",
            "├─────────┼──────────────────────┤",
            "│   aₓ    │  x分量(水平方向长度) │",
            "│   aᵧ    │  y分量(竖直方向长度) │",
            "│  [aₓ,aᵧ]│  向量的坐标表示      │",
            "└─────────┴──────────────────────┘",
            "三者描述的是同一个对象：从原点指向(3,2)的蓝色粗箭头",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            '🧠 一句话记忆：向量 a 就是一个「位移指令」：',
            '从起点到终点怎么走，走多少。',
        ])
        if HAS_PLOT:
            self._add_inline_demo(parent, "🎨 查看向量几何意义图", self._demo_vector_meaning, MacColors.CH1)

        # 1.2 向量的表示法
        self._render_one_section(parent, "1.2 向量的表示法", [
            "向量分解式: a = aₓ·i + aᵧ·j + aᵤ·k",
            "坐标表示式: a = {aₓ, aᵧ, aᵤ}",
            "",
            "例: a = 3i + 2j - k  →  a = {3, 2, -1}",
            "",
            "━━ 几何意义 ━━",
            "• i, j, k 是三个坐标轴方向的单位向量",
            "• aₓ, aᵧ, aᵤ 分别是向量在x, y, z轴上的投影",
            "• 向量 = 各分量的向量之和",
        ])
        if HAS_PLOT:
            self._add_inline_demo(parent, "📊 查看分解图", self._demo_vector_decompose, MacColors.CH1)

        # 1.3 向量的线性运算
        self._render_one_section(parent, "1.3 向量的线性运算", [
            "设 a = {aₓ, aᵧ, aᵤ}, b = {bₓ, bᵧ, bᵤ}",
            "",
            "加法: a + b = {aₓ+bₓ, aᵧ+bᵧ, aᵤ+bᵤ}",
            "减法: a - b = {aₓ-bₓ, aᵧ-bᵧ, aᵤ-bᵤ}",
            "数乘: λa = {λaₓ, λaᵧ, λaᵤ}",
            "",
            "模长: |a| = √(aₓ² + aᵧ² + aᵤ²)",
            "",
            "━━ 几何意义 ━━",
            "• 加法：从a的终点出发画b，结果是从a起点到b终点",
            "• 数乘：λ>0 同向拉伸，λ<0 反向拉伸",
            "• 模长：向量箭头的实际长度",
        ])
        if HAS_PLOT:
            self._add_inline_demo(parent, "➕ 查看加法图", self._demo_vector_add, MacColors.CH1)

        # 1.4 数量积（点积）
        self._render_one_section(parent, "1.4 数量积（点积）", [
            "定义: a · b = |a|·|b|·cosθ",
            "",
            "坐标公式: a · b = aₓbₓ + aᵧbᵧ + aᵤbᵤ",
            "",
            "垂直条件: a ⊥ b ⟺ a · b = 0",
            "",
            "━━ 几何意义 ━━",
            "• 点积 = a的模 × b在a方向上的投影",
            "• cosθ > 0：夹角为锐角，点积为正",
            "• cosθ = 0：夹角为直角，点积为零（垂直）",
            "• cosθ < 0：夹角为钝角，点积为负",
        ])
        if HAS_PLOT:
            self._add_inline_demo(parent, "✖️ 查看几何图", self._demo_vector_dot, MacColors.CH1)

        # 1.5 向量积（叉积）
        self._render_one_section(parent, "1.5 向量积（叉积）", [
            "定义: c = a × b",
            "• c ⊥ a 且 c ⊥ b（右手规则）",
            "• |c| = |a|·|b|·sinθ",
            "",
            "平行条件: a ∥ b ⟺ a × b = 0",
            "几何意义: 平行四边形面积",
            "三角形面积: S = ½|a × b|",
            "",
            "━━ 几何意义 ━━",
            "• 叉积结果是一个新向量，垂直于原两向量所在平面",
            "• 模长 = a和b构成的平行四边形面积",
            "• 方向由右手定则确定",
        ])
        if HAS_PLOT:
            self._add_inline_demo(parent, "⊗ 查看叉积图", self._demo_vector_cross, MacColors.CH1)

    def _content_surfaces(self, parent):
        """空间曲面内容"""
        sections = [
            ("2.1 旋转曲面", [
                "定义：平面曲线绕定直线旋转一周所成的曲面",
                "",
                "方程特点（曲线 L: f(x,y)=0, z=0）：",
                "• 绕 x 轴: f(x, ±√(y²+z²)) = 0",
                "• 绕 y 轴: f(±√(x²+z²), y) = 0",
                "",
                "例: y² = 2pz 绕 z 轴旋转",
                "→ x² + y² = 2pz （旋转抛物面）",
            ]),
            ("2.2 柱面", [
                "定义：平行于定直线并沿定曲线移动的直线所成曲面",
                "",
                "• 定曲线 C → 准线",
                "• 动直线 L → 母线",
                "",
                "特征：方程中缺少哪个变量，曲面就平行于哪个坐标轴",
                "例: x² + y² = R² （圆柱面，平行于 z 轴）",
            ]),
            ("2.3 二次曲面", [
                "(1) 椭球面: x²/a² + y²/b² + z²/c² = 1",
                "(2) 椭圆抛物面: x²/(2p) + y²/(2q) = z",
                "(3) 双曲抛物面(鞍面): -x²/(2p) + y²/(2q) = z",
                "(4) 单叶双曲面: x²/a² + y²/b² - z²/c² = 1",
                "(5) 双叶双曲面: x²/a² + y²/b² - z²/c² = -1",
                "(6) 二次锥面: x²/a² + y²/b² - z²/c² = 0",
            ]),
        ]

        self._render_sections(parent, sections)

        if HAS_PLOT:
            self._add_demo_button(parent, "🌐 二次曲面 3D 演示", self._demo_surfaces)

    def _content_lines_planes(self, parent):
        """直线与平面内容"""
        sections = [
            ("3.1 空间平面方程", [
                "(1) 一般式: Ax + By + Cz + D = 0",
                "    法向量 n = (A, B, C)",
                "",
                "(2) 点法式: A(x-x₀) + B(y-y₀) + C(z-z₀) = 0",
                "",
                "(3) 截距式: x/a + y/b + z/c = 1",
                "",
                "(4) 点到平面距离:",
                "    d = |Ax₀+By₀+Cz₀+D| / √(A²+B²+C²)",
            ]),
            ("3.2 空间直线方程", [
                "(1) 一般式（两平面交线）:",
                "    A₁x+B₁y+C₁z+D₁=0",
                "    A₂x+B₂y+C₂z+D₂=0",
                "",
                "(2) 对称式: (x-x₀)/m = (y-y₀)/n = (z-z₀)/p",
                "    方向向量 s=(m,n,p)",
                "",
                "(3) 参数式: x=x₀+mt, y=y₀+nt, z=z₀+pt",
            ]),
            ("3.3 位置关系", [
                "【平面与平面】",
                "  垂直: n₁·n₂=0",
                "  平行: n₁×n₂=0",
                "  夹角: cosθ=(n₁·n₂)/(|n₁|·|n₂|)",
                "",
                "【直线与直线】",
                "  垂直: s₁·s₂=0",
                "  平行: s₁×s₂=0",
                "",
                "【直线与平面】",
                "  垂直: s∥n (s×n=0)",
                "  平行: s⊥n (s·n=0)",
            ]),
        ]

        self._render_sections(parent, sections)

        if HAS_SYMPY:
            self._add_demo_button(parent, "🔢 直线平面方程演示", self._demo_lines_planes)

    def _content_limits(self, parent):
        """极限与连续内容"""
        sections = [
            ("4.1 函数", [
                "基本初等函数:",
                "• 常数函数 y = C",
                "• 幂函数 y = xⁿ",
                "• 指数函数 y = aˣ (a>0, a≠1)",
                "• 对数函数 y = logₐx",
                "• 三角函数 sinx, cosx, tanx...",
                "• 反三角函数 arcsinx, arccosx, arctanx...",
                "",
                "初等函数 = 基本初等函数经有限次四则运算与复合而成",
                "",
                "━━ 几何意义 ━━",
                "• 函数图像 = 平面上所有点 (x, f(x)) 的集合",
                "• 每个函数都有其独特的几何形状",
                "• 基本初等函数是构建复杂函数的「积木」",
            ]),
            ("4.2 极限", [
                "等价定义: lim f(x) = A ⟺ f(x) = A + α (α为无穷小)",
                "",
                "等价无穷小代换:",
                "  sinx ~ x     tanx ~ x     arcsinx ~ x",
                "  1-cosx ~ x²/2   ln(1+x) ~ x",
                "  eˣ-1 ~ x    aˣ-1 ~ x·lna   (1+x)ᵝ-1 ~ βx",
                "",
                "两个重要极限:",
                "  lim(sinx/x) = 1     lim(1+1/x)ˣ = e",
                "",
                "━━ 几何意义 ━━",
                "• 极限 = 函数图像「无限逼近」某个点",
                "• lim f(x) = A：当x靠近a时，f(x)的图像无限接近高度A",
                "• 等价无穷小：两条曲线在原点处「几乎重合」",
                "• lim(sinx/x)=1：sinx曲线在原点处与直线y=x相切",
            ]),
            ("4.3 洛必达法则", [
                "适用条件: 0/0 型 或 ∞/∞ 型",
                "",
                "若 lim f(x) = lim F(x) = 0 (∞)",
                "    x→a      x→a",
                "且 F'(x)≠0",
                "",
                "则: lim f(x)/F(x) = lim f'(x)/F'(x)",
                "",
                "━━ 几何意义 ━━",
                "• 0/0型：两条曲线都趋于0，比较谁「下降更快」",
                "• ∞/∞型：两条曲线都趋于∞，比较谁「上升更快」",
                "• 求导后比较：比较两曲线在该点的「变化率之比」",
                "• 几何上：比较两曲线在极限点处的「陡峭程度」",
            ]),
            ("4.4 连续性", [
                "连续定义: lim f(x) = f(x₀)",
                "          x→x₀",
                "",
                "间断点分类:",
                "• 第一类（左右极限都存在）:",
                "  - 可去间断点: 左极限 = 右极限 ≠ f(x₀)",
                "  - 跳跃间断点: 左极限 ≠ 右极限",
                "• 第二类（左右极限至少一个不存在）:",
                "  - 无穷间断点: 极限为 ∞",
                "  - 振荡间断点: 极限振荡不存在",
                "",
                "━━ 几何意义 ━━",
                "• 连续：曲线「一笔画成」，没有断点或跳跃",
                "• 可去间断：曲线上有个「洞」，补上就连续",
                "• 跳跃间断：曲线「突然跳到另一个高度」",
                "• 无穷间断：曲线「冲向无穷远」",
                "• 振荡间断：曲线「无限振荡」不停下来",
            ]),
        ]

        self._render_sections(parent, sections)

        if HAS_PLOT:
            self._add_demo_button(parent, "📊 极限与连续性演示", self._demo_limits)

    def _content_derivatives(self, parent):
        """导数与微分内容"""
        sections = [
            ("5.1 导数的定义", [
                "f'(x₀) = lim [f(x₀+Δx) - f(x₀)] / Δx",
                "           Δx→0",
                "",
                "几何意义: 切线斜率",
                "物理意义: 瞬时变化率",
                "",
                "可导 ⟺ 可微",
                "",
                "━━ 几何意义详解 ━━",
                "• f'(x₀) = 曲线在点(x₀, f(x₀))处的切线斜率",
                "• 切线：紧贴曲线的那条直线",
                "• 斜率 > 0：曲线在该点「上升」",
                "• 斜率 < 0：曲线在该点「下降」",
                "• 斜率 = 0：曲线在该点「水平」（可能是极值点）",
                "• 导数越大：曲线在该点越「陡峭」",
            ]),
            ("5.2 求导公式和法则", [
                "基本公式:",
                "  (C)' = 0          (xⁿ)' = nxⁿ⁻¹",
                "  (sinx)' = cosx    (cosx)' = -sinx",
                "  (tanx)' = sec²x   (aˣ)' = aˣlna",
                "  (lnx)' = 1/x",
                "",
                "法则:",
                "  (u ± v)' = u' ± v'",
                "  (uv)' = u'v + uv'",
                "  (u/v)' = (u'v - uv') / v²",
                "",
                "链式法则: [f(g(x))]' = f'(g(x))·g'(x)",
                "",
                "━━ 几何意义 ━━",
                "• (C)' = 0：常数函数是水平线，斜率为0",
                "• (xⁿ)' = nxⁿ⁻¹：幂函数的「陡峭程度」",
                "• (sinx)' = cosx：正弦曲线的斜率是余弦曲线",
                "• 链式法则：复合函数的斜率 = 外层斜率 × 内层斜率",
            ]),
            ("5.3 隐函数求导", [
                "方法: 方程两边同时对 x 求导，解出 dy/dx",
                "",
                "例: y⁵ + 2y - x - 3x⁷ = 0",
                "  两边求导: 5y⁴·(dy/dx) + 2·(dy/dx) - 1 - 21x⁶ = 0",
                "  dy/dx = (1 + 21x⁶) / (5y⁴ + 2)",
                "",
                "━━ 几何意义 ━━",
                "• 隐函数定义的曲线：不能写成 y=f(x) 形式",
                "• dy/dx = 曲线上某点的切线斜率",
                "• 例：x²+y²=1（圆）的 dy/dx = -x/y",
                "• 在(1,0)处斜率为0（水平切线）",
                "• 在(0,1)处斜率不存在（垂直切线）",
            ]),
            ("5.4 高阶导数", [
                "f''(x) = [f'(x)]'   二阶导数",
                "f⁽ⁿ⁾(x) = [f⁽ⁿ⁻¹⁾(x)]'   n阶导数",
                "",
                "常用公式:",
                "  (eˣ)⁽ⁿ⁾ = eˣ",
                "  (sinx)⁽ⁿ⁾ = sin(x + nπ/2)",
                "  (xⁿ)⁽ⁿ⁾ = n!",
                "",
                "━━ 几何意义 ━━",
                "• f''(x) > 0：曲线「下凸」（像碗口朝上）",
                "• f''(x) < 0：曲线「上凸」（像碗口朝下）",
                "• f''(x) = 0：可能是拐点（凹凸性改变的点）",
                "• 二阶导数描述曲线的「弯曲程度」",
            ]),
        ]

        self._render_sections(parent, sections)

        if HAS_SYMPY:
            self._add_demo_button(parent, "🔢 导数计算演示", self._demo_derivatives)

    def _content_multivariable(self, parent):
        """多元函数微分学内容"""
        sections = [
            ("6.1 偏导数", [
                "定义: z = f(x,y)",
                "",
                "对x: ∂z/∂x = lim [f(x+Δx,y)-f(x,y)] / Δx",
                "               Δx→0",
                "对y: ∂z/∂y = lim [f(x,y+Δy)-f(x,y)] / Δy",
                "               Δy→0",
                "",
                "求法: 将其余变量视为常数，对该变量求导",
                "",
                "━━ 几何意义 ━━",
                "• ∂z/∂x：曲面沿x方向的切线斜率",
                "• ∂z/∂y：曲面沿y方向的切线斜率",
                "• 固定y=x₀，看曲面沿x方向的「陡峭程度」",
                "• 固定x=x₀，看曲面沿y方向的「陡峭程度」",
                "• 偏导数是「单方向」的变化率",
            ]),
            ("6.2 全微分", [
                "定义: dz = fₓ(x,y)dx + fᵧ(x,y)dy",
                "",
                "重要关系:",
                "  函数连续 ⟸ 函数可微 ⟹ 函数可导",
                "  偏导数连续 ⟹ 函数可微",
                "",
                "━━ 几何意义 ━━",
                "• 全微分：曲面在某点的「最佳线性逼近」",
                "• dz = 沿x方向变化 + 沿y方向变化",
                "• 切平面：曲面在该点的「最佳平面逼近」",
                "• 可微：曲面在该点「光滑」，没有尖角",
            ]),
            ("6.3 复合函数求偏导", [
                "设 z = f(u,v), u = φ(t), v = ψ(t)",
                "则: dz/dt = (∂z/∂u)(du/dt) + (∂z/∂v)(dv/dt)",
                "",
                "设 z = f(u,v), u = φ(x,y), v = ψ(x,y)",
                "则: ∂z/∂x = (∂z/∂u)(∂u/∂x) + (∂z/∂v)(∂v/∂x)",
                "",
                "━━ 几何意义 ━━",
                "• 链式法则：多变量版本的「变化率传递」",
                "• z通过u,v受x影响，总变化 = 各路径变化之和",
                "• 几何上：沿不同路径走向目标点，累加各段斜率",
            ]),
            ("6.4 隐函数求偏导", [
                "设 F(x,y,z) = 0",
                "则: ∂z/∂x = -Fₓ/Fᵤ",
                "    ∂z/∂y = -Fᵧ/Fᵤ",
                "",
                "例: x² + y² + z² - 4z = 0",
                "  Fₓ = 2x,  Fᵤ = 2z - 4",
                "  ∂z/∂x = x/(2-z)",
                "",
                "━━ 几何意义 ━━",
                "• F(x,y,z)=0 定义了一个曲面",
                "• ∂z/∂x = -Fₓ/Fᵤ：曲面沿x方向的切线斜率",
                "• 几何上：曲面在某点沿两个方向的「倾斜程度」",
            ]),
        ]

        self._render_sections(parent, sections)

        if HAS_SYMPY:
            self._add_demo_button(parent, "🔢 偏导数演示", self._demo_multivariable)

    def _content_calculus_apps(self, parent):
        """微分学应用内容"""
        sections = [
            ("7.1 中值定理", [
                "【罗尔定理】",
                "  条件: f(x)在[a,b]连续,(a,b)可导,f(a)=f(b)",
                "  结论: ∃ξ∈(a,b), f'(ξ) = 0",
                "",
                "【拉格朗日中值定理】",
                "  条件: f(x)在[a,b]连续,(a,b)可导",
                "  结论: ∃ξ∈(a,b), f(b)-f(a)=f'(ξ)(b-a)",
                "",
                "【柯西中值定理】",
                "  结论: [f(b)-f(a)]/[F(b)-F(a)] = f'(ξ)/F'(ξ)",
                "",
                "━━ 几何意义 ━━",
                "• 罗尔定理：曲线两端等高，中间必有一点切线水平",
                "• 拉格朗日：曲线上必有一点，切线平行于两端连线",
                "• 几何上：曲线的「平均坡度」= 某点的「瞬时坡度」",
                "• 柯西定理：参数方程形式的拉格朗日定理",
            ]),
            ("7.2 单调性与极值", [
                "单调性:",
                "  f'(x) > 0 → 单调递增",
                "  f'(x) < 0 → 单调递减",
                "",
                "极值判别法:",
                "  第一判别法: f'(x)在驻点左右变号",
                "    左正右负 → 极大值",
                "    左负右正 → 极小值",
                "",
                "  第二判别法: f'(x₀)=0, f''(x₀)≠0",
                "    f''(x₀) < 0 → 极大值",
                "    f''(x₀) > 0 → 极小值",
                "",
                "━━ 几何意义 ━━",
                "• f'(x) > 0：曲线「上升」，像上坡",
                "• f'(x) < 0：曲线「下降」，像下坡",
                "• 极大值：「山顶」，先上坡后下坡",
                "• 极小值：「谷底」，先下坡后上坡",
                "• 驻点：切线水平的点（可能是山顶/谷底）",
            ]),
            ("7.3 凹凸性与拐点", [
                "凹凸性:",
                "  f''(x) > 0 → 凹（下凸）",
                "  f''(x) < 0 → 凸（上凸）",
                "",
                "拐点: 凹弧与凸弧的分界点",
                "求法: 令 f''(x) = 0, 检验左右是否变号",
                "",
                "━━ 几何意义 ━━",
                "• 凹（下凸）：曲线像「碗口朝上」，切线在曲线下方",
                "• 凸（上凸）：曲线像「碗口朝下」，切线在曲线上方",
                "• 拐点：曲线弯曲方向改变的点",
                "• 几何上：从「向上弯」变成「向下弯」的转折点",
            ]),
            ("7.4 渐近线与图形描绘", [
                "渐近线类型:",
                "• 水平渐近线: lim f(x) = A → y = A",
                "• 垂直渐近线: lim f(x) = ∞ → x = a",
                "• 斜渐近线: lim f(x)/x = k, lim[f(x)-kx] = b → y = kx+b",
                "",
                "图形描绘步骤:",
                "1. 确定定义域",
                "2. 求 f'(x) 找极值点",
                "3. 求 f''(x) 找拐点",
                "4. 确定渐近线",
                "5. 描点连线",
                "",
                "━━ 几何意义 ━━",
                "• 水平渐近线：曲线两端「趋向水平」",
                "• 垂直渐近线：曲线在某点「冲向无穷」",
                "• 斜渐近线：曲线远端「趋向一条斜线」",
                "• 图形描绘：用微积分工具「还原」曲线全貌",
            ]),
        ]

        self._render_sections(parent, sections)

        if HAS_SYMPY and HAS_PLOT:
            self._add_demo_button(parent, "📊 微分学应用演示", self._demo_calculus_apps)

    def _content_exercises(self, parent):
        """练习题内容"""
        exercises = [
            ("向量代数", "已知 a={1,2,-1}, b={2,-1,3}, 求:\n(1) a·b   (2) a×b   (3) a与b的夹角",
             "点积 = 1×2+2×(-1)+(-1)×3 = -1\n叉积 = 用行列式计算\n夹角用 cosθ = (a·b)/(|a|·|b|)",
             "【几何意义】\n• a·b = -1 表示两向量夹角为钝角（投影方向相反）\n• a×b 的模 = 以a,b为边的平行四边形面积\n• 夹角θ是两向量在平面上张开的角度"),
            ("空间曲面", "曲线 y²=2pz 绕 z 轴旋转，求旋转曲面方程",
             "绕 z 轴旋转: 用 ±√(x²+y²) 替换 y\n得 x²+y²=2pz (旋转抛物面)",
             "【几何意义】\n• 旋转曲面上每个点到z轴的距离相等\n• 截面是圆，越往上圆越大\n• 像一个碗，开口向上"),
            ("直线与平面", "求过点(1,2,3)且与平面 2x+y-z+4=0 垂直的直线方程",
             "直线方向向量 = 平面法向量 = (2,1,-1)\n对称式: (x-1)/2 = (y-2)/1 = (z-3)/(-1)",
             "【几何意义】\n• 直线方向与平面法向量平行\n• 直线像一根针，垂直穿过平面\n• 法向量指向平面的「正面」方向"),
            ("极限", "求 lim(x→0) [sin(3x)/sin(5x)]",
             "用等价无穷小: sin(3x)~3x, sin(5x)~5x\n结果 = 3/5",
             "【几何意义】\n• sin(3x) 在x→0时近似为 3x（小角度近似）\n• 比值就是两个无穷小的「速度比」\n• 几何上：两条曲线在原点处的斜率比"),
            ("导数", "求 y = e^(sinx) · ln(x²+1) 的导数",
             "用乘法法则: (uv)' = u'v + uv'\n注意链式法则",
             "【几何意义】\n• 导数 = 曲线在该点的切线斜率\n• e^(sinx) 的导数描述其增长率\n• ln(x²+1) 的导数描述其变化快慢\n• 乘积的导数 = 两函数变化率的组合"),
            ("隐函数求导", "x²+y²=1, 求 dy/dx",
             "两边对x求导: 2x+2y·(dy/dx)=0\ndy/dx = -x/y",
             "【几何意义】\n• x²+y²=1 是单位圆\n• dy/dx = -x/y 是圆上某点的切线斜率\n• 在(1,0)处斜率为0（水平切线）\n• 在(0,1)处斜率不存在（垂直切线）"),
            ("极值", "求 f(x) = x³-3x 的极值",
             "f'(x) = 3x²-3 = 3(x-1)(x+1)\n驻点 x=±1\nf''(1)=6>0→极小值\nf''(-1)=-6<0→极大值",
             "【几何意义】\n• 极值点是曲线的「山顶」或「谷底」\n• f'(x)=0 表示切线水平（山顶/谷底）\n• f''(x)判断凹凸：上凸→极大，下凸→极小\n• 几何上：曲线先上升后下降=极大，反之=极小"),
            ("偏导数", "z = x²y + sin(xy), 求 ∂z/∂x, ∂z/∂y",
             "∂z/∂x = 2xy + y·cos(xy)\n∂z/∂y = x² + x·cos(xy)",
             "【几何意义】\n• ∂z/∂x：沿x方向切面的斜率\n• ∂z/∂y：沿y方向切面的斜率\n• 偏导数是「固定一个变量」时的变化率\n• 几何上：曲面在某点沿两个方向的陡峭程度"),
        ]

        for i, (topic, problem, hint, geometry) in enumerate(exercises, 1):
            # 题目卡片
            card = CTkFrame(parent, fg_color=MacColors.CARD_BG, corner_radius=12,
                          border_width=1, border_color=MacColors.BORDER)
            card.pack(fill="x", pady=10)

            # 题号和主题
            header = CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=20, pady=(15, 5))

            CTkLabel(
                header,
                text=f"第 {i} 题",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=MacColors.ACCENT
            ).pack(side="left")

            CTkLabel(
                header,
                text=topic,
                font=ctk.CTkFont(size=12),
                text_color=MacColors.TEXT_SECONDARY
            ).pack(side="left", padx=(10, 0))

            # 题目
            CTkLabel(
                card,
                text=problem,
                font=ctk.CTkFont(size=13),
                text_color=MacColors.TEXT_PRIMARY,
                justify="left",
                wraplength=700
            ).pack(anchor="w", padx=20, pady=(5, 10))

            # 按钮区域
            btn_frame = CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=20, pady=(0, 10))

            # 提示按钮
            show_hint = [False]
            hint_label = CTkLabel(
                card,
                text="",
                font=ctk.CTkFont(size=12),
                text_color=MacColors.SUCCESS,
                justify="left",
                wraplength=700
            )

            def toggle_hint(lbl=hint_label, h=hint, btn_ref=[]):
                if show_hint[0]:
                    lbl.configure(text="")
                    show_hint[0] = False
                else:
                    lbl.configure(text=f"💡 提示:\n{h}")
                    show_hint[0] = True

            CTkButton(
                btn_frame,
                text="💡 查看提示",
                font=ctk.CTkFont(size=12),
                fg_color=MacColors.SUCCESS,
                hover_color="#2DA44E",
                height=32,
                corner_radius=8,
                command=toggle_hint
            ).pack(side="left")

            # 几何意义按钮
            show_geometry = [False]
            geometry_label = CTkLabel(
                card,
                text="",
                font=ctk.CTkFont(size=12),
                text_color=MacColors.CH1,
                justify="left",
                wraplength=700
            )

            def toggle_geometry(lbl=geometry_label, g=geometry, btn_ref=[]):
                if show_geometry[0]:
                    lbl.configure(text="")
                    show_geometry[0] = False
                else:
                    lbl.configure(text=g)
                    show_geometry[0] = True

            CTkButton(
                btn_frame,
                text="📐 查看几何意义",
                font=ctk.CTkFont(size=12),
                fg_color=MacColors.CH1,
                hover_color="#E85D5D",
                height=32,
                corner_radius=8,
                command=toggle_geometry
            ).pack(side="left", padx=(10, 0))

            hint_label.pack(anchor="w", pady=(5, 0))
            geometry_label.pack(anchor="w", pady=(5, 0))

    def _render_sections(self, parent, sections):
        """渲染章节段落"""
        for title, items in sections:
            # 段落卡片
            card = CTkFrame(parent, fg_color=MacColors.CARD_BG, corner_radius=12,
                          border_width=1, border_color=MacColors.BORDER)
            card.pack(fill="x", pady=10)

            # 标题
            CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=MacColors.TEXT_PRIMARY
            ).pack(anchor="w", padx=20, pady=(15, 10))

            # 内容
            content_text = "\n".join(items)
            textbox = CTkTextbox(
                card,
                font=ctk.CTkFont(size=13, family="Consolas"),
                fg_color="transparent",
                text_color=MacColors.TEXT_PRIMARY,
                activate_scrollbars=False,
                height=max(60, len(items) * 22)
            )
            textbox.pack(fill="x", padx=20, pady=(0, 15))
            textbox.insert("1.0", content_text)
            textbox.configure(state="disabled")

    def _render_one_section(self, parent, title, items):
        """渲染单个段落"""
        card = CTkFrame(parent, fg_color=MacColors.CARD_BG, corner_radius=12,
                      border_width=1, border_color=MacColors.BORDER)
        card.pack(fill="x", pady=10)

        CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 10))

        content_text = "\n".join(items)
        textbox = CTkTextbox(
            card,
            font=ctk.CTkFont(size=13, family="Consolas"),
            fg_color="transparent",
            text_color=MacColors.TEXT_PRIMARY,
            activate_scrollbars=False,
            height=max(60, len(items) * 22)
        )
        textbox.pack(fill="x", padx=20, pady=(0, 15))
        textbox.insert("1.0", content_text)
        textbox.configure(state="disabled")

    def _add_inline_demo(self, parent, text, command, color=None):
        """添加内联演示按钮（嵌入章节内容中）"""
        if color is None:
            color = MacColors.ACCENT
        btn_frame = CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 5))

        CTkButton(
            btn_frame,
            text=text,
            font=ctk.CTkFont(size=12),
            fg_color=color,
            hover_color=MacColors.ACCENT_HOVER,
            height=32,
            corner_radius=8,
            command=command
        ).pack(anchor="w")

    def _add_demo_button(self, parent, text, command):
        """添加演示按钮"""
        btn_frame = CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15)

        CTkButton(
            btn_frame,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=MacColors.ACCENT,
            hover_color=MacColors.ACCENT_HOVER,
            height=40,
            corner_radius=10,
            command=command
        ).pack()

    def _show_status(self):
        """显示状态"""
        self._clear_content()

        content = CTkScrollableFrame(
            self.content_frame,
            fg_color=MacColors.BG,
            corner_radius=0
        )
        content.pack(fill="both", expand=True, padx=40, pady=30)

        CTkLabel(
            content,
            text="📊 系统状态",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 20))

        status_items = [
            ("sympy 符号运算", HAS_SYMPY, "✓ 已加载" if HAS_SYMPY else "✗ 未安装 (pip install sympy)"),
            ("matplotlib 图形", HAS_PLOT, "✓ 已加载" if HAS_PLOT else "✗ 未安装 (pip install matplotlib)"),
            ("customtkinter GUI", True, "✓ 已加载"),
        ]

        for name, ok, desc in status_items:
            card = CTkFrame(content, fg_color=MacColors.CARD_BG, corner_radius=10,
                          border_width=1, border_color=MacColors.BORDER)
            card.pack(fill="x", pady=5)

            CTkLabel(
                card,
                text=name,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=MacColors.TEXT_PRIMARY
            ).pack(anchor="w", padx=20, pady=(12, 2))

            color = MacColors.SUCCESS if ok else MacColors.DANGER
            CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=12),
                text_color=color
            ).pack(anchor="w", padx=20, pady=(0, 12))

    # ══════════════════════════════════════════════════════════════
    #  演示函数
    # ══════════════════════════════════════════════════════════════

    def _demo_vectors(self):
        """向量运算可视化"""
        fig = plt.figure(figsize=(14, 5))

        ax1 = fig.add_subplot(131)
        a = np.array([3, 2]); b = np.array([1, 3])
        ax1.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='red', label='a={3,2}')
        ax1.quiver(a[0], a[1], b[0], b[1], angles='xy', scale_units='xy', scale=1, color='blue', label='b={1,3}')
        ax1.quiver(0, 0, a[0]+b[0], a[1]+b[1], angles='xy', scale_units='xy', scale=1, color='green', label='a+b')
        ax1.set_xlim(-1, 6); ax1.set_ylim(-1, 6); ax1.set_aspect('equal'); ax1.grid(True, alpha=0.3)
        ax1.set_title('向量加法'); ax1.legend()

        ax2 = fig.add_subplot(132)
        a2 = np.array([3, 1]); b2 = np.array([1, 2])
        ax2.quiver(0, 0, a2[0], a2[1], angles='xy', scale_units='xy', scale=1, color='red', label='a')
        ax2.quiver(0, 0, b2[0], b2[1], angles='xy', scale_units='xy', scale=1, color='blue', label='b')
        ax2.set_xlim(-1, 5); ax2.set_ylim(-1, 4); ax2.set_aspect('equal'); ax2.grid(True, alpha=0.3)
        ax2.set_title(f'点积: a·b = {np.dot(a2,b2)}'); ax2.legend()

        ax3 = fig.add_subplot(133)
        from matplotlib.patches import Polygon
        verts = np.array([[0,0], [3,1], [4,4], [1,3]])
        poly = Polygon(verts, alpha=0.3, color='cyan', label='面积=8')
        ax3.add_patch(poly)
        ax3.quiver(0, 0, 3, 1, angles='xy', scale_units='xy', scale=1, color='red', label='a')
        ax3.quiver(0, 0, 1, 3, angles='xy', scale_units='xy', scale=1, color='blue', label='b')
        ax3.set_xlim(-1, 5); ax3.set_ylim(-1, 5); ax3.set_aspect('equal'); ax3.grid(True, alpha=0.3)
        ax3.set_title('叉积面积'); ax3.legend()

        plt.tight_layout(); plt.show()

    def _demo_vector_meaning(self):
        """向量几何意义详解图"""
        fig = plt.figure(figsize=(14, 10))
        fig.suptitle('向量 a = 3i + 2j 的几何意义详解', fontsize=16, fontweight='bold')

        # 图1: 向量分解图
        ax1 = fig.add_subplot(221)
        a = np.array([3, 2])
        # 坐标轴
        ax1.annotate('', xy=(5, 0), xytext=(-0.5, 0),
                     arrowprops=dict(arrowstyle='->', color='black', lw=1))
        ax1.annotate('', xy=(0, 4), xytext=(0, -0.5),
                     arrowprops=dict(arrowstyle='->', color='black', lw=1))
        # 3i 分量（红色）
        ax1.annotate('', xy=(3, 0), xytext=(0, 0),
                     arrowprops=dict(arrowstyle='->', color='#FF6B6B', lw=3))
        ax1.text(1.5, -0.3, '3i (向右走3格)', fontsize=10, color='#FF6B6B', ha='center')
        # 2j 分量（青色）
        ax1.annotate('', xy=(3, 2), xytext=(3, 0),
                     arrowprops=dict(arrowstyle='->', color='#4ECDC4', lw=3))
        ax1.text(3.3, 1, '2j\n(向上走2格)', fontsize=10, color='#4ECDC4')
        # 向量 a（蓝色）
        ax1.annotate('', xy=(3, 2), xytext=(0, 0),
                     arrowprops=dict(arrowstyle='->', color='#007AFF', lw=4))
        ax1.plot(3, 2, 'o', color='#007AFF', markersize=10)
        ax1.text(3.2, 2.2, 'a = (3,2)', fontsize=12, color='#007AFF', fontweight='bold')
        # 虚线
        ax1.plot([3, 3], [0, 2], '--', color='gray', alpha=0.5)
        ax1.plot([0, 3], [2, 2], '--', color='gray', alpha=0.5)
        ax1.set_xlim(-0.5, 4.5)
        ax1.set_ylim(-0.5, 3.5)
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        ax1.set_title('向量分解: a = 3i + 2j', fontsize=12)
        ax1.set_xlabel('x (i方向)')
        ax1.set_ylabel('y (j方向)')

        # 图2: 位移路径图
        ax2 = fig.add_subplot(222)
        # 起点
        ax2.plot(0, 0, 'go', markersize=12, label='起点 (0,0)')
        # 路径1: 向东
        ax2.annotate('', xy=(3, 0), xytext=(0, 0),
                     arrowprops=dict(arrowstyle='->', color='#FF6B6B', lw=3, linestyle='--'))
        ax2.text(1.5, -0.4, '向东走3步', fontsize=10, color='#FF6B6B', ha='center')
        # 路径2: 向北
        ax2.annotate('', xy=(3, 2), xytext=(3, 0),
                     arrowprops=dict(arrowstyle='->', color='#4ECDC4', lw=3, linestyle='--'))
        ax2.text(3.4, 1, '向北走2步', fontsize=10, color='#4ECDC4')
        # 直达路径
        ax2.annotate('', xy=(3, 2), xytext=(0, 0),
                     arrowprops=dict(arrowstyle='->', color='#007AFF', lw=4))
        ax2.plot(3, 2, 'ro', markersize=12, label='终点 (3,2)')
        ax2.text(1.2, 1.5, '直达路径\n(向量a)', fontsize=11, color='#007AFF', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#E6F1FB', alpha=0.8))
        ax2.set_xlim(-0.5, 4.5)
        ax2.set_ylim(-1, 3.5)
        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper left')
        ax2.set_title('物理理解: 位移路径', fontsize=12)
        ax2.set_xlabel('x (东西方向)')
        ax2.set_ylabel('y (南北方向)')

        # 图3: 三种等价理解
        ax3 = fig.add_subplot(223)
        ax3.axis('off')
        text_content = """
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        📌 三种等价理解方式：

        1️⃣ 坐标理解：
           a 就是点 (3, 2) 的位置向量
           → "从原点到 (3,2) 怎么走"

        2️⃣ 分解理解：
           a = 水平分量 + 竖直分量
           = 3i（横着走 3）+ 2j（竖着走 2）

        3️⃣ 物理理解：
           从原点出发：
           • 先向东走 3 步 → 到达 (3, 0)
           • 再向北走 2 步 → 到达 (3, 2)
           这条直达路径就是向量 a

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        ax3.text(0.1, 0.95, text_content, transform=ax3.transAxes,
                fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        ax3.set_title('三种理解方式', fontsize=12)

        # 图4: 单位向量与坐标表示
        ax4 = fig.add_subplot(224)
        # 单位向量 i
        ax4.annotate('', xy=(1, 0), xytext=(0, 0),
                     arrowprops=dict(arrowstyle='->', color='#FF6B6B', lw=2))
        ax4.text(0.5, -0.3, 'i = (1,0)', fontsize=10, color='#FF6B6B', ha='center')
        # 单位向量 j
        ax4.annotate('', xy=(0, 1), xytext=(0, 0),
                     arrowprops=dict(arrowstyle='->', color='#4ECDC4', lw=2))
        ax4.text(-0.3, 0.5, 'j = (0,1)', fontsize=10, color='#4ECDC4', rotation=90)
        # 向量 a
        ax4.annotate('', xy=(3, 2), xytext=(0, 0),
                     arrowprops=dict(arrowstyle='->', color='#007AFF', lw=3))
        ax4.text(1.5, 1.3, 'a = 3i + 2j', fontsize=12, color='#007AFF', fontweight='bold')
        # 标注分量
        ax4.text(3, -0.3, 'aₓ = 3', fontsize=10, color='#FF6B6B', ha='center')
        ax4.text(-0.5, 2, 'aᵧ = 2', fontsize=10, color='#4ECDC4')
        ax4.set_xlim(-1, 4.5)
        ax4.set_ylim(-1, 3.5)
        ax4.set_aspect('equal')
        ax4.grid(True, alpha=0.3)
        ax4.set_title('单位向量与坐标表示', fontsize=12)
        ax4.set_xlabel('x')
        ax4.set_ylabel('y')

        plt.tight_layout()
        plt.show()

    def _demo_vector_concept(self):
        """向量概念图：大小和方向"""
        fig, axes = plt.subplots(1, 3, figsize=(14, 4))
        fig.suptitle('向量的基本概念', fontsize=14, fontweight='bold')

        # 图1: 向量有方向
        ax = axes[0]
        ax.quiver(0, 0, 3, 2, angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015)
        ax.quiver(0, 0, 2, 3, angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015)
        ax.annotate('a={3,2}', xy=(1.5, 1), fontsize=11, color='#FF6B6B')
        ax.annotate('b={2,3}', xy=(0.5, 1.8), fontsize=11, color='#4ECDC4')
        ax.set_xlim(-0.5, 4); ax.set_ylim(-0.5, 4); ax.set_aspect('equal')
        ax.grid(True, alpha=0.3); ax.set_title('向量有方向', fontsize=11)
        ax.set_xlabel('x'); ax.set_ylabel('y')

        # 图2: 向量有大小(模)
        ax = axes[1]
        ax.quiver(0, 0, 3, 0, angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015)
        ax.quiver(0, 0, 0, 4, angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015)
        ax.plot([0, 3], [0, 0], 'r--', alpha=0.5)
        ax.plot([0, 0], [0, 4], 'c--', alpha=0.5)
        ax.annotate('|a|=3', xy=(1.5, -0.4), fontsize=11, color='#FF6B6B')
        ax.annotate('|b|=4', xy=(-0.8, 2), fontsize=11, color='#4ECDC4')
        ax.set_xlim(-1, 4.5); ax.set_ylim(-1, 5); ax.set_aspect('equal')
        ax.grid(True, alpha=0.3); ax.set_title('向量有大小(模)', fontsize=11)

        # 图3: 单位向量
        ax = axes[2]
        length = np.sqrt(3**2 + 2**2)
        ax.quiver(0, 0, 3/length, 2/length, angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015)
        circle = plt.Circle((0, 0), 1, fill=False, color='gray', linestyle='--', linewidth=1)
        ax.add_patch(circle)
        ax.annotate('i', xy=(0.6, 0.2), fontsize=12, color='#FF6B6B', fontweight='bold')
        ax.annotate('|i|=1', xy=(0.3, -0.5), fontsize=11, color='gray')
        ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_aspect('equal')
        ax.grid(True, alpha=0.3); ax.set_title('单位向量(模=1)', fontsize=11)

        plt.tight_layout(); plt.show()

    def _demo_vector_decompose(self):
        """向量分解图：3D坐标表示"""
        fig = plt.figure(figsize=(10, 5))

        # 左图: 2D 分解
        ax1 = fig.add_subplot(121)
        a = np.array([3, 2])
        ax1.quiver(0, 0, a[0], 0, angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='aₓ=3')
        ax1.quiver(3, 0, 0, a[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='aᵧ=2')
        ax1.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.02, label='a={3,2}')
        ax1.plot([3, 3], [0, 2], 'k--', alpha=0.3)
        ax1.plot([0, 3], [2, 2], 'k--', alpha=0.3)
        ax1.set_xlim(-0.5, 4.5); ax1.set_ylim(-0.5, 3.5); ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3); ax1.legend(fontsize=10)
        ax1.set_title('2D向量分解: a = 3i + 2j', fontsize=11)
        ax1.set_xlabel('x (i方向)'); ax1.set_ylabel('y (j方向)')

        # 右图: 3D 分解
        ax2 = fig.add_subplot(122, projection='3d')
        a3 = np.array([3, 2, -1])
        ax2.quiver(0, 0, 0, 3, 0, 0, color='#FF6B6B', arrow_length_ratio=0.1, linewidth=2)
        ax2.quiver(3, 0, 0, 0, 2, 0, color='#4ECDC4', arrow_length_ratio=0.1, linewidth=2)
        ax2.quiver(3, 2, 0, 0, 0, -1, color='#FFEAA7', arrow_length_ratio=0.1, linewidth=2)
        ax2.quiver(0, 0, 0, 3, 2, -1, color='#007AFF', arrow_length_ratio=0.1, linewidth=3)
        ax2.plot([3, 3], [0, 2], [0, 0], 'k--', alpha=0.3)
        ax2.plot([0, 3], [2, 2], [0, 0], 'k--', alpha=0.3)
        ax2.plot([3, 3], [2, 2], [0, -1], 'k--', alpha=0.3)
        ax2.text(1.5, 0, 0, 'aₓ=3', color='#FF6B6B', fontsize=10)
        ax2.text(3, 1, 0, 'aᵧ=2', color='#4ECDC4', fontsize=10)
        ax2.text(3, 2, -0.6, 'aᵤ=-1', color='#FFEAA7', fontsize=10)
        ax2.text(1.5, 1.2, -0.3, 'a={3,2,-1}', color='#007AFF', fontsize=11, fontweight='bold')
        ax2.set_xlabel('X (i)'); ax2.set_ylabel('Y (j)'); ax2.set_zlabel('Z (k)')
        ax2.set_title('3D向量分解: a = 3i + 2j - k', fontsize=11)

        plt.tight_layout(); plt.show()

    def _demo_vector_add(self):
        """向量加法图"""
        fig, axes = plt.subplots(1, 3, figsize=(14, 4))
        fig.suptitle('向量加法的两种法则', fontsize=14, fontweight='bold')

        a = np.array([3, 1]); b = np.array([1, 3])

        # 三角形法则
        ax = axes[0]
        ax.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a={3,1}')
        ax.quiver(a[0], a[1], b[0], b[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='b={1,3}')
        ax.quiver(0, 0, a[0]+b[0], a[1]+b[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.02, label='a+b={4,4}')
        ax.set_xlim(-0.5, 5.5); ax.set_ylim(-0.5, 5.5); ax.set_aspect('equal')
        ax.grid(True, alpha=0.3); ax.legend(fontsize=9)
        ax.set_title('三角形法则', fontsize=11)

        # 平行四边形法则
        ax = axes[1]
        from matplotlib.patches import Polygon
        verts = np.array([[0,0], a, a+b, b])
        poly = Polygon(verts, alpha=0.2, color='#007AFF')
        ax.add_patch(poly)
        ax.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a')
        ax.quiver(0, 0, b[0], b[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='b')
        ax.quiver(0, 0, a[0]+b[0], a[1]+b[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.02, label='a+b')
        ax.set_xlim(-0.5, 5.5); ax.set_ylim(-0.5, 5.5); ax.set_aspect('equal')
        ax.grid(True, alpha=0.3); ax.legend(fontsize=9)
        ax.set_title('平行四边形法则', fontsize=11)

        # 数乘
        ax = axes[2]
        a2 = np.array([2, 1])
        ax.quiver(0, 0, a2[0], a2[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a={2,1}')
        ax.quiver(0, 0, 2*a2[0], 2*a2[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.02, label='2a={4,2}')
        ax.quiver(0, 0, -a2[0], -a2[1], angles='xy', scale_units='xy', scale=1, color='#FF3B30', width=0.015, label='-a={-2,-1}')
        ax.set_xlim(-3, 5.5); ax.set_ylim(-2, 4); ax.set_aspect('equal')
        ax.grid(True, alpha=0.3); ax.legend(fontsize=9)
        ax.set_title('数乘: λa', fontsize=11)

        plt.tight_layout(); plt.show()

    def _demo_vector_dot(self):
        """点积几何意义"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('数量积(点积)的几何意义', fontsize=14, fontweight='bold')

        ax = axes[0]
        a = np.array([4, 1]); b = np.array([2, 3])
        ax.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a')
        ax.quiver(0, 0, b[0], b[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='b')
        theta = np.linspace(0, np.arctan2(b[1], b[0]), 30)
        ax.plot(1.2*np.cos(theta), 1.2*np.sin(theta), 'k-', linewidth=1)
        ax.text(0.8, 0.4, 'θ', fontsize=12)
        dot = np.dot(a, b)
        ax.text(2, 0.5, f'a·b = {dot}', fontsize=11, color='#007AFF', fontweight='bold')
        ax.set_xlim(-0.5, 5.5); ax.set_ylim(-0.5, 4.5); ax.set_aspect('equal')
        ax.grid(True, alpha=0.3); ax.legend(fontsize=10)
        ax.set_title(f'a·b = |a|·|b|·cosθ = {dot}', fontsize=11)

        ax = axes[1]
        a2 = np.array([4, 2]); b2 = np.array([3, 3])
        proj = np.dot(a2, b2) / np.dot(b2, b2) * b2
        ax.quiver(0, 0, a2[0], a2[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a')
        ax.quiver(0, 0, b2[0], b2[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='b')
        ax.quiver(0, 0, proj[0], proj[1], angles='xy', scale_units='xy', scale=1, color='#FFEAA7', width=0.02, label='Prj_a(b)')
        ax.plot([a2[0], proj[0]], [a2[1], proj[1]], 'k--', alpha=0.5)
        ax.set_xlim(-0.5, 5.5); ax.set_ylim(-0.5, 4.5); ax.set_aspect('equal')
        ax.grid(True, alpha=0.3); ax.legend(fontsize=10)
        ax.set_title('投影: Prj_b(a) = (a·b/|b|²)·b', fontsize=11)

        plt.tight_layout(); plt.show()

    def _demo_vector_cross(self):
        """叉积几何意义"""
        fig = plt.figure(figsize=(12, 5))
        fig.suptitle('向量积(叉积)的几何意义', fontsize=14, fontweight='bold')

        # 图1: 2D 叉积 = 面积
        ax1 = fig.add_subplot(121)
        from matplotlib.patches import Polygon
        a = np.array([3, 1]); b = np.array([1, 3])
        cross_val = a[0]*b[1] - a[1]*b[0]
        verts = np.array([[0,0], a, a+b, b])
        poly = Polygon(verts, alpha=0.3, color='#4ECDC4')
        ax1.add_patch(poly)
        ax1.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a={3,1}')
        ax1.quiver(0, 0, b[0], b[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.015, label='b={1,3}')
        ax1.text(1.5, 1.5, f'面积={cross_val}', fontsize=12, color='#007AFF', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        ax1.set_xlim(-0.5, 5); ax1.set_ylim(-0.5, 5); ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3); ax1.legend(fontsize=10)
        ax1.set_title(f'|a×b| = 平行四边形面积 = {cross_val}', fontsize=11)

        # 图2: 3D 右手规则
        ax2 = fig.add_subplot(122, projection='3d')
        a3 = np.array([2, 1, 0]); b3 = np.array([1, 2, 0])
        c3 = np.cross(a3, b3)
        ax2.quiver(0, 0, 0, a3[0], a3[1], a3[2], color='#FF6B6B', arrow_length_ratio=0.1, linewidth=2, label='a')
        ax2.quiver(0, 0, 0, b3[0], b3[1], b3[2], color='#007AFF', arrow_length_ratio=0.1, linewidth=2, label='b')
        ax2.quiver(0, 0, 0, 0, 0, c3[2], color='#34C759', arrow_length_ratio=0.1, linewidth=3, label='a×b')
        ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')
        ax2.legend(fontsize=10)
        ax2.set_title(f'右手规则: a×b ⊥ a, a×b ⊥ b\na×b = (0,0,{c3[2]})', fontsize=11)

        plt.tight_layout(); plt.show()
        """二次曲面3D"""
        fig = plt.figure(figsize=(15, 10))

        ax1 = fig.add_subplot(231, projection='3d')
        u = np.linspace(0, 2*np.pi, 50); v = np.linspace(0, np.pi, 50)
        x = 2*np.outer(np.cos(u), np.sin(v)); y = 1.5*np.outer(np.sin(u), np.sin(v))
        z = np.outer(np.ones(np.size(u)), np.cos(v))
        ax1.plot_surface(x, y, z, alpha=0.6, cmap='coolwarm')
        ax1.set_title('椭球面')

        ax2 = fig.add_subplot(232, projection='3d')
        r = np.linspace(0, 2, 40); theta = np.linspace(0, 2*np.pi, 40)
        R, THETA = np.meshgrid(r, theta)
        X = R*np.cos(THETA); Y = R*np.sin(THETA); Z = X**2/4 + Y**2/4
        ax2.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
        ax2.set_title('旋转抛物面')

        ax3 = fig.add_subplot(233, projection='3d')
        x = np.linspace(-2, 2, 50); y = np.linspace(-2, 2, 50)
        X, Y = np.meshgrid(x, y); Z = X**2/4 - Y**2/4
        ax3.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
        ax3.set_title('鞍面')

        ax4 = fig.add_subplot(234, projection='3d')
        u = np.linspace(0, 2*np.pi, 50); v = np.linspace(-1.5, 1.5, 30)
        X = 1.5*np.outer(np.cosh(v), np.cos(u)); Y = 1.5*np.outer(np.cosh(v), np.sin(u))
        Z = np.outer(np.sinh(v), np.ones(np.size(u)))
        ax4.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
        ax4.set_title('单叶双曲面')

        ax5 = fig.add_subplot(235, projection='3d')
        theta = np.linspace(0, 2*np.pi, 50); z = np.linspace(-2, 2, 30)
        THETA, Z = np.meshgrid(theta, z); R = np.abs(Z)
        X = R*np.cos(THETA); Y = R*np.sin(THETA)
        ax5.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
        ax5.set_title('二次锥面')

        ax6 = fig.add_subplot(236, projection='3d')
        theta = np.linspace(0, 2*np.pi, 50); z = np.linspace(-2, 2, 30)
        THETA, Z = np.meshgrid(theta, z)
        X = np.cos(THETA); Y = np.sin(THETA)
        ax6.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
        ax6.set_title('圆柱面')

        plt.tight_layout(); plt.show()

    def _demo_limits(self):
        """极限几何意义演示"""
        fig = plt.figure(figsize=(14, 10))
        fig.suptitle('极限与连续性的几何意义', fontsize=16, fontweight='bold')

        # 图1: lim sin(x)/x = 1
        ax1 = fig.add_subplot(221)
        x = np.linspace(-8, 8, 500)
        x_safe = x.copy()
        x_safe[x_safe == 0] = 1e-10
        y = np.sin(x_safe) / x_safe

        ax1.plot(x, y, 'b-', linewidth=2, label='sin(x)/x')
        ax1.axhline(y=1, color='r', linestyle='--', alpha=0.5, label='y=1 (极限值)')
        ax1.plot(0, 1, 'ro', markersize=10, label='极限点 (0,1)')
        ax1.fill_between(x, y, 1, alpha=0.2, color='yellow', label='逼近过程')

        ax1.set_xlim(-8, 8)
        ax1.set_ylim(-0.3, 1.5)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=9)
        ax1.set_title('lim(sinx/x) = 1\n曲线无限逼近y=1', fontsize=12)
        ax1.set_xlabel('x')
        ax1.set_ylabel('y')

        # 图2: lim (1+1/x)^x = e
        ax2 = fig.add_subplot(222)
        x2 = np.linspace(1, 100, 200)
        y2 = (1 + 1/x2)**x2

        ax2.plot(x2, y2, 'b-', linewidth=2, label='(1+1/x)^x')
        ax2.axhline(y=np.e, color='r', linestyle='--', alpha=0.5, label=f'y=e≈{np.e:.4f} (极限值)')
        ax2.fill_between(x2, y2, np.e, alpha=0.2, color='yellow', label='逼近过程')

        ax2.set_xlim(0, 105)
        ax2.set_ylim(2, 3)
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=9)
        ax2.set_title('lim(1+1/x)^x = e\n曲线无限逼近y=e', fontsize=12)
        ax2.set_xlabel('x')
        ax2.set_ylabel('y')

        # 图3: 连续性
        ax3 = fig.add_subplot(223)
        x3 = np.linspace(-2, 3, 500)

        # 连续函数
        y3_cont = np.sin(x3) + 1
        ax3.plot(x3, y3_cont, 'b-', linewidth=2, label='连续: sin(x)+1')

        # 可去间断点
        y3_removable = np.where(x3 != 1, (x3**2 - 1)/(x3 - 1), 0)
        ax3.plot(x3, y3_removable, 'g--', linewidth=2, label='可去间断点')
        ax3.plot(1, 2, 'go', markersize=10, markerfacecolor='white', markeredgewidth=2)

        ax3.set_xlim(-2.5, 3.5)
        ax3.set_ylim(-0.5, 3)
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=9)
        ax3.set_title('连续 vs 可去间断点\n连续=一笔画成，可去=有个洞', fontsize=12)
        ax3.set_xlabel('x')
        ax3.set_ylabel('y')

        # 图4: 间断点类型
        ax4 = fig.add_subplot(224)
        x4 = np.linspace(-3, 3, 500)

        # 跳跃间断点
        y4_jump = np.where(x4 < 0, -1, 1)
        ax4.step(x4, y4_jump, 'b-', linewidth=2, where='mid', label='跳跃间断点')
        ax4.plot(0, -1, 'bo', markersize=8, markerfacecolor='white', markeredgewidth=2)
        ax4.plot(0, 1, 'bo', markersize=8)

        # 无穷间断点
        x4_inf = x4[np.abs(x4) > 0.3]
        y4_inf = 1 / x4_inf
        ax4.plot(x4_inf, y4_inf, 'r-', linewidth=2, label='无穷间断点')

        ax4.set_xlim(-3, 3)
        ax4.set_ylim(-5, 5)
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=9)
        ax4.set_title('跳跃间断点 vs 无穷间断点\n跳跃=突然跳变，无穷=冲向∞', fontsize=12)
        ax4.set_xlabel('x')
        ax4.set_ylabel('y')

        plt.tight_layout()
        plt.show()

    def _demo_derivatives(self):
        """导数几何意义演示"""
        fig = plt.figure(figsize=(14, 10))
        fig.suptitle('导数的几何意义', fontsize=16, fontweight='bold')

        # 图1: 切线斜率
        ax1 = fig.add_subplot(221)
        x = np.linspace(-2, 3, 500)
        y = x**3 - 3*x + 2
        ax1.plot(x, y, 'b-', linewidth=2, label='f(x) = x³-3x+2')

        # 在x=1处画切线
        x0 = 1
        y0 = x0**3 - 3*x0 + 2
        slope = 3*x0**2 - 3  # f'(x) = 3x²-3
        tangent_x = np.linspace(x0-1.5, x0+1.5, 100)
        tangent_y = y0 + slope * (tangent_x - x0)
        ax1.plot(tangent_x, tangent_y, 'r--', linewidth=2, label=f'切线 (斜率={slope})')
        ax1.plot(x0, y0, 'go', markersize=10, label=f'切点 ({x0},{y0})')

        ax1.set_xlim(-2.5, 3.5)
        ax1.set_ylim(-3, 6)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_title('f\'(x₀) = 切线斜率', fontsize=12)
        ax1.set_xlabel('x')
        ax1.set_ylabel('y')

        # 图2: 单调性
        ax2 = fig.add_subplot(222)
        x2 = np.linspace(-2, 2.5, 500)
        y2 = x2**3 - 3*x2
        y2_prime = 3*x2**2 - 3

        ax2.plot(x2, y2, 'b-', linewidth=2, label='f(x) = x³-3x')
        ax2.fill_between(x2, y2, where=(y2_prime > 0), alpha=0.3, color='green', label='f\'(x)>0 递增')
        ax2.fill_between(x2, y2, where=(y2_prime < 0), alpha=0.3, color='red', label='f\'(x)<0 递减')

        # 标注极值点
        ax2.plot(1, -2, 'go', markersize=10, label='极小值 f(1)=-2')
        ax2.plot(-1, 2, 'rs', markersize=10, label='极大值 f(-1)=2')

        ax2.set_xlim(-2.5, 3)
        ax2.set_ylim(-4, 4)
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=9)
        ax2.set_title('f\'(x) 判断单调性', fontsize=12)
        ax2.set_xlabel('x')
        ax2.set_ylabel('y')

        # 图3: 凹凸性
        ax3 = fig.add_subplot(223)
        x3 = np.linspace(-2, 2, 500)
        y3 = x3**4 - 4*x3**2 + 5
        y3_double = 12*x3**2 - 8

        ax3.plot(x3, y3, 'b-', linewidth=2, label='f(x) = x⁴-4x²+5')
        ax3.fill_between(x3, y3, where=(y3_double > 0), alpha=0.3, color='cyan', label='f\'\'(x)>0 凹')
        ax3.fill_between(x3, y3, where=(y3_double < 0), alpha=0.3, color='yellow', label='f\'\'(x)<0 凸')

        # 标注拐点
        inflection_x = np.sqrt(2/3)
        inflection_y = inflection_x**4 - 4*inflection_x**2 + 5
        ax3.plot([-inflection_x, inflection_x], [inflection_y, inflection_y], 'mo', markersize=10, label='拐点')

        ax3.set_xlim(-2.2, 2.2)
        ax3.set_ylim(0, 6)
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=9)
        ax3.set_title('f\'\'(x) 判断凹凸性', fontsize=12)
        ax3.set_xlabel('x')
        ax3.set_ylabel('y')

        # 图4: 极值判别
        ax4 = fig.add_subplot(224)
        x4 = np.linspace(-2, 2, 500)
        y4_prime = 3*x4**2 - 3
        y4_double = 6*x4

        ax4.plot(x4, y4_prime, 'b-', linewidth=2, label="f'(x) = 3x²-3")
        ax4.plot(x4, y4_double, 'r--', linewidth=2, label="f''(x) = 6x")
        ax4.axhline(y=0, color='k', linewidth=0.5)

        # 标注驻点
        ax4.plot([-1, 1], [0, 0], 'go', markersize=10)
        ax4.text(-1, 0.5, "f'(-1)=0\nf''(-1)=-6<0\n极大值", fontsize=9, ha='center', color='green')
        ax4.text(1, -0.5, "f'(1)=0\nf''(1)=6>0\n极小值", fontsize=9, ha='center', color='green')

        ax4.set_xlim(-2.5, 2.5)
        ax4.set_ylim(-8, 10)
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        ax4.set_title('极值判别法', fontsize=12)
        ax4.set_xlabel('x')
        ax4.set_ylabel('y')

        plt.tight_layout()
        plt.show()

    def _demo_multivariable(self):
        """偏导数演示"""
        x, y = symbols('x y')
        print("\n【偏导数演示】")
        f = x**2 + 3*x*y + y**2
        print(f"  f(x,y) = {f}")
        print(f"  ∂f/∂x = {diff(f, x)}")
        print(f"  ∂f/∂y = {diff(f, y)}")

    def _demo_calculus_apps(self):
        """微分学应用演示"""
        fig = plt.figure(figsize=(14, 5))

        ax1 = fig.add_subplot(121)
        x = np.linspace(-0.5, 3, 500)
        f = 2*x**3 - 9*x**2 + 12*x - 3
        fp = 6*x**2 - 18*x + 12
        ax1.plot(x, f, 'b-', linewidth=2, label='f(x)=2x³-9x²+12x-3')
        ax1.plot(x, fp, 'r--', linewidth=1.5, alpha=0.7, label="f'(x)")
        ax1.plot(1, 2, 'go', markersize=8, label='极大值 f(1)=2')
        ax1.plot(2, 1, 'rs', markersize=8, label='极小值 f(2)=1')
        ax1.axhline(y=0, color='k', linewidth=0.5)
        ax1.set_title('单调性与极值'); ax1.legend(); ax1.grid(True, alpha=0.3)

        ax2 = fig.add_subplot(122)
        x2 = np.linspace(-1, 3, 500)
        f2 = 3*x2**4 - 4*x2**3 + 1
        f2p = 36*x2**2 - 24*x2
        ax2.plot(x2, f2, 'b-', linewidth=2, label='f(x)=3x⁴-4x³+1')
        ax2.plot(x2, f2p, 'r--', linewidth=1.5, alpha=0.7, label="f''(x)")
        ax2.plot(2/3, 3*(2/3)**4-4*(2/3)**3+1, 'mo', markersize=8, label='拐点')
        ax2.axhline(y=0, color='k', linewidth=0.5)
        ax2.set_title('凹凸性与拐点'); ax2.legend(); ax2.grid(True, alpha=0.3)

        plt.tight_layout(); plt.show()

    def _demo_lines_planes(self):
        """直线平面方程演示"""
        x, y, z = symbols('x y z')
        print("\n【例题1】求过三点 A(1,2,3), B(3,4,5), C(-2,4,7) 的平面方程")
        AB = Matrix([2,2,2]); AC = Matrix([-3,2,4])
        n = AB.cross(AC)
        print(f"  法向量 n = {n.T}")
        plane = n[0]*(x-1) + n[1]*(y-2) + n[2]*(z-3)
        print(f"  平面方程: {sp.expand(plane)} = 0")


# ══════════════════════════════════════════════════════════════
#  启动
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = MathTutorApp()
    app.mainloop()
