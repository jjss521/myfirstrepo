# -*- coding: utf-8 -*-
"""验证修复后的 excel_importer.py"""
import sys; sys.path.insert(0, 'd:\\qoderwork')
from load_calc.excel_importer import _guess_column_index, parse_power_from_text, parse_working_info

# ═══ 测试1: 列标题匹配 ═══
print('=== 列标题匹配测试 ===')
tests = [
    (['编 号', '名   称', '规    格', '材 料', '单 位', '数 量', '备   注'], '沼气池', '名称'),
    (['序号', '设备工艺名称', '型号及规格', '单位', '数量', '备注'], '综合工房', '名称'),
    (['序号', '设备工艺名称', '型号及规格', '单位', '数量', '备注'], '综合工房', '规格'),
    (['序号', '设备工艺名称', '型号及规格', '单位', '数量', '材质', '备注'], '药剂储罐', '名称'),
    (['序号', '设备工艺名称', '型号及规格', '单位', '数量', '材质', '备注'], '药剂储罐', '规格'),
    (['序号', '设备工艺名称', '型号及规格', '单位', '数量', '备注'], '预处理池', '名称'),
    (['序号', '设备工艺名称', '型号及规格', '单位', '数量', '备注'], '预处理池', '规格'),
]
candidates_map = {
    '名称': ['名 称', '名称', '设备名称'],
    '规格': ['规 格', '规格', '型号', '参数', '设备主要参数', '设备参数'],
}
for headers, fname, col_type in tests:
    idx = _guess_column_index(headers, candidates_map[col_type])
    print(f'  {"✅" if idx is not None else "❌"} {fname}.{col_type}: col={idx}')

# ═══ 测试2: 功率提取 ═══
print('\n=== 功率提取测试 ===')
power_tests = [
    ('功率5.5kW', 5.5),
    ('P=2.5kW', 2.5),
    ('N=4kw', 4),
    ('电机功率：1.5kW', 1.5),
    ('压滤机电机功率:19.5kW', 19.5),
    ('压缩机功率:0.29KW', 0.29),
    ('行走功率2X1.5KW', 1.5),
    ('Q=94m3/min,H=0.7Bar,P=120kW', 120),
    ('Q=25m3/h , H=13m , N=4kw', 4),
    ('功率 30kw', 30),
    ('0.75KW', 0.75),
    ('DN200', None),
    ('3匹', None),
]
for text, expected in power_tests:
    val = parse_power_from_text(text)
    ok = (val == expected) or (expected is None and val is None) or (expected is not None and val is not None and abs(val - expected) < 0.01)
    print(f'  {"✅" if ok else "❌"} "{text[:30]:30s}" → {val} (期望{expected})')

# ═══ 测试3: 几用几备 ═══
print('\n=== 几用几备解析测试 ===')
work_tests = [
    ('两用一备', '两用一备,配置变频器', 3, 2),
    ('1用1备', '1用1备', 2, 1),
    ('2用1备', '2用1备', 3, 2),
    ('3 用 2 备', '3 用 2 备', 5, 3),
    ('2用', '2用', 2, 2),
    ('5用1备', '5用1备,兼做事故池搅拌', 6, 5),
    ('4 用 2 备', '4 用 2 备', 6, 4),
]
for label, remark, exp_inst, exp_work in work_tests:
    inst, work = parse_working_info(exp_inst, remark)
    ok = (inst == exp_inst and work == exp_work)
    print(f'  {"✅" if ok else "❌"} {label:12s} → installed={inst}, working={work} (期望{exp_inst},{exp_work})')
