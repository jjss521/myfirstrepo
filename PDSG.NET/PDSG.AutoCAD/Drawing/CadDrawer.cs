using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using PDSG.Core.Models;
using PDSG.Core.Exceptions;

namespace PDSG.AutoCAD.Drawing;

/// <summary>
/// PDSG AutoCAD 绘图引擎 — 使用托管 API 直接在 AutoCAD 进程内操作数据库
/// 替代 Python COM 跨进程方案，彻底消除 RPC_E_CALL_REJECTED 等卡死问题
/// </summary>
public class CadDrawer : IDisposable
{
    private Document? _doc;
    private Database? _db;
    private bool _disposed;

    /// <summary>
    /// 连接到当前 AutoCAD 文档
    /// </summary>
    public void Connect()
    {
        _doc = Application.DocumentManager.MdiActiveDocument
            ?? throw new AcadConnectionException("没有打开的 AutoCAD 文档");
        _db = _doc.Database;
    }

    /// <summary>
    /// 执行完整绘图流程
    /// </summary>
    public void Draw(LayoutResult layout)
    {
        EnsureConnected();

        using var tr = _db!.TransactionManager.StartTransaction();

        var bt = (BlockTable)tr.GetObject(_db.BlockTableId, OpenMode.ForRead);
        var btr = (BlockTableRecord)tr.GetObject(
            _db.CurrentSpaceId, OpenMode.ForWrite);

        // 绘制母线
        DrawBus(tr, btr, layout.BusLine);

        // 插入分组标签
        foreach (var label in layout.GroupLabels)
            DrawGroupLabel(tr, btr, label);

        // 插入所有回路图块
        int success = 0, failed = 0;
        foreach (var p in layout.Placements)
        {
            try
            {
                InsertBlock(tr, btr, bt, p);
                success++;
            }
            catch (Exception ex)
            {
                failed++;
                System.Diagnostics.Debug.WriteLine(
                    $"图块插入失败 ({p.CircuitId}): {ex.Message}");
            }
        }

        // 绘制参数表格
        if (layout.Table != null)
            DrawTable(tr, btr, layout.Table);

        tr.Commit();

        System.Diagnostics.Debug.WriteLine(
            $"绘图完成: 成功 {success}, 失败 {failed}");
    }

    /// <summary>
    /// 绘制母线（0.5mm 粗实线）
    /// </summary>
    private void DrawBus(Transaction tr, BlockTableRecord btr, BusLine bus)
    {
        Point3d p1, p2;

        if (bus.Direction == "horizontal")
        {
            p1 = new Point3d(bus.XStart, bus.BusY, 0);
            p2 = new Point3d(bus.XEnd, bus.BusY, 0);
        }
        else
        {
            p1 = new Point3d(bus.X, bus.YStart, 0);
            p2 = new Point3d(bus.X, bus.YEnd, 0);
        }

        var line = new Line(p1, p2);
        line.LineWeight = LineWeight.LineWeight050;
        btr.AppendEntity(line);
        tr.AddNewlyCreatedDBObject(line, true);
    }

    /// <summary>
    /// 插入图块引用并写入属性
    /// </summary>
    private void InsertBlock(
        Transaction tr, BlockTableRecord btr,
        BlockTable bt, Placement p)
    {
        if (!bt.Has(p.BlockName))
            throw new AcadOperationException(
                $"图块 '{p.BlockName}' 在当前文档中不存在");

        var blkRef = new BlockReference(
            new Point3d(p.X, p.Y, 0), bt[p.BlockName]);
        btr.AppendEntity(blkRef);
        tr.AddNewlyCreatedDBObject(blkRef, true);

        // 写入属性
        if (p.Attributes.Count > 0)
        {
            var btrDef = (BlockTableRecord)tr.GetObject(
                bt[p.BlockName], OpenMode.ForRead);

            foreach (var kv in p.Attributes)
            {
                foreach (var objId in btrDef)
                {
                    var ent = tr.GetObject(objId, OpenMode.ForRead);
                    if (ent is AttributeDefinition attDef
                        && attDef.Tag == kv.Key)
                    {
                        var attRef = new AttributeReference();
                        attRef.SetAttributeFromBlock(
                            attDef, blkRef.BlockTransform);
                        attRef.TextString = kv.Value;
                        tr.AddNewlyCreatedDBObject(attRef, true);
                        break;
                    }
                }
            }
        }
    }

