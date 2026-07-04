namespace PDSG.Core.Models;

/// <summary>
/// AutoCAD 连接配置
/// </summary>
public class AcadConfig
{
    public List<string> ProgIds { get; set; } = new()
    {
        "AutoCAD.Application.24.1",
        "AutoCAD.Application.23.1"
    };
    public bool Visible { get; set; } = true;
}

/// <summary>
/// 图块库配置
/// </summary>
public class BlockLibraryConfig
{
    public string Path { get; set; } = "./blocks/block_library.dwg";
    public string Catalog { get; set; } = "./blocks/block_catalog.yaml";
    public string TitleBlockPath { get; set; } = "./blocks/title_block.dwg";
    public string DefaultBlock { get; set; } = "LOOP_POWER_A";
}

/// <summary>
/// Excel 读取配置
/// </summary>
public class ExcelConfig
{
    public string SheetName { get; set; } = "低压配电系统";
    public int HeaderRow { get; set; } = 1;
    public int DataStartRow { get; set; } = 2;
    public double MinMatchRatio { get; set; } = 0.7;
    public bool FormatAutoDetect { get; set; } = true;
    public string DefaultBreakerModel { get; set; } = "NSX100N";
    public Dictionary<string, string> TransposedColumnAliases { get; set; } = new();
    public Dictionary<string, string> ColumnAliases { get; set; } = new();
}

/// <summary>
/// 图块映射规则
/// </summary>
public class BlockMappingRule
{
    public Dictionary<string, string> Match { get; set; } = new();
    public string Block { get; set; } = "";
}

/// <summary>
/// 图块映射配置
/// </summary>
public class BlockMappingConfig
{
    public string DefaultBlock { get; set; } = "LOOP_POWER_A";
    public double BreakerThreshold { get; set; } = 400;
    public string BlockSmall { get; set; } = "LOOP_POWER_A";
    public string BlockLarge { get; set; } = "LOOP_POWER_B";
    public List<BlockMappingRule> Rules { get; set; } = new();
}

/// <summary>
/// 边距配置
/// </summary>
public class MarginsConfig
{
    public double Top { get; set; } = 40;
    public double Bottom { get; set; } = 30;
    public double Left { get; set; } = 30;
    public double Right { get; set; } = 20;
}

/// <summary>
/// 图纸尺寸定义
/// </summary>
public class PaperSizeDef
{
    public string Name { get; set; } = "";
    public double Width { get; set; }
    public double Height { get; set; }
}

/// <summary>
/// 图纸配置
/// </summary>
public class PaperConfig
{
    public List<PaperSizeDef> Sizes { get; set; } = new();
    public string Default { get; set; } = "A3";
    public string Orientation { get; set; } = "landscape";
}

/// <summary>
/// 文字样式配置
/// </summary>
public class TextStyleConfig
{
    public string FontName { get; set; } = "SimSun";
    public double Height { get; set; } = 2.5;
}

/// <summary>
/// 标题栏配置
/// </summary>
public class TitleBlockConfig
{
    public bool Enabled { get; set; } = true;
    public string LayerName { get; set; } = "_TITLE_BLOCK";
    public string TextStyle { get; set; } = "PDSG_TITLE";
}

/// <summary>
/// 排序配置
/// </summary>
public class SortConfig
{
    public string GroupBy { get; set; } = "load_type";
    public string SortBy { get; set; } = "circuit_id";
}

/// <summary>
/// 布局配置
/// </summary>
public class LayoutConfig
{
    public double HorizontalSpacing { get; set; } = 60;
    public double BusX { get; set; } = 30;
    public double BusY { get; set; } = 200;
    public MarginsConfig Margins { get; set; } = new();
    public PaperConfig Paper { get; set; } = new();
    public TextStyleConfig TextStyle { get; set; } = new();
}

/// <summary>
/// 输出配置
/// </summary>
public class OutputConfig
{
    public string DwgPath { get; set; } = "./output/system.dwg";
    public string ReportPath { get; set; } = "./output/report.html";
    public string LogPath { get; set; } = "./logs/pdsg.log";
    public string LogLevel { get; set; } = "INFO";
}

/// <summary>
/// 应用配置（对应 config.yaml 根节点）
/// </summary>
public class AppConfig
{
    public AcadConfig Autocad { get; set; } = new();
    public BlockLibraryConfig BlockLibrary { get; set; } = new();
    public ExcelConfig Excel { get; set; } = new();
    public BlockMappingConfig BlockMapping { get; set; } = new();
    public LayoutConfig Layout { get; set; } = new();
    public SortConfig Sort { get; set; } = new();
    public TitleBlockConfig TitleBlock { get; set; } = new();
    public OutputConfig Output { get; set; } = new();
}
