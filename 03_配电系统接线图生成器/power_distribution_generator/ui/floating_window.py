"""
悬浮窗主界面

参照《氛围化编程指令书_配电系统图生成器.md》第5章全部UI规范。

实现：
- 5.1：置顶半透明悬浮窗，可拖动，可调整大小
- 5.2：完整界面结构（文件选择、柜信息、回路切换、参数编辑、操作按钮、状态栏）
- 5.3：所有交互行为
- 5.4：300ms防抖机制
- 8.1：CAD连接状态感知
- 8.2：图块插入渐入效果
- 8.3：错误静默处理
"""

import os
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QTabBar,
    QFileDialog, QMessageBox, QScrollArea, QFormLayout,
    QComboBox, QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QFont

from models import PanelData
from excel_reader import read_panel_from_excel
from ui.circuit_editor import CircuitEditor
from ui.status_bar import StatusBar, CADConnectionMonitor
from calc_engine import calculate_circuit
from code_mapper import CodeMapper
from cad.cad_driver import CADDriver
from cad.block_manager import (
    get_block_attributes, detect_attribute_changes,
    update_sync_snapshot, block_file_exists, get_block_dwg_path,
)
from cad.busbar_drawer import BusbarDrawer

logger = logging.getLogger(__name__)


class FloatingWindow(QWidget):
    """配电系统图生成器悬浮窗主界面

    参照《氛围化编程指令书_配电系统图生成器.md》第5章的完整UI实现。

    Signals:
        parameter_changed(): 参数变更信号
        generate_requested(): 生成系统图请求
        pick_point_requested(): 指定基准点请求
    """

    generate_requested = Signal()
    pick_point_requested = Signal()

    # 自定义标题栏可拖动
    class TitleBar(QWidget):
        """自定义标题栏，可拖动移动窗口，带CAD连接状态指示灯"""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent = parent
            self.drag_pos = QPoint()
            self._cad_connected = False
            self._setup_ui()

        def _setup_ui(self):
            self.setFixedHeight(32)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(8, 4, 4, 4)

            title_label = QLabel("☰ 配电系统图生成器")
            title_label.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #333;"
            )
            layout.addWidget(title_label)
            layout.addStretch()

            # CAD连接状态指示灯按钮
            self.cad_led = QPushButton()
            self.cad_led.setFixedSize(18, 18)
            self.cad_led.setToolTip("未连接AutoCAD")
            self.cad_led.setStyleSheet("""
                QPushButton {
                    border: none;
                    border-radius: 9px;
                    background: qradialgradient(
                        cx:0.4, cy:0.4, radius:0.5,
                        stop:0 #ffcccc, stop:1 #cc0000
                    );
                }
                QPushButton:hover {
                    border: 2px solid #666;
                }
            """)
            self.cad_led.clicked.connect(self._on_led_clicked)
            layout.addWidget(self.cad_led)

            layout.addSpacing(6)

            # 最小化按钮
            self.min_btn = QPushButton("─")
            self.min_btn.setFixedSize(28, 22)
            self.min_btn.setStyleSheet(
                "QPushButton { border: none; background: transparent; "
                "font-size: 14px; color: #666; }"
                "QPushButton:hover { background: #ddd; }"
            )
            self.min_btn.clicked.connect(self._on_minimize)
            layout.addWidget(self.min_btn)

            # 关闭按钮
            self.close_btn = QPushButton("×")
            self.close_btn.setFixedSize(28, 22)
            self.close_btn.setStyleSheet(
                "QPushButton { border: none; background: transparent; "
                "font-size: 16px; color: #666; }"
                "QPushButton:hover { background: #e81123; color: white; }"
            )
            self.close_btn.clicked.connect(self._on_close)
            layout.addWidget(self.close_btn)

        def set_cad_status(self, connected: bool, version: str = ""):
            """设置CAD连接状态指示灯

            Args:
                connected: 是否已连接
                version: AutoCAD版本号
            """
            self._cad_connected = connected
            if connected:
                self.cad_led.setStyleSheet("""
                    QPushButton {
                        border: none;
                        border-radius: 9px;
                        background: qradialgradient(
                            cx:0.4, cy:0.4, radius:0.5,
                            stop:0 #ccffcc, stop:1 #00cc00
                        );
                    }
                    QPushButton:hover {
                        border: 2px solid #666;
                    }
                """)
                self.cad_led.setToolTip(
                    f"已连接 AutoCAD {version} - 点击检查状态"
                )
            else:
                self.cad_led.setStyleSheet("""
                    QPushButton {
                        border: none;
                        border-radius: 9px;
                        background: qradialgradient(
                            cx:0.4, cy:0.4, radius:0.5,
                            stop:0 #ffcccc, stop:1 #cc0000
                        );
                    }
                    QPushButton:hover {
                        border: 2px solid #666;
                    }
                """)
                self.cad_led.setToolTip("未连接AutoCAD - 请启动AutoCAD")

        def _on_led_clicked(self):
            """点击指示灯显示详细状态"""
            if self.parent and hasattr(self.parent, 'status_bar'):
                if self._cad_connected:
                    self.parent.status_bar.set_warning(
                        "✅ CAD连接正常"
                    )
                else:
                    self.parent.status_bar.set_warning(
                        "⏳ CAD未连接，请先启动AutoCAD"
                    )

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.drag_pos = event.globalPosition().toPoint()
                if self.parent:
                    self.parent.drag_offset = (
                        event.globalPosition().toPoint()
                        - self.parent.frameGeometry().topLeft()
                    )

        def mouseMoveEvent(self, event):
            if event.buttons() == Qt.LeftButton and self.parent:
                self.parent.move(
                    event.globalPosition().toPoint()
                    - self.parent.drag_offset
                )

        def _on_minimize(self):
            if self.parent:
                self.parent.showMinimized()

        def _on_close(self):
            """关闭窗口"""
            QApplication.instance().quit()

    def __init__(self):
        super().__init__()
        # 数据
        self.panels = []
        self.current_panel_index = 0
        self.current_circuit_index = 0

        # CAD组件
        self.cad_driver = CADDriver()
        self.busbar_drawer = BusbarDrawer(self.cad_driver)
        self.code_mapper = CodeMapper()

        # 防抖计时器（第5.4节）
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(300)
        self.debounce_timer.timeout.connect(self._apply_cad_update)

        # 窗口属性（第5.1节）
        self._setup_window()
        self._setup_ui()

        # CAD连接监控（第8.1节）
        self.cad_monitor = CADConnectionMonitor(
            self.cad_driver, self.status_bar
        )
        self.cad_monitor.status_changed.connect(
            self._on_cad_status_changed
        )

        # 立即尝试连接已运行的AutoCAD实例
        if self.cad_driver.connect():
            version = self.cad_driver.get_version()
            self.title_bar.set_cad_status(True, version)
            self.status_bar.set_connected(version)
        else:
            # 初始状态：未连接
            self.title_bar.set_cad_status(False)

        # 加载数据
        self._load_sample_data()

    def _setup_window(self):
        """设置窗口属性（第5.1节）"""
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWindowOpacity(0.92)
        self.resize(480, 720)
        self.setMinimumSize(400, 600)

        # 窗口样式
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QPushButton {
                padding: 6px 16px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f8f8f8;
            }
            QPushButton:hover {
                background: #e8e8e8;
            }
            QPushButton:pressed {
                background: #d8d8d8;
            }
            QPushButton#btn_generate {
                background: #1565c0;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton#btn_generate:hover {
                background: #1976d2;
            }
            QPushButton#btn_pick {
                background: #2e7d32;
                color: white;
                border: none;
            }
            QPushButton#btn_pick:hover {
                background: #388e3c;
            }
            QLineEdit {
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QTabBar::tab {
                padding: 6px 12px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1565c0;
                color: white;
            }
            QTabBar::tab:!selected {
                background: #f0f0f0;
            }
            QLabel {
                font-size: 12px;
            }
        """)

    def _setup_ui(self):
        """构建界面（第5.2节）"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 自定义标题栏
        self.title_bar = self.TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # 内容区
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(6)

        # ---- 文件选择区 ----
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("选择配电系统设计Excel文件...")
        self.file_path.setReadOnly(True)
        file_layout.addWidget(self.file_path)

        self.btn_browse = QPushButton("浏览")
        self.btn_browse.clicked.connect(self._on_browse)
        self.btn_browse.setFixedWidth(60)
        file_layout.addWidget(self.btn_browse)

        self.btn_load = QPushButton("加载")
        self.btn_load.clicked.connect(self._on_load)
        self.btn_load.setFixedWidth(60)
        file_layout.addWidget(self.btn_load)

        content_layout.addLayout(file_layout)

        # ---- 开关柜信息区 ----
        cabinet_layout = QHBoxLayout()

        cabinet_form = QFormLayout()
        cabinet_form.setSpacing(4)

        self.panel_no_combo = QComboBox()
        self.panel_no_combo.currentIndexChanged.connect(
            self._on_panel_changed
        )
        cabinet_form.addRow("开关柜:", self.panel_no_combo)

        self.panel_type_combo = QComboBox()
        self.panel_type_combo.addItems(["抽屉柜", "XL21", "GGD"])
        self.panel_type_combo.currentTextChanged.connect(
            self._on_panel_info_changed
        )
        cabinet_form.addRow("柜型:", self.panel_type_combo)

        self.panel_size_edit = QLineEdit()
        self.panel_size_edit.setPlaceholderText("宽*深*高")
        self.panel_size_edit.textChanged.connect(
            self._on_panel_info_changed
        )
        cabinet_form.addRow("尺寸:", self.panel_size_edit)

        content_layout.addLayout(cabinet_form)

        # ---- 回路切换Tab + 编辑区 ----
        self.circuit_tab = QTabBar()
        self.circuit_tab.setExpanding(False)
        self.circuit_tab.currentChanged.connect(self._on_circuit_tab_changed)

        # 回路编辑区（QScrollArea）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.circuit_editor = CircuitEditor()
        self.circuit_editor.parameter_changed.connect(self._on_parameter_changed)
        self.circuit_editor.usage_changed.connect(self._on_usage_changed)
        scroll.setWidget(self.circuit_editor)

        content_layout.addWidget(self.circuit_tab)
        content_layout.addWidget(scroll, 1)  # stretch=1

        # ---- 操作按钮 ----
        btn_layout = QHBoxLayout()

        self.btn_generate = QPushButton("🔄 生成系统图")
        self.btn_generate.setObjectName("btn_generate")
        self.btn_generate.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.btn_generate)

        self.btn_pick_point = QPushButton("📍 指定基准点")
        self.btn_pick_point.setObjectName("btn_pick")
        self.btn_pick_point.clicked.connect(self._on_pick_point)
        btn_layout.addWidget(self.btn_pick_point)

        content_layout.addLayout(btn_layout)

        # ---- 状态栏 ----
        self.status_bar = StatusBar()
        content_layout.addWidget(self.status_bar)

        main_layout.addWidget(content, 1)

    def _on_cad_status_changed(self, connected: bool):
        """CAD连接状态变化时更新指示灯

        Args:
            connected: 是否已连接
        """
        version = self.cad_driver.get_version() if connected else ""
        self.title_bar.set_cad_status(connected, version)

    def _load_sample_data(self):
        """自动加载示例数据（如果存在）"""
        sample_path = Path(__file__).resolve().parent.parent / "data" / "配电系统设计.xlsx"
        logger.info("检查示例数据: %s | 存在=%s", sample_path, sample_path.exists())
        if sample_path.exists():
            self.file_path.setText(str(sample_path))
            self._on_load()

    def _on_browse(self):
        """浏览选择Excel文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择配电系统设计Excel文件",
            str(Path.home()),
            "Excel Files (*.xlsx *.xls)"
        )
        if path:
            self.file_path.setText(path)

    def _on_load(self):
        """加载Excel文件数据"""
        path = self.file_path.text()
        if not path or not os.path.exists(path):
            self.status_bar.set_warning("文件不存在，请重新选择")
            return

        try:
            logger.info("正在加载Excel: %s", path)
            panels = read_panel_from_excel(path)
            logger.info("加载完成: %d个开关柜", len(panels) if panels else 0)
            if panels:
                for p in panels:
                    logger.info("  柜%s: %d回路", p.panel_no, len(p.circuits))

            if not panels:
                self.status_bar.set_warning("未读取到开关柜数据")
                return

            self.panels = panels
            self.current_panel_index = 0

            # 更新UI
            self._update_cabinet_selector()
            self._update_circuit_tabs()

            total = sum(len(p.circuits) for p in panels)
            self.status_bar.set_circuit_count(total)
            self.status_bar.set_warning("数据已加载")
            self.status_bar.set_warning("")  # 恢复
            # 根据实际CAD连接状态更新状态栏，不盲目设为断开
            if self.cad_driver.is_connected:
                version = self.cad_driver.get_version()
                self.status_bar.set_connected(version)
            else:
                self.status_bar.set_disconnected()

        except Exception as e:
            self.status_bar.set_warning(f"加载失败: {str(e)}")

    def _update_cabinet_selector(self):
        """更新开关柜选择器"""
        self.panel_no_combo.blockSignals(True)
        self.panel_no_combo.clear()
        for panel in self.panels:
            label = f"{panel.panel_no} ({panel.panel_type}) [{len(panel.circuits)}回路]"
            self.panel_no_combo.addItem(label, panel)
        self.panel_no_combo.blockSignals(False)

        if self.panels:
            self.panel_no_combo.setCurrentIndex(0)
            self._load_panel_info(0)

    def _load_panel_info(self, index: int):
        """加载第index个开关柜的信息"""
        if index < 0 or index >= len(self.panels):
            return

        panel = self.panels[index]
        self.panel_type_combo.blockSignals(True)
        self.panel_size_edit.blockSignals(True)

        type_index = self.panel_type_combo.findText(panel.panel_type)
        if type_index >= 0:
            self.panel_type_combo.setCurrentIndex(type_index)
        else:
            self.panel_type_combo.setCurrentText(panel.panel_type)
        self.panel_size_edit.setText(panel.panel_size)

        self.panel_type_combo.blockSignals(False)
        self.panel_size_edit.blockSignals(False)

    def _on_panel_changed(self, index: int):
        """切换开关柜"""
        self.current_panel_index = index
        self._load_panel_info(index)
        self._update_circuit_tabs()

    def _on_panel_info_changed(self):
        """开关柜信息变更"""
        if self.current_panel_index < len(self.panels):
            panel = self.panels[self.current_panel_index]
            panel.panel_type = self.panel_type_combo.currentText()
            panel.panel_size = self.panel_size_edit.text()

    def _update_circuit_tabs(self):
        """更新回路Tab栏"""
        self.circuit_tab.blockSignals(True)
        self.circuit_tab.clear()

        if self.current_panel_index < len(self.panels):
            panel = self.panels[self.current_panel_index]
            for i, circuit in enumerate(panel.circuits):
                label = f"回路{i+1}"
                if circuit.circuit_usage:
                    label += f":{circuit.circuit_usage[:4]}"
                self.circuit_tab.addTab(label)

            if panel.circuits:
                self.circuit_tab.setCurrentIndex(0)
                self._load_circuit_editor(0)

        self.circuit_tab.blockSignals(False)

    def _on_circuit_tab_changed(self, index: int):
        """切换回路Tab"""
        self._load_circuit_editor(index)

    def _load_circuit_editor(self, index: int):
        """加载指定回路的编辑控件"""
        self.current_circuit_index = index

        if self.current_panel_index < len(self.panels):
            panel = self.panels[self.current_panel_index]
            if index < len(panel.circuits):
                circuit = panel.circuits[index]
                logger.debug("加载回路编辑器: panel=%s circuit[%d]=%s pe=%s",
                            panel.panel_no, index, circuit.circuit_usage, circuit.pe_power)
                self.circuit_editor.set_circuit(circuit, panel.panel_type)
            else:
                logger.warning("回路索引越界: index=%d, circuits_count=%d", index, len(panel.circuits))
        else:
            logger.warning("开关柜索引越界: panel_index=%d, panels_count=%d",
                          self.current_panel_index, len(self.panels))

    def _on_usage_changed(self, usage: str):
        """回路用途变更，自动更新回路编号

        （第5.3节第2条）
        """
        if self.current_panel_index < len(self.panels):
            panel = self.panels[self.current_panel_index]
            if self.current_circuit_index < len(panel.circuits):
                circuit = panel.circuits[self.current_circuit_index]

                # 重新生成回路编号
                existing = [c.circuit_no for c in panel.circuits
                           if c != circuit and c.circuit_no]
                circuit.circuit_no = self.code_mapper.generate_circuit_no(
                    usage, panel.panel_no, existing
                )

    def _on_parameter_changed(self):
        """参数变更，启动防抖计时器（第5.4节）

        任何参数变更时触发，300ms内无新操作才执行CAD更新。
        """
        # 先更新内存数据
        self.circuit_editor.get_updated_circuit()

        # 更新Tab标签
        self._refresh_tab_labels()

        # 启动防抖
        self.debounce_timer.start()

    def _refresh_tab_labels(self):
        """刷新回路Tab标签"""
        if self.current_panel_index < len(self.panels):
            panel = self.panels[self.current_panel_index]
            self.circuit_tab.blockSignals(True)
            for i, circuit in enumerate(panel.circuits):
                label = f"回路{i+1}"
                if circuit.circuit_usage:
                    label += f":{circuit.circuit_usage[:4]}"
                self.circuit_tab.setTabText(i, label)
            self.circuit_tab.blockSignals(False)

    def _apply_cad_update(self):
        """防抖到期后，增量更新CAD

        参照《氛围化编程指令书_配电系统图生成器.md》第5.4节和第7.2节。
        """
        if not self.cad_driver.is_connected:
            return

        if self.current_panel_index < len(self.panels):
            panel = self.panels[self.current_panel_index]
            for circuit in panel.circuits:
                if circuit.cad_handle is None:
                    continue

                # 增量判断（第7.2节）
                changed = detect_attribute_changes(circuit)
                if changed:
                    self.cad_driver.update_block_attributes(
                        circuit.cad_handle, changed
                    )
                    update_sync_snapshot(circuit)

    def _on_generate(self):
        """点击"生成系统图"按钮

        在CAD基准点处依次插入所有回路图块+母线（阶段3）。
        """
        if not self.cad_driver.is_connected:
            self.status_bar.set_warning("⚠ 未连接AutoCAD，请先启动CAD")
            return

        if self.current_panel_index >= len(self.panels):
            self.status_bar.set_warning("⚠ 无数据可生成")
            return

        panel = self.panels[self.current_panel_index]
        if panel.base_point is None:
            self.status_bar.set_warning("⚠ 请先指定基准点")
            return

        base = panel.base_point
        generated_count = 0

        for i, circuit in enumerate(panel.circuits):
            # 计算插入点（第4.4节）
            pos = self.busbar_drawer.calculate_circuit_position(base, i)

            # 构建属性字典
            attrs = get_block_attributes(circuit)

            # 确保图块已加载
            block_type = circuit.block_type
            dwg_path = get_block_dwg_path(block_type)

            if block_file_exists(block_type):
                self.cad_driver.ensure_block_loaded(dwg_path, block_type)
            else:
                # DWG不存在时使用临时图块
                self.cad_driver.create_temp_block(block_type)

            # 插入图块（渐入效果，第8.2节）
            handle = self.cad_driver.insert_with_fade_in(
                block_type, pos, attrs
            )

            if handle:
                circuit.cad_handle = handle
                update_sync_snapshot(circuit)
                generated_count += 1

                # 500ms后恢复透明度
                QTimer.singleShot(
                    500,
                    lambda h=handle: self.cad_driver.restore_opacity(h)
                )

        # 绘制母线
        if generated_count > 0 and panel.circuits:
            first_pos = self.busbar_drawer.calculate_circuit_position(base, 0)
            last_pos = self.busbar_drawer.calculate_circuit_position(
                base, len(panel.circuits) - 1
            )

            busbar_y = self.busbar_drawer.calculate_busbar_y(base)
            busbar_start = (first_pos[0], busbar_y, first_pos[2])
            busbar_end = (last_pos[0], busbar_y, last_pos[2])

            handle = self.busbar_drawer.draw_busbar(
                busbar_start, busbar_end, panel.busbar_handle
            )
            if handle:
                panel.busbar_handle = handle

        self.status_bar.set_circuit_count(
            len(panel.circuits), generated_count
        )
        self.status_bar.set_warning(f"✅ 已生成 {generated_count} 个回路")

    def _on_pick_point(self):
        """点击"指定基准点"按钮

        切换到CAD窗口等待用户点击，获取坐标后回填（第6.2节）。
        """
        if not self.cad_driver.is_connected:
            self.status_bar.set_warning("⚠ 未连接AutoCAD，请先启动CAD")
            return

        self.status_bar.set_warning("请在CAD中点击选择基准点...")

        point = self.cad_driver.pick_insertion_point()
        if point:
            if self.current_panel_index < len(self.panels):
                panel = self.panels[self.current_panel_index]
                panel.base_point = point
                self.status_bar.set_warning(
                    f"✅ 基准点已设置: ({point[0]:.0f}, {point[1]:.0f})"
                )
        else:
            self.status_bar.set_warning("⚠ 未选择基准点")
