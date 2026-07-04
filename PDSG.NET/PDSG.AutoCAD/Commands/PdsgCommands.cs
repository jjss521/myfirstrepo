using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Runtime;

namespace PDSG.AutoCAD.Commands;

/// <summary>
/// PDSG AutoCAD 命令注册 — 在 AutoCAD 命令行输入 PDSG 即可执行
/// </summary>
public class PdsgCommands
{
    /// <summary>
    /// PDSG 命令 — 读取 Excel 并生成配电系统图
    /// </summary>
    [CommandMethod("PDSG")]
    public void PdsgGenerate()
    {
        var doc = Application.DocumentManager.MdiActiveDocument;
        if (doc == null) return;

        var ed = doc.Editor;
        var result = ed.GetString("\n请输入 Excel 文件路径: ");
        if (result.Status != Autodesk.AutoCAD.EditorInput.PromptStatus.OK)
            return;

        string excelPath = result.StringResult.Trim().Trim('"');
        if (!File.Exists(excelPath))
        {
            ed.WriteMessage($"\n文件不存在: {excelPath}");
            return;
        }

        try
        {
            var cfg = PDSG.Core.Config.ConfigLoader.Load("config.yaml");
            var (records, errors) = PDSG.Core.Excel.ExcelReader.ReadAndValidate(excelPath, cfg.Excel);

            if (records.Count == 0)
            {
                ed.WriteMessage("\n无有效回路数据");
                return;
            }

            var catalog = PDSG.Core.Mapping.BlockLibrary.LoadCatalog(cfg.BlockLibrary.Catalog);
            var (mapped, warnings) = PDSG.Core.Mapping.BlockMapper.MapCircuits(records, cfg.BlockMapping, catalog);
            PDSG.Core.Mapping.AttributeBuilder.BuildAllAttributes(mapped, catalog);
            var layout = PDSG.Core.Layout.LayoutEngine.Compute(mapped, cfg.Layout, cfg.Sort);

            using var drawer = new Drawing.CadDrawer();
            drawer.Connect();
            drawer.Draw(layout);
            drawer.SaveAs(cfg.Output.DwgPath);

            ed.WriteMessage($"\n生成完成: {mapped.Count} 个回路, 保存到 {cfg.Output.DwgPath}");
        }
        catch (System.Exception ex)
        {
            ed.WriteMessage($"\n错误: {ex.Message}");
        }
    }

    /// <summary>
    /// PDSG_DRY 命令 — 仅校验 Excel，不连接 AutoCAD
    /// </summary>
    [CommandMethod("PDSG_DRY")]
    public void PdsgDryRun()
    {
        var doc = Application.DocumentManager.MdiActiveDocument;
        if (doc == null) return;

        var ed = doc.Editor;
        var result = ed.GetString("\n请输入 Excel 文件路径: ");
        if (result.Status != Autodesk.AutoCAD.EditorInput.PromptStatus.OK)
            return;

        string excelPath = result.StringResult.Trim().Trim('"');
        if (!File.Exists(excelPath))
        {
            ed.WriteMessage($"\n文件不存在: {excelPath}");
            return;
        }

        try
        {
            var cfg = PDSG.Core.Config.ConfigLoader.Load("config.yaml");
            var (records, errors) = PDSG.Core.Excel.ExcelReader.ReadAndValidate(excelPath, cfg.Excel);

            ed.WriteMessage($"\nExcel 校验完成: 有效 {records.Count} / 跳过 {errors.Count}");

            if (records.Count > 0)
            {
                var catalog = PDSG.Core.Mapping.BlockLibrary.LoadCatalog(cfg.BlockLibrary.Catalog);
                var (mapped, warnings) = PDSG.Core.Mapping.BlockMapper.MapCircuits(records, cfg.BlockMapping, catalog);
                PDSG.Core.Mapping.AttributeBuilder.BuildAllAttributes(mapped, catalog);
                var layout = PDSG.Core.Layout.LayoutEngine.Compute(mapped, cfg.Layout, cfg.Sort);

                ed.WriteMessage($"\n布局计算完成: {layout.Placements.Count} 个回路");
                ed.WriteMessage($"\n图纸幅面: {layout.PaperSize.Name} ({layout.PaperSize.Width}x{layout.PaperSize.Height}mm)");
                ed.WriteMessage($"\n母线: X={layout.BusLine.XStart:F1}~{layout.BusLine.XEnd:F1}");
            }
        }
        catch (System.Exception ex)
        {
            ed.WriteMessage($"\n错误: {ex.Message}");
        }
    }
}
