"""
AutoCAD COM驱动层

参照《氛围化编程指令书_配电系统图生成器.md》第6章全部COM接口规范。

提供AutoCAD连接、基准点获取、图块操作、属性更新等核心功能。
所有COM调用均通过 safe_cad_call 包装，实现错误诊断与静默处理。
"""

import logging

# pythoncom（来自pywin32）用于COM线程初始化，可选依赖
# 未安装时CAD连接仍可工作，只是缺少CoInitialize()可能降低连接稳定性
try:
    import pythoncom
    HAS_PYWIN32 = True
except ImportError:
    pythoncom = None
    HAS_PYWIN32 = False

import comtypes.client
from comtypes import COMError

logger = logging.getLogger(__name__)


# 图块间距（CAD单位，第4.4节）
CIRCUIT_SPACING = 3000
# 母线与图块底部的偏移
BUSBAR_OFFSET = 800


def safe_cad_call(func, *args, **kwargs):
    """COM调用包装器，失败时记录诊断日志

    参照《氛围化编程指令书_配电系统图生成器.md》第8.3节。

    Args:
        func: 要调用的函数
        *args, **kwargs: 函数参数

    Returns:
        函数返回值，失败时返回None
    """
    try:
        return func(*args, **kwargs)
    except COMError as e:
        logger.warning("COM错误: %s | HRESULT=0x%08X | 文本=%s",
                       func.__name__, e.hresult if hasattr(e, 'hresult') else 0, e)
        return None
    except AttributeError as e:
        logger.warning("AutoCAD对象无效: %s | %s", func.__name__, e)
        return None
    except OSError as e:
        logger.warning("OS/COM初始化错误: %s | %s", func.__name__, e)
        return None
    except Exception as e:
        logger.warning("CAD调用异常: %s | %s: %s", func.__name__, type(e).__name__, e)
        return None


def _com_point(x, y, z=0.0):
    """创建AutoCAD点对象"""
    return comtypes.client.CreateObject("AutoCAD.APoint",
                                        (float(x), float(y), float(z)))


def _com_safearray(points_list):
    """创建AutoCAD SafeArray"""
    return comtypes.client.CreateObject("AutoCAD.ACAD_SafeArray",
                                        list(points_list))


