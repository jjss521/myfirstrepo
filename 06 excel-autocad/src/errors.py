"""PDSG 自定义异常类

异常分类与处理策略:
- 环境/配置级问题 -> 直接退出
- 单个回路数据问题 -> 跳过继续
"""


class PDSGError(Exception):
    """PDSG 基础异常类"""
    pass


class ExcelReadError(PDSGError):
    """Excel 文件读取异常（文件不存在/Sheet未找到/列匹配失败）"""
    pass


class ConfigError(PDSGError):
    """配置文件加载或校验异常"""
    pass


class BlockLibraryError(PDSGError):
    """图块库异常（DWG不存在/图块缺失/属性Tag缺失）"""
    pass


class AcadConnectionError(PDSGError):
    """AutoCAD 连接异常（未运行/版本不兼容）"""
    pass


class AcadOperationError(PDSGError):
    """AutoCAD 操作异常（图块插入失败/属性写入失败）"""
    pass


class CircuitValidationError(PDSGError):
    """单个回路数据校验异常（不导致程序退出，仅跳过该回路）"""
    pass
