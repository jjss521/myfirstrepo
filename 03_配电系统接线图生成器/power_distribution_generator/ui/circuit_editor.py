"""
回路参数编辑区

参照《氛围化编程指令书_配电系统图生成器.md》第5.2~5.3节。

提供单个回路的参数编辑控件，支持：
- 手动输入字段：回路用途、设备功率、线缆型号
- 自动计算字段：只读显示
- 保护整定值：可手动覆盖
- 修改功率后自动触发重新计算
"""

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QComboBox, QSpinBox, QGroupBox,
    QVBoxLayout, QHBoxLayout,
)
from PySide6.QtCore import Signal, Qt

import logging

from calc_engine import calculate_circuit
from models import CircuitData

logger = logging.getLogger(__name__)


# 回路用途可选值
CIRCUIT_USAGES = [
    "1#进线", "2#进线", "水泵", "污水泵", "给水泵",
    "排水泵", "污泥泵", "刮泥机", "搅拌机", "风机",
    "鼓风机", "曝气机", "起重机", "电动葫芦", "闸门",
    "启闭机", "格栅", "压滤机", "脱水机", "加药装置",
    "消毒装置", "照明", "插座", "空调", "通风机",
    "联络", "备用",
]

# 线缆型号可选值
CABLE_SPECS = [
    "YJV-0.6/1kV",
    "YJV22-0.6/1kV",
    "VV-0.6/1kV",
    "VV22-0.6/1kV",
    "YJLV-0.6/1kV",
    "BV-0.45/0.75kV",
    "RVV-0.3/0.5kV",
]


