using System.IO;
using PDSG.Core.Models;
using PDSG.Core.Exceptions;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace PDSG.Core.Mapping;

/// <summary>
/// PDSG 图块管理器 — 管理图块目录 YAML，支持增删改查图块定义
/// 核心原则：只使用图形内已存在的块名，与自动插入的回路块名对应并复核
/// </summary>
public class BlockManager
{
    private readonly string _catalogPath;
    private List<BlockDefinition> _blocks;

    /// <summary>
    /// 当前图块目录中的所有图块
    /// </summary>
    public IReadOnlyList<BlockDefinition> Blocks => _blocks;

    /// <summary>
    /// 从 YAML 文件加载图块目录
    /// </summary>
    public static BlockManager Load(string catalogPath)
    {
        if (!File.Exists(catalogPath))
            throw new BlockLibraryException($"图块目录文件不存在: {catalogPath}");

        var yaml = File.ReadAllText(catalogPath);
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

        var blocks = ParseBlocks(raw);
        return new BlockManager(catalogPath, blocks);
    }

    /// <summary>
    /// 创建空的图块目录
    /// </summary>
    public static BlockManager CreateEmpty(string catalogPath)
    {
        return new BlockManager(catalogPath, new List<BlockDefinition>());
    }

    private BlockManager(string catalogPath, List<BlockDefinition> blocks)
    {
        _catalogPath = catalogPath;
        _blocks = blocks;
    }

    /// <summary>
    /// 添加新图块定义
    /// </summary>
    public void AddBlock(BlockDefinition block)
    {
        if (_blocks.Any(b => b.Name == block.Name))
            throw new BlockLibraryException($"图块 '{block.Name}' 已存在");

        _blocks.Add(block);
    }

    /// <summary>
    /// 修改已有图块定义
    /// </summary>
    public void UpdateBlock(string name, BlockDefinition updated)
    {
        var idx = _blocks.FindIndex(b => b.Name == name);
        if (idx < 0)
            throw new BlockLibraryException($"图块 '{name}' 不存在");

        updated.Name = name;
        _blocks[idx] = updated;
    }

    /// <summary>
    /// 删除图块定义
    /// </summary>
    public bool RemoveBlock(string name)
    {
        return _blocks.RemoveAll(b => b.Name == name) > 0;
    }

    /// <summary>
    /// 查找图块定义
    /// </summary>
    public BlockDefinition? Find(string name)
    {
        return _blocks.FirstOrDefault(b => b.Name == name);
    }

    /// <summary>
    /// 获取所有图块名称
    /// </summary>
    public IEnumerable<string> GetAllNames() => _blocks.Select(b => b.Name);

    /// <summary>
    /// 复核图块名是否与自动插入的回路块名对应
    /// 只使用图形内已存在的块名
    /// </summary>
    public BlockValidationResult ValidateAgainstDrawing(
        IEnumerable<string> drawingBlockNames)
    {
        var drawingNames = new HashSet<string>(drawingBlockNames);
        var result = new BlockValidationResult();

        foreach (var block in _blocks)
        {
            var exists = drawingNames.Contains(block.Name);
            result.BlockStatus[block.Name] = exists;

            if (!exists)
            {
                result.MissingInDrawing.Add(block.Name);
            }
        }

        // 检查图形中有哪些回路块但不在目录中
        var loopPrefixes = new[] { "LOOP_", "VFD_", "LGT_", "AC_", "SKT_", "SPR_", "CAP_" };
        foreach (var drawingName in drawingNames)
        {
            if (loopPrefixes.Any(p => drawingName.StartsWith(p, StringComparison.OrdinalIgnoreCase)))
            {
                if (!_blocks.Any(b => b.Name == drawingName))
                {
                    result.NotInCatalog.Add(drawingName);
                }
            }
        }

        result.IsValid = result.MissingInDrawing.Count == 0;
        return result;
    }

    /// <summary>
    /// 保存到 YAML 文件
    /// </summary>
    public void Save()
    {
        var dir = Path.GetDirectoryName(_catalogPath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        var serializer = new SerializerBuilder()
            .WithNamingConvention(NullNamingConvention.Instance)
            .Build();

        var data = new
        {
            blocks = _blocks.Select(b => new
            {
                name = b.Name,
                description = b.Description,
                applicable = b.Applicable,
                attributes = b.Attributes
            }).ToList()
        };

        var yaml = serializer.Serialize(data);
        File.WriteAllText(_catalogPath, yaml);
    }

    /// <summary>
    /// 从单个 DWG 文件导入图块定义（读取块名列表）
    /// </summary>
    public static List<string> ReadBlockNamesFromDwg(string dwgPath)
    {
        if (!File.Exists(dwgPath))
            throw new BlockLibraryException($"DWG 文件不存在: {dwgPath}");

        // DWG 文件是二进制格式，无法直接读取块名
        // 需要通过 AutoCAD API 读取，这里返回空列表作为占位
        // 实际实现由 AutoCAD 层的 BlockEditor 提供
        return new List<string>();
    }

    /// <summary>
    /// 批量导入多个 DWG 文件的图块
    /// </summary>
    public ImportResult ImportFromDwgs(List<string> dwgPaths)
    {
        var result = new ImportResult();

        foreach (var dwgPath in dwgPaths)
        {
            try
            {
                var names = ReadBlockNamesFromDwg(dwgPath);
                result.FilesProcessed++;
                result.TotalBlocksFound += names.Count;

                foreach (var name in names)
                {
                    if (!_blocks.Any(b => b.Name == name))
                    {
                        _blocks.Add(new BlockDefinition
                        {
                            Name = name,
                            Description = $"从 {Path.GetFileName(dwgPath)} 导入"
                        });
                        result.BlocksAdded++;
                    }
                    else
                    {
                        result.BlocksSkipped++;
                    }
                }
            }
            catch (Exception ex)
            {
                result.Errors.Add($"{dwgPath}: {ex.Message}");
            }
        }

        return result;
    }

    private static List<BlockDefinition> ParseBlocks(Dictionary<string, object>? raw)
    {
        var blocks = new List<BlockDefinition>();
        if (raw == null || !raw.TryGetValue("blocks", out var blocksObj)
            || blocksObj is not List<object> blockList)
            return blocks;

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

        return blocks;
    }
}

/// <summary>
/// 图块验证结果
/// </summary>
public class BlockValidationResult
{
    public bool IsValid { get; set; }
    public Dictionary<string, bool> BlockStatus { get; set; } = new();
    public List<string> MissingInDrawing { get; set; } = new();
    public List<string> NotInCatalog { get; set; } = new();
}

/// <summary>
/// 批量导入结果
/// </summary>
public class ImportResult
{
    public int FilesProcessed { get; set; }
    public int TotalBlocksFound { get; set; }
    public int BlocksAdded { get; set; }
    public int BlocksSkipped { get; set; }
    public List<string> Errors { get; set; } = new();
}
