#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS Sonoma-style customtkinter GUI for 市政工程电气自控设计说明书生成器.

Replaces the ttkbootstrap GUI with a modern, sidebar-navigated desktop app.
All UI code lives in this single file — zero backend changes required.

Launch:  python src/macos_gui.py
"""

import os
import sys
import json
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

# ── Path setup (mirrors main.py) ───────────────────────────────────────────
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Allow importing backend modules (for DocxGenerator preview)
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, 'backend')
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import customtkinter as ctk

from core.engine import GenerateEngine

# ── Optional: tkinterdnd2 for drag-drop ────────────────────────────────────
_TKINTERDND2_AVAILABLE = False
try:
    from tkinterdnd2 import DND_FILES  # noqa: F401
    _TKINTERDND2_AVAILABLE = True
except ImportError:
    pass

# ── Backend imports for preview ────────────────────────────────────────────
_DOCX_PREVIEW_AVAILABLE = False
DocxGenerator = None  # type: ignore[assignment]
try:
    from app.services.docx_generator import DocxGenerator  # noqa: F811
    _DOCX_PREVIEW_AVAILABLE = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════════════════
# 1. DESIGN SYSTEM CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

COLORS: Dict[str, str] = {
    "bg_primary":    "#F5F5F7",
    "bg_sidebar":    "#E8E8ED",
    "bg_card":       "#FFFFFF",
    "bg_hover":      "#E8E8ED",
    "bg_selected":   "#D2D2D7",
    "accent_blue":   "#007AFF",
    "accent_green":  "#34C759",
    "accent_orange": "#FF9500",
    "accent_red":    "#FF3B30",
    "text_primary":  "#1D1D1F",
    "text_secondary":"#86868B",
    "text_tertiary": "#C7C7CC",
    "separator":     "#D2D2D7",
}

FONTS: Dict[str, Dict[str, Any]] = {
    "header":       {"family": "微软雅黑", "size": 20, "weight": "bold"},
    "section":      {"family": "微软雅黑", "size": 15, "weight": "bold"},
    "body":         {"family": "微软雅黑", "size": 13},
    "caption":      {"family": "微软雅黑", "size": 11},
    "mono":         {"family": "Consolas", "size": 11},
    "title":        {"family": "微软雅黑", "size": 24, "weight": "bold"},
    "sidebar_item": {"family": "微软雅黑", "size": 13},
}


def get_ctk_font(key: str) -> ctk.CTkFont:
    """Create a CTkFont from the FONTS params dict. Safe to call after CTk root exists."""
    params = dict(FONTS[key])
    return ctk.CTkFont(**params)

APP_TITLE    = "市政工程电气自控设计说明书生成器"
APP_VERSION  = "1.0.0"
PROJECT_TYPES: List[tuple] = [
    ("water_supply", "给水工程"),
    ("drainage",     "排水工程"),
    ("road",         "道路工程"),
    ("sanitation",   "环卫工程"),
]
DESIGN_STAGES  = ["可行性研究", "初步设计"]
VOLTAGE_LEVELS = ["10kV", "35kV", "0.4kV", "6kV"]
LOAD_LEVELS    = ["一级", "二级", "三级"]

DEFAULT_PARAMS: Dict[str, Any] = {
    "project_name":   "",
    "project_type":   "water_supply",
    "design_stage":   "初步设计",
    "voltage_level":  "10kV",
    "load_level":     "二级",
    "power_source":   "一路",
    "standby_desc":   "",
    "tx_config":      "",
    "tx_count":       "1",
    "tx_location":    "变配电间内",
    "project_date":   datetime.now().strftime("%Y年%m月%d日"),
}

_RECENT_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                           "电气自控生成器")
_RECENT_FILE = os.path.join(_RECENT_DIR, "recent.json")

# ═══════════════════════════════════════════════════════════════════════════
# 2. EngineContext
# ═══════════════════════════════════════════════════════════════════════════

class EngineContext:
    """Holds engine instance, current data, and cached state."""

    def __init__(self) -> None:
        project_root = os.path.dirname(_SRC_DIR)
        self.engine = GenerateEngine(project_root)
        self.excel_data: Optional[Dict[str, Any]] = None
        self.excel_path: str = ""
        self.last_output_path: str = ""
        self.project_params: Dict[str, Any] = dict(DEFAULT_PARAMS)

    def health_status(self) -> Dict[str, Any]:
        return self.engine.health_check()

    def is_healthy(self) -> bool:
        return self.engine.health_check()["all_pass"]


# ═══════════════════════════════════════════════════════════════════════════
# 3. PAGE: ProjectPage
# ═══════════════════════════════════════════════════════════════════════════

class ProjectPage(ctk.CTkFrame):
    """Card-based project info form."""

    def __init__(self, master, ctx: EngineContext, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.ctx = ctx
        self.params: Dict[str, Any] = dict(DEFAULT_PARAMS)
        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 20))
        ctk.CTkLabel(hdr, text="项目信息", font=get_ctk_font("header"),
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(hdr, text="配置工程基本参数用于文档生成",
                     font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        # Two-column card layout
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(fill="both", expand=True)

        # Left card: 基本信息
        left_card = ctk.CTkFrame(cols, fg_color=COLORS["bg_card"],
                                 corner_radius=12)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._build_left_card(left_card)

        # Right card: 电气配置
        right_card = ctk.CTkFrame(cols, fg_color=COLORS["bg_card"],
                                  corner_radius=12)
        right_card.pack(side="right", fill="both", expand=True, padx=(8, 0))
        self._build_right_card(right_card)

        # Bottom save button
        ctk.CTkButton(
            self, text="💾 保存项目信息", font=get_ctk_font("body"),
            fg_color=COLORS["accent_blue"], hover_color="#0066D6",
            corner_radius=10, height=40,
            command=self.save_params,
        ).pack(pady=(15, 0))

    def _build_left_card(self, card: ctk.CTkFrame) -> None:
        pad = {"padx": 20, "pady": (12, 4)}
        epad = {"padx": 20, "pady": (2, 15)}

        ctk.CTkLabel(card, text="基本信息", font=get_ctk_font("section"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", **pad)

        # 工程名称
        ctk.CTkLabel(card, text="工程名称 *", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        self.entry_name = ctk.CTkEntry(card, font=get_ctk_font("body"),
                                       placeholder_text="示例工程",
                                       corner_radius=8)
        self.entry_name.pack(fill="x", padx=20, pady=(0, 15))
        self.entry_name.insert(0, "示例工程")

        # 工程类型
        ctk.CTkLabel(card, text="工程类型 *", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        self.type_var = ctk.StringVar(value="给水工程")
        self.type_combo = ctk.CTkOptionMenu(
            card, values=[lbl for _, lbl in PROJECT_TYPES],
            variable=self.type_var, font=get_ctk_font("body"),
            corner_radius=8, fg_color=COLORS["bg_primary"],
            button_color=COLORS["accent_blue"],
            command=self._on_type_change,
        )
        self.type_combo.pack(fill="x", padx=20, pady=(0, 15))

        # 设计阶段
        ctk.CTkLabel(card, text="设计阶段 *", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        self.stage_var = ctk.StringVar(value="初步设计")
        ctk.CTkOptionMenu(
            card, values=DESIGN_STAGES, variable=self.stage_var,
            font=get_ctk_font("body"), corner_radius=8,
            fg_color=COLORS["bg_primary"],
            button_color=COLORS["accent_blue"],
        ).pack(fill="x", padx=20, pady=(0, 15))

        # 编制日期
        ctk.CTkLabel(card, text="编制日期", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        date_row = ctk.CTkFrame(card, fg_color="transparent")
        date_row.pack(fill="x", padx=20, pady=(0, 15))
        today_str = datetime.now().strftime("%Y年%m月%d日")
        self.date_var = ctk.StringVar(value=today_str)
        ctk.CTkEntry(date_row, textvariable=self.date_var, font=get_ctk_font("body"),
                     corner_radius=8).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(date_row, text="今天", width=60, font=get_ctk_font("caption"),
                      fg_color=COLORS["text_tertiary"],
                      hover_color=COLORS["bg_selected"],
                      text_color=COLORS["text_primary"],
                      command=lambda: self.date_var.set(today_str),
                      ).pack(side="left", padx=(8, 0))

    def _build_right_card(self, card: ctk.CTkFrame) -> None:
        pad = {"padx": 20, "pady": (12, 4)}
        epad = {"padx": 20, "pady": (2, 15)}

        ctk.CTkLabel(card, text="电气配置", font=get_ctk_font("section"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", **pad)

        # 供电电压等级
        ctk.CTkLabel(card, text="供电电压等级", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        self.voltage_var = ctk.StringVar(value="10kV")
        ctk.CTkOptionMenu(
            card, values=VOLTAGE_LEVELS, variable=self.voltage_var,
            font=get_ctk_font("body"), corner_radius=8,
            fg_color=COLORS["bg_primary"],
            button_color=COLORS["accent_blue"],
        ).pack(fill="x", padx=20, pady=(0, 15))

        # 用电负荷等级
        ctk.CTkLabel(card, text="用电负荷等级", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        self.load_var = ctk.StringVar(value="二级")
        ctk.CTkOptionMenu(
            card, values=LOAD_LEVELS, variable=self.load_var,
            font=get_ctk_font("body"), corner_radius=8,
            fg_color=COLORS["bg_primary"],
            button_color=COLORS["accent_blue"],
        ).pack(fill="x", padx=20, pady=(0, 15))

        # 电源回路数
        ctk.CTkLabel(card, text="电源回路数", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        self.ps_var = ctk.StringVar(value="一路")
        ctk.CTkSegmentedButton(
            card, values=["一路", "两路"], variable=self.ps_var,
            font=get_ctk_font("body"),
        ).pack(fill="x", padx=20, pady=(0, 15))

        # 备用电源说明
        ctk.CTkLabel(card, text="备用电源说明", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        self.standby_text = ctk.CTkTextbox(card, height=60, font=get_ctk_font("caption"),
                                           corner_radius=8,
                                           fg_color=COLORS["bg_primary"],
                                           wrap="word")
        self.standby_text.pack(fill="x", padx=20, pady=(0, 10))
        self.standby_text.insert("1.0", "当一路电源故障时，另一路可承担全部负荷。")

        # 变配电间位置
        ctk.CTkLabel(card, text="变配电间位置", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", **epad)
        self.tx_loc_var = ctk.StringVar(value="变配电间内")
        ctk.CTkEntry(card, textvariable=self.tx_loc_var, font=get_ctk_font("body"),
                     corner_radius=8).pack(fill="x", padx=20, pady=(0, 10))

    # ── Logic ──────────────────────────────────────────────────────────────

    def _on_type_change(self, value: str) -> None:
        """When project type changes, load rule and update design stage."""
        for code, lbl in PROJECT_TYPES:
            if lbl == value:
                rule = self.ctx.engine.load_rule(code)
                if rule:
                    stage = rule.get("design_stage", "初步设计")
                    self.stage_var.set(stage)
                break

    def save_params(self) -> None:
        """Persist form values into context."""
        label = self.type_var.get()
        project_type = "water_supply"
        for code, lbl in PROJECT_TYPES:
            if lbl == label:
                project_type = code
                break

        self.params.update({
            "project_name":   self.entry_name.get().strip() or "示例工程",
            "project_type":   project_type,
            "design_stage":   self.stage_var.get(),
            "voltage_level":  self.voltage_var.get(),
            "load_level":     self.load_var.get(),
            "power_source":   self.ps_var.get(),
            "standby_desc":   self.standby_text.get("1.0", "end-1c").strip(),
            "tx_location":    self.tx_loc_var.get().strip(),
            "project_date":   self.date_var.get(),
        })
        self.ctx.project_params = dict(self.params)
        messagebox.showinfo("保存成功", "项目信息已保存")

    def get_params(self) -> Dict[str, Any]:
        """Return current params dict, saving first."""
        self.save_params()
        return self.params


# ═══════════════════════════════════════════════════════════════════════════
# 4. PAGE: ExcelPage
# ═══════════════════════════════════════════════════════════════════════════

class ExcelPage(ctk.CTkFrame):
    """Excel import page with drag-drop zone and results table."""

    def __init__(self, master, ctx: EngineContext, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.ctx = ctx
        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 15))
        ctk.CTkLabel(hdr, text="导入负荷计算表", font=get_ctk_font("header"),
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(hdr, text="📂 选择文件", font=get_ctk_font("body"),
                      fg_color=COLORS["accent_blue"], corner_radius=8,
                      command=self._select_file).pack(side="right", padx=(8, 0))
        self.parse_btn = ctk.CTkButton(
            hdr, text="🔄 解析并预览", font=get_ctk_font("body"),
            fg_color=COLORS["bg_selected"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_hover"],
            corner_radius=8, command=self._parse_excel,
        )
        self.parse_btn.pack(side="right", padx=(8, 0))

        # Drag-drop zone
        self.drop_zone = ctk.CTkFrame(
            self, fg_color=COLORS["bg_primary"],
            border_width=2, border_color=COLORS["text_tertiary"],
            corner_radius=12, height=120,
        )
        self.drop_zone.pack(fill="x", pady=(0, 10))
        self.drop_zone.pack_propagate(False)

        inner = ctk.CTkFrame(self.drop_zone, fg_color="transparent")
        inner.pack(expand=True)
        drop_hint = "拖拽 Excel 文件到这里" if _TKINTERDND2_AVAILABLE else "📂 点击此区域选择 Excel 文件"
        ctk.CTkLabel(inner, text=drop_hint, font=get_ctk_font("section"),
                     text_color=COLORS["text_secondary"]).pack()
        ctk.CTkLabel(inner, text="支持 .xlsx / .xls 格式",
                     font=get_ctk_font("caption"),
                     text_color=COLORS["text_tertiary"]).pack(pady=(4, 0))

        # Make drop zone clickable
        self.drop_zone.bind("<Button-1>", lambda e: self._select_file())
        for child in inner.winfo_children():
            child.bind("<Button-1>", lambda e: self._select_file())
        inner.bind("<Button-1>", lambda e: self._select_file())

        # Hover effects for drop zone
        self.drop_zone.bind("<Enter>", lambda e: self._on_drop_enter())
        self.drop_zone.bind("<Leave>", lambda e: self._on_drop_leave())

        # File label
        self.file_label = ctk.CTkLabel(
            self, text="未选择文件", font=get_ctk_font("caption"),
            text_color=COLORS["text_secondary"],
        )
        self.file_label.pack(anchor="w", pady=(0, 10))

        # Results area (initially hidden)
        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")

    def _on_drop_enter(self) -> None:
        self.drop_zone.configure(border_color=COLORS["accent_blue"])

    def _on_drop_leave(self) -> None:
        self.drop_zone.configure(border_color=COLORS["text_tertiary"])

    # ── Logic ──────────────────────────────────────────────────────────────

    def _select_file(self) -> None:
        path = filedialog.askopenfilename(
            title="选择负荷计算Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")],
        )
        if path:
            self.ctx.excel_path = path
            self.file_label.configure(
                text=f"📄 {path}", text_color=COLORS["text_primary"])
            self.ctx.excel_data = None
            self._parse_excel()

    def _parse_excel(self) -> None:
        if not self.ctx.excel_path:
            messagebox.showwarning("提示", "请先选择Excel文件")
            return
        self.parse_btn.configure(text="⏳ 解析中...", state="disabled")
        threading.Thread(target=self._do_parse, daemon=True).start()

    def _do_parse(self) -> None:
        try:
            data = self.ctx.engine.parse_excel(self.ctx.excel_path)
            self.ctx.excel_data = data
            self.after(0, self._display_result, data)
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("解析失败", str(exc)))
            self.after(0, lambda: self.parse_btn.configure(
                text="🔄 解析并预览", state="normal"))

    def _display_result(self, data: Dict[str, Any]) -> None:
        self.parse_btn.configure(text="🔄 解析并预览", state="normal")
        summary = data.get("summary", {})

        # Hide old results
        self.results_frame.pack_forget()
        self.results_frame.destroy()
        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, pady=(10, 0))

        # ── Summary card ──
        card = ctk.CTkFrame(self.results_frame, fg_color=COLORS["bg_card"],
                            corner_radius=12)
        card.pack(fill="x", pady=(0, 12))

        stats = [
            ("设备总数",   summary.get("total_devices", 0), "台"),
            ("安装容量",   f'{summary.get("total_equip_power", 0):.1f}', "kW"),
            ("计算负荷",   f'{summary.get("total_sc_k", 0):.1f}', "kVA"),
            ("补偿容量",   f'{summary.get("qc_compensation", 0):.1f}', "kvar"),
            ("补偿前cosφ", f'{summary.get("cos_before", 0):.4f}', ""),
            ("推荐变压器", summary.get("recommended_transformer", "-"), ""),
        ]
        stat_grid = ctk.CTkFrame(card, fg_color="transparent")
        stat_grid.pack(padx=20, pady=15, fill="x")
        for i, (label, value, unit) in enumerate(stats):
            col = i % 3
            row = i // 3
            cell = ctk.CTkFrame(stat_grid, fg_color="transparent")
            cell.grid(row=row, column=col, padx=15, pady=8, sticky="w")
            display = f"{value}{unit}"
            ctk.CTkLabel(cell, text=display, font=get_ctk_font("section"),
                         text_color=COLORS["accent_blue"]).pack(anchor="w")
            ctk.CTkLabel(cell, text=label, font=get_ctk_font("caption"),
                         text_color=COLORS["text_secondary"]).pack(anchor="w")
        # Make grid columns stretch
        for c in range(3):
            stat_grid.grid_columnconfigure(c, weight=1)

        # ── Area detail table ──
        table_card = ctk.CTkFrame(self.results_frame, fg_color=COLORS["bg_card"],
                                  corner_radius=12)
        table_card.pack(fill="both", expand=True)

        ctk.CTkLabel(table_card, text="各区域负荷明细", font=get_ctk_font("section"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(15, 5))

        # Treeview for detail
        tree_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = ("area", "devices", "power", "pc", "qc", "sc")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        self.tree.heading("area", text="区域名称")
        self.tree.heading("devices", text="设备数")
        self.tree.heading("power", text="设备容量(kW)")
        self.tree.heading("pc", text="有功(kW)")
        self.tree.heading("qc", text="无功(kvar)")
        self.tree.heading("sc", text="视在(kVA)")
        self.tree.column("area", width=150)
        self.tree.column("devices", width=70, anchor="center")
        for c in ("power", "pc", "qc", "sc"):
            self.tree.column(c, width=110, anchor="e")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Populate
        for area, info in data.get("area_summaries", {}).items():
            self.tree.insert("", "end", values=(
                area,
                info.get("device_count", 0),
                f'{info.get("equip_power", 0):.1f}',
                f'{info.get("pc", 0):.1f}',
                f'{info.get("qc", 0):.1f}',
                f'{info.get("sc", 0):.1f}',
            ))
        # 合计 row
        self.tree.insert("", "end", values=(
            "合计",
            summary.get("total_devices", 0),
            f'{summary.get("total_equip_power", 0):.1f}',
            f'{summary.get("total_pc", 0):.1f}',
            f'{summary.get("total_qc", 0):.1f}',
            f'{summary.get("total_sc", 0):.1f}',
        ), tags=("summary",))
        self.tree.tag_configure("summary", font=("微软雅黑", 11, "bold"))
        self.after(0, self.tree.yview_moveto, 1.0)


# ═══════════════════════════════════════════════════════════════════════════
# 5. PAGE: GeneratePage
# ═══════════════════════════════════════════════════════════════════════════

class GeneratePage(ctk.CTkFrame):
    """Document generation page with config summary, progress, log, and preview."""

    def __init__(self, master, ctx: EngineContext, get_params_cb,
                 **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.ctx = ctx
        self.get_params_cb = get_params_cb  # callable → Dict[str, Any]
        self._preview_expanded = False
        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 15))
        ctk.CTkLabel(hdr, text="生成设计说明书", font=get_ctk_font("header"),
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(
            hdr, text="🔄 刷新配置", font=get_ctk_font("caption"),
            fg_color=COLORS["bg_selected"],
            text_color=COLORS["text_primary"],
            corner_radius=8, command=self._refresh_config,
        ).pack(side="right")

        # Three-column layout
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # ── Left: config summary ──
        left_card = ctk.CTkFrame(main, fg_color=COLORS["bg_card"],
                                 corner_radius=12, width=260)
        left_card.pack(side="left", fill="both", padx=(0, 8))
        left_card.pack_propagate(False)
        ctk.CTkLabel(left_card, text="当前配置", font=get_ctk_font("section"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(15, 5))
        self.config_text = ctk.CTkTextbox(
            left_card, font=get_ctk_font("mono"), fg_color=COLORS["bg_card"],
            corner_radius=8, wrap="word",
        )
        self.config_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.config_text.configure(state="disabled")

        # ── Center: actions + log ──
        center = ctk.CTkFrame(main, fg_color="transparent")
        center.pack(side="left", fill="both", expand=True, padx=(8, 8))

        # Action buttons
        btn_row = ctk.CTkFrame(center, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 10))
        self.gen_btn = ctk.CTkButton(
            btn_row, text="📝 生成Word文档", font=get_ctk_font("body"),
            fg_color=COLORS["accent_blue"], hover_color="#0066D6",
            corner_radius=12, height=40, command=self._generate,
        )
        self.gen_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(
            btn_row, text="📂 打开输出文件夹", font=get_ctk_font("body"),
            fg_color="transparent", border_width=1,
            border_color=COLORS["accent_blue"],
            text_color=COLORS["accent_blue"],
            corner_radius=8, command=self._open_output,
        ).pack(side="left", padx=(5, 0))

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            center, mode="indeterminate", height=6,
            fg_color=COLORS["bg_primary"],
            progress_color=COLORS["accent_blue"],
            corner_radius=3,
        )
        self.progress.pack(fill="x", pady=(0, 10))

        # Log output
        log_card = ctk.CTkFrame(center, fg_color=COLORS["bg_card"],
                                corner_radius=12)
        log_card.pack(fill="both", expand=True)
        ctk.CTkLabel(log_card, text="生成日志", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(10, 3))
        self.log_text = ctk.CTkTextbox(
            log_card, font=get_ctk_font("mono"), fg_color=COLORS["bg_card"],
            corner_radius=8, wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")

        # Output path label
        self.path_var = ctk.StringVar(value="")
        self.path_label = ctk.CTkLabel(
            center, textvariable=self.path_var,
            font=get_ctk_font("caption"), text_color=COLORS["accent_green"],
        )
        self.path_label.pack(anchor="w", pady=(5, 0))

        # ── Right: steps ──
        right_card = ctk.CTkFrame(main, fg_color=COLORS["bg_card"],
                                  corner_radius=12, width=200)
        right_card.pack(side="right", fill="both", padx=(8, 0))
        right_card.pack_propagate(False)
        ctk.CTkLabel(right_card, text="生成步骤", font=get_ctk_font("section"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(15, 10))
        steps = [
            "1️⃣ 填写项目信息",
            "2️⃣ 导入Excel",
            "3️⃣ 生成文档",
            "4️⃣ 查看输出",
        ]
        for s in steps:
            ctk.CTkLabel(right_card, text=s, font=get_ctk_font("caption"),
                         text_color=COLORS["text_secondary"]).pack(
                anchor="w", padx=15, pady=2)

        # ── Preview section (below center) ──
        self.preview_toggle = ctk.CTkButton(
            center, text="📋 实时预览  ▸", font=get_ctk_font("caption"),
            fg_color="transparent", text_color=COLORS["accent_blue"],
            hover_color=COLORS["bg_hover"], corner_radius=8,
            command=self._toggle_preview,
        )
        self.preview_toggle.pack(anchor="w", pady=(8, 2))

        self.preview_frame = ctk.CTkFrame(center, fg_color=COLORS["bg_card"],
                                          corner_radius=12, height=180)
        # Hidden by default

    # ── Preview ────────────────────────────────────────────────────────────

    def _toggle_preview(self) -> None:
        if self._preview_expanded:
            self.preview_frame.pack_forget()
            self.preview_toggle.configure(text="📋 实时预览  ▸")
            self._preview_expanded = False
        else:
            if not self.preview_frame.winfo_ismapped():
                self._build_preview_content()
                self.preview_frame.pack(fill="both", expand=True, pady=(5, 0))
            self.preview_toggle.configure(text="📋 实时预览  ▾")
            self._preview_expanded = True
            self._refresh_preview()

    def _build_preview_content(self) -> None:
        btn_row = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(btn_row, text="文档大纲预览", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(side="left")
        ctk.CTkButton(
            btn_row, text="🔄 刷新预览", font=get_ctk_font("caption"),
            fg_color=COLORS["bg_selected"],
            text_color=COLORS["text_primary"],
            corner_radius=6, width=90,
            command=self._refresh_preview,
        ).pack(side="right")

        self.preview_text = ctk.CTkTextbox(
            self.preview_frame, font=get_ctk_font("caption"),
            fg_color=COLORS["bg_card"], corner_radius=8, wrap="word",
        )
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.preview_text.configure(state="disabled")

    def _refresh_preview(self) -> None:
        if not self._preview_expanded:
            return

        if not _DOCX_PREVIEW_AVAILABLE:
            self._set_preview("预览功能需后端支持 (DocxGenerator 导入失败)")
            return

        if not self.ctx.excel_data:
            self._set_preview("请先在「Excel导入」页面解析负荷计算表")
            return

        params = self.get_params_cb()
        project_type = params.get("project_type", "water_supply")
        design_stage = params.get("design_stage", "初步设计")

        rules_dir = os.path.join(_PROJECT_ROOT, "backend", "data", "rules")
        output_dir = os.path.join(_PROJECT_ROOT, "output")

        def _task() -> None:
            try:
                from app.services.docx_generator import DocxGenerator as DG
                gen = DG(rules_dir=rules_dir, output_dir=output_dir,
                         template="standard")
                blocks = gen.preview(project_type, design_stage,
                                     self.ctx.excel_data, params)
                self.after(0, self._render_preview_blocks, blocks)
            except Exception as exc:
                self.after(0, self._set_preview, f"预览生成失败: {exc}")

        threading.Thread(target=_task, daemon=True).start()

    def _render_preview_blocks(self, blocks: list) -> None:
        lines: List[str] = []
        for blk in blocks:
            kind = blk[0]
            if kind == "cover":
                _, name, subtitle, info_list = blk
                lines.append(f"📕 {name}")
                lines.append(f"   {subtitle}")
                for line in info_list:
                    lines.append(f"   {line}")
                lines.append("")
            elif kind == "pagebreak":
                lines.append("─" * 48 + "  分页  " + "─" * 48)
            elif kind in ("h1", "h2", "h3"):
                prefix = {"h1": "# ", "h2": "## ", "h3": "### "}[kind]
                lines.append(f"{prefix}{blk[1]}")
            elif kind == "p":
                lines.append(f"  {blk[1]}")
            elif kind == "b":
                lines.append(f"  • {blk[1]}")
            elif kind == "table":
                _, _, headers, rows = blk
                lines.append(f"  [表格] {' | '.join(headers)}")
                for row in rows[:5]:
                    lines.append(f"    {' | '.join(str(c) for c in row)}")
                if len(rows) > 5:
                    lines.append(f"    ... (共 {len(rows)} 行)")
                lines.append("")
            elif kind == "sig":
                lines.append("  [签署栏] 编制 / 校核 / 审核 / 审定")
        self._set_preview("\n".join(lines))

    def _set_preview(self, text: str) -> None:
        if hasattr(self, "preview_text"):
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", text)
            self.preview_text.configure(state="disabled")

    # ── Config Refresh ─────────────────────────────────────────────────────

    def _refresh_config(self) -> None:
        params = self.get_params_cb()
        self.config_text.configure(state="normal")
        self.config_text.delete("1.0", "end")
        text = (
            f'项目名称: {params.get("project_name", "-")}\n'
            f'工程类型: {params.get("project_type", "-")}\n'
            f'设计阶段: {params.get("design_stage", "-")}\n'
            f'电压等级: {params.get("voltage_level", "-")}\n'
            f'负荷等级: {params.get("load_level", "-")}\n'
            f'电源回路: {params.get("power_source", "-")}\n'
            f'备用说明: {params.get("standby_desc", "-")}\n'
            f'变配电间: {params.get("tx_location", "-")}\n'
            f'\n--- Excel数据 ---\n'
            f'文件: {"✅ 已加载" if self.ctx.excel_data else "❌ 未选择"}\n'
        )
        if self.ctx.excel_data:
            s = self.ctx.excel_data.get("summary", {})
            text += (
                f'设备总数: {s.get("total_devices", 0)}\n'
                f'总容量: {s.get("total_equip_power", 0):.1f} kW\n'
                f'计算负荷: {s.get("total_sc_k", 0):.1f} kVA\n'
                f'变压器: {s.get("recommended_transformer", "-")}\n'
            )
        self.config_text.insert("1.0", text)
        self.config_text.configure(state="disabled")

    # ── Generation ─────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _generate(self) -> None:
        if not self.ctx.excel_data:
            messagebox.showwarning("缺少数据",
                                   "请先在「Excel导入」页面解析负荷计算表")
            return

        params = self.get_params_cb()
        self.gen_btn.configure(text="⏳ 生成中...", state="disabled")
        self.progress.start()
        self._log("🚀 开始生成文档...")
        self._log(f'   工程类型: {params.get("project_type", "-")}')
        self._log(f'   设计阶段: {params.get("design_stage", "-")}')
        self._log(f'   项目名称: {params.get("project_name", "-")}')

        def _task() -> None:
            try:
                edata = self.ctx.excel_data
                assert edata is not None, "excel_data must be set"
                output_path = self.ctx.engine.generate(
                    project_type=params.get("project_type", "water_supply"),
                    design_stage=params.get("design_stage", "初步设计"),
                    excel_data=edata,
                    params=params,
                )
                self.ctx.last_output_path = output_path
                self.after(0, self._on_success, output_path)
            except Exception as exc:
                tb = traceback.format_exc()
                self.after(0, self._on_error, str(exc), tb)

        threading.Thread(target=_task, daemon=True).start()

    def _on_success(self, path: str) -> None:
        self.progress.stop()
        self.gen_btn.configure(text="📝 生成Word文档", state="normal")
        self._log("✅ 文档生成成功！")
        self._log(f'   输出路径: {path}')
        self.path_var.set(f"✅ 文档已生成: {path}")
        messagebox.showinfo("生成成功", f"文档已生成：\n{path}")

    def _on_error(self, err: str, tb: str) -> None:
        self.progress.stop()
        self.gen_btn.configure(text="📝 生成Word文档", state="normal")
        self._log(f"❌ 生成失败: {err}")
        messagebox.showerror("生成失败", err)

    @staticmethod
    def _open_output() -> None:
        output_dir = os.path.join(_PROJECT_ROOT, "output")
        os.makedirs(output_dir, exist_ok=True)
        os.startfile(output_dir)


# ═══════════════════════════════════════════════════════════════════════════
# 6. PAGE: RulesPage
# ═══════════════════════════════════════════════════════════════════════════

class RulesPage(ctk.CTkFrame):
    """Knowledge base viewer — rule items in a treeview with detail panel."""

    def __init__(self, master, ctx: EngineContext, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.ctx = ctx
        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 15))
        ctk.CTkLabel(hdr, text="规范深度要求 - 知识库", font=get_ctk_font("header"),
                     text_color=COLORS["text_primary"]).pack(side="left")
        self.filter_var = ctk.StringVar(value="全部")
        ctk.CTkOptionMenu(
            hdr, values=["全部"] + [lbl for _, lbl in PROJECT_TYPES],
            variable=self.filter_var, font=get_ctk_font("body"),
            corner_radius=8, fg_color=COLORS["bg_primary"],
            button_color=COLORS["accent_blue"],
            command=lambda _: self.refresh(),
        ).pack(side="right")
        ctk.CTkLabel(hdr, text="筛选工程类型：", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(side="right", padx=(0, 6))

        # Split layout
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # Left: item list
        left_card = ctk.CTkFrame(main, fg_color=COLORS["bg_card"],
                                 corner_radius=12, width=400)
        left_card.pack(side="left", fill="both", padx=(0, 8))
        left_card.pack_propagate(False)

        tree_frame = ctk.CTkFrame(left_card, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.listbox = ttk.Treeview(
            tree_frame, columns=("type", "section", "title", "calc"),
            show="headings", height=18,
        )
        self.listbox.heading("type", text="工程类型")
        self.listbox.heading("section", text="章节")
        self.listbox.heading("title", text="条目名称")
        self.listbox.heading("calc", text="含计算")
        self.listbox.column("type", width=80)
        self.listbox.column("section", width=50, anchor="center")
        self.listbox.column("title", width=170)
        self.listbox.column("calc", width=50, anchor="center")
        self.listbox.bind("<<TreeviewSelect>>", self._on_select)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=vsb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Right: detail
        right_card = ctk.CTkFrame(main, fg_color=COLORS["bg_card"],
                                  corner_radius=12)
        right_card.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self.detail_title = ctk.CTkLabel(
            right_card, text="选择一个条目查看详情", font=get_ctk_font("body"),
            text_color=COLORS["text_primary"],
        )
        self.detail_title.pack(anchor="w", padx=20, pady=(15, 5))

        self.detail_text = ctk.CTkTextbox(
            right_card, font=get_ctk_font("body"),
            fg_color=COLORS["bg_card"], corner_radius=8,
            wrap="word",
        )
        self.detail_text.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.detail_text.configure(state="disabled")

    # ── Data ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        filter_val = self.filter_var.get()
        for item in self.listbox.get_children():
            self.listbox.delete(item)

        for code, label in PROJECT_TYPES:
            if filter_val != "全部" and label != filter_val:
                continue
            rule = self.ctx.engine.load_rule(code)
            if not rule:
                continue
            for cat_key, cat_data in rule.get("categories", {}).items():
                section = cat_data.get("section_id", "")
                for item in cat_data.get("items", []):
                    calc_mark = "✅" if item.get("has_calculation") else ""
                    self.listbox.insert(
                        "", "end",
                        values=(label, section, item["title"], calc_mark),
                        tags=(code, cat_key, str(item.get("order", ""))),
                    )

    def _on_select(self, event) -> None:
        sel = self.listbox.selection()
        if not sel:
            return
        values = self.listbox.item(sel[0], "values")
        tags = self.listbox.item(sel[0], "tags")
        if not tags or len(tags) < 3:
            return

        code, cat_key, order_str = tags
        rule = self.ctx.engine.load_rule(code)
        if not rule:
            return

        cat_data = rule.get("categories", {}).get(cat_key, {})
        for item in cat_data.get("items", []):
            if str(item.get("order", "")) == order_str:
                self.detail_title.configure(
                    text=f'{rule["project_type"]} → {cat_data["title"]} → {item["title"]}')
                requirement = item.get("requirement", "无具体要求")
                calc = "是" if item.get("has_calculation") else "否"
                table = "需要" if item.get("table_required") else "不需要"
                calc_from = ("来自Excel"
                             if item.get("calc_from_excel") else "直接生成")

                detail = (
                    f'📋 要求：{requirement}\n\n'
                    f'📌 含计算：{calc}\n'
                    f'📊 需要表格：{table}\n'
                    f'🔄 计算来源：{calc_from}\n'
                    f'📖 章节编号：{cat_data.get("section_id", "")}\n'
                    f'🏗️ 工程类型：{rule["project_type"]}'
                )
                self.detail_text.configure(state="normal")
                self.detail_text.delete("1.0", "end")
                self.detail_text.insert("1.0", detail)
                self.detail_text.configure(state="disabled")
                break


# ═══════════════════════════════════════════════════════════════════════════
# 7. PAGE: AboutPage
# ═══════════════════════════════════════════════════════════════════════════

class AboutPage(ctk.CTkFrame):
    """About / system status page with project save/load."""

    def __init__(self, master, ctx: EngineContext, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.ctx = ctx
        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Centered content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=80)

        # App info
        ctk.CTkLabel(content, text="⚡", font=get_ctk_font("title"),
                     text_color=COLORS["accent_blue"]).pack(pady=(30, 0))
        ctk.CTkLabel(content, text=APP_TITLE, font=get_ctk_font("title"),
                     text_color=COLORS["text_primary"]).pack(pady=(5, 2))
        ctk.CTkLabel(content, text=f"版本 {APP_VERSION}", font=get_ctk_font("body"),
                     text_color=COLORS["text_secondary"]).pack()
        desc = (
            "基于《市政公用工程设计文件编制深度规定》（2025年版）\n"
            "自动生成工程电气及自控设计说明书Word文档"
        )
        ctk.CTkLabel(content, text=desc, font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"],
                     justify="center").pack(pady=(10, 20))

        # System status card
        status_card = ctk.CTkFrame(content, fg_color=COLORS["bg_card"],
                                   corner_radius=12)
        status_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(status_card, text="系统状态", font=get_ctk_font("section"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(15, 10))

        self.status_labels: Dict[str, ctk.CTkLabel] = {}
        checks = [
            ("规则文件", "rules"),
            ("Excel解析器", "excel"),
            ("Word生成器", "docx"),
            ("python-docx", "pydocx"),
            ("输出目录", "output"),
        ]
        for label, key in checks:
            row = ctk.CTkFrame(status_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(row, text=label, font=get_ctk_font("body"),
                         text_color=COLORS["text_primary"],
                         width=120, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="⚪ 检查中...", font=get_ctk_font("caption"),
                               text_color=COLORS["text_secondary"])
            lbl.pack(side="right")
            self.status_labels[key] = lbl

        # Project management buttons
        mgmt_card = ctk.CTkFrame(content, fg_color=COLORS["bg_card"],
                                 corner_radius=12)
        mgmt_card.pack(fill="x")

        ctk.CTkLabel(mgmt_card, text="项目管理", font=get_ctk_font("section"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(15, 10))

        btn_row = ctk.CTkFrame(mgmt_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkButton(
            btn_row, text="💾 保存项目", font=get_ctk_font("body"),
            fg_color=COLORS["accent_blue"], corner_radius=8,
            command=self._save_project,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="📂 加载项目", font=get_ctk_font("body"),
            fg_color=COLORS["bg_selected"],
            text_color=COLORS["text_primary"],
            corner_radius=8, command=self._load_project,
        ).pack(side="left")

        # Recent projects
        self.recent_frame = ctk.CTkFrame(mgmt_card, fg_color="transparent")
        self.recent_frame.pack(fill="x", padx=20, pady=(5, 15))
        self._load_recent_list()

    # ── Health Check ───────────────────────────────────────────────────────

    def refresh(self) -> None:
        status = self.ctx.health_status()
        mapping = {
            "rules":  "规则文件",
            "excel":  "Excel解析器",
            "docx":   "Word生成器",
            "pydocx": "python-docx",
            "output": "输出目录",
        }
        for item_name, msg in status.get("checks", []):
            for key, label in mapping.items():
                if label in item_name:
                    ok = "[OK]" in msg
                    self.status_labels[key].configure(
                        text=f'{"✅" if ok else "❌"} {msg}',
                        text_color=(COLORS["accent_green"]
                                    if ok else COLORS["accent_red"]))
                    break

    # ── Project Save / Load ────────────────────────────────────────────────

    def _save_project(self) -> None:
        path = filedialog.asksaveasfilename(
            title="保存项目",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        data = {
            "params": self.ctx.project_params,
            "excel_path": self.ctx.excel_path,
            "saved_at": datetime.now().isoformat(),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._add_recent(path)
            messagebox.showinfo("保存成功", f"项目已保存至:\n{path}")
        except OSError as exc:
            messagebox.showerror("保存失败", str(exc))

    def _load_project(self) -> None:
        path = filedialog.askopenfilename(
            title="加载项目",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.ctx.project_params = data.get("params", dict(DEFAULT_PARAMS))
            self.ctx.excel_path = data.get("excel_path", "")
            if self.ctx.excel_path and os.path.exists(self.ctx.excel_path):
                self.ctx.excel_data = None
                threading.Thread(
                    target=lambda: self.ctx.engine.parse_excel(self.ctx.excel_path),
                    daemon=True,
                ).start()
            self._add_recent(path)
            messagebox.showinfo("加载成功", f"项目已加载:\n{path}")
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("加载失败", str(exc))

    def _add_recent(self, path: str) -> None:
        os.makedirs(_RECENT_DIR, exist_ok=True)
        recent: list = []
        if os.path.exists(_RECENT_FILE):
            try:
                with open(_RECENT_FILE, "r", encoding="utf-8") as f:
                    recent = json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
        # Deduplicate and keep last 5
        recent = [r for r in recent if r.get("path") != path]
        recent.insert(0, {"path": path, "name": os.path.basename(path),
                          "time": datetime.now().isoformat()})
        recent = recent[:5]
        with open(_RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(recent, f, ensure_ascii=False, indent=2)
        self._load_recent_list()

    def _load_recent_list(self) -> None:
        for w in self.recent_frame.winfo_children():
            w.destroy()
        if not os.path.exists(_RECENT_FILE):
            ctk.CTkLabel(self.recent_frame, text="暂无最近项目",
                         font=get_ctk_font("caption"),
                         text_color=COLORS["text_tertiary"]).pack(anchor="w")
            return
        try:
            with open(_RECENT_FILE, "r", encoding="utf-8") as f:
                recent = json.load(f)
        except (OSError, json.JSONDecodeError):
            recent = []
        if not recent:
            ctk.CTkLabel(self.recent_frame, text="暂无最近项目",
                         font=get_ctk_font("caption"),
                         text_color=COLORS["text_tertiary"]).pack(anchor="w")
            return
        ctk.CTkLabel(self.recent_frame, text="最近项目:", font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 4))
        for entry in recent:
            name = entry.get("name", "未知")
            path = entry.get("path", "")
            btn = ctk.CTkButton(
                self.recent_frame, text=f"📄 {name}", font=get_ctk_font("caption"),
                fg_color="transparent", text_color=COLORS["accent_blue"],
                hover_color=COLORS["bg_hover"], corner_radius=6,
                anchor="w",
                command=lambda p=path: self._load_project_by_path(p),
            )
            btn.pack(fill="x", pady=1)

    def _load_project_by_path(self, path: str) -> None:
        if not os.path.exists(path):
            messagebox.showerror("错误", f"文件不存在:\n{path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.ctx.project_params = data.get("params", dict(DEFAULT_PARAMS))
            self.ctx.excel_path = data.get("excel_path", "")
            if self.ctx.excel_path and os.path.exists(self.ctx.excel_path):
                self.ctx.excel_data = None
            self._add_recent(path)
            messagebox.showinfo("加载成功", f"项目已加载:\n{path}")
        except Exception as exc:
            messagebox.showerror("加载失败", str(exc))


# ═══════════════════════════════════════════════════════════════════════════
# 8. MAIN APPLICATION WINDOW
# ═══════════════════════════════════════════════════════════════════════════

class MacOSApp(ctk.CTk):
    """macOS Sonoma-style main application window."""

    def __init__(self) -> None:
        super().__init__()

        # ── Appearance ──
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # ── Window config ──
        self.title(APP_TITLE)
        self.geometry("1280x820")
        self.minsize(1050, 700)
        self.attributes("-alpha", 0.97)
        self.configure(fg_color=COLORS["bg_primary"])

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - 1280) // 2}+{(sh - 820) // 2}")

        # ── Context ──
        self.ctx = EngineContext()
        self.status_var = tk.StringVar(value="就绪")
        self.health_var = tk.StringVar(value="⚪ 检查中...")

        # ── State ──
        self._current_page: Optional[str] = None
        self._pages: Dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: Dict[str, ctk.CTkButton] = {}
        self._nav_selectors: Dict[str, ctk.CTkFrame] = {}
        self._fade_after_id: Optional[str] = None

        # ── Build ──
        self._build_layout()
        self._switch_page("project")
        self._check_health()

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """Full window layout: sidebar + content area + status bar."""
        # Container grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Content container ──
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0))

        # ── Pages (must exist before sidebar references them) ──
        self._pages["project"]  = ProjectPage(self.content_frame, self.ctx)
        self._pages["excel"]    = ExcelPage(self.content_frame, self.ctx)
        self._pages["generate"] = GeneratePage(
            self.content_frame, self.ctx,
            get_params_cb=lambda: (
                self._pages["project"].get_params()
                if "project" in self._pages
                else dict(DEFAULT_PARAMS)
            ),
        )
        self._pages["rules"]    = RulesPage(self.content_frame, self.ctx)
        self._pages["about"]    = AboutPage(self.content_frame, self.ctx)

        # ── Sidebar (safe now — pages exist) ──
        self._build_sidebar()

        # ── Status bar ──
        self._build_statusbar()

    def _build_sidebar(self) -> None:
        """220px sidebar with nav items."""
        sidebar = ctk.CTkFrame(
            self, fg_color=COLORS["bg_sidebar"],
            corner_radius=0, width=220,
        )
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        # App title
        title_area = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_area.pack(fill="x", padx=16, pady=(20, 20))
        ctk.CTkLabel(title_area, text="⚡ 电气自控生成器",
                     font=get_ctk_font("sidebar_item"),
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(title_area, text=f"v{APP_VERSION}",
                     font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        # Separator
        ctk.CTkFrame(sidebar, fg_color=COLORS["separator"],
                     height=1).pack(fill="x", padx=12)

        # Nav items
        nav_items = [
            ("project",  "📋 项目信息"),
            ("excel",    "📊 Excel导入"),
            ("generate", "📄 生成文档"),
            ("rules",    "📚 知识库"),
            ("about",    "ℹ️ 关于"),
        ]

        nav_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_container.pack(fill="x", padx=8, pady=(12, 0))

        for key, label in nav_items:
            # Row container for selector strip + button
            row = ctk.CTkFrame(nav_container, fg_color="transparent", height=38)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # Selection indicator strip (hidden by default)
            sel_strip = ctk.CTkFrame(row, fg_color="transparent",
                                     width=3, corner_radius=0)
            sel_strip.place(x=0, rely=0, relheight=1.0)
            self._nav_selectors[key] = sel_strip

            btn = ctk.CTkButton(
                row, text=label,
                font=get_ctk_font("sidebar_item"),
                fg_color="transparent",
                hover_color=COLORS["bg_selected"],
                text_color=COLORS["text_primary"],
                anchor="w", corner_radius=8, height=34,
                command=lambda k=key: self._switch_page(k),
            )
            btn.pack(fill="both", padx=(4, 4), pady=0)
            self._nav_buttons[key] = btn

        # Bottom: project management + version
        ctk.CTkFrame(sidebar, fg_color=COLORS["separator"],
                     height=1).pack(fill="x", padx=12, pady=(10, 5))

        # Save/Load buttons
        proj_mgmt = ctk.CTkFrame(sidebar, fg_color="transparent")
        proj_mgmt.pack(fill="x", padx=8, pady=(0, 2))
        ctk.CTkButton(
            proj_mgmt, text="💾 保存项目", font=get_ctk_font("caption"),
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_selected"], corner_radius=6,
            anchor="w", height=30,
            command=self._pages["about"]._save_project,
        ).pack(fill="x", pady=1)
        ctk.CTkButton(
            proj_mgmt, text="📂 加载项目", font=get_ctk_font("caption"),
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color=COLORS["bg_selected"], corner_radius=6,
            anchor="w", height=30,
            command=self._pages["about"]._load_project,
        ).pack(fill="x", pady=1)

        # Bottom spacer + status
        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=12, pady=(0, 15))
        self.sidebar_status = ctk.CTkLabel(
            bottom, textvariable=self.health_var, font=get_ctk_font("caption"),
            text_color=COLORS["text_secondary"],
        )
        self.sidebar_status.pack(anchor="w")

    def _build_statusbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=COLORS["bg_sidebar"], height=28,
                           corner_radius=0)
        bar.grid(row=1, column=1, sticky="ew")
        bar.pack_propagate(False)
        ctk.CTkLabel(bar, textvariable=self.status_var, font=get_ctk_font("caption"),
                     text_color=COLORS["text_secondary"]).pack(
            side="left", padx=12, pady=2)

    # ── Navigation ─────────────────────────────────────────────────────────

    def _switch_page(self, page_name: str) -> None:
        """Switch content area to the target page with smooth transition."""
        if self._current_page == page_name:
            return

        # Cancel any in-progress fade
        if self._fade_after_id:
            self.after_cancel(self._fade_after_id)
            self._fade_after_id = None

        # Hide current page
        if self._current_page and self._current_page in self._pages:
            self._pages[self._current_page].pack_forget()

        # Update nav button styling and selection strips
        for key, btn in self._nav_buttons.items():
            if key == page_name:
                btn.configure(fg_color=COLORS["bg_selected"])
            else:
                btn.configure(fg_color="transparent")
        for key, strip in self._nav_selectors.items():
            strip.configure(
                fg_color=COLORS["accent_blue"] if key == page_name else "transparent"
            )

        # Show target page with fade-in effect
        page = self._pages.get(page_name)
        if page:
            # Start hidden (low opacity via fg_color trick using a cover frame)
            page.pack(fill="both", expand=True)
            # Force immediate render then trigger data refresh
            self.update_idletasks()
            self._current_page = page_name

        # Refresh data on certain pages (deferred for smoothness)
        if page_name == "rules":
            self._pages["rules"].refresh()
        elif page_name == "about":
            self._pages["about"].refresh()
        elif page_name == "generate":
            self._pages["generate"]._refresh_config()

        self.status_var.set(f"就绪 — {self._nav_labels().get(page_name, '')}")

    @staticmethod
    def _nav_labels() -> Dict[str, str]:
        return {
            "project":  "项目信息",
            "excel":    "Excel导入",
            "generate": "生成文档",
            "rules":    "知识库",
            "about":    "关于",
        }

    # ── Health Check ───────────────────────────────────────────────────────

    def _check_health(self) -> None:
        status = self.ctx.health_status()
        if status["all_pass"]:
            self.health_var.set("✅ 系统正常")
        else:
            fails = [m for _, m in status["checks"] if "[FAIL]" in m]
            msg = f'⚠️ {fails[0][:20]}' if fails else "⚠️ 部分异常"
            self.health_var.set(msg)
        self.status_var.set("就绪")

    # ── Close ──────────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════
# 9. MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Launch the macOS-style desktop application."""
    app = MacOSApp()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    # Initial data loads after UI is ready
    app.after(300, lambda: app._pages["rules"].refresh())
    app.after(300, lambda: app._pages["about"].refresh())
    app.after(500, lambda: (
        app._pages["generate"]._refresh_config()
        if "generate" in app._pages else None
    ))
    app.mainloop()


if __name__ == "__main__":
    main()
