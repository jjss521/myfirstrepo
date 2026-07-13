"""
工程建设标准有效性检查工具 - GUI界面

基于 customtkinter 的现代化桌面界面（纯文本输入模式）。
支持 PyInstaller 打包为 EXE。
"""

import json
import logging
import os
import queue
import sys
import threading
from tkinter import filedialog, messagebox


def get_base_dir():
    """获取程序根目录（兼容 PyInstaller 打包和开发模式）"""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()

try:
    import customtkinter as ctk
except ImportError:
    import tkinter as tk

    tk.messagebox.showerror(
        "缺少依赖", "未安装 customtkinter，请运行:\n\n  pip install customtkinter"
    )
    sys.exit(1)

# 确保能导入项目其他模块
sys.path.insert(0, BASE_DIR)

from config import (
    DEFAULT_OUTPUT_DIR,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
)
from models import StandardStatus, ValidatedStandard
from report_generator import generate_report, save_report
from standard_parser import parse_standards_from_text
from utils import setup_logging
from web_scraper import fetch_replacement_info, search_standard

# ==================== 自定义日志Handler ====================


class QueueLogHandler(logging.Handler):
    """将日志消息放入队列，由主线程安全地显示到UI"""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        msg = self.format(record)
        level = record.levelname
        self.log_queue.put((level, msg))


# ==================== 主GUI类 ====================


