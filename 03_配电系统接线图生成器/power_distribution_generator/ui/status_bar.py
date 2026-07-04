"""
状态栏组件

参照《氛围化编程指令书_配电系统图生成器.md》第5.2节（界面底部状态栏）
和第8.1节（CAD连接状态感知）。

提供：
- CAD连接状态实时显示
- 回路数统计
- 错误微弱提示（不弹窗）
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QColor, QPalette


class StatusBar(QWidget):
    """悬浮窗底部状态栏组件

    包含：
    - CAD连接状态指示灯和文字
    - 回路统计信息

    Signals:
        connection_status_changed(bool): 连接状态变化信号
    """

    connection_status_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(12)

        # CAD连接状态
        self.status_icon = QLabel("⏳")
        self.status_icon.setFixedWidth(20)
        layout.addWidget(self.status_icon)

        self.status_text = QLabel("等待AutoCAD...")
        self.status_text.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.status_text)

        layout.addStretch()

        # 回路统计
        self.circuit_count_label = QLabel("回路数: 0")
        self.circuit_count_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.circuit_count_label)

        self.generated_count_label = QLabel("已生成: 0")
        self.generated_count_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.generated_count_label)

    def set_connected(self, version: str = ""):
        """设置已连接状态

        Args:
            version: AutoCAD版本号
        """
        self.status_icon.setText("✅")
        self.status_text.setText(f"已连接 AutoCAD {version}")
        self.status_text.setStyleSheet("font-size: 11px; color: #2e7d32;")
        self.connection_status_changed.emit(True)

    def set_disconnected(self):
        """设置断开状态"""
        self.status_icon.setText("⏳")
        self.status_text.setText("等待AutoCAD...")
        self.status_text.setStyleSheet("font-size: 11px; color: #f9a825;")
        self.connection_status_changed.emit(False)

    def set_warning(self, message: str):
        """设置警告信息（第8.3节错误微弱提示）

        Args:
            message: 警告信息
        """
        self.status_icon.setText("⚠")
        self.status_text.setText(message)
        self.status_text.setStyleSheet("font-size: 11px; color: #e65100;")

    def set_circuit_count(self, total: int, generated: int = 0):
        """更新回路统计

        Args:
            total: 总回路数
            generated: 已生成到CAD的回路数
        """
        self.circuit_count_label.setText(f"回路数: {total}")
        self.generated_count_label.setText(f"已生成: {generated}")


class CADConnectionMonitor(QObject):
    """CAD连接状态监控器

    后台每5秒检测CAD连接状态（第8.1节）。
    连接正常时状态栏显示✅绿色，断开时显示⏳黄色。
    从断开恢复时自动重连，不中断用户操作。

    Signals:
        status_changed(bool): 连接状态变化信号
    """

    status_changed = Signal(bool)

    def __init__(self, cad_driver, status_bar: StatusBar):
        """
        Args:
            cad_driver: CADDriver实例
            status_bar: StatusBar实例
        """
        super().__init__()
        self.cad_driver = cad_driver
        self.status_bar = status_bar
        self.last_connected = False

        self.timer = QTimer()
        self.timer.setInterval(5000)  # 每5秒检测
        self.timer.timeout.connect(self._check_connection)
        self.timer.start()

    def _check_connection(self):
        """检查CAD连接状态

        当未连接时主动尝试连接已运行的AutoCAD实例。
        """
        connected = self.cad_driver.is_connected

        if not connected:
            # 主动尝试连接已运行的AutoCAD实例
            self.cad_driver.connect()
            connected = self.cad_driver.is_connected

        if connected and not self.last_connected:
            # 从断开恢复
            version = self.cad_driver.get_version()
            self.status_bar.set_connected(version)
            self.status_changed.emit(True)
        elif connected and self.last_connected:
            # 保持连接，不发重复信号
            pass
        elif not connected and self.last_connected:
            # 从连接断开
            self.status_bar.set_disconnected()
            self.status_changed.emit(False)
        elif not connected and not self.last_connected:
            # 持续断开，不发重复信号
            pass

        self.last_connected = connected
