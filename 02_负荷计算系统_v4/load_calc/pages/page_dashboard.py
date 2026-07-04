# -*- coding: utf-8 -*-
"""仪表盘页面 - Apple 简约优雅风格"""
import tkinter as tk
from tkinter import ttk
from math import sqrt

from ..config import APP_NAME, THEME, PIE_COLORS, blend_color, FONT_UI, FONT_DISPLAY, FONT_MONO, FONT_CHART, MATPLOTLIB_FONT_FAMILY, FS
from ..models import LOAD_LEVEL_SECONDARY, LOAD_LEVEL_TERTIARY
from ..widgets import CardFrame, InfoRow, MetricCard, ScrollableFrame


class DashboardPage(ttk.Frame):
    """主仪表盘 - 显示全厂负荷概况"""

    PIE_COLORS = PIE_COLORS

    def __init__(self, master, hv_system=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hv_system = hv_system
        self._chart_canvas = None
        self._create_widgets()

    def set_hv_system(self, hv_system):
        self.hv_system = hv_system
        self.refresh()

    def _create_widgets(self):
        sc = ScrollableFrame(self)
        sc.pack(fill="both", expand=True)
        content = sc.inner

        # 标题区
        title_frame = tk.Frame(content, bg=THEME["BG_MAIN"])
        title_frame.pack(fill="x", padx=20, pady=(20, 5))

        # 蓝色竖线装饰 + 标题
        accent = tk.Frame(title_frame, bg=THEME["ACCENT_BLUE"], width=4, height=28)
        accent.pack(side="left", padx=(0, 10))
        tk.Label(title_frame, text=APP_NAME,
                 font=(FONT_DISPLAY, FS[20], "bold"),
                 fg=THEME["FG_PRIMARY"], bg=THEME["BG_MAIN"]).pack(side="left")

        subtitle = tk.Label(content, text="Wastewater Treatment Plant Load Calculation System",
                            font=(FONT_UI, FS[10]),
                            fg=THEME["FG_MUTED"], bg=THEME["BG_MAIN"])
        subtitle.pack(anchor="w", padx=20, pady=(0, 15))

        # 指标卡片
        self.metrics_frame = tk.Frame(content, bg=THEME["BG_MAIN"])
        self.metrics_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.cards = {}
        metrics = [
            ("total_pc", "补偿后有功功率", THEME["ACCENT_BLUE"], "kW"),
            ("total_qc", "补偿后无功功率", THEME["ACCENT_ORANGE"], "kvar"),
            ("total_sc", "补偿后视在功率", THEME["ACCENT_GREEN"], "kVA"),
            ("power_factor", "补偿后功率因数", THEME["ACCENT_PURPLE"], ""),
        ]
        for key, title, color, unit in metrics:
            card = MetricCard(self.metrics_frame, title, "", unit, color, width=200)
            card.pack(side="left", padx=5, pady=5)
            self.cards[key] = card

        # 中间区域：系统概览 + 饼图
        main = tk.Frame(content, bg=THEME["BG_MAIN"])
        main.pack(fill="both", expand=True, padx=20, pady=5)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=3)

        overview_frame = CardFrame(main, "系统概览", padding=15)
        overview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.overview_text = tk.Text(overview_frame, height=18, width=50,
                                     font=(FONT_MONO, FS[10]),
                                     bg=THEME["BG_CARD"], fg=THEME["FG_PRIMARY"],
                                     insertbackground=THEME["ACCENT_BLUE"],
                                     selectbackground=THEME["BG_ACTIVE"],
                                     relief="flat", wrap="word",
                                     highlightbackground=THEME["BORDER"],
                                     highlightthickness=1)
        self.overview_text.pack(fill="both", expand=True)

        self.chart_frame = tk.Frame(main, bg=THEME["BG_MAIN"])
        self.chart_frame.grid(row=0, column=1, sticky="nsew")

        # 底部区域：负荷分布表 + 设备组统计
        bottom_frame = tk.Frame(content, bg=THEME["BG_MAIN"])
        bottom_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)

        dist_card = CardFrame(bottom_frame, "负荷分布表", padding=10)
        dist_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.dist_tree = ttk.Treeview(dist_card,
                                      columns=("system", "pc", "qc", "sc", "pf"),
                                      show="headings", height=8)
        self.dist_tree.heading("system", text="系统名称")
        self.dist_tree.heading("pc", text="Pc(kW)")
        self.dist_tree.heading("qc", text="Qc(kvar)")
        self.dist_tree.heading("sc", text="Sc(kVA)")
        self.dist_tree.heading("pf", text="cos\u03c6")
        self.dist_tree.column("system", width=180)
        self.dist_tree.column("pc", width=90, anchor="center")
        self.dist_tree.column("qc", width=90, anchor="center")
        self.dist_tree.column("sc", width=90, anchor="center")
        self.dist_tree.column("pf", width=70, anchor="center")

        vsb = ttk.Scrollbar(dist_card, orient="vertical", command=self.dist_tree.yview)
        self.dist_tree.configure(yscrollcommand=vsb.set)
        self.dist_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        group_card = CardFrame(bottom_frame, "设备组统计明细", padding=10)
        group_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.group_tree = ttk.Treeview(group_card,
                                       columns=("group", "pe", "pc", "qc", "sc", "kp"),
                                       show="headings", height=8)
        cols = [("group", "设备组名称", 180), ("pe", "Pe(kW)", 80),
                ("pc", "Pc(kW)", 80), ("qc", "Qc(kvar)", 80),
                ("sc", "Sc(kVA)", 80), ("kp", "K\u2211p", 60)]
        for key, text, width in cols:
            self.group_tree.heading(key, text=text)
            self.group_tree.column(key, width=width, anchor="center")

        vsb2 = ttk.Scrollbar(group_card, orient="vertical", command=self.group_tree.yview)
        self.group_tree.configure(yscrollcommand=vsb2.set)
        self.group_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

        # 负荷分级
        load_card = CardFrame(content, "负荷分级（二级/三级负荷分析）", padding=10)
        load_card.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        lf_top = tk.Frame(load_card, bg=THEME["BG_CARD"])
        lf_top.pack(fill="both", expand=True)
        lf_top.columnconfigure(0, weight=2)
        lf_top.columnconfigure(1, weight=3)

        self.load_chart_frame = tk.Frame(lf_top, bg=THEME["BG_CARD"])
        self.load_chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        load_table_frame = tk.Frame(lf_top, bg=THEME["BG_CARD"])
        load_table_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        columns = ("sub", "group", "eq", "pc", "level")
        self.load_level_tree = ttk.Treeview(load_table_frame,
                                            columns=columns,
                                            show="headings", height=8)
        col_cfgs = [
            ("sub", "子系统", 120),
            ("group", "建/构筑物", 120),
            ("eq", "设备名称", 120),
            ("pc", "Pc(kW)", 90),
            ("level", "负荷等级", 80),
        ]
        for key, text, w in col_cfgs:
            self.load_level_tree.heading(key, text=text)
            self.load_level_tree.column(key, width=w, anchor="center")
        self.load_level_tree.column("eq", anchor="w")
        self.load_level_tree.column("level", anchor="w")

        vsb3 = ttk.Scrollbar(load_table_frame, orient="vertical",
                             command=self.load_level_tree.yview)
        self.load_level_tree.configure(yscrollcommand=vsb3.set)
        self.load_level_tree.pack(side="left", fill="both", expand=True)
        vsb3.pack(side="right", fill="y")

        self.load_summary_label = tk.Label(load_card, text="",
                                           font=(FONT_UI, FS[10], "bold"),
                                           fg=THEME["FG_PRIMARY"], bg=THEME["BG_CARD"])
        self.load_summary_label.pack(anchor="w", padx=5, pady=(5, 0))

    def _draw_pie_chart(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            import matplotlib
            matplotlib.rcParams['font.sans-serif'] = MATPLOTLIB_FONT_FAMILY
            matplotlib.rcParams['axes.unicode_minus'] = False
            matplotlib.rcParams['figure.facecolor'] = THEME["BG_CARD"]
            matplotlib.rcParams['axes.facecolor'] = THEME["BG_CARD"]
            matplotlib.rcParams['text.color'] = THEME["FG_PRIMARY"]
            matplotlib.rcParams['axes.labelcolor'] = THEME["FG_SECONDARY"]
            matplotlib.rcParams['xtick.color'] = THEME["FG_SECONDARY"]
            matplotlib.rcParams['ytick.color'] = THEME["FG_SECONDARY"]
        except ImportError:
            tk.Label(self.chart_frame,
                     text="需要安装 matplotlib 库以显示图表\npip install matplotlib",
                     font=(FONT_UI, FS[11]), fg=THEME["FG_MUTED"],
                     bg=THEME["BG_MAIN"]).pack(expand=True)
            return

        labels = []
        sizes = []
        for sub in self.hv_system.subsystems:
            for g in sub.groups:
                pc = g.computed_pc
                if pc > 1.0:
                    name = g.name if len(g.name) <= 12 else g.name[:10] + ".."
                    labels.append(name)
                    sizes.append(pc)

        if not sizes:
            tk.Label(self.chart_frame,
                     text="暂无数据", font=(FONT_UI, FS[11]),
                     fg=THEME["FG_MUTED"], bg=THEME["BG_MAIN"]).pack(expand=True)
            return

        fig = Figure(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor(THEME["BG_CARD"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["BG_CARD"])

        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, autopct="%1.1f%%",
            colors=self.PIE_COLORS[:len(sizes)],
            startangle=90, pctdistance=0.75,
            textprops={"fontsize": 8, "color": THEME["FG_PRIMARY"]},
            wedgeprops={"edgecolor": THEME["BG_CARD"], "linewidth": 1.5},
        )

        legend_labels = [f"{l} ({s:.0f}kW)" for l, s in zip(labels, sizes)]
        ax.legend(wedges, legend_labels,
                  loc="center left", bbox_to_anchor=(1, 0.5),
                  fontsize=8, frameon=False,
                  facecolor=THEME["BG_CARD"],
                  labelcolor=THEME["FG_PRIMARY"])

        ax.set_title("各建/构筑物有功负荷(Pc)分布",
                     fontsize=11, fontweight="bold", pad=15,
                     color=THEME["ACCENT_BLUE"])

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=THEME["BG_CARD"], highlightthickness=0)
        widget.pack(fill="both", expand=True)
        self._chart_canvas = canvas

    def _collect_load_level_data(self):
        sec_pc = 0.0
        ter_pc = 0.0
        rows = []
        for sub in self.hv_system.subsystems:
            for g in sub.groups:
                for eq in g.equipment_list:
                    if eq.is_subtotal:
                        continue
                    rows.append((sub.name, g.name, eq.name, eq.pc, eq.load_level))
                    if eq.load_level == LOAD_LEVEL_SECONDARY:
                        sec_pc += eq.pc
                    else:
                        ter_pc += eq.pc
        return sec_pc, ter_pc, rows

    def _draw_load_level_chart(self):
        for w in self.load_chart_frame.winfo_children():
            w.destroy()

        sec_pc, ter_pc, _ = self._collect_load_level_data()
        if sec_pc + ter_pc <= 0:
            tk.Label(self.load_chart_frame,
                     text="暂无负荷分级数据",
                     font=(FONT_UI, FS[11]),
                     fg=THEME["FG_MUTED"], bg=THEME["BG_CARD"]).pack(expand=True)
            return

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            import matplotlib
            matplotlib.rcParams['font.sans-serif'] = MATPLOTLIB_FONT_FAMILY
            matplotlib.rcParams['axes.unicode_minus'] = False
            matplotlib.rcParams['figure.facecolor'] = THEME["BG_CARD"]
            matplotlib.rcParams['axes.facecolor'] = THEME["BG_CARD"]
            matplotlib.rcParams['text.color'] = THEME["FG_PRIMARY"]
        except ImportError:
            tk.Label(self.load_chart_frame,
                     text="需要安装 matplotlib 库以显示图表",
                     font=(FONT_UI, FS[11]),
                     fg=THEME["FG_MUTED"], bg=THEME["BG_CARD"]).pack(expand=True)
            return

        fig = Figure(figsize=(4, 3), dpi=100)
        fig.patch.set_facecolor(THEME["BG_CARD"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(THEME["BG_CARD"])

        sizes = [sec_pc, ter_pc]
        labels = [f"二级负荷\n{sec_pc:.1f}kW", f"三级负荷\n{ter_pc:.1f}kW"]
        colors = [THEME["ACCENT_BLUE"], THEME["ACCENT_ORANGE"]]
        explode = (0.05, 0)

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct="%1.1f%%",
            colors=colors, explode=explode,
            startangle=90, pctdistance=0.6,
            textprops={"fontsize": 9, "fontweight": "bold",
                       "color": THEME["FG_PRIMARY"]},
            wedgeprops={"edgecolor": THEME["BG_CARD"], "linewidth": 1.5},
        )
        ax.set_title("二级/三级负荷有功功率占比",
                     fontsize=11, fontweight="bold", pad=10,
                     color=THEME["ACCENT_BLUE"])

        canvas = FigureCanvasTkAgg(fig, master=self.load_chart_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=THEME["BG_CARD"], highlightthickness=0)
        widget.pack(fill="both", expand=True)

    def refresh(self):
        if not self.hv_system:
            return

        total_pc_380 = sum(s.compensated_pc for s in self.hv_system.subsystems)
        total_qc_380 = sum(s.compensated_qc for s in self.hv_system.subsystems)
        total_sc_380 = sqrt(total_pc_380 ** 2 + total_qc_380 ** 2)
        pf_380 = total_pc_380 / total_sc_380 if total_sc_380 > 0 else 0

        self.cards["total_pc"].update_value(f"{total_pc_380:.1f}")
        self.cards["total_qc"].update_value(f"{total_qc_380:.1f}")
        self.cards["total_sc"].update_value(f"{total_sc_380:.1f}")
        self.cards["power_factor"].update_value(f"{pf_380:.4f}",
                                                 THEME["ACCENT_GREEN"] if pf_380 >= 0.9 else THEME["ACCENT_ORANGE"])

        self.overview_text.configure(state="normal")
        self.overview_text.delete("1.0", "end")
        hv_pc = self.hv_system.total_pc
        hv_qc = self.hv_system.total_qc
        hv_sc = self.hv_system.total_sc
        hv_pf = self.hv_system.power_factor
        txt = f"[ {self.hv_system.name} ]\n\n"
        txt += f"--- 380V侧（补偿后）---\n"
        txt += f"  总有功功率 Pc = {total_pc_380:.2f} kW\n"
        txt += f"  总无功功率 Qc = {total_qc_380:.2f} kvar\n"
        txt += f"  总视在功率 Sc = {total_sc_380:.2f} kVA\n"
        txt += f"  功率因数 cosphi = {pf_380:.4f}\n\n"
        txt += f"--- 10kV侧（补偿+变压器损耗后）---\n"
        txt += f"  高压侧有功 = {hv_pc:.2f} kW\n"
        txt += f"  高压侧无功 = {hv_qc:.2f} kvar\n"
        txt += f"  高压侧视在 = {hv_sc:.2f} kVA\n"
        txt += f"  高压侧cosphi = {hv_pf:.4f}\n\n"
        txt += f"  子系统数量: {len(self.hv_system.subsystems)}\n\n"
        txt += "-" * 30 + "\n"
        txt += "  计算说明:\n"
        txt += "  - 采用需要系数法计算\n"
        txt += "  - 380V侧补偿后功率因数目标>=0.95\n"
        txt += "  - 变压器损耗按1%/5%估算\n"
        txt += "  - 设备组同时系数Kp/Kq计入\n"
        self.overview_text.insert("1.0", txt)
        self.overview_text.configure(state="disabled")

        for item in self.dist_tree.get_children():
            self.dist_tree.delete(item)
        for sub in self.hv_system.subsystems:
            self.dist_tree.insert("", "end", values=(
                sub.name,
                f"{sub.total_pc:.1f}",
                f"{sub.total_qc:.1f}",
                f"{sub.total_sc:.1f}",
                f"{sub.power_factor_after:.3f}"
            ))

        for item in self.group_tree.get_children():
            self.group_tree.delete(item)
        for sub in self.hv_system.subsystems:
            for g in sub.groups:
                self.group_tree.insert("", "end", values=(
                    f"{sub.name[:4]}...{g.name[:8]}",
                    f"{g.total_device_power:.1f}",
                    f"{g.computed_pc:.2f}",
                    f"{g.computed_qc:.2f}",
                    f"{g.computed_sc:.2f}",
                    f"{g.kp:.1f}"
                ))

        self._draw_pie_chart()
        self._update_load_level()

    def _update_load_level(self):
        sec_pc, ter_pc, rows = self._collect_load_level_data()

        for item in self.load_level_tree.get_children():
            self.load_level_tree.delete(item)
        for sub_name, grp_name, eq_name, pc, level in rows:
            self.load_level_tree.insert("", "end", values=(
                sub_name[:10],
                grp_name[:12],
                eq_name[:14],
                f"{pc:.2f}",
                level,
            ))

        total = sec_pc + ter_pc
        if total > 0:
            self.load_summary_label.configure(
                text=f"二级负荷: {sec_pc:.2f} kW ({sec_pc/total*100:.1f}%)  |  "
                     f"三级负荷: {ter_pc:.2f} kW ({ter_pc/total*100:.1f}%)  |  "
                     f"总计: {total:.2f} kW",
                fg=THEME["FG_PRIMARY"])
        else:
            self.load_summary_label.configure(text="暂无负荷分级数据",
                                               fg=THEME["FG_MUTED"])

        self._draw_load_level_chart()