    /// <summary>
    /// 绘制分组标签文字
    /// </summary>
    private void DrawGroupLabel(
        Transaction tr, BlockTableRecord btr, GroupLabel label)
    {
        var text = new DBText
        {
            Position = new Point3d(label.X - 20, label.Y, 0),
            TextString = label.Text,
            Height = 5.0
        };
        btr.AppendEntity(text);
        tr.AddNewlyCreatedDBObject(text, true);
    }

    /// <summary>
    /// 绘制参数表格
    /// </summary>
    private void DrawTable(
        Transaction tr, BlockTableRecord btr, TableLayout table)
    {
        double colW = table.ColWidth;
        double labelW = table.LabelColWidth;
        double rowH = table.RowHeight;
        double textH = 3.5;

        int nDataCols = table.Headers.Count;
        int nRows = table.RowLabels.Count + 1;
        double totalW = labelW + nDataCols * colW;
        double totalH = nRows * rowH;

        double x0 = table.X;
        double yTop = table.Y;

        // 水平线
        for (int i = 0; i <= nRows; i++)
        {
            double y = yTop - i * rowH;
            AddLine(tr, btr, x0, y, x0 + totalW, y);
        }

        // 垂直线
        AddLine(tr, btr, x0, yTop, x0, yTop - totalH);
        double xLabelRight = x0 + labelW;
        AddLine(tr, btr, xLabelRight, yTop, xLabelRight, yTop - totalH);

        for (int j = 1; j <= nDataCols; j++)
        {
            double x = xLabelRight + j * colW;
            AddLine(tr, btr, x, yTop, x, yTop - totalH);
        }

        // 表头
        for (int j = 0; j < nDataCols; j++)
        {
            double cx = xLabelRight + j * colW + colW / 2;
            double cy = yTop - rowH / 2;
            AddText(tr, btr, table.Headers[j], cx, cy, textH);
        }

        // 行标签
        for (int i = 0; i < table.RowLabels.Count; i++)
        {
            double cy = yTop - (i + 1) * rowH + rowH / 2;
            double cx = x0 + labelW / 2;
            AddText(tr, btr, table.RowLabels[i], cx, cy, textH);
        }

        // 数据
        for (int i = 0; i < table.Rows.Count; i++)
        {
            double cy = yTop - (i + 1) * rowH + rowH / 2;
            for (int j = 0; j < table.Rows[i].Count; j++)
            {
                if (string.IsNullOrEmpty(table.Rows[i][j])) continue;
                double cx = xLabelRight + j * colW + colW / 2;
                AddText(tr, btr, table.Rows[i][j], cx, cy, textH);
            }
        }
    }

    /// <summary>
    /// 保存 DWG 文件
    /// </summary>
    public void SaveAs(string path)
    {
        EnsureConnected();
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        var absPath = Path.GetFullPath(path);
        _doc!.Database.SaveAs(absPath, DwgVersion.Current);
    }

    /// <summary>
    /// 关闭连接（不关闭 AutoCAD）
    /// </summary>
    public void Close()
    {
        _disposed = true;
        _doc = null;
        _db = null;
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            Close();
            GC.SuppressFinalize(this);
        }
    }

    private void EnsureConnected()
    {
        if (_doc == null || _db == null)
            throw new AcadOperationException("未连接 AutoCAD，请先调用 Connect()");
    }

    private static void AddLine(
        Transaction tr, BlockTableRecord btr,
        double x1, double y1, double x2, double y2)
    {
        var line = new Line(new Point3d(x1, y1, 0), new Point3d(x2, y2, 0));
        btr.AppendEntity(line);
        tr.AddNewlyCreatedDBObject(line, true);
    }

    private static void AddText(
        Transaction tr, BlockTableRecord btr,
        string text, double x, double y, double height)
    {
        var dbText = new DBText
        {
            Position = new Point3d(x, y, 0),
            TextString = text,
            Height = height
        };
        btr.AppendEntity(dbText);
        tr.AddNewlyCreatedDBObject(dbText, true);
    }
}
