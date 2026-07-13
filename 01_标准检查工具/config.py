"""常量和配置参数"""

from __future__ import annotations

import re
from re import Pattern
from typing import Final

# ==================== csres.com 配置 ====================
CSRES_BASE_URL: Final[str] = "http://www.csres.com"
CSRES_SEARCH_URL: Final[str] = "http://www.csres.com/s.jsp"
REQUEST_TIMEOUT: Final[int] = 15  # 请求超时（秒）
REQUEST_DELAY_MIN: Final[float] = 2.0  # 最小请求间隔（秒）
REQUEST_DELAY_MAX: Final[float] = 5.0  # 最大请求间隔（秒）
MAX_RETRIES: Final[int] = 3  # 最大重试次数
RETRY_BACKOFF_FACTOR: Final[int] = 2  # 重试退避因子
USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ==================== OCR 配置 ====================
OCR_CONFIDENCE_THRESHOLD: Final[float] = 0.6  # OCR置信度阈值
OCR_LANG: Final[str] = "ch"  # 中文语言模型
OCR_USE_GPU: Final[bool] = False  # CPU模式
MERGE_LINE_DISTANCE: Final[int] = 30  # 文本行合并距离阈值（像素）

# ==================== 标准编号正则 ====================
# 匹配标准编号：GB 50016-2014, JGJ/T 3-2010, GB/T 50352-2019 等
STANDARD_NUMBER_PATTERN: Final[Pattern[str]] = re.compile(
    r"([A-Z]{1,4}(?:/[A-Z])?\s*\d+(?:\.\d+)?\s*[-—－]\s*\d{4})"
)

# 匹配标准编号后的标准名称（中文）
STANDARD_NAME_PATTERN: Final[Pattern[str]] = re.compile(
    r"[\s ]+([\u4e00-\u9fff][\u4e00-\u9fff\w\s（）()、·/]{0,50}[\u4e00-\u9fff）)\w])"
)

# 已知的标准前缀列表（用于优先级匹配）
KNOWN_PREFIXES: Final[list[str]] = [
    "GB",
    "GB/T",
    "GB/Z",
    "GBJ",
    "JGJ",
    "JGJ/T",
    "CJJ",
    "CJJ/T",
    "HG",
    "HG/T",
    "JB",
    "JB/T",
    "DL",
    "DL/T",
    "SL",
    "SL/T",
    "JT",
    "JT/T",
    "JTG",
    "JTG/T",
    "SH",
    "SH/T",
    "YB",
    "YB/T",
    "TB",
    "TB/T",
    "MH",
    "MH/T",
    "CECS",
    "DB",
    "DB/T",
    "JTG",
    "JTG/T",
    "YSJ",
    "YSJ/T",
]

# ==================== OCR数字纠错映射 ====================
# 在标准编号的数字区域，这些字母可能是对应数字的误识别
DIGIT_CORRECTIONS: Final[dict[str, str]] = {
    "O": "0",
    "o": "0",
    "l": "1",
    "I": "1",
    "i": "1",
    "S": "5",
    "s": "5",
    "B": "8",
    "Z": "2",
    "z": "2",
}

# ==================== 状态文本映射 ====================
STATUS_TEXT_MAP: Final[dict[str, str]] = {
    "现行": "ACTIVE",
    "作废": "ABOLISHED",
    "废止": "REPEALED",
    "即将实施": "UPCOMING",
    "未实施": "UPCOMING",
}

# ==================== 默认路径 ====================
DEFAULT_INPUT_DIR: Final[str] = "./screenshots"
DEFAULT_OUTPUT_DIR: Final[str] = "./output"
