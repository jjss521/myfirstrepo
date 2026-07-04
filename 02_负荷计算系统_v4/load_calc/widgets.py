# -*- coding: utf-8 -*-
"""自定义UI组件 - Apple 简约素雅高级风格"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .config import THEME, blend_color, FONT_UI, FONT_DISPLAY, FS


class CardFrame(tk.Frame):
    """卡片式容器 - Apple 白色面板"""
    def __init__(self, master, title: str = "", padding: int = 12, **kwargs):
        super().__init__(master, bg=THEME["BG_CARD"],
                         highlightbackground=THEME["BORDER"],
                         highlightthickness=1, **kwargs)
        self.title = title
        self._padding = padding
        self._create_widgets()

    def _create_widgets(self):
        p = self._padding
        if self.title:
            # 标题行：左侧细竖线 + 蓝色标题
            header_frame = tk.Frame(self, bg=THEME["BG_CARD"])
            header_frame.pack(fill="x", padx=p, pady=(p, 0))

            # 细竖线装饰
            accent = tk.Frame(header_frame, bg=THEME["ACCENT_BLUE"], width=3, height=14)
            accent.pack(side="left", padx=(0, 8))

            tk.Label(header_frame, text=self.title,
                     font=(FONT_UI, FS[11], "bold"),
                     fg=THEME["FG_PRIMARY"], bg=THEME["BG_CARD"]).pack(side="left")

        # 分隔线
        sep = tk.Frame(self, bg=THEME["SEPARATOR"], height=1)
        sep.pack(fill="x", padx=p, pady=(8, 8))


class InfoRow(tk.Frame):
    """信息行：标签 + 值"""
    def __init__(self, master, label: str, value: str = "",
                 label_width: int = 16, value_color: str = None, **kwargs):
        super().__init__(master, bg=THEME["BG_CARD"], **kwargs)
        self.label_w = tk.Label(self, text=label,
                                font=(FONT_UI, FS[10]),
                                fg=THEME["FG_SECONDARY"], bg=THEME["BG_CARD"],
                                width=label_width, anchor="w")
        self.label_w.pack(side="left", padx=(0, 5))

        self.value_w = tk.Label(self, text=value,
                                font=(FONT_UI, FS[10], "bold"),
                                fg=value_color or THEME["FG_PRIMARY"],
                                bg=THEME["BG_CARD"])
        self.value_w.pack(side="left")
        self.pack(fill="x", pady=2)

    def set_value(self, text: str, color: str = None):
        self.value_w.configure(text=text)
        if color:
            self.value_w.configure(fg=color)


class StatusBar(tk.Frame):
    """状态栏 - Apple 浅色底部"""
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=THEME["BG_DARK"], **kwargs)
        # 顶部分隔线
        sep = tk.Frame(self, bg=THEME["SEPARATOR"], height=1)
        sep.pack(fill="x")

        self.label = tk.Label(self, text="就绪",
                              font=(FONT_UI, FS[9]),
                              fg=THEME["FG_SECONDARY"], bg=THEME["BG_DARK"],
                              anchor="w", padx=10, pady=4)
        self.label.pack(fill="x", expand=True)

    def set_text(self, text: str):
        self.label.configure(text=text)


class DataTable(tk.Frame):
    """数据显示表格 - 深色主题"""
    def __init__(self, master, columns: list, **kwargs):
        super().__init__(master, bg=THEME["BG_CARD"], **kwargs)
        self.columns = columns
        self._create_tree()

    def _create_tree(self):
        self.tree = ttk.Treeview(
            self, columns=self.columns,
            show="headings", height=12,
            selectmode="browse"
        )
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center", minwidth=80)

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


class MetricCard(tk.Frame):
    """指标卡片 - Apple 简约白色 + 顶部细色条"""
    def __init__(self, master, title: str, value: str = "",
                 unit: str = "", color: str = None,
                 width: int = 180, height: int = 100, **kwargs):
        super().__init__(master, bg=THEME["BG_CARD"],
                         highlightbackground=THEME["BORDER"],
                         highlightthickness=1, **kwargs)
        self.configure(width=width, height=height)
        self.pack_propagate(False)

        if color is None:
            color = THEME["ACCENT_BLUE"]

        self._color = color
        self._unit = unit
        self._width = width
        self._height = height

        # 顶部细色条
        accent_bar = tk.Frame(self, bg=color, height=3, width=width)
        accent_bar.pack(fill="x")

        # 标题
        tk.Label(self, text=title,
                 font=(FONT_UI, FS[9]),
                 fg=THEME["FG_SECONDARY"], bg=THEME["BG_CARD"]).pack(pady=(10, 0))

        # 数值
        display = f"{value}{' ' + unit if unit else ''}"
        self.value_label = tk.Label(self, text=display,
                                    font=(FONT_UI, FS[16], "bold"),
                                    fg=THEME["FG_PRIMARY"], bg=THEME["BG_CARD"])
        self.value_label.pack(pady=(2, 0))

    def update_value(self, value: str, color: str = None):
        display = f"{value}{' ' + self._unit if self._unit else ''}"
        self.value_label.configure(text=display)
        if color:
            self.value_label.configure(fg=color)


class ScrollableFrame(tk.Frame):
    """可垂直滚动的容器 - Apple 浅色主题"""
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=THEME["BG_MAIN"], **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0,
                                bg=THEME["BG_MAIN"])
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=THEME["BG_MAIN"])

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self._win_id = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮
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
        self.canvas.itemconfig(self._win_id, width=event.width)
        inner_h = self.inner.winfo_reqheight()
        if inner_h < event.height and inner_h > 0:
            self.canvas.itemconfig(self._win_id, height=event.height)

    def _bind_mousewheel(self, event):
        """进入Canvas区域时绑定滚轮（仅绑定到Canvas，避免全局冲突）"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        """离开Canvas区域时解绑滚轮"""
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _start_drag(self, event):
        self._drag_start_y = event.y_root
        self._is_dragging = False
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


class SidebarButton(tk.Frame):
    """侧边栏导航按钮 - Apple 浅色主题"""
    def __init__(self, master, text: str, icon: str = "",
                 command: Callable = None, **kwargs):
        super().__init__(master, cursor="hand2", bg=THEME["BG_CARD"], **kwargs)
        self.command = command

        display_text = f"  {icon}  {text}" if icon else f"  {text}"
        self.label = tk.Label(self, text=display_text,
                              font=(FONT_UI, FS[11]),
                              fg=THEME["FG_PRIMARY"], bg=THEME["BG_CARD"],
                              padx=15, pady=10)
        self.label.pack(fill="x")
        self.label.bind("<Button-1>", self._on_click)
        self.bind("<Button-1>", self._on_click)

        # hover效果
        hover_bg = blend_color(THEME["ACCENT_BLUE"], THEME["BG_CARD"], 0.08)
        self.label.bind("<Enter>", lambda e: self.label.configure(bg=hover_bg))
        self.label.bind("<Leave>", lambda e: self.label.configure(bg=THEME["BG_CARD"]))

    def _on_click(self, event):
        if self.command:
            self.command()
