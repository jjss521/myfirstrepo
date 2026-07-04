using Autodesk.AutoCAD.Runtime;

namespace PDSG.AutoCAD;

/// <summary>
/// PDSG AutoCAD 插件入口 — 实现 IExtensionApplication 接口
/// AutoCAD 加载 ARX/NetDLL 时自动调用 Initialize()
/// </summary>
public class PdsgPlugin : IExtensionApplication
{
    public void Initialize()
    {
        var doc = Autodesk.AutoCAD.ApplicationServices.Application
            .DocumentManager.MdiActiveDocument;
        if (doc != null)
        {
            doc.Editor.WriteMessage(
                "\n[PDSG] 配电柜系统图自动生成工具 v2.0 (.NET) 已加载\n"
              + "  命令: PDSG (生成) | PDSG_DRY (校验)\n");
        }
    }

    public void Terminate()
    {
        // 清理资源（如有）
    }
}
