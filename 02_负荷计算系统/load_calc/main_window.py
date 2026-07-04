# -*- coding: utf-8 -*-
"""主窗口与导航 - 顶部导航布局"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from tkinterdnd2.TkinterDnD import require as require_dnd
from ttkbootstrap.constants import *

from .config import APP_NAME, APP_SUBTITLE, APP_VERSION
from .widgets import StatusBar
from .data_loader import build_project_data
from . import data_persistence
from .calc_engine import calc_compensation
from .pages import DashboardPage, Page10KV, Page380V, EquipmentPage, ReportPage, DistributionPage


class MainWindow:
    """主窗口 - 顶部导航布局"""

    def __init__(self):
        self.root = tb.Window(themename="cosmo")
        require_dnd(self.root)
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 680)

        self.hv_system = data_persistence.load_data()
        if self.hv_system is None:
            self.hv_system = build_project_data()
            if data_persistence.SAVE_FILE:
                data_persistence.save_data(self.hv_system)

        self._create_layout()
        self._bind_events()
        self._refresh_all()

    def _create_layout(self):
        """创建整体布局"""
        # 顶部标题栏
        header = ttk.Frame(self.root, padding=(15, 8))
        header.pack(fill="x")

        ttk.Label(header, text=APP_NAME,
                  font=("微软雅黑", 16, "bold"),
                  foreground="#1a237e").pack(side="left")
        ttk.Label(header, text=f"v{APP_VERSION}",
                  font=("微软雅黑", 9), foreground="#aaa").pack(side="left", padx=(5, 0))
        ttk.Label(header, text=APP_SUBTITLE,
                  font=("微软雅黑", 9), foreground="#888").pack(side="left", padx=(20, 0))

        # 右侧：计算更新按钮
        self.btn_calc = ttk.Button(header, text="🔄  计算更新",
                                   command=self._calculate_all,
                                   style="success", width=14)
        self.btn_calc.pack(side="right")

        # 分隔线
        ttk.Separator(self.root, orient="horizontal").pack(fill="x")

        # 顶部导航栏
        self._create_top_nav()

        # 分隔线
        ttk.Separator(self.root, orient="horizontal").pack(fill="x")

        # 内容区（全宽）
        self.content = ttk.Frame(self.root)
        self.content.pack(fill="both", expand=True)

        # 创建各页面
        self.pages = {}
        self._create_pages()

        # 状态栏
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill="x")
        self.status_bar.set_text("就绪 - 数据已加载 ✓")

    def _create_top_nav(self):
        """创建顶部导航栏"""
        NAV_BG = "#f5f7fa"
        NAV_FG = "#333333"
        HOVER_BG = "#e3f2fd"
        ACTIVE_BG = "#bbdefb"
        SEP_COLOR = "#e0e0e0"

        nav_bar = tk.Frame(self.root, bg=NAV_BG, height=42)
        nav_bar.pack(fill="x")
        nav_bar.pack_propagate(False)

        inner = tk.Frame(nav_bar, bg=NAV_BG)
        inner.pack(expand=True)

        nav_items = [
            ("dashboard",    "📊  仪表盘"),
            ("10kv",         "⚡  10KV总览"),
            ("380v",         "🔌  380V详情"),
            ("distribution", "🗄  配电系统"),
            ("equipment",    "🔧  设备管理"),
            ("report",       "📋  报表导出"),
        ]

        self.nav_buttons = {}
        for i, (key, text) in enumerate(nav_items):
            if i > 0:
                sep = tk.Frame(inner, bg=SEP_COLOR, width=1, height=22)
                sep.pack(side="left", padx=2)

            btn = tk.Label(inner, text=text,
                           font=("微软雅黑", 11),
                           fg=NAV_FG, bg=NAV_BG,
                           padx=18, pady=8, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_page(k))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=HOVER_BG))
            btn.bind("<Leave>", lambda e, b=btn, k=key:
                     b.configure(bg=ACTIVE_BG if k == self._current_page else NAV_BG))
            self.nav_buttons[key] = btn

        self._current_page = "dashboard"
        self.nav_buttons["dashboard"].configure(bg=ACTIVE_BG)

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

        # 默认显示仪表盘
        self.pages["dashboard"].pack(fill="both", expand=True)

    def _switch_page(self, page_key: str):
        """切换页面"""
        if page_key == self._current_page:
            return

        # 隐藏当前页
        self.pages[self._current_page].pack_forget()

        # 更新导航高亮
        ACTIVE_BG = "#bbdefb"
        NORMAL_BG = "#f5f7fa"
        self.nav_buttons[self._current_page].configure(bg=NORMAL_BG)
        self.nav_buttons[page_key].configure(bg=ACTIVE_BG)

        # 显示新页面
        self.pages[page_key].pack(fill="both", expand=True)
        self.pages[page_key].refresh()

        # 更新状态栏
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
        # 定期刷新防止tkinterdnd2事件循环阻塞
        self._poll_interval = 500  # ms
        self._poll_after_id = None
        self._start_poller()

    def _start_poller(self):
        """启动定期轮询，保持事件循环通畅，防止长时间运行后死机"""
        try:
            self._poll_after_id = self.root.after(self._poll_interval, self._poller_tick)
        except tk.TclError:
            pass

    def _poller_tick(self):
        """轮询心跳：定期触发，保持事件循环活跃"""
        try:
            if self.root.winfo_exists():
                self._poll_after_id = self.root.after(self._poll_interval, self._poller_tick)
        except (tk.TclError, RuntimeError):
            pass

    def _refresh_all(self):
        """刷新所有页面"""
        for page in self.pages.values():
            page.refresh()

    def _on_data_changed(self):
        """数据变更回调 - 重新计算补偿并刷新所有页面"""
        self._full_recalculation()
        self.status_bar.set_text("数据已更新 ✓ 补偿已重算 全页面同步刷新")

    def _full_recalculation(self):
        """全量重算：先保存DistributionPage编辑，再对每个子系统重算补偿"""
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
        """计算更新 - 全量计算并刷新所有页面"""
        self._full_recalculation()
        self.status_bar.set_text("✅ 全系统计算更新完成 - 所有数据已同步")

    def run(self):
        """运行主窗口"""
        self.root.mainloop()

    def _on_close(self):
        """关闭窗口 - 先取消定时器、保存数据再退出"""
        # 取消after定时器，防止资源泄漏
        try:
            if self._poll_after_id is not None:
                self.root.after_cancel(self._poll_after_id)
                self._poll_after_id = None
        except Exception:
            pass
        try:
            if hasattr(self, 'hv_system') and self.hv_system is not None:
                from . import data_persistence
                data_persistence.save_data(self.hv_system)
        except Exception:
            pass
        # 强制释放所有grab
        try:
            while self.root.grab_current():
                self.root.grab_current().grab_release()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        # 强制退出（应对tkinterdnd2事件钩子阻塞）
        import os
        os._exit(0)
