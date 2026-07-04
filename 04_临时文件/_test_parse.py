# -*- coding: utf-8 -*-
"""模拟当前 excel_importer.py 对各Excel文件的解析结果"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 复制当前 excel_importer 的关键函数进行测试
def _guess_column_index(headers, candidates):
    for i, h in enumerate(headers):
        h_clean = str(h).strip().replace(" ", "")
        for cand in candidates:
            if h_clean == cand.replace(" ", ""):
                return i
    return None

def parse_power_from_text(text):
    if not text:
        return None
    for pattern in [
        r'[NPnp]\s*[≈=:：]?\s*(\d+\.?\d*)\s*[kK][wW]',
        r'(\d+\.?\d*)\s*[kK][wW]',
    ]:
        m = re.search(pattern, text)
        if m:
            val = float(m.group(1))
            if val > 0:
                return val
    return None

def parse_working_info(quantity_val, remark=""):
    installed = int(float(quantity_val)) if quantity_val else 1
    if remark:
        m = re.search(r'(\d+)\s*用\s*(\d+)', remark)
        if m:
            working = int(m.group(1))
            backup = int(m.group(2))
            future_m = re.search(r'远期增加\s*(\d+)', remark)
            extra = int(future_m.group(1)) if future_m else 0
            return max(working + backup + extra, installed), working
    return installed, installed

def parse_excel_file_sim(file_path):
    building_name = os.path.splitext(os.path.basename(file_path))[0].strip()
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.xlsx':
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = [list(row) for row in ws.iter_rows(values_only=True)]
        wb.close()
    else:
        import xlrd
        wb = xlrd.open_workbook(file_path)
        ws = wb.sheet_by_index(0)
        rows = [[ws.cell_value(r, c) for c in range(ws.ncols)] for r in range(ws.nrows)]
    
    if not rows or len(rows) < 2:
        return building_name, [], "无数据"
    
    headers = [str(c or "") for c in rows[0]]
    data_rows = rows[1:]
    
    name_c = _guess_column_index(headers, ["名 称", "名称", "设备名称"])
    spec_c = _guess_column_index(headers, ["规 格", "规格", "型号", "参数", "设备主要参数", "设备参数"])
    qty_c = _guess_column_index(headers, ["数量", "台数"])
    rem_c = _guess_column_index(headers, ["备 注", "备注", "说明"])
    
    debug = f"name_c={name_c}, spec_c={spec_c}, qty_c={qty_c}, rem_c={rem_c}, 表头={headers}"
    
    if name_c is None:
        return building_name, [], debug
    
    equip_list = []
    errors = []
    for ri, row in enumerate(data_rows):
        if not row or all(str(c or "").strip() == "" for c in row):
            continue
        name = str(row[name_c]).strip() if name_c < len(row) else ""
        if not name:
            continue
        
        power = None
        spec_text = ""
        if spec_c is not None and spec_c < len(row):
            spec_text = str(row[spec_c]).strip()
            power = parse_power_from_text(spec_text)
        
        qty = 1
        if qty_c is not None and qty_c < len(row):
            try:
                qty = int(float(str(row[qty_c])))
            except (ValueError, TypeError):
                qty = 1
        
        remark = str(row[rem_c]).strip() if rem_c is not None and rem_c < len(row) else ""
        installed, working = parse_working_info(qty, remark)
        
        if power is None or power <= 0:
            errors.append(f"  ❌ 行{ri+1}: {name} | 规格='{spec_text[:40]}' → 未提取到功率")
        else:
            errors.append(f"  ✅ 行{ri+1}: {name} | power={power}kW | installed={installed}, working={working}")
    
    return building_name, errors, debug


base = r'C:\Users\Administrator\AppData\Local\Temp'
all_files = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f.lower().endswith(('.xls', '.xlsx')) and 'Rar$' in root:
            all_files.append(os.path.join(root, f))

print("=" * 70)
print("  当前 excel_importer.py 解析结果模拟")
print("=" * 70)

for fp in sorted(all_files):
    fname = os.path.basename(fp)
    print(f"\n{'='*60}")
    print(f"  文件: {fname}")
    print(f"{'='*60}")
    name, results, debug = parse_excel_file_sim(fp)
    print(f"  建筑物名: {name}")
    print(f"  诊断: {debug}")
    if results:
        for r in results:
            print(r)
    else:
        print("  ⚠️ 没有任何设备被识别!")
