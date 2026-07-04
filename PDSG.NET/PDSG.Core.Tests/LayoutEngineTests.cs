using PDSG.Core.Models;
using PDSG.Core.Layout;

namespace PDSG.Core.Tests;

/// <summary>
/// 布局引擎单元测试
/// </summary>
public class LayoutEngineTests
{
    private static List<CircuitWithBlock> CreateTestCircuits(int count)
    {
        var circuits = new List<CircuitWithBlock>();
        for (int i = 1; i <= count; i++)
        {
            circuits.Add(new CircuitWithBlock
            {
                Record = new CircuitRecord
                {
                    RowNumber = i,
                    CircuitId = $"W{i}",
                    CircuitName = $"Load {i}",
                    LoadType = i % 2 == 0 ? LoadType.Lighting : LoadType.Power,
                    BreakerPoles = 3,
                    BreakerTripCurrentA = 100,
                    RatedPowerKw = i * 5,
                    RatedCurrentA = i * 10,
                    BreakerModel = "NSX100N",
                    CtRatio = "100/5",
                    CableType = "YJV",
                    CableSection = "3x25"
                },
                BlockName = "LOOP_POWER_A"
            });
        }
        return circuits;
    }

    [Fact]
    public void Compute_SingleCircuit_ReturnsSinglePlacement()
    {
        var circuits = CreateTestCircuits(1);
        var layoutCfg = new LayoutConfig
        {
            HorizontalSpacing = 60,
            BusX = 30,
            BusY = 200
        };
        var sortCfg = new SortConfig();

        var result = LayoutEngine.Compute(circuits, layoutCfg, sortCfg);

        Assert.Single(result.Placements);
        Assert.Equal(30, result.Placements[0].X);
        Assert.Equal(200, result.Placements[0].Y);
    }

    [Fact]
    public void Compute_MultipleCircuits_SpacingCorrect()
    {
        var circuits = CreateTestCircuits(5);
        var layoutCfg = new LayoutConfig
        {
            HorizontalSpacing = 60,
            BusX = 30,
            BusY = 200
        };
        var sortCfg = new SortConfig();

        var result = LayoutEngine.Compute(circuits, layoutCfg, sortCfg);

        Assert.Equal(5, result.Placements.Count);
        Assert.Equal(30, result.Placements[0].X);
        Assert.Equal(90, result.Placements[1].X);
        Assert.Equal(150, result.Placements[2].X);
    }

    [Fact]
    public void Compute_BusLine_CoversAllCircuits()
    {
        var circuits = CreateTestCircuits(4);
        var layoutCfg = new LayoutConfig
        {
            HorizontalSpacing = 60,
            BusX = 30,
            BusY = 200
        };
        var sortCfg = new SortConfig();

        var result = LayoutEngine.Compute(circuits, layoutCfg, sortCfg);

        Assert.Equal(30, result.BusLine.XStart);
        Assert.Equal(210, result.BusLine.XEnd); // 30 + 3*60
    }

    [Fact]
    public void Compute_EmptyCircuits_ThrowsArgumentException()
    {
        var circuits = new List<CircuitWithBlock>();
        var layoutCfg = new LayoutConfig();
        var sortCfg = new SortConfig();

        Assert.Throws<ArgumentException>(() =>
            LayoutEngine.Compute(circuits, layoutCfg, sortCfg));
    }

    [Fact]
    public void Compute_GroupLabels_GeneratedForEachGroup()
    {
        var circuits = new List<CircuitWithBlock>
        {
            new() { Record = new CircuitRecord { CircuitId = "W1", LoadType = LoadType.Power, CircuitName = "A", BreakerPoles = 3, BreakerTripCurrentA = 50, RatedPowerKw = 10, RatedCurrentA = 20, BreakerModel = "X", CtRatio = "1", CableType = "Y", CableSection = "1" },
                    BlockName = "B1" },
            new() { Record = new CircuitRecord { CircuitId = "W2", LoadType = LoadType.Lighting, CircuitName = "B", BreakerPoles = 1, BreakerTripCurrentA = 20, RatedPowerKw = 2, RatedCurrentA = 5, BreakerModel = "X", CtRatio = "1", CableType = "Y", CableSection = "1" },
                    BlockName = "B2" }
        };
        var layoutCfg = new LayoutConfig { HorizontalSpacing = 60, BusX = 30, BusY = 200 };
        var sortCfg = new SortConfig();

        var result = LayoutEngine.Compute(circuits, layoutCfg, sortCfg);

        Assert.Equal(2, result.GroupLabels.Count);
    }
}
