# -*- coding: utf-8 -*-
"""主窗口与导航 - Apple 简约优雅风格导航布局"""

import tkinter as tk
from tkinter import ttk
import sys
import logging
import ttkbootstrap as tb
from tkinterdnd2.TkinterDnD import require as require_dnd
from ttkbootstrap.constants import *

from .config import APP_NAME, APP_SUBTITLE, APP_VERSION, THEME, TTK_THEME, apply_dark_theme, blend_color, FONT_UI, FONT_DISPLAY, FS
from .widgets import StatusBar
from .data_loader import build_project_data
from . import data_persistence
from .calc_engine import calc_compensation
from .pages import DashboardPage, Page10KV, Page380V, EquipmentPage, ReportPage, DistributionPage

logger = logging.getLogger(__name__)


class MainWindow:
    """主窗口 - Apple 简约优雅顶部导航布局"""

    def __init__(self):
        self.root = tb.Window(themename=TTK_THEME)
        require_dnd(self.root)
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 680)
        self.root.configure(bg=THEME["BG_MAIN"])

        # 应用深色主题
        apply_dark_theme(self.root)

        self.hv_system = data_persistence.load_data()
        if self.hv_system is None:
            logger.info("无保存数据，加载预设数据")
            self.hv_system = build_project_data()
            if self.hv_system is not None:
                data_persistence.save_data(self.hv_system)

        self._create_layout()
        self._bind_events()
        self._refresh_all()

    def _create_layout(self):
        """创建整体布局"""
        # ── Header ──
        header = tk.Frame(self.root, bg=THEME["BG_CARD"], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        # 左侧蓝色竖线装饰
        accent_bar = tk.Frame(header, bg=THEME["ACCENT_BLUE"], width=3, height=30)
        accent_bar.pack(side="left", padx=(12, 8), pady=13)

        # 标题文字
        title_frame = tk.Frame(header, bg=THEME["BG_CARD"])
        title_frame.pack(side="left", padx=(0, 0))

        tk.Label(title_frame, text=APP_NAME,
                 font=(FONT_UI, FS[15], "bold"),
                 fg=THEME["FG_PRIMARY"], bg=THEME["BG_CARD"]).pack(side="left")
        tk.Label(title_frame, text=f"v{APP_VERSION}",
                 font=(FONT_UI, FS[9]),
                 fg=THEME["FG_MUTED"], bg=THEME["BG_CARD"]).pack(side="left", padx=(8, 0), pady=(4, 0))

        # 英文副标题
        tk.Label(header, text=APP_SUBTITLE,
                 font=(FONT_UI, FS[9]),
                 fg=THEME["FG_MUTED"], bg=THEME["BG_CARD"]).pack(side="left", padx=(20, 0))

        # 右侧计算按钮 - Apple蓝色风格
        self.btn_calc = tk.Label(header, text="⟳  计算更新",
                                 font=(FONT_UI, FS[11], "bold"),
                                 fg="#FFFFFF",
                                 bg=THEME["ACCENT_BLUE"],
                                 padx=16, pady=6, cursor="hand2")
        self.btn_calc.pack(side="right", padx=15, pady=10)
        self.btn_calc.bind("<Button-1>", lambda e: self._calculate_all())
        self.btn_calc.bind("<Enter>", lambda e: self.btn_calc.configure(
            bg=blend_color(THEME["ACCENT_BLUE"], "#000000", 0.15)))
        self.btn_calc.bind("<Leave>", lambda e: self.btn_calc.configure(
            bg=THEME["ACCENT_BLUE"]))

        # Header底部分隔线
        sep_frame = tk.Frame(self.root, bg=THEME["SEPARATOR"], height=1)
        sep_frame.pack(fill="x")

        # ── Navigation Bar ──
        self._create_top_nav()

        # Nav底部分隔线
        sep_frame2 = tk.Frame(self.root, bg=THEME["SEPARATOR"], height=1)
        sep_frame2.pack(fill="x")

        # ── Content Area ──
        self.content = tk.Frame(self.root, bg=THEME["BG_MAIN"])
        self.content.pack(fill="both", expand=True)

        self.pages = {}
        self._create_pages()

        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill="x")
        self.status_bar.set_text("就绪 - 数据已加载")

    def _create_top_nav(self):
        """创建顶部导航栏 - Apple简约白色风格"""
        NAV_BG = THEME["BG_NAV"]
        NAV_FG = THEME["FG_SECONDARY"]
        ACTIVE_FG = THEME["ACCENT_BLUE"]
        ACTIVE_BG = blend_color(THEME["ACCENT_BLUE"], NAV_BG, 0.08)
        SEP_COLOR = THEME["SEPARATOR"]

        nav_bar = tk.Frame(self.root, bg=NAV_BG, height=44)
        nav_bar.pack(fill="x")
        nav_bar.pack_propagate(False)

        inner = tk.Frame(nav_bar, bg=NAV_BG)
        inner.pack(expand=True)

        nav_items = [
            ("dashboard",    "◆  仪表盘"),
            ("10kv",         "◆  10KV总览"),
            ("380v",         "◆  380V详情"),
            ("distribution", "◆  配电系统"),
            ("equipment",    "◆  设备管理"),
            ("report",       "◆  报表导出"),
        ]

        self.nav_buttons = {}
        self._nav_fg_colors = {}
        for i, (key, text) in enumerate(nav_items):
            if i > 0:
                sep = tk.Frame(inner, bg=SEP_COLOR, width=1, height=20)
                sep.pack(side="left", padx=2)

            # 导航按钮
            btn_frame = tk.Frame(inner, bg=NAV_BG)
            btn_frame.pack(side="left")

            # 底部指示条
            indicator = tk.Frame(btn_frame, bg=NAV_BG, height=2)
            indicator.pack(fill="x")

            btn = tk.Label(btn_frame, text=text,
                          font=(FONT_UI, FS[11]),
                          fg=NAV_FG, bg=NAV_BG,
                          padx=16, pady=8, cursor="hand2")
            btn.pack()

            btn.bind("<Button-1>", lambda e, k=key: self._switch_page(k))
            btn.bind("<Enter>", lambda e, b=btn, ind=indicator, k=key:
                     self._nav_hover(b, ind, k))
            btn.bind("<Leave>", lambda e, b=btn, ind=indicator, k=key:
                     self._nav_leave(b, ind, k))

            self.nav_buttons[key] = btn
            self._nav_fg_colors[key] = (btn, indicator)

        self._current_page = "dashboard"
        self._activate_nav("dashboard")

    def _nav_hover(self, btn, indicator, key):
        """导航悬停效果"""
        if key != self._current_page:
            btn.configure(fg=THEME["FG_PRIMARY"])
            indicator.configure(bg=blend_color(THEME["ACCENT_BLUE"], THEME["BG_NAV"], 0.2))

    def _nav_leave(self, btn, indicator, key):
        """导航离开效果"""
        if key != self._current_page:
            btn.configure(fg=THEME["FG_SECONDARY"])
            indicator.configure(bg=THEME["BG_NAV"])

    def _activate_nav(self, key):
        """激活导航项"""
        ACTIVE_FG = THEME["ACCENT_BLUE"]
        ACTIVE_BG = blend_color(THEME["ACCENT_BLUE"], THEME["BG_NAV"], 0.08)
        NAV_FG = THEME["FG_SECONDARY"]
        NAV_BG = THEME["BG_NAV"]

        # 重置所有
        for k, (btn, ind) in self._nav_fg_colors.items():
            btn.configure(fg=NAV_FG, bg=NAV_BG)
            ind.configure(bg=NAV_BG)

        # 激活当前
        btn, ind = self._nav_fg_colors[key]
        btn.configure(fg=ACTIVE_FG, bg=ACTIVE_BG)
        ind.configure(bg=THEME["ACCENT_BLUE"])

    def _create_pages(self):
        """创建所有页面"""
        page_classes = {
            "dashboard": DashboardPage,
            "10kv": Page10KV,
            "380v": Page380V,
            "distribution": DistributionPage,
            "equipment": EquipmentPage,
            "report": ReportPage,
        }
        for key, cls in page_classes.items():
            kwargs = {}
            if key == "equipment":
                kwargs["notify_callback"] = self._on_data_changed
            if key == "distribution":
                kwargs["data_changed_callback"] = self._on_data_changed
            page = cls(self.content, hv_system=self.hv_system, **kwargs)
            self.pages[key] = page

        self.pages["dashboard"].pack(fill="both", expand=True)

    def _switch_page(self, page_key: str):
        """切换页面"""
        if page_key == self._current_page:
            return

        self.pages[self._current_page].pack_forget()

        self._activate_nav(page_key)

        self.pages[page_key].pack(fill="both", expand=True)
        self.pages[page_key].refresh()

        page_names = {
            "dashboard": "仪表盘",
            "10kv": "10KV全厂总览",
            "380v": "380V配电系统详情",
            "distribution": "配电系统总负荷计算",
            "equipment": "设备管理",
            "report": "报表导出",
        }
        self.status_bar.set_text(f"当前页面: {page_names.get(page_key, page_key)}")

        self._current_page = page_key

    def _bind_events(self):
        """绑定事件"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _refresh_all(self):
        """刷新所有页面"""
        for page in self.pages.values():
            page.refresh()

    def _on_data_changed(self):
        """数据变更回调"""
        self._full_recalculation()
        self.status_bar.set_text("数据已更新  补偿已重算  全页面同步刷新")

    def _full_recalculation(self):
        """全量重算"""
        dist_page = self.pages.get("distribution")
        if dist_page and hasattr(dist_page, "save_all_subsystem_tabs"):
            dist_page.save_all_subsystem_tabs()

        for sub in self.hv_system.subsystems:
            total_pc = sub.total_pc
            total_qc = sub.total_qc
            result = calc_compensation(total_pc, total_qc, sub.target_power_factor)
            sub.compensation_qc = result.actual_qc

        self._refresh_all()

    def _calculate_all(self):
        """计算更新"""
        self._full_recalculation()
        self.status_bar.set_text("全系统计算更新完成 - 所有数据已同步")

    def run(self):
        """运行主窗口"""
        self.root.mainloop()

    def _on_close(self):
        """关闭窗口 - 安全退出"""
        try:
            if hasattr(self, 'hv_system') and self.hv_system is not None:
                data_persistence.save_data(self.hv_system)
                logger.info("应用程序数据已保存")
        except Exception:
            logger.exception("保存数据时出错")

        try:
            while self.root.grab_current():
                self.root.grab_current().grab_release()
        except Exception:
            logger.debug("释放grab时出错", exc_info=True)

        try:
            self.root.destroy()
        except Exception:
            logger.debug("销毁窗口时出错", exc_info=True)

        sys.exit(0)
