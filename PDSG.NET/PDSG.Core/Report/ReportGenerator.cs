using System.Text;
using PDSG.Core.Models;

namespace PDSG.Core.Report;

/// <summary>
/// PDSG 报告生成器 — 使用 Scriban 渲染 HTML 报告
/// </summary>
public static class ReportGenerator
{
    private const string DefaultTemplate = @"<!DOCTYPE html>
<html lang=""zh-CN"">
<head>
<meta charset=""UTF-8"">
<title>PDSG 处理报告</title>
<style>
  body { font-family: 'Microsoft YaHei', sans-serif; margin: 30px; background: #fafafa; }
  h1 { color: #333; border-bottom: 2px solid #4a90d9; padding-bottom: 8px; }
  .summary { background: #fff; padding: 15px 20px; border-radius: 6px; border: 1px solid #ddd; margin: 15px 0; }
  .summary span { display: inline-block; margin-right: 30px; font-size: 16px; }
  .success { color: #27ae60; font-weight: bold; }
  .warning { color: #e67e22; font-weight: bold; }
  .error { color: #e74c3c; font-weight: bold; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 13px; }
  th { background: #4a90d9; color: #fff; }
  tr:nth-child(even) { background: #f5f5f5; }
</style>
</head>
<body>
<h1>PDSG 配电系统图生成报告</h1>
<div class=""summary"">
  <span><b>时间:</b> {{ timestamp }}</span>
  <span><b>源文件:</b> {{ source_file }}</span><br>
  <span><b>总回路数:</b> {{ total }}</span>
  <span class=""success""><b>成功:</b> {{ success_count }}</span>
  <span class=""warning""><b>警告:</b> {{ warning_count }}</span>
  <span class=""error""><b>跳过:</b> {{ error_count }}</span>
</div>

{{ if success_list.size > 0 }}
<h2>成功回路清单</h2>
<table>
  <tr><th>回路编号</th><th>回路名称</th><th>负荷类型</th><th>图块名称</th><th>X</th><th>Y</th></tr>
  {{ for item in success_list }}
  <tr>
    <td>{{ item.circuit_id }}</td>
    <td>{{ item.circuit_name }}</td>
    <td>{{ item.load_type }}</td>
    <td>{{ item.block_name }}</td>
    <td>{{ item.x }}</td>
    <td>{{ item.y }}</td>
  </tr>
  {{ end }}
</table>
{{ end }}

{{ if errors.size > 0 }}
<h2>错误/跳过明细</h2>
<table>
  <tr><th>Excel行号</th><th>回路编号</th><th>错误类型</th><th>错误消息</th></tr>
  {{ for e in errors }}
  <tr>
    <td>{{ e.row_number }}</td>
    <td>{{ e.circuit_id }}</td>
    <td>{{ e.error_type }}</td>
    <td>{{ e.error_message }}</td>
  </tr>
  {{ end }}
</table>
{{ end }}

{{ if warnings.size > 0 }}
<h2>警告明细</h2>
<table>
  <tr><th>回路编号</th><th>警告类型</th><th>警告消息</th></tr>
  {{ for w in warnings }}
  <tr>
    <td>{{ w.circuit_id }}</td>
    <td>{{ w.error_type }}</td>
    <td>{{ w.error_message }}</td>
  </tr>
  {{ end }}
</table>
{{ end }}

<div style=""margin-top:40px;color:#999;font-size:12px"">PDSG v2.0 (.NET) — 自动生成</div>
</body>
</html>";

    /// <summary>
    /// 生成 HTML 报告
    /// </summary>
    public static void Generate(
        List<ErrorRecord> errors,
        List<CircuitWithBlock> mapped,
        List<ErrorRecord> warnings,
        string sourceFile,
        string reportPath,
        List<Placement>? placements = null)
    {
        var dir = Path.GetDirectoryName(reportPath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        var successList = new List<object>();
        if (placements != null)
        {
            foreach (var p in placements)
            {
                var circuit = mapped.FirstOrDefault(m => m.Record.CircuitId == p.CircuitId);
                successList.Add(new
                {
                    circuit_id = p.CircuitId,
                    circuit_name = circuit?.Record.CircuitName ?? "",
                    load_type = circuit?.Record.LoadType.ToChinese() ?? "",
                    block_name = p.BlockName,
                    x = $"{p.X:F1}",
                    y = $"{p.Y:F1}"
                });
            }
        }

        var template = Scriban.Template.Parse(DefaultTemplate);
        var html = template.Render(new
        {
            timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            source_file = Path.GetFileName(sourceFile),
            total = mapped.Count + errors.Count,
            success_count = mapped.Count,
            warning_count = warnings.Count,
            error_count = errors.Count,
            success_list = successList,
            errors = errors.Select(e => new
            {
                row_number = e.RowNumber,
                circuit_id = e.CircuitId,
                error_type = e.ErrorType,
                error_message = e.ErrorMessage
            }),
            warnings = warnings.Select(w => new
            {
                circuit_id = w.CircuitId,
                error_type = w.ErrorType,
                error_message = w.ErrorMessage
            })
        });

        File.WriteAllText(reportPath, html, Encoding.UTF8);
    }
}
