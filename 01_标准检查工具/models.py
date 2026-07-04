"""数据模型定义"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class StandardStatus(Enum):
    """标准状态枚举"""
    ACTIVE = "现行"
    ABOLISHED = "作废"
    REPEALED = "废止"
    UPCOMING = "即将实施"
    UNKNOWN = "未知"


@dataclass
class OcrTextRegion:
    """OCR识别的单个文本区域"""
    bbox: List[List[float]]  # 4个角点坐标
    text: str
    confidence: float


@dataclass
class MergedTextLine:
    """合并后的文本行"""
    text: str
    confidence: float
    y_center: float  # 用于排序


@dataclass
class StandardRef:
    """从截图中提取的标准引用"""
    number: str           # 标准编号，如 "GB 50016-2014"
    name: str             # 标准名称，如 "建筑设计防火规范"
    source_files: List[str] = field(default_factory=list)  # 来源截图文件列表
    confidence: float = 0.0  # OCR置信度
    raw_text: str = ""    # 原始OCR文本，用于调试


@dataclass
class SearchResult:
    """csres.com搜索结果"""
    standard_ref: StandardRef
    status: StandardStatus
    csres_number: str      # 网站上的标准编号
    csres_name: str        # 网站上的标准名称
    detail_url: str        # 详情页URL
    department: str = ""   # 发布部门
    effective_date: str = ""  # 实施日期


@dataclass
class ReplacementInfo:
    """替代信息"""
    old_number: str        # 旧标准编号
    old_name: str          # 旧标准名称
    replacement_number: str = ""   # 替代标准编号
    replacement_name: str = ""     # 替代标准名称
    abolished_date: str = ""       # 作废/废止日期
    replacement_notes: str = ""    # 替代说明原文


@dataclass
class ValidatedStandard:
    """验证后的完整标准记录"""
    standard_ref: StandardRef
    search_result: Optional[SearchResult] = None
    replacement_info: Optional[ReplacementInfo] = None
