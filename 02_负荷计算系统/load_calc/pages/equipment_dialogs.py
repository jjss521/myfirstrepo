# -*- coding: utf-8 -*-
"""设备与建/构筑物编辑对话框"""

import tkinter as tk
from tkinter import ttk, messagebox
from math import tan, acos, sqrt
from ..models import Equipment, EquipmentGroup, Subsystem, LOAD_LEVEL_CHOICES
from ..config import DEFAULT_KX, DEFAULT_COS_PHI, DEFAULT_TAN_PHI
from ..reference_db import KX_DB


class EquipmentEditDialog:
    """设备添加/编辑对话框"""

    def __init__(self, parent, equipment: Equipment = None):
        self.parent = parent
        self.equipment = equipment
        self.result = None
        self._suggestion_label = None
        self._grab_set_done = False

        self._create_dialog()
        if equipment:
            self._load_data(equipment)
        self.dialog.wait_window()

    def _create_dialog(self):
        is_edit = self.equipment is not None
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑设备" if is_edit else "添加设备")
        self.dialog.geometry("480x560")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self._grab_set_done = True
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # 主框架
        main = ttk.Frame(self.dialog, padding=20)
        main.pack(fill="both", expand=True)

        # 标题
        title_text = "编辑设备信息" if is_edit else "添加新设备"
        ttk.Label(main, text=title_text,
                  font=("微软雅黑", 14, "bold"),
                  foreground="#1565C0").pack(anchor="w", pady=(0, 15))

        # 表单字段
        fields_frame = ttk.Frame(main)
        fields_frame.pack(fill="both", expand=True)

        # 定义字段
        self.entries = {}
        fields = [
            ("name", "设备名称 *", True),
            ("rated_power", "额定功率 (kW) *", True),
            ("installed_count", "安装台数", False),
            ("working_count", "工作台数", False),
            ("kx", "需要系数 Kx", False),
            ("cos_phi", "功率因数 cosφ", False),
            ("tan_phi", "tanφ", False),
            ("comp_qc", "无功补偿率(kvar)", False),
            ("remark", "备注", False),
        ]

        row = 0
        for key, label, required in fields:
            container = ttk.Frame(fields_frame)
            container.grid(row=row, column=0, sticky="ew", pady=4, padx=5)
            container.columnconfigure(1, weight=1)

            mark = " *" if required else ""
            ttk.Label(container, text=label + mark,
                      font=("微软雅黑", 10),
                      width=18, anchor="w").grid(row=0, column=0, sticky="w")

            entry = ttk.Entry(container, font=("微软雅黑", 10))
            entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
            self.entries[key] = entry
            row += 1

        # 负荷等级下拉
        level_container = ttk.Frame(fields_frame)
        level_container.grid(row=row, column=0, sticky="ew", pady=4, padx=5)
        level_container.columnconfigure(1, weight=1)
        ttk.Label(level_container, text="负荷等级",
                  font=("微软雅黑", 10),
                  width=18, anchor="w").grid(row=0, column=0, sticky="w")
        self.load_level_var = tk.StringVar(value="二级负荷")
        self.load_level_combo = ttk.Combobox(level_container,
                                              textvariable=self.load_level_var,
                                              values=LOAD_LEVEL_CHOICES,
                                              font=("微软雅黑", 10),
                                              state="readonly", width=22)
        self.load_level_combo.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        row += 1

        # 自动计算tanφ的绑定
        self.entries["cos_phi"].bind("<KeyRelease>", self._auto_calc_tan_phi)

        # 设备名称输入时触发Kx建议
        self.entries["name"].bind("<KeyRelease>", self._on_name_changed)

        # 建议标签
        self._suggestion_label = ttk.Label(
            fields_frame,
            text="",
            font=("微软雅黑", 9),
            foreground="#1565C0",
            wraplength=420,
        )
        self._suggestion_label.grid(
            row=row, column=0, columnspan=2, sticky="w",
            padx=5, pady=(2, 0))
        row += 1

        # 提示
        ttk.Label(fields_frame,
                  text="* 为必填项 | 修改cosφ后自动计算tanφ | 输入设备名称自动推荐Kx | 负荷等级根据名称自动检测",
                  font=("微软雅黑", 8), foreground="#999").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(5, 0))

        # 按钮区
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(btn_frame, text="确定",
                   command=self._on_confirm,
                   width=12).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="取消",
                   command=self._on_cancel,
                   width=12).pack(side="right")

        # 居中
        self.dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - 480) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - 500) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _on_name_changed(self, event=None):
        """设备名称改变时自动搜索Kx建议"""
        name = self.entries["name"].get().strip()
        if not name or len(name) < 1:
            if self._suggestion_label:
                self._suggestion_label.configure(text="")
            return

        matches = KX_DB.fuzzy_search(name, top_n=3)
        if not matches:
            self._suggestion_label.configure(
                text="未匹配到Kx参考值，请手动输入", foreground="#999")
            return

        best = matches[0]
        txt = (f"推荐参考: [{best.equipment_name}] "
               f"Kx={best.kx_range}  cosφ={best.cos_phi_range}")
        if len(matches) > 1:
            txt += f"\n其他匹配: {' | '.join(m.equipment_name for m in matches[1:])}"
        self._suggestion_label.configure(text=txt, foreground="#1565C0")

        # 只在创建模式且字段为空时自动填充
        if self.equipment is None:
            if not self.entries["kx"].get():
                self.entries["kx"].delete(0, "end")
                self.entries["kx"].insert(0, str(best.kx_avg))
            if not self.entries["cos_phi"].get():
                self.entries["cos_phi"].delete(0, "end")
                self.entries["cos_phi"].insert(0, str(best.cos_phi_avg))
            if not self.entries["tan_phi"].get():
                self.entries["tan_phi"].delete(0, "end")
                self.entries["tan_phi"].insert(0, str(best.tan_phi_avg))

            
    def _auto_calc_tan_phi(self, event=None):
        """根据cosφ自动计算tanφ"""
        try:
            cos_val = float(self.entries["cos_phi"].get())
            if 0 < cos_val <= 1:
                tan_val = tan(acos(cos_val))
                self.entries["tan_phi"].delete(0, "end")
                self.entries["tan_phi"].insert(0, f"{tan_val:.4f}")
            elif cos_val > 1:
                self.entries["cos_phi"].delete(0, "end")
                self.entries["cos_phi"].insert(0, "1.0")
        except (ValueError, ZeroDivisionError):
            pass

    def _load_data(self, eq: Equipment):
        """编辑模式：加载设备数据到表单"""
        self.entries["name"].insert(0, eq.name)
        self.entries["rated_power"].insert(0, str(eq.rated_power))
        self.entries["installed_count"].insert(0, str(eq.installed_count))
        self.entries["working_count"].insert(0, str(eq.working_count))
        self.entries["kx"].insert(0, str(eq.kx))
        self.entries["cos_phi"].insert(0, str(eq.cos_phi))
        self.entries["tan_phi"].insert(0, str(eq.tan_phi))
        self.entries["comp_qc"].insert(0, str(eq.comp_qc))
        self.entries["remark"].insert(0, eq.remark)
        self.load_level_var.set(eq.load_level)

    def _validate(self) -> bool:
        """校验输入数据"""
        try:
            name = self.entries["name"].get().strip()
            if not name:
                messagebox.showwarning("输入错误", "请输入设备名称", parent=self.dialog)
                return False

            rated = float(self.entries["rated_power"].get())
            if rated <= 0:
                messagebox.showwarning("输入错误", "额定功率必须大于0", parent=self.dialog)
                return False

            installed = int(self.entries["installed_count"].get() or "1")
            working = int(self.entries["working_count"].get() or "1")
            if installed < 1 or working < 1:
                messagebox.showwarning("输入错误", "台数必须≥1", parent=self.dialog)
                return False
            if working > installed:
                messagebox.showwarning("输入错误", "工作台数不能大于安装台数", parent=self.dialog)
                return False

            kx = float(self.entries["kx"].get() or str(DEFAULT_KX))
            if not (0 < kx <= 1):
                messagebox.showwarning("输入错误", "Kx应在0~1之间", parent=self.dialog)
                return False

            cos_phi = float(self.entries["cos_phi"].get() or str(DEFAULT_COS_PHI))
            if not (0 < cos_phi <= 1):
                messagebox.showwarning("输入错误", "cosφ应在0~1之间", parent=self.dialog)
                return False

            tan_phi = float(self.entries["tan_phi"].get() or str(DEFAULT_TAN_PHI))
            return True

        except ValueError:
            messagebox.showwarning("输入错误", "请检查数值格式", parent=self.dialog)
            return False

    def _safe_destroy(self):
        """安全销毁对话框，释放grab资源"""
        try:
            if self._grab_set_done:
                self.dialog.grab_release()
                self._grab_set_done = False
        except Exception:
            pass
        try:
            self.dialog.destroy()
        except Exception:
            pass

    def _on_confirm(self):
        if not self._validate():
            return
        name = self.entries["name"].get().strip()
        rated_power = float(self.entries["rated_power"].get())
        installed_count = int(self.entries["installed_count"].get() or "1")
        working_count = int(self.entries["working_count"].get() or "1")
        kx = float(self.entries["kx"].get() or str(DEFAULT_KX))
        cos_phi = float(self.entries["cos_phi"].get() or str(DEFAULT_COS_PHI))
        tan_phi = float(self.entries["tan_phi"].get() or str(DEFAULT_TAN_PHI))
        comp_qc = float(self.entries["comp_qc"].get() or "0")
        if comp_qc < 0:
            messagebox.showwarning("输入错误", "无功补偿率不能为负数", parent=self.dialog)
            return False
        remark = self.entries["remark"].get().strip()

        self.result = Equipment(
            name=name,
            rated_power=rated_power,
            installed_count=installed_count,
            working_count=working_count,
            kx=kx,
            cos_phi=cos_phi,
            tan_phi=tan_phi,
            comp_qc=comp_qc,
            remark=remark,
            load_level=self.load_level_var.get(),
        )
        self._safe_destroy()

    def _on_cancel(self):
        self.result = None
        self._safe_destroy()


