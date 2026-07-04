namespace PDSG.Core.Models;

/// <summary>
/// Excel 文件格式枚举
/// </summary>
public enum ExcelFormat
{
    Standard,   // 标准格式：每行一个回路，列为参数
    Transposed  // 转置格式：每列一个回路，行为参数
}

/// <summary>
/// 负荷类型枚举
/// </summary>
public enum LoadType
{
    Power = 0,       // 动力
    Lighting = 1,    // 照明
    Vfd = 2,         // 变频
    Ac = 3,          // 空调
    Socket = 4,      // 插座
    Spare = 5,       // 备用
    Capacitor = 6    // 电容补偿
}

/// <summary>
/// 负荷类型扩展方法
/// </summary>
public static class LoadTypeExtensions
{
    private static readonly Dictionary<LoadType, string> ChineseNames = new()
    {
        [LoadType.Power] = "动力",
        [LoadType.Lighting] = "照明",
        [LoadType.Vfd] = "变频",
        [LoadType.Ac] = "空调",
        [LoadType.Socket] = "插座",
        [LoadType.Spare] = "备用",
        [LoadType.Capacitor] = "电容补偿"
    };

    private static readonly Dictionary<string, LoadType> FromChinese;

    static LoadTypeExtensions()
    {
        FromChinese = ChineseNames.ToDictionary(kv => kv.Value, kv => kv.Key);
    }

    public static string ToChinese(this LoadType type) =>
        ChineseNames.TryGetValue(type, out var name) ? name : type.ToString();

    public static LoadType? FromString(string value)
    {
        var trimmed = value.Trim();
        if (FromChinese.TryGetValue(trimmed, out var lt)) return lt;
        if (Enum.TryParse<LoadType>(trimmed, true, out var parsed)) return parsed;
        return null;
    }
}

/// <summary>
/// 负荷类型到图块命名缩写映射
/// </summary>
public static class LoadTypeAbbreviation
{
    public static string Get(LoadType type) => type switch
    {
        LoadType.Power => "PWR",
        LoadType.Lighting => "LGT",
        LoadType.Vfd => "VFD",
        LoadType.Ac => "AC",
        LoadType.Socket => "SKT",
        LoadType.Spare => "SPR",
        LoadType.Capacitor => "CAP",
        _ => "UNK"
    };
}
