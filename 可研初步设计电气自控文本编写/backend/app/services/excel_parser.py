# -*- coding: utf-8 -*-
"""
Excel 负荷计算表解析器
========================
支持 .xlsx (openpyxl) 与 .xls (xlrd)。
采用"需要系数法"：解析每个设备组，按区域分组汇总，
计算全厂安装容量、计算负荷、无功补偿容量与推荐变压器。

返回结构：
{
  'summary': {                       # 全局汇总
      'total_devices', 'total_equip_power', 'total_pjs', 'total_qjs',
      'total_sc_before', 'cos_before', 'qc_compensation', 'cos_target',
      'total_sc_after', 'recommended_transformer', 'tx_capacity', 'tx_count',
      'load_rate', 'area_count'
  },
  'area_summaries': { 区域名: {device_count, pe, pjs, qjs, sc, cos} },
  'devices': [ {area, name, pe, count, kx, cos, pjs, qjs, sc} ... ]
}
"""

import math
import os

# ---------- 列关键词匹配 ----------
COL_RULES = [
    ('name', ['设备组名称', '设备名称', '负荷名称', '名称', '设备']),
    ('pe',   ['额定功率', '单台功率', '设备功率', '功率(kw)', '功率']),
    ('count',['安装台数', '台数', '数量', '安装数量']),
    ('work', ['工作台数', '工作台数', '工作数']),
    ('kx',   ['需要系数', '需用系数', 'kx']),
    ('cos',  ['cos', '功率因数', 'cosφ', 'cos f']),
    ('tan',  ['tan', 'tanφ', 'tan f']),
    ('pc',   ['pc(kw)', 'pc', '有功计算负荷', '计算负荷(kw)']),
    ('qc',   ['qc(kvar)', 'qc', '无功计算负荷']),
    ('sc',   ['sc(kva)', 'sc', '视在计算负荷']),
]

# 汇总/非设备行关键词（出现则跳过）
SKIP_KEYWORDS = ['计算负荷', '总计算', '功率因数', '补偿', '变压器', '折算',
                 '侧总负荷', '同时系数', '损耗', '小计', '合计', '无功',
                 '选择变压器', '尖峰', '经济运行', '备注', '负荷等级']

STD_TX = [400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500]


def _norm(s):
    s = s if isinstance(s, str) else ('' if s is None else str(s))
    return s.replace(' ', '').replace('（', '(').replace('）', ')').lower()


def _match_col(header_cells):
    """根据表头cells返回 列角色->列索引 的映射。"""
    mapping = {}
    normed = [_norm(c) for c in header_cells]
    for role, kws in COL_RULES:
        if role in mapping:
            continue
        for i, h in enumerate(normed):
            if not h:
                continue
            for kw in kws:
                if kw in h:
                    mapping[role] = i
                    break
            if role in mapping:
                break
    return mapping


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _read_sheet(rows):
    """
    rows: list[list]，已转为纯值。
    返回 (devices, area_summaries)
    """
    devices = []
    area_summaries = {}
    header_idx = None
    col_map = None
    current_area = None

    for ri, row in enumerate(rows):
        # 找表头：含"设备组名称"或"设备名称"
        if header_idx is None:
            joined = ''.join(_norm(c) for c in row if c)
            if '设备组名称' in joined or '设备名称' in joined or '负荷名称' in joined:
                header_idx = ri
                col_map = _match_col(row)
                continue
            else:
                continue

        # 已是数据区
        name = row[0] if len(row) > 0 else None
        name = name if isinstance(name, str) else (str(name) if name is not None else '')

        # 收集关键列值
        def get(role):
            idx = col_map.get(role)
            if idx is None or idx >= len(row):
                return None
            v = row[idx]
            return v if _is_number(v) else None

        pe = get('pe')
        cnt = get('count')
        kx = get('kx')
        cos = get('cos')
        pc = get('pc')
        sc = get('sc')
        qc = get('qc')

        # 汇总/非设备行
        if any(kw in name for kw in SKIP_KEYWORDS):
            continue

        # 分组标题行：只有名称、无数值
        has_num = any(v is not None for v in (pe, cnt, kx, cos, pc, sc, qc))
        if not has_num:
            if name.strip():
                current_area = name.strip()
            continue

        # 设备行
        pe_install = (pe * cnt) if (pe is not None and cnt is not None) else (pe if pe else 0)
        # 有功计算负荷：优先用表内 PC，否则 Pe*Kx
        if pc is not None and pc > 0:
            pjs = pc
        elif pe_install > 0 and kx is not None:
            pjs = pe_install * kx
        elif pc is not None:
            pjs = pc
        else:
            pjs = 0.0

        cos_val = cos if (cos is not None and cos > 0) else (0.85 if cos is None else max(cos, 0.01))
        try:
            tan_val = math.tan(math.acos(min(max(cos_val, 0.01), 0.999)))
        except Exception:
            tan_val = 0.6

        if sc is not None and sc > 0:
            sjs = sc
        else:
            sjs = (pjs / cos_val) if cos_val > 0.01 else pjs
        qjs = (qc if (qc is not None) else pjs * tan_val)

        area = current_area if current_area else '全厂'
        rec = {
            'area': area,
            'name': name.strip(),
            'pe': round(pe_install, 2),
            'count': cnt if cnt is not None else 1,
            'kx': kx,
            'cos': round(cos_val, 3) if cos is not None else None,
            'pjs': round(pjs, 2),
            'qjs': round(qjs, 2),
            'sc': round(sjs, 2),
        }
        devices.append(rec)
        a = area_summaries.setdefault(area, {'device_count': 0, 'pe': 0.0, 'pjs': 0.0, 'qjs': 0.0, 'sc': 0.0})
        a['device_count'] += 1
        a['pe'] += pe_install
        a['pjs'] += pjs
        a['qjs'] += qjs
        a['sc'] += sjs

    return devices, area_summaries