class KxReferenceEditorDialog:
    """Kx参考值表编辑器对话框"""

    def __init__(self, parent):
        self.parent = parent
        self.result = False
        self._grab_set_done = False
        self._create_dialog()
        self._load_table()
        self.dialog.wait_window()

    def _create_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Kx参考值表管理")
        self.dialog.geometry("720x520")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self._grab_set_done = True
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

        main = ttk.Frame(self.dialog, padding=15)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="常用设备需要系数和功率因数参考表",
                  font=("微软雅黑", 14, "bold"),
                  foreground="#4E342E").pack(anchor="w", pady=(0, 10))

        # 搜索区
        search_frame = ttk.Frame(main)
        search_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(search_frame, text="搜索:",
                  font=("微软雅黑", 9)).pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, font=("微软雅黑", 10), width=30)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._load_table())

        # 参考表
        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True, pady=(0, 8))

        columns = ("name", "kx", "cos", "tan")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", height=12,
                                 selectmode="browse")
        col_config = [
            ("name", "设备名称", 280),
            ("kx", "Kx范围", 100),
            ("cos", "cosφ范围", 110),
            ("tan", "tanφ范围", 110),
        ]
        for key, text, w in col_config:
            self.tree.heading(key, text=text)
            self.tree.column(key, width=w, anchor="center")
        self.tree.column("name", anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # 编辑区
        edit_frame = ttk.LabelFrame(main, text="编辑选中项", padding=10)
        edit_frame.pack(fill="x")

        row_f = ttk.Frame(edit_frame)
        row_f.pack(fill="x", pady=2)

        ttk.Label(row_f, text="设备名称:",
                  font=("微软雅黑", 9), width=10).pack(side="left")
        self.edit_name = ttk.Entry(row_f, font=("微软雅黑", 9), width=35)
        self.edit_name.pack(side="left", padx=5)

        ttk.Label(row_f, text="Kx:", font=("微软雅黑", 9)).pack(side="left", padx=(15, 0))
        self.edit_kx = ttk.Entry(row_f, font=("微软雅黑", 9), width=10)
        self.edit_kx.pack(side="left", padx=5)

        ttk.Label(row_f, text="cosφ:", font=("微软雅黑", 9)).pack(side="left", padx=(15, 0))
        self.edit_cos = ttk.Entry(row_f, font=("微软雅黑", 9), width=10)
        self.edit_cos.pack(side="left", padx=5)

        ttk.Label(row_f, text="tanφ:", font=("微软雅黑", 9)).pack(side="left", padx=(15, 0))
        self.edit_tan = ttk.Entry(row_f, font=("微软雅黑", 9), width=10)
        self.edit_tan.pack(side="left", padx=5)

        # 按钮
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.pack(fill="x", pady=(8, 0))

        ttk.Button(btn_frame, text="保存修改",
                   command=self._save_edit,
                   width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="添加新项",
                   command=self._add_new,
                   width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="删除选中",
                   command=self._delete_item,
                   width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="关闭",
                   command=self._on_close,
                   width=10).pack(side="right", padx=5)

        self.dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - 720) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - 520) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _load_table(self, keyword=""):
        for item in self.tree.get_children():
            self.tree.delete(item)
        keyword = keyword or self.search_entry.get().strip()
        if keyword:
            refs = KX_DB.search(keyword)
        else:
            refs = [KX_DB.get(n) for n in KX_DB.all_names]
        for ref in refs:
            if ref:
                self.tree.insert("", "end", values=(
                    ref.equipment_name,
                    ref.kx_range,
                    ref.cos_phi_range,
                    ref.tan_phi_range,
                ))

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        if values:
            self.edit_name.delete(0, "end")
            self.edit_name.insert(0, values[0])
            self.edit_kx.delete(0, "end")
            self.edit_kx.insert(0, values[1])
            self.edit_cos.delete(0, "end")
            self.edit_cos.insert(0, values[2])
            self.edit_tan.delete(0, "end")
            self.edit_tan.insert(0, values[3])

    def _save_edit(self):
        name = self.edit_name.get().strip()
        kx = self.edit_kx.get().strip()
        cos = self.edit_cos.get().strip()
        tan = self.edit_tan.get().strip()
        if not name or not kx or not cos or not tan:
            messagebox.showwarning("输入错误", "请填写完整信息", parent=self.dialog)
            return
        try:
            KX_DB.update(name, kx, cos, tan)
            self._load_table()
            messagebox.showinfo("成功", f"已保存: {name}", parent=self.dialog)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}", parent=self.dialog)

    def _add_new(self):
        self.edit_name.delete(0, "end")
        self.edit_kx.delete(0, "end")
        self.edit_cos.delete(0, "end")
        self.edit_tan.delete(0, "end")
        self.edit_name.focus()

    def _delete_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择要删除的项", parent=self.dialog)
            return
        values = self.tree.item(sel[0], "values")
        if not values:
            return
        if messagebox.askyesno("确认删除",
                               f"确定删除「{values[0]}」的参考值？",
                               parent=self.dialog):
            if values[0] in KX_DB._table:
                del KX_DB._table[values[0]]
            self._load_table()
            self.edit_name.delete(0, "end")
            self.edit_kx.delete(0, "end")
            self.edit_cos.delete(0, "end")
            self.edit_tan.delete(0, "end")

    def _safe_destroy(self):
        """安全销毁对话框，释放grab资源"""
        try:
            if self._grab_set_done:
                self.dialog.grab_release()
                self._grab_set_done = False
        except Exception:
            pass
        try:
            self.dialog.destroy()
        except Exception:
            pass

    def _on_close(self):
        self.result = True
        self._safe_destroy()


