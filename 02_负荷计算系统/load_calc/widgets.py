# -*- coding: utf-8 -*-
"""自定义UI组件"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class CardFrame(ttk.Frame):
    """卡片式容器"""
    def __init__(self, master, title: str = "", padding: int = 10, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(padding=padding)
        self.title = title
        self._create_widgets()

    def _create_widgets(self):
        if self.title:
            header = ttk.Label(self, text=self.title,
                               font=("微软雅黑", 11, "bold"),
                               foreground="#1565C0")
            header.pack(anchor="w", pady=(0, 8))
        # padding separator
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(0, 8))


class InfoRow(ttk.Frame):
    """信息行：标签 + 值"""
    def __init__(self, master, label: str, value: str = "",
                 label_width: int = 16, value_color: str = None, **kwargs):
        super().__init__(master, **kwargs)
        self.label_w = ttk.Label(self, text=label,
                                 font=("微软雅黑", 10),
                                 width=label_width, anchor="w")
        self.label_w.pack(side="left", padx=(0, 5))

        self.value_w = ttk.Label(self, text=value,
                                 font=("微软雅黑", 10, "bold"),
                                 foreground=value_color or "#333333")
        self.value_w.pack(side="left")
        self.pack(fill="x", pady=2)

    def set_value(self, text: str, color: str = None):
        self.value_w.configure(text=text)
        if color:
            self.value_w.configure(foreground=color)


class StatusBar(ttk.Frame):
    """状态栏"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.label = ttk.Label(self, text="就绪",
                               font=("微软雅黑", 9),
                               relief="sunken", anchor="w",
                               padding=(5, 2))
        self.label.pack(fill="x", expand=True)

    def set_text(self, text: str):
        self.label.configure(text=text)


class DataTable(ttk.Frame):
    """数据显示表格"""
    def __init__(self, master, columns: list, **kwargs):
        super().__init__(master, **kwargs)
        self.columns = columns
        self._create_tree()

    def _create_tree(self):
        # 使用Treeview作为表格
        self.tree = ttk.Treeview(
            self, columns=self.columns,
            show="headings", height=12,
            selectmode="browse"
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center", minwidth=80)

        # 滚动条
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def add_row(self, values: tuple, tags: str = ""):
        self.tree.insert("", "end", values=values, tags=(tags,) if tags else ())

    def get_selected(self) -> Optional[dict]:
        sel = self.tree.selection()
        if not sel:
            return None
        item = self.tree.item(sel[0])
        return dict(zip(self.columns, item["values"]))


class MetricCard(ttk.Frame):
    """指标卡片"""
    def __init__(self, master, title: str, value: str = "",
                 unit: str = "", color: str = "#2196F3",
                 width: int = 180, height: int = 100, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(width=width, height=height)
        self.pack_propagate(False)

        # 创建画布绘制背景
        canvas = tk.Canvas(self, width=width, height=height,
                          bg="white", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # 顶部分隔线
        canvas.create_rectangle(0, 0, width, 4, fill=color, outline="")

        # 标题
        canvas.create_text(width//2, 28, text=title,
                          font=("微软雅黑", 9),
                          fill="#666666")

        # 数值
        canvas.create_text(width//2 - 20, 62, text=value,
                          font=("微软雅黑", 18, "bold"),
                          fill=color, anchor="e")

        # 单位
        if unit:
            canvas.create_text(width//2 + 5, 62, text=unit,
                              font=("微软雅黑", 10),
                              fill="#999999", anchor="w")

        self.canvas = canvas

    def update_value(self, value: str, color: str = None):
        self.canvas.itemconfig(2, text=value)
        if color:
            self.canvas.itemconfig(2, fill=color)


class ScrollableFrame(ttk.Frame):
    """可垂直滚动的容器 - 支持鼠标滚轮和中键拖动"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self._win_id = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮 — 绑定到Canvas自身而非全局，避免多实例和长时间运行后冲突
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        # 中键拖动
        self.canvas.bind("<ButtonPress-2>", self._start_drag)
        self.canvas.bind("<B2-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-2>", self._end_drag)
        self.inner.bind("<ButtonPress-2>", self._start_drag)
        self.inner.bind("<B2-Motion>", self._on_drag)
        self.inner.bind("<ButtonRelease-2>", self._end_drag)

        self._drag_start_y = 0
        self._is_dragging = False

    def _on_inner_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # 设置内层框架宽度与Canvas一致
        self.canvas.itemconfig(self._win_id, width=event.width)
        # 若内容高度小于可见区域，则拉伸内框填满Canvas，以支持expand=True的子组件
        inner_h = self.inner.winfo_reqheight()
        if inner_h < event.height and inner_h > 0:
            self.canvas.itemconfig(self._win_id, height=event.height)

    def _bind_mousewheel(self, event):
        """进入Canvas区域时绑定滚轮到Canvas自身，避免全局绑定冲突"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        """离开Canvas区域时解绑滚轮"""
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _start_drag(self, event):
        self._drag_start_y = event.y_root
        self._is_dragging = False
        # 改变光标
        self.canvas.configure(cursor="fleur")

    def _on_drag(self, event):
        dy = self._drag_start_y - event.y_root
        if abs(dy) > 3:
            self._is_dragging = True
        if self._is_dragging:
            self.canvas.yview_scroll(int(dy / 2), "units")
            self._drag_start_y = event.y_root

    def _end_drag(self, event):
        self._is_dragging = False
        self.canvas.configure(cursor="")


class SidebarButton(ttk.Frame):
    """侧边栏导航按钮"""
    def __init__(self, master, text: str, icon: str = "",
                 command: Callable = None, **kwargs):
        super().__init__(master, cursor="hand2", **kwargs)
        self.command = command

        self.label = ttk.Label(self, text=f"  {icon}  {text}" if icon else f"  {text}",
                               font=("微软雅黑", 11),
                               foreground="white", background="#1a237e",
                               padding=(15, 10))
        self.label.pack(fill="x")
        self.label.bind("<Button-1>", self._on_click)
        self.bind("<Button-1>", self._on_click)

        # hover效果
        self.label.bind("<Enter>", lambda e: self.label.configure(background="#283593"))
        self.label.bind("<Leave>", lambda e: self.label.configure(background="#1a237e"))

    def _on_click(self, event):
        if self.command:
            self.command()