class CADDriver:
    """AutoCAD COM驱动

    封装所有AutoCAD交互操作，属性：acad, doc, ms。
    """

    def __init__(self):
        self.acad = None
        self.doc = None
        self.ms = None
        self._com_initialized = False

    def _ensure_com_initialized(self):
        """确保当前线程已初始化COM

        Windows COM自动化要求每个线程在使用COM对象前调用CoInitialize()。
        未初始化时GetActiveObject()会抛出OSError或COMError。

        注意：需要 pywin32（pythoncom 模块）。未安装时跳过此步骤，
        comtypes 在大多数情况下仍能正常工作。
        """
        if not self._com_initialized:
            if not HAS_PYWIN32:
                logger.debug("pywin32未安装，跳过CoInitialize()（建议 pip install pywin32 提高连接稳定性）")
                self._com_initialized = True  # 标记为已处理（跳过模式）
                return
            try:
                pythoncom.CoInitialize()
                self._com_initialized = True
                logger.info("COM初始化成功（CoInitialize）")
            except Exception as e:
                logger.error("COM初始化失败: %s", e)
                self._com_initialized = False

    def connect(self):
        """连接AutoCAD应用程序

        参照《氛围化编程指令书_配电系统图生成器.md》第6.1节。

        连接策略：
        1. 先确保COM已初始化
        2. 尝试通用ProgID "AutoCAD.Application"
        3. 若失败，尝试版本特定ProgID（R24~R29）
        4. 连接成功后设置acad.Visible=True并获取文档

        Returns:
            bool: 连接成功返回True
        """
        # 确保COM初始化
        self._ensure_com_initialized()

        def _do_connect():
            self.acad = comtypes.client.GetActiveObject("AutoCAD.Application")
            self.acad.Visible = True
            self.doc = self.acad.ActiveDocument
            self.ms = self.doc.ModelSpace
            return True

        result = safe_cad_call(_do_connect)

        if result is not None:
            logger.info("AutoCAD连接成功（通用ProgID）")
            return True

        # 通用ProgID失败，尝试版本特定ProgID
        # AutoCAD版本映射：R24=2024, R25=2025, R26=2026, R27=2027, R28=2028, R29=2029
        for ver in range(29, 23, -1):  # 从高版本向低版本尝试
            def _try_version(v=ver):
                prog_id = f"AutoCAD.Application.{v}"
                self.acad = comtypes.client.GetActiveObject(prog_id)
                self.acad.Visible = True
                self.doc = self.acad.ActiveDocument
                self.ms = self.doc.ModelSpace
                return True

            result = safe_cad_call(_try_version)
            if result is not None:
                logger.info("AutoCAD连接成功（ProgID: AutoCAD.Application.%d）", ver)
                return True

        logger.warning("AutoCAD连接失败：未找到运行中的AutoCAD实例")
        return False

    @property
    def is_connected(self) -> bool:
        """检查连接状态"""
        try:
            if self.acad is None:
                return False
            _ = self.acad.Visible
            return True
        except Exception:
            self.acad = None
            self.doc = None
            self.ms = None
            logger.info("AutoCAD连接已断开")
            return False

    def get_version(self) -> str:
        """获取AutoCAD版本号"""
        def _get_ver():
            return str(self.acad.Version)
        return safe_cad_call(_get_ver) or ""

    def pick_insertion_point(self):
        """让用户在CAD中点击选择基准点

        参照《氛围化编程指令书_配电系统图生成器.md》第6.2节。

        Returns:
            (x, y, z) 元组，用户取消时返回None
        """
        def _pick():
            point = self.doc.Utility.GetPoint(
                None, "请选择配电系统图基准点:"
            )
            if point:
                return (float(point[0]), float(point[1]), float(point[2]))
            return None

        return safe_cad_call(_pick)

    def insert_circuit_block(self, block_name: str, insert_point: tuple,
                             attributes_dict: dict) -> str:
        """插入一个回路图块并填充所有属性

        参照《氛围化编程指令书_配电系统图生成器.md》第6.3节。

        Args:
            block_name: 图块名称
            insert_point: 插入点坐标 (x, y, z)
            attributes_dict: 属性标签->值的字典

        Returns:
            图块句柄字符串，失败返回None
        """
        def _insert():
            point = _com_point(*insert_point)
            blk_ref = self.ms.InsertBlock(
                point, block_name, 1.0, 1.0, 1.0, 0.0
            )

            # 填充属性
            for att in blk_ref.Attributes:
                tag = att.TagString
                if tag in attributes_dict:
                    att.TextString = str(attributes_dict[tag])

            return str(blk_ref.Handle)

        return safe_cad_call(_insert)

    def update_block_attributes(self, handle: str, changed_attrs: dict):
        """通过句柄精准修改图块属性，不重插

        参照《氛围化编程指令书_配电系统图生成器.md》第6.4节。

        Args:
            handle: 图块句柄
            changed_attrs: 要修改的 {标签: 新值} 字典
        """
        def _update():
            blk_ref = self.doc.HandleToObject(handle)

            for att in blk_ref.Attributes:
                if att.TagString in changed_attrs:
                    att.TextString = str(changed_attrs[att.TagString])

            # 刷新视图
            self.doc.Regen(1)  # acActiveViewport

        safe_cad_call(_update)

    def ensure_block_loaded(self, block_dwg_path: str, block_name: str):
        """确保图块定义已加载到当前图纸中

        参照《氛围化编程指令书_配电系统图生成器.md》第6.6节。

        Args:
            block_dwg_path: 图块DWG文件路径
            block_name: 图块名称
        """
        def _ensure():
            blocks = self.doc.Blocks

            # 检查图块是否已存在
            for i in range(blocks.Count):
                if blocks.Item(i).Name == block_name:
                    return  # 已存在

            # 不存在则通过插入外部DWG加载定义
            from pathlib import Path
            if Path(block_dwg_path).exists():
                # 插入到空白位置并删除引用
                dummy_point = _com_point(0, 0, 0)
                blk_ref = self.ms.InsertBlock(
                    dummy_point, block_dwg_path, 1.0, 1.0, 1.0, 0.0
                )
                blk_ref.Delete()

        safe_cad_call(_ensure)

    def create_temp_block(self, block_name: str):
        """在CAD中创建临时图块（仅含属性定义占位）

        当DWG文件不存在时，在内存中创建简易图块替代。

        Args:
            block_name: 图块名称
        """
        def _create():
            blocks = self.doc.Blocks

            # 检查是否已存在
            for i in range(blocks.Count):
                if blocks.Item(i).Name == block_name:
                    return

            # 创建新图块定义
            insertion_point = _com_point(0, 0, 0)
            temp_block = blocks.Add(insertion_point, block_name)

            # 添加属性定义
            attrs = [
                ("CIRCUIT_NAME", "回路名称", 50, 180),
                ("CIRCUIT_NO", "回路编号", 50, 160),
                ("PE_POWER", "功率(kW)", 50, 140),
                ("IC_CURRENT", "电流(A)", 50, 120),
                ("FRAME_CURRENT", "壳架(A)", 50, 100),
                ("IN_RATED", "In(A)", 50, 80),
                ("IS1", "Is1(A)", 50, 60),
                ("IS2", "Is2(A)", 200, 60),
                ("IS3", "Is3(A)", 350, 60),
                ("CT_RATIO", "CT变比", 50, 40),
                ("MONITOR", "监控信号", 50, 20),
                ("CABLE_SPEC", "线缆", 50, 0),
                ("CABLE_NO", "线缆编号", 260, 0),
                ("UNIT_SPACE", "单元空间", 260, 180),
            ]

            for tag, prompt, x_pos, y_pos in attrs:
                att_def = temp_block.AddAttribute(
                    1,  # AttributeMode
                    1,  # InsertionPoint for AttDef API call - we set below
                    tag,
                    prompt,
                    tag,  # Default value = tag name
                )
                # 设置位置
                att_def.InsertionPoint = _com_point(float(x_pos), float(y_pos), 0)
                att_def.Height = 15.0

        safe_cad_call(_create)

    def insert_with_fade_in(self, block_name: str, insert_point: tuple,
                            attributes_dict: dict) -> str:
        """新回路插入时半透明渐入效果

        参照《氛围化编程指令书_配电系统图生成器.md》第8.2节。

        Args:
            block_name: 图块名称
            insert_point: 插入点坐标
            attributes_dict: 属性字典

        Returns:
            图块句柄
        """
        handle = self.insert_circuit_block(block_name, insert_point,
                                           attributes_dict)

        def _set_transparency(val):
            if handle:
                try:
                    blk_ref = self.doc.HandleToObject(handle)
                    blk_ref.Transparency = val
                except Exception:
                    pass

        if handle:
            # 先设为半透明
            _set_transparency(50)
            # 注意：实际项目中应在QTimer中延迟恢复
            # 此处返回句柄，由调用方在500ms后调用 restore_opacity(handle)

        return handle

    def restore_opacity(self, handle: str):
        """恢复图块为不透明

        Args:
            handle: 图块句柄
        """
        def _restore():
            blk_ref = self.doc.HandleToObject(handle)
            blk_ref.Transparency = 0

        safe_cad_call(_restore)
