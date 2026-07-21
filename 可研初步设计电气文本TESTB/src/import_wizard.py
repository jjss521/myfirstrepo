"""
Import Wizard — 导入已完稿 .docx 文档，按标题分割，分配到子模块，保存为模板变体

4-step workflow:
1. Select .docx file
2. Parse & split preview (auto-split by headings)
3. Assign each section to sub-module
4. Save all as variants

Accessed from TemplateLibraryPage._open_import_wizard via:
    from import_wizard import ImportWizard
    ImportWizard(self, self.ctx)
"""
from __future__ import annotations

import os
import sys
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from tkinter import filedialog, messagebox

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

# ── COLORS: import from macos_gui with fallback ──
try:
    from macos_gui import COLORS
except ImportError:
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

# ── Ensure backend is importable ──
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SRC_DIR)
_BACKEND_DIR = os.path.join(_PROJECT_DIR, 'backend')
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)


def _iter_categories(categories: dict):
    """Walk category data, handling both flat (items directly) and
    container (sub-categories under a key) structures — matches
    GenerateEngine._iter_categories behaviour."""
    for key, data in categories.items():
        if not isinstance(data, dict):
            continue
        if 'items' in data:
            yield key, data
        else:
            for sub_key, sub_data in data.items():
                if isinstance(sub_data, dict) and 'items' in sub_data:
                    yield sub_key, sub_data


