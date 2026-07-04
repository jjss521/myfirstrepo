# -*- coding: utf-8 -*-
"""仪表盘页面"""
import tkinter as tk
from tkinter import ttk
from math import sqrt

from ..config import APP_NAME, SYSTEM_COLORS, COLORS
from ..models import LOAD_LEVEL_SECONDARY, LOAD_LEVEL_TERTIARY
from ..widgets import CardFrame, InfoRow, MetricCard, ScrollableFrame


class DashboardPage(ttk.Frame):
    """主仪表盘 - 显示全厂负荷概况"""

    # 饼图配色方案
    PIE_COLORS = [
        "#1565C0", "#E65100", "#2E7D32", "#6A1B9A", "#00838F",
        "#F57F17", "#C62828", "#283593", "#4E342E", "#00695C",
        "#AD1457", "#558B2F", "#37474F", "#5C6BC0", "#EF6C00",
        "#26A69A", "#78909C", "#D81B60", "#1E88E5", "#43A047",
        "#8E24AA", "#00ACC1",
    ]

    def __init__(self, master, hv_system=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hv_system = hv_system
        self._chart_canvas = None
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
        title = ttk.Label(content, text="污水厂负荷计算系统",
                         font=("微软雅黑", 20, "bold"),
                         foreground="#1a237e")
        title.pack(anchor="w", padx=20, pady=(20, 5))

        subtitle = ttk.Label(content, text="Wastewater Treatment Plant Load Calculation System",
                            font=("微软雅黑", 10), foreground="#888")
        subtitle.pack(anchor="w", padx=20, pady=(0, 15))

        # 主要指标卡片区域
        self.metrics_frame = ttk.Frame(content)
        self.metrics_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.cards = {}
        metrics = [
            ("total_pc", "总有功功率", "#1565C0", "kW"),
            ("total_qc", "总无功功率", "#E65100", "kvar"),
            ("total_sc", "总视在功率", "#2E7D32", "kVA"),
            ("power_factor", "功率因数", "#6A1B9A", ""),
        ]
        for key, title, color, unit in metrics:
            card = MetricCard(self.metrics_frame, title, "", unit, color, width=200)
            card.pack(side="left", padx=5, pady=5)
            self.cards[key] = card

        # 主内容区
        main = ttk.Frame(content)
        main.pack(fill="both", expand=True, padx=20, pady=5)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=3)

        # 左侧：系统概览
        overview_frame = CardFrame(main, "系统概览", padding=15)
        overview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.overview_text = tk.Text(overview_frame, height=18, width=50,
                                     font=("微软雅黑", 10),
                                     bg="#fafafa", relief="flat",
                                     wrap="word")
        self.overview_text.pack(fill="both", expand=True)

        # 右侧：负荷分布饼图（直接显示，不在标签页内）
        self.chart_frame = ttk.Frame(main)
        self.chart_frame.grid(row=0, column=1, sticky="nsew")

        # 底部：负荷分布表 + 设备组统计
        bottom_frame = ttk.Frame(content)
        bottom_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)

        # 左：负荷分布表
        dist_card = CardFrame(bottom_frame, "负荷分布表", padding=10)
        dist_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.dist_tree = ttk.Treeview(dist_card,
                                      columns=("system", "pc", "qc", "sc", "pf"),
                                      show="headings", height=8)
        self.dist_tree.heading("system", text="系统名称")
        self.dist_tree.heading("pc", text="Pc(kW)")
        self.dist_tree.heading("qc", text="Qc(kvar)")
        self.dist_tree.heading("sc", text="Sc(kVA)")
        self.dist_tree.heading("pf", text="cosφ")
        self.dist_tree.column("system", width=180)
        self.dist_tree.column("pc", width=90, anchor="center")
        self.dist_tree.column("qc", width=90, anchor="center")
        self.dist_tree.column("sc", width=90, anchor="center")
        self.dist_tree.column("pf", width=70, anchor="center")

        vsb = ttk.Scrollbar(dist_card, orient="vertical", command=self.dist_tree.yview)
        self.dist_tree.configure(yscrollcommand=vsb.set)
        self.dist_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # 右：设备组统计明细
        group_card = CardFrame(bottom_frame, "设备组统计明细", padding=10)
        group_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.group_tree = ttk.Treeview(group_card,
                                       columns=("group", "pe", "pc", "qc", "sc", "kp"),
                                       show="headings", height=8)
        cols = [("group", "设备组名称", 180), ("pe", "Pe(kW)", 80),
                ("pc", "Pc(kW)", 80), ("qc", "Qc(kvar)", 80),
                ("sc", "Sc(kVA)", 80), ("kp", "K∑p", 60)]
        for key, text, width in cols:
            self.group_tree.heading(key, text=text)
            self.group_tree.column(key, width=width, anchor="center")

        vsb2 = ttk.Scrollbar(group_card, orient="vertical", command=self.group_tree.yview)
        self.group_tree.configure(yscrollcommand=vsb2.set)
        self.group_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

        # ════════════════════════════════════════
        # 负荷分级区域
        # ════════════════════════════════════════
        load_card = CardFrame(content, "负荷分级（二级/三级负荷分析）", padding=10)
        load_card.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        # 负荷分级左右布局
        lf_top = ttk.Frame(load_card)
        lf_top.pack(fill="both", expand=True)
        lf_top.columnconfigure(0, weight=2)
        lf_top.columnconfigure(1, weight=3)

        # 左：饼图
        self.load_chart_frame = ttk.Frame(lf_top)
        self.load_chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # 右：数据表
        load_table_frame = ttk.Frame(lf_top)
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

        # 负荷分级汇总标签
        self.load_summary_label = ttk.Label(load_card, text="",
                                           font=("微软雅黑", 10, "bold"),
                                           foreground="#333")
        self.load_summary_label.pack(anchor="w", padx=5, pady=(5, 0))

    def _draw_pie_chart(self):
        """绘制各建/构筑物有功功率Pc饼状图"""
        # 清除旧图表
        for w in self.chart_frame.winfo_children():
            w.destroy()

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            import matplotlib
            matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
            matplotlib.rcParams['axes.unicode_minus'] = False
        except ImportError:
            ttk.Label(self.chart_frame,
                      text="需要安装 matplotlib 库以显示图表\npip install matplotlib",
                      font=("微软雅黑", 11), foreground="#999").pack(expand=True)
            return

        # 收集数据
        labels = []
        sizes = []
        colors = []
        for sub in self.hv_system.subsystems:
            for g in sub.groups:
                pc = g.computed_pc
                if pc > 1.0:  # 忽略极小值
                    name = g.name if len(g.name) <= 12 else g.name[:10] + ".."
                    labels.append(name)
                    sizes.append(pc)

        if not sizes:
            ttk.Label(self.chart_frame,
                      text="暂无数据", font=("微软雅黑", 11), foreground="#999").pack(expand=True)
            return

        # 绘制饼图
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, autopct="%1.1f%%",
            colors=self.PIE_COLORS[:len(sizes)],
            startangle=90, pctdistance=0.75,
            textprops={"fontsize": 8},
        )

        # 图例
        legend_labels = [f"{l} ({s:.0f}kW)" for l, s in zip(labels, sizes)]
        ax.legend(wedges, legend_labels,
                  loc="center left", bbox_to_anchor=(1, 0.5),
                  fontsize=8, frameon=False)

        ax.set_title("各建/构筑物有功负荷(Pc)分布",
                     fontsize=11, fontweight="bold", pad=15)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvas = canvas

    def _collect_load_level_data(self):
        """收集全厂二级/三级负荷数据"""
        sec_pc = 0.0  # 二级负荷有功
        ter_pc = 0.0  # 三级负荷有功
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
        """绘制二级/三级负荷饼图"""
        for w in self.load_chart_frame.winfo_children():
            w.destroy()

        sec_pc, ter_pc, _ = self._collect_load_level_data()
        if sec_pc + ter_pc <= 0:
            ttk.Label(self.load_chart_frame,
                      text="暂无负荷分级数据",
                      font=("微软雅黑", 11), foreground="#999").pack(expand=True)
            return

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            import matplotlib
            matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
            matplotlib.rcParams['axes.unicode_minus'] = False
        except ImportError:
            ttk.Label(self.load_chart_frame,
                      text="需要安装 matplotlib 库以显示图表",
                      font=("微软雅黑", 11), foreground="#999").pack(expand=True)
            return

        fig = Figure(figsize=(4, 3), dpi=100)
        ax = fig.add_subplot(111)

        sizes = [sec_pc, ter_pc]
        labels = [f"二级负荷\n{sec_pc:.1f}kW", f"三级负荷\n{ter_pc:.1f}kW"]
        colors = ["#1565C0", "#FF9800"]
        explode = (0.05, 0)

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct="%1.1f%%",
            colors=colors, explode=explode,
            startangle=90, pctdistance=0.6,
            textprops={"fontsize": 9, "fontweight": "bold"},
        )
        ax.set_title("二级/三级负荷有功功率占比",
                     fontsize=11, fontweight="bold", pad=10)

        canvas = FigureCanvasTkAgg(fig, master=self.load_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh(self):
        if not self.hv_system:
            return

        # 计算 380V 侧总负荷（各子系统总和，不含变压器损耗和补偿）
        total_pc_380 = sum(s.total_pc for s in self.hv_system.subsystems)
        total_qc_380 = sum(s.total_qc for s in self.hv_system.subsystems)
        from math import sqrt
        total_sc_380 = sqrt(total_pc_380 ** 2 + total_qc_380 ** 2)
        pf_380 = total_pc_380 / total_sc_380 if total_sc_380 > 0 else 0

        # 更新指标卡片（380V 侧，与负荷分布表一致）
        self.cards["total_pc"].update_value(f"{total_pc_380:.1f}")
        self.cards["total_qc"].update_value(f"{total_qc_380:.1f}")
        self.cards["total_sc"].update_value(f"{total_sc_380:.1f}")
        self.cards["power_factor"].update_value(f"{pf_380:.4f}",
                                                  "#4CAF50" if pf_380 >= 0.9 else "#FF9800")

        # 更新概览文本（保持10kV侧参考数据，但标注说明）
        self.overview_text.configure(state="normal")
        self.overview_text.delete("1.0", "end")
        hv_pc = self.hv_system.total_pc
        hv_qc = self.hv_system.total_qc
        hv_sc = self.hv_system.total_sc
        hv_pf = self.hv_system.power_factor
        txt = f"【{self.hv_system.name}】\n\n"
        txt += f"━ 380V侧（补偿前）━\n"
        txt += f"总有功功率 Pc = {total_pc_380:.2f} kW\n"
        txt += f"总无功功率 Qc = {total_qc_380:.2f} kvar\n"
        txt += f"总视在功率 Sc = {total_sc_380:.2f} kVA\n"
        txt += f"功率因数 cosφ = {pf_380:.4f}\n\n"
        txt += f"━ 10kV侧（补偿+变压器损耗后）━\n"
        txt += f"高压侧有功 = {hv_pc:.2f} kW\n"
        txt += f"高压侧无功 = {hv_qc:.2f} kvar\n"
        txt += f"高压侧视在 = {hv_sc:.2f} kVA\n"
        txt += f"高压侧cosφ = {hv_pf:.4f}\n\n"
        txt += f"子系统数量: {len(self.hv_system.subsystems)}\n\n"
        txt += "=" * 30 + "\n"
        txt += "计算说明：\n"
        txt += "• 采用需要系数法计算\n"
        txt += "• 380V侧补偿后功率因数目标≥0.95\n"
        txt += "• 变压器损耗按1%/5%估算\n"
        txt += "• 设备组同时系数K∑p/K∑q计入\n"
        self.overview_text.insert("1.0", txt)
        self.overview_text.configure(state="disabled")

        # 更新系统分布表
        for item in self.dist_tree.get_children():
            self.dist_tree.delete(item)
        for sub in self.hv_system.subsystems:
            self.dist_tree.insert("", "end", values=(
                sub.name,
                f"{sub.total_pc:.1f}",
                f"{sub.total_qc:.1f}",
                f"{sub.total_sc:.1f}",
                f"{sub.power_factor_before:.3f}"
            ))

        # 更新设备组统计
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

        # 绘制饼图
        self._draw_pie_chart()

        # 更新负荷分级
        self._update_load_level()

    def _update_load_level(self):
        """更新负荷分级数据"""
        sec_pc, ter_pc, rows = self._collect_load_level_data()

        # 更新表格
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

        # 更新汇总标签
        total = sec_pc + ter_pc
        if total > 0:
            self.load_summary_label.configure(
                text=f"📊 二级负荷: {sec_pc:.2f} kW ({sec_pc/total*100:.1f}%)  |  "
                     f"三级负荷: {ter_pc:.2f} kW ({ter_pc/total*100:.1f}%)  |  "
                     f"总计: {total:.2f} kW")
        else:
            self.load_summary_label.configure(text="暂无负荷分级数据")

        # 绘制饼图
        self._draw_load_level_chart()
