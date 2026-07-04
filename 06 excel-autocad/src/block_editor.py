"""PDSG 图块编辑器模块

通过 AutoCAD COM 创建、编辑和管理配电系统图标准回路图块。
生成 block_library.dwg 和 title_block.dwg 文件。

功能:
- 创建 2 种标准回路图块 (LOOP_POWER_A / LOOP_POWER_B)
- 创建标题栏图块 (TITLE_BLOCK)
- 在 AutoCAD 中打开块编辑器 (BEDIT) 修改图块
- 验证图块库完整性
- 保存为标准 DWG 文件

v2.0: 简化为 2 种图块 (按断路器电流阈值区分)，不含属性定义。
"""
import logging
import os
import time
from array import array
from typing import Dict, List, Optional, Tuple

from .data_model import AcadConfig
from .errors import AcadConnectionError, AcadOperationError, BlockLibraryError

logger = logging.getLogger(__name__)


# ================================================================
# ATTDEF 模式常量 (AutoCAD acAttributeMode)
# ================================================================

ATT_INVISIBLE = 1
ATT_CONSTANT = 2
ATT_VERIFY = 4
ATT_PRESET = 8

# 文字对齐 (AutoCAD acAlignment)
ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2
ALIGN_MIDDLE = 4


# ================================================================
# 图块几何参数 (单位: mm, 与 config.yaml 布局参数匹配)
# ================================================================

class BlockParams:
    """图块几何参数"""
    # --- 连接线 ---
    STUB_LEN = 5               # 母线连接短横线长度

    # --- 断路器 ---
    BRK_W = 12                 # 断路器矩形宽度
    BRK_H = 7                  # 断路器矩形高度

    # --- 电缆 ---
    CABLE_LEN = 15             # 电缆段长度

    # --- 负载端 ---
    LOAD_W = 8                 # 负载端宽度
    LOAD_H = 6                 # 负载端高度

    # --- 相位标记 ---
    PHASE_TICK = 2             # 相位竖线半长
    PHASE_GAP = 2.5            # 相位标记间距

    # --- 间隔 ---
    GAP = 3                    # 元件间距

    # --- 文字 ---
    TEXT_H = 3.0               # 属性文字高度
    LABEL_H = 4.0              # 标签文字高度
    TEXT_FONT = "SimSun"       # 属性文字字体 (宋体)

    # --- 属性文字行 Y 坐标 (从插入点向上排列) ---
    ROW_Y = [22, 29, 36, 43, 50, 57]

    # --- 属性文字列 X 坐标 ---
    COL_X = [8, 28, 50]

    # --- VFD 变频器专用 ---
    VFD_RECT_W = 10            # 整流/逆变矩形宽度
    VFD_RECT_H = 7             # 整流/逆变矩形高度
    VFD_GAP = 4                # 变频器元件间距

    # --- 图框 ---
    TITLE_W = 180              # 图框宽度
    TITLE_H = 50               # 图框高度


# ================================================================
# 标准图块定义
# ================================================================

STANDARD_BLOCKS: List[Dict] = [
    {"name": "LOOP_POWER_A", "desc": "400A及以下断路器回路",
     "breaker_max_current": 400},
    {"name": "LOOP_POWER_B", "desc": "400A以上断路器回路",
     "breaker_min_current": 401},
]

# 标题栏属性
TITLE_BLOCK_ATTRS: List[str] = [
    "PROJECT_NAME", "DRAWING_NO", "DATE", "DESIGNER",
]


# ================================================================
# 图块编辑器
# ================================================================

