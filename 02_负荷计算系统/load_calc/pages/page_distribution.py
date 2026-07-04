# -*- coding: utf-8 -*-
"""配电系统总负荷计算页面"""
import tkinter as tk
from tkinter import ttk, messagebox
from math import sqrt

from ..calc_engine import calc_subsystem_summary, calc_compensation_with_actual_qc, calc_transformer_loss, calc_qc_for_hv_pf_target, HV_TARGET_POWER_FACTOR
from ..models import Subsystem, TRANSFORMER_OPERATION_MODES
from ..widgets import CardFrame, MetricCard, InfoRow, ScrollableFrame
from .equipment_dialogs import KpKqEditDialog


class DistributionPage(ttk.Frame):
    """配电系统总负荷计算"""
    def __init__(self, master, hv_system=None, data_changed_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hv_system = hv_system
        self._data_changed_callback = data_changed_callback  # 数据变更回调
        self._tabs = {}
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
        title = ttk.Label(content, text="配电系统总负荷计算",
                         font=("微软雅黑", 18, "bold"),
                         foreground="#1565C0")
        title.pack(anchor="w", padx=20, pady=(15, 5))

        # 说明
        ttk.Label(content, text="各配电系统独立计算：无功补偿、变压器选择、10KV侧换算",
                 font=("微软雅黑", 9), foreground="#888").pack(anchor="w", padx=20, pady=(0, 10))

        # 工具栏
        toolbar = ttk.Frame(content)
        toolbar.pack(fill="x", padx=15, pady=(0, 5))

        self.btn_kpkq = ttk.Button(toolbar, text="⚙️ 同时系数",
                                    command=self._edit_kp_kq,
                                    state="disabled", width=12)
        self.btn_kpkq.pack(side="left", padx=2)

        ttk.Label(toolbar, text="批量设置当前子系统下所有设备组的KΣP/KΣq",
                  font=("微软雅黑", 8), foreground="#999").pack(side="left", padx=(10, 0))

        # Notebook 标签页
        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def refresh(self):
        if not self.hv_system:
            return

        # 清除旧标签页
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self._tabs.clear()

        subs = self.hv_system.subsystems
        for idx, sub in enumerate(subs):
            tab = _SubsystemTab(self.notebook, sub,
                                data_changed_callback=self._data_changed_callback)
            tab_label = f"{sub.name[:18]}"
            self.notebook.add(tab, text=tab_label)
            self._tabs[idx] = tab

        # 全厂10KV汇总标签页
        tab3 = _HVSummaryTab(self.notebook, self.hv_system)
        self.notebook.add(tab3, text="全厂10KV总配电系统")
        self._tabs["hv"] = tab3

        # 刷新所有标签页
        for tab in self._tabs.values():
            tab.refresh()

    def save_all_subsystem_tabs(self):
        """保存所有子系统标签页的UI值到模型（供计算更新按钮调用）"""
        for key, tab in self._tabs.items():
            if key == "hv":
                continue
            if hasattr(tab, "save_to_model"):
                tab.save_to_model()

    def _get_current_tab(self):
        """获取当前选中的标签页实例"""
        sel = self.notebook.select()
        if not sel:
            return None
        try:
            return self.notebook.nametowidget(sel)
        except Exception:
            return None

    def _on_tab_changed(self, event=None):
        """标签页切换时更新同时系数按钮状态"""
        tab = self._get_current_tab()
        if isinstance(tab, _SubsystemTab):
            self.btn_kpkq.configure(state="normal")
        else:
            self.btn_kpkq.configure(state="disabled")

    def _edit_kp_kq(self):
        """批量设置当前子系统下所有设备组的KΣP/KΣq"""
        tab = self._get_current_tab()
        if not isinstance(tab, _SubsystemTab):
            messagebox.showwarning("提示", "请先选中一个配电系统", parent=self)
            return

        subsystem = tab.subsystem
        if not subsystem.groups:
            messagebox.showinfo("提示", f"子系统「{subsystem.name}」下没有设备组", parent=self)
            return

        dialog = KpKqEditDialog(self, subsystem=subsystem)
        if dialog.result:
            tab.refresh()
            if self._data_changed_callback:
                self._data_changed_callback()


class _SubsystemTab(ttk.Frame):
    """380V子系统标签页 - 可编辑补偿和变压器"""

    def __init__(self, master, subsystem: Subsystem,
                 data_changed_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.subsystem = subsystem
        self._data_changed_callback = data_changed_callback
        self._debounce_timer_id = None  # 防抖定时器ID
        self._is_refreshing = False     # 防止刷新→recalc 循环的标志
        self._create_widgets()

    def _create_widgets(self):
        # 使用 Canvas + Scrollbar 支持滚动
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._scrollable = ttk.Frame(canvas)

        self._scrollable.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._scrollable, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
        # 中键拖动
        self._drag_info = {"start_y": 0, "active": False}
        def _start_drag(event):
            self._drag_info["start_y"] = event.y_root
            self._drag_info["active"] = False
            canvas.configure(cursor="fleur")
        def _on_drag(event):
            dy = self._drag_info["start_y"] - event.y_root
            if abs(dy) > 3:
                self._drag_info["active"] = True
            if self._drag_info["active"]:
                canvas.yview_scroll(int(dy / 2), "units")
                self._drag_info["start_y"] = event.y_root
        def _end_drag(event):
            self._drag_info["active"] = False
            canvas.configure(cursor="")
        canvas.bind("<ButtonPress-2>", _start_drag, add="+")
        canvas.bind("<B2-Motion>", _on_drag, add="+")
        canvas.bind("<ButtonRelease-2>", _end_drag, add="+")
        self._scrollable.bind("<ButtonPress-2>", _start_drag, add="+")
        self._scrollable.bind("<B2-Motion>", _on_drag, add="+")
        self._scrollable.bind("<ButtonRelease-2>", _end_drag, add="+")
        self._canvas = canvas

        content = self._scrollable

        # ========== Section A: 原始负荷数据 ==========
        sec_a = CardFrame(content, "一、原始负荷数据", padding=12)
        sec_a.pack(fill="x", padx=15, pady=(10, 5))

        # Treeview 表格
        columns = ("name", "pc", "qc", "sc", "pf")
        self.group_tree = ttk.Treeview(sec_a, columns=columns,
                                       show="headings", height=6)
        col_cfg = [
            ("name", "设备组名称", 200, "w"),
            ("pc", "Pc(kW)", 110, "center"),
            ("qc", "Qc(kvar)", 110, "center"),
            ("sc", "Sc(kVA)", 110, "center"),
            ("pf", "cosφ", 90, "center"),
        ]
        for key, text, w, anchor in col_cfg:
            self.group_tree.heading(key, text=text)
            self.group_tree.column(key, width=w, anchor=anchor)

        self.group_tree.pack(fill="x", pady=(0, 8))

        # 合计行
        summary_frame = ttk.Frame(sec_a)
        summary_frame.pack(fill="x")

        self._total_labels = {}
        for i, (key, label, unit) in enumerate([
            ("pc", "总有功 Pc", "kW"),
            ("qc", "总无功 Qc", "kvar"),
            ("sc", "总视在 Sc", "kVA"),
            ("pf", "补偿前 cosφ", ""),
        ]):
            lbl = ttk.Label(summary_frame, text=f"{label}: ",
                           font=("微软雅黑", 9), anchor="e")
            lbl.grid(row=0, column=i*2, sticky="e", padx=(10 if i > 0 else 0, 0))

            val = ttk.Label(summary_frame, text="0.00",
                           font=("微软雅黑", 9, "bold"), foreground="#1565C0")
            val.grid(row=0, column=i*2+1, sticky="w", padx=(2, 0))

            if unit:
                ttk.Label(summary_frame, text=unit,
                         font=("微软雅黑", 8), foreground="#999").grid(
                    row=0, column=i*2+1, sticky="w", padx=(val.winfo_reqwidth() + 2, 0))

            self._total_labels[key] = val

        # ========== Section B: 无功补偿计算 ==========
        sec_b = CardFrame(content, "二、无功补偿计算（可编辑）", padding=12)
        sec_b.pack(fill="x", padx=15, pady=(5, 5))

        # 第一行：目标功率因数 + 需要补偿容量
        row1 = ttk.Frame(sec_b)
        row1.pack(fill="x", pady=3)

        ttk.Label(row1, text="目标功率因数:",
                 font=("微软雅黑", 9), width=14, anchor="w").pack(side="left")
        self.target_pf_var = tk.DoubleVar(value=0.95)
        self.target_pf_entry = ttk.Entry(row1, textvariable=self.target_pf_var,
                                         width=8, font=("微软雅黑", 9))
        self.target_pf_entry.pack(side="left", padx=(0, 20))
        self.target_pf_entry.bind("<KeyRelease>", lambda e: self._recalc())

        ttk.Label(row1, text="需要补偿容量:",
                 font=("微软雅黑", 9), anchor="w").pack(side="left")
        self.required_qc_label = ttk.Label(row1, text="0",
                                          font=("微软雅黑", 9, "bold"),
                                          foreground="#E65100")
        self.required_qc_label.pack(side="left", padx=(5, 3))
        ttk.Label(row1, text="kvar", font=("微软雅黑", 8),
                 foreground="#999").pack(side="left")

        # 第二行：实际补偿容量 + 高压侧需求提示
        row2 = ttk.Frame(sec_b)
        row2.pack(fill="x", pady=3)

        ttk.Label(row2, text="实际补偿容量:",
                 font=("微软雅黑", 9), width=14, anchor="w").pack(side="left")
        self.actual_qc_var = tk.DoubleVar(value=0)
        self.actual_qc_entry = ttk.Entry(row2, textvariable=self.actual_qc_var,
                                         width=8, font=("微软雅黑", 9))
        self.actual_qc_entry.pack(side="left", padx=(0, 3))
        ttk.Label(row2, text="kvar", font=("微软雅黑", 8),
                 foreground="#999").pack(side="left")
        self.actual_qc_entry.bind("<KeyRelease>", lambda e: self._recalc())

        # 高压侧需求提示标签
        self.hv_req_label = ttk.Label(row2, text="",
                                     font=("微软雅黑", 8),
                                     foreground="#F44336")
        self.hv_req_label.pack(side="left", padx=(10, 0))

        # 第三行：补偿后结果
        row3 = ttk.Frame(sec_b)
        row3.pack(fill="x", pady=3)

        self._comp_labels = {}
        for i, (key, label, unit) in enumerate([
            ("pc", "补偿后Pc", "kW"),
            ("qc", "补偿后Qc", "kvar"),
            ("sc", "补偿后Sc", "kVA"),
            ("pf", "补偿后cosφ", ""),
        ]):
            ttk.Label(row3, text=f"{label}: ",
                     font=("微软雅黑", 9), anchor="e").pack(side="left", padx=(5 if i > 0 else 0, 0))
            val = ttk.Label(row3, text="0.00",
                           font=("微软雅黑", 9, "bold"),
                           foreground="#4CAF50")
            val.pack(side="left", padx=(1, 0))
            if unit:
                ttk.Label(row3, text=unit, font=("微软雅黑", 8),
                         foreground="#999").pack(side="left")
            self._comp_labels[key] = val

        # ========== Section C: 变压器选择 ==========
        sec_c = CardFrame(content, "三、变压器选择（可编辑）", padding=12)
        sec_c.pack(fill="x", padx=15, pady=(5, 5))

        row_t1 = ttk.Frame(sec_c)
        row_t1.pack(fill="x", pady=3)

        ttk.Label(row_t1, text="单台容量:",
                 font=("微软雅黑", 9), width=12, anchor="w").pack(side="left")
        self.tf_rating_var = tk.DoubleVar(value=1250)
        self.tf_rating_entry = ttk.Entry(row_t1, textvariable=self.tf_rating_var,
                                         width=8, font=("微软雅黑", 9))
        self.tf_rating_entry.pack(side="left", padx=(0, 3))
        ttk.Label(row_t1, text="kVA", font=("微软雅黑", 8),
                 foreground="#999").pack(side="left")
        self.tf_rating_entry.bind("<KeyRelease>", lambda e: self._recalc())

        ttk.Label(row_t1, text="    台数:",
                 font=("微软雅黑", 9), anchor="w").pack(side="left", padx=(20, 0))
        self.tf_count_var = tk.IntVar(value=2)
        self.tf_count_entry = ttk.Entry(row_t1, textvariable=self.tf_count_var,
                                        width=6, font=("微软雅黑", 9))
        self.tf_count_entry.pack(side="left", padx=(0, 3))
        ttk.Label(row_t1, text="台", font=("微软雅黑", 8),
                 foreground="#999").pack(side="left")
        self.tf_count_entry.bind("<KeyRelease>", lambda e: self._recalc())

        row_t2 = ttk.Frame(sec_c)
        row_t2.pack(fill="x", pady=3)

        ttk.Label(row_t2, text="运行方式:",
                 font=("微软雅黑", 9), width=12, anchor="w").pack(side="left")
        self.tf_mode_var = tk.StringVar(value="同时运行")
        self.tf_mode_combo = ttk.Combobox(row_t2, textvariable=self.tf_mode_var,
                                          values=TRANSFORMER_OPERATION_MODES,
                                          width=12, font=("微软雅黑", 9), state="normal")
        self.tf_mode_combo.pack(side="left", padx=(0, 20))
        self.tf_mode_combo.bind("<<ComboboxSelected>>", lambda e: self._recalc())
        self.tf_mode_combo.bind("<KeyRelease>", lambda e: self._recalc())

        ttk.Label(row_t2, text="变压器总有效容量:",
                 font=("微软雅黑", 9), anchor="w").pack(side="left")
        self.eff_cap_label = ttk.Label(row_t2, text="2500",
                                      font=("微软雅黑", 9, "bold"),
                                      foreground="#1565C0")
        self.eff_cap_label.pack(side="left", padx=(5, 3))
        ttk.Label(row_t2, text="kVA", font=("微软雅黑", 8),
                 foreground="#999").pack(side="left")

        row_t3 = ttk.Frame(sec_c)
        row_t3.pack(fill="x", pady=3)

        ttk.Label(row_t3, text="变压器负载率:",
                 font=("微软雅黑", 9), width=12, anchor="w").pack(side="left")
        self.load_rate_label = ttk.Label(row_t3, text="0.0%",
                                        font=("微软雅黑", 11, "bold"),
                                        foreground="#4CAF50")
        self.load_rate_label.pack(side="left", padx=(5, 0))

        # ========== Section D: 10KV侧负荷 ==========
        sec_d = CardFrame(content, "四、10KV侧负荷（折算后）", padding=12)
        sec_d.pack(fill="x", padx=15, pady=(5, 5))

        self._hv_labels = {}
        row_hv = ttk.Frame(sec_d)
        row_hv.pack(fill="x", pady=2)

        hv_items = [
            ("loss_p", "变压器ΔP", "kW", "#E65100"),
            ("loss_q", "变压器ΔQ", "kvar", "#E65100"),
            ("hv_pc", "高压侧Pc", "kW", "#1565C0"),
            ("hv_qc", "高压侧Qc", "kvar", "#1565C0"),
            ("hv_sc", "高压侧Sc", "kVA", "#1565C0"),
            ("hv_pf", "高压侧cosφ", "", "#1565C0"),
        ]
        for idx, (key, label, unit, color) in enumerate(hv_items):
            ttk.Label(row_hv, text=f"{label}: ",
                     font=("微软雅黑", 9), anchor="e").pack(
                side="left", padx=(8 if idx >= 3 else 0, 0))
            val = ttk.Label(row_hv, text="0.00",
                           font=("微软雅黑", 9, "bold"),
                           foreground=color)
            val.pack(side="left", padx=(1, 0))
            if unit:
                ttk.Label(row_hv, text=unit, font=("微软雅黑", 8),
                         foreground="#999").pack(side="left")
            self._hv_labels[key] = val

        # 高压侧功率因数达标状态标签
        self._hv_pf_status = ttk.Label(sec_d, text="",
                                       font=("微软雅黑", 9, "bold"))
        self._hv_pf_status.pack(anchor="w", padx=(8, 0), pady=(2, 0))

        # ========== 保存按钮 ==========
        btn_frame = ttk.Frame(content)
        btn_frame.pack(fill="x", padx=15, pady=(10, 20))

        self.save_btn = ttk.Button(btn_frame, text="保存修改",
                                   command=self._save, style="success.TButton")
        self.save_btn.pack(side="left", padx=5)

        self.reset_btn = ttk.Button(btn_frame, text="重置",
                                    command=self._load_from_model)
        self.reset_btn.pack(side="left", padx=5)

        self.status_label = ttk.Label(btn_frame, text="",
                                     font=("微软雅黑", 9), foreground="#4CAF50")
        self.status_label.pack(side="left", padx=15)

    def refresh(self):
        """刷新显示 - 从模型加载数据"""
        self._is_refreshing = True  # 防止刷新→recalc 触发 debounce 循环
        self._load_from_model()
        self._recalc()
        self._is_refreshing = False

    def save_to_model(self):
        """将当前UI值保存到模型（供计算更新按钮调用）"""
        try:
            target_pf = float(self.target_pf_var.get())
            actual_qc = float(self.actual_qc_var.get())
            tf_rating = float(self.tf_rating_var.get())
            tf_count = int(self.tf_count_var.get())
            tf_mode = self.tf_mode_var.get()
        except (ValueError, tk.TclError):
            return False

        sub = self.subsystem
        sub.target_power_factor = target_pf
        sub.compensation_qc = actual_qc
        sub.transformer_rating = tf_rating
        sub.transformer_count = tf_count
        sub.transformer_operation_mode = tf_mode
        return True

    def _load_from_model(self):
        """从 Subsystem 模型加载数据到 UI"""
        sub = self.subsystem
        self.target_pf_var.set(sub.target_power_factor)
        self.actual_qc_var.set(sub.compensation_qc)
        self.tf_rating_var.set(sub.transformer_rating)
        self.tf_count_var.set(sub.transformer_count)
        self.tf_mode_var.set(sub.transformer_operation_mode)

    def _recalc(self):
        """根据当前 UI 输入重新计算所有值

        增强功能（符合用户需求：参数变更时自动保存并触发全链路计算）：
        1. 先执行 save_to_model() 将UI值持久化到 Subsystem 模型
        2. 执行就地UI预览刷新
        3. 通过防抖机制（800ms）调用数据变更回调，
           触发全量重算并刷新所有关联页面（仪表盘、10KV总览、380V详情、报表）
        """
        # 第1步：自动保存UI值到模型
        self.save_to_model()

        sub = self.subsystem
        try:
            target_pf = float(self.target_pf_var.get())
            actual_qc = float(self.actual_qc_var.get())
            tf_rating = float(self.tf_rating_var.get())
            tf_count = int(self.tf_count_var.get())
            tf_mode = self.tf_mode_var.get()
        except (ValueError, tk.TclError):
            return

        total_pc = sub.total_pc
        total_qc = sub.total_qc
        total_sc = sub.total_sc

        # 更新 Treeview
        for item in self.group_tree.get_children():
            self.group_tree.delete(item)
        for g in sub.groups:
            self.group_tree.insert("", "end", values=(
                g.name,
                f"{g.computed_pc:.2f}",
                f"{g.computed_qc:.2f}",
                f"{g.computed_sc:.2f}",
                f"{g.power_factor:.4f}",
            ))

        # 合计行
        before_sc = sqrt(total_pc ** 2 + total_qc ** 2)
        pf_before = total_pc / before_sc if before_sc > 0 else 0
        self._total_labels["pc"].configure(text=f"{total_pc:.2f}")
        self._total_labels["qc"].configure(text=f"{total_qc:.2f}")
        self._total_labels["sc"].configure(text=f"{total_sc:.2f}")
        self._total_labels["pf"].configure(text=f"{pf_before:.4f}")

        # 补偿计算
        # 低压侧需要补偿到目标功率因数的容量
        tan_before = total_qc / total_pc if total_pc > 0 else 0
        tan_after = sqrt(1 - target_pf ** 2) / target_pf if target_pf > 0 else 0
        required_qc_lv = total_pc * (tan_before - tan_after) if total_pc > 0 else 0

        # 高压侧需要确保cosφ≥0.95的容量
        required_qc_hv = calc_qc_for_hv_pf_target(total_pc, total_qc, HV_TARGET_POWER_FACTOR)

        # 综合需求容量
        required_qc = max(required_qc_lv, required_qc_hv)
        self.required_qc_label.configure(text=f"{required_qc:.1f}")

        # 高压侧需求提示
        if actual_qc < required_qc_hv and required_qc_hv > 0:
            self.hv_req_label.configure(
                text=f"需≥{required_qc_hv:.0f}kvar(高压侧cosφ≥0.95)",
                foreground="#F44336")
        else:
            self.hv_req_label.configure(text="✓ 满足高压侧0.95要求",
                                        foreground="#4CAF50")

        # 补偿后参数
        compensated_qc = max(0, total_qc - actual_qc)
        compensated_sc = sqrt(total_pc ** 2 + compensated_qc ** 2)
        pf_after = total_pc / compensated_sc if compensated_sc > 0 else 0

        self._comp_labels["pc"].configure(text=f"{total_pc:.2f}")
        self._comp_labels["qc"].configure(text=f"{compensated_qc:.2f}")
        self._comp_labels["sc"].configure(text=f"{compensated_sc:.2f}")
        self._comp_labels["pf"].configure(text=f"{pf_after:.4f}")

        # 变压器计算
        # 有效容量
        if tf_mode == "同时运行":
            eff_cap = tf_rating * tf_count
        elif tf_mode == "一用一备":
            eff_cap = tf_rating
        elif tf_mode == "两用一备" and tf_count >= 3:
            eff_cap = tf_rating * 2
        elif tf_mode == "三台同时运行" and tf_count >= 3:
            eff_cap = tf_rating * tf_count
        else:
            eff_cap = tf_rating * tf_count

        self.eff_cap_label.configure(text=f"{eff_cap:.0f}")

        load_rate = compensated_sc / eff_cap if eff_cap > 0 else 0
        lr_text = f"{load_rate * 100:.1f}%"
        if load_rate < 0.85:
            lr_color = "#4CAF50"  # 绿色
        elif load_rate < 1.0:
            lr_color = "#FF9800"  # 橙色
        else:
            lr_color = "#F44336"  # 红色
        self.load_rate_label.configure(text=lr_text, foreground=lr_color)

        # 变压器损耗
        loss_p = compensated_sc * 0.01
        loss_q = compensated_sc * 0.05

        # 高压侧
        hv_pc = total_pc + loss_p
        hv_qc = compensated_qc + loss_q
        hv_sc = sqrt(hv_pc ** 2 + hv_qc ** 2)
        hv_pf = hv_pc / hv_sc if hv_sc > 0 else 0

        self._hv_labels["loss_p"].configure(text=f"{loss_p:.2f}")
        self._hv_labels["loss_q"].configure(text=f"{loss_q:.2f}")
        self._hv_labels["hv_pc"].configure(text=f"{hv_pc:.2f}")
        self._hv_labels["hv_qc"].configure(text=f"{hv_qc:.2f}")
        self._hv_labels["hv_sc"].configure(text=f"{hv_sc:.2f}")
        self._hv_labels["hv_pf"].configure(text=f"{hv_pf:.4f}")

        # 高压侧功率因数达标检测
        hv_pf_ok = hv_pf >= HV_TARGET_POWER_FACTOR
        if hv_pf_ok:
            self._hv_pf_status.configure(
                text=f"✓ 高压侧cosφ≥{HV_TARGET_POWER_FACTOR}，达标",
                foreground="#4CAF50")
        else:
            need_more = required_qc_hv - actual_qc
            self._hv_pf_status.configure(
                text=f"⚠ 高压侧cosφ<{HV_TARGET_POWER_FACTOR}，需追加补偿 {need_more:.0f}kvar",
                foreground="#F44336")

        # 第2步：防抖触发全链路数据变更回调（仅在用户交互时触发，刷新时不触发）
        if self._data_changed_callback and not self._is_refreshing:
            if self._debounce_timer_id is not None:
                self.after_cancel(self._debounce_timer_id)
            self._debounce_timer_id = self.after(
                800, self._on_debounce_fire
            )

    def _on_debounce_fire(self):
        """防抖到期后触发全链路重算"""
        self._debounce_timer_id = None
        self.save_to_model()
        if self._data_changed_callback:
            self._data_changed_callback()

    def _save(self):
        """保存当前 UI 值到 Subsystem 模型"""
        try:
            target_pf = float(self.target_pf_var.get())
            actual_qc = float(self.actual_qc_var.get())
            tf_rating = float(self.tf_rating_var.get())
            tf_count = int(self.tf_count_var.get())
            tf_mode = self.tf_mode_var.get()
        except (ValueError, tk.TclError):
            self.status_label.configure(text="输入格式错误！", foreground="#F44336")
            return

        sub = self.subsystem
        sub.target_power_factor = target_pf
        sub.compensation_qc = actual_qc
        sub.transformer_rating = tf_rating
        sub.transformer_count = tf_count
        sub.transformer_operation_mode = tf_mode

        self.status_label.configure(text="修改已保存 ✓", foreground="#4CAF50")
        self.after(2000, lambda: self.status_label.configure(text=""))


class _HVSummaryTab(ttk.Frame):
    """全厂10KV汇总标签页 - 只展示"""

    def __init__(self, master, hv_system, **kwargs):
        super().__init__(master, **kwargs)
        self.hv_system = hv_system
        self._create_widgets()

    def _create_widgets(self):
        # 可滚动的容器
        sc = ScrollableFrame(self)
        sc.pack(fill="both", expand=True)
        content = sc.inner

        # 说明文字
        ttk.Label(content, text="以下为各380V子系统折算至10KV侧的负荷汇总",
                 font=("微软雅黑", 9), foreground="#888").pack(
            anchor="w", padx=15, pady=(10, 5))

        # 指标卡片
        card_frame = ttk.Frame(content)
        card_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.cards = {}
        for key, title, color, unit in [
            ("pc", "总有功功率", "#1565C0", "kW"),
            ("qc", "总无功功率", "#E65100", "kvar"),
            ("sc", "总视在功率", "#2E7D32", "kVA"),
            ("pf", "功率因数", "#6A1B9A", ""),
            ("cap", "变压器总容量", "#00838F", "kVA"),
        ]:
            card = MetricCard(card_frame, title, "0", unit, color, width=160)
            card.pack(side="left", padx=4)
            self.cards[key] = card

        # 子系统详情表格
        detail_frame = CardFrame(content, "各子系统10KV侧负荷核定", padding=10)
        detail_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

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
            ("trans_cap", "有效容量(kVA)", 110),
            ("load_rate", "负载率(%)", 90),
            ("loss_p", "ΔP(kW)", 80),
            ("loss_q", "ΔQ(kvar)", 90),
        ]
        for key, text, w in col_config:
            self.tree.heading(key, text=text)
            self.tree.column(key, width=w, anchor="center")
        self.tree.column("name", anchor="w")

        vsb = ttk.Scrollbar(detail_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def refresh(self):
        if not self.hv_system:
            return

        # 更新指标卡片
        total_pc = self.hv_system.total_pc
        total_qc = self.hv_system.total_qc
        total_sc = self.hv_system.total_sc
        pf = self.hv_system.power_factor

        self.cards["pc"].update_value(f"{total_pc:.1f}")
        self.cards["qc"].update_value(f"{total_qc:.1f}")
        self.cards["sc"].update_value(f"{total_sc:.1f}")
        self.cards["pf"].update_value(f"{pf:.4f}",
                                       "#4CAF50" if pf >= HV_TARGET_POWER_FACTOR else "#FF9800")

        total_eff_cap = sum(s.effective_transformer_capacity
                           for s in self.hv_system.subsystems)
        self.cards["cap"].update_value(f"{total_eff_cap:.0f}")

        # 更新表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        for sub in self.hv_system.subsystems:
            summary = calc_subsystem_summary(sub)
            lr = summary["load_rate"]
            self.tree.insert("", "end", values=(
                sub.name,
                f"{summary['hv_pc']:.2f}",
                f"{summary['hv_qc']:.2f}",
                f"{summary['hv_sc']:.2f}",
                f"{summary['hv_pf']:.4f}",
                f"{sub.effective_transformer_capacity:.0f}",
                f"{lr*100:.1f}",
                f"{summary['transformer_loss_p']:.2f}",
                f"{summary['transformer_loss_q']:.2f}",
            ))
