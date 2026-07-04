using PDSG.Core.Models;

namespace PDSG.Core.Mapping;

/// <summary>
/// PDSG 属性构建器 — 将回路数据转换为图块属性键值对
/// </summary>
public static class AttributeBuilder
{
    /// <summary>
    /// 为单个回路构建图块属性
    /// </summary>
    public static Dictionary<string, string> BuildAttributes(
        CircuitRecord circuit,
        BlockDefinition? blockDef)
    {
        var allAttrs = new Dictionary<string, string>
        {
            ["CIRCUIT_ID"] = circuit.CircuitId,
            ["CIRCUIT_NAME"] = circuit.CircuitName,
            ["BREAKER_MODEL"] = circuit.BreakerModel,
            ["BREAKER_POLES"] = $"{circuit.BreakerPoles}P",
            ["BREAKER_Ir"] = $"{circuit.BreakerTripCurrentA:F1}A",
            ["CABLE_TYPE"] = circuit.CableType,
            ["CABLE_SECTION"] = circuit.CableSection,
            ["LOAD_POWER"] = $"{circuit.RatedPowerKw:F2}kW",
            ["LOAD_CURRENT"] = $"{circuit.RatedCurrentA:F2}A",
            ["LOAD_TYPE"] = circuit.LoadType.ToChinese(),
            ["CT_RATIO"] = circuit.CtRatio
        };

        if (!string.IsNullOrEmpty(circuit.CabinetCode))
            allAttrs["CABINET_CODE"] = circuit.CabinetCode;
        if (!string.IsNullOrEmpty(circuit.DistributionType))
            allAttrs["DISTRIBUTION_TYPE"] = circuit.DistributionType;
        if (!string.IsNullOrEmpty(circuit.OperationMode))
            allAttrs["OPERATION_MODE"] = circuit.OperationMode;
        if (circuit.BreakerFrameCurrentA.HasValue)
            allAttrs["BREAKER_FRAME"] = $"{circuit.BreakerFrameCurrentA.Value:F0}A";
        if (!string.IsNullOrEmpty(circuit.Contactor))
            allAttrs["CONTACTOR"] = circuit.Contactor;
        if (!string.IsNullOrEmpty(circuit.ThermalRelay))
            allAttrs["THERMAL_RELAY"] = circuit.ThermalRelay;
        if (!string.IsNullOrEmpty(circuit.PowerMonitoring))
            allAttrs["POWER_MONITORING"] = circuit.PowerMonitoring;
        if (!string.IsNullOrEmpty(circuit.CableNumber))
            allAttrs["CABLE_NUMBER"] = circuit.CableNumber;

        if (circuit.LoadType == LoadType.Vfd)
        {
            allAttrs["VFD_MODEL"] = circuit.VfdModel ?? "";
            allAttrs["VFD_POWER"] = circuit.VfdPowerKw.HasValue
                ? $"{circuit.VfdPowerKw.Value:F2}kW" : "";
        }

        if (!string.IsNullOrEmpty(circuit.Remark))
            allAttrs["REMARK"] = circuit.Remark;

        if (blockDef?.Attributes.Count > 0)
        {
            return blockDef.Attributes
                .Where(tag => allAttrs.ContainsKey(tag))
                .ToDictionary(tag => tag, tag => allAttrs[tag]);
        }

        return allAttrs;
    }

    /// <summary>
    /// 批量为所有已映射回路构建属性（就地写入）
    /// </summary>
    public static void BuildAllAttributes(
        List<CircuitWithBlock> mappedCircuits,
        BlockCatalog? catalog = null)
    {
        foreach (var cwb in mappedCircuits)
        {
            var blockDef = catalog?.Find(cwb.BlockName);
            cwb.Attributes = BuildAttributes(cwb.Record, blockDef);
        }
    }
}
