#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式数学教学程序 - macOS Big Sur / Ventura 风格 GUI
空间解析几何 & 微分学

主入口文件 —— 仅负责 UI 框架，文本数据和演示逻辑存放于各子模块中。
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

try:
    import customtkinter as ctk
    from customtkinter import CTk, CTkFrame, CTkLabel, CTkButton, CTkTextbox, CTkScrollableFrame, CTkCanvas
except ImportError:
    print("请先安装 customtkinter: pip install customtkinter")
    sys.exit(1)

# 可用性检测（rcParams / 字体在 demos.py 中设置）
try:
    import sympy  # noqa: F401
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

try:
    import numpy  # noqa: F401
    import matplotlib  # noqa: F401
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

# 子模块
from mac_colors import MacColors
from content_data import (
    get_welcome_card_data,
    get_vector_algebra_sections,
    get_surfaces_sections,
    get_lines_planes_sections,
    get_limits_sections,
    get_derivatives_sections,
    get_multivariable_sections,
    get_calculus_apps_sections,
    CHAPTER_TITLES,
)
import demos
import exercises


# ══════════════════════════════════════════════════════════════
#  字体辅助
# ══════════════════════════════════════════════════════════════

def _resolve_font():
    """选择第一个可用字体族"""
    import tkinter.font as tkfont
    available = set(tkfont.families())
    for fam in MacColors.FONT_FAMILY:
        if fam in available:
            return fam
    return "Segoe UI"  # Windows fallback


# ══════════════════════════════════════════════════════════════
#  交通灯按钮 (Canvas)
# ══════════════════════════════════════════════════════════════

class _TrafficLight(CTkFrame):
    """macOS 风格交通灯按钮组 (关闭 / 最小化 / 最大化)"""

    _R = 6  # radius → 12px diameter

    def __init__(self, parent, close_cmd, min_cmd, zoom_cmd, **kw):
        super().__init__(parent, fg_color="transparent", width=60, height=MacColors.TITLEBAR_HEIGHT, **kw)
        self.pack_propagate(False)

        self._canvas = CTkCanvas(self, width=60, height=MacColors.TITLEBAR_HEIGHT,
                                 highlightthickness=0, bg=self._hex(MacColors.TITLEBAR_BG))
        self._canvas.pack()

        y = MacColors.TITLEBAR_HEIGHT // 2
        self._ids = {}
        for idx, (cx, color, tag) in enumerate([
            (12, MacColors.TRAFFIC_CLOSE,    "close"),
            (30, MacColors.TRAFFIC_MINIMIZE, "minimize"),
            (48, MacColors.TRAFFIC_MAXIMIZE, "zoom"),
        ]):
            oid = self._canvas.create_oval(
                cx - self._R, y - self._R, cx + self._R, y + self._R,
                fill=color, outline="", width=0,
            )
            self._ids[tag] = oid

        # 命令绑定
        self._cmds = {"close": close_cmd, "minimize": min_cmd, "zoom": zoom_cmd}

        # 悬停图标符号
        self._hover_symbols = {"close": "✕", "minimize": "−", "zoom": "+"}
        self._hover_text_id = None

        # 事件
        for tag in ("close", "minimize", "zoom"):
            oid = self._ids[tag]
            self._canvas.tag_bind(oid, "<Enter>", lambda e, t=tag: self._on_enter(t))
            self._canvas.tag_bind(oid, "<Leave>", lambda e, t=tag: self._on_leave(t))
            self._canvas.tag_bind(oid, "<Button-1>", lambda e, t=tag: self._cmds[t]())

    @staticmethod
    def _hex(color):
        """确保颜色是 #RRGGBB 格式（去掉 alpha 后缀）"""
        if len(color) == 9:
            return color[:7]
        return color

    def _on_enter(self, tag):
        cx_map = {"close": 12, "minimize": 30, "zoom": 48}
        y = MacColors.TITLEBAR_HEIGHT // 2
        cx = cx_map[tag]
        sym = self._hover_symbols[tag]
        if self._hover_text_id:
            self._canvas.delete(self._hover_text_id)
        self._hover_text_id = self._canvas.create_text(
            cx, y, text=sym, fill="#4D000000" if tag == "close" else "#4D000000",
            font=("Segoe UI", 8, "bold"),
        )

    def _on_leave(self, tag):
        if self._hover_text_id:
            self._canvas.delete(self._hover_text_id)
            self._hover_text_id = None


# ══════════════════════════════════════════════════════════════
#  主应用
# ══════════════════════════════════════════════════════════════

