"""PDSG AutoCAD 绘图器

通过 COM 直接驱动 AutoCAD（绕过 pyautocad 的连接），实现:
- 连接 AutoCAD（多版本 ProgID 探测）
- 导入图块库
- 插入图块引用并填写属性
- 绘制母线（粗实线）
- 插入图框
- 保存 DWG
"""
import logging
import os
import time
from typing import Dict, List, Optional, Tuple

import comtypes

from .data_model import (
    AcadConfig,
    BlockLibraryConfig,
    BusLine,
    GroupLabel,
    LayoutConfig,
    LayoutResult,
    Placement,
    TextStyleConfig,
    TitleBlockConfig,
)
from .errors import AcadConnectionError, AcadOperationError

logger = logging.getLogger(__name__)

# AutoCAD COM 繁忙错误码
RPC_E_CALL_REJECTED = -2147418111


def _apoint(x, y, z=0):
    """创建 AutoCAD 所需的点数组（3 个 double）"""
    from array import array
    return array('d', [float(x), float(y), float(z)])


def _com_retry(fn, desc: str = "COM操作", max_retries: int = 3, delay: float = 1.0):
    """COM 操作重试包装器

    AutoCAD COM 经常返回 RPC_E_CALL_REJECTED (-2147418111)
    表示 "被呼叫方拒绝接收呼叫"，通常是因为上一个操作尚未完成。
    本函数自动重试，等待 AutoCAD 就绪。
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            err_code = getattr(e, 'hresult', None) or getattr(e, 'args', (None,))[0]
            if err_code == RPC_E_CALL_REJECTED or '被呼叫方' in str(e):
                logger.warning(
                    "%s: AutoCAD 繁忙 (尝试 %d/%d)，%.1f 秒后重试...",
                    desc, attempt + 1, max_retries, delay,
                )
                time.sleep(delay)
            else:
                raise
    raise last_error


def _read_point_attr(obj, attr_name: str) -> Optional[Tuple[float, float]]:
    """安全读取 COM 对象的点属性 (StartPoint, EndPoint 等)

    返回 (x, y) 或 None。
    """
    try:
        pt = getattr(obj, attr_name, None)
        if pt is None:
            return None
        # comtypes 可能返回 tuple, list, 或 array
        coords = list(pt)
        if len(coords) >= 2:
            return (float(coords[0]), float(coords[1]))
    except Exception:
        pass
    return None


class CadDrawer:
    """AutoCAD 绘图器（直接使用 COM 对象）"""

    def __init__(self):
        self.app = None    # AutoCAD Application COM 对象
        self.doc = None    # 当前文档 COM 对象
        self.model = None  # ModelSpace COM 对象
        self._connected = False
        # 自动检测到的块内水平母线 X 偏移（块坐标系内）
        self._block_bus_offset_x: float = 0.0

    def connect(self, acad_cfg: AcadConfig) -> bool:
        """连接 AutoCAD"""
        try:
            import comtypes
            import comtypes.client
        except ImportError as e:
            raise AcadConnectionError(
                f"缺少依赖: {e}。请安装: pip install comtypes"
            )

        self._ensure_sta_com()

        last_error = None
        for progid in acad_cfg.progids:
            try:
                logger.debug("尝试连接: %s", progid)
                self.app = comtypes.client.GetActiveObject(progid)
                self.doc = self.app.ActiveDocument
                self.model = self.app.ActiveDocument.ModelSpace
                self._connected = True

                if acad_cfg.visible:
                    try:
                        self.app.Visible = True
                    except Exception:
                        pass

                logger.info(
                    "AutoCAD 连接成功: %s (版本 %s)",
                    progid, self.app.Version,
                )
                return True

            except Exception as e:
                last_error = e
                logger.debug("连接 %s 失败: %s", progid, e)

        raise AcadConnectionError(
            f"无法连接 AutoCAD。已尝试: {acad_cfg.progids}。"
            f"请确认 AutoCAD 已启动。最后错误: {last_error}"
        )

    def new_document(self) -> None:
        """新建空白文档"""
        if not self._connected:
            raise AcadOperationError("未连接 AutoCAD")
        try:
            self.doc = self.app.Documents.Add()
            self.model = self.doc.ModelSpace
            logger.debug("新建文档")
        except Exception as e:
            raise AcadOperationError(f"新建文档失败: {e}")

    def open_library_as_working_doc(self, lib_cfg: BlockLibraryConfig) -> None:
        """打开图块库 DWG 作为工作文档

        直接在图块库文件中绘图（图块定义已存在其中），
        然后通过 save_as() 另存为输出文件。

        打开后自动检测块内水平母线位置，用于后续精准拼接。
        """
        if not self._connected:
            raise AcadOperationError("未连接 AutoCAD")

        lib_path = os.path.abspath(lib_cfg.path)
        if not os.path.isfile(lib_path):
            from .errors import BlockLibraryError
            raise BlockLibraryError(f"图块库 DWG 不存在: {lib_path}")

        try:
            self.doc = self.app.Documents.Open(lib_path, False)
            time.sleep(2)  # 等待 AutoCAD 完成文件加载
            self.model = self.doc.ModelSpace

            # 彻底清理模型空间
            self._clean_model_space()
            time.sleep(1)

            # 自动检测块内水平母线位置
            self._auto_detect_bus_offset(lib_cfg)

            logger.info("已打开图块库作为工作文档: %s", lib_path)
        except Exception as e:
            raise AcadOperationError(f"打开图块库失败: {e}")

    # ----------------------------------------------------------------
    # 模型空间清理
    # ----------------------------------------------------------------

    def _clean_model_space(self) -> None:
        """彻底清理模型空间中的所有实体（保留图块定义）

        使用循环删除策略: 反复删除直到 Count=0，
        避免单次遍历遗漏（某些实体删除后索引重排）。
        """
        try:
            ms = self.doc.ModelSpace
            total_deleted = 0
            max_rounds = 20

            for round_num in range(max_rounds):
                count = ms.Count
                if count == 0:
                    break
                deleted_this_round = 0
                for i in range(count - 1, -1, -1):
                    try:
                        ms.Item(i).Delete()
                        deleted_this_round += 1
                    except Exception:
                        pass
                total_deleted += deleted_this_round
                if deleted_this_round == 0:
                    break  # 无法删除更多
                logger.debug(
                    "清理第 %d 轮: 删除 %d 个实体",
                    round_num + 1, deleted_this_round,
                )

            # 最终验证
            remaining = ms.Count
            if remaining > 0:
                logger.warning(
                    "模型空间清理不完整: 剩余 %d 个实体", remaining
                )
            else:
                logger.info("模型空间已彻底清理: 共删除 %d 个实体", total_deleted)

        except Exception as e:
            logger.warning("清理模型空间失败: %s", e)

    # ----------------------------------------------------------------
    # 块内母线自动检测 + 拼接
    # ----------------------------------------------------------------

    def _auto_detect_bus_offset(
        self, lib_cfg: BlockLibraryConfig
    ) -> None:
        """自动检测块内水平母线的 X 位置

        扫描第一个可用图块定义，找到 y≈0 附近的水平线段，
        记录其 X 起点。此值用于在 draw() 中自动修正插入位置，
        使块内水平母线与绘制的垂直母线精准对齐。
        """
        block_names = self._get_block_names_from_catalog(lib_cfg)
        if not block_names:
            return

        for name in block_names:
            result = self._scan_block_geometry(name)
            if result and result.get("h_bus_x") is not None:
                self._block_bus_offset_x = result["h_bus_x"]
                logger.info(
                    "自动检测: 图块 %s 水平母线在 x=%.1f, "
                    "插入时将自动补偿偏移",
                    name, self._block_bus_offset_x,
                )
                return

        logger.info("未检测到块内水平母线，使用配置偏移量")
        self._block_bus_offset_x = 0.0

    def _scan_block_geometry(self, block_name: str) -> Optional[Dict]:
        """扫描图块定义内的线段，分析母线位置

        Returns:
            {
                "h_bus_x": float,     # 水平母线的 X 起点 (块坐标系)
                "h_bus_y": float,     # 水平母线的 Y 坐标
                "h_bus_len": float,   # 水平母线长度
                "v_lines": [...],     # 垂直线信息
                "entity_count": int,
            }
            或 None (图块不存在)
        """
        try:
            block_def = self.doc.Blocks.Item(block_name)
        except Exception:
            return None

        result = {
            "entity_count": block_def.Count,
            "h_bus_x": None,
            "h_bus_y": None,
            "h_bus_len": 0,
            "v_lines": [],
        }

        h_bus_best_dist = float('inf')

        for i in range(block_def.Count):
            try:
                ent = block_def.Item(i)
                ent_name = ent.EntityName if hasattr(ent, 'EntityName') else ""

                if "Line" not in ent_name and "AcDbLine" not in str(ent_name):
                    continue

                sp = _read_point_attr(ent, 'StartPoint')
                ep = _read_point_attr(ent, 'EndPoint')
                if not sp or not ep:
                    continue

                x1, y1 = sp
                x2, y2 = ep
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)

                # 检测水平线 (dy < 1mm, 长度 > 5mm)
                if dy < 1.0 and dx > 5.0:
                    avg_y = (y1 + y2) / 2
                    dist = abs(avg_y)
                    line_x = min(x1, x2)
                    if dist < h_bus_best_dist:
                        h_bus_best_dist = dist
                        result["h_bus_x"] = round(line_x, 2)
                        result["h_bus_y"] = round(avg_y, 2)
                        result["h_bus_len"] = round(dx, 2)

                # 检测垂直线 (dx < 1mm, 长度 > 5mm)
                if dx < 1.0 and dy > 5.0:
                    avg_x = (x1 + x2) / 2
                    result["v_lines"].append({
                        "x": round(avg_x, 2),
                        "y_start": round(min(y1, y2), 2),
                        "y_end": round(max(y1, y2), 2),
                        "len": round(dy, 2),
                    })

            except Exception:
                pass

        logger.debug(
            "扫描图块 %s: %d 实体, 水平母线 x=%.1f y=%.1f (长 %.0f), "
            "%d 条垂直线",
            block_name, result["entity_count"],
            result["h_bus_x"] or 0, result["h_bus_y"] or 0,
            result["h_bus_len"], len(result["v_lines"]),
        )
        return result

    def diagnose_blocks(self) -> List[Dict]:
        """诊断当前文档中所有标准图块的几何结构

        返回每个图块的线段分析结果，帮助排查拼接问题。
        可通过 GUI 的「诊断图块」按钮调用。
        """
        from .block_editor import STANDARD_BLOCKS
        results = []
        for bdef in STANDARD_BLOCKS:
            info = self._scan_block_geometry(bdef["name"])
            if info:
                info["name"] = bdef["name"]
                results.append(info)
                logger.info(
                    "诊断 %s: %d 实体, 水平母线 x=%.1f y=%.1f (长 %.0fmm), "
                    "%d 条垂直线",
                    bdef["name"], info["entity_count"],
                    info["h_bus_x"] or 0, info["h_bus_y"] or 0,
                    info["h_bus_len"], len(info["v_lines"]),
                )
            else:
                logger.warning("诊断 %s: 图块不存在", bdef["name"])
        return results

    # ----------------------------------------------------------------
    # 图块导入（兼容旧接口）
    # ----------------------------------------------------------------

    def load_blocks(self, lib_cfg: BlockLibraryConfig) -> None:
        """导入图块库（兼容旧接口）"""
        if not self._connected:
            raise AcadOperationError("未连接 AutoCAD")

        block_names = self._get_block_names_from_catalog(lib_cfg)
        all_exist = True
        for name in block_names:
            try:
                self.doc.Blocks.Item(name)
            except Exception:
                all_exist = False
                break

        if all_exist and block_names:
            logger.info("所有图块已在当前文档中定义，无需导入")
            return

        lib_path = os.path.abspath(lib_cfg.path)
        if not os.path.isfile(lib_path):
            from .errors import BlockLibraryError
            raise BlockLibraryError(f"图块库 DWG 不存在: {lib_path}")

        imported = 0
        for name in block_names:
            try:
                try:
                    self.doc.Blocks.Item(name)
                    imported += 1
                    continue
                except Exception:
                    pass

                cmd = (
                    f'(command "-INSERT" '
                    f'"{name}={lib_path}" '
                    f'"0,0" "" "" "")\n'
                )
                self.doc.SendCommand(cmd)
                time.sleep(1.5)
                imported += 1
            except Exception as e:
                logger.warning("导入图块 %s 失败: %s", name, e)

        time.sleep(2)
        logger.info("已导入 %d/%d 个图块定义", imported, len(block_names))

    def _get_block_names_from_catalog(
        self, lib_cfg: BlockLibraryConfig
    ) -> List[str]:
        """从图块目录 YAML 获取需要导入的图块名列表"""
        catalog_path = os.path.abspath(lib_cfg.catalog)
        if not os.path.isfile(catalog_path):
            logger.warning("图块目录文件不存在: %s，使用默认图块", catalog_path)
            return [lib_cfg.default_block]

        try:
            import yaml
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            names = [b["name"] for b in data.get("blocks", []) if b.get("name")]
            logger.debug("从目录加载图块名: %s", names)
            return names
        except Exception as e:
            logger.warning("读取图块目录失败: %s，使用默认图块", e)
            return [lib_cfg.default_block]

    # ----------------------------------------------------------------
    # 绘图
    # ----------------------------------------------------------------

    def draw(self, layout: LayoutResult, layout_cfg: LayoutConfig) -> None:
        """执行绘图

        自动拼接逻辑:
        - 如果检测到块内水平母线位置 (_block_bus_offset_x)，
          自动修正图块插入 X 坐标，使水平母线与垂直母线精准对齐。
        - 修正公式: actual_x = bus_x + (layout_x - bus_x) - block_bus_offset_x
          当 block_offset_x=15 且块内母线在 x=0 时:
          actual_x = 100 + 15 - 0 = 115 (不变)
          当块内母线在 x=15 时:
          actual_x = 100 + 15 - 15 = 100 (插入点移到母线上)
        """
        if not self._connected:
            raise AcadOperationError("未连接 AutoCAD")

        # 设置图纸界限
        self._set_paper_limits(layout.paper_size)

        # 计算 X 轴补偿: 让块内水平母线对齐到垂直母线
        bus_x = layout.bus_line.x
        x_correction = self._block_bus_offset_x
        if abs(x_correction) > 0.1:
            logger.info(
                "自动拼接: 块内水平母线在 x=%.1f, 插入 X 将补偿 %.1fmm",
                x_correction, -x_correction,
            )

        # 绘制母线
        self.draw_bus(layout.bus_line)

        # 插入分组标签
        for label in layout.group_labels:
            self._draw_group_label(label)

        # 记录前几个图块的坐标
        for i, p in enumerate(layout.placements[:5]):
            corrected_x = p.x - x_correction
            logger.info(
                "布局坐标 [%d]: %s @ (%.1f, %.1f) -> %s"
                + (" [补偿后 %.1f]" if abs(x_correction) > 0.1 else ""),
                i + 1, p.circuit_id, p.x, p.y, p.block_name,
                corrected_x,
            )
        if len(layout.placements) > 5:
            logger.info("  ... 共 %d 个回路", len(layout.placements))

        # 插入图块
        success = 0
        failed = 0
        for placement in layout.placements:
            try:
                # 应用 X 补偿
                actual_x = placement.x - x_correction
                self._place_block_at(
                    actual_x, placement.y, placement
                )
                success += 1
            except Exception as e:
                failed += 1
                logger.warning(
                    "图块插入失败 (回路 %s): %s",
                    placement.circuit_id, e,
                )

        logger.info("已插入 %d/%d 回路（失败 %d）", success, success + failed, failed)

        # 绘制参数表格
        if layout.table:
            self.draw_table(layout.table)

    def draw_bus(self, bus_line: BusLine) -> None:
        """绘制母线（0.5mm 粗实线）

        支持水平和垂直两种方向。
        """
        def _do_draw():
            if bus_line.direction == "horizontal":
                p1 = _apoint(bus_line.x_start, bus_line.bus_y, 0)
                p2 = _apoint(bus_line.x_end, bus_line.bus_y, 0)
            else:
                p1 = _apoint(bus_line.x, bus_line.y_start, 0)
                p2 = _apoint(bus_line.x, bus_line.y_end, 0)
            line = self.model.AddLine(p1, p2)
            line.Lineweight = 50

        try:
            _com_retry(_do_draw, "绘制母线", max_retries=3, delay=1.5)
            if bus_line.direction == "horizontal":
                logger.debug("水平母线: Y=%.1f, X=[%.1f ~ %.1f]",
                             bus_line.bus_y, bus_line.x_start, bus_line.x_end)
            else:
                logger.debug("垂直母线: X=%.1f, Y=[%.1f ~ %.1f]",
                             bus_line.x, bus_line.y_start, bus_line.y_end)
        except Exception as e:
            raise AcadOperationError(f"母线绘制失败: {e}")

    def _place_block_at(
        self, x: float, y: float, placement: Placement
    ) -> None:
        """在指定坐标插入图块引用（带重试）"""
        def _do_insert():
            insert_point = _apoint(x, y, 0)
            block_ref = self.model.InsertBlock(
                insert_point,
                placement.block_name,
                1.0, 1.0, 1.0, 0.0,
            )
            if placement.attributes:
                try:
                    attrs = block_ref.GetAttributes()
                    for attr in attrs:
                        tag = attr.TagString
                        if tag in placement.attributes:
                            attr.TextString = placement.attributes[tag]
                except Exception as e:
                    logger.warning(
                        "属性写入警告 (回路 %s): %s",
                        placement.circuit_id, e,
                    )

        _com_retry(
            _do_insert,
            f"插入 {placement.block_name} [{placement.circuit_id}]",
            max_retries=3,
            delay=1.0,
        )
        logger.debug(
            "图块已插入: %s @ (%.1f, %.1f) 回路=%s",
            placement.block_name, x, y, placement.circuit_id,
        )

    def place_block(self, placement: Placement) -> None:
        """插入图块引用（兼容旧接口，不做 X 补偿）"""
        try:
            self._place_block_at(
                placement.x, placement.y, placement
            )
        except Exception as e:
            raise AcadOperationError(
                f"图块插入失败 ({placement.block_name} @ {placement.circuit_id}): {e}"
            )

    def _draw_group_label(self, label: GroupLabel) -> None:
        """绘制分组标签文字"""
        def _do_draw():
            point = _apoint(label.x - 20, label.y, 0)
            self.model.AddText(label.text, point, 5.0)

        try:
            _com_retry(_do_draw, f"分组标签 '{label.text}'", max_retries=2, delay=1.0)
            logger.debug("分组标签: \"%s\" @ (%.1f, %.1f)", label.text, label.x, label.y)
        except Exception as e:
            logger.warning("分组标签绘制失败: %s", e)

    # ----------------------------------------------------------------
    # 参数表格
    # ----------------------------------------------------------------

    def draw_table(self, table) -> None:
        """绘制参数表格

        表格结构:
        - 第0列: 行标签 (回路编号, 回路名称, ...)
        - 第1~N列: 各回路数据
        - 表头行: 回路编号

        用线段画网格，用文字填充单元格。
        """
        from .data_model import TableLayout
        if not isinstance(table, TableLayout):
            return

        col_w = table.col_width
        label_w = table.label_col_width  # 行标签列宽
        row_h = table.row_height
        text_h = 3.5  # 文字高度

        n_data_cols = len(table.headers)
        n_rows = len(table.row_labels) + 1  # +1 for header row
        total_w = label_w + n_data_cols * col_w
        total_h = n_rows * row_h

        # 表格左上角坐标
        x0 = table.x
        y_top = table.y  # 表格顶部 Y

        logger.info(
            "绘制参数表格: %d 列 x %d 行, 宽 %.0fmm, 高 %.0fmm",
            n_data_cols + 1, n_rows, total_w, total_h,
        )

        # 画水平线 (n_rows + 1 条)
        for i in range(n_rows + 1):
            y = y_top - i * row_h
            self._safe_add_line(x0, y, x0 + total_w, y)

        # 画垂直线 (n_data_cols + 2 条)
        # 第0条: 最左
        self._safe_add_line(x0, y_top, x0, y_top - total_h)
        # 第1条: 标签列右边界
        x_label_right = x0 + label_w
        self._safe_add_line(x_label_right, y_top, x_label_right, y_top - total_h)
        # 数据列分隔线
        for j in range(1, n_data_cols + 1):
            x = x_label_right + j * col_w
            self._safe_add_line(x, y_top, x, y_top - total_h)

        # 填充表头 (回路编号)
        for j, header in enumerate(table.headers):
            cx = x_label_right + j * col_w + col_w / 2
            cy = y_top - row_h / 2
            self._safe_add_text(header, cx, cy, text_h, center=True)

        # 填充行标签
        for i, label in enumerate(table.row_labels):
            cy = y_top - (i + 1) * row_h + row_h / 2
            cx = x0 + label_w / 2
            self._safe_add_text(label, cx, cy, text_h, center=True)

        # 填充数据
        for i, row_data in enumerate(table.rows):
            cy = y_top - (i + 1) * row_h + row_h / 2
            for j, cell_text in enumerate(row_data):
                if not cell_text:
                    continue
                cx = x_label_right + j * col_w + col_w / 2
                self._safe_add_text(cell_text, cx, cy, text_h, center=True)

        logger.info("参数表格绘制完成")

    def _safe_add_line(self, x1, y1, x2, y2) -> None:
        """安全绘制线段（带重试）"""
        def _do():
            p1 = _apoint(x1, y1, 0)
            p2 = _apoint(x2, y2, 0)
            self.model.AddLine(p1, p2)
        try:
            _com_retry(_do, "画线", max_retries=2, delay=0.5)
        except Exception as e:
            logger.debug("画线失败 (%.1f,%.1f)->(%.1f,%.1f): %s", x1, y1, x2, y2, e)

    def _safe_add_text(self, text, x, y, height, center=False) -> None:
        """安全添加文字（带重试）"""
        def _do():
            pt = _apoint(x, y, 0)
            t = self.model.AddText(text, pt, height)
            if center:
                # 居中对齐: 设置对齐方式和锚点
                try:
                    t.Alignment = 10  # acAlignmentMiddleCenter
                    t.TextAlignmentPoint = pt
                except Exception:
                    pass
        try:
            _com_retry(_do, f"文字'{text[:10]}'", max_retries=2, delay=0.3)
        except Exception as e:
            logger.debug("文字绘制失败 '%s': %s", text, e)

    def insert_title_block(
        self, cfg: TitleBlockConfig, paper_size=None
    ) -> None:
        """插入图框

        根据纸张幅面自动选择对应的图块:
        - cfg.blocks 定义了 幅面名 → 图块名 的映射
        - 如 A1 → "A1", A2 → "A2"
        - 未匹配时使用 cfg.default_block
        """
        if not cfg.enabled:
            return

        # 根据幅面选择图块名
        block_name = cfg.default_block
        if paper_size and cfg.blocks:
            for size_key, blk_name in cfg.blocks.items():
                if size_key in paper_size.name:
                    block_name = blk_name
                    break

        try:
            insert_point = _apoint(cfg.insert_at_x, cfg.insert_at_y, 0)
            block_ref = self.model.InsertBlock(
                insert_point,
                block_name,
                1.0, 1.0, 1.0, 0.0,
            )
            try:
                for attr in block_ref.GetAttributes():
                    tag = attr.TagString
                    if tag in cfg.attributes:
                        attr.TextString = cfg.attributes[tag]
            except Exception:
                pass
            logger.info("图框已插入: %s (幅面 %s)", block_name,
                        paper_size.name if paper_size else "未知")
        except Exception as e:
            logger.warning("图框插入失败 (%s): %s", block_name, e)

    def save_as(self, path: str) -> None:
        """保存 DWG 文件

        处理常见保存错误:
        - 先关闭其他打开的文档，释放文件锁
        - 使用显式 DWG 格式参数
        - 主路径失败时自动用带时间戳的备用路径
        """
        if not self._connected:
            raise AcadOperationError("未连接 AutoCAD")

        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        # 关闭除当前文档外的其他文档，释放文件锁
        self._close_other_documents()

        acR24_DWG = 60  # AutoCAD 2013+ DWG 格式

        def _do_save(target_path):
            self.doc.SaveAs(target_path, acR24_DWG)

        try:
            _com_retry(lambda: _do_save(abs_path), "保存 DWG", max_retries=3, delay=1.5)
            logger.info("已保存: %s", abs_path)
        except Exception as e:
            # 备用路径: 加时间戳
            base, ext = os.path.splitext(abs_path)
            import datetime
            ts = datetime.datetime.now().strftime("%H%M%S")
            fallback = f"{base}_{ts}{ext}"
            try:
                _do_save(fallback)
                logger.warning("主路径保存失败，已保存到备用路径: %s", fallback)
            except Exception as e2:
                raise AcadOperationError(
                    f"保存失败 (主路径和备用路径均失败):\n"
                    f"  主路径: {e}\n  备用路径: {e2}"
                )

    def _close_other_documents(self) -> None:
        """关闭除当前工作文档外的所有打开文档"""
        try:
            docs = self.app.Documents
            current_name = self.doc.Name
            for i in range(docs.Count - 1, -1, -1):
                try:
                    d = docs.Item(i)
                    if d.Name != current_name:
                        d.Close(False)  # 不保存
                except Exception:
                    pass
        except Exception as e:
            logger.debug("关闭其他文档失败（可忽略）: %s", e)

    def _set_paper_limits(self, paper_size) -> None:
        """设置图纸界限"""
        def _do_set():
            self.doc.SetVariable("LIMMIN", _apoint(0, 0, 0))
            self.doc.SetVariable("LIMMAX", _apoint(paper_size.width, paper_size.height, 0))

        try:
            _com_retry(_do_set, "设置图纸界限", max_retries=2, delay=1.0)
            logger.debug("图纸界限: %s (%.0fx%.0f)",
                         paper_size.name, paper_size.width, paper_size.height)
        except Exception as e:
            logger.debug("设置图纸界限失败（可忽略）: %s", e)

    def _ensure_sta_com(self):
        """确保当前线程的 COM 处于 STA 模式"""
        import comtypes
        import threading
        
        # 检查是否在主线程
        if threading.current_thread() is not threading.main_thread():
            logger.warning("COM 操作不在主线程，可能导致死锁")
        
        try:
            comtypes.CoInitialize()
        except OSError as e:
            # -2147417850 = RPC_E_WRONG_THREAD: 当前线程未初始化COM
            # -2147417848 = RPC_E_CHANGED_MODE: COM已被初始化为不同模式
            if e.winerror == -2147417850:
                logger.debug("COM 当前线程未初始化，正在初始化")
                comtypes.CoInitialize()
            elif e.winerror == -2147417848:
                logger.debug("COM 已初始化为不同模式，重新初始化")
                comtypes.CoUninitialize()
                comtypes.CoInitialize()
            else:
                logger.warning("COM 初始化异常（可忽略）: %s", e)

    def close(self) -> None:
        """关闭连接（不关闭 AutoCAD），释放 COM 引用"""
        self._connected = False
        self.app = None
        self.doc = None
        self.model = None
        try:
            comtypes.CoUninitialize()
        except Exception:
            pass
