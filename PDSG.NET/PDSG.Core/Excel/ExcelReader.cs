using ClosedXML.Excel;
using PDSG.Core.Models;
using PDSG.Core.Exceptions;

namespace PDSG.Core.Excel;

/// <summary>
/// PDSG Excel 读取器 — 使用 ClosedXML 读取和校验回路数据
/// </summary>
public static class ExcelReader
{
    /// <summary>
    /// 读取 Excel 并校验，返回有效回路和错误记录
    /// </summary>
    public static (List<CircuitRecord> Records, List<ErrorRecord> Errors)
        ReadAndValidate(string path, ExcelConfig cfg)
    {
        if (!File.Exists(path))
            throw new ExcelReadException($"Excel 文件不存在: {path}");

        using var workbook = new XLWorkbook(path);

        var ws = FindSheet(workbook, cfg.SheetName);

        var fmt = DetectFormat(ws, cfg);

        return fmt == ExcelFormat.Transposed
            ? ReadTransposed(ws, cfg)
            : ReadStandard(ws, cfg);
    }

    private static IXLWorksheet FindSheet(XLWorkbook wb, string sheetName)
    {
        if (wb.Worksheets.TryGetWorksheet(sheetName, out var ws))
            return ws;

        var first = wb.Worksheets.FirstOrDefault();
        if (first != null) return first;

        throw new ExcelReadException($"Excel 文件中未找到工作表: {sheetName}");
    }

    private static ExcelFormat DetectFormat(IXLWorksheet ws, ExcelConfig cfg)
    {
        if (!cfg.FormatAutoDetect) return ExcelFormat.Standard;

        var headerRow = ws.Row(cfg.HeaderRow);
        int nonEmptyHeaders = 0;
        foreach (var cell in headerRow.CellsUsed())
        {
            if (!string.IsNullOrWhiteSpace(cell.GetString()))
                nonEmptyHeaders++;
        }

        if (nonEmptyHeaders <= 3)
        {
            var firstCol = ws.Column(1);
            int paramRows = 0;
            for (int r = cfg.DataStartRow; r <= Math.Min(cfg.DataStartRow + 20, ws.LastRowUsed()?.RowNumber() ?? 0); r++)
            {
                if (!string.IsNullOrWhiteSpace(firstCol.Cell(r).GetString()))
                    paramRows++;
            }
            if (paramRows >= 5) return ExcelFormat.Transposed;
        }

        return ExcelFormat.Standard;
    }

    private static (List<CircuitRecord>, List<ErrorRecord>) ReadStandard(IXLWorksheet ws, ExcelConfig cfg)
    {
        var records = new List<CircuitRecord>();
        var errors = new List<ErrorRecord>();

        var aliasMap = BuildAliasMap(cfg);

        int lastRow = ws.LastRowUsed()?.RowNumber() ?? cfg.DataStartRow;

        for (int row = cfg.DataStartRow; row <= lastRow; row++)
        {
            var rawValues = new Dictionary<string, string>();
            foreach (var cell in ws.Row(row).CellsUsed())
            {
                rawValues[cell.Address.ColumnNumber.ToString()] = cell.GetString();
            }

            if (rawValues.Values.All(string.IsNullOrWhiteSpace))
                continue;

            try
            {
                var record = ParseStandardRow(row, rawValues, aliasMap, cfg);
                records.Add(record);
            }
            catch (CircuitValidationException ex)
            {
                errors.Add(new ErrorRecord
                {
                    RowNumber = row,
                    CircuitId = rawValues.TryGetValue("1", out var id) ? id : "",
                    ErrorType = "数据校验",
                    ErrorMessage = ex.Message,
                    RawValues = rawValues
                });
            }
        }

        return (records, errors);
    }

    private static CircuitRecord ParseStandardRow(
        int row,
        Dictionary<string, string> rawValues,
        Dictionary<int, string> aliasMap,
        ExcelConfig cfg)
    {
        var record = new CircuitRecord { RowNumber = row };

        string? GetField(string internalName)
        {
            foreach (var kv in cfg.ColumnAliases)
            {
                if (kv.Value == internalName)
                {
                    var matching = rawValues.FirstOrDefault(r =>
                        r.Value.Equals(kv.Key, StringComparison.OrdinalIgnoreCase));
                    if (!string.IsNullOrEmpty(matching.Value)) return matching.Value;
                }
            }
            return null;
        }

        record.CircuitId = GetField("circuit_id") ?? "";
        record.CircuitName = GetField("circuit_name") ?? "";
        record.BreakerModel = GetField("breaker_model") ?? cfg.DefaultBreakerModel;
        record.CtRatio = GetField("ct_ratio") ?? "";
        record.CableType = GetField("cable_type") ?? "";
        record.CableSection = GetField("cable_section") ?? "";

        var ltStr = GetField("load_type");
        record.LoadType = ltStr != null ? LoadTypeExtensions.FromString(ltStr) ?? LoadType.Power : LoadType.Power;

        var polesStr = GetField("breaker_poles");
        record.BreakerPoles = polesStr != null ? ParseInt(polesStr) : 3;

        var powerStr = GetField("rated_power_kw");
        record.RatedPowerKw = powerStr != null ? ParseDouble(powerStr) : 0;

        var currentStr = GetField("rated_current_a");
        record.RatedCurrentA = currentStr != null ? ParseDouble(currentStr) : 0;

        var tripStr = GetField("breaker_trip_current_a");
        record.BreakerTripCurrentA = tripStr != null ? ParseDouble(tripStr) : 0;

        record.Remark = GetField("remark");
        record.CabinetCode = GetField("cabinet_code");
        record.DistributionType = GetField("distribution_type");
        record.OperationMode = GetField("operation_mode");
        record.Contactor = GetField("contactor");
        record.ThermalRelay = GetField("thermal_relay");
        record.PowerMonitoring = GetField("power_monitoring");
        record.CableNumber = GetField("cable_number");

        var frameStr = GetField("breaker_frame_current_a");
        record.BreakerFrameCurrentA = frameStr != null ? ParseDouble(frameStr) : null;

        return record;
    }

