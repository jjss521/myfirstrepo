using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Runtime;
using PDSG.Core.Mapping;
using PDSG.Core.Config;
using PDSG.Core.Models;

namespace PDSG.AutoCAD.Commands;

/// <summary>
/// PDSG 图块管理命令
/// </summary>
public class BlockCommands
{
    /// <summary>
    /// PDSG_BLOCKS — 列出当前文档中所有回路图块
    /// </summary>
    [CommandMethod("PDSG_BLOCKS")]
    public void ListBlocks()
    {
        var doc = Application.DocumentManager.MdiActiveDocument;
        if (doc == null) return;
        var ed = doc.Editor;

        using var editor = new Drawing.BlockEditor();
        editor.Connect();

        var circuitBlocks = editor.GetCircuitBlockNames();
        var allBlocks = editor.GetAllBlockNames();

        ed.WriteMessage($"\n=== 回路图块 ({circuitBlocks.Count} 个) ===");
        foreach (var name in circuitBlocks)
            ed.WriteMessage($"\n  {name}");

        ed.WriteMessage($"\n\n=== 所有图块 ({allBlocks.Count} 个) ===");
        foreach (var name in allBlocks.Take(20))
            ed.WriteMessage($"\n  {name}");
        if (allBlocks.Count > 20)
            ed.WriteMessage($"\n  ... 还有 {allBlocks.Count - 20} 个");

        // 加载目录并复核
        try
        {
            var cfg = ConfigLoader.Load("config.yaml");
            var catalog = BlockManager.Load(cfg.BlockLibrary.Catalog);
            var result = editor.ValidateCatalog(catalog);

            ed.WriteMessage($"\n\n=== 目录复核 ===");
            ed.WriteMessage($"\n有效: {result.IsValid}");
            if (result.MissingInDrawing.Count > 0)
            {
                ed.WriteMessage($"\n图形中缺失:");
                foreach (var name in result.MissingInDrawing)
                    ed.WriteMessage($"\n  {name}");
            }
            if (result.NotInCatalog.Count > 0)
            {
                ed.WriteMessage($"\n图形中有但目录中无:");
                foreach (var name in result.NotInCatalog)
                    ed.WriteMessage($"\n  {name}");
            }
        }
        catch (System.Exception ex)
        {
            ed.WriteMessage($"\n目录复核失败: {ex.Message}");
        }
    }

    /// <summary>
    /// PDSG_BCREATE — 创建新回路图块
    /// </summary>
    [CommandMethod("PDSG_BCREATE")]
    public void CreateBlock()
    {
        var doc = Application.DocumentManager.MdiActiveDocument;
        if (doc == null) return;
        var ed = doc.Editor;

        var nameResult = ed.GetString("\n请输入图块名称 (如 LOOP_POWER_C): ");
        if (nameResult.Status != Autodesk.AutoCAD.EditorInput.PromptStatus.OK) return;

        var descResult = ed.GetString("\n请输入图块描述: ");
        if (descResult.Status != Autodesk.AutoCAD.EditorInput.PromptStatus.OK) return;

        string blockName = nameResult.StringResult.Trim().ToUpper();
        string description = descResult.StringResult.Trim();

        using var editor = new Drawing.BlockEditor();
        editor.Connect();

        try
        {
            editor.CreateBlock(blockName, description);
            ed.WriteMessage($"\n图块已创建: {blockName} ({description})");

            // 自动更新目录
            UpdateCatalog(blockName, description);
        }
        catch (System.Exception ex)
        {
            ed.WriteMessage($"\n创建失败: {ex.Message}");
        }
    }

    /// <summary>
    /// PDSG_BEDIT — 在 AutoCAD 块编辑器中修改图块
    /// </summary>
    [CommandMethod("PDSG_BEDIT")]
    public void EditBlock()
    {
        var doc = Application.DocumentManager.MdiActiveDocument;
        if (doc == null) return;
        var ed = doc.Editor;

        var nameResult = ed.GetString("\n请输入要编辑的图块名称: ");
        if (nameResult.Status != Autodesk.AutoCAD.EditorInput.PromptStatus.OK) return;

        string blockName = nameResult.StringResult.Trim();

        using var editor = new Drawing.BlockEditor();
        editor.Connect();

        if (editor.OpenBlockEditor(blockName))
            ed.WriteMessage($"\n已打开块编辑器: {blockName}");
        else
            ed.WriteMessage($"\n图块 '{blockName}' 不存在");
    }

