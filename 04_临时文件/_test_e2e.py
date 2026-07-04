# -*- coding: utf-8 -*-
"""端到端验证：用修复后的excel_importer解析所有Excel文件"""
import os, sys
sys.path.insert(0, 'd:\\qoderwork')
from load_calc.excel_importer import parse_excel_file

base = r'C:\Users\Administrator\AppData\Local\Temp'
all_files = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f.lower().endswith(('.xls', '.xlsx')) and 'Rar$' in root:
            all_files.append(os.path.join(root, f))

for fp in sorted(all_files):
    fname = os.path.basename(fp)
    print(f"{'='*60}")
    print(f"  文件: {fname}")
    print(f"{'='*60}")
    name, equip_list = parse_excel_file(fp)
    print(f"  建筑物: {name}")
    print(f"  识别设备数: {len(equip_list)}")
    for eq in equip_list:
        print(f"    {eq.name:20s} Pe={eq.rated_power:>6.1f}kW  installed={eq.installed_count} working={eq.working_count}")
    if not equip_list:
        print(f"  ⚠️  没有识别到任何设备!")
    print()
