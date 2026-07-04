using PDSG.Core.Models;
using PDSG.Core.Mapping;
using PDSG.Core.Layout;

namespace PDSG.Core.Tests;

/// <summary>
/// 图块映射器单元测试
/// </summary>
public class BlockMapperTests
{
    [Fact]
    public void MapCircuits_WithMatchingRule_ReturnsCorrectBlock()
    {
        var circuits = new List<CircuitRecord>
        {
            new() { RowNumber = 1, CircuitId = "W1", CircuitName = "Test",
                     LoadType = LoadType.Power, BreakerPoles = 3, BreakerTripCurrentA = 100 }
        };

        var cfg = new BlockMappingConfig
        {
            DefaultBlock = "DEFAULT",
            Rules = new List<BlockMappingRule>
            {
                new() { Match = new() { ["load_type"] = "动力", ["poles"] = "3" }, Block = "LOOP_POWER_A" }
            }
        };

        var (mapped, warnings) = BlockMapper.MapCircuits(circuits, cfg);

        Assert.Single(mapped);
        Assert.Equal("LOOP_POWER_A", mapped[0].BlockName);
        Assert.Empty(warnings);
    }

    [Fact]
    public void MapCircuits_NoMatchingRule_UsesDefault()
    {
        var circuits = new List<CircuitRecord>
        {
            new() { RowNumber = 1, CircuitId = "W1", CircuitName = "Test",
                     LoadType = LoadType.Vfd, BreakerPoles = 3, BreakerTripCurrentA = 50 }
        };

        var cfg = new BlockMappingConfig
        {
            DefaultBlock = "DEFAULT",
            Rules = new List<BlockMappingRule>()
        };

        var (mapped, warnings) = BlockMapper.MapCircuits(circuits, cfg);

        Assert.Single(mapped);
        Assert.Equal("DEFAULT", mapped[0].BlockName);
        Assert.Single(warnings);
    }

    [Fact]
    public void MapCircuits_BreakerThreshold_MapsSmallCorrectly()
    {
        var circuits = new List<CircuitRecord>
        {
            new() { RowNumber = 1, CircuitId = "W1", CircuitName = "Small",
                     LoadType = LoadType.Power, BreakerPoles = 3, BreakerTripCurrentA = 200 },
            new() { RowNumber = 2, CircuitId = "W2", CircuitName = "Large",
                     LoadType = LoadType.Power, BreakerPoles = 3, BreakerTripCurrentA = 600 }
        };

        var cfg = new BlockMappingConfig
        {
            DefaultBlock = "DEFAULT",
            Rules = new List<BlockMappingRule>
            {
                new() { Match = new() { ["breaker_max_current"] = "400" }, Block = "LOOP_SMALL" },
                new() { Match = new() { ["breaker_min_current"] = "401" }, Block = "LOOP_LARGE" }
            }
        };

        var (mapped, _) = BlockMapper.MapCircuits(circuits, cfg);

        Assert.Equal("LOOP_SMALL", mapped[0].BlockName);
        Assert.Equal("LOOP_LARGE", mapped[1].BlockName);
    }
}
