# -*- coding: utf-8 -*-
"""设备管理页面 - 以建/构筑物为单位的管理界面"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import tkinterdnd2
from typing import Optional

from ..models import Equipment, EquipmentGroup, Subsystem
from ..widgets import CardFrame, ScrollableFrame
from ..config import THEME, blend_color, FONT_UI, FONT_DISPLAY, FS
from .equipment_dialogs import EquipmentEditDialog, BuildingEditDialog, KxReferenceEditorDialog, SubsystemEditDialog, ValvePowerConfigDialog
from ..excel_importer import parse_excel_file


class EquipmentPage(ttk.Frame):
    """设备管理页面 - 以建/构筑物为核心的管理界面"""

    def __init__(self, master, hv_system=None, notify_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hv_system = hv_system
        self._notify_callback = notify_callback  # 数据变更通知回调
        self._selected_sub = None      # 当前选中的子系统 (Subsystem)
        self._selected_group = None    # 当前选中的建/构筑物 (EquipmentGroup)
        self._selected_equip_idx = None  # 选中设备在 group 中的索引
        self._editing = False           # 原地编辑状态
        self._edit_widget = None         # 原地编辑 Entry 引用

        self._create_widgets()

    def set_hv_system(self, hv_system):
        self.hv_system = hv_system
        self.refresh()

    def _create_widgets(self):
        """创建整体布局"""
        # 可滚动的容器
        sc = ScrollableFrame(self)
        sc.pack(fill="both", expand=True)
        content = sc.inner

        # 标题
        header = tk.Frame(content, bg=THEME["BG_MAIN"])
        header.pack(fill="x", padx=20, pady=(15, 10))

        accent = tk.Frame(header, bg=THEME["ACCENT_ORANGE"], width=4, height=24)
        accent.pack(side="left", padx=(0, 10))

        tk.Label(header, text="设备管理",
                 font=(FONT_DISPLAY, FS[18], "bold"),
                 fg=THEME["ACCENT_ORANGE"], bg=THEME["BG_MAIN"]).pack(side="left")

        tk.Label(header, text="— 按建/构筑物分类管理",
                 font=(FONT_UI, FS[10]),
                 fg=THEME["FG_MUTED"], bg=THEME["BG_MAIN"]).pack(side="left", padx=(10, 0))

        # 主分割区
        main = ttk.PanedWindow(content, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ── 左侧：建/构筑物树形导航 ──
        left_frame = CardFrame(main, "建/构筑物导航", padding=5)
        main.add(left_frame, weight=35)

        self._create_left_panel(left_frame)

        # ── 右侧：设备管理区 ──
        right_frame = ttk.Frame(main)
        main.add(right_frame, weight=65)

        self._create_right_panel(right_frame)

    def _create_left_panel(self, parent):
        """左侧：建/构筑物树形导航"""
        # ════ Excel 导入专区 ════
        import_frame = tk.Frame(parent, bg=blend_color(THEME["ACCENT_GREEN"], THEME["BG_CARD"], 0.1),
                                highlightbackground=blend_color(THEME["ACCENT_GREEN"], THEME["BORDER"], 0.3),
                                highlightthickness=1)
        import_frame.pack(fill="x", pady=(0, 6))

        self.import_btn = tk.Label(
            import_frame,
            text="  导入 Excel 设备清单",
            font=(FONT_UI, FS[11], "bold"),
            fg=THEME["ACCENT_GREEN"],
            bg=blend_color(THEME["ACCENT_GREEN"], THEME["BG_CARD"], 0.15),
            cursor="hand2", padx=12, pady=10,
            anchor="center"
        )
        self.import_btn.pack(fill="x", padx=2, pady=(2, 0))
        self.import_btn.bind("<Button-1>", lambda e: self._import_from_excel())
        self.import_btn.bind("<Enter>", lambda e: self.import_btn.configure(
            bg=blend_color(THEME["ACCENT_GREEN"], THEME["BG_CARD"], 0.25)))
        self.import_btn.bind("<Leave>", lambda e: self.import_btn.configure(
            bg=blend_color(THEME["ACCENT_GREEN"], THEME["BG_CARD"], 0.15)))

        hint = tk.Label(
            import_frame,
            text="  拖放 .xlsx/.xls 文件到此处或下方导航树",
            font=(FONT_UI, FS[8]),
            fg=THEME["FG_MUTED"],
            bg=blend_color(THEME["ACCENT_GREEN"], THEME["BG_CARD"], 0.1),
            anchor="w"
        )
        hint.pack(fill="x", padx=5, pady=(0, 2))

        # 注册拖放
        import_frame.drop_target_register(tkinterdnd2.DND_FILES)
        import_frame.dnd_bind("<<Drop>>", self._on_drop)
        import_frame.dnd_bind("<<DragEnter>>", lambda e: import_frame.configure(
            bg=blend_color(THEME["ACCENT_GREEN"], THEME["BG_CARD"], 0.2)))
        import_frame.dnd_bind("<<DragLeave>>", lambda e: import_frame.configure(
            bg=blend_color(THEME["ACCENT_GREEN"], THEME["BG_CARD"], 0.1)))

        # 查询过滤
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(filter_frame, text="搜索:",
                  font=(FONT_UI, FS[9])).pack(side="left", padx=(0, 5))
        self.filter_entry = ttk.Entry(filter_frame, font=(FONT_UI, FS[9]))
        self.filter_entry.pack(side="left", fill="x", expand=True)
        self.filter_entry.bind("<KeyRelease>", lambda e: self._filter_tree())

        # 树形导航
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        self.building_tree = ttk.Treeview(tree_frame,
                                          columns=("info",),
                                          show="tree",
                                          selectmode="extended",
                                          height=20)
        self.building_tree.heading("#0", text="建/构筑物")
        self.building_tree.column("#0", width=250, minwidth=200)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.building_tree.yview)
        self.building_tree.configure(yscrollcommand=vsb.set)

        self.building_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.building_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        # 右键菜单
        self._building_context_menu = tk.Menu(self, tearoff=0)
        self._building_context_menu.add_command(label="编辑建筑物", command=self._edit_building_from_menu)
        self._building_context_menu.add_separator()
        self._building_context_menu.add_command(label="删除建筑物", command=self._delete_building_from_menu)
        self.building_tree.bind("<Button-3>", self._show_building_context_menu)
        # 注册树形导航的拖放
        self.building_tree.drop_target_register(tkinterdnd2.DND_FILES)
        self.building_tree.dnd_bind("<<Drop>>", self._on_drop)

    def _create_right_panel(self, parent):
        """右侧：设备管理区"""
        # ── 工具栏（ttk.Button + 矢量图标，分组布局）──
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", padx=5, pady=(5, 0))

        # ── Row 0: 设备组 | 建/构筑物组 ──
        row0 = ttk.Frame(toolbar)
        row0.pack(fill="x", pady=2)

        # 设备操作组
        equip_frame = ttk.LabelFrame(row0, text="设备操作", padding=3)
        equip_frame.pack(side="left", padx=(0, 8))

        self.btn_add_equip = ttk.Button(equip_frame, text="➕ 添加设备",
                                        command=self._add_equipment)
        self.btn_add_equip.pack(side="left", padx=1)

        self.btn_edit_equip = ttk.Button(equip_frame, text="✏️ 编辑",
                                         command=self._edit_equipment,
                                         state="disabled")
        self.btn_edit_equip.pack(side="left", padx=1)

        self.btn_del_equip = ttk.Button(equip_frame, text="🗑️ 删除",
                                        command=self._delete_equipment,
                                        state="disabled")
        self.btn_del_equip.pack(side="left", padx=1)

        # 建/构筑物组
        bldg_frame = ttk.LabelFrame(row0, text="建/构筑物", padding=3)
        bldg_frame.pack(side="left", padx=8)

        self.btn_add_bldg = ttk.Button(bldg_frame, text="🏗️ 添加建筑",
                                       command=self._add_building)
        self.btn_add_bldg.pack(side="left", padx=1)

        self.btn_del_bldg = ttk.Button(bldg_frame, text="🗑️ 删除",
                                       command=self._delete_building,
                                       state="disabled")
        self.btn_del_bldg.pack(side="left", padx=1)

        self.btn_batch_del = ttk.Button(bldg_frame, text="🗑️ 批量删除",
                                        command=self._batch_delete_buildings,
                                        state="disabled")
        self.btn_batch_del.pack(side="left", padx=1)

        # ── Row 1: 配电系统组 | 工具组 ──
        row1 = ttk.Frame(toolbar)
        row1.pack(fill="x", pady=2)

        sub_frame = ttk.LabelFrame(row1, text="配电系统", padding=3)
        sub_frame.pack(side="left", padx=(0, 8))

        self.btn_add_sub = ttk.Button(sub_frame, text="➕ 添加系统",
                                      command=self._add_subsystem)
        self.btn_add_sub.pack(side="left", padx=1)

        self.btn_del_sub = ttk.Button(sub_frame, text="🗑️ 删除",
                                      command=self._delete_subsystem,
                                      state="disabled")
        self.btn_del_sub.pack(side="left", padx=1)

        # 工具组
        tool_frame = ttk.LabelFrame(row1, text="工具", padding=3)
        tool_frame.pack(side="left", padx=8)

        self.btn_refresh = ttk.Button(tool_frame, text="🔄 刷新",
                                      command=self.refresh)
        self.btn_refresh.pack(side="left", padx=1)

        self.btn_kx = ttk.Button(tool_frame, text="📖 Kx参考",
                                 command=self._open_kx_editor)
        self.btn_kx.pack(side="left", padx=1)

        self.btn_valve_power = ttk.Button(tool_frame, text="⚙️ 阀门功率预设",
                                          command=self._open_valve_power_config)
        self.btn_valve_power.pack(side="left", padx=1)

        # ── 当前建/构筑物信息 ──
        self.group_info = tk.Label(parent,
                                   text="请在左侧选择一个建/构筑物",
                                   font=(FONT_UI, FS[10]),
                                   fg=THEME["FG_MUTED"],
                                   bg=THEME["BG_MAIN"],
                                   anchor="w", padx=10, pady=5)
        self.group_info.pack(fill="x")

        # ── 设备列表表格 ──
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, pady=(5, 5))

        columns = ("idx", "name", "pe", "installed", "working",
                   "kx", "cos", "tan", "pc", "qc", "sc", "remark")
        self.equip_tree = ttk.Treeview(table_frame,
                                       columns=columns,
                                       show="headings",
                                       selectmode="browse",
                                       height=15)

        col_config = [
            ("idx", "#", 35, "center"),
            ("name", "设备名称", 140, "w"),
            ("pe", "Pe(kW)", 80, "center"),
            ("installed", "安装", 55, "center"),
            ("working", "工作", 55, "center"),
            ("kx", "Kx", 55, "center"),
            ("cos", "cosφ", 60, "center"),
            ("tan", "tanφ", 60, "center"),
            ("pc", "Pc(kW)", 80, "center"),
            ("qc", "Qc(kvar)", 80, "center"),
            ("sc", "Sc(kVA)", 80, "center"),
            ("remark", "备注", 100, "w"),
        ]
        for key, text, w, anchor in col_config:
            self.equip_tree.heading(key, text=text)
            self.equip_tree.column(key, width=w, anchor=anchor)

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self.equip_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal",
                            command=self.equip_tree.xview)
        self.equip_tree.configure(yscrollcommand=vsb.set,
                                  xscrollcommand=hsb.set)

        self.equip_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        self.equip_tree.bind("<<TreeviewSelect>>", self._on_equip_select)
        self.equip_tree.bind("<Double-1>", self._on_equip_double_click)

        # ── 底部统计栏 ──
        self.status_label = tk.Label(parent,
                                     text="",
                                     font=(FONT_UI, FS[9]),
                                     fg=THEME["FG_SECONDARY"],
                                     bg=THEME["BG_MAIN"],
                                     anchor="w", padx=10, pady=3)
        self.status_label.pack(fill="x")

    # ─────────────────────── 数据填充 ───────────────────────

    def _build_tree(self):
        """重建左侧建/构筑物树"""
        for item in self.building_tree.get_children():
            self.building_tree.delete(item)

        if not self.hv_system:
            return

        for si, sub in enumerate(self.hv_system.subsystems):
            sub_iid = f"sub_{si}"
            short_name = sub.name if len(sub.name) <= 16 else sub.name[:14] + ".."
            self.building_tree.insert("", "end", iid=sub_iid,
                                      text=short_name)

            for gi, grp in enumerate(sub.groups):
                grp_iid = f"grp_{si}_{gi}"
                self.building_tree.insert(sub_iid, "end",
                                          iid=grp_iid,
                                          text=f"  {grp.name}")

        # 展开所有
        for item in self.building_tree.get_children():
            self.building_tree.item(item, open=True)

    def _load_equipment_table(self, group: EquipmentGroup):
        """加载指定建/构筑物的设备列表"""
        for item in self.equip_tree.get_children():
            self.equip_tree.delete(item)

        if not group:
            self.status_label.configure(text="")
            return

        idx = 0
        for i, eq in enumerate(group.equipment_list):
            if eq.is_subtotal:
                # 小计行用特殊颜色标识
                item_id = self.equip_tree.insert("", "end", values=(
                    "─", eq.name, "", "", "", "", "", "",
                    f"{eq.pc:.2f}", "", "", ""))
                self.equip_tree.tag_configure("subtotal",
                                              background=blend_color(THEME["ACCENT_ORANGE"], THEME["BG_CARD"], 0.1),
                                              font=(FONT_UI, FS[9], "bold"))
                self.equip_tree.item(item_id, tags=("subtotal",))
            else:
                idx += 1
                self.equip_tree.insert("", "end", iid=f"eq_{i}",
                                       values=(
                                           idx, eq.name,
                                           f"{eq.rated_power:.1f}",
                                           eq.installed_count,
                                           eq.working_count,
                                           f"{eq.kx:.2f}",
                                           f"{eq.cos_phi:.2f}",
                                           f"{eq.tan_phi:.4f}",
                                           f"{eq.pc:.2f}",
                                           f"{eq.qc:.2f}",
                                           f"{eq.sc:.2f}",
                                           eq.remark or ""))

        # 状态栏 - 显示小计数 AND 计入同时系数的计算值
        total_pe = group.total_device_power
        subtotal_pc = group.subtotal_pc
        subtotal_qc = group.subtotal_qc
        subtotal_sc = group.subtotal_sc
        comp_pc = group.computed_pc
        comp_qc = group.computed_qc
        comp_sc = group.computed_sc
        self.status_label.configure(
            text=(f"  总计: Pe={total_pe:.1f}kW | "
                  f"\u2211Pc={subtotal_pc:.2f}kW | "
                  f"\u2211Qc={subtotal_qc:.2f}kvar | "
                  f"\u2211Sc={subtotal_sc:.2f}kVA | "
                  f"cos\u03c6={group.power_factor:.3f} | "
                  f"\u2502 K\u2211ppc\u2192{comp_pc:.2f}kW "
                  f"K\u2211qqc\u2192{comp_qc:.2f}kvar "
                  f"Sc\u2192{comp_sc:.2f}kVA"))

    # ─────────────────────── 事件处理 ───────────────────────

    def _on_tree_select(self, event):
        """建/构筑物树点击事件（支持多选）"""
        sel = self.building_tree.selection()
        if not sel:
            self._clear_selection()
            return

        # 检查是否有多个建/构筑物被选中 → 启用批量删除
        grp_selected = [iid for iid in sel if iid.startswith("grp_")]
        if len(grp_selected) > 1:
            self.btn_batch_del.configure(state="normal")
        else:
            self.btn_batch_del.configure(state="disabled")

        iid = sel[0]
        if iid.startswith("grp_"):
            parts = iid.split("_")
            si, gi = int(parts[1]), int(parts[2])
            sub = self.hv_system.subsystems[si]
            group = sub.groups[gi]

            self._selected_sub = sub
            self._selected_group = group
            self._selected_equip_idx = None

            # 更新信息
            self.group_info.configure(
                text=f"  子系统: {sub.name}  ->  建/构筑物: {group.name}",
                fg=THEME["FG_PRIMARY"])

            # 加载设备表
            self._load_equipment_table(group)

            # 启用相关按钮
            self.btn_del_bldg.configure(state="normal")
            self.btn_del_sub.configure(state="normal")
            self.btn_add_equip.configure(state="normal")
            self.btn_edit_equip.configure(state="disabled")
            self.btn_del_equip.configure(state="disabled")
        elif iid.startswith("sub_"):
            parts = iid.split("_")
            si = int(parts[1])
            sub = self.hv_system.subsystems[si]

            self._selected_sub = sub
            self._selected_group = None
            self._selected_equip_idx = None

            self.group_info.configure(
                text=f"  配电系统: {sub.name}（共{len(sub.groups)}个建/构筑物）",
                fg=THEME["FG_SECONDARY"])

            # 清空设备表
            for item in self.equip_tree.get_children():
                self.equip_tree.delete(item)
            self.status_label.configure(text="")

            # 启用子系统删除，禁用其他
            self.btn_del_bldg.configure(state="disabled")
            self.btn_del_sub.configure(state="normal")
            self.btn_add_equip.configure(state="disabled")
            self.btn_edit_equip.configure(state="disabled")
            self.btn_del_equip.configure(state="disabled")
        else:
            self._clear_selection()

    def _on_equip_select(self, event):
        """设备列表选中事件"""
        sel = self.equip_tree.selection()
        if not sel:
            self.btn_edit_equip.configure(state="disabled")
            self.btn_del_equip.configure(state="disabled")
            self._selected_equip_idx = None
            return

        item_id = sel[0]
        if item_id.startswith("eq_"):
            idx = int(item_id.split("_")[1])
            self._selected_equip_idx = idx
            self.btn_edit_equip.configure(state="normal")
            self.btn_del_equip.configure(state="normal")
        else:
            # 小计行不能编辑
            self._selected_equip_idx = None
            self.btn_edit_equip.configure(state="disabled")
            self.btn_del_equip.configure(state="disabled")

    # --- 设备表格原地编辑（双击编辑） ---

    # 可原地编辑的列索引 (1-based): #2名称, #3Pe, #4安装, #5工作, #6Kx, #7cosφ, #12备注
    _EDITABLE_EQUIP_COLS = {2, 3, 4, 5, 6, 7, 12}

    def _on_equip_double_click(self, event):
        """双击设备表格单元格，触发原地编辑"""
        if self._edit_widget is not None:
            self._cancel_equip_cell_edit()

        region = self.equip_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.equip_tree.identify_column(event.x)
        item = self.equip_tree.identify_row(event.y)
        if not item or not item.startswith("eq_"):
            return  # 小计行不可编辑

        col_idx = int(column[1])
        if col_idx not in self._EDITABLE_EQUIP_COLS:
            return

        self._start_equip_cell_edit(item, column, col_idx)

    def _start_equip_cell_edit(self, item, column, col_idx):
        """在设备表格单元格上放置 Entry 控件"""
        bbox = self.equip_tree.bbox(item, column)
        if not bbox:
            return
        x, y, w, h = bbox

        values = self.equip_tree.item(item, "values")
        if not values:
            return
        current_val = str(values[col_idx - 1])

        self._edit_widget = tk.Entry(
            self.equip_tree,
            font=(FONT_UI, FS[9]),
            bg="#ffffff",
            relief="solid",
            bd=1,
        )
        self._edit_widget.place(x=x, y=y, width=w, height=h)
        self._edit_widget.insert(0, current_val)
        self._edit_widget.select_range(0, "end")
        self._edit_widget.focus_set()

        self._editing = True
        self._edit_item = item
        self._edit_col_idx = col_idx
        self._edit_old_values = values

        self._edit_widget.bind("<Return>", lambda e: self._commit_equip_cell_edit())
        self._edit_widget.bind("<Escape>", lambda e: self._cancel_equip_cell_edit())
        self._edit_widget.bind("<FocusOut>", self._on_equip_edit_focusout)

    def _on_equip_edit_focusout(self, event):
        """FocusOut 延迟提交"""
        if self._editing:
            self.after(100, self._commit_equip_cell_edit)

    def _commit_equip_cell_edit(self):
        """提交原地编辑：校验 → 更新 Equipment → 刷新"""
        if not self._editing:
            return
        self._editing = False

        if self._edit_widget is None:
            return

        new_value = self._edit_widget.get().strip()
        self._edit_widget.destroy()
        self._edit_widget = None

        col_idx = self._edit_col_idx
        old_values = self._edit_old_values
        old_value = str(old_values[col_idx - 1])

        # 未变更或为空则跳过（名称列允许为空不跳过，由校验处理）
        if col_idx != 2 and (new_value == old_value or not new_value):
            return
        if col_idx == 2 and new_value == old_value:
            return
        if col_idx == 2 and not new_value:
            return  # 名称不能为空

        # 获取对应的 Equipment 对象
        item = self._edit_item
        eq_idx = int(item.split("_")[1])
        eq_list = [e for i, e in enumerate(self._selected_group.equipment_list)
                   if not e.is_subtotal]
        if eq_idx >= len(eq_list):
            return
        eq = eq_list[eq_idx]

        try:
            if col_idx == 2:  # 设备名称
                eq.name = new_value
            elif col_idx == 3:  # Pe (kW)
                v = float(new_value)
                if v <= 0:
                    raise ValueError
                eq.rated_power = v
            elif col_idx == 4:  # 安装台数
                v = int(new_value)
                if v < 1:
                    raise ValueError
                if v < eq.working_count:
                    messagebox.showwarning("输入错误", "安装台数不能小于工作台数", parent=self)
                    return
                eq.installed_count = v
            elif col_idx == 5:  # 工作台数
                v = int(new_value)
                if v < 1:
                    raise ValueError
                if v > eq.installed_count:
                    messagebox.showwarning("输入错误", "工作台数不能大于安装台数", parent=self)
                    return
                eq.working_count = v
            elif col_idx == 6:  # Kx
                v = float(new_value)
                if not (0 < v <= 1):
                    raise ValueError
                eq.kx = v
            elif col_idx == 7:  # cosφ
                v = float(new_value)
                if not (0 < v <= 1):
                    raise ValueError
                eq.cos_phi = v
                from math import tan, acos
                eq.tan_phi = tan(acos(v))
            elif col_idx == 12:  # 备注
                eq.remark = new_value
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效的数值", parent=self)
            return

        # 刷新并通知重算
        self._load_equipment_table(self._selected_group)
        self._notify_data_changed()

    def _cancel_equip_cell_edit(self):
        """取消原地编辑"""
        if not self._editing:
            return
        self._editing = False
        if self._edit_widget is not None:
            self._edit_widget.destroy()
            self._edit_widget = None

    def _clear_selection(self):
        """清除所有选中状态"""
        self._selected_sub = None
        self._selected_group = None
        self._selected_equip_idx = None

        self.group_info.configure(
            text="请在左侧选择一个建/构筑物",
            fg=THEME["FG_MUTED"])

        for item in self.equip_tree.get_children():
            self.equip_tree.delete(item)

        self.status_label.configure(text="")
        self.btn_del_bldg.configure(state="disabled")
        self.btn_batch_del.configure(state="disabled")
        self.btn_del_sub.configure(state="disabled")
        self.btn_add_equip.configure(state="disabled")
        self.btn_edit_equip.configure(state="disabled")
        self.btn_del_equip.configure(state="disabled")

    def _filter_tree(self):
        """根据搜索关键字过滤树"""
        keyword = self.filter_entry.get().strip().lower()
        for item in self.building_tree.get_children():
            self.building_tree.item(item, open=bool(keyword))
            for child in self.building_tree.get_children(item):
                text = self.building_tree.item(child, "text").strip().lower()
                if keyword and keyword not in text:
                    self.building_tree.detach(child)
                else:
                    self.building_tree.reattach(child, item, "end")

    # ─────────────────────── CRUD操作 ───────────────────────

    def _add_equipment(self):
        """添加设备到当前建/构筑物"""
        if not self._selected_group:
            messagebox.showwarning("提示", "请先在左侧选择一个建/构筑物")
            return

        dialog = EquipmentEditDialog(self)
        if dialog.result:
            self._selected_group.add_equipment(dialog.result)
            self._load_equipment_table(self._selected_group)
            self._build_tree()  # 更新计数
            self._notify_data_changed()

    def _edit_equipment(self):
        """编辑选中的设备"""
        if self._selected_equip_idx is None or not self._selected_group:
            return

        eq_list = [e for i, e in enumerate(self._selected_group.equipment_list)
                   if not e.is_subtotal]
        if self._selected_equip_idx >= len(eq_list):
            return

        old_eq = eq_list[self._selected_equip_idx]
        dialog = EquipmentEditDialog(self, equipment=old_eq)
        if dialog.result:
            new_eq = dialog.result
            # 在原始列表中替换
            for i, e in enumerate(self._selected_group.equipment_list):
                if e is old_eq:
                    self._selected_group.equipment_list[i] = new_eq
                    break
            self._load_equipment_table(self._selected_group)
            self._notify_data_changed()

    def _delete_equipment(self):
        """删除选中的设备"""
        if self._selected_equip_idx is None or not self._selected_group:
            return

        eq_list = [(i, e) for i, e in
                   enumerate(self._selected_group.equipment_list)
                   if not e.is_subtotal]
        if self._selected_equip_idx >= len(eq_list):
            return

        idx, eq = eq_list[self._selected_equip_idx]
        if not messagebox.askyesno("确认删除",
                                   f"确定要删除设备「{eq.name}」吗？",
                                   parent=self):
            return

        del self._selected_group.equipment_list[idx]
        self._selected_equip_idx = None
        self._load_equipment_table(self._selected_group)
        self._build_tree()
        self._notify_data_changed()

    def _add_building(self):
        """添加建/构筑物（设备组）"""
        if not self.hv_system:
            messagebox.showwarning("提示", "系统数据未加载")
            return

        # 如果没有建筑物被选中，默认选择第一个子系统
        target_sub = self._selected_sub
        if not target_sub and self.hv_system.subsystems:
            target_sub = self.hv_system.subsystems[0]

        if not target_sub:
            return

        dialog = BuildingEditDialog(self)
        if dialog.result:
            info = dialog.result
            new_group = EquipmentGroup(
                name=info["name"],
                kp=info["kp"],
                kq=info["kq"],
            )
            # 添加到当前子系统的末尾
            target_sub.add_group(new_group)

            # 先通知数据变更（触发refresh刷新所有页面）
            self._notify_data_changed()

            # 再重建树并选中新建的建筑物
            self._build_tree()
            for si, sub in enumerate(self.hv_system.subsystems):
                if sub is target_sub:
                    for gi, grp in enumerate(sub.groups):
                        if grp is new_group:
                            iid = f"grp_{si}_{gi}"
                            if self.building_tree.exists(iid):
                                self.building_tree.selection_set(iid)
                                self.building_tree.see(iid)
                            break

    def _delete_building(self):
        """删除建/构筑物及其所有设备"""
        if not self._selected_group or not self._selected_sub:
            return

        group_name = self._selected_group.name
        equip_count = len([e for e in self._selected_group.equipment_list
                          if not e.is_subtotal])

        msg = f"确定要删除建/构筑物「{group_name}」吗？\n"
        msg += f"该操作将同时删除其中的 {equip_count} 台设备！"
        if not messagebox.askyesno("确认删除", msg, parent=self):
            return

        self._selected_sub.groups.remove(self._selected_group)
        self._notify_data_changed()
        self._clear_selection()
        self._build_tree()

    def _show_building_context_menu(self, event):
        """右键菜单：建/构筑物节点操作"""
        iid = self.building_tree.identify_row(event.y)
        if not iid or not iid.startswith("grp_"):
            return

        # 选中右键点击的节点
        self.building_tree.selection_set(iid)
        self.building_tree.focus(iid)

        # 更新group/sub信息以便菜单命令使用
        parts = iid.split("_")
        si, gi = int(parts[1]), int(parts[2])
        sub = self.hv_system.subsystems[si]
        group = sub.groups[gi]
        self._menu_context_group = group
        self._menu_context_sub = sub

        # 弹出菜单
        self._building_context_menu.post(event.x_root, event.y_root)

    def _edit_building_from_menu(self):
        """右键菜单：编辑建筑物"""
        group = getattr(self, '_menu_context_group', None)
        sub = getattr(self, '_menu_context_sub', None)
        if not group or not sub:
            return

        dialog = BuildingEditDialog(self, group=group)
        if dialog.result:
            self._selected_sub = sub
            self._selected_group = group
            self._load_equipment_table(group)
            self._build_tree()
            self._notify_data_changed()
            self.group_info.configure(
                text=f"  子系统: {sub.name}  ->  建/构筑物: {group.name}",
                fg=THEME["FG_PRIMARY"])

    def _delete_building_from_menu(self):
        """右键菜单：删除建筑物"""
        group = getattr(self, '_menu_context_group', None)
        sub = getattr(self, '_menu_context_sub', None)
        if not group or not sub:
            return

        group_name = group.name
        equip_count = len([e for e in group.equipment_list if not e.is_subtotal])
        msg = f"确定要删除建/构筑物「{group_name}」吗？\n"
        msg += f"该操作将同时删除其中的 {equip_count} 台设备！"
        if not messagebox.askyesno("确认删除", msg, parent=self):
            return

        sub.groups.remove(group)
        self._notify_data_changed()
        self._clear_selection()
        self._build_tree()

    def _batch_delete_buildings(self):
        """批量删除选中的多个建/构筑物"""
        sel = self.building_tree.selection()
        grp_items = [(iid, iid.split("_")) for iid in sel if iid.startswith("grp_")]
        if len(grp_items) < 2:
            messagebox.showwarning("提示", "请按住 Ctrl 键同时选中多个建/构筑物", parent=self)
            return

        # 收集所有要删除的建筑物信息
        delete_list = []
        for iid, parts in grp_items:
            si, gi = int(parts[1]), int(parts[2])
            if si < len(self.hv_system.subsystems):
                sub = self.hv_system.subsystems[si]
                if gi < len(sub.groups):
                    group = sub.groups[gi]
                    equip_count = len([e for e in group.equipment_list if not e.is_subtotal])
                    delete_list.append((sub, group, equip_count))

        if not delete_list:
            return

        # 构建确认对话框
        msg = "确定要删除以下建/构筑物吗？\n"
        msg += "=" * 40 + "\n"
        total_equip = 0
        for sub, group, equip_count in delete_list:
            msg += f"  - 「{group.name}」（{equip_count}台设备）\n"
            total_equip += equip_count
        msg += "=" * 40 + "\n"
        msg += f"共 {len(delete_list)} 个建/构筑物，{total_equip} 台设备将被删除！"

        if not messagebox.askyesno("确认批量删除", msg, parent=self):
            return

        # 执行删除
        for sub, group, _ in delete_list:
            sub.groups.remove(group)

        self._notify_data_changed()
        self._clear_selection()
        self._build_tree()

    def _add_subsystem(self):
        """添加配电系统"""
        if not self.hv_system:
            messagebox.showwarning("提示", "系统数据未加载")
            return

        dialog = SubsystemEditDialog(self)
        if dialog.result:
            new_sub = dialog.result
            self.hv_system.add_subsystem(new_sub)
            self._notify_data_changed()
            self._build_tree()
            # 展开树并选中新建的子系统
            for si, sub in enumerate(self.hv_system.subsystems):
                if sub is new_sub:
                    iid = f"sub_{si}"
                    if self.building_tree.exists(iid):
                        self.building_tree.selection_set(iid)
                        self.building_tree.see(iid)
                    break

    def _delete_subsystem(self):
        """删除配电系统及其所有建/构筑物"""
        if not self._selected_sub:
            messagebox.showwarning("提示", "请先在左侧选中一个配电系统")
            return

        sub_name = self._selected_sub.name
        building_count = len(self._selected_sub.groups)

        msg = f"确定要删除配电系统「{sub_name}」吗？\n"
        msg += f"该操作将同时删除其中的 {building_count} 个建/构筑物及其所有设备！"
        if not messagebox.askyesno("确认删除", msg, parent=self):
            return

        self.hv_system.subsystems.remove(self._selected_sub)
        self._notify_data_changed()
        self._clear_selection()
        self._build_tree()

    def _notify_data_changed(self):
        """通知主窗口数据已变更（刷新其他页面）"""
        if self._notify_callback:
            self._notify_callback()

    def _open_kx_editor(self):
        """打开Kx参考值表编辑器"""
        KxReferenceEditorDialog(self)

    def _open_valve_power_config(self):
        """打开阀门功率预设配置对话框"""
        ValvePowerConfigDialog(self)

    # ─────────────────────── 公开接口 ───────────────────────

    def refresh(self):
        """刷新整个页面"""
        if not self.hv_system:
            return

        # 保存当前选中状态
        saved_sub = self._selected_sub
        saved_group = self._selected_group

        self._build_tree()
        self._clear_selection()

        # 尝试恢复选中 - 直接恢复内部状态和设备表格，不依赖事件触发
        # 因为 selection_set() 在某些环境下可能不触发 <<TreeviewSelect>> 事件
        if saved_group and saved_sub:
            for si, sub in enumerate(self.hv_system.subsystems):
                if sub is saved_sub:
                    for gi, grp in enumerate(sub.groups):
                        if grp is saved_group:
                            iid = f"grp_{si}_{gi}"
                            if self.building_tree.exists(iid):
                                self.building_tree.selection_set(iid)
                                self.building_tree.see(iid)
                                # 直接设置内部状态并加载设备表
                                self._selected_sub = saved_sub
                                self._selected_group = saved_group
                                self._load_equipment_table(saved_group)
                                self.group_info.configure(
                                    text=f"  子系统: {saved_sub.name}  ->  建/构筑物: {saved_group.name}",
                                    fg=THEME["FG_PRIMARY"])
                                self.btn_del_bldg.configure(state="normal")
                                self.btn_del_sub.configure(state="normal")
                                self.btn_add_equip.configure(state="normal")
                            break

    def _import_from_excel(self):
        """从Excel文件导入设备（文件选择对话框）"""
        from tkinter import filedialog
        files = filedialog.askopenfilenames(
            title="选择设备清单Excel文件（可多选）",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")],
            parent=self,
        )
        if files:
            self._import_files(files)

    def _import_files(self, file_paths):
        """导入Excel文件列表（供按钮和拖放共用）"""
        if not self.hv_system:
            messagebox.showwarning("提示", "系统数据未加载")
            return

        target_sub = self._selected_sub
        if not target_sub and self.hv_system.subsystems:
            target_sub = self.hv_system.subsystems[0]
        if not target_sub:
            messagebox.showwarning("提示", "请先创建或选择一个配电系统", parent=self)
            return

        imported = 0
        buildings = []
        errors = []

        for fp in file_paths:
            try:
                name, eqs = parse_excel_file(fp)
                if not eqs:
                    errors.append((os.path.basename(fp), "未识别到有效设备"))
                    continue
                grp = EquipmentGroup(name=name)
                for e in eqs:
                    grp.add_equipment(e)
                target_sub.add_group(grp)
                imported += len(eqs)
                buildings.append(name)
            except Exception as e:
                errors.append((os.path.basename(fp), str(e)))

        if imported > 0:
            self._notify_data_changed()
            self._build_tree()
            msg = f"✅ 导入完成\n新建建筑物: {'、'.join(buildings)}\n导入设备: {imported} 台"
            if errors:
                msg += "\n\n以下失败:\n" + "\n".join(f"  {f}: {e}" for f, e in errors)
            messagebox.showinfo("导入完成", msg, parent=self)
            last = buildings[-1]
            for si, sub in enumerate(self.hv_system.subsystems):
                if sub is target_sub:
                    for gi, grp in enumerate(sub.groups):
                        if grp.name == last:
                            iid = f"grp_{si}_{gi}"
                            if self.building_tree.exists(iid):
                                self.building_tree.selection_set(iid)
                                self.building_tree.see(iid)
                            break
        else:
            msg = "未导入任何设备\n" + "\n".join(f"  {f}: {e}" for f, e in errors)
            messagebox.showwarning("导入结果", msg, parent=self)

    def _on_drop(self, event):
        """拖放文件事件处理"""
        raw = event.data
        if not raw:
            return
        try:
            files = self.tk.splitlist(raw)
        except Exception:
            files = str(raw).replace("{", "").replace("}", "").split()
        files = [f.strip() for f in files]
        xlsx_files = [f for f in files
                      if f.lower().endswith(('.xlsx', '.xls'))]
        if not xlsx_files:
            messagebox.showinfo("提示", "请拖放 .xlsx 或 .xls 格式的Excel文件", parent=self)
            return
        self._import_files(xlsx_files)
