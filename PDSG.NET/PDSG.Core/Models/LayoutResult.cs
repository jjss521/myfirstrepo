namespace PDSG.Core.Models;

/// <summary>
/// 图纸幅面
/// </summary>
public record PaperSize(string Name, double Width, double Height);

/// <summary>
/// 图块放置信息
/// </summary>
public class Placement
{
    public string BlockName { get; set; } = "";
    public double X { get; set; }
    public double Y { get; set; }
    public Dictionary<string, string> Attributes { get; set; } = new();
    public string CircuitId { get; set; } = "";
}

/// <summary>
/// 母线绘制信息
/// </summary>
public class BusLine
{
    public double X { get; set; }
    public double YStart { get; set; }
    public double YEnd { get; set; }
    public string Direction { get; set; } = "vertical";
    public double BusY { get; set; }
    public double XStart { get; set; }
    public double XEnd { get; set; }
}

/// <summary>
/// 分组标签
/// </summary>
public record GroupLabel(string Text, double X, double Y);

/// <summary>
/// 表格单元格
/// </summary>
public record TableCell(string Text, double X, double Y);

/// <summary>
/// 参数表格布局信息
/// </summary>
public class TableLayout
{
    public double X { get; set; }
    public double Y { get; set; }
    public double ColWidth { get; set; }
    public double LabelColWidth { get; set; } = 30;
    public double RowHeight { get; set; } = 7;
    public List<string> Headers { get; set; } = new();
    public List<List<string>> Rows { get; set; } = new();
    public List<string> RowLabels { get; set; } = new();
}

/// <summary>
/// 布局计算结果
/// </summary>
public class LayoutResult
{
    public List<Placement> Placements { get; set; } = new();
    public BusLine BusLine { get; set; } = new();
    public List<GroupLabel> GroupLabels { get; set; } = new();
    public PaperSize PaperSize { get; set; } = new("", 0, 0);
    public TableLayout? Table { get; set; }
}