class StandardCheckerApp(ctk.CTk):
    """工程建设标准有效性检查工具 - 主窗口"""

    # ---- 配色方案 ----
    PRIMARY = "#0D9488"  # 主色调 - 青绿
    PRIMARY_HOVER = "#0F766E"
    PRIMARY_LIGHT = "#CCFBF1"
    SURFACE = "gray17"  # 卡片/面板背景
    SURFACE_LIGHT = "gray85"
    TEXT_PRIMARY = "gray90"
    TEXT_SECONDARY = "gray55"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    DANGER_HOVER = "#DC2626"
    BORDER = "gray25"
    TAG_COLORS = {
        "INFO": ("#CBD5E1", "#475569"),
        "WARNING": ("#FCD34D", "#B45309"),
        "ERROR": ("#FCA5A5", "#DC2626"),
        "DEBUG": ("#64748B", "#94A3B8"),
        "SUCCESS": ("#6EE7B7", "#059669"),
    }

    def __init__(self):
        super().__init__()

        # 窗口设置
        self.title("工程建设标准有效性检查工具")
        self.geometry("1060x860")
        self.minsize(920, 720)

        # 主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 路径
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            self._default_output = os.path.join(exe_dir, "output")
        else:
            self._default_output = os.path.abspath(DEFAULT_OUTPUT_DIR)

        # 状态
        self.is_running = False
        self.log_queue = queue.Queue()
        self.report_path = ""

        # 构建界面
        self._build_ui()

        # 定时检查日志队列
        self._poll_log_queue()

    # ==================== UI 构建 ====================

    def _build_ui(self):
        self._build_header()

        # 主内容区 - 使用可滚动容器思路，但这里用 pack 权重分配
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=22, pady=(0, 10))

        # 上半部分：输入区 + 参数
        top_half = ctk.CTkFrame(content, fg_color="transparent")
        top_half.pack(fill="x", pady=(0, 6))

        self._build_text_input(top_half)
        self._build_params(top_half)

        # 控制栏
        self._build_controls(content)
        # 进度条
        self._build_progress(content)
        # 标签页
        self._build_tabs(content)

    # ---- 标题栏 ----

    def _build_header(self):
        header = ctk.CTkFrame(self, height=68, corner_radius=0, fg_color="transparent")
        header.pack(fill="x")
        header.pack_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=24, pady=12)

        ctk.CTkLabel(
            left,
            text="工程建设标准有效性检查工具",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="文本输入 · 网站查询 · 替代检测 · 报告生成",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(2, 0))

        # 右侧：主题切换
        self.theme_btn = ctk.CTkButton(
            header,
            text="☀",
            width=38,
            height=38,
            corner_radius=19,
            fg_color="transparent",
            border_width=1,
            border_color="gray40",
            hover_color="gray30",
            font=ctk.CTkFont(size=16),
            command=self._toggle_theme,
        )
        self.theme_btn.pack(side="right", padx=18, pady=15)

    # ---- 文本输入区 ----

    def _build_text_input(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color=self.BORDER)
        card.pack(fill="x", pady=(10, 8))

        # 标题行
        title_row = ctk.CTkFrame(card, fg_color="transparent")
        title_row.pack(fill="x", padx=18, pady=(14, 0))

        ctk.CTkLabel(
            title_row,
            text="标准列表输入",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left")

        # 行数统计
        self.line_count_label = ctk.CTkLabel(
            title_row,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_SECONDARY,
        )
        self.line_count_label.pack(side="right")

        # 格式提示
        hint = ctk.CTkLabel(
            card,
            text="每行一条：编号 + 名称（如  GB 50016-2014 建筑设计防火规范）  支持逗号、空格分隔多条",
            font=ctk.CTkFont(size=11),
            text_color=self.TEXT_SECONDARY,
        )
        hint.pack(anchor="w", padx=18, pady=(2, 6))

        # 文本框
        self.text_input_box = ctk.CTkTextbox(
            card,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            height=175,
            corner_radius=8,
            border_width=1,
            border_color="gray30",
        )
        self.text_input_box.pack(fill="x", padx=18, pady=(0, 6))

        # 插入占位示例
        placeholder = (
            "GB 50016-2014 建筑设计防火规范\n"
            "GB/T 50352-2019 民用建筑设计统一标准\n"
            "JGJ/T 3-2010 高层建筑混凝土结构技术规程\n"
            "GB 50222-2017 建筑内部装修设计防火规范"
        )
        self.text_input_box.insert("1.0", placeholder)
        self.text_input_box.bind("<KeyRelease>", self._on_text_changed)
        self._on_text_changed(None)  # 初始化行数

        # 工具栏
        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.pack(fill="x", padx=18, pady=(0, 14))

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
            toolbar,
            text="从文件导入",
            width=100,
            command=self._import_from_file,
            **btn_kwargs,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            toolbar,
            text="从剪贴板粘贴",
            width=110,
            command=self._paste_from_clipboard,
            **btn_kwargs,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            toolbar,
            text="清空内容",
            width=85,
            command=self._clear_text_input,
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="gray25",
            hover_color="#7F1D1D",
            border_width=1,
            border_color="gray35",
        ).pack(side="left", padx=(0, 6))

        # 右侧：解析预览
        ctk.CTkButton(
            toolbar,
            text="解析预览",
            width=85,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.PRIMARY,
            hover_color=self.PRIMARY_HOVER,
            corner_radius=6,
            height=32,
            command=self._preview_parse,
        ).pack(side="right")

    # ---- 参数配置 ----

    def _build_params(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color=self.BORDER)
        card.pack(fill="x", pady=(0, 4))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        # 输出目录
        ctk.CTkLabel(inner, text="输出目录:", width=72, anchor="w", font=ctk.CTkFont(size=13)).pack(
            side="left"
        )
        self.output_var = ctk.StringVar(value=self._default_output)
        ctk.CTkEntry(
            inner,
            textvariable=self.output_var,
            height=34,
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(
            inner,
            text="浏览",
            width=60,
            height=34,
            corner_radius=6,
            fg_color="gray25",
            hover_color="gray35",
            border_width=1,
            border_color="gray35",
            font=ctk.CTkFont(size=12),
            command=self._browse_output,
        ).pack(side="left", padx=(0, 28))

        # 请求间隔
        ctk.CTkLabel(inner, text="请求间隔:", width=72, anchor="w", font=ctk.CTkFont(size=13)).pack(
            side="left"
        )
        self.delay_min_var = ctk.IntVar(value=int(REQUEST_DELAY_MIN))
        ctk.CTkEntry(
            inner,
            textvariable=self.delay_min_var,
            width=38,
            height=34,
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(inner, text="~", width=14, font=ctk.CTkFont(size=13)).pack(side="left")
        self.delay_max_var = ctk.IntVar(value=int(REQUEST_DELAY_MAX))
        ctk.CTkEntry(
            inner,
            textvariable=self.delay_max_var,
            width=38,
            height=34,
        ).pack(side="left", padx=(0, 2))
        ctk.CTkLabel(inner, text="秒", width=22, font=ctk.CTkFont(size=13)).pack(
            side="left", padx=(0, 28)
        )

        # 调试模式
        self.debug_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            inner,
            text="调试模式",
            variable=self.debug_var,
            font=ctk.CTkFont(size=13),
        ).pack(side="left")

    # ---- 控制按钮 ----

    def _build_controls(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=8)

        self.run_btn = ctk.CTkButton(
            bar,
            text="▶  开始检查",
            height=46,
            width=160,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=10,
            fg_color=self.PRIMARY,
            hover_color=self.PRIMARY_HOVER,
            command=self._on_start,
        )
        self.run_btn.pack(side="left", padx=(0, 10))

        self.proofread_btn = ctk.CTkButton(
            bar,
            text="规范校对",
            height=46,
            width=110,
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            fg_color="transparent",
            hover_color=self.PRIMARY_HOVER,
            border_width=2,
            border_color=self.PRIMARY,
            text_color=self.PRIMARY,
            command=self._open_proofread_window,
        )
        self.proofread_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            bar,
            text="■  停止",
            height=46,
            width=100,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=10,
            fg_color=self.DANGER,
            hover_color=self.DANGER_HOVER,
            command=self._on_stop,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=(0, 10))

        self.open_btn = ctk.CTkButton(
            bar,
            text="打开报告",
            height=46,
            width=110,
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            fg_color="gray30",
            hover_color="gray40",
            border_width=1,
            border_color="gray40",
            command=self._open_report,
            state="disabled",
        )
        self.open_btn.pack(side="left", padx=(0, 10))

        # 右侧统计标签
        self.stats_label = ctk.CTkLabel(
            bar,
            text="就绪",
            font=ctk.CTkFont(size=13),
            text_color=self.TEXT_SECONDARY,
        )
        self.stats_label.pack(side="right", padx=5)

    # ---- 进度条 ----

    def _build_progress(self, parent):
        self.progress = ctk.CTkProgressBar(parent, height=5, corner_radius=3)
        self.progress.pack(fill="x", pady=(0, 6))
        self.progress.set(0)

    # ---- 标签页 ----

    def _build_tabs(self, parent):
        self.tabview = ctk.CTkTabview(parent, height=280, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, pady=(0, 6))

        # 运行日志
        log_tab = self.tabview.add("运行日志")
        self.log_text = ctk.CTkTextbox(
            log_tab,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            state="disabled",
            corner_radius=6,
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # 解析结果
        result_tab = self.tabview.add("解析结果")
        self.result_text = ctk.CTkTextbox(
            result_tab,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            wrap="word",
            state="disabled",
            corner_radius=6,
        )
        self.result_text.pack(fill="both", expand=True, padx=4, pady=4)

        # 报告预览
        report_tab = self.tabview.add("报告预览")
        self.report_text = ctk.CTkTextbox(
            report_tab,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            wrap="word",
            state="disabled",
            corner_radius=6,
        )
        self.report_text.pack(fill="both", expand=True, padx=4, pady=4)

    # ==================== 事件处理 ====================

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="🌙")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="☀")

    def _browse_output(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_var.set(path)

    def _on_text_changed(self, event):
        """文本变化时更新行数统计"""
        try:
            text = self.text_input_box.get("1.0", "end-1c")
            lines = [l for l in text.split("\n") if l.strip()]
            self.line_count_label.configure(text=f"{len(lines)} 行有效内容")
        except Exception:
            pass

    def _import_from_file(self):
        """从文本文件导入标准列表"""
        path = filedialog.askopenfilename(
            title="选择标准列表文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, encoding="gbk") as f:
                    content = f.read()
            except Exception as e:
                messagebox.showerror("错误", f"无法读取文件:\n{e}")
                return

        # 追加到文本框（如果已有内容则换行后追加）
        current = self.text_input_box.get("1.0", "end-1c").strip()
        if current:
            self.text_input_box.insert("end", "\n" + content)
        else:
            self.text_input_box.delete("1.0", "end")
            self.text_input_box.insert("1.0", content)
        self._on_text_changed(None)

    def _paste_from_clipboard(self):
        """从剪贴板粘贴内容"""
        try:
            clipboard_text = self.clipboard_get()
            if not clipboard_text:
                messagebox.showinfo("提示", "剪贴板为空")
                return
            # 替换当前内容
            self.text_input_box.delete("1.0", "end")
            self.text_input_box.insert("1.0", clipboard_text)
            self._on_text_changed(None)
        except Exception:
            messagebox.showinfo("提示", "剪贴板中没有文本内容")

    def _clear_text_input(self):
        """清空文本输入框"""
        self.text_input_box.delete("1.0", "end")
        self._on_text_changed(None)

    def _open_proofread_window(self):
        """打开规范编号校对窗口"""
        from proofread_window import ProofreadWindow

        ProofreadWindow(self)

    def _preview_parse(self):
        """预览解析结果：解析当前文本中的标准并显示到解析结果Tab"""
        text = self.text_input_box.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("提示", "请先在文本框中输入标准列表")
            return

        standards = parse_standards_from_text(text)
        if not standards:
            messagebox.showwarning(
                "解析结果",
                "未能从文本中解析出任何标准编号。\n\n"
                "请确保每行包含标准编号，如:\n"
                "GB 50016-2014 建筑设计防火规范",
            )
            return

        # 显示结果
        lines = []
        for i, ref in enumerate(standards, 1):
            name_part = f"  {ref.name}" if ref.name else "  (未识别名称)"
            lines.append(f"{i:>3}. {ref.number}{name_part}")

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert(
            "1.0",
            f"共解析出 {len(standards)} 条标准:\n\n" + "\n".join(lines),
        )
        self.result_text.configure(state="disabled")
        self.tabview.set("解析结果")

    def _on_start(self):
        """开始执行检查流程"""
        output_dir = self.output_var.get().strip()
        os.makedirs(output_dir, exist_ok=True)

        # 获取文本框内容
        text = self.text_input_box.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("提示", "请先在文本框中粘贴标准列表")
            return

        # 锁定UI
        self.is_running = True
        self._cancel_requested = False
        self.run_btn.configure(state="disabled", text="检查中...")
        self.stop_btn.configure(state="normal")
        self.open_btn.configure(state="disabled")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.stats_label.configure(text="正在处理...")

        # 清空日志和结果
        self._clear_textbox(self.log_text)
        self._clear_textbox(self.result_text)
        self._clear_textbox(self.report_text)
        self.report_path = ""

        # 切换到日志Tab
        self.tabview.set("运行日志")

        # 后台运行
        thread = threading.Thread(
            target=self._run_pipeline,
            args=(output_dir,),
            kwargs={"text_input": text},
            daemon=True,
        )
        thread.start()

    def _on_stop(self):
        """请求停止"""
        self._cancel_requested = True
        self.stop_btn.configure(state="disabled")
        self._append_log("WARNING", "正在停止...（当前请求完成后停止）")

    def _open_report(self):
        """打开生成的报告文件"""
        if self.report_path and os.path.exists(self.report_path):
            os.startfile(self.report_path)

    # ==================== 后端流水线 ====================

    def _run_pipeline(self, output_dir, text_input=None):
        """在后台线程中运行完整检查流程"""
        try:
            # 设置日志
            logger = setup_logging(output_dir, self.debug_var.get())
            log_handler = QueueLogHandler(self.log_queue)
            log_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            log_handler.setLevel(logging.DEBUG if self.debug_var.get() else logging.INFO)
            logger.addHandler(log_handler)

            logger.info("=" * 55)
            logger.info("  工程建设标准有效性检查工具")
            logger.info("=" * 55)

            delay_min = float(self.delay_min_var.get())
            delay_max = float(self.delay_max_var.get())

            # ===== 阶段1: 解析标准文本 =====
            logger.info("输入方式: 文本输入")
            logger.info(f"输出目录: {output_dir}")
            logger.info("")

            logger.info("[阶段1/2] 解析标准文本...")
            standards = parse_standards_from_text(text_input)
            total_before = len(standards)

            if not standards:
                logger.error("未能从文本中解析出任何标准编号")
                logger.error("请确保每行至少包含一个标准编号，如: GB 50016-2014 建筑设计防火规范")
                self._finish(False)
                return

            logger.info(f"文本解析: {len(standards)} 条标准")
            logger.info("")

            # 显示解析结果
            result_lines = []
            for i, ref in enumerate(standards, 1):
                result_lines.append(f"{i:>3}. {ref.number}  {ref.name}")
            self._update_result_text("\n".join(result_lines))
            self._update_stats(f"解析 {len(standards)} 条标准")

            # 保存缓存
            self._save_cache(standards, output_dir)

            # ===== 阶段2: 网站查询 =====
            logger.info("[阶段2/2] 查询 csres.com ...")

            validated = validate_standards_with_cancel(
                standards,
                delay_min,
                delay_max,
                logger,
                cancel_check=lambda: self._cancel_requested,
                progress_callback=lambda i, t: self._update_stats(f"查询: {i}/{t}"),
            )

            if self._cancel_requested:
                logger.warning("用户取消")
                self._finish(False)
                return

            # ===== 生成报告 =====
            logger.info("")
            logger.info("生成报告...")
            report = generate_report(validated, ["文本输入"], total_before)
            self.report_path = save_report(report, output_dir)
            self._update_report_text(report)
            self.tabview.set("报告预览")

            # 统计
            expired = sum(
                1
                for v in validated
                if v.search_result and v.search_result.status.value in ("作废", "废止")
            )
            active = sum(
                1 for v in validated if v.search_result and v.search_result.status.value == "现行"
            )
            unknown = sum(
                1
                for v in validated
                if v.search_result is None or v.search_result.status.value == "未知"
            )

            logger.info("")
            logger.info("=" * 55)
            logger.info("  处理完成！")
            logger.info(f"  报告: {self.report_path}")
            logger.info(f"  现行有效: {active}  已过期: {expired}  未确认: {unknown}")
            logger.info("=" * 55)
            self._update_stats(f"完成  |  现行: {active}  过期: {expired}  未知: {unknown}")
            self._finish(True)

        except Exception as e:
            self.log_queue.put(("ERROR", f"运行出错: {e}"))
            import traceback

            self.log_queue.put(("ERROR", traceback.format_exc()))
            self._finish(False)

    def _finish(self, success: bool):
        """完成后恢复UI状态（由后台线程调用）"""
        self.is_running = False
        self._finish_success = success
        self.after(0, self._apply_finish_ui)

    def _apply_finish_ui(self):
        self.run_btn.configure(state="normal", text="▶  开始检查")
        self.stop_btn.configure(state="disabled")
        self.progress.stop()
        if self._finish_success:
            self.progress.set(1.0)
            self.open_btn.configure(state="normal")
        else:
            self.progress.set(0)

    def _save_cache(self, standards, output_dir):
        """保存标准缓存JSON"""
        os.makedirs(output_dir, exist_ok=True)
        cache_path = os.path.join(output_dir, "standards_cache.json")
        data = []
        for ref in standards:
            data.append(
                {
                    "number": ref.number,
                    "name": ref.name,
                    "source_files": ref.source_files,
                    "confidence": ref.confidence,
                    "raw_text": ref.raw_text,
                }
            )
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ==================== UI 更新辅助 ====================

    def _poll_log_queue(self):
        """定时检查日志队列并显示"""
        while True:
            try:
                level, msg = self.log_queue.get_nowait()
                self._append_log(level, msg)
            except queue.Empty:
                break
        self.after(100, self._poll_log_queue)

    def _append_log(self, level: str, msg: str):
        """向日志文本框追加一行"""
        self.log_text.configure(state="normal")

        dark_color, light_color = self.TAG_COLORS.get(level, ("#CBD5E1", "#475569"))
        color = dark_color if ctk.get_appearance_mode() == "Dark" else light_color

        self.log_text.insert("end", msg + "\n", level)
        self.log_text.tag_config(level, foreground=color)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_textbox(self, textbox):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.configure(state="disabled")

    def _update_stats(self, text: str):
        self.after(0, lambda: self.stats_label.configure(text=text))

    def _update_result_text(self, text: str):
        def _do():
            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", text)
            self.result_text.configure(state="disabled")

        self.after(0, _do)

    def _update_report_text(self, text: str):
        def _do():
            self.report_text.configure(state="normal")
            self.report_text.delete("1.0", "end")
            self.report_text.insert("1.0", text)
            self.report_text.configure(state="disabled")

        self.after(0, _do)


# ==================== 支持取消的validate_standards ====================


def validate_standards_with_cancel(
    standards,
    delay_min,
    delay_max,
    logger,
    cancel_check=None,
    progress_callback=None,
):
    """带取消支持的批量标准验证"""
    import requests as req_lib

    from utils import RateLimiter

    session = req_lib.Session()
    rate_limiter = RateLimiter(delay_min, delay_max)
    results = []
    total = len(standards)

    for i, ref in enumerate(standards, 1):
        if cancel_check and cancel_check():
            break

        if progress_callback:
            progress_callback(i, total)

        logger.info(f"[{i}/{total}] 查询: {ref.number} {ref.name}")

        search_result = search_standard(ref, session, rate_limiter)
        replacement_info = None

        if search_result and search_result.status in (
            StandardStatus.ABOLISHED,
            StandardStatus.REPEALED,
        ):
            logger.info(f"  -> {search_result.status.value}, 获取替代信息...")
            replacement_info = fetch_replacement_info(
                search_result.detail_url,
                ref.number,
                ref.name,
                session,
                rate_limiter,
            )

        results.append(
            ValidatedStandard(
                standard_ref=ref,
                search_result=search_result,
                replacement_info=replacement_info,
            )
        )

    return results


# ==================== 启动入口 ====================


def launch():
    app = StandardCheckerApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