    private static (List<CircuitRecord>, List<ErrorRecord>) ReadTransposed(IXLWorksheet ws, ExcelConfig cfg)
    {
        var records = new List<CircuitRecord>();
        var errors = new List<ErrorRecord>();

        int lastCol = ws.LastColumnUsed()?.ColumnNumber() ?? 1;

        for (int col = 2; col <= lastCol; col++)
        {
            try
            {
                var record = ParseTransposedColumn(ws, col, cfg);
                records.Add(record);
            }
            catch (CircuitValidationException ex)
            {
                errors.Add(new ErrorRecord
                {
                    RowNumber = 0,
                    CircuitId = $"Col{col}",
                    ErrorType = "数据校验",
                    ErrorMessage = ex.Message
                });
            }
        }

        return (records, errors);
    }

    private static CircuitRecord ParseTransposedColumn(IXLWorksheet ws, int col, ExcelConfig cfg)
    {
        var record = new CircuitRecord { RowNumber = col };

        string? GetParam(string paramAlias)
        {
            int lastRow = ws.LastRowUsed()?.RowNumber() ?? 0;
            for (int r = cfg.DataStartRow; r <= lastRow; r++)
            {
                var label = ws.Cell(r, 1).GetString();
                if (label.Equals(paramAlias, StringComparison.OrdinalIgnoreCase))
                    return ws.Cell(r, col).GetString();
            }
            return null;
        }

        record.CircuitId = $"C{col}";
        record.CircuitName = GetParam("回路用途") ?? "";

        var ltStr = GetParam("运行方式");
        if (ltStr != null && OperationModeToLoadType.TryGetValue(ltStr, out var inferred))
            record.LoadType = inferred;
        else
            record.LoadType = LoadType.Power;

        var powerStr = GetParam("设备功率Pe(kW)") ?? GetParam("设备功率");
        record.RatedPowerKw = powerStr != null ? ParseDouble(powerStr) : 0;

        var currentStr = GetParam("计算电流Ic(A)") ?? GetParam("计算电流");
        record.RatedCurrentA = currentStr != null ? ParseDouble(currentStr) : 0;

        record.BreakerModel = GetParam("断路器型号") ?? cfg.DefaultBreakerModel;

        var polesStr = GetParam("极数");
        record.BreakerPoles = polesStr != null ? ParseInt(polesStr) : 3;

        var tripStr = GetParam("脱扣器额定电流In(A)") ?? GetParam("脱扣器电流");
        record.BreakerTripCurrentA = tripStr != null ? ParseDouble(tripStr) : 0;

        record.CtRatio = GetParam("电流互感器变比") ?? "";
        record.CableType = GetParam("线缆型号规格") ?? "";
        record.CableNumber = GetParam("线缆编号") ?? "";
        record.OperationMode = GetParam("运行方式");
        record.DistributionType = GetParam("配电形式");
        record.Contactor = GetParam("接触器");
        record.ThermalRelay = GetParam("热继电器");
        record.PowerMonitoring = GetParam("电力监控信号");
        record.CabinetCode = GetParam("开关柜代号");

        var frameStr = GetParam("断路器壳架电流(A)");
        record.BreakerFrameCurrentA = frameStr != null ? ParseDouble(frameStr) : null;

        return record;
    }

    private static readonly Dictionary<string, LoadType> OperationModeToLoadType = new()
    {
        ["变频"] = LoadType.Vfd,
        ["工频"] = LoadType.Power,
        ["直启"] = LoadType.Power,
        ["软启"] = LoadType.Power,
        ["星三角"] = LoadType.Power
    };

    private static Dictionary<int, string> BuildAliasMap(ExcelConfig cfg) => new();

    private static double ParseDouble(string s)
    {
        s = s.Trim().Replace(",", "").Replace("kW", "").Replace("A", "").Replace("mm²", "");
        return double.TryParse(s, System.Globalization.NumberStyles.Any,
            System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : 0;
    }

    private static int ParseInt(string s)
    {
        s = s.Trim().Replace("P", "").Replace("p", "");
        return int.TryParse(s, out var v) ? v : 3;
    }
}
