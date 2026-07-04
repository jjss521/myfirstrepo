using PDSG.Core.Models;
using PDSG.Core.Mapping;

namespace PDSG.Core.Tests;

/// <summary>
/// 属性构建器单元测试
/// </summary>
public class AttributeBuilderTests
{
    [Fact]
    public void BuildAttributes_BasicCircuit_ReturnsAllRequiredFields()
    {
        var circuit = new CircuitRecord
        {
            CircuitId = "W1",
            CircuitName = "Motor Pump",
            LoadType = LoadType.Power,
            RatedPowerKw = 15.5,
            RatedCurrentA = 30.2,
            BreakerModel = "NSX100N",
            BreakerPoles = 3,
            BreakerTripCurrentA = 80,
            CtRatio = "100/5",
            CableType = "YJV",
            CableSection = "3x25+1x16"
        };

        var attrs = AttributeBuilder.BuildAttributes(circuit, null);

        Assert.Equal("W1", attrs["CIRCUIT_ID"]);
        Assert.Equal("Motor Pump", attrs["CIRCUIT_NAME"]);
        Assert.Equal("NSX100N", attrs["BREAKER_MODEL"]);
        Assert.Equal("3P", attrs["BREAKER_POLES"]);
        Assert.Equal("80.0A", attrs["BREAKER_Ir"]);
        Assert.Equal("YJV", attrs["CABLE_TYPE"]);
        Assert.Equal("3x25+1x16", attrs["CABLE_SECTION"]);
        Assert.Equal("15.50kW", attrs["LOAD_POWER"]);
        Assert.Equal("30.20A", attrs["LOAD_CURRENT"]);
        Assert.Equal("动力", attrs["LOAD_TYPE"]);
        Assert.Equal("100/5", attrs["CT_RATIO"]);
    }

    [Fact]
    public void BuildAttributes_WithBlockDef_FiltersAttributes()
    {
        var circuit = new CircuitRecord
        {
            CircuitId = "W1",
            CircuitName = "Test",
            LoadType = LoadType.Power,
            BreakerPoles = 3,
            BreakerTripCurrentA = 50,
            RatedPowerKw = 10,
            RatedCurrentA = 20,
            BreakerModel = "NSX100N",
            CtRatio = "50/5",
            CableType = "YJV",
            CableSection = "3x16"
        };

        var blockDef = new BlockDefinition
        {
            Name = "TEST",
            Attributes = new List<string> { "CIRCUIT_ID", "CIRCUIT_NAME", "BREAKER_MODEL" }
        };

        var attrs = AttributeBuilder.BuildAttributes(circuit, blockDef);

        Assert.Equal(3, attrs.Count);
        Assert.True(attrs.ContainsKey("CIRCUIT_ID"));
        Assert.True(attrs.ContainsKey("CIRCUIT_NAME"));
        Assert.True(attrs.ContainsKey("BREAKER_MODEL"));
        Assert.False(attrs.ContainsKey("LOAD_POWER"));
    }

    [Fact]
    public void BuildAttributes_VfdCircuit_IncludesVfdFields()
    {
        var circuit = new CircuitRecord
        {
            CircuitId = "V1",
            CircuitName = "Fan",
            LoadType = LoadType.Vfd,
            VfdModel = "ABB ACS580",
            VfdPowerKw = 7.5,
            BreakerPoles = 3,
            BreakerTripCurrentA = 25,
            RatedPowerKw = 7.5,
            RatedCurrentA = 15,
            BreakerModel = "NSX100N",
            CtRatio = "30/5",
            CableType = "YJV",
            CableSection = "3x6"
        };

        var attrs = AttributeBuilder.BuildAttributes(circuit, null);

        Assert.Equal("ABB ACS580", attrs["VFD_MODEL"]);
        Assert.Equal("7.50kW", attrs["VFD_POWER"]);
    }
}
