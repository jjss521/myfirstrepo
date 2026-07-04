using PDSG.Core.Models;

namespace PDSG.Core.Layout;

/// <summary>
/// PDSG 布局引擎 — 计算图块放置坐标、母线位置、参数表格和图纸幅面
/// </summary>
public static class LayoutEngine
{
    private static readonly List<string> TableRowDefs = new()
    {
        "回路编号", "回路名称", "负荷类型", "功率(kW)", "电流(A)",
        "断路器型号", "极数", "脱扣器(A)", "CT变比",
        "电缆型号", "电缆截面", "备注"
    };

    /// <summary>
    /// 计算水平布局
    /// </summary>
    public static LayoutResult Compute(
        List<CircuitWithBlock> circuits,
        LayoutConfig layoutCfg,
        SortConfig sortCfg)
    {
        if (circuits.Count == 0)
            throw new ArgumentException("无有效回路数据，无法计算布局");

        var ordered = GroupAndSort(circuits, sortCfg);

        int totalCircuits = ordered.Count;
        double spacing = layoutCfg.HorizontalSpacing;
        var margins = layoutCfg.Margins;

        // 计算各回路放置坐标
        var placements = new List<Placement>();
        double firstX = layoutCfg.BusX;
        double busY = layoutCfg.BusY;

        for (int i = 0; i < ordered.Count; i++)
        {
            double x = firstX + i * spacing;
            placements.Add(new Placement
            {
                BlockName = ordered[i].BlockName,
                X = x,
                Y = busY,
                Attributes = ordered[i].Attributes,
                CircuitId = ordered[i].Record.CircuitId
            });
        }

        // 水平母线
        double lastX = totalCircuits > 1
            ? firstX + (totalCircuits - 1) * spacing
            : firstX;

        var busLine = new BusLine
        {
            Direction = "horizontal",
            BusY = busY,
            XStart = firstX,
            XEnd = lastX,
            X = firstX,
            YStart = busY,
            YEnd = busY
        };

        // 分组标签
        var groupLabels = new List<GroupLabel>();
        int idx = 0;
        var groups = GroupCircuits(circuits, sortCfg);
        foreach (var (groupName, items) in groups)
        {
            double labelX = firstX + idx * spacing;
            double labelY = busY + 15;
            groupLabels.Add(new GroupLabel(groupName, labelX, labelY));
            idx += items.Count;
        }

        // 选择图纸幅面
        var paperSize = SelectPaperSize(totalCircuits, spacing, margins, layoutCfg.Paper);

        // 参数表格
        var table = ComputeTable(ordered, firstX, busY - 60, spacing, margins);

        return new LayoutResult
        {
            Placements = placements,
            BusLine = busLine,
            GroupLabels = groupLabels,
            PaperSize = paperSize,
            Table = table
        };
    }

    private static List<CircuitWithBlock> GroupAndSort(
        List<CircuitWithBlock> circuits, SortConfig sortCfg)
    {
        var groups = GroupCircuits(circuits, sortCfg);
        var result = new List<CircuitWithBlock>();
        foreach (var (_, items) in groups)
            result.AddRange(items);
        return result;
    }

    private static List<(string Name, List<CircuitWithBlock> Items)> GroupCircuits(
        List<CircuitWithBlock> circuits, SortConfig sortCfg)
    {
        var grouped = circuits
            .GroupBy(c => sortCfg.GroupBy switch
            {
                "load_type" => c.Record.LoadType.ToChinese(),
                _ => "全部"
            })
            .Select(g => (
                Name: g.Key,
                Items: g.OrderBy(c => c.Record.CircuitId).ToList()
            ))
            .ToList();

        return grouped;
    }

    private static TableLayout ComputeTable(
        List<CircuitWithBlock> circuits,
        double startX, double startY,
        double spacing, MarginsConfig margins)
    {
        var table = new TableLayout
        {
            X = startX,
            Y = startY,
            ColWidth = spacing * 0.8,
            LabelColWidth = 30,
            RowHeight = 7,
            RowLabels = new List<string>(TableRowDefs),
            Headers = circuits.Select(c => c.Record.CircuitId).ToList(),
            Rows = new List<List<string>>()
        };

        foreach (var label in TableRowDefs)
        {
            var row = new List<string>();
            foreach (var c in circuits)
            {
                row.Add(GetTableRowValue(c.Record, label));
            }
            table.Rows.Add(row);
        }

        return table;
    }

    private static string GetTableRowValue(CircuitRecord r, string label) => label switch
    {
        "回路编号" => r.CircuitId,
        "回路名称" => r.CircuitName,
        "负荷类型" => r.LoadType.ToChinese(),
        "功率(kW)" => r.RatedPowerKw > 0 ? $"{r.RatedPowerKw:F1}" : "",
        "电流(A)" => r.RatedCurrentA > 0 ? $"{r.RatedCurrentA:F1}" : "",
        "断路器型号" => r.BreakerModel,
        "极数" => $"{r.BreakerPoles}P",
        "脱扣器(A)" => r.BreakerTripCurrentA > 0 ? $"{r.BreakerTripCurrentA:F0}" : "",
        "CT变比" => r.CtRatio,
        "电缆型号" => r.CableType,
        "电缆截面" => r.CableSection,
        "备注" => r.Remark ?? "",
        _ => ""
    };

    private static PaperSize SelectPaperSize(
        int circuitCount, double spacing,
        MarginsConfig margins, PaperConfig paperCfg)
    {
        double requiredWidth = circuitCount * spacing + margins.Left + margins.Right;

        var sizes = paperCfg.Sizes
            .OrderBy(s => s.Width)
            .ToList();

        foreach (var s in sizes)
        {
            double w = paperCfg.Orientation == "landscape" ? Math.Max(s.Width, s.Height) : Math.Min(s.Width, s.Height);
            if (w >= requiredWidth)
                return new PaperSize(s.Name, s.Width, s.Height);
        }

        var largest = sizes.LastOrDefault() ?? new PaperSizeDef { Name = "A1", Width = 841, Height = 594 };
        return new PaperSize(largest.Name, largest.Width, largest.Height);
    }
}