class BlockEditor:
    """图块编辑器 — 通过 AutoCAD COM 创建和管理标准回路图块

    典型工作流:
    1. connect()            — 连接 AutoCAD
    2. create_library_doc() — 新建空白文档
    3. create_all_blocks()  — 创建 2 种标准图块 (LOOP_POWER_A/B)
    4. create_title_block() — 创建标题栏图块
    5. save_library()       — 保存为 block_library.dwg
    6. close()              — 清理

    v2.0: 图块不含属性定义，所有参数在图块下方表格中展示。
    """

    def __init__(self):
        self.app = None
        self.doc = None
        self._connected = False

    # ----------------------------------------------------------------
    # 连接管理
    # ----------------------------------------------------------------

    def connect(self, acad_cfg: AcadConfig = None) -> bool:
        """连接 AutoCAD

        Args:
            acad_cfg: 连接配置，为 None 时使用默认值

        Returns:
            True 连接成功

        Raises:
            AcadConnectionError: 无法连接
        """
        try:
            import comtypes
            import comtypes.client
        except ImportError as e:
            raise AcadConnectionError(f"缺少 comtypes 依赖: {e}")

        self._ensure_sta_com()

        if acad_cfg is None:
            acad_cfg = AcadConfig()

        last_error = None
        for progid in acad_cfg.progids:
            try:
                self.app = comtypes.client.GetActiveObject(progid)
                self.app.Visible = acad_cfg.visible
                self._connected = True
                logger.info("AutoCAD 连接成功: %s (版本 %s)",
                            progid, self.app.Version)
                return True
            except Exception as e:
                last_error = e
                logger.debug("连接 %s 失败: %s", progid, e)

        raise AcadConnectionError(
            f"无法连接 AutoCAD: {acad_cfg.progids}, 最后错误: {last_error}"
        )

    def close(self):
        """断开连接（不关闭 AutoCAD）"""
        self._connected = False
        self.app = None
        self.doc = None

    @property
    def connected(self) -> bool:
        return self._connected

    # ----------------------------------------------------------------
    # 文档管理
    # ----------------------------------------------------------------

    def create_library_doc(self):
        """新建空白文档用于创建图块库"""
        self._check_connected()
        try:
            # 刷新 COM 线程初始化
            self._ensure_sta_com()
            self.doc = self.app.Documents.Add()
            logger.info("已创建新文档: %s", self.doc.Name)
        except Exception as e:
            # COM 可能在操作过程中失效，尝试重连后重试一次
            logger.warning("首次创建文档失败，尝试重连: %s", e)
            try:
                self.reconnect()
                self.doc = self.app.Documents.Add()
                logger.info("重连后创建文档成功: %s", self.doc.Name)
            except Exception as e2:
                raise AcadOperationError(f"创建文档失败: {e2}")

    # ----------------------------------------------------------------
    # 图块创建 — 批量
    # ----------------------------------------------------------------

    def create_all_blocks(self) -> Tuple[int, int]:
        """创建 2 种标准回路图块 (LOOP_POWER_A / LOOP_POWER_B)

        Returns:
            (成功数, 失败数)
        """
        self._check_connected()
        self.doc = self.app.ActiveDocument

        ok = 0
        fail_list = []
        for bdef in STANDARD_BLOCKS:
            try:
                self._create_single_block(bdef)
                ok += 1
            except Exception as e:
                logger.warning("创建图块 %s 首次失败: %s", bdef["name"], e)
                fail_list.append(bdef)
            # 间隔延迟，避免 RPC_E_CALL_REJECTED
            time.sleep(0.5)

        # 重试失败的图块
        if fail_list:
            time.sleep(1)
            retry_ok = 0
            still_fail = []
            for bdef in fail_list:
                try:
                    self._create_single_block(bdef)
                    retry_ok += 1
                except Exception as e:
                    logger.error("创建图块 %s 重试仍失败: %s", bdef["name"], e)
                    still_fail.append(bdef)
            ok += retry_ok
            fail_list = still_fail

        logger.info("标准图块创建完成: 成功 %d / 失败 %d", ok, len(fail_list))
        return ok, len(fail_list)

    def create_title_block(self) -> bool:
        """创建标题栏图块 (TITLE_BLOCK)

        Returns:
            True 创建成功
        """
        self._check_connected()
        self.doc = self.app.ActiveDocument
        try:
            self._build_title_block_def(
                "TITLE_BLOCK",
                BlockParams.TITLE_W,
                BlockParams.TITLE_H,
            )
            logger.info("标题栏图块 TITLE_BLOCK 已创建")
            return True
        except Exception as e:
            logger.error("创建标题栏图块失败: %s", e)
            return False

    # ----------------------------------------------------------------
    # 图块创建 — 单个
    # ----------------------------------------------------------------

    def create_single_block(self, block_name: str) -> bool:
        """创建指定的单个标准图块

        Args:
            block_name: 图块名称（必须在 STANDARD_BLOCKS 中）

        Returns:
            True 创建成功
        """
        self._check_connected()
        self.doc = self.app.ActiveDocument

        bdef = None
        for b in STANDARD_BLOCKS:
            if b["name"] == block_name:
                bdef = b
                break

        if bdef is None:
            logger.error("未知图块: %s", block_name)
            return False

        # 首次尝试
        try:
            self._create_single_block(bdef)
            return True
        except Exception as e:
            logger.warning("创建图块 %s 首次失败: %s，1秒后重试...", block_name, e)

        # 重试一次
        time.sleep(1)
        try:
            self._check_connected()
            self.doc = self.app.ActiveDocument
            self._create_single_block(bdef)
            return True
        except Exception as e:
            logger.error("创建图块 %s 重试仍失败: %s", block_name, e)
            return False

    def _create_single_block(self, bdef: Dict):
        """内部: 创建单个图块

        v2.0: 仅创建空白图块定义 (占位)，用户通过 BEDIT 手动编辑几何图形。
        图块不含属性定义。

        插入点 (0,0) 位于占位矩形的左侧垂直中心，即母线连接点。
        """
        name = bdef["name"]

        # 删除已存在的同名图块
        self._purge_block(name)

        bp = self.doc.Blocks
        origin = _pt(0, 0, 0)
        block = bp.Add(origin, name)

        # 绘制占位矩形，垂直居中于插入点 (0,0)
        # 插入点 = 左侧中心 = 母线连接点
        p = BlockParams
        w = p.BRK_W + p.CABLE_LEN * 2   # 42mm
        h = 10                             # 10mm 高
        self._add_rect(block, 0, -h / 2, w, h / 2)

        # 在模型空间插入一个引用（确保 DWG 中包含定义）
        self.doc.ModelSpace.InsertBlock(origin, name, 1.0, 1.0, 1.0, 0.0)
        logger.info("图块已创建: %s (%s)", name, bdef["desc"])

    # ----------------------------------------------------------------
    # 几何图形 — 标准回路 (动力/照明/空调/电容补偿/备用)
    # ----------------------------------------------------------------

    def _draw_normal_geometry(self, block, poles: int):
        """绘制标准回路几何图形

        布局 (从左到右):
          [连接短线] — [电缆段] — [断路器矩形] — [电缆段] — [负载端]

        坐标系: (0,0) = 图块插入点 = 母线连接点
        """
        p = BlockParams

        # ---- 关键 X 坐标 ----
        x0 = 0                                   # 起点
        x1 = p.STUB_LEN                          # 连接短横线终点
        x2 = x1 + p.CABLE_LEN                    # 电缆段终点
        x3 = x2 + p.GAP                          # 断路器左边缘
        x4 = x3 + p.BRK_W                       # 断路器右边缘
        x5 = x4 + p.GAP                          # 电缆段起点
        x6 = x5 + p.CABLE_LEN                    # 电缆段终点
        x7 = x6 + p.GAP                          # 负载端左边缘
        x8 = x7 + p.LOAD_W                       # 负载端右边缘

        y0 = 5                                   # 中心线 Y

        # 1) 连接短横线 (母线 -> 电缆)
        self._add_line(block, x0, y0, x1, y0)

        # 2) 第一段电缆
        self._add_line(block, x1, y0, x2, y0)

        # 3) 断路器矩形 (中心对齐)
        by_bot = y0 - p.BRK_H / 2
        by_top = y0 + p.BRK_H / 2
        self._add_rect(block, x3, by_bot, x4, by_top)

        # 4) 极数标注 (矩形内)
        pole_text = f"{poles}P"
        self._add_text(block, pole_text,
                       x3 + p.BRK_W / 2, y0,
                       height=2.5, center=True)

        # 5) 断路器竖线标记 (矩形两侧)
        self._add_line(block, x3, y0 - 4, x3, y0 + 4)
        self._add_line(block, x4, y0 - 4, x4, y0 + 4)

        # 6) 第二段电缆
        self._add_line(block, x5, y0, x6, y0)

        # 7) 负载端矩形
        ly_bot = y0 - p.LOAD_H / 2
        ly_top = y0 + p.LOAD_H / 2
        self._add_rect(block, x7, ly_bot, x8, ly_top)

        # 8) 相位标记 (第一段电缆上方小竖线)
        n_marks = max(poles, 1)
        for i in range(n_marks):
            mx = x1 + 3 + i * p.PHASE_GAP
            self._add_line(block, mx, y0 + p.PHASE_TICK,
                           mx, y0 - p.PHASE_TICK)

        # 9) 末端标记 (负载端右侧小箭头)
        self._add_line(block, x8, y0, x8 + 3, y0)
        self._add_line(block, x8 + 3, y0, x8 + 1, y0 + 1.5)
        self._add_line(block, x8 + 3, y0, x8 + 1, y0 - 1.5)

    # ----------------------------------------------------------------
    # 几何图形 — VFD 变频回路
    # ----------------------------------------------------------------

    def _draw_vfd_geometry(self, block, poles: int):
        """绘制变频回路几何图形

        布局: [连接线] — [整流器] — [逆变器] — [输出] — [负载]
        """
        p = BlockParams

        x0 = 0
        x1 = p.STUB_LEN
        x2 = x1 + p.CABLE_LEN
        x3 = x2 + p.GAP
        x4 = x3 + p.VFD_RECT_W
        x5 = x4 + p.VFD_GAP
        x6 = x5 + p.VFD_RECT_W
        x7 = x6 + p.GAP
        x8 = x7 + p.CABLE_LEN
        x9 = x8 + p.GAP
        x10 = x9 + p.LOAD_W

        y0 = 5

        # 1) 连接短横线 + 电缆
        self._add_line(block, x0, y0, x1, y0)
        self._add_line(block, x1, y0, x2, y0)

        # 2) 整流器 (AC->DC)
        ry_bot = y0 - p.VFD_RECT_H / 2
        ry_top = y0 + p.VFD_RECT_H / 2
        self._add_rect(block, x3, ry_bot, x4, ry_top)
        self._add_text(block, "AC/DC", x3 + p.VFD_RECT_W / 2, y0,
                       height=2.0, center=True)

        # 3) 连接线 整流->逆变
        self._add_line(block, x4, y0, x5, y0)

        # 4) 逆变器 (DC->AC)
        self._add_rect(block, x5, ry_bot, x6, ry_top)
        self._add_text(block, "DC/AC", x5 + p.VFD_RECT_W / 2, y0,
                       height=2.0, center=True)

        # 5) 连接线 逆变->输出
        self._add_line(block, x6, y0, x7, y0)

        # 6) 输出电缆
        self._add_line(block, x7, y0, x8, y0)

        # 7) 负载端
        ly_bot = y0 - p.LOAD_H / 2
        ly_top = y0 + p.LOAD_H / 2
        self._add_rect(block, x9, ly_bot, x10, ly_top)

        # 8) 相位标记
        n_marks = max(poles, 1)
        for i in range(n_marks):
            mx = x1 + 3 + i * p.PHASE_GAP
            self._add_line(block, mx, y0 + p.PHASE_TICK,
                           mx, y0 - p.PHASE_TICK)

        # 9) VFD 整体标签
        self._add_text(block, "VFD",
                       (x3 + x6) / 2, y0 + p.VFD_RECT_H / 2 + 3,
                       height=2.5, center=True)

        # 10) 变频器元件竖线连接 (顶部/底部虚线效果)
        for xi in [x3, x4, x5, x6]:
            self._add_line(block, xi, ry_top, xi, ry_top + 2)
            self._add_line(block, xi, ry_bot, xi, ry_bot - 2)

        # 11) 末端箭头
        self._add_line(block, x10, y0, x10 + 3, y0)
        self._add_line(block, x10 + 3, y0, x10 + 1, y0 + 1.5)
        self._add_line(block, x10 + 3, y0, x10 + 1, y0 - 1.5)

    # ----------------------------------------------------------------
    # 属性定义
    # ----------------------------------------------------------------

    def _add_attribute_defs(self, block, attr_tags: List[str]):
        """为图块添加属性定义 (ATTDEF)

        属性按行排列在几何图形上方。
        每行 3 列，每列放 1 个属性。
        """
        p = BlockParams
        cols = len(p.COL_X)

        for i, tag in enumerate(attr_tags):
            row = i // cols
            col = i % cols

            x = p.COL_X[col]
            y = p.ROW_Y[row] if row < len(p.ROW_Y) else (
                p.ROW_Y[-1] + (row - len(p.ROW_Y) + 1) * 7
            )

            self._add_attdef(
                block,
                tag=tag,
                default="",
                prompt=f"请输入{tag}",
                x=x, y=y,
                height=p.TEXT_H,
            )

    def _add_attdef(self, block, tag, default, prompt, x, y, height):
        """添加单个 ATTDEF

        使用 Block.AddAttribute COM 方法。
        关键: 不设置 StyleName（使用文档默认文字样式），
        避免 AutoCAD "Primary key not found" 错误。
        """
        pt = _pt(x, y, 0)
        try:
            attdef = block.AddAttribute(
                height,
                ATT_VERIFY,      # mode: 插入时验证
                prompt,
                pt,
                tag,
                default,
            )
            # 不设置 StyleName — 使用文档默认文字样式
            # 不设置 TextAlignmentPoint — 左对齐时 InsertionPoint 即为锚点
            return
        except Exception:
            pass

        # 回退: 尝试 mode=0 (普通模式，无验证)
        try:
            block.AddAttribute(height, 0, prompt, pt, tag, default)
            return
        except Exception:
            pass

        # 最终回退: 使用 SendCommand 执行 -ATTDEF 命令
        # 注意: 这会在模型空间创建 ATTDEF，而非块内
        # 但至少能让用户看到问题所在
        try:
            cmd = (
                f'(command "-ATTDEF" '
                f'"{tag}" '        # 标记
                f'"{prompt}" '     # 提示
                f'"{default}" '    # 默认值
                f'"L" '            # 左对齐
                f'"{x},{y}" '      # 插入点
                f'"{height}")\n'   # 文字高度
            )
            self.doc.SendCommand(cmd)
            time.sleep(0.05)
        except Exception as e:
            logger.warning("ATTDEF 添加失败 [%s]: %s", tag, e)

    # ----------------------------------------------------------------
    # 标题栏
    # ----------------------------------------------------------------

    def _build_title_block_def(self, name, width, height):
        """创建标题栏图块定义

        包含: 外边框、内边框、分隔线、标签文字、属性定义
        """
        self._purge_block(name)

        bp = self.doc.Blocks
        origin = _pt(0, 0, 0)
        block = bp.Add(origin, name)

        # 外边框
        self._add_rect(block, 0, 0, width, height)

        # 内边框 (左侧 5mm)
        self._add_rect(block, 5, 5, width - 5, height - 5)

        # 标题区域顶部分隔线
        ty = height - 15
        self._add_line(block, 5, ty, width - 5, ty)

        # 项目名称标签
        self._add_text(block, "配电系统单线图",
                       width / 2, ty + 5,
                       height=BlockParams.LABEL_H, center=True)

        # 属性列分隔线
        col_w = (width - 10) / 4
        for i in range(1, 4):
            cx = 5 + col_w * i
            self._add_line(block, cx, 5, cx, ty)

        # 属性定义 (标签 + ATTDEF)
        attr_cfg = [
            ("PROJECT_NAME", "项目名称:", 0),
            ("DRAWING_NO",   "图纸编号:", 1),
            ("DATE",         "日    期:", 2),
            ("DESIGNER",     "设 计 人:", 3),
        ]

        for tag, label, col in attr_cfg:
            ax = 5 + col_w * col + 3
            # 标签
            self._add_text(block, label, ax, ty - 5, height=3.0)
            # ATTDEF
            self._add_attdef(
                block, tag=tag, default="",
                prompt=f"请输入{label}",
                x=ax, y=10, height=3.5,
            )

        # 在模型空间插入引用
        self.doc.ModelSpace.InsertBlock(origin, name, 1.0, 1.0, 1.0, 0.0)

    # ----------------------------------------------------------------
    # 图块编辑
    # ----------------------------------------------------------------

    def edit_block(self, block_name: str) -> bool:
        """在 AutoCAD 中打开块编辑器 (BEDIT)

        用户可以在 AutoCAD 中直接修改图块的几何图形和属性位置。

        Args:
            block_name: 要编辑的图块名

        Returns:
            True 成功打开
        """
        self._check_connected()
        self.doc = self.app.ActiveDocument

        # 检查图块是否存在
        try:
            self.doc.Blocks.Item(block_name)
        except Exception:
            logger.error("图块 '%s' 在当前文档中不存在", block_name)
            return False

        try:
            cmd = f'-BEDIT "{block_name}"\n'
            self.doc.SendCommand(cmd)
            logger.info("已打开块编辑器: %s", block_name)
            return True
        except Exception as e:
            logger.error("打开块编辑器失败: %s", e)
            return False

    def close_block_editor(self, save: bool = True):
        """关闭块编辑器

        Args:
            save: True 保存修改, False 放弃修改
        """
        self._check_connected()
        self.doc = self.app.ActiveDocument
        try:
            if save:
                self.doc.SendCommand("BCLOSE\n1\n")   # 保存
            else:
                self.doc.SendCommand("BCLOSE\n0\n")   # 不保存
            logger.info("块编辑器已关闭 (保存=%s)", save)
        except Exception as e:
            logger.warning("关闭块编辑器异常: %s", e)

    # ----------------------------------------------------------------
    # 图块清理/删除
    # ----------------------------------------------------------------

    def purge_blocks(self) -> int:
        """删除文档中所有标准图块定义

        Returns:
            删除的图块数量
        """
        self._check_connected()
        self.doc = self.app.ActiveDocument

        count = 0
        all_names = [b["name"] for b in STANDARD_BLOCKS] + ["TITLE_BLOCK"]
        for name in all_names:
            if self._purge_block(name):
                count += 1

        logger.info("已清理 %d 个图块", count)
        return count

    def _purge_block(self, name: str) -> bool:
        """删除单个图块: 先删除所有引用，再删除定义"""
        try:
            block_def = self.doc.Blocks.Item(name)
        except Exception:
            return False

        try:
            # 删除模型空间中所有该图块的引用
            ms = self.doc.ModelSpace
            i = 0
            while i < ms.Count:
                try:
                    ent = ms.Item(i)
                    if hasattr(ent, 'Name') and ent.Name == name:
                        ent.Delete()
                        continue  # 删除后索引不变
                except Exception:
                    pass
                i += 1

            block_def.Delete()
            logger.debug("图块已删除: %s", name)
            return True
        except Exception as e:
            logger.warning("删除图块 %s 失败: %s", name, e)
            return False

    # ----------------------------------------------------------------
    # 验证
    # ----------------------------------------------------------------

    def validate_library(self) -> Dict:
        """验证当前文档中的图块库完整性

        检查:
        1. 2 种标准图块是否存在 (LOOP_POWER_A / LOOP_POWER_B)
        2. TITLE_BLOCK 是否存在

        Returns:
            {
                "ok": True/False,
                "blocks": {name: {"exists": bool}},
                "title_block": True/False,
                "missing_blocks": [names],
            }
        """
        self._check_connected()
        self.doc = self.app.ActiveDocument

        result = {
            "ok": True,
            "blocks": {},
            "title_block": False,
            "missing_blocks": [],
        }

        for bdef in STANDARD_BLOCKS:
            name = bdef["name"]
            info = {"exists": False}

            try:
                self.doc.Blocks.Item(name)
                info["exists"] = True
            except Exception:
                result["ok"] = False
                result["missing_blocks"].append(name)

            result["blocks"][name] = info

        # 检查标题栏
        try:
            self.doc.Blocks.Item("TITLE_BLOCK")
            result["title_block"] = True
        except Exception:
            result["title_block"] = False

        return result

    def check_block_bounds(self) -> List[Dict]:
        """检查各图块定义的几何边界

        用于诊断图块重叠问题: 如果插入点 (0,0) 不在图块几何的
        左侧中心位置，插入后的图块可能看起来偏移或重叠。

        Returns:
            [{"name": str, "exists": bool,
              "min_x": float, "min_y": float,
              "max_x": float, "max_y": float,
              "width": float, "height": float,
              "entity_count": int}, ...]
        """
        self._check_connected()
        self.doc = self.app.ActiveDocument

        results = []
        all_names = [b["name"] for b in STANDARD_BLOCKS] + ["TITLE_BLOCK"]

        for name in all_names:
            info = {"name": name, "exists": False}
            try:
                block_def = self.doc.Blocks.Item(name)
                info["exists"] = True
                info["entity_count"] = block_def.Count

                # 遍历实体获取边界
                min_x = min_y = float('inf')
                max_x = max_y = float('-inf')

                for i in range(block_def.Count):
                    try:
                        ent = block_def.Item(i)
                        # 尝试获取实体的几何边界
                        try:
                            bb_min = ent.GetBoundingBox()
                            # GetBoundingBox 返回 (min_pt, max_pt)
                            # 但 comtypes 可能不直接支持，改用 StartPoint/EndPoint
                        except Exception:
                            pass

                        # 通用方式: 读取实体的关键点
                        for attr in ['StartPoint', 'EndPoint', 'Center',
                                     'InsertionPoint', 'Origin']:
                            try:
                                pt = getattr(ent, attr)
                                if pt:
                                    coords = list(pt)
                                    min_x = min(min_x, coords[0])
                                    min_y = min(min_y, coords[1])
                                    max_x = max(max_x, coords[0])
                                    max_y = max(max_y, coords[1])
                            except Exception:
                                pass

                    except Exception:
                        pass

                if min_x != float('inf'):
                    info["min_x"] = round(min_x, 2)
                    info["min_y"] = round(min_y, 2)
                    info["max_x"] = round(max_x, 2)
                    info["max_y"] = round(max_y, 2)
                    info["width"] = round(max_x - min_x, 2)
                    info["height"] = round(max_y - min_y, 2)
                else:
                    info["min_x"] = info["min_y"] = None
                    info["max_x"] = info["max_y"] = None
                    info["width"] = info["height"] = None

            except Exception:
                pass

            results.append(info)
            logger.info(
                "图块 %s: %s",
                name,
                f"边界 ({info.get('min_x')}, {info.get('min_y')}) "
                f"~ ({info.get('max_x')}, {info.get('max_y')}) "
                f"尺寸 {info.get('width')}x{info.get('height')}mm "
                f"({info.get('entity_count', 0)} 实体)"
                if info["exists"] else "不存在"
            )

        return results

    # ----------------------------------------------------------------
    # 保存
    # ----------------------------------------------------------------

    def save_library(self, path: str) -> bool:
        """保存图块库 DWG 文件

        Args:
            path: 保存路径 (如 ./blocks/block_library.dwg)

        Returns:
            True 保存成功
        """
        self._check_connected()
        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        try:
            self.doc.SaveAs(abs_path)
            logger.info("图块库已保存: %s", abs_path)
            return True
        except Exception as e:
            logger.error("保存失败: %s", e)
            return False

    def save_title_block(self, path: str) -> bool:
        """单独保存标题栏 DWG

        需要先 create_title_block() 创建标题栏，然后调用此方法保存。

        Args:
            path: 保存路径 (如 ./blocks/title_block.dwg)

        Returns:
            True 保存成功
        """
        return self.save_library(path)

    # ----------------------------------------------------------------
    # 生成完整图块库 (一键操作)
    # ----------------------------------------------------------------

    def generate_full_library(
        self,
        library_path: str = "./blocks/block_library.dwg",
        title_path: str = "./blocks/title_block.dwg",
    ) -> Dict:
        """一键生成完整图块库

        步骤: 新建文档 → 创建 2 种标准图块 → 创建标题栏 → 保存

        Args:
            library_path: block_library.dwg 路径
            title_path: title_block.dwg 路径

        Returns:
            {"ok": bool, "blocks_ok": int, "blocks_fail": int,
             "title_ok": bool, "library_path": str, "title_path": str}
        """
        self._check_connected()

        result = {
            "ok": False,
            "blocks_ok": 0,
            "blocks_fail": 0,
            "title_ok": False,
            "library_path": os.path.abspath(library_path),
            "title_path": os.path.abspath(title_path),
        }

        try:
            # 新建文档
            self.create_library_doc()

            # 创建标准图块
            ok, fail = self.create_all_blocks()
            result["blocks_ok"] = ok
            result["blocks_fail"] = fail

            # 保存图块库
            if not self.save_library(library_path):
                return result

            # 创建标题栏并保存
            # 新建另一个文档用于标题栏
            self.create_library_doc()
            title_ok = self.create_title_block()
            result["title_ok"] = title_ok
            if title_ok:
                self.save_library(title_path)

            result["ok"] = (fail == 0 and title_ok)
            logger.info(
                "图块库生成完成: 标准图块 %d/%d, 标题栏 %s",
                ok, ok + fail, "成功" if title_ok else "失败",
            )

        except Exception as e:
            logger.error("图块库生成失败: %s", e)

        return result

    # ----------------------------------------------------------------
    # 内部辅助方法
    # ----------------------------------------------------------------

    def _check_connected(self):
        """检查 AutoCAD COM 连接是否有效，失效时尝试自动重连"""
        if self.app is None:
            raise AcadOperationError("未连接 AutoCAD，请先点击「连接 AutoCAD」")

        # 验证 COM 引用是否仍然有效
        if not self._is_alive():
            logger.warning("COM 连接已失效，尝试重新连接...")
            try:
                self.reconnect()
            except Exception as e:
                self._connected = False
                raise AcadOperationError(
                    f"AutoCAD 连接已断开，请重新连接。\n原因: {e}"
                )

    def _is_alive(self) -> bool:
        """检测 COM 引用是否仍然有效"""
        if self.app is None:
            return False
        try:
            # 尝试访问一个轻量属性来验证连接
            _ = self.app.Name
            return True
        except Exception:
            return False

    def reconnect(self) -> bool:
        """重新连接 AutoCAD (COM 引用失效时调用)"""
        logger.info("正在重新连接 AutoCAD...")
        self._connected = False
        self.app = None
        self.doc = None
        return self.connect()

    @staticmethod
    def _ensure_sta_com():
        """确保 COM 线程模型为 STA"""
        import comtypes
        try:
            comtypes.CoInitialize()
        except OSError as e:
            if e.winerror == -2147417850:  # RPC_E_CHANGED_MODE
                comtypes.CoUninitialize()
                comtypes.CoInitialize()

    # ---- 几何辅助 ----

    def _add_line(self, block, x1, y1, x2, y2):
        """添加线段"""
        p1 = _pt(x1, y1, 0)
        p2 = _pt(x2, y2, 0)
        return block.AddLine(p1, p2)

    def _add_rect(self, block, x1, y1, x2, y2):
        """添加矩形 (4 条线段)"""
        self._add_line(block, x1, y1, x2, y1)  # 底
        self._add_line(block, x2, y1, x2, y2)  # 右
        self._add_line(block, x2, y2, x1, y2)  # 顶
        self._add_line(block, x1, y2, x1, y1)  # 左

    def _add_circle(self, block, cx, cy, r):
        """添加圆"""
        c = _pt(cx, cy, 0)
        return block.AddCircle(c, r)

    def _add_text(self, block, text, x, y, height=None, center=False):
        """添加文字

        Args:
            center: True 居中对齐, False 左对齐
        """
        if height is None:
            height = BlockParams.TEXT_H
        pt = _pt(x, y, 0)
        t = block.AddText(text, pt, height)
        if center:
            t.Alignment = ALIGN_MIDDLE
            t.TextAlignmentPoint = pt
        return t


# ================================================================
# 模块级辅助函数
# ================================================================

def _pt(x, y, z=0):
    """创建 AutoCAD COM 所需的点数组 (array of double)"""
    return array('d', [float(x), float(y), float(z)])