class MathTutorApp(CTk):
    def __init__(self):
        super().__init__()

        self.title("数学教学程序 - 空间解析几何 & 微分学")
        self.geometry("1200x750")
        self.minsize(1000, 600)
        self.configure(fg_color=MacColors.BG)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self._font_family = _resolve_font()
        self.current_chapter = None
        self._is_zoomed = False
        self._drag_data = {"x": 0, "y": 0}

        self._build_ui()

    # ────────────────────────────────────────────
    #  UI 构建
    # ────────────────────────────────────────────

    def _build_ui(self):
        # 标题栏
        self._build_titlebar()
        # 主体区域
        self.main_frame = CTkFrame(self, fg_color=MacColors.BG, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)
        self._build_sidebar()
        self._build_content_area()

    # ── 标题栏 ──

    def _build_titlebar(self):
        self.titlebar = CTkFrame(self, fg_color=MacColors.TITLEBAR_BG, corner_radius=0,
                                 height=MacColors.TITLEBAR_HEIGHT)
        self.titlebar.pack(fill="x")
        self.titlebar.pack_propagate(False)

        # 底部细线
        CTkFrame(self.titlebar, height=1, fg_color=MacColors.BORDER, corner_radius=0).pack(
            side="bottom", fill="x")

        # 交通灯
        self.traffic = _TrafficLight(
            self.titlebar,
            close_cmd=self._close_app,
            min_cmd=self._minimize_app,
            zoom_cmd=self._toggle_zoom,
        )
        self.traffic.pack(side="left", padx=(10, 0))

        # 居中标题
        self._title_label = CTkLabel(
            self.titlebar, text="数学教学",
            font=ctk.CTkFont(family=self._font_family, size=13, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY,
        )
        self._title_label.place(relx=0.5, rely=0.5, anchor="center")

        # 拖拽绑定
        for w in (self.titlebar, self._title_label):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)

    # ── 侧边栏 ──

    def _build_sidebar(self):
        self.sidebar = CTkFrame(
            self.main_frame, width=240,
            fg_color=MacColors.SIDEBAR_BG, corner_radius=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # 右侧细线
        CTkFrame(self.sidebar, width=1, fg_color=MacColors.BORDER, corner_radius=0).pack(
            side="right", fill="y")

        # Logo 区域
        logo_frame = CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(18, 4))

        CTkLabel(
            logo_frame, text="📐 数学教学",
            font=ctk.CTkFont(family=self._font_family, size=18, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY,
        ).pack(anchor="w")

        CTkLabel(
            logo_frame, text="空间解析几何 & 微分学",
            font=ctk.CTkFont(family=self._font_family, size=11),
            text_color=MacColors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(2, 0))

        # 分隔线
        CTkFrame(self.sidebar, height=1, fg_color=MacColors.SUBTLE_BORDER).pack(
            fill="x", padx=16, pady=(14, 10))

        # 章节标题
        CTkLabel(
            self.sidebar, text="章  节",
            font=ctk.CTkFont(family=self._font_family, size=11, weight="bold"),
            text_color=MacColors.TEXT_TERTIARY,
        ).pack(anchor="w", padx=20, pady=(0, 6))

        # 章节按钮
        self.chapter_buttons = []
        for num, (name, color) in CHAPTER_TITLES.items():
            btn = self._create_chapter_button(num, name, color)
            self.chapter_buttons.append(btn)

        # 底部区域
        CTkFrame(self.sidebar, height=1, fg_color=MacColors.SUBTLE_BORDER).pack(
            fill="x", padx=16, pady=(10, 8), side="bottom")

        bottom_frame = CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=12, pady=(0, 14), side="bottom")

        # 状态按钮
        self._status_btn = CTkButton(
            bottom_frame, text="📊  查看状态",
            font=ctk.CTkFont(family=self._font_family, size=12),
            fg_color="transparent", text_color=MacColors.TEXT_SECONDARY,
            hover_color=MacColors.HOVER_BG, height=32, corner_radius=6,
            anchor="w",
            command=self._show_status,
        )
        self._status_btn.pack(fill="x", padx=4, pady=1)

        # 偏好设置
        CTkButton(
            bottom_frame, text="⚙️  偏好设置",
            font=ctk.CTkFont(family=self._font_family, size=12),
            fg_color="transparent", text_color=MacColors.TEXT_SECONDARY,
            hover_color=MacColors.HOVER_BG, height=32, corner_radius=6,
            anchor="w",
            command=lambda: None,
        ).pack(fill="x", padx=4, pady=1)

        # 帮助
        CTkButton(
            bottom_frame, text="❓  帮助",
            font=ctk.CTkFont(family=self._font_family, size=12),
            fg_color="transparent", text_color=MacColors.TEXT_SECONDARY,
            hover_color=MacColors.HOVER_BG, height=32, corner_radius=6,
            anchor="w",
            command=lambda: None,
        ).pack(fill="x", padx=4, pady=1)

    def _create_chapter_button(self, num, name, color):
        btn_frame = CTkFrame(self.sidebar, fg_color="transparent", height=36)
        btn_frame.pack(fill="x", padx=8, pady=1)
        btn_frame.pack_propagate(False)

        # 左侧色条
        CTkFrame(btn_frame, width=3, fg_color=color, corner_radius=2).pack(
            side="left", padx=(4, 8), pady=8)

        btn = CTkButton(
            btn_frame, text=f"  {num}.  {name}",
            font=ctk.CTkFont(family=self._font_family, size=13),
            fg_color="transparent", text_color=MacColors.TEXT_PRIMARY,
            hover_color=MacColors.HOVER_BG, anchor="w",
            height=34, corner_radius=8,
            command=lambda n=num: self._show_chapter(n),
        )
        btn.pack(fill="x", expand=True, padx=(0, 4))
        return btn

    # ── 内容区域 ──

    def _build_content_area(self):
        self.content_frame = CTkFrame(
            self.main_frame, fg_color=MacColors.BG, corner_radius=0,
        )
        self.content_frame.pack(side="right", fill="both", expand=True)
        self._show_welcome()

    # ────────────────────────────────────────────
    #  窗口控制
    # ────────────────────────────────────────────

    def _close_app(self):
        self.quit()
        self.destroy()

    def _minimize_app(self):
        self.iconify()

    def _toggle_zoom(self):
        if self._is_zoomed:
            self.attributes("-zoomed", False)
            self._is_zoomed = False
        else:
            self.attributes("-zoomed", True)
            self._is_zoomed = True

    def _start_drag(self, event):
        self._drag_data["x"] = event.x_root - self.winfo_x()
        self._drag_data["y"] = event.y_root - self.winfo_y()

    def _do_drag(self, event):
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")

    # ────────────────────────────────────────────
    #  欢迎页
    # ────────────────────────────────────────────

    def _show_welcome(self):
        self._clear_content()

        welcome = CTkScrollableFrame(
            self.content_frame, fg_color=MacColors.BG, corner_radius=0,
        )
        welcome.pack(fill="both", expand=True, padx=40, pady=30)

        CTkLabel(
            welcome, text="👋 欢迎使用数学教学程序",
            font=ctk.CTkFont(family=self._font_family, size=24, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        CTkLabel(
            welcome, text="基于 PDF 教材内容，以最浅显的教学方法帮助你完全掌握",
            font=ctk.CTkFont(family=self._font_family, size=13),
            text_color=MacColors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 24))

        # 卡片网格
        cards_frame = CTkFrame(welcome, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 20))

        for i, (icon, title, desc, color) in enumerate(get_welcome_card_data()):
            card = self._create_card(cards_frame, icon, title, desc, color)
            card.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="nsew")

        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)

        # 快速开始按钮
        CTkButton(
            welcome, text="快速开始：向量代数  ›",
            font=ctk.CTkFont(family=self._font_family, size=13, weight="bold"),
            fg_color=MacColors.ACCENT, hover_color=MacColors.ACCENT_HOVER,
            text_color="#FFFFFF",
            height=36, corner_radius=8,
            command=lambda: self._show_chapter("1"),
        ).pack(pady=(16, 0))

    def _create_card(self, parent, icon, title, desc, color):
        card = CTkFrame(
            parent, fg_color=MacColors.CARD_BG, corner_radius=10,
            border_width=1, border_color=MacColors.BORDER,
        )

        # 顶部色条
        CTkFrame(card, height=4, fg_color=color, corner_radius=2).pack(
            fill="x", padx=0, pady=(0, 0))

        inner = CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=(12, 15))

        CTkLabel(
            inner, text=f"{icon}  {title}",
            font=ctk.CTkFont(family=self._font_family, size=15, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY,
        ).pack(anchor="w")

        CTkLabel(
            inner, text=desc,
            font=ctk.CTkFont(family=self._font_family, size=12),
            text_color=MacColors.TEXT_SECONDARY,
            wraplength=300, justify="left",
        ).pack(anchor="w", pady=(6, 0))

        return card

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # ────────────────────────────────────────────
    #  章节路由
    # ────────────────────────────────────────────

    def _show_chapter(self, chapter_num):
        self.current_chapter = chapter_num
        self._clear_content()

        title, color = CHAPTER_TITLES[chapter_num]

        content = CTkScrollableFrame(
            self.content_frame, fg_color=MacColors.BG, corner_radius=0,
        )
        content.pack(fill="both", expand=True, padx=40, pady=30)

        # 章节标题头部
        header = CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        CTkFrame(header, width=5, height=32, fg_color=color, corner_radius=3).pack(
            side="left", padx=(0, 12),
        )
        CTkLabel(
            header, text=f"第{chapter_num}章: {title}",
            font=ctk.CTkFont(family=self._font_family, size=24, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY,
        ).pack(side="left")

        # 根据章节号分发内容
        if chapter_num == "1":
            self._render_chapter1(content)
        elif chapter_num == "2":
            self._render_sections(content, get_surfaces_sections())
            if HAS_PLOT:
                self._add_demo_button(content, "🌐 二次曲面 3D 演示", demos.demo_surfaces)
        elif chapter_num == "3":
            self._render_sections(content, get_lines_planes_sections())
            if HAS_SYMPY:
                self._add_demo_button(content, "🔢 直线平面方程演示", demos.demo_lines_planes)
        elif chapter_num == "4":
            self._render_sections(content, get_limits_sections())
            if HAS_PLOT:
                self._add_demo_button(content, "📊 极限与连续性演示", demos.demo_limits)
        elif chapter_num == "5":
            self._render_sections(content, get_derivatives_sections())
            if HAS_SYMPY:
                self._add_demo_button(content, "🔢 导数计算演示", demos.demo_derivatives)
        elif chapter_num == "6":
            self._render_sections(content, get_multivariable_sections())
            if HAS_SYMPY:
                self._add_demo_button(content, "🔢 偏导数演示", demos.demo_multivariable)
        elif chapter_num == "7":
            self._render_sections(content, get_calculus_apps_sections())
            if HAS_SYMPY and HAS_PLOT:
                self._add_demo_button(content, "📊 微分学应用演示", demos.demo_calculus_apps)
        elif chapter_num == "8":
            exercises.render_exercises(content)

    def _render_chapter1(self, parent):
        """第 1 章使用 _render_one_section + 内联演示按钮"""
        demo_map = {
            "1.1 向量的概念":        (demos.demo_vector_concept,   "📐 查看图形解释",       MacColors.CH1),
            "1.1.1 向量几何意义详解 ⭐": (demos.demo_vector_meaning,  "🎨 查看向量几何意义图",  MacColors.CH1),
            "1.2 向量的表示法":       (demos.demo_vector_decompose, "📊 查看分解图",         MacColors.CH1),
            "1.3 向量的线性运算":     (demos.demo_vector_add,       "➕ 查看加法图",         MacColors.CH1),
            "1.4 数量积（点积）":     (demos.demo_vector_dot,       "✖️ 查看几何图",         MacColors.CH1),
            "1.5 向量积（叉积）":     (demos.demo_vector_cross,     "⊗ 查看叉积图",         MacColors.CH1),
        }

        for title, items in get_vector_algebra_sections():
            self._render_one_section(parent, title, items)
            if HAS_PLOT and title in demo_map:
                func, btn_text, btn_color = demo_map[title]
                self._add_inline_demo(parent, btn_text, func, btn_color)

    # ────────────────────────────────────────────
    #  通用渲染组件
    # ────────────────────────────────────────────

    def _render_sections(self, parent, sections):
        """渲染 [(标题, 内容行列表), ...]"""
        for title, items in sections:
            card = CTkFrame(
                parent, fg_color=MacColors.CARD_BG, corner_radius=10,
                border_width=1, border_color=MacColors.BORDER,
            )
            card.pack(fill="x", pady=8)

            # 标题
            CTkLabel(
                card, text=title,
                font=ctk.CTkFont(family=self._font_family, size=16, weight="bold"),
                text_color=MacColors.TEXT_PRIMARY,
            ).pack(anchor="w", padx=20, pady=(15, 8))

            # 内容
            content_text = "\n".join(items)
            textbox = CTkTextbox(
                card, font=ctk.CTkFont(size=13, family="Consolas"),
                fg_color="transparent", text_color=MacColors.TEXT_PRIMARY,
                activate_scrollbars=False,
                height=max(60, len(items) * 22),
            )
            textbox.pack(fill="x", padx=20, pady=(0, 15))
            textbox.insert("1.0", content_text)
            textbox.configure(state="disabled")

    def _render_one_section(self, parent, title, items):
        """渲染单个段落（用于第 1 章，每个段落独立处理）"""
        card = CTkFrame(
            parent, fg_color=MacColors.CARD_BG, corner_radius=10,
            border_width=1, border_color=MacColors.BORDER,
        )
        card.pack(fill="x", pady=8)

        CTkLabel(
            card, text=title,
            font=ctk.CTkFont(family=self._font_family, size=16, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(15, 8))

        content_text = "\n".join(items)
        textbox = CTkTextbox(
            card, font=ctk.CTkFont(size=13, family="Consolas"),
            fg_color="transparent", text_color=MacColors.TEXT_PRIMARY,
            activate_scrollbars=False,
            height=max(60, len(items) * 22),
        )
        textbox.pack(fill="x", padx=20, pady=(0, 15))
        textbox.insert("1.0", content_text)
        textbox.configure(state="disabled")

    def _add_inline_demo(self, parent, text, command, color=None):
        """内联演示按钮（嵌入章节内容中）"""
        if color is None:
            color = MacColors.ACCENT
        btn_frame = CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 5))

        CTkButton(
            btn_frame, text=f"{text}  ›",
            font=ctk.CTkFont(family=self._font_family, size=12, weight="bold"),
            fg_color=color, hover_color=MacColors.ACCENT_HOVER,
            text_color="#FFFFFF",
            height=32, corner_radius=8,
            command=command,
        ).pack(anchor="w")

    def _add_demo_button(self, parent, text, command):
        """底部演示按钮"""
        btn_frame = CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=12)

        CTkButton(
            btn_frame, text=f"{text}  ›",
            font=ctk.CTkFont(family=self._font_family, size=13, weight="bold"),
            fg_color=MacColors.ACCENT, hover_color=MacColors.ACCENT_HOVER,
            text_color="#FFFFFF",
            height=36, corner_radius=8,
            command=command,
        ).pack()

    # ────────────────────────────────────────────
    #  状态页 (macOS About 风格)
    # ────────────────────────────────────────────

    def _show_status(self):
        self._clear_content()

        content = CTkScrollableFrame(
            self.content_frame, fg_color=MacColors.BG, corner_radius=0,
        )
        content.pack(fill="both", expand=True, padx=40, pady=30)

        # 居中容器
        center = CTkFrame(content, fg_color="transparent")
        center.pack(expand=True)

        # 应用图标
        CTkLabel(
            center, text="📐",
            font=ctk.CTkFont(size=48),
        ).pack(pady=(20, 8))

        CTkLabel(
            center, text="数学教学",
            font=ctk.CTkFont(family=self._font_family, size=22, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY,
        ).pack(pady=(0, 2))

        CTkLabel(
            center, text="版本 1.0.0",
            font=ctk.CTkFont(family=self._font_family, size=12),
            text_color=MacColors.TEXT_SECONDARY,
        ).pack(pady=(0, 4))

        CTkLabel(
            center, text="空间解析几何 & 微分学",
            font=ctk.CTkFont(family=self._font_family, size=12),
            text_color=MacColors.TEXT_TERTIARY,
        ).pack(pady=(0, 20))

        # 分隔线
        CTkFrame(center, height=1, fg_color=MacColors.SUBTLE_BORDER).pack(
            fill="x", padx=40, pady=(0, 16))

        # 系统信息列表
        CTkLabel(
            center, text="系统信息",
            font=ctk.CTkFont(family=self._font_family, size=13, weight="bold"),
            text_color=MacColors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=40, pady=(0, 10))

        status_items = [
            ("sympy 符号运算", HAS_SYMPY,
             "已加载" if HAS_SYMPY else "未安装 (pip install sympy)"),
            ("matplotlib 图形", HAS_PLOT,
             "已加载" if HAS_PLOT else "未安装 (pip install matplotlib)"),
            ("customtkinter GUI", True, "已加载"),
        ]

        for name, ok, desc in status_items:
            row = CTkFrame(center, fg_color="transparent")
            row.pack(fill="x", padx=40, pady=3)

            CTkLabel(
                row, text=name,
                font=ctk.CTkFont(family=self._font_family, size=12),
                text_color=MacColors.TEXT_PRIMARY,
            ).pack(side="left")

            status_color = MacColors.SUCCESS if ok else MacColors.DANGER
            status_icon = "✓" if ok else "✗"
            CTkLabel(
                row, text=f"{status_icon}  {desc}",
                font=ctk.CTkFont(family=self._font_family, size=12),
                text_color=status_color,
            ).pack(side="right")


# ══════════════════════════════════════════════════════════════
#  启动
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = MathTutorApp()
    app.mainloop()
