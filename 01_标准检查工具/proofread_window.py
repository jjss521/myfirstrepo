"""
规范编号校对工具窗口

输入文字 → 识别所有标准编号 → 在线检查有效性 → 自动纠正错误 → 标红记录
"""

import logging
import os
import queue
import sys
import threading
from tkinter import messagebox

try:
    import customtkinter as ctk
except ImportError:
    import tkinter as tk

    tk.messagebox.showerror("缺少依赖", "未安装 customtkinter")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import REQUEST_DELAY_MAX, REQUEST_DELAY_MIN
from models import StandardStatus, ValidatedStandard
from standard_parser import parse_standards_from_text
from utils import RateLimiter
from web_scraper import fetch_replacement_info, search_standard

logger = logging.getLogger("standard_checker")


class ProofreadWindow(ctk.CTkToplevel):
    """规范编号校对工具 - 独立校对窗口"""

    # 配色 - 与主窗口一致
    PRIMARY = "#0D9488"
    PRIMARY_HOVER = "#0F766E"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    DANGER_HOVER = "#DC2626"
    TEXT_SECONDARY = "gray55"
    BORDER = "gray25"

    def __init__(self, parent):
        super().__init__(parent)
        self.title("规范编号校对工具")
        self.geometry("980x760")
        self.minsize(800, 600)

        # 状态
        self.is_running = False
        self._cancel_requested = False
        self.log_queue = queue.Queue()
        self._validated_results = []
        self._parsed_standards = []
        self._corrected_text = ""

        self._build_ui()
        self._poll_log_queue()

        # 居中
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + (pw - 980) // 2
        y = py + (ph - 760) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    # ==================== UI 构建 ====================

    def _build_ui(self):
        # 标题
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(16, 6))

        ctk.CTkLabel(
            header,
            text="规范编号校对工具",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="  粘贴文本 → 识别编号 → 在线检查 → 自动纠正",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_SECONDARY,
        ).pack(side="left", padx=(12, 0))

        # 图例
        legend = ctk.CTkFrame(header, fg_color="transparent")
        legend.pack(side="right")
        ctk.CTkLabel(
            legend, text="■ 有效", font=ctk.CTkFont(size=11), text_color=self.SUCCESS
        ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            legend, text="■ 过期/错误", font=ctk.CTkFont(size=11), text_color=self.DANGER
        ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            legend, text="■ 未确认", font=ctk.CTkFont(size=11), text_color=self.TEXT_SECONDARY
        ).pack(side="left")

        # 输入区卡片
        input_card = ctk.CTkFrame(self, corner_radius=12, border_width=1, border_color=self.BORDER)
        input_card.pack(fill="x", padx=22, pady=(6, 6))

        input_title = ctk.CTkFrame(input_card, fg_color="transparent")
        input_title.pack(fill="x", padx=18, pady=(12, 0))

        ctk.CTkLabel(input_title, text="输入文本", font=ctk.CTkFont(size=14, weight="bold")).pack(
            side="left"
        )

        self.line_count_label = ctk.CTkLabel(
            input_title,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.TEXT_SECONDARY,
        )
        self.line_count_label.pack(side="right")

        # 格式提示
        ctk.CTkLabel(
            input_card,
            text="支持换行、分号（; 或 ；）、多个空格、逗号分隔标准编号",
            font=ctk.CTkFont(size=11),
            text_color=self.TEXT_SECONDARY,
        ).pack(anchor="w", padx=18, pady=(2, 4))

        # 文本框
        self.text_input = ctk.CTkTextbox(
            input_card,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            height=130,
            corner_radius=8,
            border_width=1,
            border_color="gray30",
        )
        self.text_input.pack(fill="x", padx=18, pady=(0, 6))

        # 占位示例
        placeholder = (
            "GB 50016-2014 建筑设计防火规范\n"
            "GB/T 50352-2019 民用建筑设计统一标准; JGJ/T 3-2010 高层建筑混凝土结构技术规程\n"
            "GB 50222-2017 建筑内部装修设计防火规范"
        )
        self.text_input.insert("1.0", placeholder)
        self.text_input.bind("<KeyRelease>", self._on_text_changed)
        self._on_text_changed(None)

        # 工具栏
        toolbar = ctk.CTkFrame(input_card, fg_color="transparent")
        toolbar.pack(fill="x", padx=18, pady=(0, 12))

        btn_kwargs = dict(
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="gray25",
            hover_color="gray35",
            border_width=1,
            border_color="gray35",
        )

        ctk.CTkButton(
            toolbar, text="从文件导入", width=90, command=self._import_file, **btn_kwargs
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            toolbar, text="从剪贴板粘贴", width=100, command=self._paste_clipboard, **btn_kwargs
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            toolbar,
            text="清空",
            width=60,
            command=self._clear_input,
            fg_color="gray25",
            hover_color="#7F1D1D",
            border_width=1,
            border_color="gray35",
            corner_radius=6,
            height=32,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

        # 操作按钮（右侧）
        self.btn_start = ctk.CTkButton(
            toolbar,
            text="开始校对",
            width=100,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.PRIMARY,
            hover_color=self.PRIMARY_HOVER,
            corner_radius=6,
            height=34,
            command=self._on_start_proofread,
        )
        self.btn_start.pack(side="right", padx=(6, 0))

        self.btn_parse_only = ctk.CTkButton(
            toolbar,
            text="仅解析",
            width=75,
            font=ctk.CTkFont(size=12),
            fg_color="gray30",
            hover_color="gray40",
            corner_radius=6,
            height=34,
            border_width=1,
            border_color="gray40",
            command=self._on_parse_only,
        )
        self.btn_parse_only.pack(side="right", padx=(6, 0))

        self.btn_stop = ctk.CTkButton(
            toolbar,
            text="停止",
            width=60,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.DANGER,
            hover_color=self.DANGER_HOVER,
            corner_radius=6,
            height=34,
            command=self._on_stop,
            state="disabled",
        )
        self.btn_stop.pack(side="right")

        # 进度条
        self.progress = ctk.CTkProgressBar(self, height=4, corner_radius=2)
        self.progress.pack(fill="x", padx=22, pady=(0, 4))
        self.progress.set(0)

        # 标签页区域
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=22, pady=(4, 12))

        # 校对结果 Tab
        result_tab = self.tabview.add("校对结果")
        self.result_box = ctk.CTkTextbox(
            result_tab,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            wrap="word",
            state="disabled",
            corner_radius=6,
        )
        self.result_box.pack(fill="both", expand=True, padx=4, pady=4)

        # 详细信息 Tab
        detail_tab = self.tabview.add("详细信息")
        self.detail_frame = ctk.CTkScrollableFrame(detail_tab, corner_radius=6)
        self.detail_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # 纠正文本 Tab
        corrected_tab = self.tabview.add("纠正文本")
        self.corrected_box = ctk.CTkTextbox(
            corrected_tab,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            state="disabled",
            corner_radius=6,
        )
        self.corrected_box.pack(fill="both", expand=True, padx=4, pady=4)

        self.btn_copy_corrected = ctk.CTkButton(
            corrected_tab,
            text="复制纠正结果",
            width=120,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=self.PRIMARY,
            hover_color=self.PRIMARY_HOVER,
            corner_radius=6,
            command=self._copy_corrected_text,
        )
        self.btn_copy_corrected.pack(side="right", padx=8, pady=6)

        # 底部状态栏
        status_bar = ctk.CTkFrame(self, fg_color="transparent", height=28)
        status_bar.pack(fill="x", padx=22, pady=(0, 8))

        self.status_label = ctk.CTkLabel(
            status_bar,
            text="就绪 - 请粘贴包含标准编号的文本",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_SECONDARY,
        )
        self.status_label.pack(side="left")

        self.stats_label = ctk.CTkLabel(
            status_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_SECONDARY,
        )
        self.stats_label.pack(side="right")

    # ==================== 事件处理 ====================

    def _on_text_changed(self, event=None):
        try:
            text = self.text_input.get("1.0", "end-1c")
            entries = [
                e for e in text.replace(";", "\n").replace("；", "\n").split("\n") if e.strip()
            ]
            self.line_count_label.configure(text=f"{len(entries)} 条内容")
        except Exception:
            pass

    def _import_file(self):
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, encoding="gbk") as f:
                content = f.read()
        current = self.text_input.get("1.0", "end-1c").strip()
        if current:
            self.text_input.insert("end", "\n" + content)
        else:
            self.text_input.delete("1.0", "end")
            self.text_input.insert("1.0", content)
        self._on_text_changed()

    def _paste_clipboard(self):
        try:
            text = self.clipboard_get()
            if text:
                self.text_input.delete("1.0", "end")
                self.text_input.insert("1.0", text)
                self._on_text_changed()
        except Exception:
            messagebox.showinfo("提示", "剪贴板为空")

    def _clear_input(self):
        self.text_input.delete("1.0", "end")
        self._on_text_changed()

    def _on_parse_only(self):
        """仅解析标准编号，不做在线查询"""
        text = self.text_input.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("提示", "请先输入或粘贴包含标准编号的文本")
            return

        standards = parse_standards_from_text(text)
        if not standards:
            messagebox.showwarning("解析结果", "未能从文本中解析出任何标准编号")
            return

        self._parsed_standards = standards

        # 显示解析结果
        lines = []
        for i, ref in enumerate(standards, 1):
            name_part = f"  {ref.name}" if ref.name else "  (未识别名称)"
            lines.append(f"{i:>3}. {ref.number}{name_part}")

        self._show_result_text(
            f"共解析出 {len(standards)} 条标准（仅解析，未做在线检查）:\n\n" + "\n".join(lines)
        )
        self.status_label.configure(text=f"解析完成: {len(standards)} 条标准")
        self.tabview.set("校对结果")

    def _on_start_proofread(self):
        """开始在线校对"""
        text = self.text_input.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("提示", "请先输入或粘贴包含标准编号的文本")
            return

        standards = parse_standards_from_text(text)
        if not standards:
            messagebox.showwarning("解析结果", "未能从文本中解析出任何标准编号")
            return

        self._parsed_standards = standards
        self._validated_results = []
        self._corrected_text = ""

        # 锁定 UI
        self.is_running = True
        self._cancel_requested = False
        self.btn_start.configure(state="disabled", text="校对中...")
        self.btn_parse_only.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status_label.configure(text="正在在线校对...")
        self.stats_label.configure(text=f"共 {len(standards)} 条待查")

        # 清空结果
        self._clear_result_box()
        self._clear_detail_frame()
        self._clear_corrected_box()

        self.tabview.set("校对结果")

        # 后台线程
        thread = threading.Thread(
            target=self._run_proofread_pipeline,
            args=(standards,),
            daemon=True,
        )
        thread.start()

    def _on_stop(self):
        self._cancel_requested = True
        self.btn_stop.configure(state="disabled")
        self.status_label.configure(text="正在停止...")

    # ==================== 后台校对流水线 ====================

    def _run_proofread_pipeline(self, standards):
        """后台线程：逐条在线查询标准"""
        try:
            import requests as req_lib

            session = req_lib.Session()
            rate_limiter = RateLimiter(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            total = len(standards)

            for i, ref in enumerate(standards, 1):
                if self._cancel_requested:
                    break

                self.log_queue.put(("INFO", f"[{i}/{total}] 查询: {ref.number} {ref.name}"))
                self.after(
                    0, lambda idx=i, t=total: self.stats_label.configure(text=f"查询: {idx}/{t}")
                )

                # 在线搜索
                search_result = search_standard(ref, session, rate_limiter)
                replacement_info = None

                # 如果是过期标准，获取替代信息
                if search_result and search_result.status in (
                    StandardStatus.ABOLISHED,
                    StandardStatus.REPEALED,
                ):
                    self.log_queue.put(
                        ("WARNING", f"  → {search_result.status.value}，获取替代信息...")
                    )
                    replacement_info = fetch_replacement_info(
                        search_result.detail_url,
                        ref.number,
                        ref.name,
                        session,
                        rate_limiter,
                    )

                validated = ValidatedStandard(
                    standard_ref=ref,
                    search_result=search_result,
                    replacement_info=replacement_info,
                )
                self._validated_results.append(validated)

                # 实时更新结果
                self.after(0, self._refresh_result_display)

            # 完成
            if self._cancel_requested:
                self.log_queue.put(("WARNING", "用户取消"))
                self._finish_proofread(False)
            else:
                self.log_queue.put(("SUCCESS", "校对完成！"))
                self._finish_proofread(True)

        except Exception as e:
            self.log_queue.put(("ERROR", f"校对出错: {e}"))
            import traceback

            self.log_queue.put(("ERROR", traceback.format_exc()))
            self._finish_proofread(False)

    def _finish_proofread(self, success):
        """完成后恢复UI"""
        self.is_running = False
        self._finish_ok = success
        self.after(0, self._apply_finish_proofread_ui)

    def _apply_finish_proofread_ui(self):
        self.btn_start.configure(state="normal", text="开始校对")
        self.btn_parse_only.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.progress.stop()

        if self._finish_ok:
            self.progress.set(1.0)
            # 统计
            expired = sum(
                1
                for v in self._validated_results
                if v.search_result and v.search_result.status.value in ("作废", "废止")
            )
            active = sum(
                1
                for v in self._validated_results
                if v.search_result and v.search_result.status.value == "现行"
            )
            unknown = sum(
                1
                for v in self._validated_results
                if v.search_result is None or v.search_result.status.value == "未知"
            )
            self.stats_label.configure(
                text=f"现行: {active}  |  过期: {expired}  |  未确认: {unknown}"
            )
            self.status_label.configure(text="校对完成")

            # 生成纠正文本
            self._generate_corrected_text()
        else:
            self.progress.set(0)
            self.status_label.configure(text="校对已停止")

        # 最终刷新
        self._refresh_result_display()

    # ==================== 结果展示 ====================

    def _refresh_result_display(self):
        """刷新校对结果展示"""
        # 结果文本
        lines = []
        for i, v in enumerate(self._validated_results, 1):
            ref = v.standard_ref
            sr = v.search_result
            rp = v.replacement_info

            name_part = f"  {ref.name}" if ref.name else ""

            if sr is None:
                status_tag = "[?] 未确认"
            elif sr.status.value == "现行":
                status_tag = "[✓] 现行"
            elif sr.status.value in ("作废", "废止"):
                status_tag = "[✗] 已过期"
                if rp and rp.replacement_number:
                    status_tag += f"  → 替代: {rp.replacement_number}"
                    if rp.replacement_name:
                        status_tag += f" {rp.replacement_name}"
            elif sr.status.value == "即将实施":
                status_tag = "[~] 即将实施"
            else:
                status_tag = f"[?] {sr.status.value}"

            lines.append(f"{i:>3}. {ref.number}{name_part}    {status_tag}")

        total = len(self._parsed_standards)
        checked = len(self._validated_results)
        header_text = f"已检查 {checked}/{total} 条标准:\n\n"
        self._show_result_text(header_text + "\n".join(lines))

        # 详细信息表格
        self._refresh_detail_table()

    def _show_result_text(self, text):
        """在结果文本框中显示带颜色的文本"""
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")

        # 解析文本，为不同状态添加颜色标签
        for line in text.split("\n"):
            if "[✓] 现行" in line:
                # 绿色
                self.result_box.insert("end", line + "\n", "valid")
            elif "[✗] 已过期" in line:
                # 红色
                self.result_box.insert("end", line + "\n", "expired")
            elif "[~] 即将实施" in line:
                # 橙色
                self.result_box.insert("end", line + "\n", "upcoming")
            elif "[?]" in line:
                # 灰色
                self.result_box.insert("end", line + "\n", "unknown")
            else:
                self.result_box.insert("end", line + "\n")

        # 配置标签颜色
        self.result_box.tag_config("valid", foreground=self.SUCCESS)
        self.result_box.tag_config("expired", foreground=self.DANGER)
        self.result_box.tag_config("upcoming", foreground=self.WARNING)
        self.result_box.tag_config("unknown", foreground="gray55")
        self.result_box.configure(state="disabled")

    def _refresh_detail_table(self):
        """刷新详细信息表格"""
        # 清空
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        # 表头
        header = ctk.CTkFrame(self.detail_frame, fg_color="gray25", height=32)
        header.pack(fill="x", pady=(0, 2))
        header.pack_propagate(False)

        cols = [
            ("序号", 40),
            ("标准编号", 140),
            ("名称", 200),
            ("状态", 70),
            ("修正编号", 140),
            ("来源", 100),
        ]
        for name, width in cols:
            ctk.CTkLabel(
                header, text=name, width=width, font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
            ).pack(side="left", padx=(4, 2))

        # 数据行
        for i, v in enumerate(self._validated_results, 1):
            ref = v.standard_ref
            sr = v.search_result
            rp = v.replacement_info

            # 状态和颜色
            if sr is None:
                status_text = "未确认"
                row_color = "gray55"
            elif sr.status.value == "现行":
                status_text = "现行"
                row_color = self.SUCCESS
            elif sr.status.value in ("作废", "废止"):
                status_text = "已过期"
                row_color = self.DANGER
            else:
                status_text = sr.status.value
                row_color = self.WARNING

            replacement_text = ""
            if rp:
                if rp.replacement_number:
                    replacement_text = rp.replacement_number
                    if rp.replacement_name:
                        replacement_text += f" {rp.replacement_name}"
                elif rp.replacement_notes:
                    replacement_text = rp.replacement_notes[:30]

            source = sr.csres_number if sr else ""

            row = ctk.CTkFrame(self.detail_frame, fg_color="transparent", height=28)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=str(i), width=40, font=ctk.CTkFont(size=11), anchor="w").pack(
                side="left", padx=(4, 2)
            )
            ctk.CTkLabel(
                row, text=ref.number, width=140, font=ctk.CTkFont(size=11), anchor="w"
            ).pack(side="left", padx=2)
            ctk.CTkLabel(
                row, text=ref.name or "(无)", width=200, font=ctk.CTkFont(size=11), anchor="w"
            ).pack(side="left", padx=2)
            ctk.CTkLabel(
                row,
                text=status_text,
                width=70,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=row_color,
                anchor="w",
            ).pack(side="left", padx=2)
            ctk.CTkLabel(
                row,
                text=replacement_text,
                width=140,
                font=ctk.CTkFont(size=11),
                text_color=self.DANGER if replacement_text else "gray55",
                anchor="w",
            ).pack(side="left", padx=2)
            ctk.CTkLabel(
                row,
                text=source,
                width=100,
                font=ctk.CTkFont(size=10),
                text_color="gray55",
                anchor="w",
            ).pack(side="left", padx=2)

    # ==================== 纠正文本生成 ====================

    def _generate_corrected_text(self):
        """生成纠正后的完整文本"""
        original = self.text_input.get("1.0", "end-1c").strip()
        if not original or not self._validated_results:
            return

        # 构建替换映射
        corrections = {}
        for v in self._validated_results:
            ref = v.standard_ref
            rp = v.replacement_info
            if rp and rp.replacement_number:
                corrections[ref.number] = rp.replacement_number

        # 在原始文本中做替换
        corrected = original
        correction_log = []

        for old_number, new_number in corrections.items():
            if old_number in corrected:
                corrected = corrected.replace(old_number, new_number)
                # 查找对应的名称
                old_name = ""
                new_name = ""
                for v in self._validated_results:
                    if v.standard_ref.number == old_number:
                        old_name = v.standard_ref.name
                        if v.replacement_info and v.replacement_info.replacement_name:
                            new_name = v.replacement_info.replacement_name
                        break
                correction_log.append(f"  {old_number} {old_name}  →  {new_number} {new_name}")

        self._corrected_text = corrected

        # 显示纠正文本
        self.corrected_box.configure(state="normal")
        self.corrected_box.delete("1.0", "end")

        if correction_log:
            self.corrected_box.insert("end", f"=== 共纠正 {len(corrections)} 条标准编号 ===\n\n")
            for log_line in correction_log:
                self.corrected_box.insert("end", log_line + "\n", "correction")
            self.corrected_box.tag_config("correction", foreground=self.DANGER)
            self.corrected_box.insert("end", "\n" + "=" * 50 + "\n\n")

        self.corrected_box.insert("end", corrected)
        self.corrected_box.configure(state="disabled")

    def _copy_corrected_text(self):
        """复制纠正文本到剪贴板"""
        if not self._corrected_text:
            messagebox.showinfo("提示", "暂无纠正文本，请先执行校对")
            return
        self.clipboard_clear()
        self.clipboard_append(self._corrected_text)
        self.status_label.configure(text="纠正结果已复制到剪贴板")

    # ==================== 辅助方法 ====================

    def _poll_log_queue(self):
        while True:
            try:
                level, msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            # 静默处理（校对窗口不需要详细日志）
        self.after(200, self._poll_log_queue)

    def _clear_result_box(self):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.configure(state="disabled")

    def _clear_detail_frame(self):
        for w in self.detail_frame.winfo_children():
            w.destroy()

    def _clear_corrected_box(self):
        self.corrected_box.configure(state="normal")
        self.corrected_box.delete("1.0", "end")
        self.corrected_box.configure(state="disabled")

    def _on_close(self):
        if self.is_running:
            self._cancel_requested = True
        try:
            self.destroy()
        except Exception:
            pass
