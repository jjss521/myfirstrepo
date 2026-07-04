# -*- coding: utf-8 -*-
"""测试Excel文件解析"""
import os, sys, glob

base_temp = r'C:\Users\Administrator\AppData\Local\Temp'
# 找到所有 Rar$ 文件夹下的 xls/xlsx 文件
all_files = []
for root, dirs, files in os.walk(base_temp):
    for f in files:
        if f.lower().endswith(('.xls', '.xlsx')) and 'Rar$' in root:
            all_files.append(os.path.join(root, f))

print(f"找到 {len(all_files)} 个Excel文件:")
for fp in all_files:
    print(f"  [{os.path.getsize(fp)} bytes] {os.path.basename(fp)}")

print("\n" + "="*80)

for fp in all_files:
    fname = os.path.basename(fp)
    ext = os.path.splitext(fp)[1].lower()
    print(f"\n{'='*60}")
    print(f"  文件: {fname} ({ext})")
    print(f"{'='*60}")
    
    if ext == '.xlsx':
        import openpyxl
        wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
        ws = wb.active
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append([str(c or "").strip() for c in row])
        wb.close()
    else:
        import xlrd
        wb = xlrd.open_workbook(fp)
        ws = wb.sheet_by_index(0)
        rows = [[str(ws.cell_value(r, c)).strip() for c in range(ws.ncols)] for r in range(ws.nrows)]
    
    print(f"  行数: {len(rows)}, 列数: {len(rows[0]) if rows else 0}")
    
    # 打印表头
    if rows:
        print(f"  表头: {rows[0]}")
    
    # 打印前20行数据
    for r in range(1, min(len(rows), 25)):
        print(f"  行{r}: {rows[r]}")
