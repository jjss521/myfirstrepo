# -*- coding: utf-8 -*-
"""Excel导入模块 - 从设备清单Excel文件导入设备数据"""

import os
import re
from .models import Equipment, EquipmentGroup


def _guess_column_index(headers, candidates):
    """模糊匹配列标题，返回列索引

    策略：先尝试精确匹配，再尝试包含匹配（candidate是header的子串），
    最后尝试逐字包含匹配（header包含candidate中的每个字）。
    """
    for i, h in enumerate(headers):
        h_clean = str(h).strip().replace(" ", "").replace("　", "")
        for cand in candidates:
            cand_clean = cand.replace(" ", "").replace("　", "")
            # 1) 精确匹配
            if h_clean == cand_clean:
                return i
            # 2) 包含匹配：candidate是header的子串
            if cand_clean in h_clean:
                return i
            # 3) 逐字包含：header包含candidate中的所有字（应对"设备工艺名称"→"名称"）
            all_chars_found = all(ch in h_clean for ch in cand_clean if '\u4e00' <= ch <= '\u9fff')
            if all_chars_found and len(cand_clean) >= 2:
                # 只有当candidate中的中文字全部在header中且长度合理才返回
                char_ratio = sum(1 for ch in cand_clean if '\u4e00' <= ch <= '\u9fff') / max(len(cand_clean), 1)
                if char_ratio > 0.5:  # candidate中大部分是中文
                    return i
    return None


def parse_power_from_text(text):
    """从规格文本中提取功率值(kW)"""
    if not text:
        return None
    # 按优先级依次尝试各模式：
    # 1) 英文标记: P=xxkW, N=xxkW 等
    # 2) 中文"功率": 功率=xxkW, 功率:xxkW, 功率 xxkW
    # 3) 通用: xxkW（兜底）
    for pattern in [
        r'[NPnpnN]\s*[≈=:：]?\s*(\d+\.?\d*)\s*[kK][wW]',
        r'功率\s*[≈=:：]?\s*(\d+\.?\d*)\s*[kK][wW]',
        r'(\d+\.?\d*)\s*[kK][wW]',
    ]:
        m = re.search(pattern, text)
        if m:
            val = float(m.group(1))
            if val > 0:
                return val
    return None


def parse_working_info(quantity_val, remark=""):
    """解析几用几备信息

    支持格式："1用1备", "2用1备", "两用一备", "3 用 2 备", "5用1备"等
    """
    installed = int(float(quantity_val)) if quantity_val else 1

    if remark:
        # 中文数字归一化
        normalized = remark.replace("两", "2").replace("一", "1").replace("二", "2").replace("三", "3").replace("四", "4").replace("五", "5")
        m = re.search(r'(\d+)\s*用\s*(\d+)', normalized)
        if m:
            working = int(m.group(1))
            backup = int(m.group(2))
            # 检查是否有远期增加
            future_m = re.search(r'远期增加\s*(\d+)', normalized)
            extra = int(future_m.group(1)) if future_m else 0
            return max(working + backup + extra, installed), working

    return installed, installed


def _find_header_row(rows):
    """自动扫描所有行，定位真正的表头行（包含名称、规格等关键字段的行）

    返回 (header_row_index, header_cells)，如果未找到则返回 (-1, None)。
    策略：依次扫描每一行，尝试匹配关键列候选词，
    如果一行中同时匹配到"名称/设备名称"和"规格/型号"则认为找到表头。
    """
    name_candidates = ["名 称", "名称", "设备名称", "设备工艺名称"]
    spec_candidates = ["规 格", "规格", "型号", "参数", "设备主要参数", "设备参数", "型号及规格"]

    for i, row in enumerate(rows):
        cells = [str(c or "").strip() for c in row]
        # 跳过全空行
        if all(c == "" for c in cells):
            continue

        name_idx = _guess_column_index([cells], name_candidates)
        spec_idx = _guess_column_index([cells], spec_candidates)

        # 必须同时匹配到名称列和规格列才认为是表头
        if name_idx is not None and spec_idx is not None:
            return i, cells

    return -1, None


def parse_excel_file(file_path):
    """解析单个Excel文件，返回(建筑物名称, 设备列表)"""
    building_name = os.path.splitext(os.path.basename(file_path))[0].strip()
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.xlsx':
        rows = _parse_xlsx(file_path)
    elif ext == '.xls':
        rows = _parse_xls(file_path)
    else:
        return building_name, []

    if not rows or len(rows) < 2:
        return building_name, []

    # 自动定位表头行
    header_row_idx, headers = _find_header_row(rows)
    if header_row_idx < 0:
        return building_name, []

    data_rows = rows[header_row_idx + 1:]

    # 猜测关键列索引
    name_c = _guess_column_index(headers, ["名 称", "名称", "设备名称", "设备工艺名称"])
    spec_c = _guess_column_index(headers, ["规 格", "规格", "型号", "参数", "设备主要参数", "设备参数", "型号及规格"])
    qty_c = _guess_column_index(headers, ["数量", "台数"])
    rem_c = _guess_column_index(headers, ["备 注", "备注", "说明"])

    if name_c is None:
        return building_name, []

    equip_list = []
    for row in data_rows:
        if not row or all(str(c or "").strip() == "" for c in row):
            continue

        name = str(row[name_c]).strip() if name_c < len(row) else ""
        if not name:
            continue

        # 提取功率
        power = None
        if spec_c is not None and spec_c < len(row):
            power = parse_power_from_text(str(row[spec_c]).strip())
        if power is None or power <= 0:
            continue

        # 数量
        qty = 1
        if qty_c is not None and qty_c < len(row):
            try:
                qty = int(float(str(row[qty_c])))
            except (ValueError, TypeError):
                qty = 1

        # 备注中的几用几备
        remark = str(row[rem_c]).strip() if rem_c is not None and rem_c < len(row) else ""
        installed, working = parse_working_info(qty, remark)

        equip_list.append(Equipment(
            name=name,
            rated_power=power,
            installed_count=installed,
            working_count=working,
        ))

    return building_name, equip_list


def _parse_xlsx(file_path):
    """解析 .xlsx 文件"""
    import openpyxl
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active
    rows = [list(row) for row in ws.iter_rows(values_only=True)]
    wb.close()
    return rows


def _parse_xls(file_path):
    """解析 .xls 文件"""
    import xlrd
    wb = xlrd.open_workbook(file_path)
    ws = wb.sheet_by_index(0)
    return [[ws.cell_value(r, c) for c in range(ws.ncols)] for r in range(ws.nrows)]
