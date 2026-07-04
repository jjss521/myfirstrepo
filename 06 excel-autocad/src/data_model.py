"""PDSG 数据模型定义

包含所有层次的数据类:
- 数据层: RawRow, CircuitRecord, ErrorRecord
- 映射层: CircuitWithBlock, BlockDefinition, BlockCatalog
- 布局层: PaperSize, Placement, BusLine, GroupLabel, LayoutResult
- 配置模型: AppConfig 及各子配置类
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


# ============================================================
# 枚举
# ============================================================

class ExcelFormat(str, Enum):
    """Excel 文件格式枚举"""
    STANDARD = "standard"       # 标准格式：每行一个回路，列为参数
    TRANSPOSED = "transposed"   # 转置格式：每列一个回路，行为参数


class LoadType(str, Enum):
    """负荷类型枚举"""
    POWER = "动力"
    LIGHTING = "照明"
    VFD = "变频"
    AC = "空调"
    SOCKET = "插座"
    SPARE = "备用"
    CAPACITOR = "电容补偿"

    @classmethod
    def from_str(cls, value: str) -> Optional["LoadType"]:
        """从字符串解析负荷类型，支持中英文"""
        value = value.strip()
        for member in cls:
            if member.value == value or member.name == value.upper():
                return member
        return None


# 负荷类型排序顺序（用于布局分组排列）
LOAD_TYPE_ORDER = [
    LoadType.POWER,
    LoadType.VFD,
    LoadType.AC,
    LoadType.LIGHTING,
    LoadType.SOCKET,
    LoadType.SPARE,
    LoadType.CAPACITOR,
]

# 负荷类型到图块命名缩写映射
LOAD_TYPE_ABBR = {
    LoadType.POWER: "PWR",
    LoadType.LIGHTING: "LGT",
    LoadType.VFD: "VFD",
    LoadType.AC: "AC",
    LoadType.SOCKET: "SKT",
    LoadType.SPARE: "SPR",
    LoadType.CAPACITOR: "CAP",
}

# 运行方式 → 负荷类型推断映射（转置格式 Excel 使用）
OPERATION_MODE_TO_LOAD_TYPE = {
    "变频": LoadType.VFD,
    "工频": LoadType.POWER,
    "直启": LoadType.POWER,
    "软启": LoadType.POWER,
    "星三角": LoadType.POWER,
}


# ============================================================
# 数据层
# ============================================================

@dataclass
class RawRow:
    """Excel 原始行数据"""
    row_number: int
    values: Dict[str, str]


@dataclass
class CircuitRecord:
    """校验后的回路记录"""
    row_number: int
    circuit_id: str
    circuit_name: str
    load_type: LoadType
    rated_power_kw: float
    rated_current_a: float
    breaker_model: str
    breaker_poles: int
    breaker_trip_current_a: float
    ct_ratio: str
    cable_type: str
    cable_section: str
    vfd_model: Optional[str] = None
    vfd_power_kw: Optional[float] = None
    remark: Optional[str] = None
    # --- v1.1 新增字段（转置格式 Excel 扩展） ---
    cabinet_code: Optional[str] = None          # 开关柜代号
    cabinet_size: Optional[str] = None          # 开关柜尺寸(WxDxH)mm
    unit_space: Optional[str] = None            # 单元空间（如 16E）
    distribution_type: Optional[str] = None     # 配电形式（如 MCC）
    operation_mode: Optional[str] = None        # 运行方式（如 变频）
    breaker_frame_current_a: Optional[float] = None  # 断路器壳架电流(A)
    contactor: Optional[str] = None             # 接触器
    thermal_relay: Optional[str] = None         # 热继电器
    power_monitoring: Optional[str] = None      # 电力监控信号
    cable_number: Optional[str] = None          # 线缆编号


@dataclass
class ErrorRecord:
    """校验失败记录"""
    row_number: int
    circuit_id: str
    error_type: str
    error_message: str
    raw_values: Dict[str, str] = field(default_factory=dict)


# ============================================================
# 映射层
# ============================================================

@dataclass
class BlockDefinition:
    """图块定义（从 block_catalog.yaml 读取）"""
    name: str
    description: str
    applicable: Dict[str, Any]
    attributes: List[str]


class BlockCatalog:
    """图块目录管理器"""

    def __init__(self, blocks: List[BlockDefinition]):
        self.blocks = blocks
        self._index: Dict[str, BlockDefinition] = {b.name: b for b in blocks}

    def find(self, block_name: str) -> Optional[BlockDefinition]:
        """根据名称查找图块定义"""
        return self._index.get(block_name)

    def all_names(self) -> List[str]:
        """返回所有图块名称"""
        return list(self._index.keys())


@dataclass
class CircuitWithBlock:
    """关联了图块的回路"""
    record: CircuitRecord
    block_name: str
    attributes: Dict[str, str] = field(default_factory=dict)


# ============================================================
# 布局层
# ============================================================

@dataclass
class PaperSize:
    """图纸幅面"""
    name: str
    width: float
    height: float


@dataclass
class Placement:
    """图块放置信息"""
    block_name: str
    x: float
    y: float
    attributes: Dict[str, str]
    circuit_id: str


@dataclass
class BusLine:
    """母线绘制信息

    direction='vertical': 垂直母线 (x固定, y_start~y_end)
    direction='horizontal': 水平母线 (y固定, x_start~x_end)
    """
    x: float = 0           # 垂直母线: X坐标; 水平母线: 不用
    y_start: float = 0     # 垂直母线: Y起点
    y_end: float = 0       # 垂直母线: Y终点
    # 水平母线字段
    direction: str = "vertical"  # "vertical" | "horizontal"
    bus_y: float = 0       # 水平母线: Y坐标
    x_start: float = 0     # 水平母线: X起点
    x_end: float = 0       # 水平母线: X终点


@dataclass
class GroupLabel:
    """分组标签"""
    text: str
    x: float
    y: float


@dataclass
class TableCell:
    """表格单元格"""
    text: str
    x: float  # 左下角 X
    y: float  # 左下角 Y


@dataclass
class TableLayout:
    """参数表格布局信息

    表格位于原理图下方，每列对应一个回路，每行对应一个参数。
    """
    x: float = 0              # 表格左下角 X
    y: float = 0              # 表格左下角 Y (底边)
    col_width: float = 0      # 列宽
    row_height: float = 7     # 行高
    headers: List[str] = field(default_factory=list)  # 列头 (回路编号)
    rows: List[List[str]] = field(default_factory=list)  # [行标签, 行数据...]
    row_labels: List[str] = field(default_factory=list)  # 行标签


@dataclass
class LayoutResult:
    """布局计算结果"""
    placements: List[Placement]
    bus_line: BusLine
    group_labels: List[GroupLabel]
    paper_size: PaperSize
    table: Optional[TableLayout] = None


# ============================================================
# 配置模型
# ============================================================

@dataclass
class AcadConfig:
    """AutoCAD 连接配置"""
    progids: List[str] = field(default_factory=lambda: [
        "AutoCAD.Application.24.1",
        "AutoCAD.Application.23.1",
    ])
    visible: bool = True


@dataclass
class BlockLibraryConfig:
    """图块库配置"""
    path: str = "./blocks/block_library.dwg"
    catalog: str = "./blocks/block_catalog.yaml"
    title_block_path: str = "./blocks/title_block.dwg"
    default_block: str = "LOOP_POWER_A"


@dataclass
class ExcelConfig:
    """Excel 读取配置"""
    sheet_name: str = "回路清单"
    header_row: int = 1
    data_start_row: int = 2
    column_aliases: Dict[str, str] = field(default_factory=dict)
    min_match_ratio: float = 0.7  # 必填列最低匹配率
    # --- v1.1 新增（转置格式支持） ---
    format_auto_detect: bool = True               # 自动检测 Excel 格式
    transposed_column_aliases: Dict[str, str] = field(default_factory=dict)  # 转置格式列名映射
    default_breaker_model: str = ""               # 默认断路器型号（Excel 中无此列时使用）


@dataclass
class BlockMappingRule:
    """图块映射规则"""
    match: Dict[str, Any]
    block: str


@dataclass
class BlockMappingConfig:
    """图块映射配置"""
    rules: List[BlockMappingRule] = field(default_factory=list)
    default_block: str = "LOOP_POWER_A"


@dataclass
class PaperSizeDef:
    """幅面定义"""
    name: str
    width: float
    height: float


@dataclass
class PaperConfig:
    """图纸幅面配置"""
    sizes: List[PaperSizeDef] = field(default_factory=lambda: [
        PaperSizeDef("A2", 594, 420),
        PaperSizeDef("A1", 841, 594),
        PaperSizeDef("A0", 1189, 841),
    ])
    auto_select: bool = True


@dataclass
class MarginsConfig:
    """边距配置"""
    left: float = 25
    right: float = 25
    top: float = 15
    bottom: float = 30


@dataclass
class LayoutConfig:
    """布局配置

    水平布局: 回路从左到右排列，间距由 horizontal_spacing 控制。
    水平母线在顶部，各回路垂直向下。表格在原理图下方。
    """
    paper: PaperConfig = field(default_factory=PaperConfig)
    # 母线位置
    bus_x: float = 100           # 垂直母线 X (兼容旧布局)
    bus_y: float = 780           # 水平母线 Y 坐标 (水平布局)
    block_offset_x: float = 15   # 图块相对母线的 X 偏移
    # 间距
    vertical_spacing: float = 70          # 垂直间距 (旧布局用)
    vertical_spacing_auto: bool = True
    horizontal_spacing: float = 2140.5407 # 水平间距 (mm, 相邻回路 X 增量)
    # 表格
    table_enabled: bool = True            # 是否绘制参数表格
    table_row_height: float = 7           # 表格行高
    table_label_col_width: float = 30     # 行标签列宽
    table_gap_from_schematic: float = 50  # 表格与原理图的间距
    margins: MarginsConfig = field(default_factory=MarginsConfig)


@dataclass
class SortConfig:
    """排序配置"""
    group_by: str = "load_type"
    group_order: List[str] = field(default_factory=lambda: [
        "动力", "变频", "空调", "照明", "插座", "备用", "电容补偿"
    ])
    group_separator_enabled: bool = True
    group_separator_text: str = "{type} 配电"


@dataclass
class OutputConfig:
    """输出配置"""
    dwg_path: str = "./output/配电系统图.dwg"
    report_path: str = "./output/report.html"
    log_path: str = "./logs/app.log"
    log_level: str = "INFO"


@dataclass
class TextStyleConfig:
    """文字样式配置"""
    font: str = "宋体"
    height: float = 3.5


@dataclass
class TitleBlockConfig:
    """图框配置"""
    enabled: bool = True
    insert_at_x: float = 0
    insert_at_y: float = 0
    attributes: Dict[str, str] = field(default_factory=lambda: {
        "PROJECT_NAME": "",
        "DRAWING_NO": "",
        "DATE": "",
        "DESIGNER": "",
    })


@dataclass
class AppConfig:
    """应用总配置"""
    autocad: AcadConfig = field(default_factory=AcadConfig)
    block_library: BlockLibraryConfig = field(default_factory=BlockLibraryConfig)
    excel: ExcelConfig = field(default_factory=ExcelConfig)
    block_mapping: BlockMappingConfig = field(default_factory=BlockMappingConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    sort: SortConfig = field(default_factory=SortConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    text_style: TextStyleConfig = field(default_factory=TextStyleConfig)
    title_block: TitleBlockConfig = field(default_factory=TitleBlockConfig)
