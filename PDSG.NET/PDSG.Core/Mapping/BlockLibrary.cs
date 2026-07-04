using System.IO;
using PDSG.Core.Models;
using PDSG.Core.Exceptions;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace PDSG.Core.Mapping;

/// <summary>
/// PDSG 图块库管理 — 从 block_catalog.yaml 加载图块目录
/// </summary>
public static class BlockLibrary
{
    /// <summary>
    /// 从 YAML 文件加载图块目录
    /// </summary>
    public static BlockCatalog LoadCatalog(string catalogPath)
    {
        if (!File.Exists(catalogPath))
            throw new BlockLibraryException($"图块目录文件不存在: {catalogPath}");

        string yaml;
        try
        {
            yaml = File.ReadAllText(catalogPath);
        }
        catch (Exception ex)
        {
            throw new BlockLibraryException($"图块目录读取失败: {ex.Message}", ex);
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
            throw new BlockLibraryException($"图块目录解析失败: {ex.Message}", ex);
        }

        if (raw == null || !raw.TryGetValue("blocks", out var blocksObj)
            || blocksObj is not List<object> blockList)
        {
            throw new BlockLibraryException("图块目录文件缺少 'blocks' 字段");
        }

        var blocks = new List<BlockDefinition>();
        foreach (var item in blockList)
        {
            if (item is not Dictionary<string, object> dict) continue;

            var def = new BlockDefinition();
            if (dict.TryGetValue("name", out var n)) def.Name = n.ToString()!;
            if (dict.TryGetValue("description", out var d)) def.Description = d.ToString()!;
            if (dict.TryGetValue("applicable", out var a) && a is Dictionary<string, object> appDict)
                def.Applicable = appDict;
            if (dict.TryGetValue("attributes", out var attrs) && attrs is List<object> attrList)
                def.Attributes = attrList.Select(a => a.ToString()!).ToList();

            blocks.Add(def);
        }

        return new BlockCatalog(blocks);
    }

    /// <summary>
    /// 生成示例图块目录文件
    /// </summary>
    public static void CreateSampleCatalog(string outputPath)
    {
        var serializer = new SerializerBuilder()
            .WithNamingConvention(NullNamingConvention.Instance)
            .Build();

        var sample = new
        {
            blocks = new Dictionary<string, object>[]
            {
                new() { ["name"] = "LOOP_POWER_A", ["description"] = "400A及以下断路器回路", ["applicable"] = new { breaker_max_current = 400 }, ["attributes"] = Array.Empty<string>() },
                new() { ["name"] = "LOOP_POWER_B", ["description"] = "400A以上断路器回路", ["applicable"] = new { breaker_min_current = 401 }, ["attributes"] = Array.Empty<string>() },
                new() { ["name"] = "LOOP_VFD_3P_01", ["description"] = "3P变频器回路", ["applicable"] = new { load_type = "变频", poles = 3 }, ["attributes"] = Array.Empty<string>() },
                new() { ["name"] = "LOOP_LGT_1P_01", ["description"] = "1P照明回路", ["applicable"] = new { load_type = "照明", poles = 1 }, ["attributes"] = Array.Empty<string>() }
            }
        };

        var yaml = serializer.Serialize(sample);
        File.WriteAllText(outputPath, yaml);
    }
}
