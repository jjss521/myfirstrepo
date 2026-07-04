namespace PDSG.Core.Models;

/// <summary>
/// 图块定义（从 block_catalog.yaml 读取）
/// </summary>
public class BlockDefinition
{
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public Dictionary<string, object> Applicable { get; set; } = new();
    public List<string> Attributes { get; set; } = new();
}

/// <summary>
/// 图块目录管理器
/// </summary>
public class BlockCatalog
{
    private readonly Dictionary<string, BlockDefinition> _index;

    public IReadOnlyList<BlockDefinition> Blocks { get; }

    public BlockCatalog(IList<BlockDefinition> blocks)
    {
        Blocks = (IReadOnlyList<BlockDefinition>)blocks;
        _index = blocks.ToDictionary(b => b.Name);
    }

    public BlockDefinition? Find(string blockName) =>
        _index.TryGetValue(blockName, out var def) ? def : null;

    public IEnumerable<string> AllNames() => _index.Keys;
}

/// <summary>
/// 关联了图块的回路
/// </summary>
public class CircuitWithBlock
{
    public CircuitRecord Record { get; set; } = new();
    public string BlockName { get; set; } = "";
    public Dictionary<string, string> Attributes { get; set; } = new();
}