class BuildingEditDialog:
    """建/构筑物（设备组）添加/编辑对话框"""

    def __init__(self, parent, group: EquipmentGroup = None):
        self.parent = parent
        self.group = group
        self.result = None
        self._grab_set_done = False

        self._create_dialog()
        if group:
            self._load_data(group)
        self.dialog.wait_window()

    def _create_dialog(self):
        is_edit = self.group is not None
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑建/构筑物" if is_edit else "添加建/构筑物")
        self.dialog.geometry("420x280")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self._grab_set_done = True
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        main = ttk.Frame(self.dialog, padding=20)
        main.pack(fill="both", expand=True)

        title_text = "编辑建/构筑物信息" if is_edit else "添加新建/构筑物"
        ttk.Label(main, text=title_text,
                  font=("微软雅黑", 14, "bold"),
                  foreground="#4E342E").pack(anchor="w", pady=(0, 15))

        fields_frame = ttk.Frame(main)
        fields_frame.pack(fill="both", expand=True)

        self.entries = {}
        fields = [
            ("name", "建/构筑物名称 *"),
            ("kp", "有功同时系数 K\u2211p"),
            ("kq", "无功同时系数 K\u2211q"),
        ]

        for row, (key, label) in enumerate(fields):
            container = ttk.Frame(fields_frame)
            container.grid(row=row, column=0, sticky="ew", pady=6, padx=5)
            container.columnconfigure(1, weight=1)

            ttk.Label(container, text=label,
                      font=("微软雅黑", 10),
                      width=22, anchor="w").grid(row=0, column=0, sticky="w")

            entry = ttk.Entry(container, font=("微软雅黑", 10))
            entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
            self.entries[key] = entry

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(btn_frame, text="确定",
                   command=self._on_confirm,
                   width=12).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="取消",
                   command=self._on_cancel,
                   width=12).pack(side="right")

        self.dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - 420) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - 280) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _load_data(self, group: EquipmentGroup):
        self.entries["name"].insert(0, group.name)
        self.entries["kp"].insert(0, str(group.kp))
        self.entries["kq"].insert(0, str(group.kq))

    def _validate(self) -> bool:
        try:
            name = self.entries["name"].get().strip()
            if not name:
                messagebox.showwarning("输入错误", "请输入建/构筑物名称", parent=self.dialog)
                return False

            kp = float(self.entries["kp"].get() or "1.0")
            kq = float(self.entries["kq"].get() or "1.0")
            if not (0 < kp <= 1):
                messagebox.showwarning("输入错误", "K∑p应在0~1之间", parent=self.dialog)
                return False
            if not (0 < kq <= 1):
                messagebox.showwarning("输入错误", "K∑q应在0~1之间", parent=self.dialog)
                return False
            return True
        except ValueError:
            messagebox.showwarning("输入错误", "请检查数值格式", parent=self.dialog)
            return False

    def _safe_destroy(self):
        """安全销毁对话框，释放grab资源"""
        try:
            if self._grab_set_done:
                self.dialog.grab_release()
                self._grab_set_done = False
        except Exception:
            pass
        try:
            self.dialog.destroy()
        except Exception:
            pass

    def _on_confirm(self):
        if not self._validate():
            return
        self.result = {
            "name": self.entries["name"].get().strip(),
            "kp": float(self.entries["kp"].get() or "1.0"),
            "kq": float(self.entries["kq"].get() or "1.0"),
        }
        self._safe_destroy()

    def _on_cancel(self):
        self.result = None
        self._safe_destroy()


