using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using PDSG.Core.Models;
using PDSG.Core.Mapping;
using PDSG.Core.Exceptions;

namespace PDSG.AutoCAD.Drawing;

/// <summary>
/// PDSG AutoCAD 图块编辑器 — 使用托管 API 在 AutoCAD 中创建和管理回路图块
/// 核心原则：只使用图形内已存在的块名，与自动插入的回路块名对应并复核
/// </summary>
public class BlockEditor : IDisposable
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
    /// 获取当前文档中所有块定义的名称
    /// </summary>
    public List<string> GetAllBlockNames()
    {
        EnsureConnected();
        var names = new List<string>();

        using var tr = _db!.TransactionManager.StartTransaction();
        var bt = (BlockTable)tr.GetObject(_db.BlockTableId, OpenMode.ForRead);

        foreach (var objId in bt)
        {
            var btr = (BlockTableRecord)tr.GetObject(objId, OpenMode.ForRead);
            // 跳过模型空间和图纸空间
            if (btr.IsLayout) continue;
            names.Add(btr.Name);
        }

        return names;
    }

    /// <summary>
    /// 获取图形中所有回路类块名（LOOP_、VFD_ 等前缀）
    /// </summary>
    public List<string> GetCircuitBlockNames()
    {
        var allNames = GetAllBlockNames();
        var prefixes = new[] { "LOOP_", "VFD_", "LGT_", "AC_", "SKT_", "SPR_", "CAP_" };

        return allNames
            .Where(n => prefixes.Any(p => n.StartsWith(p, StringComparison.OrdinalIgnoreCase)))
            .OrderBy(n => n)
            .ToList();
    }

    /// <summary>
    /// 复核图块目录与图形中块名的一致性
    /// </summary>
    public BlockValidationResult ValidateCatalog(BlockManager catalog)
    {
        var drawingNames = GetAllBlockNames();
        return catalog.ValidateAgainstDrawing(drawingNames);
    }

    /// <summary>
    /// 创建新的回路图块定义
    /// </summary>
    public bool CreateBlock(string name, string description, double width = 42, double height = 10)
    {
        EnsureConnected();

        using var tr = _db!.TransactionManager.StartTransaction();
        var bt = (BlockTable)tr.GetObject(_db.BlockTableId, OpenMode.ForWrite);
        var btr = (BlockTableRecord)tr.GetObject(
            _db.CurrentSpaceId, OpenMode.ForWrite);

        // 检查是否已存在
        if (bt.Has(name))
        {
            // 删除已存在的图块
            PurgeBlock(tr, bt, name);
        }

        // 创建新的块定义
        var blockDef = new BlockTableRecord
        {
            Name = name,
            Origin = new Point3d(0, 0, 0)
        };
        bt.Add(blockDef);
        tr.AddNewlyCreatedDBObject(blockDef, true);

        // 绘制占位矩形
        var halfH = height / 2;
        AddLine(tr, blockDef, 0, -halfH, width, -halfH);
        AddLine(tr, blockDef, width, -halfH, width, halfH);
        AddLine(tr, blockDef, width, halfH, 0, halfH);
        AddLine(tr, blockDef, 0, halfH, 0, -halfH);

        // 添加描述文字
        var text = new DBText
        {
            Position = new Point3d(width / 2, 0, 0),
            TextString = description,
            Height = 2.5
        };
        blockDef.AppendEntity(text);
        tr.AddNewlyCreatedDBObject(text, true);

        // 在模型空间插入引用（确保 DWG 中包含定义）
        var blkRef = new BlockReference(new Point3d(0, 0, 0), blockDef.ObjectId);
        btr.AppendEntity(blkRef);
        tr.AddNewlyCreatedDBObject(blkRef, true);

        tr.Commit();
        return true;
    }

    /// <summary>
    /// 修改已有图块的描述
    /// </summary>
    public bool UpdateBlockDescription(string name, string newDescription)
    {
        EnsureConnected();

        using var tr = _db!.TransactionManager.StartTransaction();
        var bt = (BlockTable)tr.GetObject(_db.BlockTableId, OpenMode.ForRead);

        if (!bt.Has(name)) return false;

        var btr = (BlockTableRecord)tr.GetObject(bt[name], OpenMode.ForWrite);

        // 查找并更新描述文字
        foreach (var objId in btr)
        {
            var ent = tr.GetObject(objId, OpenMode.ForRead);
            if (ent is DBText text)
            {
                text.UpgradeOpen();
                text.TextString = newDescription;
                break;
            }
        }

        tr.Commit();
        return true;
    }

    /// <summary>
    /// 删除图块定义（先删除所有引用）
    /// </summary>
    public bool DeleteBlock(string name)
    {
        EnsureConnected();

        using var tr = _db!.TransactionManager.StartTransaction();
        var bt = (BlockTable)tr.GetObject(_db.BlockTableId, OpenMode.ForWrite);

        if (!bt.Has(name)) return false;

        PurgeBlock(tr, bt, name);
        tr.Commit();
        return true;
    }

    /// <summary>
    /// 批量创建图块（从 BlockManager 加载）
    /// </summary>
    public (int success, int failed) CreateBlocksFromCatalog(BlockManager catalog)
    {
        int success = 0, failed = 0;

        foreach (var block in catalog.Blocks)
        {
            try
            {
                CreateBlock(block.Name, block.Description);
                success++;
            }
            catch
            {
                failed++;
            }
        }

        return (success, failed);
    }

    /// <summary>
    /// 在 AutoCAD 中打开块编辑器 (BEDIT)
    /// </summary>
    public bool OpenBlockEditor(string blockName)
    {
        EnsureConnected();

        using var tr = _db!.TransactionManager.StartTransaction();
        var bt = (BlockTable)tr.GetObject(_db.BlockTableId, OpenMode.ForRead);

        if (!bt.Has(blockName)) return false;

        // 通过 Editor 打开 BEDIT
        _doc!.Editor.WriteMessage($"\n请在 AutoCAD 中执行: -BEDIT \"{blockName}\"");
        return true;
    }

    /// <summary>
    /// 关闭块编辑器
    /// </summary>
    public void CloseBlockEditor(bool save = true)
    {
        EnsureConnected();
        _doc!.Editor.WriteMessage(save ? "\n请在 AutoCAD 中执行: BCLOSE 保存" : "\n请在 AutoCAD 中执行: BCLOSE 不保存");
    }

    /// <summary>
    /// 保存为 DWG 文件
    /// </summary>
    public void SaveAs(string path)
    {
        EnsureConnected();
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        _db!.SaveAs(Path.GetFullPath(path), DwgVersion.Current);
    }

    /// <summary>
    /// 从其他 DWG 文件导入图块定义
    /// </summary>
    public int ImportBlocksFromDwg(string sourceDwgPath, List<string>? blockNames = null)
    {
        EnsureConnected();
        if (!File.Exists(sourceDwgPath))
            throw new BlockLibraryException($"源 DWG 文件不存在: {sourceDwgPath}");

        int imported = 0;

        var sourceDb = new Database(false, true);
        try
        {
            sourceDb.ReadDwgFile(sourceDwgPath,
                FileOpenMode.OpenForReadAndAllShare, true, "");

            using var tr = _db!.TransactionManager.StartTransaction();
            var bt = (BlockTable)tr.GetObject(_db.BlockTableId, OpenMode.ForWrite);

            // sourceTr 必须在 sourceDb 之前释放
            using (var sourceTr = sourceDb.TransactionManager.StartTransaction())
            {
                var sourceBt = (BlockTable)sourceTr.GetObject(
                    sourceDb.BlockTableId, OpenMode.ForRead);

                foreach (var objId in sourceBt)
                {
                    var sourceBtr = (BlockTableRecord)sourceTr.GetObject(
                        objId, OpenMode.ForRead);

                    if (sourceBtr.IsLayout) continue;
                    if (sourceBtr.Name.StartsWith("*")) continue; // 跳过匿名块

                    // 如果指定了块名列表，只导入指定的块
                    if (blockNames != null && !blockNames.Contains(sourceBtr.Name))
                        continue;

                    // 跳过已存在的块
                    if (bt.Has(sourceBtr.Name)) continue;

                    // 使用 DeepCloneObjects 复制块定义到块表
                    var idCollection = new ObjectIdCollection { sourceBtr.ObjectId };
                    var mapping = new IdMapping();
                    sourceDb.DeepCloneObjects(idCollection, _db.BlockTableId, mapping, false);

                    imported++;
                }
            } // sourceTr 在此释放

            tr.Commit();
        }
        finally
        {
            sourceDb.Dispose(); // sourceDb 在 sourceTr 之后释放
        }

        return imported;
    }

    /// <summary>
    /// 诊断所有图块的几何信息
    /// </summary>
    public List<BlockDiagInfo> DiagnoseBlocks()
    {
        EnsureConnected();
        var results = new List<BlockDiagInfo>();

        using var tr = _db!.TransactionManager.StartTransaction();
        var bt = (BlockTable)tr.GetObject(_db.BlockTableId, OpenMode.ForRead);

        foreach (var objId in bt)
        {
            var btr = (BlockTableRecord)tr.GetObject(objId, OpenMode.ForRead);
            if (btr.IsLayout) continue;
            if (btr.Name.StartsWith("*")) continue;

            var info = new BlockDiagInfo
            {
                Name = btr.Name,
                Exists = true,
                EntityCount = 0
            };

            // 扫描几何信息
            double minX = double.MaxValue, minY = double.MaxValue;
            double maxX = double.MinValue, maxY = double.MinValue;

            foreach (var entId in btr)
            {
                info.EntityCount++;
                var ent = tr.GetObject(entId, OpenMode.ForRead);
                try
                {
                    if (ent is Line line)
                    {
                        minX = Math.Min(minX, Math.Min(line.StartPoint.X, line.EndPoint.X));
                        minY = Math.Min(minY, Math.Min(line.StartPoint.Y, line.EndPoint.Y));
                        maxX = Math.Max(maxX, Math.Max(line.StartPoint.X, line.EndPoint.X));
                        maxY = Math.Max(maxY, Math.Max(line.StartPoint.Y, line.EndPoint.Y));
                    }
                    else if (ent is DBText text)
                    {
                        var pt = text.Position;
                        minX = Math.Min(minX, pt.X);
                        minY = Math.Min(minY, pt.Y);
                        maxX = Math.Max(maxX, pt.X + text.Height * text.TextString.Length * 0.6);
                        maxY = Math.Max(maxY, pt.Y + text.Height);
                    }
                }
                catch { }
            }

            if (minX != double.MaxValue)
            {
                info.MinX = minX;
                info.MinY = minY;
                info.MaxX = maxX;
                info.MaxY = maxY;
                info.Width = maxX - minX;
                info.Height = maxY - minY;
            }

            results.Add(info);
        }

        return results;
    }

    private void PurgeBlock(Transaction tr, BlockTable bt, string name)
    {
        if (!bt.Has(name)) return;

        var btr = (BlockTableRecord)tr.GetObject(bt[name], OpenMode.ForWrite);

        // 遍历所有布局（模型空间 + 图纸空间），删除所有块引用
        foreach (var btObjId in bt)
        {
            var layoutBtr = (BlockTableRecord)tr.GetObject(btObjId, OpenMode.ForRead);
            if (!layoutBtr.IsLayout) continue;

            layoutBtr.UpgradeOpen();
            var toDelete = new List<ObjectId>();
            foreach (var objId in layoutBtr)
            {
                var ent = tr.GetObject(objId, OpenMode.ForRead);
                if (ent is BlockReference blkRef && blkRef.Name == name)
                {
                    toDelete.Add(objId);
                }
            }
            foreach (var objId in toDelete)
            {
                var ent = tr.GetObject(objId, OpenMode.ForWrite);
                ent.Erase(true);
            }
        }

        // 删除块定义
        btr.Erase(true);
    }

    private static void AddLine(
        Transaction tr, BlockTableRecord btr,
        double x1, double y1, double x2, double y2)
    {
        var line = new Line(new Point3d(x1, y1, 0), new Point3d(x2, y2, 0));
        btr.AppendEntity(line);
        tr.AddNewlyCreatedDBObject(line, true);
    }

    private void EnsureConnected()
    {
        if (_doc == null || _db == null)
            throw new AcadOperationException("未连接 AutoCAD，请先调用 Connect()");
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _disposed = true;
            _doc = null;
            _db = null;
        }
    }
}

/// <summary>
/// 图块诊断信息
/// </summary>
public class BlockDiagInfo
{
    public string Name { get; set; } = "";
    public bool Exists { get; set; }
    public int EntityCount { get; set; }
    public double MinX { get; set; }
    public double MinY { get; set; }
    public double MaxX { get; set; }
    public double MaxY { get; set; }
    public double Width { get; set; }
    public double Height { get; set; }
}