    /// <summary>
    /// PDSG_BIMPORT — 从其他 DWG 文件导入图块
    /// </summary>
    [CommandMethod("PDSG_BIMPORT")]
    public void ImportBlocks()
    {
        var doc = Application.DocumentManager.MdiActiveDocument;
        if (doc == null) return;
        var ed = doc.Editor;

        var pathResult = ed.GetString("\n请输入源 DWG 文件路径: ");
        if (pathResult.Status != Autodesk.AutoCAD.EditorInput.PromptStatus.OK) return;

        string dwgPath = pathResult.StringResult.Trim().Trim('"');
        if (!System.IO.File.Exists(dwgPath))
        {
            ed.WriteMessage($"\n文件不存在: {dwgPath}");
            return;
        }

        using var editor = new Drawing.BlockEditor();
        editor.Connect();

        try
        {
            int imported = editor.ImportBlocksFromDwg(dwgPath);
            ed.WriteMessage($"\n已从 {System.IO.Path.GetFileName(dwgPath)} 导入 {imported} 个图块");
        }
        catch (System.Exception ex)
        {
            ed.WriteMessage($"\n导入失败: {ex.Message}");
        }
    }

    /// <summary>
    /// PDSG_BDELETE — 删除图块
    /// </summary>
    [CommandMethod("PDSG_BDELETE")]
    public void DeleteBlock()
    {
        var doc = Application.DocumentManager.MdiActiveDocument;
        if (doc == null) return;
        var ed = doc.Editor;

        var nameResult = ed.GetString("\n请输入要删除的图块名称: ");
        if (nameResult.Status != Autodesk.AutoCAD.EditorInput.PromptStatus.OK) return;

        string blockName = nameResult.StringResult.Trim();

        using var editor = new Drawing.BlockEditor();
        editor.Connect();

        if (editor.DeleteBlock(blockName))
            ed.WriteMessage($"\n图块已删除: {blockName}");
        else
            ed.WriteMessage($"\n图块 '{blockName}' 不存在");
    }

    /// <summary>
    /// PDSG_BDIAG — 诊断所有图块几何信息
    /// </summary>
    [CommandMethod("PDSG_BDIAG")]
    public void DiagnoseBlocks()
    {
        var doc = Application.DocumentManager.MdiActiveDocument;
        if (doc == null) return;
        var ed = doc.Editor;

        using var editor = new Drawing.BlockEditor();
        editor.Connect();

        var diagnostics = editor.DiagnoseBlocks();

        ed.WriteMessage($"\n=== 图块诊断 ({diagnostics.Count} 个) ===");
        foreach (var info in diagnostics)
        {
            if (info.Exists)
            {
                ed.WriteMessage(
                    $"\n  {info.Name}: {info.EntityCount} 实体, "
                  + $"边界 ({info.MinX:F1},{info.MinY:F1})~({info.MaxX:F1},{info.MaxY:F1}), "
                  + $"尺寸 {info.Width:F1}x{info.Height:F1}mm");
            }
            else
            {
                ed.WriteMessage($"\n  {info.Name}: 不存在");
            }
        }
    }

    private static void UpdateCatalog(string blockName, string description)
    {
        try
        {
            var cfg = ConfigLoader.Load("config.yaml");
            var catalog = BlockManager.Load(cfg.BlockLibrary.Catalog);

            if (catalog.Find(blockName) == null)
            {
                catalog.AddBlock(new BlockDefinition
                {
                    Name = blockName,
                    Description = description
                });
                catalog.Save();
            }
        }
        catch
        {
            // 目录更新失败不影响主流程
        }
    }
}
