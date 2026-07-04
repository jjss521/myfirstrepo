# -*- coding: utf-8 -*-
"""380V配电系统详情页面 - Apple 简约优雅风格"""
import tkinter as tk
from tkinter import ttk

from ..calc_engine import calc_subsystem_summary
from ..widgets import CardFrame, MetricCard, ScrollableFrame
from ..config import THEME, blend_color, FONT_UI, FONT_DISPLAY, FS


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
        sc = ScrollableFrame(self)
        sc.pack(fill="both", expand=True)
        content = sc.inner

        # 标题
        title_frame = tk.Frame(content, bg=THEME["BG_MAIN"])
        title_frame.pack(fill="x", padx=20, pady=(15, 5))
        accent = tk.Frame(title_frame, bg=THEME["ACCENT_GREEN"], width=4, height=24)
        accent.pack(side="left", padx=(0, 10))
        self.title_label = tk.Label(title_frame, text="380V配电系统详情",
                                    font=(FONT_DISPLAY, FS[18], "bold"),
                                    fg=THEME["ACCENT_GREEN"], bg=THEME["BG_MAIN"])
        self.title_label.pack(side="left")

        # 切换按钮
        nav_frame = tk.Frame(content, bg=THEME["BG_MAIN"])
        nav_frame.pack(fill="x", padx=20, pady=(0, 10))

        btn_style = {
            "font": (FONT_UI, FS[10]),
            "fg": THEME["ACCENT_BLUE"],
            "bg": blend_color(THEME["ACCENT_BLUE"], THEME["BG_CARD"], 0.08),
            "cursor": "hand2",
            "padx": 14, "pady": 4,
        }
        prev_btn = tk.Label(nav_frame, text="< 上一个系统", **btn_style)
        prev_btn.pack(side="left", padx=5)
        prev_btn.bind("<Button-1>", lambda e: self._prev_system())
        prev_btn.bind("<Enter>", lambda e: prev_btn.configure(
            bg=blend_color(THEME["ACCENT_BLUE"], THEME["BG_CARD"], 0.15)))
        prev_btn.bind("<Leave>", lambda e: prev_btn.configure(
            bg=blend_color(THEME["ACCENT_BLUE"], THEME["BG_CARD"], 0.08)))

        next_btn = tk.Label(nav_frame, text="下一个系统 >", **btn_style)
        next_btn.pack(side="left", padx=5)
        next_btn.bind("<Button-1>", lambda e: self._next_system())
        next_btn.bind("<Enter>", lambda e: next_btn.configure(
            bg=blend_color(THEME["ACCENT_BLUE"], THEME["BG_CARD"], 0.15)))
        next_btn.bind("<Leave>", lambda e: next_btn.configure(
            bg=blend_color(THEME["ACCENT_BLUE"], THEME["BG_CARD"], 0.08)))

        self.nav_label = tk.Label(nav_frame, text="",
                                  font=(FONT_UI, FS[10]),
                                  fg=THEME["FG_SECONDARY"], bg=THEME["BG_MAIN"])
        self.nav_label.pack(side="left", padx=10)

        # 指标卡片
        self.metrics_frame = tk.Frame(content, bg=THEME["BG_MAIN"])
        self.metrics_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.cards = {}
        for key, title, color, unit in [
            ("pc", "总有功", THEME["ACCENT_BLUE"], "kW"),
            ("qc", "总无功", THEME["ACCENT_ORANGE"], "kvar"),
            ("sc", "总视在", THEME["ACCENT_GREEN"], "kVA"),
            ("pf_before", "补偿前cos\u03c6", THEME["ACCENT_RED"], ""),
            ("pf_after", "补偿后cos\u03c6", THEME["ACCENT_GREEN"], ""),
            ("qc_comp", "补偿容量", THEME["ACCENT_ORANGE"], "kvar"),
        ]:
            card = MetricCard(self.metrics_frame, title, "0", unit, color, width=140)
            card.pack(side="left", padx=3)
            self.cards[key] = card

        # 颜色图例
        legend_frame = tk.Frame(content, bg=THEME["BG_MAIN"])
        legend_frame.pack(fill="x", padx=20, pady=(0, 10))
        legend_items = [
            (THEME["ACCENT_BLUE"], "有功功率"),
            (THEME["ACCENT_ORANGE"], "无功功率"),
            (THEME["ACCENT_GREEN"], "视在功率"),
        ]
        for color, text in legend_items:
            cvs = tk.Canvas(legend_frame, width=14, height=14,
                           highlightthickness=0, bg=THEME["BG_CARD"])
            cvs.pack(side="left", padx=(0, 2))
            cvs.create_rectangle(2, 2, 12, 12, fill=color, outline=THEME["BORDER"])
            tk.Label(legend_frame, text=text + "  ",
                     font=(FONT_UI, FS[8]),
                     fg=THEME["FG_MUTED"], bg=THEME["BG_MAIN"]).pack(side="left")

        # 主区域：标签页显示各设备组
        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def refresh(self):
        if not self.hv_system:
            return
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
            frame = tk.Frame(self.notebook, bg=THEME["BG_MAIN"], padx=10, pady=10)
            self.notebook.add(frame, text=g.name[:12])

            # 设备组信息卡片
            info_card = CardFrame(frame, g.name, padding=10)
            info_card.pack(fill="both", expand=True, padx=10, pady=5)

            info_frame = tk.Frame(info_card, bg=THEME["BG_CARD"])
            info_frame.pack(fill="both", expand=True)

            for row, (label, val) in enumerate([
                ("设备组名称", g.name),
                ("设备功率 Pe", f"{g.total_device_power:.2f} kW"),
                ("有功小计 (Pc)", f"{g.subtotal_pc:.2f} kW"),
                ("无功小计 (Qc)", f"{g.subtotal_qc:.2f} kvar"),
                ("视在小计 (Sc)", f"{g.subtotal_sc:.2f} kVA"),
                ("同时系数 Kp", f"{g.kp}"),
                ("同时系数 Kq", f"{g.kq}"),
                ("计算有功 Pc", f"{g.computed_pc:.2f} kW"),
                ("计算无功 Qc", f"{g.computed_qc:.2f} kvar"),
                ("计算视在 Sc", f"{g.computed_sc:.2f} kVA"),
                ("功率因数 cos\u03c6", f"{g.power_factor:.4f}"),
            ]):
                bg = THEME["BG_CARD"] if row % 2 == 0 else THEME["BG_CARD_ALT"]
                row_frame = tk.Frame(info_frame, bg=bg)
                row_frame.pack(fill="x", pady=1)

                tk.Label(row_frame, text=label,
                         font=(FONT_UI, FS[9]),
                         fg=THEME["FG_SECONDARY"], bg=bg,
                         width=18, anchor="w").pack(side="left", padx=5, pady=2)
                tk.Label(row_frame, text=val,
                         font=(FONT_UI, FS[9], "bold"),
                         fg=THEME["FG_PRIMARY"], bg=bg,
                         anchor="w").pack(side="left", padx=5, pady=2)

    def _prev_system(self):
        if self._subsystem_index > 0:
            self._subsystem_index -= 1
            self.refresh()

    def _next_system(self):
        subs = self.hv_system.subsystems if self.hv_system else []
        if self._subsystem_index < len(subs) - 1:
            self._subsystem_index += 1
            self.refresh()
