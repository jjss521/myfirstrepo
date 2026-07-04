namespace PDSG.Core.Models;

/// <summary>
/// Excel 原始行数据
/// </summary>
public record RawRow(int RowNumber, Dictionary<string, string> Values);

/// <summary>
/// 校验后的回路记录
/// </summary>
public class CircuitRecord
{
    public int RowNumber { get; set; }
    public string CircuitId { get; set; } = "";
    public string CircuitName { get; set; } = "";
    public LoadType LoadType { get; set; }
    public double RatedPowerKw { get; set; }
    public double RatedCurrentA { get; set; }
    public string BreakerModel { get; set; } = "";
    public int BreakerPoles { get; set; }
    public double BreakerTripCurrentA { get; set; }
    public string CtRatio { get; set; } = "";
    public string CableType { get; set; } = "";
    public string CableSection { get; set; } = "";
    public string? VfdModel { get; set; }
    public double? VfdPowerKw { get; set; }
    public string? Remark { get; set; }
    public string? CabinetCode { get; set; }
    public string? CabinetSize { get; set; }
    public string? UnitSpace { get; set; }
    public string? DistributionType { get; set; }
    public string? OperationMode { get; set; }
    public double? BreakerFrameCurrentA { get; set; }
    public string? Contactor { get; set; }
    public string? ThermalRelay { get; set; }
    public string? PowerMonitoring { get; set; }
    public string? CableNumber { get; set; }
}

/// <summary>
/// 校验失败记录
/// </summary>
public class ErrorRecord
{
    public int RowNumber { get; set; }
    public string CircuitId { get; set; } = "";
    public string ErrorType { get; set; } = "";
    public string ErrorMessage { get; set; } = "";
    public Dictionary<string, string> RawValues { get; set; } = new();
}
