# -*- coding: utf-8 -*-
"""10KV全厂总览页面"""
import tkinter as tk
from tkinter import ttk

from ..calc_engine import calc_subsystem_summary, calc_hv_system_summary
from ..widgets import CardFrame, InfoRow, MetricCard, ScrollableFrame


class Page10KV(ttk.Frame):
    """10kV高压系统总览"""
    def __init__(self, master, hv_system=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hv_system = hv_system
        self._create_widgets()

    def set_hv_system(self, hv_system):
        self.hv_system = hv_system
        self.refresh()

    def _create_widgets(self):
        # 可滚动的容器
        sc = ScrollableFrame(self)
        sc.pack(fill="both", expand=True)
        content = sc.inner

        # 标题
        title = ttk.Label(content, text="二期全厂10KV负荷总览",
                         font=("微软雅黑", 18, "bold"),
                         foreground="#1565C0")
        title.pack(anchor="w", padx=20, pady=(15, 5))

        # 指标卡片
        self.metrics_frame = ttk.Frame(content)
        self.metrics_frame.pack(fill="x", padx=20, pady=(5, 15))

        self.cards = {}
        for key, title, color, unit in [
            ("hv_pc", "总有功功率", "#1565C0", "kW"),
            ("hv_qc", "总无功功率", "#E65100", "kvar"),
            ("hv_sc", "总视在功率", "#2E7D32", "kVA"),
            ("hv_pf", "功率因数", "#6A1B9A", ""),
            ("hv_rate", "变压器总容量", "#00838F", "kVA"),
        ]:
            card = MetricCard(self.metrics_frame, title, "0", unit, color, width=170)
            card.pack(side="left", padx=5)
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

        # 子系统详情表格
        detail_frame = CardFrame(content, "各子系统10KV侧负荷核定", padding=10)
        detail_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        columns = ("name", "pc", "qc", "sc", "pf", "trans_cap", "load_rate",
                   "loss_p", "loss_q")
        self.tree = ttk.Treeview(detail_frame, columns=columns,
                                 show="headings", height=6)
        col_config = [
            ("name", "子系统名称", 200),
            ("pc", "Pc(kW)", 100),
            ("qc", "Qc(kvar)", 100),
            ("sc", "Sc(kVA)", 100),
            ("pf", "cosφ", 80),
            ("trans_cap", "变压器(kVA)", 110),
            ("load_rate", "负载率(%)", 90),
            ("loss_p", "ΔP(kW)", 80),
            ("loss_q", "ΔQ(kvar)", 90),
        ]
        for key, text, w in col_config:
            self.tree.heading(key, text=text)
            self.tree.column(key, width=w, anchor="center")
        self.tree.column("name", anchor="w")

        # 数值单位说明
        unit_note = ttk.Label(detail_frame,
                              text="注: Pc=有功功率(kW)  Qc=无功功率(kvar)  Sc=视在功率(kVA)  cosφ=功率因数",
                              font=("微软雅黑", 8), foreground="#aaa")
        unit_note.pack(anchor="w", padx=5, pady=(3, 0))

        vsb = ttk.Scrollbar(detail_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def refresh(self):
        if not self.hv_system:
            return
        summary = calc_hv_system_summary(self.hv_system)

        self.cards["hv_pc"].update_value(f"{summary['total_pc']:.1f}")
        self.cards["hv_qc"].update_value(f"{summary['total_qc']:.1f}")
        self.cards["hv_sc"].update_value(f"{summary['total_sc']:.1f}")
        pf = summary["power_factor"]
        self.cards["hv_pf"].update_value(f"{pf:.4f}",
                                          "#4CAF50" if pf >= 0.9 else "#FF9800")

        total_cap = sum(s.transformer_rating * s.transformer_count
                        for s in self.hv_system.subsystems)
        self.cards["hv_rate"].update_value(f"{total_cap:.0f}")

        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in summary["subsystems"]:
            sm = s["summary"]
            self.tree.insert("", "end", values=(
                s["name"],
                f"{sm['hv_pc']:.2f}",
                f"{sm['hv_qc']:.2f}",
                f"{sm['hv_sc']:.2f}",
                f"{sm['hv_pf']:.4f}",
                f"{sm['transformer_capacity']:.0f}",
                f"{sm['load_rate']*100:.1f}",
                f"{sm['transformer_loss_p']:.2f}",
                f"{sm['transformer_loss_q']:.2f}",
            ))
