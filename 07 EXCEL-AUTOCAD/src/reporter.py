"""PDSG 报告生成器

使用 Jinja2 渲染 HTML 报告，包含:
- 处理时间戳与源文件
- 汇总统计
- 成功回路清单
- 错误/警告明细
- 图块使用统计
"""
import logging
import os
from datetime import datetime
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, BaseLoader

from .data_model import CircuitWithBlock, ErrorRecord

logger = logging.getLogger(__name__)

# 内嵌默认模板（当 templates/ 目录不存在时使用）
DEFAULT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>PDSG 处理报告</title>
<style>
  body { font-family: "Microsoft YaHei", "宋体", sans-serif; margin: 30px; background: #fafafa; }
  h1 { color: #333; border-bottom: 2px solid #4a90d9; padding-bottom: 8px; }
  h2 { color: #555; margin-top: 30px; }
  .summary { background: #fff; padding: 15px 20px; border-radius: 6px; border: 1px solid #ddd; margin: 15px 0; }
  .summary span { display: inline-block; margin-right: 30px; font-size: 16px; }
  .success { color: #27ae60; font-weight: bold; }
  .warning { color: #e67e22; font-weight: bold; }
  .error { color: #e74c3c; font-weight: bold; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 13px; }
  th { background: #4a90d9; color: #fff; }
  tr:nth-child(even) { background: #f5f5f5; }
  .footer { margin-top: 40px; color: #999; font-size: 12px; }
</style>
</head>
<body>
<h1>PDSG 配电系统图生成报告</h1>

<div class="summary">
  <span><strong>时间:</strong> {{ timestamp }}</span>
  <span><strong>源文件:</strong> {{ source_file }}</span><br>
  <span><strong>总回路数:</strong> {{ total }}</span>
  <span class="success"><strong>成功:</strong> {{ success_count }}</span>
  <span class="warning"><strong>警告:</strong> {{ warning_count }}</span>
  <span class="error"><strong>跳过:</strong> {{ error_count }}</span>
</div>

{% if block_stats %}
<h2>图块使用统计</h2>
<table>
  <tr><th>图块名称</th><th>使用次数</th></tr>
  {% for name, count in block_stats.items() %}
  <tr><td>{{ name }}</td><td>{{ count }}</td></tr>
  {% endfor %}
</table>
{% endif %}

{% if success_list %}
<h2>成功回路清单</h2>
<table>
  <tr><th>回路编号</th><th>回路名称</th><th>负荷类型</th><th>图块名称</th><th>X</th><th>Y</th></tr>
  {% for item in success_list %}
  <tr>
    <td>{{ item.circuit_id }}</td>
    <td>{{ item.circuit_name }}</td>
    <td>{{ item.load_type }}</td>
    <td>{{ item.block_name }}</td>
    <td>{{ "%.1f"|format(item.x) }}</td>
    <td>{{ "%.1f"|format(item.y) }}</td>
  </tr>
  {% endfor %}
</table>
{% endif %}

{% if errors %}
<h2>错误/跳过多细</h2>
<table>
  <tr><th>Excel行号</th><th>回路编号</th><th>错误类型</th><th>错误消息</th></tr>
  {% for e in errors %}
  <tr>
    <td>{{ e.row_number }}</td>
    <td>{{ e.circuit_id }}</td>
    <td>{{ e.error_type }}</td>
    <td>{{ e.error_message }}</td>
  </tr>
  {% endfor %}
</table>
{% endif %}

{% if warnings %}
<h2>警告明细</h2>
<table>
  <tr><th>Excel行号</th><th>回路编号</th><th>类型</th><th>消息</th></tr>
  {% for w in warnings %}
  <tr>
    <td>{{ w.row_number }}</td>
    <td>{{ w.circuit_id }}</td>
    <td>{{ w.error_type }}</td>
    <td>{{ w.error_message }}</td>
  </tr>
  {% endfor %}
</table>
{% endif %}

<div class="footer">
  PDSG v1.0.0 — 配电柜系统图自动生成程序 | {{ timestamp }}
</div>
</body>
</html>
"""


def generate(
    errors: List[ErrorRecord],
    mapped: List[CircuitWithBlock],
    warnings: List[ErrorRecord],
    source_file: str,
    report_path: str,
    placements=None,
    template_dir: str = None,
) -> str:
    """生成 HTML 报告

    Args:
        errors: 校验失败的错误记录
        mapped: 成功映射的回路列表
        warnings: 映射警告
        source_file: 源 Excel 文件路径
        report_path: 报告输出路径
        placements: 布局放置结果（可选，用于显示坐标）
        template_dir: Jinja2 模板目录（可选）

    Returns:
        生成的报告文件路径
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建成功回路清单
    success_list = []
    placement_map = {}
    if placements:
        for p in placements:
            placement_map[p.circuit_id] = p

    for cwb in mapped:
        p = placement_map.get(cwb.record.circuit_id)
        success_list.append({
            "circuit_id": cwb.record.circuit_id,
            "circuit_name": cwb.record.circuit_name,
            "load_type": cwb.record.load_type.value,
            "block_name": cwb.block_name,
            "x": p.x if p else 0,
            "y": p.y if p else 0,
        })

    # 图块使用统计
    block_stats: Dict[str, int] = {}
    for cwb in mapped:
        block_stats[cwb.block_name] = block_stats.get(cwb.block_name, 0) + 1

    # 渲染
    if template_dir and os.path.isdir(template_dir):
        env = Environment(loader=FileSystemLoader(template_dir))
        try:
            template = env.get_template("report.html.j2")
        except Exception:
            template = env.from_string(DEFAULT_TEMPLATE)
    else:
        template = Environment(loader=BaseLoader()).from_string(DEFAULT_TEMPLATE)

    html = template.render(
        timestamp=timestamp,
        source_file=os.path.basename(source_file),
        total=len(mapped) + len(errors),
        success_count=len(mapped),
        warning_count=len(warnings),
        error_count=len(errors),
        block_stats=block_stats,
        success_list=success_list,
        errors=errors,
        warnings=warnings,
    )

    # 写入文件
    abs_path = os.path.abspath(report_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("报告已生成: %s", abs_path)
    return abs_path