class CircuitEditor(QWidget):
    """回路参数编辑区

    对应UI规范中的参数编辑区域（QScrollArea内QFormLayout）。

    Signals:
        parameter_changed(): 参数变更信号，触发防抖
    """

    parameter_changed = Signal()

    # 回路用途变更的独立信号
    usage_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._circuit = None
        self._panel_type = ""
        self._updating = False  # 防止循环触发
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # ---- 基本参数 ----
        basic_group = QGroupBox("基本参数")
        basic_form = QFormLayout(basic_group)
        basic_form.setSpacing(4)

        self.usage_combo = QComboBox()
        self.usage_combo.setEditable(True)
        self.usage_combo.addItems(CIRCUIT_USAGES)
        self.usage_combo.currentTextChanged.connect(self._on_usage_changed)
        basic_form.addRow("回路用途:", self.usage_combo)

        self.pe_spin = QDoubleSpinBox()
        self.pe_spin.setRange(0.0, 10000.0)
        self.pe_spin.setDecimals(1)
        self.pe_spin.setSuffix(" kW")
        self.pe_spin.valueChanged[float].connect(self._on_pe_changed)
        self.pe_spin.editingFinished.connect(self._on_pe_editing_finished)
        basic_form.addRow("设备功率:", self.pe_spin)

        self.ic_label = QLabel("0.0 A")
        self.ic_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 4px 8px; "
            "border-radius: 3px; color: #666;"
        )
        basic_form.addRow("计算电流:", self.ic_label)

        self.frame_label = QLabel("0 A")
        self.frame_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 4px 8px; "
            "border-radius: 3px; color: #666;"
        )
        basic_form.addRow("壳架电流:", self.frame_label)

        self.in_label = QLabel("0 A")
        self.in_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 4px 8px; "
            "border-radius: 3px; color: #666;"
        )
        basic_form.addRow("脱扣器In:", self.in_label)

        self.ct_label = QLabel("/")
        self.ct_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 4px 8px; "
            "border-radius: 3px; color: #666;"
        )
        basic_form.addRow("CT变比:", self.ct_label)

        self.space_label = QLabel("/")
        self.space_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 4px 8px; "
            "border-radius: 3px; color: #666;"
        )
        basic_form.addRow("单元空间:", self.space_label)

        self.monitor_label = QLabel("/")
        self.monitor_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 4px 8px; "
            "border-radius: 3px; color: #666;"
        )
        basic_form.addRow("监控信号:", self.monitor_label)

        layout.addWidget(basic_group)

        # ---- 线缆参数 ----
        cable_group = QGroupBox("线缆参数")
        cable_form = QFormLayout(cable_group)
        cable_form.setSpacing(4)

        self.cable_combo = QComboBox()
        self.cable_combo.setEditable(True)
        self.cable_combo.addItems(CABLE_SPECS)
        self.cable_combo.currentTextChanged.connect(self._emit_parameter_changed)
        cable_form.addRow("线缆型号:", self.cable_combo)

        self.cable_no_edit = QLineEdit()
        self.cable_no_edit.setPlaceholderText("根据项目结果填入")
        self.cable_no_edit.textChanged.connect(self._emit_parameter_changed)
        cable_form.addRow("线缆编号:", self.cable_no_edit)

        layout.addWidget(cable_group)

        # ---- 保护整定 ----
        protect_group = QGroupBox("保护整定")
        protect_layout = QHBoxLayout(protect_group)

        is1_layout = QVBoxLayout()
        is1_layout.addWidget(QLabel("Is1(长延时):"))
        self.is1_spin = QSpinBox()
        self.is1_spin.setRange(0, 10000)
        self.is1_spin.setSuffix(" A")
        self.is1_spin.valueChanged.connect(self._emit_parameter_changed)
        is1_layout.addWidget(self.is1_spin)
        protect_layout.addLayout(is1_layout)

        is2_layout = QVBoxLayout()
        is2_layout.addWidget(QLabel("Is2(短延时):"))
        self.is2_spin = QSpinBox()
        self.is2_spin.setRange(0, 10000)
        self.is2_spin.setSuffix(" A")
        self.is2_spin.valueChanged.connect(self._emit_parameter_changed)
        is2_layout.addWidget(self.is2_spin)
        protect_layout.addLayout(is2_layout)

        is3_layout = QVBoxLayout()
        is3_layout.addWidget(QLabel("Is3(瞬动):"))
        self.is3_spin = QSpinBox()
        self.is3_spin.setRange(0, 10000)
        self.is3_spin.setSuffix(" A")
        self.is3_spin.valueChanged.connect(self._emit_parameter_changed)
        is3_layout.addWidget(self.is3_spin)
        protect_layout.addLayout(is3_layout)

        layout.addWidget(protect_group)

        layout.addStretch()

    def set_circuit(self, circuit: CircuitData, panel_type: str):
        """加载回路数据到编辑控件

        Args:
            circuit: 回路数据
            panel_type: 柜型
        """
        self._circuit = circuit
        self._panel_type = panel_type
        self._updating = True

        # 基本参数
        self.usage_combo.setCurrentText(circuit.circuit_usage)
        self.pe_spin.setValue(circuit.pe_power)

        # 自动计算字段（只读）
        self.ic_label.setText(f"{circuit.ic_current}A")
        self.frame_label.setText(f"{circuit.frame_current}A")
        self.in_label.setText(f"{circuit.in_rated}A")
        self.ct_label.setText(circuit.ct_ratio)
        self.space_label.setText(circuit.unit_space)
        self.monitor_label.setText(circuit.monitor)

        # 线缆参数
        cable_index = self.cable_combo.findText(circuit.cable_spec)
        if cable_index >= 0:
            self.cable_combo.setCurrentIndex(cable_index)
        else:
            self.cable_combo.setCurrentText(circuit.cable_spec)
        self.cable_no_edit.setText(circuit.cable_no)

        # 保护整定
        self.is1_spin.setValue(int(circuit.is1))
        self.is2_spin.setValue(int(circuit.is2))
        self.is3_spin.setValue(int(circuit.is3))

        self._updating = False

    def get_updated_circuit(self) -> CircuitData:
        """从控件值获取更新后的回路数据

        Returns:
            更新后的CircuitData
        """
        if self._circuit is None:
            return None

        self._circuit.circuit_usage = self.usage_combo.currentText()
        self._circuit.pe_power = self.pe_spin.value()
        self._circuit.cable_spec = self.cable_combo.currentText()
        self._circuit.cable_no = self.cable_no_edit.text()
        self._circuit.is1 = float(self.is1_spin.value())
        self._circuit.is2 = float(self.is2_spin.value())
        self._circuit.is3 = float(self.is3_spin.value())

        return self._circuit

    def _on_usage_changed(self, text: str):
        """回路用途变更"""
        if self._updating:
            return
        if self._circuit:
            self._circuit.circuit_usage = text
        self._emit_parameter_changed()
        self.usage_changed.emit(text)

    def _ensure_circuit(self):
        """确保 _circuit 存在，不存在则自动创建默认回路

        允许用户在未加载Excel数据时直接输入功率进行计算测试。
        自动创建的回路使用当前编辑器中的用途和柜型信息。
        """
        if self._circuit is not None:
            return True

        # 自动创建默认回路
        usage = self.usage_combo.currentText() or "馈线"
        self._circuit = CircuitData(
            column_index=1,
            circuit_usage=usage,
            pe_power=0.0,
        )
        logger.info("自动创建默认回路: usage=%s, panel_type=%s", usage, self._panel_type)
        return True

    def _on_pe_changed(self, value):
        """设备功率变更，触发重新计算

        修改功率后自动重新计算Ic/壳架/In/CT/单元空间并更新UI显示（第5.3节）。
        防御性处理：即使 signal 传入字符串也能正确转为 float。
        """
        if self._updating:
            return

        # 确保回路数据存在（未加载Excel时自动创建）
        if not self._ensure_circuit():
            logger.warning("_on_pe_changed: 无法创建回路数据，跳过计算")
            return

        # 防御性类型转换：确保 value 是 float
        try:
            value = float(value)
        except (TypeError, ValueError):
            return

        # 更新回路数据
        self._circuit.pe_power = value

        # 重新计算
        try:
            self._circuit = calculate_circuit(self._circuit, self._panel_type)
        except Exception as e:
            logger.error("计算失败: %s: %s", type(e).__name__, e, exc_info=True)
            return

        # 更新UI显示（只读字段）
        self._updating = True
        self.ic_label.setText(f"{self._circuit.ic_current}A")
        self.frame_label.setText(f"{self._circuit.frame_current}A")
        self.in_label.setText(f"{self._circuit.in_rated}A")
        self.ct_label.setText(self._circuit.ct_ratio)
        self.space_label.setText(self._circuit.unit_space)
        self.monitor_label.setText(self._circuit.monitor)

        # 同步更新保护整定（基于新In值计算）
        self.is1_spin.setValue(int(self._circuit.is1))
        self.is2_spin.setValue(int(self._circuit.is2))
        self.is3_spin.setValue(int(self._circuit.is3))
        self._updating = False

        self._emit_parameter_changed()

    def _on_pe_editing_finished(self):
        """编辑完成（Enter/失去焦点）时兜底触发重新计算

        作为 valueChanged 的补充，确保手动输入完整后结果一定更新。
        """
        if self._updating:
            return

        # 确保回路数据存在
        if not self._ensure_circuit():
            return

        value = self.pe_spin.value()
        if value == self._circuit.pe_power:
            # 值未变化则不重复计算
            return

        # 直接复用已有计算逻辑
        self._circuit.pe_power = value
        try:
            self._circuit = calculate_circuit(self._circuit, self._panel_type)
        except Exception as e:
            logger.error("计算失败(editing_finished): %s: %s", type(e).__name__, e, exc_info=True)
            return

        self._updating = True
        self.ic_label.setText(f"{self._circuit.ic_current}A")
        self.frame_label.setText(f"{self._circuit.frame_current}A")
        self.in_label.setText(f"{self._circuit.in_rated}A")
        self.ct_label.setText(self._circuit.ct_ratio)
        self.space_label.setText(self._circuit.unit_space)
        self.monitor_label.setText(self._circuit.monitor)

        self.is1_spin.setValue(int(self._circuit.is1))
        self.is2_spin.setValue(int(self._circuit.is2))
        self.is3_spin.setValue(int(self._circuit.is3))
        self._updating = False

        self._emit_parameter_changed()

    def _emit_parameter_changed(self):
        """发射参数变更信号（防抖触发）"""
        if not self._updating:
            self.parameter_changed.emit()
