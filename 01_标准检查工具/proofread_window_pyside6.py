"""
规范编号校对工具窗口 - PySide6 版本

输入文字 → 识别所有标准编号 → 在线检查有效性 → 自动纠正错误 → 标红记录
"""

import os
import sys
import queue
import logging
import threading

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QProgressBar,
    QTabWidget, QScrollArea, QFrame,
    QMessageBox, QFileDialog, QHBoxLayout, QVBoxLayout,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextCursor, QColor

# 确保能导入项目其他模块
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import REQUEST_DELAY_MIN, REQUEST_DELAY_MAX
from models import StandardStatus, ValidatedStandard
from standard_parser import parse_standards_from_text
from web_scraper import search_standard, fetch_replacement_info
from utils import RateLimiter


# ==================== 自定义日志 Handler ====================

class QueueLogHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        msg = self.format(record)
        level = record.levelname
        self.log_queue.put((level, msg))


# ==================== 校对窗口 ====================

class ProofreadWindowPySide6(QDialog):
    """规范编号校对工具 - PySide6 独立窗口"""

    PRIMARY = "#0d9488"
    PRIMARY_HOVER = "#0f766e"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    DANGER = "#dc2626"
    DANGER_HOVER = "#b91c1c"
    TEXT_SECONDARY = "#888888"
    BG = "#1a1a2e"
    SURFACE = "#16213e"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("规范编号校对工具")
        self.setMinimumSize(800, 600)
        self.resize(980, 760)

        # 状态
        self.is_running = False
        self._cancel_requested = False
        self.log_queue = queue.Queue()
        self._validated_results = []
        self._parsed_standards = []
        self._corrected_text = ""

        # 构建界面
        self._build_ui()

        # 定时检查日志队列
        self._log_timer = QTimer()
        self._log_timer.timeout.connect(self._poll_log_queue)
        self._log_timer.start(200)

        # 居中显示
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(max(0, x), max(0, y))

    # ==================== UI 构建 ====================

    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.BG};
                color: #e0e0e0;
            }}
            QWidget {{
                background-color: {self.BG};
                color: #e0e0e0;
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
                color: #e0e0e0;
            }}
            QScrollArea {{
                background-color: {self.SURFACE};
                border: none;
            }}
            QLabel {{
                color: #e0e0e0;
            }}
        """)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        self._build_header(main_layout)
        self._build_input_area(main_layout)
        self._build_progress(main_layout)
        self._build_tabs(main_layout)
        self._build_status_bar(main_layout)

        self._apply_style()

    def _build_header(self, parent_layout):
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.PRIMARY}, stop:1 #0f3460);
                border: none;
                border-radius: 10px;
            }}
        """)

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(18, 8, 18, 8)

        title = QLabel("规范编号校对工具")
        title.setStyleSheet("""
            QLabel {{
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)
        h_layout.addWidget(title)

        hint = QLabel("  粘贴文本 → 识别编号 → 在线检查 → 自动纠正")
        hint.setStyleSheet("""
            QLabel {{
                color: rgba(255,255,255,0.7);
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        h_layout.addWidget(hint)

        h_layout.addStretch()

        # 图例
        legend = QWidget()
        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(12)

        for text, color in [("■ 有效", self.SUCCESS),
                            ("■ 过期/错误", self.DANGER),
                            ("■ 未确认", self.TEXT_SECONDARY)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent; border: none;")
            legend_layout.addWidget(lbl)

        h_layout.addWidget(legend)
        parent_layout.addWidget(header)

    def _build_input_area(self, parent_layout):
        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(6)

        # 标题行
        title_row = QHBoxLayout()
        title_label = QLabel("输入文本")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_row.addWidget(title_label)
        title_row.addStretch()
        self.line_count_label = QLabel("")
        self.line_count_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 12px;")
        title_row.addWidget(self.line_count_label)
        card_layout.addLayout(title_row)

        # 格式提示
        hint = QLabel("支持换行、分号（; 或 ；）、多个空格、逗号分隔标准编号")
        hint.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)

        # 文本框
        self.text_input = QTextEdit()
        self.text_input.setFixedHeight(130)
        self.text_input.setFont(QFont("Consolas", 13))
        placeholder = (
            "GB 50016-2014 建筑设计防火规范\n"
            "GB/T 50352-2019 民用建筑设计统一标准; JGJ/T 3-2010 高层建筑混凝土结构技术规程\n"
            "GB 50222-2017 建筑内部装修设计防火规范"
        )
        self.text_input.setPlainText(placeholder)
        self.text_input.textChanged.connect(self._on_text_changed)
        self._on_text_changed()
        card_layout.addWidget(self.text_input)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        btn_import = QPushButton("从文件导入")
        btn_import.setFixedHeight(32)
        btn_import.clicked.connect(self._import_file)
        toolbar.addWidget(btn_import)

        btn_paste = QPushButton("从剪贴板粘贴")
        btn_paste.setFixedHeight(32)
        btn_paste.clicked.connect(self._paste_clipboard)
        toolbar.addWidget(btn_paste)

        btn_clear = QPushButton("清空")
        btn_clear.setFixedHeight(32)
        btn_clear.setStyleSheet(f"""
            QPushButton:hover {{
                background-color: #7f1d1d;
                border: 1px solid {self.DANGER};
            }}
        """)
        btn_clear.clicked.connect(self._clear_input)
        toolbar.addWidget(btn_clear)

        toolbar.addStretch()

        # 操作按钮（右侧）
        self.btn_start = QPushButton("开始校对")
        self.btn_start.setFixedHeight(34)
        self.btn_start.setFixedWidth(100)
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PRIMARY};
                border: none;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {self.PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
        """)
        self.btn_start.clicked.connect(self._on_start_proofread)
        toolbar.addWidget(self.btn_start)

        self.btn_parse_only = QPushButton("仅解析")
        self.btn_parse_only.setFixedHeight(34)
        self.btn_parse_only.setFixedWidth(80)
        self.btn_parse_only.setStyleSheet("""
            QPushButton {{
                background-color: #333;
                border: 1px solid #555;
                color: #e0e0e0;
                font-size: 12px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #444;
                border: 1px solid #0d9488;
            }}
        """)
        self.btn_parse_only.clicked.connect(self._on_parse_only)
        toolbar.addWidget(self.btn_parse_only)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setFixedHeight(34)
        self.btn_stop.setFixedWidth(60)
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.DANGER};
                border: none;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {self.DANGER_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
        """)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_stop.setEnabled(False)
        toolbar.addWidget(self.btn_stop)

        card_layout.addLayout(toolbar)
        parent_layout.addWidget(card)

    def _build_progress(self, parent_layout):
        self.progress = QProgressBar()
        self.progress.setFixedHeight(5)
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setTextVisible(False)
        parent_layout.addWidget(self.progress)

    def _build_tabs(self, parent_layout):
        self.tab_widget = QTabWidget()

        # 校对结果 Tab
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setFont(QFont("Microsoft YaHei", 12))
        self.tab_widget.addTab(self.result_box, "校对结果")

        # 详细信息 Tab
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_content = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_content)
        self.detail_layout.setContentsMargins(8, 8, 8, 8)
        self.detail_layout.setSpacing(2)
        self.detail_scroll.setWidget(self.detail_content)
        self.tab_widget.addTab(self.detail_scroll, "详细信息")

        # 纠正文本 Tab
        corrected_widget = QWidget()
        corrected_layout = QVBoxLayout(corrected_widget)
        corrected_layout.setContentsMargins(8, 8, 8, 8)
        corrected_layout.setSpacing(6)

        self.corrected_box = QTextEdit()
        self.corrected_box.setReadOnly(True)
        self.corrected_box.setFont(QFont("Consolas", 12))
        corrected_layout.addWidget(self.corrected_box)

        btn_copy = QPushButton("复制纠正结果")
        btn_copy.setFixedHeight(32)
        btn_copy.setFixedWidth(120)
        btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.PRIMARY};
                border: none;
                color: white;
                font-size: 12px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {self.PRIMARY_HOVER};
            }}
        """)
        btn_copy.clicked.connect(self._copy_corrected_text)
        corrected_layout.addWidget(btn_copy, 0, Qt.AlignRight)

        self.tab_widget.addTab(corrected_widget, "纠正文本")
        parent_layout.addWidget(self.tab_widget)

    def _build_status_bar(self, parent_layout):
        status_bar = QFrame()
        status_bar.setFixedHeight(32)
        status_bar.setStyleSheet("background-color: transparent; border: none;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(4, 0, 4, 0)

        self.status_label = QLabel("就绪 - 请粘贴包含标准编号的文本")
        self.status_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 12px;")
        status_layout.addWidget(self.status_label)

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 12px;")
        status_layout.addWidget(self.stats_label, 0, Qt.AlignRight)

        parent_layout.addWidget(status_bar)

    # ==================== 事件处理 ====================

    def _on_text_changed(self):
        try:
            text = self.text_input.toPlainText()
            entries = []
            for line in text.replace('；', '\n').replace(';', '\n').split('\n'):
                if line.strip():
                    entries.append(line)
            self.line_count_label.setText(f"{len(entries)} 条内容")
        except Exception:
            pass

    def _import_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择文本文件", "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, 'r', encoding='gbk') as f:
                content = f.read()
        current = self.text_input.toPlainText().strip()
        if current:
            self.text_input.append(content)
        else:
            self.text_input.setPlainText(content)
        self._on_text_changed()

    def _paste_clipboard(self):
        try:
            from PySide6.QtGui import QGuiApplication
            text = QGuiApplication.clipboard().text()
            if text:
                self.text_input.setPlainText(text)
                self._on_text_changed()
        except Exception:
            QMessageBox.information(self, "提示", "剪贴板为空")

    def _clear_input(self):
        self.text_input.clear()
        self._on_text_changed()

    def _on_parse_only(self):
        """仅解析标准编号，不做在线查询"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入或粘贴包含标准编号的文本")
            return

        standards = parse_standards_from_text(text)
        if not standards:
            QMessageBox.warning(self, "解析结果", "未能从文本中解析出任何标准编号")
            return

        self._parsed_standards = standards

        lines = []
        for i, ref in enumerate(standards, 1):
            name_part = f"  {ref.name}" if ref.name else "  (未识别名称)"
            lines.append(f"{i:>3}. {ref.number}{name_part}")

        self.result_box.setPlainText(
            f"共解析出 {len(standards)} 条标准（仅解析，未做在线检查）:\n\n"
            + "\n".join(lines)
        )
        self.status_label.setText(f"解析完成: {len(standards)} 条标准")
        self.tab_widget.setCurrentIndex(0)

    def _on_start_proofread(self):
        """开始在线校对"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入或粘贴包含标准编号的文本")
            return

        standards = parse_standards_from_text(text)
        if not standards:
            QMessageBox.warning(self, "解析结果", "未能从文本中解析出任何标准编号")
            return

        self._parsed_standards = standards
        self._validated_results = []
        self._corrected_text = ""

        # 锁定 UI
        self.is_running = True
        self._cancel_requested = False
        self.btn_start.setEnabled(False)
        self.btn_start.setText("校对中...")
        self.btn_parse_only.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setRange(0, 0)
        self.status_label.setText("正在在线校对...")
        self.stats_label.setText(f"共 {len(standards)} 条待查")

        # 清空结果
        self.result_box.clear()
        self._clear_detail_frame()
        self.corrected_box.clear()

        self.tab_widget.setCurrentIndex(0)

        # 后台线程
        thread = threading.Thread(
            target=self._run_proofread_pipeline,
            args=(standards,),
            daemon=True,
        )
        thread.start()

    def _on_stop(self):
        self._cancel_requested = True
        self.btn_stop.setEnabled(False)
        self.status_label.setText("正在停止...")

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
                self._update_stats_safe(f"查询: {i}/{total}")

                search_result = search_standard(ref, session, rate_limiter)
                replacement_info = None

                if search_result and search_result.status in (
                    StandardStatus.ABOLISHED, StandardStatus.REPEALED
                ):
                    self.log_queue.put(("WARNING",
                        f"  → {search_result.status.value}，获取替代信息..."))
                    replacement_info = fetch_replacement_info(
                        search_result.detail_url,
                        ref.number, ref.name,
                        session, rate_limiter,
                    )

                validated = ValidatedStandard(
                    standard_ref=ref,
                    search_result=search_result,
                    replacement_info=replacement_info,
                )
                self._validated_results.append(validated)

                # 切回 UI 线程刷新显示
                QTimer.singleShot(0, self._refresh_result_display)

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
        """完成后恢复 UI（切回 UI 线程）"""
        self.is_running = False
        QTimer.singleShot(0, lambda: self._apply_finish_proofread_ui(success))

    def _apply_finish_proofread_ui(self, success):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("开始校对")
        self.btn_parse_only.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setRange(0, 1)

        if success:
            self.progress.setValue(1)
            expired = sum(1 for v in self._validated_results
                         if v.search_result and v.search_result.status.value in ('作废', '废止'))
            active = sum(1 for v in self._validated_results
                        if v.search_result and v.search_result.status.value == '现行')
            unknown = sum(1 for v in self._validated_results
                         if v.search_result is None or v.search_result.status.value == '未知')
            self.stats_label.setText(
                f"现行: {active}  |  过期: {expired}  |  未确认: {unknown}")
            self.status_label.setText("校对完成")
            self._generate_corrected_text()
        else:
            self.progress.setValue(0)
            self.status_label.setText("校对已停止")

        self._refresh_result_display()

    # ==================== 结果展示 ====================

    def _refresh_result_display(self):
        """刷新校对结果展示"""
        lines = []
        for i, v in enumerate(self._validated_results, 1):
            ref = v.standard_ref
            sr = v.search_result
            rp = v.replacement_info

            name_part = f"  {ref.name}" if ref.name else ""

            if sr is None:
                status_tag = "[?] 未确认"
            elif sr.status.value == '现行':
                status_tag = "[✓] 现行"
            elif sr.status.value in ('作废', '废止'):
                status_tag = "[✗] 已过期"
                if rp and rp.replacement_number:
                    status_tag += f"  → 替代: {rp.replacement_number}"
                    if rp.replacement_name:
                        status_tag += f" {rp.replacement_name}"
            elif sr.status.value == '即将实施':
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
        self.result_box.clear()
        for line in text.split('\n'):
            if '[✓] 现行' in line:
                self._append_colored(self.result_box, line + '\n', self.SUCCESS)
            elif '[✗] 已过期' in line:
                self._append_colored(self.result_box, line + '\n', self.DANGER)
            elif '[~] 即将实施' in line:
                self._append_colored(self.result_box, line + '\n', self.WARNING)
            elif '[?]' in line:
                self._append_colored(self.result_box, line + '\n', self.TEXT_SECONDARY)
            else:
                self.result_box.append(line)

    def _append_colored(self, text_edit, text, color):
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        text_edit.setTextCursor(cursor)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text, fmt)

    def _refresh_detail_table(self):
        """刷新详细信息表格"""
        self._clear_detail_frame()

        # 表头
        header = QFrame()
        header.setFixedHeight(32)
        header.setStyleSheet(f"background-color: #333; border-radius: 4px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(8, 4, 8, 4)
        h_layout.setSpacing(4)

        for name, width in [("序号", 40), ("标准编号", 140), ("名称", 200),
                            ("状态", 70), ("修正编号", 140), ("来源", 100)]:
            lbl = QLabel(name)
            lbl.setFixedWidth(width)
            lbl.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent; border: none;")
            h_layout.addWidget(lbl)

        self.detail_layout.addWidget(header)

        # 数据行
        for i, v in enumerate(self._validated_results, 1):
            ref = v.standard_ref
            sr = v.search_result
            rp = v.replacement_info

            if sr is None:
                status_text = "未确认"
                row_color = self.TEXT_SECONDARY
            elif sr.status.value == '现行':
                status_text = "现行"
                row_color = self.SUCCESS
            elif sr.status.value in ('作废', '废止'):
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

            row = QFrame()
            row.setFixedHeight(28)
            row.setStyleSheet("background-color: transparent; border: none;")
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(8, 2, 8, 2)
            r_layout.setSpacing(4)

            for val, width in [(str(i), 40), (ref.number, 140),
                               (ref.name or "(无)", 200), (status_text, 70),
                               (replacement_text, 140), (source, 100)]:
                lbl = QLabel(str(val))
                lbl.setFixedWidth(width)
                lbl.setStyleSheet(f"font-size: 12px; background: transparent; border: none;")
                if val == status_text:
                    lbl.setStyleSheet(f"color: {row_color}; font-weight: bold; font-size: 12px; background: transparent; border: none;")
                r_layout.addWidget(lbl)

            self.detail_layout.addWidget(row)

        self.detail_layout.addStretch()

    # ==================== 纠正文本生成 ====================

    def _generate_corrected_text(self):
        """生成纠正后的完整文本"""
        original = self.text_input.toPlainText().strip()
        if not original or not self._validated_results:
            return

        corrections = {}
        for v in self._validated_results:
            ref = v.standard_ref
            rp = v.replacement_info
            if rp and rp.replacement_number:
                corrections[ref.number] = rp.replacement_number

        corrected = original
        correction_log = []

        for old_number, new_number in corrections.items():
            if old_number in corrected:
                corrected = corrected.replace(old_number, new_number)
                old_name = ""
                new_name = ""
                for v in self._validated_results:
                    if v.standard_ref.number == old_number:
                        old_name = v.standard_ref.name
                        if v.replacement_info and v.replacement_info.replacement_name:
                            new_name = v.replacement_info.replacement_name
                        break
                correction_log.append(
                    f"  {old_number} {old_name}  →  {new_number} {new_name}")

        self._corrected_text = corrected

        self.corrected_box.clear()
        if correction_log:
            self.corrected_box.append(
                f"=== 共纠正 {len(corrections)} 条标准编号 ===\n"
            )
            for log_line in correction_log:
                self.corrected_box.append(log_line)
            self.corrected_box.append("\n" + "=" * 50 + "\n")

        self.corrected_box.append(corrected)

    def _copy_corrected_text(self):
        """复制纠正文本到剪贴板"""
        if not self._corrected_text:
            QMessageBox.information(self, "提示", "暂无纠正文本，请先执行校对")
            return
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(self._corrected_text)
        self.status_label.setText("纠正结果已复制到剪贴板")

    # ==================== 辅助方法 ====================

    def _poll_log_queue(self):
        """定时检查日志队列并显示（只读队列，不重建定时器）"""
        while True:
            try:
                level, msg = self.log_queue.get_nowait()
            except queue.Empty:
                break

    def _clear_detail_frame(self):
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _update_stats_safe(self, text):
        QTimer.singleShot(0, lambda t=text: self.stats_label.setText(t))

    def closeEvent(self, event):
        if self.is_running:
            self._cancel_requested = True
        event.accept()