class SubsystemEditDialog:
    """配电系统添加/编辑对话框"""

    def __init__(self, parent, subsystem: Subsystem = None):
        self.parent = parent
        self.subsystem = subsystem
        self.result = None
        self._grab_set_done = False

        self._create_dialog()
        if subsystem:
            self._load_data(subsystem)
        self.dialog.wait_window()

    def _create_dialog(self):
        is_edit = self.subsystem is not None
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑配电系统" if is_edit else "添加配电系统")
        self.dialog.geometry("460x420")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self._grab_set_done = True
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        from ..models import TRANSFORMER_OPERATION_MODES, VoltageLevel

        main = ttk.Frame(self.dialog, padding=20)
        main.pack(fill="both", expand=True)

        title_text = "编辑配电系统信息" if is_edit else "添加新配电系统"
        ttk.Label(main, text=title_text,
                  font=("微软雅黑", 14, "bold"),
                  foreground="#1565C0").pack(anchor="w", pady=(0, 15))

        fields_frame = ttk.Frame(main)
        fields_frame.pack(fill="both", expand=True)

        self.entries = {}
        fields = [
            ("name", "配电系统名称 *", True),
            ("voltage", "电压等级", False),
            ("transformer_rating", "单台变压器容量(kVA)", False),
            ("transformer_count", "变压器台数", False),
            ("transformer_mode", "运行方式", False),
            ("target_pf", "目标功率因数", False),
        ]

        for row, (key, label, required) in enumerate(fields):
            container = ttk.Frame(fields_frame)
            container.grid(row=row, column=0, sticky="ew", pady=4, padx=5)
            container.columnconfigure(1, weight=1)

            mark = " *" if required else ""
            ttk.Label(container, text=label + mark,
                      font=("微软雅黑", 10),
                      width=22, anchor="w").grid(row=0, column=0, sticky="w")

            if key == "voltage":
                entry = ttk.Combobox(container,
                                     values=[v.value for v in VoltageLevel],
                                     font=("微软雅黑", 10), state="readonly",
                                     width=22)
                entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
                entry.set("0.4kV")
            elif key == "transformer_mode":
                entry = ttk.Combobox(container,
                                     values=TRANSFORMER_OPERATION_MODES,
                                     font=("微软雅黑", 10),
                                     width=22, state="normal")
                entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
                entry.set("同时运行")
            else:
                entry = ttk.Entry(container, font=("微软雅黑", 10))
                entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
            self.entries[key] = entry

        # 提示
        ttk.Label(fields_frame,
                  text="* 为必填项 | 变压器参数可后续在配电系统页面修改",
                  font=("微软雅黑", 8), foreground="#999").grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(5, 0))

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(btn_frame, text="确定",
                   command=self._on_confirm,
                   width=12).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="取消",
                   command=self._on_cancel,
                   width=12).pack(side="right")

        self.dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - 460) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - 420) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _load_data(self, sub: Subsystem):
        self.entries["name"].insert(0, sub.name)
        self.entries["voltage"].set(sub.voltage.value)
        self.entries["transformer_rating"].insert(0, str(sub.transformer_rating))
        self.entries["transformer_count"].insert(0, str(sub.transformer_count))
        self.entries["transformer_mode"].set(sub.transformer_operation_mode)
        self.entries["target_pf"].insert(0, str(sub.target_power_factor))

    def _validate(self) -> bool:
        try:
            name = self.entries["name"].get().strip()
            if not name:
                messagebox.showwarning("输入错误", "请输入配电系统名称", parent=self.dialog)
                return False

            rating = float(self.entries["transformer_rating"].get() or "0")
            if rating < 0:
                messagebox.showwarning("输入错误", "变压器容量不能为负数", parent=self.dialog)
                return False

            count = int(self.entries["transformer_count"].get() or "0")
            if count < 0:
                messagebox.showwarning("输入错误", "变压器台数不能为负数", parent=self.dialog)
                return False

            pf = float(self.entries["target_pf"].get() or "0.95")
            if not (0 < pf <= 1):
                messagebox.showwarning("输入错误", "目标功率因数应在0~1之间", parent=self.dialog)
                return False

            return True
        except ValueError:
            messagebox.showwarning("输入错误", "请检查数值格式", parent=self.dialog)
            return False

    def _on_confirm(self):
        if not self._validate():
            return

        from ..models import VoltageLevel

        name = self.entries["name"].get().strip()
        voltage_str = self.entries["voltage"].get()
        try:
            voltage = next(v for v in VoltageLevel if v.value == voltage_str)
        except StopIteration:
            voltage = VoltageLevel.LV_380V

        rating = float(self.entries["transformer_rating"].get() or "0")
        count = int(self.entries["transformer_count"].get() or "0")
        mode = self.entries["transformer_mode"].get() or "同时运行"
        target_pf = float(self.entries["target_pf"].get() or "0.95")

        self.result = Subsystem(
            name=name,
            voltage=voltage,
            transformer_rating=rating,
            transformer_count=count,
            transformer_operation_mode=mode,
            target_power_factor=target_pf,
        )
        self._safe_destroy()

    def _on_cancel(self):
        self.result = None
        self._safe_destroy()


