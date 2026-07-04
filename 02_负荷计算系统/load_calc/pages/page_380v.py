# -*- coding: utf-8 -*-
"""380V配电系统详情页面"""
import tkinter as tk
from tkinter import ttk

from ..calc_engine import calc_subsystem_summary
from ..widgets import CardFrame, MetricCard, ScrollableFrame


class Page380V(ttk.Frame):
    """380V配电系统详情"""
    def __init__(self, master, hv_system=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hv_system = hv_system
        self._subsystem_index = 0
        self._create_widgets()

    def set_hv_system(self, hv_system):
        self.hv_system = hv_system
        self._subsystem_index = 0
        self.refresh()

    def _create_widgets(self):
        # 可滚动的容器
        sc = ScrollableFrame(self)
        sc.pack(fill="both", expand=True)
        content = sc.inner

        # 标题
        self.title_label = ttk.Label(content, text="380V配电系统详情",
                                     font=("微软雅黑", 18, "bold"),
                                     foreground="#2E7D32")
        self.title_label.pack(anchor="w", padx=20, pady=(15, 5))

        # 切换按钮
        nav_frame = ttk.Frame(content)
        nav_frame.pack(fill="x", padx=20, pady=(0, 10))
        ttk.Button(nav_frame, text="◀ 上一个系统",
                   command=self._prev_system).pack(side="left", padx=5)
        ttk.Button(nav_frame, text="下一个系统 ▶",
                   command=self._next_system).pack(side="left", padx=5)
        self.nav_label = ttk.Label(nav_frame, text="",
                                    font=("微软雅黑", 10), foreground="#666")
        self.nav_label.pack(side="left", padx=10)

        # 指标卡片
        self.metrics_frame = ttk.Frame(content)
        self.metrics_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.cards = {}
        for key, title, color, unit in [
            ("pc", "总有功", "#1565C0", "kW"),
            ("qc", "总无功", "#E65100", "kvar"),
            ("sc", "总视在", "#2E7D32", "kVA"),
            ("pf_before", "补偿前cosφ", "#F44336", ""),
            ("pf_after", "补偿后cosφ", "#4CAF50", ""),
            ("qc_comp", "补偿容量", "#FF9800", "kvar"),
        ]:
            card = MetricCard(self.metrics_frame, title, "0", unit, color, width=140)
            card.pack(side="left", padx=3)
            self.cards[key] = card

        # 颜色图例
        legend_frame = ttk.Frame(content)
        legend_frame.pack(fill="x", padx=20, pady=(0, 10))
        legend_items = [
            ("#1565C0", "有功功率"),
            ("#E65100", "无功功率"),
            ("#2E7D32", "视在功率"),
        ]
        for color, text in legend_items:
            cvs = tk.Canvas(legend_frame, width=14, height=14,
                           highlightthickness=0, bg="white")
            cvs.pack(side="left", padx=(0, 2))
            cvs.create_rectangle(2, 2, 12, 12, fill=color, outline="#ccc")
            ttk.Label(legend_frame, text=text + "  ",
                     font=("微软雅黑", 8), foreground="#888").pack(side="left")

        # 主区域：标签页显示各设备组
        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def refresh(self):
        if not self.hv_system:
            return
        # 清除旧标签
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        subs = self.hv_system.subsystems
        if not subs:
            return

        self._subsystem_index = max(0, min(self._subsystem_index, len(subs)-1))
        sub = subs[self._subsystem_index]
        self.title_label.configure(text=f"{sub.name} 详情")
        self.nav_label.configure(text=f"({self._subsystem_index+1}/{len(subs)})")

        summary = calc_subsystem_summary(sub)
        self.cards["pc"].update_value(f"{summary['pc']:.1f}")
        self.cards["qc"].update_value(f"{summary['qc']:.1f}")
        self.cards["sc"].update_value(f"{summary['sc']:.1f}")
        self.cards["pf_before"].update_value(f"{summary['pf_before']:.4f}")
        self.cards["pf_after"].update_value(f"{summary['pf_after']:.4f}")
        self.cards["qc_comp"].update_value(f"{summary['actual_qc']:.0f}")

        # 每个设备组分页
        for g in sub.groups:
            frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(frame, text=g.name[:12])

            # 设备组信息
            info_frame = ttk.Frame(frame)
            info_frame.pack(fill="x", pady=(0, 10))

            for row, (label, val) in enumerate([
                ("设备组名称", g.name),
                ("设备功率 Pe", f"{g.total_device_power:.2f} kW"),
                ("有功小计 (∑Pc)", f"{g.subtotal_pc:.2f} kW"),
                ("无功小计 (∑Qc)", f"{g.subtotal_qc:.2f} kvar"),
                ("视在小计 (∑Sc)", f"{g.subtotal_sc:.2f} kVA"),
                ("同时系数 K∑p", f"{g.kp}"),
                ("同时系数 K∑q", f"{g.kq}"),
                ("计算有功 Pc", f"{g.computed_pc:.2f} kW"),
                ("计算无功 Qc", f"{g.computed_qc:.2f} kvar"),
                ("计算视在 Sc", f"{g.computed_sc:.2f} kVA"),
                ("功率因数 cosφ", f"{g.power_factor:.4f}"),
            ]):
                ttk.Label(info_frame, text=label,
                         font=("微软雅黑", 9),
                         width=18, anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=1)
                ttk.Label(info_frame, text=val,
                         font=("微软雅黑", 9, "bold"),
                         anchor="w").grid(row=row, column=1, sticky="w", padx=5, pady=1)

    def _prev_system(self):
        if self._subsystem_index > 0:
            self._subsystem_index -= 1
            self.refresh()

    def _next_system(self):
        subs = self.hv_system.subsystems if self.hv_system else []
        if self._subsystem_index < len(subs) - 1:
            self._subsystem_index += 1
            self.refresh()
