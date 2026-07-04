using System.IO;
using PDSG.Core.Models;
using PDSG.Core.Exceptions;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace PDSG.Core.Config;

/// <summary>
/// PDSG 配置加载器 — 从 YAML 文件加载配置并转换为 AppConfig
/// </summary>
public static class ConfigLoader
{
    /// <summary>
    /// 从 YAML 文件加载应用配置
    /// </summary>
    public static AppConfig Load(string path)
    {
        if (!File.Exists(path))
            throw new ConfigException($"配置文件不存在: {path}");

        string yaml;
        try
        {
            yaml = File.ReadAllText(path);
        }
        catch (Exception ex)
        {
            throw new ConfigException($"配置文件读取失败: {ex.Message}", ex);
        }

        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(NullNamingConvention.Instance)
            .Build();

        Dictionary<string, object>? raw;
        try
        {
            raw = deserializer.Deserialize<Dictionary<string, object>>(yaml);
        }
        catch (Exception ex)
        {
            throw new ConfigException($"配置文件解析失败: {ex.Message}", ex);
        }

        if (raw == null) raw = new();

        return BuildAppConfig(raw);
    }

    private static AppConfig BuildAppConfig(Dictionary<string, object> raw)
    {
        var cfg = new AppConfig();

        // AutoCAD 连接
        if (raw.TryGetValue("autocad", out var acadObj) && acadObj is Dictionary<string, object> acadRaw)
        {
            if (acadRaw.TryGetValue("progids", out var progids) && progids is List<object> progidList)
                cfg.Autocad.ProgIds = progidList.Select(p => p.ToString() ?? "").ToList();
            if (acadRaw.TryGetValue("visible", out var vis))
                cfg.Autocad.Visible = Convert.ToBoolean(vis);
        }

        // 图块库
        if (raw.TryGetValue("block_library", out var libObj) && libObj is Dictionary<string, object> libRaw)
        {
            if (libRaw.TryGetValue("path", out var p)) cfg.BlockLibrary.Path = p.ToString()!;
            if (libRaw.TryGetValue("catalog", out var c)) cfg.BlockLibrary.Catalog = c.ToString()!;
            if (libRaw.TryGetValue("title_block_path", out var tb)) cfg.BlockLibrary.TitleBlockPath = tb.ToString()!;
            if (libRaw.TryGetValue("default_block", out var db)) cfg.BlockLibrary.DefaultBlock = db.ToString()!;
        }

        // Excel
        if (raw.TryGetValue("excel", out var excelObj) && excelObj is Dictionary<string, object> excelRaw)
        {
            if (excelRaw.TryGetValue("sheet_name", out var v)) cfg.Excel.SheetName = v.ToString()!;
            if (excelRaw.TryGetValue("header_row", out var v2)) cfg.Excel.HeaderRow = Convert.ToInt32(v2);
            if (excelRaw.TryGetValue("data_start_row", out var v3)) cfg.Excel.DataStartRow = Convert.ToInt32(v3);
            if (excelRaw.TryGetValue("min_match_ratio", out var v4)) cfg.Excel.MinMatchRatio = Convert.ToDouble(v4);
            if (excelRaw.TryGetValue("format_auto_detect", out var v5)) cfg.Excel.FormatAutoDetect = Convert.ToBoolean(v5);
            if (excelRaw.TryGetValue("default_breaker_model", out var v6)) cfg.Excel.DefaultBreakerModel = v6.ToString()!;

            if (excelRaw.TryGetValue("transposed_column_aliases", out var tca) && tca is Dictionary<string, object> tcaDict)
                cfg.Excel.TransposedColumnAliases = tcaDict.ToDictionary(kv => kv.Key, kv => kv.Value.ToString()!);

            if (excelRaw.TryGetValue("column_aliases", out var ca) && ca is Dictionary<string, object> caDict)
                cfg.Excel.ColumnAliases = caDict.ToDictionary(kv => kv.Key, kv => kv.Value.ToString()!);
        }

        // 图块映射
        if (raw.TryGetValue("block_mapping", out var mapObj) && mapObj is Dictionary<string, object> mapRaw)
        {
            if (mapRaw.TryGetValue("default_block", out var v)) cfg.BlockMapping.DefaultBlock = v.ToString()!;
            if (mapRaw.TryGetValue("breaker_threshold", out var v2)) cfg.BlockMapping.BreakerThreshold = Convert.ToDouble(v2);
            if (mapRaw.TryGetValue("block_small", out var v3)) cfg.BlockMapping.BlockSmall = v3.ToString()!;
            if (mapRaw.TryGetValue("block_large", out var v4)) cfg.BlockMapping.BlockLarge = v4.ToString()!;

            if (mapRaw.TryGetValue("rules", out var rulesObj) && rulesObj is List<object> ruleList)
            {
                foreach (var ruleItem in ruleList)
                {
                    if (ruleItem is Dictionary<string, object> ruleDict)
                    {
                        var rule = new BlockMappingRule();
                        if (ruleDict.TryGetValue("match", out var match) && match is Dictionary<string, object> matchDict)
                            rule.Match = matchDict.ToDictionary(kv => kv.Key, kv => kv.Value.ToString()!);
                        if (ruleDict.TryGetValue("block", out var block))
                            rule.Block = block.ToString()!;
                        cfg.BlockMapping.Rules.Add(rule);
                    }
                }
            }
        }

        // 布局
        if (raw.TryGetValue("layout", out var layoutObj) && layoutObj is Dictionary<string, object> layoutRaw)
        {
            if (layoutRaw.TryGetValue("horizontal_spacing", out var v)) cfg.Layout.HorizontalSpacing = Convert.ToDouble(v);
            if (layoutRaw.TryGetValue("bus_x", out var v2)) cfg.Layout.BusX = Convert.ToDouble(v2);
            if (layoutRaw.TryGetValue("bus_y", out var v3)) cfg.Layout.BusY = Convert.ToDouble(v3);

            if (layoutRaw.TryGetValue("margins", out var marginsObj) && marginsObj is Dictionary<string, object> marginsDict)
            {
                if (marginsDict.TryGetValue("top", out var mt)) cfg.Layout.Margins.Top = Convert.ToDouble(mt);
                if (marginsDict.TryGetValue("bottom", out var mb)) cfg.Layout.Margins.Bottom = Convert.ToDouble(mb);
                if (marginsDict.TryGetValue("left", out var ml)) cfg.Layout.Margins.Left = Convert.ToDouble(ml);
                if (marginsDict.TryGetValue("right", out var mr)) cfg.Layout.Margins.Right = Convert.ToDouble(mr);
            }

            if (layoutRaw.TryGetValue("paper", out var paperObj) && paperObj is Dictionary<string, object> paperDict)
            {
                if (paperDict.TryGetValue("default", out var pd)) cfg.Layout.Paper.Default = pd.ToString()!;
                if (paperDict.TryGetValue("orientation", out var po)) cfg.Layout.Paper.Orientation = po.ToString()!;
                if (paperDict.TryGetValue("sizes", out var sizesObj) && sizesObj is List<object> sizeList)
                {
                    foreach (var sizeItem in sizeList)
                    {
                        if (sizeItem is Dictionary<string, object> sizeDict)
                        {
                            var def = new PaperSizeDef();
                            if (sizeDict.TryGetValue("name", out var sn)) def.Name = sn.ToString()!;
                            if (sizeDict.TryGetValue("width", out var sw)) def.Width = Convert.ToDouble(sw);
                            if (sizeDict.TryGetValue("height", out var sh)) def.Height = Convert.ToDouble(sh);
                            cfg.Layout.Paper.Sizes.Add(def);
                        }
                    }
                }
            }
        }

        // 输出
        if (raw.TryGetValue("output", out var outputObj) && outputObj is Dictionary<string, object> outputRaw)
        {
            if (outputRaw.TryGetValue("dwg_path", out var v)) cfg.Output.DwgPath = v.ToString()!;
            if (outputRaw.TryGetValue("report_path", out var v2)) cfg.Output.ReportPath = v2.ToString()!;
            if (outputRaw.TryGetValue("log_path", out var v3)) cfg.Output.LogPath = v3.ToString()!;
            if (outputRaw.TryGetValue("log_level", out var v4)) cfg.Output.LogLevel = v4.ToString()!;
        }

        // 排序
        if (raw.TryGetValue("sort", out var sortObj) && sortObj is Dictionary<string, object> sortRaw)
        {
            if (sortRaw.TryGetValue("group_by", out var v)) cfg.Sort.GroupBy = v.ToString()!;
            if (sortRaw.TryGetValue("sort_by", out var v2)) cfg.Sort.SortBy = v2.ToString()!;
        }

        return cfg;
    }
}
