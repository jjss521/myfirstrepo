using PDSG.Core.Models;

namespace PDSG.Core.Mapping;

/// <summary>
/// PDSG 图块映射器 — 按负荷类型+极数组合匹配回路图块
/// </summary>
public static class BlockMapper
{
    /// <summary>
    /// 将回路列表映射为带图块的回路
    /// </summary>
    public static (List<CircuitWithBlock> Mapped, List<ErrorRecord> Warnings)
        MapCircuits(
            List<CircuitRecord> circuits,
            BlockMappingConfig cfg,
            BlockCatalog? catalog = null)
    {
        var mapped = new List<CircuitWithBlock>();
        var warnings = new List<ErrorRecord>();

        foreach (var circuit in circuits)
        {
            string? blockName = FindBlock(circuit, cfg.Rules);

            if (blockName == null)
            {
                blockName = cfg.DefaultBlock;
                warnings.Add(new ErrorRecord
                {
                    RowNumber = circuit.RowNumber,
                    CircuitId = circuit.CircuitId,
                    ErrorType = "图块映射警告",
                    ErrorMessage = $"回路 {circuit.CircuitId}: 负荷类型={circuit.LoadType.ToChinese()} 极数={circuit.BreakerPoles} 无匹配规则，使用默认图块 {blockName}"
                });
            }

            if (catalog != null && catalog.Find(blockName) == null)
            {
                warnings.Add(new ErrorRecord
                {
                    RowNumber = circuit.RowNumber,
                    CircuitId = circuit.CircuitId,
                    ErrorType = "图块目录警告",
                    ErrorMessage = $"回路 {circuit.CircuitId}: 图块 \"{blockName}\" 在图块目录中不存在"
                });
            }

            mapped.Add(new CircuitWithBlock
            {
                Record = circuit,
                BlockName = blockName
            });
        }

        return (mapped, warnings);
    }

    private static string? FindBlock(CircuitRecord circuit, List<BlockMappingRule> rules)
    {
        foreach (var rule in rules)
        {
            if (RuleMatches(circuit, rule))
                return rule.Block;
        }
        return null;
    }

    private static bool RuleMatches(CircuitRecord circuit, BlockMappingRule rule)
    {
        foreach (var kv in rule.Match)
        {
            string key = kv.Key.ToLowerInvariant();
            string expected = kv.Value.ToLowerInvariant();

            string actual = key switch
            {
                "load_type" => circuit.LoadType.ToChinese(),
                "poles" => circuit.BreakerPoles.ToString(),
                "breaker_max_current" => circuit.BreakerTripCurrentA.ToString(),
                "breaker_min_current" => circuit.BreakerTripCurrentA.ToString(),
                _ => ""
            };

            if (key == "breaker_max_current")
            {
                if (double.TryParse(expected, out var maxVal) && circuit.BreakerTripCurrentA > maxVal)
                    return false;
            }
            else if (key == "breaker_min_current")
            {
                if (double.TryParse(expected, out var minVal) && circuit.BreakerTripCurrentA < minVal)
                    return false;
            }
            else
            {
                if (!actual.Equals(expected, StringComparison.OrdinalIgnoreCase))
                    return false;
            }
        }
        return true;
    }
}
