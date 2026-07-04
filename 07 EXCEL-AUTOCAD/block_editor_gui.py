"""PDSG 图块编辑器 GUI

独立的图块管理界面，功能包括:
- 浏览 2 种标准回路图块定义 (LOOP_POWER_A / LOOP_POWER_B)
- 一键生成完整图块库 (block_library.dwg + title_block.dwg)
- 创建/重建单个图块
- 在 AutoCAD 块编辑器 (BEDIT) 中修改图块
- 验证图块库完整性
- 保存图块库 DWG

启动方式:
  python run_block_editor.py
  或从主程序 gui.py 菜单「工具 → 图块编辑器」打开
"""
import logging
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# 确保 src 在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_model import AcadConfig
from src.errors import AcadConnectionError, AcadOperationError, BlockLibraryError
from src.block_editor import (
    BlockEditor,
    BlockParams,
    STANDARD_BLOCKS,
    TITLE_BLOCK_ATTRS,
)
from src.config_loader import load_config

logger = logging.getLogger("pdsg.block_editor_gui")


# ================================================================
# 图块编辑器窗口
# ================================================================

class BlockEditorWindow:
    """图块编辑器独立窗口"""

    TITLE = "PDSG 图块编辑器"
    SIZE = "960x680"

    def __init__(self, parent: tk.Tk = None, cfg=None):
        """
        Args:
            parent: 父窗口 (为 None 时创建新 Tk)
            cfg: AppConfig 配置对象
        """
        self.cfg = cfg
        self._owns_root = parent is None
        if parent is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(parent)

        self.root.title(self.TITLE)
        self.root.geometry(self.SIZE)
        self.root.minsize(800, 550)

        # 图块编辑器实例
        self.editor = BlockEditor()
        self._acad_connected = False

        # 样式
        self.style = ttk.Style()
        self._apply_style()

        # 构建界面
        self._build_layout()

        # 加载配置
        if cfg is None:
            self._load_default_config()

        if self._owns_root:
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            self.root.mainloop()

    # ----------------------------------------------------------------
    # 样式
    # ----------------------------------------------------------------

    def _apply_style(self):
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure("Title.TLabel", font=("Microsoft YaHei", 11, "bold"))
        self.style.configure("Section.TLabel", font=("Microsoft YaHei", 10, "bold"))
        self.style.configure("OK.TLabel", foreground="#27ae60",
                             font=("Microsoft YaHei", 9, "bold"))
        self.style.configure("Fail.TLabel", foreground="#e74c3c",
                             font=("Microsoft YaHei", 9, "bold"))
        self.style.configure("Info.TLabel", font=("Microsoft YaHei", 9))
        self.style.configure("Action.TButton", font=("Microsoft YaHei", 9, "bold"))

    # ----------------------------------------------------------------
    # 布局
    # ----------------------------------------------------------------

    def _build_layout(self):
        # 顶部工具栏
        self._build_toolbar()

        # 中间: 左右分栏
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 5))

        # 左侧: 图块列表
        left = ttk.Frame(paned, width=320)
        paned.add(left, weight=1)
        self._build_block_list(left)

        # 右侧: 详情 + 操作
        right = ttk.Frame(paned, width=500)
        paned.add(right, weight=2)
        self._build_detail_panel(right)

        # 底部状态栏
        self._build_status_bar()

    def _build_toolbar(self):
        """顶部工具栏"""
        bar = ttk.Frame(self.root)
        bar.pack(fill=tk.X, padx=8, pady=(6, 2))

        # AutoCAD 连接
        ttk.Button(bar, text="连接 AutoCAD", command=self._connect_acad).pack(
            side=tk.LEFT, padx=2
        )
        self.acad_status = tk.StringVar(value="● 未连接")
        ttk.Label(bar, textvariable=self.acad_status,
                  style="Fail.TLabel").pack(side=tk.LEFT, padx=(4, 16))

        ttk.Separator(bar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=8
        )

        # 批量操作
        ttk.Button(bar, text="一键生成图块库",
                   command=self._generate_all, style="Action.TButton").pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(bar, text="验证图块库",
                   command=self._validate).pack(side=tk.LEFT, padx=2)

        ttk.Separator(bar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=8
        )

        # 文件路径
        self.lib_path_var = tk.StringVar(
            value=os.path.join(PROJECT_ROOT, "blocks", "block_library.dwg")
        )
        self.title_path_var = tk.StringVar(
            value=os.path.join(PROJECT_ROOT, "blocks", "title_block.dwg")
        )

        ttk.Label(bar, text="图块库:").pack(side=tk.LEFT)
        ttk.Entry(bar, textvariable=self.lib_path_var, width=30).pack(
            side=tk.LEFT, padx=2, fill=tk.X, expand=True
        )
        ttk.Button(bar, text="...", width=3,
                   command=self._browse_lib_path).pack(side=tk.LEFT)

    def _build_block_list(self, parent):
        """左侧: 图块列表"""
        lbl = ttk.Label(parent, text="标准回路图块", style="Section.TLabel")
        lbl.pack(anchor=tk.W, padx=8, pady=(8, 4))

        # Treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("desc", "threshold"),
            show="headings",
            yscrollcommand=scroll.set,
            selectmode="browse",
        )
        scroll.config(command=self.tree.yview)

        self.tree.heading("desc", text="图块名称 / 描述")
        self.tree.heading("threshold", text="断路器阈值")
        self.tree.column("desc", width=200, minwidth=120)
        self.tree.column("threshold", width=100, minwidth=60)

        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 填充列表
        for bdef in STANDARD_BLOCKS:
            if "breaker_max_current" in bdef:
                threshold = f"≤{bdef['breaker_max_current']}A"
            else:
                threshold = f">{bdef.get('breaker_min_current', 400) - 1}A"
            self.tree.insert("", tk.END,
                             iid=bdef["name"],
                             values=(bdef["desc"], threshold))

        # 分隔: 标题栏图块
        self.tree.insert("", tk.END, iid="_sep",
                         values=("── 标题栏 ──", ""))
        self.tree.insert("", tk.END, iid="A1",
                         values=("A1 图框 (841×594)", "A1 幅面"))
        self.tree.insert("", tk.END, iid="A2",
                         values=("A2 图框 (594×420)", "A2 幅面"))

        # 选中事件
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 默认选中第一个
        self.tree.selection_set(STANDARD_BLOCKS[0]["name"])
        self.tree.focus(STANDARD_BLOCKS[0]["name"])

    def _build_detail_panel(self, parent):
        """右侧: 详情面板"""
        # 上半: 图块信息
        info_frame = ttk.LabelFrame(parent, text="图块信息")
        info_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        self.detail_name_var = tk.StringVar()
        self.detail_desc_var = tk.StringVar()
        self.detail_threshold_var = tk.StringVar()

        row = 0
        for label, var in [
            ("图块名称:", self.detail_name_var),
            ("描    述:", self.detail_desc_var),
            ("断路器阈值:", self.detail_threshold_var),
        ]:
            ttk.Label(info_frame, text=label,
                      font=("Microsoft YaHei", 9, "bold")).grid(
                row=row, column=0, sticky=tk.W, padx=10, pady=2
            )
            ttk.Label(info_frame, textvariable=var).grid(
                row=row, column=1, sticky=tk.W, padx=10, pady=2
            )
            row += 1

        # 中间: 说明 (v2.0 图块不含属性)
        note_frame = ttk.LabelFrame(parent, text="说明")
        note_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(note_frame,
                  text="v2.0: 回路图块不含属性定义 (ATTDEF)。\n"
                       "所有元器件参数在图块下方的表格中展示。\n"
                       "用户可通过 AutoCAD 块编辑器 (BEDIT) 自定义图块几何图形。",
                  font=("Microsoft YaHei", 9), wraplength=500,
                  justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=8)

        # 操作按钮
        btn_frame = ttk.LabelFrame(parent, text="操作")
        btn_frame.pack(fill=tk.X, padx=8, pady=(4, 8))

        btn_row1 = ttk.Frame(btn_frame)
        btn_row1.pack(fill=tk.X, padx=10, pady=6)

        ttk.Button(btn_row1, text="创建此图块",
                   command=self._create_selected).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row1, text="重建此图块",
                   command=self._recreate_selected).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row1, text="在 AutoCAD 中编辑 (BEDIT)",
                   command=self._edit_in_acad).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row1, text="删除此图块",
                   command=self._delete_selected).pack(side=tk.LEFT, padx=3)

        btn_row2 = ttk.Frame(btn_frame)
        btn_row2.pack(fill=tk.X, padx=10, pady=(0, 6))

        ttk.Button(btn_row2, text="保存图块库 DWG",
                   command=self._save_library).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row2, text="清空所有图块",
                   command=self._purge_all).pack(side=tk.LEFT, padx=3)

        # 几何参数参考
        param_frame = ttk.LabelFrame(parent, text="几何参数参考 (mm)")
        param_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        p = BlockParams
        param_text = (
            f"连接线: {p.STUB_LEN}mm | 电缆段: {p.CABLE_LEN}mm | "
            f"断路器: {p.BRK_W}x{p.BRK_H}mm | "
            f"负载端: {p.LOAD_W}x{p.LOAD_H}mm | "
            f"间距: {p.GAP}mm | 文字: {p.TEXT_H}mm ({p.TEXT_FONT})"
        )
        ttk.Label(param_frame, text=param_text,
                  font=("Microsoft YaHei", 8), wraplength=600).pack(
            anchor=tk.W, padx=10, pady=6
        )

    def _build_status_bar(self):
        """底部状态栏"""
        bar = ttk.Frame(self.root)
        bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=(0, 3))

        self.status_var = tk.StringVar(value="就绪 — 请先连接 AutoCAD")
        ttk.Label(bar, textvariable=self.status_var,
                  style="Info.TLabel").pack(side=tk.LEFT)

    # ----------------------------------------------------------------
    # 事件处理
    # ----------------------------------------------------------------

    def _on_tree_select(self, event):
        """图块列表选中变化"""
        sel = self.tree.selection()
        if not sel:
            return
        name = sel[0]

        if name == "_sep":
            return

        if name in ("A1", "A2"):
            size_info = {"A1": "A1 图框 (841×594mm)", "A2": "A2 图框 (594×420mm)"}
            self.detail_name_var.set(name)
            self.detail_desc_var.set(size_info.get(name, "标题栏图块"))
            self.detail_threshold_var.set("—")
            return

        # 标准图块
        bdef = None
        for b in STANDARD_BLOCKS:
            if b["name"] == name:
                bdef = b
                break

        if bdef is None:
            return

        self.detail_name_var.set(bdef["name"])
        self.detail_desc_var.set(bdef["desc"])
        if "breaker_max_current" in bdef:
            self.detail_threshold_var.set(f"≤{bdef['breaker_max_current']}A")
        else:
            self.detail_threshold_var.set(f">{bdef.get('breaker_min_current', 400) - 1}A")

    # ----------------------------------------------------------------
    # AutoCAD 连接
    # ----------------------------------------------------------------

    def _connect_acad(self):
        """连接 AutoCAD (在主线程执行，COM STA 要求同线程操作)"""
        self.status_var.set("正在连接 AutoCAD...")
        self.root.update_idletasks()

        try:
            acad_cfg = AcadConfig()
            if self.cfg:
                acad_cfg = self.cfg.autocad
            self.editor.connect(acad_cfg)
            self._acad_connected = True
            self._on_acad_connected()
        except AcadConnectionError as e:
            self._on_acad_error(str(e))

    def _on_acad_connected(self):
        self.acad_status.set("● 已连接")
        # 更新标签样式
        for widget in self.root.winfo_children():
            pass  # 简单方式: 直接更新
        self.status_var.set("AutoCAD 已连接 — 可以开始操作")
        # 尝试刷新样式 (通过重建标签)
        self._refresh_acad_label()

    def _on_acad_error(self, msg):
        self._acad_connected = False
        self._refresh_acad_label()
        self.status_var.set(f"连接失败: {msg}")
        messagebox.showerror("AutoCAD 连接失败",
                             f"{msg}\n\n请确保 AutoCAD 已启动。")

    def _refresh_acad_label(self):
        """刷新 AutoCAD 连接状态标签"""
        # 找到工具栏中的状态标签并更新
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Label) and hasattr(sub, 'cget'):
                        try:
                            tv = sub.cget('textvariable')
                            if tv and 'autocad' in str(tv).lower():
                                pass
                        except Exception:
                            pass

        # 简单处理: 直接设置 StringVar 即可触发更新
        if self._acad_connected:
            self.acad_status.set("● 已连接")
        else:
            self.acad_status.set("● 未连接")

    # ----------------------------------------------------------------
    # 图块操作
    # ----------------------------------------------------------------

    def _check_acad(self) -> bool:
        """检查 AutoCAD 是否已连接且 COM 引用有效"""
        if not self._acad_connected:
            messagebox.showwarning("提示", "请先连接 AutoCAD")
            return False

        # 验证 COM 引用是否仍然有效
        if self.editor.app is not None:
            try:
                _ = self.editor.app.Name
            except Exception:
                # COM 引用失效，尝试重连
                self.status_var.set("COM 连接已失效，正在重新连接...")
                self.root.update_idletasks()
                try:
                    self.editor.reconnect()
                    self.status_var.set("已重新连接 AutoCAD")
                except Exception as e:
                    self._acad_connected = False
                    self._refresh_acad_label()
                    messagebox.showerror(
                        "AutoCAD 连接断开",
                        f"COM 连接已失效，请重新点击「连接 AutoCAD」。\n\n原因: {e}"
                    )
                    return False

        return True

    def _get_selected_block(self) -> str:
        """获取当前选中的图块名"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个图块")
            return ""
        name = sel[0]
        if name == "_sep":
            return ""
        return name

    def _create_selected(self):
        """创建选中的图块"""
        if not self._check_acad():
            return
        name = self._get_selected_block()
        if not name:
            return

        self.status_var.set(f"正在创建图块: {name}...")
        self.root.update_idletasks()

        try:
            # 确保有活动文档
            try:
                self.editor.doc = self.editor.app.ActiveDocument
            except Exception:
                self.editor.create_library_doc()

            if name in ("A1", "A2"):
                ok = self.editor.create_title_block()
            else:
                ok = self.editor.create_single_block(name)

            if ok:
                self.status_var.set(f"图块 {name} 创建成功")
                messagebox.showinfo("成功", f"图块 {name} 已创建")
            else:
                self.status_var.set(f"图块 {name} 创建失败")
                messagebox.showerror("失败", f"图块 {name} 创建失败，请查看日志")

        except Exception as e:
            self.status_var.set(f"创建失败: {e}")
            messagebox.showerror("错误", str(e))

    def _recreate_selected(self):
        """重建选中的图块 (先删除再创建)"""
        if not self._check_acad():
            return
        name = self._get_selected_block()
        if not name:
            return

        if not messagebox.askyesno(
            "确认重建",
            f"将删除并重新创建图块 {name}。\n"
            f"如果有手动修改将丢失，是否继续？"
        ):
            return

        self.status_var.set(f"正在重建图块: {name}...")
        self.root.update_idletasks()

        try:
            self.editor.doc = self.editor.app.ActiveDocument
            # 先删除
            self.editor._purge_block(name)
            # 再创建
            if name in ("A1", "A2"):
                ok = self.editor.create_title_block()
            else:
                ok = self.editor.create_single_block(name)

            if ok:
                self.status_var.set(f"图块 {name} 重建成功")
                messagebox.showinfo("成功", f"图块 {name} 已重建")
            else:
                self.status_var.set(f"图块 {name} 重建失败")

        except Exception as e:
            self.status_var.set(f"重建失败: {e}")
            messagebox.showerror("错误", str(e))

    def _edit_in_acad(self):
        """在 AutoCAD 块编辑器中打开选中的图块"""
        if not self._check_acad():
            return
        name = self._get_selected_block()
        if not name:
            return

        try:
            self.editor.doc = self.editor.app.ActiveDocument
            ok = self.editor.edit_block(name)
            if ok:
                self.status_var.set(
                    f"已在 AutoCAD 中打开块编辑器: {name} — "
                    f"编辑完成后在 AutoCAD 中点击「关闭块编辑器」并保存"
                )
            else:
                self.status_var.set(f"无法打开块编辑器: {name}")
                messagebox.showwarning(
                    "提示",
                    f"图块 {name} 在当前文档中不存在。\n"
                    f"请先创建该图块。"
                )
        except Exception as e:
            self.status_var.set(f"打开块编辑器失败: {e}")
            messagebox.showerror("错误", str(e))

    def _delete_selected(self):
        """删除选中的图块"""
        if not self._check_acad():
            return
        name = self._get_selected_block()
        if not name:
            return

        if not messagebox.askyesno("确认删除", f"确定要删除图块 {name} 吗？"):
            return

        try:
            self.editor.doc = self.editor.app.ActiveDocument
            ok = self.editor._purge_block(name)
            if ok:
                self.status_var.set(f"图块 {name} 已删除")
            else:
                self.status_var.set(f"图块 {name} 不存在或已删除")
        except Exception as e:
            self.status_var.set(f"删除失败: {e}")

    def _purge_all(self):
        """清空所有标准图块"""
        if not self._check_acad():
            return

        if not messagebox.askyesno(
            "确认清空",
            "将删除当前文档中所有标准回路图块和标题栏图块。\n"
            "如有手动修改将丢失，是否继续？"
        ):
            return

        try:
            self.editor.doc = self.editor.app.ActiveDocument
            count = self.editor.purge_blocks()
            self.status_var.set(f"已清理 {count} 个图块")
            messagebox.showinfo("完成", f"已清理 {count} 个图块")
        except Exception as e:
            self.status_var.set(f"清理失败: {e}")
            messagebox.showerror("错误", str(e))

    # ----------------------------------------------------------------
    # 批量操作
    # ----------------------------------------------------------------

    def _generate_all(self):
        """一键生成完整图块库"""
        if not self._check_acad():
            return

        lib_path = self.lib_path_var.get().strip()
        title_path = self.title_path_var.get().strip()

        if not lib_path or not title_path:
            messagebox.showwarning("提示", "请设置图块库和标题栏的保存路径")
            return

        if not messagebox.askyesno(
            "确认生成",
            f"将生成完整图块库:\n\n"
            f"• 2 种标准回路图块 (LOOP_POWER_A / LOOP_POWER_B)\n"
            f"• 1 个标题栏图块\n\n"
            f"保存到:\n"
            f"  {lib_path}\n"
            f"  {title_path}\n\n"
            f"是否继续？"
        ):
            return

        self.status_var.set("正在生成图块库...")
        self.root.update_idletasks()

        try:
            result = self.editor.generate_full_library(lib_path, title_path)
            self._on_generate_done(result)
        except Exception as e:
            self._on_generate_error(str(e))

    def _on_generate_done(self, result):
        if result["ok"]:
            self.status_var.set(
                f"图块库生成成功: 标准图块 {result['blocks_ok']}/2, "
                f"标题栏 {'成功' if result['title_ok'] else '失败'}"
            )
            messagebox.showinfo(
                "生成完成",
                f"图块库生成成功!\n\n"
                f"标准图块: {result['blocks_ok']}/{result['blocks_ok'] + result['blocks_fail']}\n"
                f"标题栏: {'成功' if result['title_ok'] else '失败'}\n\n"
                f"文件:\n"
                f"  {result['library_path']}\n"
                f"  {result['title_path']}",
            )
        else:
            self.status_var.set(
                f"图块库生成完成 (有问题): "
                f"标准图块 {result['blocks_ok']}, "
                f"失败 {result['blocks_fail']}"
            )
            messagebox.showwarning(
                "生成完成 (有问题)",
                f"标准图块: 成功 {result['blocks_ok']}, "
                f"失败 {result['blocks_fail']}\n"
                f"标题栏: {'成功' if result['title_ok'] else '失败'}\n\n"
                f"请查看日志了解失败原因。",
            )

    def _on_generate_error(self, msg):
        self.status_var.set(f"生成失败: {msg}")
        messagebox.showerror("生成失败", msg)

    def _validate(self):
        """验证图块库"""
        if not self._check_acad():
            return

        self.status_var.set("正在验证图块库...")
        self.root.update_idletasks()

        try:
            self.editor.doc = self.editor.app.ActiveDocument
            result = self.editor.validate_library()

            # 构建报告
            lines = []
            ok_count = 0
            for bdef in STANDARD_BLOCKS:
                name = bdef["name"]
                info = result["blocks"].get(name, {})
                if info.get("exists"):
                    ok_count += 1
                    lines.append(f"  ✓ {name}")
                else:
                    lines.append(f"  ✗ {name} (不存在)")

            title_status = "✓" if result["title_blocks"]["A1"] else "✗"
            lines.append(f"\n  {title_status} A1 (标题栏)")
            title_status = "✓" if result["title_blocks"]["A2"] else "✗"
            lines.append(f"  {title_status} A2 (标题栏)")

            overall = "通过" if result["ok"] and result["title_blocks"]["A1"] and result["title_blocks"]["A2"] else "有问题"

            msg = (
                f"验证结果: {overall}\n\n"
                f"标准图块: {ok_count}/{len(STANDARD_BLOCKS)} 存在\n"
                f"标题栏 A1: {'存在' if result['title_blocks']['A1'] else '不存在'}\n"
                f"标题栏 A2: {'存在' if result['title_blocks']['A2'] else '不存在'}\n\n"
                + "\n".join(lines)
            )

            self.status_var.set(
                f"验证完成: {ok_count}/{len(STANDARD_BLOCKS)} 存在"
            )

            if result["ok"] and result["title_blocks"]["A1"] and result["title_blocks"]["A2"]:
                messagebox.showinfo("验证结果", msg)
            else:
                messagebox.showwarning("验证结果", msg)

        except Exception as e:
            self.status_var.set(f"验证失败: {e}")
            messagebox.showerror("错误", str(e))

    # ----------------------------------------------------------------
    # 文件操作
    # ----------------------------------------------------------------

    def _save_library(self):
        """保存当前文档为图块库 DWG"""
        if not self._check_acad():
            return

        path = self.lib_path_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请设置保存路径")
            return

        try:
            self.editor.doc = self.editor.app.ActiveDocument
            ok = self.editor.save_library(path)
            if ok:
                self.status_var.set(f"图块库已保存: {path}")
                messagebox.showinfo("保存成功", f"图块库已保存到:\n{path}")
            else:
                self.status_var.set("保存失败")
                messagebox.showerror("保存失败", "保存失败，请查看日志")
        except Exception as e:
            self.status_var.set(f"保存失败: {e}")
            messagebox.showerror("错误", str(e))

    def _browse_lib_path(self):
        """浏览图块库保存路径"""
        path = filedialog.asksaveasfilename(
            title="选择图块库保存路径",
            filetypes=[("AutoCAD DWG", "*.dwg"), ("所有文件", "*.*")],
            defaultextension=".dwg",
            initialfile="block_library.dwg",
            initialdir=os.path.join(PROJECT_ROOT, "blocks"),
        )
        if path:
            self.lib_path_var.set(path)

    # ----------------------------------------------------------------
    # 配置
    # ----------------------------------------------------------------

    def _load_default_config(self):
        """加载默认配置"""
        config_path = os.path.join(PROJECT_ROOT, "config.yaml")
        if os.path.isfile(config_path):
            try:
                self.cfg = load_config(config_path)
                # 更新路径
                lib_abs = os.path.abspath(
                    os.path.join(PROJECT_ROOT, self.cfg.block_library.path)
                )
                title_abs = os.path.abspath(
                    os.path.join(PROJECT_ROOT, self.cfg.block_library.title_block_path)
                )
                self.lib_path_var.set(lib_abs)
                self.title_path_var.set(title_abs)
            except Exception:
                pass

    # ----------------------------------------------------------------
    # 关闭
    # ----------------------------------------------------------------

    def _on_close(self):
        """关闭窗口"""
        self.editor.close()
        self.root.destroy()


# ================================================================
# 入口
# ================================================================

def launch_block_editor(parent=None, cfg=None):
    """启动图块编辑器

    Args:
        parent: 父窗口 (为 None 时创建独立窗口)
        cfg: AppConfig 配置
    """
    # 设置 DPI 感知
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    return BlockEditorWindow(parent=parent, cfg=cfg)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    launch_block_editor()
