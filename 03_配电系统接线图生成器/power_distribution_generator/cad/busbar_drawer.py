"""
母线绘制与更新模块

参照《氛围化编程指令书_配电系统图生成器.md》第4.4节和第6.5节。
负责在AutoCAD中绘制水平母线Polyline，以及在回路数量变化时
更新母线终点坐标。
"""

from cad.cad_driver import CADDriver, safe_cad_call, _com_point, _com_safearray

# 母线宽度（CAD单位，第6.5节）
BUSBAR_WIDTH = 5.0


class BusbarDrawer:
    """母线绘制器

    封装水平母线的绘制与更新操作。
    """

    def __init__(self, cad_driver: CADDriver):
        """
        Args:
            cad_driver: CADDriver实例
        """
        self.cad = cad_driver

    def draw_busbar(self, start_point: tuple, end_point: tuple,
                    busbar_handle: str = None) -> str:
        """绘制或延长母线（水平Polyline）

        参照《氛围化编程指令书_配电系统图生成器.md》第6.5节。

        Args:
            start_point: 起点坐标 (x, y, z)
            end_point: 终点坐标 (x, y, z)
            busbar_handle: 已有母线句柄，None表示首次绘制

        Returns:
            母线句柄
        """
        if busbar_handle is None:
            return self._create_busbar(start_point, end_point)
        else:
            return self._extend_busbar(busbar_handle, end_point)

    def _create_busbar(self, start_point: tuple, end_point: tuple) -> str:
        """首次绘制母线

        Args:
            start_point: 起点坐标
            end_point: 终点坐标

        Returns:
            母线句柄
        """
        def _create():
            points = [
                float(start_point[0]), float(start_point[1]),
                float(end_point[0]), float(end_point[1]),
            ]
            pl = self.cad.ms.AddLightweightPolyline(_com_safearray(points))
            pl.ConstantWidth = BUSBAR_WIDTH
            return str(pl.Handle)

        return safe_cad_call(_create)

    def _extend_busbar(self, busbar_handle: str, end_point: tuple) -> str:
        """增量修改母线终点坐标

        Args:
            busbar_handle: 已有母线句柄
            end_point: 新的终点坐标

        Returns:
            母线句柄
        """
        def _extend():
            pl = self.cad.doc.HandleToObject(busbar_handle)
            coord_count = pl.NumberOfVertices

            if coord_count >= 2:
                # 修改最后一个顶点
                pl.SetPoint(coord_count - 1, _com_point(
                    float(end_point[0]), float(end_point[1]), 0.0
                ))

            return busbar_handle

        return safe_cad_call(_extend)

    def calculate_busbar_y(self, base_point: tuple) -> float:
        """计算母线的Y坐标

        母线的Y坐标 = 基准点Y - BUSBAR_OFFSET（第4.4节）。
        注意：实际项目中图块连接点位置由DWG设计决定，
        此处使用通用偏移值。

        Args:
            base_point: 基准点坐标 (x, y, z)

        Returns:
            母线Y坐标
        """
        return float(base_point[1]) - 800  # BUSBAR_OFFSET

    def calculate_circuit_position(self, base_point: tuple,
                                   circuit_index: int,
                                   spacing: int = 3000) -> tuple:
        """计算回路图块的插入位置

        回路i的插入点: x = base_x + i × spacing, y = base_y（第4.4节）。

        Args:
            base_point: 基准点坐标
            circuit_index: 回路序号（从0开始）
            spacing: 回路间距（CAD单位，默认3000）

        Returns:
            插入点坐标 (x, y, z)
        """
        x = float(base_point[0]) + circuit_index * spacing
        y = float(base_point[1])
        z = float(base_point[2]) if len(base_point) > 2 else 0.0
        return (x, y, z)
