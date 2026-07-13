"""
工程建设标准有效性检查工具 - PySide6 GUI

基于 PySide6 的现代化桌面界面（纯文本输入模式）。
支持 PyInstaller 打包为 EXE。
"""

import json
import logging
import os
import queue
import sys
import threading

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# 确保能导入项目其他模块
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import (
    DEFAULT_OUTPUT_DIR,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
)
from models import StandardStatus, ValidatedStandard
from report_generator import generate_report, save_report
from standard_parser import parse_standards_from_text
from utils import RateLimiter, setup_logging
from web_scraper import fetch_replacement_info, search_standard

# ==================== 自定义日志 Handler ====================


class QueueLogHandler(logging.Handler):
    """将日志消息放入队列，由主线程安全地显示到 UI"""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        msg = self.format(record)
        level = record.levelname
        self.log_queue.put((level, msg))


# ==================== 主窗口 ====================


class StandardCheckerMainWindow(QMainWindow):
    """工程建设标准有效性检查工具 - 主窗口"""

    # 配色
    PRIMARY = "#0d9488"
    PRIMARY_HOVER = "#0f766e"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    DANGER = "#dc2626"
    SURFACE = "#16213e"
    BG = "#1a1a2e"
    TEXT = "#e0e0e0"
    TEXT_SECONDARY = "#888888"

    def __init__(self):
        super().__init__()

        # 窗口设置
        self.setWindowTitle("工程建设标准有效性检查工具")
        self.setMinimumSize(920, 720)
        self.resize(1060, 860)

        # 状态
        self.is_running = False
        self._cancel_requested = False
        self.log_queue = queue.Queue()
        self.report_path = ""
        self._finish_success = False

        # 路径
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            self._default_output = os.path.join(exe_dir, "output")
        else:
            self._default_output = os.path.abspath(DEFAULT_OUTPUT_DIR)

        # 中央 widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # 构建界面
        self._build_header(main_layout)
        self._build_text_input(main_layout)
        self._build_params(main_layout)
        self._build_controls(main_layout)
        self._build_progress(main_layout)
        self._build_tabs(main_layout)

        # 定时检查日志队列
        self._log_timer = QTimer()
        self._log_timer.timeout.connect(self._poll_log_queue)
        self._log_timer.start(100)

        # 应用样式
        self._apply_style()

    # ==================== UI 构建 ====================

    def _apply_style(self):
        """应用 QSS 样式表"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.BG};
                color: {self.TEXT};
            }}
            QWidget {{
                background-color: {self.BG};
                color: {self.TEXT};
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 13px;
            }}
            QFrame {{
                background-color: {self.SURFACE};
                border: 1px solid #0f3460;
                border-radius: 10px;
            }}
            QTextEdit {{
                background-color: #0f0f23;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 6px;
                color: #d4d4d4;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 13px;
                selection-background-color: {self.PRIMARY};
            }}
            QLineEdit {{
                background-color: #0f0f23;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 4px 8px;
                color: {self.TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {self.PRIMARY};
            }}
            QPushButton {{
                background-color: #333;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px 14px;
                color: {self.TEXT};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #444;
                border: 1px solid {self.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: #222;
            }}
            QPushButton:disabled {{
                background-color: #222;
                color: #666;
                border: 1px solid #333;
            }}
            QProgressBar {{
                background-color: #0f0f23;
                border: none;
                border-radius: 3px;
                height: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {self.PRIMARY};
                border-radius: 3px;
            }}
            QTabWidget::pane {{
                border: 1px solid #0f3460;
                border-radius: 8px;
                background-color: {self.SURFACE};
                margin-top: 4px;
            }}
            QTabBar::tab {{
                background-color: {self.BG};
                color: #999;
                border: none;
                padding: 8px 18px;
                border-radius: 6px 6px 0 0;
                margin-right: 2px;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.PRIMARY};
                color: white;
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #333;
                color: {self.TEXT};
            }}
            QCheckBox {{
                spacing: 6px;
                color: {self.TEXT};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #555;
                background-color: #0f0f23;
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.PRIMARY};
                border: 1px solid {self.PRIMARY};
            }}
            QLabel {{
                color: {self.TEXT};
            }}
            QScrollBar:vertical {{
                background-color: {self.BG};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #444;
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #666;
            }}
        """)

    def _build_header(self, parent_layout):
        """构建标题栏"""
        header = QFrame()
        header.setFixedHeight(68)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.PRIMARY}, stop:1 #0f3460);
                border: none;
                border-radius: 10px;
            }}
        """)

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 10, 20, 10)

        # 左侧标题
        title_label = QLabel("工程建设标准有效性检查工具")
        title_label.setStyleSheet("""
            QLabel {{
                color: white;
                font-size: 22px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)
        h_layout.addWidget(title_label)

        h_layout.addStretch()

        subtitle_label = QLabel("文本输入 · 网站查询 · 替代检测 · 报告生成")
        subtitle_label.setStyleSheet("""
            QLabel {{
                color: rgba(255,255,255,0.75);
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        h_layout.addWidget(subtitle_label)
        h_layout.addStretch()

        # 右侧占位（主题按钮暂隐藏）
        h_layout.addStretch()

        parent_layout.addWidget(header)

    def _build_text_input(self, parent_layout):
        """构建标准列表输入区"""
        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 14)
        card_layout.setSpacing(6)

        # 标题行
        title_row = QHBoxLayout()
        title_label = QLabel("标准列表输入")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        title_row.addWidget(title_label)
        title_row.addStretch()
        self.line_count_label = QLabel("")
        self.line_count_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 12px;")
        title_row.addWidget(self.line_count_label)
        card_layout.addLayout(title_row)

        # 格式提示
        hint = QLabel(
            "每行一条：编号 + 名称（如  GB 50016-2014 建筑设计防火规范）  支持逗号、空格分隔多条"
        )
        hint.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)

        # 文本框
        self.text_input_box = QTextEdit()
        self.text_input_box.setFixedHeight(175)
        self.text_input_box.setFont(QFont("Consolas", 13))
        placeholder = (
            "GB 50016-2014 建筑设计防火规范\n"
            "GB/T 50352-2019 民用建筑设计统一标准\n"
            "JGJ/T 3-2010 高层建筑混凝土结构技术规程\n"
            "GB 50222-2017 建筑内部装修设计防火规范"
        )
        self.text_input_box.setPlainText(placeholder)
        self.text_input_box.textChanged.connect(self._on_text_changed)
        self._on_text_changed()
        card_layout.addWidget(self.text_input_box)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        btn_import = QPushButton("从文件导入")
        btn_import.setFixedHeight(32)
        btn_import.clicked.connect(self._import_from_file)
        toolbar.addWidget(btn_import)

        btn_paste = QPushButton("从剪贴板粘贴")
        btn_paste.setFixedHeight(32)
        btn_paste.clicked.connect(self._paste_from_clipboard)
        toolbar.addWidget(btn_paste)

        btn_clear = QPushButton("清空内容")
        btn_clear.setFixedHeight(32)
        btn_clear.setStyleSheet(f"""
            QPushButton:hover {{
                background-color: #7f1d1d;
                border: 1px solid {self.DANGER};
            }}
        """)
        btn_clear.clicked.connect(self._clear_text_input)
        toolbar.addWidget(btn_clear)

        toolbar.addStretch()

        btn_preview = QPushButton("解析预览")
        btn_preview.setFixedHeight(32)
        btn_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PRIMARY};
                border: none;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 0 16px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {self.PRIMARY_HOVER};
            }}
        """)
        btn_preview.clicked.connect(self._preview_parse)
        toolbar.addWidget(btn_preview)

        card_layout.addLayout(toolbar)
        parent_layout.addWidget(card)

    def _build_params(self, parent_layout):
        """构建参数配置区"""
        card = QFrame()
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(10)

        # 输出目录
        label_out = QLabel("输出目录:")
        label_out.setFixedWidth(72)
        card_layout.addWidget(label_out)

        self.output_edit = QLineEdit(self._default_output)
        self.output_edit.setFixedHeight(34)
        card_layout.addWidget(self.output_edit)

        btn_browse = QPushButton("浏览")
        btn_browse.setFixedHeight(34)
        btn_browse.setFixedWidth(60)
        btn_browse.clicked.connect(self._browse_output)
        card_layout.addWidget(btn_browse)

        card_layout.addSpacing(20)

        # 请求间隔
        label_delay = QLabel("请求间隔:")
        label_delay.setFixedWidth(72)
        card_layout.addWidget(label_delay)

        self.delay_min_edit = QLineEdit(str(int(REQUEST_DELAY_MIN)))
        self.delay_min_edit.setFixedWidth(40)
        self.delay_min_edit.setFixedHeight(34)
        card_layout.addWidget(self.delay_min_edit)

        label_tilde = QLabel("~")
        label_tilde.setFixedWidth(14)
        card_layout.addWidget(label_tilde)

        self.delay_max_edit = QLineEdit(str(int(REQUEST_DELAY_MAX)))
        self.delay_max_edit.setFixedWidth(40)
        self.delay_max_edit.setFixedHeight(34)
        card_layout.addWidget(self.delay_max_edit)

        label_sec = QLabel("秒")
        label_sec.setFixedWidth(22)
        card_layout.addWidget(label_sec)

        card_layout.addSpacing(20)

        # 调试模式
        self.debug_check = QCheckBox("调试模式")
        card_layout.addWidget(self.debug_check)

        card_layout.addStretch()
        parent_layout.addWidget(card)

    def _build_controls(self, parent_layout):
        """构建控制按钮栏"""
        bar = QHBoxLayout()
        bar.setSpacing(10)

        # 开始检查
        self.run_btn = QPushButton("▶  开始检查")
        self.run_btn.setFixedHeight(46)
        self.run_btn.setFixedWidth(160)
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PRIMARY};
                border: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {self.PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
        """)
        self.run_btn.clicked.connect(self._on_start)
        bar.addWidget(self.run_btn)

        # 规范校对
        self.proofread_btn = QPushButton("规范校对")
        self.proofread_btn.setFixedHeight(46)
        self.proofread_btn.setFixedWidth(110)
        self.proofread_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {self.PRIMARY};
                color: {self.PRIMARY};
                font-size: 14px;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: rgba(13,148,136,0.15);
            }}
        """)
        self.proofread_btn.clicked.connect(self._open_proofread_window)
        bar.addWidget(self.proofread_btn)

        # 停止
        self.stop_btn = QPushButton("■  停止")
        self.stop_btn.setFixedHeight(46)
        self.stop_btn.setFixedWidth(100)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.DANGER};
                border: none;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: #b91c1c;
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
        """)
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setEnabled(False)
        bar.addWidget(self.stop_btn)

        # 打开报告
        self.open_btn = QPushButton("打开报告")
        self.open_btn.setFixedHeight(46)
        self.open_btn.setFixedWidth(110)
        self.open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #333;
                border: 1px solid #555;
                color: {self.TEXT};
                font-size: 14px;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: #444;
                border: 1px solid {self.PRIMARY};
            }}
            QPushButton:disabled {{
                background-color: #222;
                color: #666;
                border: 1px solid #333;
            }}
        """)
        self.open_btn.clicked.connect(self._open_report)
        self.open_btn.setEnabled(False)
        bar.addWidget(self.open_btn)

        bar.addStretch()

        # 统计标签
        self.stats_label = QLabel("就绪")
        self.stats_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 13px;")
        bar.addWidget(self.stats_label)

        parent_layout.addLayout(bar)

    def _build_progress(self, parent_layout):
        """构建进度条"""
        self.progress = QProgressBar()
        self.progress.setFixedHeight(5)
        self.progress.setRange(0, 0)  # indeterminate by default
        self.progress.setTextVisible(False)
        parent_layout.addWidget(self.progress)

    def _build_tabs(self, parent_layout):
        """构建标签页"""
        self.tab_widget = QTabWidget()

        # 运行日志 Tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 12))
        self.tab_widget.addTab(self.log_text, "运行日志")

        # 解析结果 Tab
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Microsoft YaHei", 12))
        self.tab_widget.addTab(self.result_text, "解析结果")

        # 报告预览 Tab
        self.report_text_widget = QTextEdit()
        self.report_text_widget.setReadOnly(True)
        self.report_text_widget.setFont(QFont("Microsoft YaHei", 12))
        self.tab_widget.addTab(self.report_text_widget, "报告预览")

        parent_layout.addWidget(self.tab_widget)

    # ==================== 事件处理 ====================

    def _browse_output(self):
        """选择输出目录"""
        path = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_edit.text())
        if path:
            self.output_edit.setText(path)

    def _on_text_changed(self):
        """文本变化时更新行数统计"""
        text = self.text_input_box.toPlainText()
        lines = [l for l in text.split("\n") if l.strip()]
        self.line_count_label.setText(f"{len(lines)} 行有效内容")

    def _import_from_file(self):
        """从文本文件导入标准列表"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择标准列表文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
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
                QMessageBox.critical(self, "错误", f"无法读取文件:\n{e}")
                return

        current = self.text_input_box.toPlainText().strip()
        if current:
            self.text_input_box.append(content)
        else:
            self.text_input_box.setPlainText(content)
        self._on_text_changed()

    def _paste_from_clipboard(self):
        """从剪贴板粘贴内容"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            QMessageBox.information(self, "提示", "剪贴板为空")
            return
        self.text_input_box.setPlainText(text)
        self._on_text_changed()

    def _clear_text_input(self):
        """清空文本输入框"""
        self.text_input_box.clear()
        self._on_text_changed()

    def _open_proofread_window(self):
        """打开规范编号校对窗口"""
        try:
            from proofread_window_pyside6 import ProofreadWindowPySide6

            self.proofread_window = ProofreadWindowPySide6(self)
            self.proofread_window.show()
        except ImportError:
            QMessageBox.warning(self, "提示", "proofread_window_pyside6.py 未找到，暂不可用")

    def _preview_parse(self):
        """预览解析结果"""
        text = self.text_input_box.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先在文本框中输入标准列表")
            return

        standards = parse_standards_from_text(text)
        if not standards:
            QMessageBox.warning(
                self,
                "解析结果",
                "未能从文本中解析出任何标准编号。\n\n"
                "请确保每行至少包含一个标准编号，如:\n"
                "GB 50016-2014 建筑设计防火规范",
            )
            return

        lines = []
        for i, ref in enumerate(standards, 1):
            name_part = f"  {ref.name}" if ref.name else "  (未识别名称)"
            lines.append(f"{i:>3}. {ref.number}{name_part}")

        self.result_text.setPlainText(f"共解析出 {len(standards)} 条标准:\n\n" + "\n".join(lines))
        self.tab_widget.setCurrentIndex(1)  # 切换到解析结果 Tab

    def _on_start(self):
        """开始执行检查流程"""
        output_dir = self.output_edit.text().strip()
        os.makedirs(output_dir, exist_ok=True)

        text = self.text_input_box.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先在文本框中粘贴标准列表")
            return

        # 锁定 UI
        self.is_running = True
        self._cancel_requested = False
        self.run_btn.setEnabled(False)
        self.run_btn.setText("检查中...")
        self.stop_btn.setEnabled(True)
        self.open_btn.setEnabled(False)
        self.progress.setRange(0, 0)  # indeterminate
        self._update_stats("正在处理...")

        # 清空日志和结果
        self.log_text.clear()
        self.result_text.clear()
        self.report_text_widget.clear()
        self.report_path = ""

        # 切换到日志 Tab
        self.tab_widget.setCurrentIndex(0)

        # 缓存 UI 控件值（后台线程不可直接读取 Qt 控件）
        self._debug_checked = self.debug_check.isChecked()
        self._delay_min_text = self.delay_min_edit.text()
        self._delay_max_text = self.delay_max_edit.text()

        # 后台运行
        thread = threading.Thread(
            target=self._run_pipeline,
            args=(output_dir, text),
            daemon=True,
        )
        thread.start()

    def _on_stop(self):
        """请求停止"""
        self._cancel_requested = True
        self.stop_btn.setEnabled(False)
        self._append_log("WARNING", "正在停止...（当前请求完成后停止）")

    def _open_report(self):
        """打开生成的报告文件"""
        if self.report_path and os.path.exists(self.report_path):
            os.startfile(self.report_path)

    # ==================== 后台流水线 ====================

    def _run_pipeline(self, output_dir, text_input):
        """在后台线程中运行完整检查流程"""
        try:
            logger = setup_logging(output_dir, self._debug_checked)
            log_handler = QueueLogHandler(self.log_queue)
            log_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
            log_handler.setLevel(logging.DEBUG if self._debug_checked else logging.INFO)
            logger.addHandler(log_handler)

            logger.info("=" * 55)
            logger.info("  工程建设标准有效性检查工具")
            logger.info("=" * 55)

            delay_min = float(self._delay_min_text)
            delay_max = float(self._delay_max_text)

            # ===== 阶段1: 解析标准文本 =====
            logger.info("[阶段1/2] 解析标准文本...")
            standards = parse_standards_from_text(text_input)

            if not standards:
                logger.error("未能从文本中解析出任何标准编号")
                self._finish(False)
                return

            logger.info(f"文本解析: {len(standards)} 条标准")

            # 显示解析结果
            result_lines = []
            for i, ref in enumerate(standards, 1):
                result_lines.append(f"{i:>3}. {ref.number}  {ref.name}")
            QTimer.singleShot(0, lambda: self.result_text.setPlainText("\n".join(result_lines)))
            self._update_stats(f"解析 {len(standards)} 条标准")

            # 保存缓存
            self._save_cache(standards, output_dir)

            # ===== 阶段2: 网站查询 =====
            logger.info("[阶段2/2] 查询 csres.com ...")

            validated = self._validate_standards(standards, delay_min, delay_max, logger)

            if self._cancel_requested:
                logger.warning("用户取消")
                self._finish(False)
                return

            # ===== 生成报告 =====
            logger.info("")
            logger.info("生成报告...")
            report = generate_report(validated, ["文本输入"], len(standards))
            self.report_path = save_report(report, output_dir)

            # 切换到 UI 线程更新报告
            QTimer.singleShot(0, lambda: self.report_text_widget.setPlainText(report))
            QTimer.singleShot(0, lambda: self.tab_widget.setCurrentIndex(2))  # 切换到报告预览 Tab

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
            import traceback

            self.log_queue.put(("ERROR", f"运行出错: {e}"))
            self.log_queue.put(("ERROR", traceback.format_exc()))
            self._finish(False)

    def _validate_standards(self, standards, delay_min, delay_max, logger):
        """带取消支持的批量标准验证"""
        import requests as req_lib

        session = req_lib.Session()
        rate_limiter = RateLimiter(delay_min, delay_max)
        results = []
        total = len(standards)

        for i, ref in enumerate(standards, 1):
            if self._cancel_requested:
                break

            self._update_stats(f"查询: {i}/{total}")
            logger.info(f"[{i}/{total}] 查询: {ref.number} {ref.name}")

            search_result = search_standard(ref, session, rate_limiter)
            replacement_info = None

            if search_result and search_result.status in (
                StandardStatus.ABOLISHED,
                StandardStatus.REPEALED,
            ):
                logger.info(f"  -> {search_result.status.value}，获取替代信息...")
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

    def _finish(self, success: bool):
        """完成后恢复 UI 状态（由后台线程调用）"""
        self.is_running = False
        self._finish_success = success
        # 用 QTimer.singleShot 切回 UI 线程执行
        QTimer.singleShot(0, self._apply_finish_ui)

    def _apply_finish_ui(self):
        """UI 线程中恢复按钮状态"""
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  开始检查")
        self.stop_btn.setEnabled(False)
        self.progress.setRange(0, 1)
        if self._finish_success:
            self.progress.setValue(1)
            self.open_btn.setEnabled(True)
        else:
            self.progress.setValue(0)

    def _save_cache(self, standards, output_dir):
        """保存标准缓存 JSON"""
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

    def _append_log(self, level: str, msg: str):
        """向日志文本框追加一行（支持颜色）"""
        # 颜色映射
        color_map = {
            "INFO": "#94a3b8",
            "WARNING": "#fcd34d",
            "ERROR": "#fca5a5",
            "DEBUG": "#64748b",
            "SUCCESS": "#6ee7b7",
        }
        color = QColor(color_map.get(level, "#94a3b8"))

        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

        fmt = cursor.charFormat()
        fmt.setForeground(color)
        cursor.insertText(msg + "\n", fmt)
        self.log_text.ensureCursorVisible()

    def _update_stats(self, text: str):
        """线程安全地更新统计标签"""
        QTimer.singleShot(0, lambda: self.stats_label.setText(text))

    def closeEvent(self, event):
        """关闭窗口时停止后台线程"""
        if self.is_running:
            self._cancel_requested = True
        event.accept()


# ==================== 启动入口 ====================


def launch():
    """启动 PySide6 GUI"""
    app = QApplication([])
    app.setStyle("Fusion")
    window = StandardCheckerMainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch()