class KpKqEditDialog:
    """同时系数KΣP/KΣq快速编辑对话框"""

    def __init__(self, parent, group: EquipmentGroup = None, subsystem: Subsystem = None):
        self.parent = parent
        self.group = group
        self.subsystem = subsystem
        self.result = None
        self._grab_set_done = False

        self._create_dialog()
        if group:
            self._load_data(group)
        elif subsystem:
            if subsystem.groups:
                self._load_data(subsystem.groups[0])
        self.dialog.wait_window()

    def _create_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑同时系数")
        self.dialog.geometry("360x220")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self._grab_set_done = True
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        main = ttk.Frame(self.dialog, padding=20)
        main.pack(fill="both", expand=True)

        if self.subsystem:
            title_text = f"批量设置同时系数 - {self.subsystem.name}"
        elif self.group:
            title_text = f"编辑「{self.group.name}」的同时系数"
        else:
            title_text = "编辑同时系数"
        ttk.Label(main,
                  text=title_text,
                  font=("微软雅黑", 12, "bold"),
                  foreground="#4E342E").pack(anchor="w", pady=(0, 15))

        fields_frame = ttk.Frame(main)
        fields_frame.pack(fill="both", expand=True)

        self.entries = {}
        fields = [
            ("kp", "有功同时系数 K∑p", "1.0"),
            ("kq", "无功同时系数 K∑q", "1.0"),
        ]

        for row, (key, label, default) in enumerate(fields):
            container = ttk.Frame(fields_frame)
            container.grid(row=row, column=0, sticky="ew", pady=6, padx=5)
            container.columnconfigure(1, weight=1)

            ttk.Label(container, text=label,
                      font=("微软雅黑", 10),
                      width=24, anchor="w").grid(row=0, column=0, sticky="w")

            entry = ttk.Entry(container, font=("微软雅黑", 10))
            entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
            entry.insert(0, default)
            self.entries[key] = entry

        # 提示
        hint_text = ("提示：将统一设置当前子系统下全部设备组的KΣP/KΣq值"
                     if self.subsystem else
                     "提示：修改后立即触发全系统重新计算")
        ttk.Label(fields_frame,
                  text=hint_text,
                  font=("微软雅黑", 8), foreground="#999").grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(5, 0))

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(btn_frame, text="确定",
                   command=self._on_confirm,
                   width=12).pack(side="right", padx=(10, 0))
        ttk.Button(btn_frame, text="取消",
                   command=self._on_cancel,
                   width=12).pack(side="right")

        self.dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - 360) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - 220) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _load_data(self, group: EquipmentGroup):
        self.entries["kp"].delete(0, "end")
        self.entries["kp"].insert(0, str(group.kp))
        self.entries["kq"].delete(0, "end")
        self.entries["kq"].insert(0, str(group.kq))

    def _validate(self) -> bool:
        try:
            kp = float(self.entries["kp"].get() or "1.0")
            kq = float(self.entries["kq"].get() or "1.0")
            if not (0 < kp <= 1):
                messagebox.showwarning("输入错误", "K∑p应在0~1之间", parent=self.dialog)
                return False
            if not (0 < kq <= 1):
                messagebox.showwarning("输入错误", "K∑q应在0~1之间", parent=self.dialog)
                return False
            return True
        except ValueError:
            messagebox.showwarning("输入错误", "请检查数值格式", parent=self.dialog)
            return False

    def _on_confirm(self):
        if not self._validate():
            return
        kp = float(self.entries["kp"].get() or "1.0")
        kq = float(self.entries["kq"].get() or "1.0")
        if self.group:
            self.group.kp = kp
            self.group.kq = kq
            self.result = {"kp": kp, "kq": kq}
        elif self.subsystem:
            for g in self.subsystem.groups:
                g.kp = kp
                g.kq = kq
            self.result = {"kp": kp, "kq": kq, "count": len(self.subsystem.groups)}
        self._safe_destroy()

    def _on_cancel(self):
        self.result = None
        self._safe_destroy()

    def _safe_destroy(self):
        """安全销毁对话框，释放grab资源"""
        try:
            if self._grab_set_done:
                self.dialog.grab_release()
                self._grab_set_done = False
        except Exception:
            pass
        try:
            self.dialog.destroy()
        except Exception:
            pass