class ImportWizard(ctk.CTkToplevel):
    """四步导入向导窗口 — 导入 .docx → 分割 → 分配 → 保存"""

    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.parent = parent

        self.title("导入文档 — 模板变体生成向导")
        self.geometry("900x650")
        self.minsize(800, 550)

        # ── State ──
        self.docx_path: str = ""
        self.sections: List[Dict] = []  # [{"heading", "content", "level"}, ...]
        self.assignment_rows: List[Dict] = []  # [{"section_idx", "heading", "type_var", "stage_var", "submodule_var"}, ...]

        # ── Load rule data for dropdowns ──
        self.project_types: List[tuple] = []
        self.design_stages: List[str] = ["可行性研究", "初步设计"]
        self.category_names: List[str] = ["电气", "自控"]
        self.items_by_type: Dict[str, List[Dict]] = {}
        self.submodule_names: List[str] = []
        self._load_rule_data()

        # ── Build UI ──
        self._build()

        self.transient(parent)
        self.grab_set()

    # ════════════════════════════════════════════════════════════════════
    #  DATA LOADING
    # ════════════════════════════════════════════════════════════════════

    def _load_rule_data(self) -> None:
        """Load project types, stages, categories, item titles, sub-module
        names from rule JSON files via the engine."""
        engine = getattr(self.ctx, 'engine', None)
        if engine is None:
            self.project_types = [
                ("water_supply", "给水工程"),
                ("drainage",     "排水工程"),
                ("road",         "道路工程"),
                ("sanitation",   "环卫工程"),
            ]
            return

        # Build project types from engine's own list (if available)
        for code, info in getattr(engine, 'PROJECT_TYPES', {}).items():
            label = info.get('label', code)
            self.project_types.append((code, label))

        if not self.project_types:
            self.project_types = [
                ("water_supply", "给水工程"),
                ("drainage",     "排水工程"),
                ("road",         "道路工程"),
                ("sanitation",   "环卫工程"),
            ]

        seen_names: set = set()

        for code, _label in self.project_types:
            rule = engine.load_rule(code)
            items_list: List[Dict] = []
            if rule:
                for stage_name, stage_data in rule.get("design_stages", {}).items():
                    if not isinstance(stage_data, dict):
                        continue
                    # sanitation uses {"sections": {…}}; others are flat
                    categories = stage_data.get("sections", stage_data) if isinstance(stage_data, dict) else {}
                    for cat_key, cat_data in _iter_categories(categories):
                        for item in cat_data.get("items", []):
                            items_list.append({
                                "title": item.get("title", ""),
                                "category": cat_key,
                                "stage": stage_name,
                            })
                            for sm in item.get("sub_modules", []):
                                name = sm.get("name", "")
                                if name and name not in seen_names:
                                    seen_names.add(name)
                                    self.submodule_names.append(name)
            self.items_by_type[code] = items_list

        self.submodule_names.sort()

    # ════════════════════════════════════════════════════════════════════
    #  UI — MAIN STRUCTURE
    # ════════════════════════════════════════════════════════════════════

    def _build(self) -> None:
        """Build the four-step wizard layout."""
        # Step indicator bar
        self.step_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.step_frame.pack(fill="x", padx=20, pady=(15, 5))

        step_texts = ["① 选择文件", "② 预览分割", "③ 分配子模块", "④ 保存确认"]
        self.step_labels: List[ctk.CTkLabel] = []
        for i, text in enumerate(step_texts):
            lbl = ctk.CTkLabel(self.step_frame, text=text, font=("", 13))
            lbl.pack(side="left", padx=(0, 25))
            self.step_labels.append(lbl)
        self._update_step(0)

        # Content area
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=20, pady=10)

        # Four step containers
        self.step_frames: List[ctk.CTkFrame] = []
        for _i in range(4):
            frame = ctk.CTkFrame(self.content, fg_color="transparent")
            self.step_frames.append(frame)

        self._build_step1()
        self._build_step2()
        self._build_step3()
        self._build_step4()

        # Bottom navigation bar (must be created before _show_step)
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=20, pady=15)

        self.back_btn = ctk.CTkButton(
            nav, text="← 上一步", command=self._go_back, state="disabled")
        self.back_btn.pack(side="left")

        self.next_btn = ctk.CTkButton(
            nav, text="下一步 →", command=self._go_next,
            fg_color=COLORS.get("accent_blue", "#007AFF"))
        self.next_btn.pack(side="right")

        self.cancel_btn = ctk.CTkButton(
            nav, text="取消", command=self.destroy, fg_color="gray")
        self.cancel_btn.pack(side="right", padx=(0, 10))

        self.current_step: int = 0

        self._show_step(0)

    # ════════════════════════════════════════════════════════════════════
    #  STEP NAVIGATION
    # ════════════════════════════════════════════════════════════════════

    def _update_step(self, step: int) -> None:
        """Highlight current step label, mark completed steps green."""
        for i, lbl in enumerate(self.step_labels):
            if i == step:
                lbl.configure(
                    text_color=COLORS.get("accent_blue", "#007AFF"),
                    font=("", 13, "bold"))
            elif i < step:
                lbl.configure(text_color="green", font=("", 13))
            else:
                lbl.configure(text_color="gray", font=("", 13))

    def _show_step(self, step: int) -> None:
        """Switch to the given step, running any step-specific setup."""
        for f in self.step_frames:
            f.pack_forget()
        self.step_frames[step].pack(fill="both", expand=True)
        self._update_step(step)
        self.current_step = step

        # Back button
        self.back_btn.configure(state="normal" if step > 0 else "disabled")

        # Next / Save button
        if step == 3:
            self.next_btn.configure(text="💾 保存全部", command=self._save_all)
        else:
            self.next_btn.configure(text="下一步 →", command=self._go_next)

        # Step-specific setup
        if step == 1 and self.docx_path:
            self._parse_docx()
        elif step == 2:
            self._build_assignment_rows()
        elif step == 3:
            self._build_summary()

    def _go_back(self) -> None:
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _go_next(self) -> None:
        if self.current_step == 0:
            if not self.docx_path:
                messagebox.showwarning("提示", "请先选择一个 .docx 文件")
                return
        elif self.current_step == 1:
            if not self.sections:
                messagebox.showwarning("提示", "未检测到章节内容")
                return
        elif self.current_step == 2:
            for row in self.assignment_rows:
                sm_val = row["submodule_var"].get()
                if not sm_val or sm_val.strip() == "":
                    messagebox.showwarning("提示", "请为所有章节选择子模块名称")
                    return
        self._show_step(self.current_step + 1)

    # ════════════════════════════════════════════════════════════════════
    #  STEP 1 — FILE SELECTION
    # ════════════════════════════════════════════════════════════════════

    def _build_step1(self) -> None:
        frame = self.step_frames[0]
        ctk.CTkLabel(frame, text="选择已完稿的 Word 文档",
                     font=("", 16, "bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkLabel(frame, text="选择一个 .docx 文件，系统将自动按标题（Heading）结构分割文档。",
                     font=("", 12)).pack(anchor="w")

        ctk.CTkFrame(frame, fg_color="transparent", height=30).pack()

        select_frame = ctk.CTkFrame(
            frame, fg_color=COLORS.get("bg_card", "#FFFFFF"), corner_radius=12)
        select_frame.pack(fill="x", pady=20, padx=20)

        self.file_label = ctk.CTkLabel(select_frame, text="未选择文件", font=("", 14))
        self.file_label.pack(pady=(30, 15))

        ctk.CTkButton(
            select_frame, text="📂 选择 Word 文档 (.docx)",
            command=self._select_file,
            fg_color=COLORS.get("accent_blue", "#007AFF"),
            height=40, font=("", 13),
        ).pack(pady=(0, 30))

    def _select_file(self) -> None:
        path = filedialog.askopenfilename(
            title="选择已完稿的Word文档",
            filetypes=[("Word文档", "*.docx"), ("所有文件", "*.*")],
        )
        if path:
            self.docx_path = path
            self.file_label.configure(
                text=f"📄 {os.path.basename(path)}", text_color="black")

    # ════════════════════════════════════════════════════════════════════
    #  STEP 2 — PARSE & PREVIEW
    # ════════════════════════════════════════════════════════════════════

    def _build_step2(self) -> None:
        frame = self.step_frames[1]

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text="预览并调整分割",
                     font=("", 16, "bold")).pack(side="left")
        ctk.CTkLabel(top, text="左侧选择章节，右侧预览内容。可使用下方按钮调整分割。",
                     font=("", 11)).pack(side="left", padx=(20, 0))

        main = ctk.CTkFrame(frame, fg_color="transparent")
        main.pack(fill="both", expand=True, pady=10)

        # Left: section tree
        left = ctk.CTkFrame(
            main, fg_color=COLORS.get("bg_card", "#FFFFFF"), corner_radius=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ctk.CTkLabel(left, text="文档结构",
                     font=("", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.section_tree = ttk.Treeview(left, show="tree", height=15)
        self.section_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.section_tree.bind("<<TreeviewSelect>>", self._on_section_select)

        # Right: content preview
        right = ctk.CTkFrame(
            main, fg_color=COLORS.get("bg_card", "#FFFFFF"), corner_radius=12)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        ctk.CTkLabel(right, text="章节内容",
                     font=("", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.section_preview = ctk.CTkTextbox(
            right, wrap="word", state="disabled")
        self.section_preview.pack(
            fill="both", expand=True, padx=10, pady=(0, 10))

        # Split/merge controls
        ctrl = ctk.CTkFrame(frame, fg_color="transparent")
        ctrl.pack(fill="x", pady=(5, 0))
        ctk.CTkButton(
            ctrl, text="🔀 合并到上一章节",
            command=self._merge_up, width=130).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            ctrl, text="✂️ 在此分割",
            command=self._split_here, width=100).pack(side="left")

    def _parse_docx(self) -> None:
        """Parse .docx file and extract sections by heading paragraphs."""
        try:
            from docx import Document

            doc = Document(self.docx_path)

            self.sections = []
            current_heading = "文档开头"
            current_level = 1
            current_content: List[str] = []

            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue

                style = ""
                if para.style and para.style.name:
                    style = para.style.name.lower()
                is_heading = any(
                    prefix in style for prefix in ["heading", "标题"])

                if is_heading:
                    # Save previous section
                    if current_content:
                        self.sections.append({
                            "heading": current_heading,
                            "content": "\n".join(current_content),
                            "level": current_level,
                        })

                    # Extract heading level number
                    level = 1
                    parts = style.split()
                    for part in parts:
                        if part.isdigit():
                            level = int(part)
                            break

                    current_heading = text
                    current_level = level
                    current_content = []
                else:
                    current_content.append(text)

            # Save last section
            if current_content:
                self.sections.append({
                    "heading": current_heading,
                    "content": "\n".join(current_content),
                    "level": current_level,
                })

            # Populate treeview
            self._reparse_tree()

        except ImportError:
            messagebox.showerror("缺少依赖",
                "需要安装 python-docx 库。\n请运行: pip install python-docx")
            self.sections = []
        except Exception as e:
            messagebox.showerror("解析失败", f"无法解析文档：{e}")
            self.sections = []

    def _on_section_select(self, event) -> None:
        sel = self.section_tree.selection()
        if not sel:
            return
        iid = sel[0]
        if iid.startswith("sec_"):
            idx = int(iid.replace("sec_", ""))
            if 0 <= idx < len(self.sections):
                sec = self.sections[idx]
                self.section_preview.configure(state="normal")
                self.section_preview.delete("1.0", "end")
                self.section_preview.insert("1.0", sec["content"])
                self.section_preview.configure(state="disabled")

    def _merge_up(self) -> None:
        """Merge selected section into the previous one."""
        sel = self.section_tree.selection()
        if not sel:
            return
        iid = sel[0]
        if not iid.startswith("sec_"):
            return
        idx = int(iid.replace("sec_", ""))
        if idx <= 0 or idx >= len(self.sections):
            return

        self.sections[idx - 1]["content"] += "\n" + self.sections[idx]["content"]
        self.sections.pop(idx)
        self._reparse_tree()

    def _split_here(self) -> None:
        """Split selected section at a natural paragraph break near midpoint."""
        sel = self.section_tree.selection()
        if not sel:
            return
        iid = sel[0]
        if not iid.startswith("sec_"):
            return
        idx = int(iid.replace("sec_", ""))
        if idx >= len(self.sections):
            return

        sec = self.sections[idx]
        content = sec["content"]
        if not content.strip():
            return

        mid = len(content) // 2
        split_at = content.rfind("\n", 0, mid)
        if split_at < 0:
            split_at = mid

        part1 = content[:split_at].strip()
        part2 = content[split_at:].strip()
        if part1 and part2:
            self.sections[idx]["content"] = part1
            self.sections.insert(idx + 1, {
                "heading": sec["heading"] + " (续)",
                "content": part2,
                "level": sec["level"],
            })
            self._reparse_tree()

    def _reparse_tree(self) -> None:
        """Rebuild the treeview from self.sections."""
        for item in self.section_tree.get_children():
            self.section_tree.delete(item)
        for i, sec in enumerate(self.sections):
            indent = "  " * (sec.get("level", 1) - 1)
            display = f"{indent}{sec['heading']}"
            self.section_tree.insert(
                "", "end", iid=f"sec_{i}", text=display, open=True)

    # ════════════════════════════════════════════════════════════════════
    #  STEP 3 — ASSIGN TO SUB-MODULES
    # ════════════════════════════════════════════════════════════════════

    def _build_step3(self) -> None:
        frame = self.step_frames[2]

        ctk.CTkLabel(frame, text="将各章节分配到子模块",
                     font=("", 16, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(frame, text="为每个文档章节选择对应的工程类型、设计阶段、子模块名称。",
                     font=("", 11)).pack(anchor="w")

        self.assign_container = ctk.CTkScrollableFrame(
            frame, fg_color="transparent")
        self.assign_container.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(self.assign_container,
                     text="请先完成第2步（预览分割）。",
                     font=("", 12)).pack(pady=50)

    def _build_assignment_rows(self) -> None:
        """Populate the scrollable assignment area with one row per section."""
        for w in self.assign_container.winfo_children():
            w.destroy()

        if not self.sections:
            ctk.CTkLabel(self.assign_container,
                         text="没有需要分配的章节。请返回第2步。",
                         font=("", 12)).pack(pady=50)
            return

        self.assignment_rows = []

        # Prepare combo values
        type_labels = [label for _code, label in self.project_types]
        sm_values = self.submodule_names if self.submodule_names else ["(无子模块)"]

        for i, sec in enumerate(self.sections):
            row_frame = ctk.CTkFrame(
                self.assign_container,
                fg_color=COLORS.get("bg_card", "#FFFFFF"), corner_radius=8)
            row_frame.pack(fill="x", pady=4, padx=5)

            # Heading
            ctk.CTkLabel(row_frame, text=sec["heading"],
                         font=("", 12, "bold")).pack(
                anchor="w", padx=10, pady=(8, 5))

            # Content preview (truncated)
            preview = sec["content"][:80]
            if len(sec["content"]) > 80:
                preview += "..."
            ctk.CTkLabel(row_frame, text=preview,
                         font=("", 10), text_color="gray").pack(
                anchor="w", padx=10, pady=(0, 5))

            # Assignment controls
            assign_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            assign_frame.pack(fill="x", padx=10, pady=(0, 8))

            # Project type
            ctk.CTkLabel(assign_frame, text="工程类型：").pack(side="left")
            type_var = tk.StringVar(value=type_labels[0] if type_labels else "")
            ctk.CTkComboBox(
                assign_frame, values=type_labels, width=120,
                state="readonly", variable=type_var,
            ).pack(side="left", padx=(0, 10))

            # Design stage
            ctk.CTkLabel(assign_frame, text="阶段：").pack(side="left")
            stage_var = tk.StringVar(value="可行性研究")
            ctk.CTkComboBox(
                assign_frame, values=self.design_stages, width=90,
                state="readonly", variable=stage_var,
            ).pack(side="left", padx=(0, 10))

            # Sub-module
            ctk.CTkLabel(assign_frame, text="子模块：").pack(side="left")
            sm_var = tk.StringVar(value=sm_values[0])
            ctk.CTkComboBox(
                assign_frame, values=sm_values, width=150,
                state="readonly", variable=sm_var,
            ).pack(side="left", padx=(0, 10))

            self.assignment_rows.append({
                "section_idx": i,
                "heading": sec["heading"],
                "type_var": type_var,
                "stage_var": stage_var,
                "submodule_var": sm_var,
            })

    # ════════════════════════════════════════════════════════════════════
    #  STEP 4 — SAVE SUMMARY & EXECUTION
    # ════════════════════════════════════════════════════════════════════

    def _build_step4(self) -> None:
        frame = self.step_frames[3]

        ctk.CTkLabel(frame, text="保存确认",
                     font=("", 16, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(frame, text="以下章节将被保存为模板变体。",
                     font=("", 11)).pack(anchor="w")

        self.summary_text = ctk.CTkTextbox(
            frame, wrap="word", state="disabled")
        self.summary_text.pack(fill="both", expand=True, pady=10)

    def _build_summary(self) -> None:
        """Render save confirmation summary."""
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")

        total = len(self.assignment_rows)
        self.summary_text.insert("end",
            f"共 {total} 个章节将被保存为模板变体\n\n", "bold")
        self.summary_text.insert("end",
            f"来源文件：{os.path.basename(self.docx_path)}\n")
        self.summary_text.insert("end", "-" * 50 + "\n\n")

        for row in self.assignment_rows:
            sm = row["submodule_var"].get()
            pt = row["type_var"].get()
            stage = row["stage_var"].get()
            self.summary_text.insert("end", f"📄 {row['heading']}\n")
            self.summary_text.insert("end", f"   → {pt} / {stage} / {sm}\n\n")

        self.summary_text.configure(state="disabled")

    def _save_all(self) -> None:
        """Save all sections as template variants via CustomTemplateManager."""
        try:
            from app.services.custom_template_manager import CustomTemplateManager
        except ImportError:
            messagebox.showerror("导入失败",
                "无法加载 CustomTemplateManager。\n请确认 backend/app/services/ 存在且路径正确。")
            return

        # Determine data dir from engine's project_root, or fall back
        engine = getattr(self.ctx, 'engine', None)
        if engine and getattr(engine, 'project_root', None):
            ctm_dir = os.path.join(
                engine.project_root, "backend", "data", "custom_templates")
        else:
            ctm_dir = os.path.join(_PROJECT_DIR, "backend", "data", "custom_templates")

        mgr = CustomTemplateManager(ctm_dir)

        # Lookup maps
        code_map = {
            "给水工程": "water_supply",
            "排水工程": "drainage",
            "道路工程": "road",
            "环卫工程": "sanitation",
        }
        # Reverse: code → label
        label_map = {v: k for k, v in code_map.items()}

        saved_count = 0
        errors: List[str] = []

        for row in self.assignment_rows:
            sec = self.sections[row["section_idx"]]
            pt_label = row["type_var"].get()
            pt_code = code_map.get(pt_label, "water_supply")
            stage = row["stage_var"].get()
            sm_name = row["submodule_var"].get()

            # Try to find matching item for category / item_title
            category = "电气"  # default
            item_title = row["heading"]  # fallback: use section heading

            items = self.items_by_type.get(pt_code, [])
            matching = [it for it in items if it["stage"] == stage]
            if matching:
                # Prefer an item whose sub_modules contain the selected name
                best = matching[0]
                for it in matching:
                    # We can't easily check sub-modules here, so take first match
                    category = it["category"]
                    item_title = it["title"] if it["title"] else item_title
                    break
                if best:
                    category = best["category"]
                    if best["title"]:
                        item_title = best["title"]

            # Derive template name from source doc + sub-module
            base = os.path.splitext(os.path.basename(self.docx_path))[0]
            template_name = f"{base}_{sm_name}"

            template = {
                "project_type": pt_code,
                "design_stage": stage,
                "category": category,
                "item_title": item_title,
                "template_name": template_name,
                "content": sec["content"],
                "source_doc": os.path.basename(self.docx_path),
                "tags": [pt_label, stage],
                "is_rich_text": False,
                "sub_module_name": sm_name,
            }

            try:
                mgr.save_template(template)
                saved_count += 1
            except Exception as e:
                errors.append(f"{row['heading']}: {e}")

        # Report
        result_msg = f"✅ 成功保存 {saved_count}/{len(self.assignment_rows)} 个模板变体。"
        if errors:
            result_msg += f"\n\n⚠️ {len(errors)} 个失败：\n"
            result_msg += "\n".join(errors[:5])

        messagebox.showinfo("导入完成", result_msg)

        if saved_count > 0:
            self.destroy()  # Close wizard on success