def _load_rows(path):
    """返回 list[list]，统一 openpyxl / xlrd。"""
    ext = os.path.splitext(path)[1].lower()
    all_rows = []
    if ext == '.xls':
        import xlrd
        wb = xlrd.open_workbook(path)
        for sh in wb.sheets():
            rows = []
            for r in range(sh.nrows):
                rows.append([sh.cell_value(r, c) for c in range(sh.ncols)])
            all_rows.append(rows)
    else:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        for sh in wb.worksheets:
            rows = []
            for row in sh.iter_rows(values_only=True):
                rows.append(list(row))
            all_rows.append(rows)
    return all_rows


def select_transformer(s_after):
    for cap in STD_TX:
        if s_after <= cap:
            return f'1×{cap}kVA', cap, 1
    for cap in STD_TX:
        if s_after <= 2 * cap:
            return f'2×{cap}kVA', cap, 2
    return f'2×{STD_TX[-1]}kVA', STD_TX[-1], 2


def parse(path):
    """解析负荷计算表，返回完整结果字典。

    多 sheet 工作簿中通常主表（第一个含设备表头的 sheet）即为全厂负荷，
    其余 sheet 多为子项明细或模板残留，故只取第一个有效设备 sheet。
    """
    sheets = _load_rows(path)
    devices = []
    area_summaries = {}
    for rows in sheets:
        d, a = _read_sheet(rows)
        if d:                      # 找到第一个含设备的 sheet 即采用
            devices, area_summaries = d, a
            break

    # 全局汇总
    total_pe = sum(d['pe'] for d in devices)
    total_pjs = sum(d['pjs'] for d in devices)
    total_qjs = sum(d['qjs'] for d in devices)
    total_sc_before = math.sqrt(total_pjs ** 2 + total_qjs ** 2) if (total_pjs or total_qjs) else 0
    cos_before = (total_pjs / total_sc_before) if total_sc_before > 0 else 0.85
    cos_target = 0.92
    qc = 0.0
    if cos_before < cos_target and total_pjs > 0:
        qc = total_pjs * (math.tan(math.acos(cos_before)) - math.tan(math.acos(cos_target)))
    qc = max(qc, 0)
    total_sc_after = total_pjs / cos_target if cos_target > 0 else total_sc_before
    tx_str, tx_cap, tx_cnt = select_transformer(total_sc_after)
    load_rate = (total_sc_after / (tx_cap * tx_cnt)) if (tx_cap * tx_cnt) > 0 else 0

    # 区域整理：四舍五入
    for k, v in area_summaries.items():
        v['pe'] = round(v['pe'], 1)
        v['pjs'] = round(v['pjs'], 1)
        v['qjs'] = round(v['qjs'], 1)
        v['sc'] = round(v['sc'], 1)
        v['cos'] = round(v['pjs'] / v['sc'], 3) if v['sc'] > 0 else 0.85

    summary = {
        'total_devices': len(devices),
        'total_equip_power': round(total_pe, 1),
        'total_pjs': round(total_pjs, 1),
        'total_qjs': round(total_qjs, 1),
        'total_sc_before': round(total_sc_before, 1),
        'cos_before': round(cos_before, 3),
        'qc_compensation': round(qc, 1),
        'cos_target': cos_target,
        'total_sc_after': round(total_sc_after, 1),
        'recommended_transformer': tx_str,
        'tx_capacity': tx_cap,
        'tx_count': tx_cnt,
        'load_rate': round(load_rate, 3),
        'area_count': len(area_summaries),
    }
    return {'summary': summary, 'area_summaries': area_summaries, 'devices': devices}


if __name__ == '__main__':
    import sys, json
    p = sys.argv[1] if len(sys.argv) > 1 else r'D:\00-水厂负荷计算表.xlsx'
    res = parse(p)
    print(json.dumps(res['summary'], ensure_ascii=False, indent=2))
    print('区域数:', res['summary']['area_count'])
    for k, v in res['area_summaries'].items():
        print(f"  {k}: {v['device_count']}台, Pe={v['pe']}kW, Sjs={v['sc']}kVA")
