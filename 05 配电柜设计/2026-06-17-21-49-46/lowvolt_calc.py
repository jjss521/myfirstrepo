#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低压配电系统回路参数计算工具 v13
- 输入面板：1行紧凑布局，所有字段+按钮在一行
- 表格内联编辑：功率/回路用途直接输入，配电形式/运行方式下拉框，无需弹窗
- 电力监控信号：2行显示（上行"三相电流,有功电度"，下行"合/分,故障"）居中
- 单击表格行任意位置→回填输入面板参数
- 所有数据支持Ctrl+C复制
- 自动补备用：8E(默认100A)/8E/2(默认63A)
- 表格水平滚动：底部滚动条 + 鼠标滚轮(垂直) + Shift+滚轮(水平)
- 柜子代号统一带"="前缀
- 中国市政中南院李浩
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math, os, copy
from datetime import datetime

# ============================================================
# 数据
# ============================================================
CABLE_TABLE = [
    ("2.5",   20.8, 3.52,  13.5, 13.2),
    ("4",     27.2, 2.21,  14.8, 14.3),
    ("6",     34.4, 1.48,  16.1, 15.6),
    ("10",    48.0, 0.90,  19.6, 18.4),
    ("16",    66.4, 0.55,  22.4, 21.4),
    ("25+16", 84.0, 0.35,  26.2, 25.4),
    ("35+16", 100,  0.25,  28.8, 27.5),
    ("50+25", 128,  0.175, 33.4, 32.1),
    ("70+35", 160,  0.125, 38.8, 37.1),
    ("95+50", 196,  0.106, 44.1, 42.2),
    ("120+70",228,  0.087, 49.5, 47.7),
    ("150+70",260,  0.073, 54.1, 51.4),
    ("185+95",300,  0.062, 60.5, 57.7),
]
DEVICE_TABLE = [
    (0.06,0.12,"LC1D09", "LRD01",   0.18),(0.09,0.18,"LC1D09","LRD02",0.18),
    (0.12,0.24,"LC1D09", "LRD02",   0.18),(0.18,0.36,"LC1D09","LRD03",0.37),
    (0.25,0.5, "LC1D09", "LRD04",   0.37),(0.37,0.74,"LC1D09","LRD05",0.75),
    (0.55,1.1, "LC1D09", "LRD06",   1.5), (0.75,1.5, "LC1D09","LRD06",1.5),
    (1.1,2.2,  "LC1D09", "LRD07",   2.2), (1.5,3.0,  "LC1D09","LRD08",4.0),
    (2.2,4.4,  "LC1D09", "LRD10",   5.5), (3.0,6.0,  "LC1D09","LRD10",7.5),
    (4.0,8.0,  "LC1D12", "LRD14",   7.5), (5.5,11.0,"LC1D18","LRD16",7.5),
    (7.5,15.0, "LC1D18", "LRD21",   9.0), (11,22,   "LC1D25","LRD22",15),
    (15,30,    "LC1D32", "LRD32",   18.5),(18.5,37, "LC1D40A","LRD33",22),
    (22,44,    "LC1D50A","LRD3357", 30),  (30,60,   "LC1D65A","LRD3361",37),
    (37,74,    "LC1D80", "LR9D5372",45),  (45,90,   "LC1D95","LR9D5373",55),
    (55,110,   "LC1D115","LR9D5374",75),  (75,150,  "LC1D150","LR9D5377",90),
    (90,180,   "LC1D205","LR9D5377",110), (110,220, "LC1D245","LR9D5380",132),
    (132,264,  "LC1D300","LR9D5382",160), (160,320, "LC1F400","LR9D5384",200),
    (200,400,  "LC1F400","LR9D5385",250), (250,500, "LC1F500","LR9D5385",315),
    (315,630,  "LC1F630","LR9D5386",400),
]
SHELL_CURRENTS = [100,160,250,400,630,800,1250]
TRIP_RATINGS   = [16,20,25,32,40,50,63,80,100,125,160,200,250,320,400,500,630,800,1000,1250,1600,2000]
PIPE_MAP       = {2.5:20,4:20,6:25,10:25,16:32,25:32,35:40,70:50,50:40,95:65,120:65,150:80,185:80,240:100}
UNIT_SPACE_MAP = {100:"8E/2",160:"8E/2",250:"8E",400:"16E",630:"24E",800:"24E",1250:"32E"}
def unit_to_e(u: str) -> int:
    if u=="8E/2": return 4
    if u=="8E": return 8
    if u=="16E": return 16
    if u=="24E": return 24
    if u=="32E": return 32
    return 0
CT_RATIOS      = [20,30,50,75,100,150,200,300,400,500,600,800,1000,1500,2000]
RUN_MODES      = ["工频","变频"]
DIST_MODES     = ["MCC","PC"]
CORE_TYPES     = ["3","4","5","3+2","4+1"]
CABINET_TYPES  = ["抽屉柜","固定柜","GCS","GCK","MNS","GGD"]
CABINET_SIZES  = {"抽屉柜":"600×600×2200","固定柜":"800×600×2200",
                  "GCS":"800×800×2200","GCK":"1000×800×2200",
                  "MNS":"600×1000×2200","GGD":"1000×600×2200"}
MAX_E_PER_CAB = 72

# 布局常量
ROW_HEIGHT_NORMAL = 58
ROW_HEIGHT_MONITOR = 56
ROW_HEIGHT_OP = 52
COL_WIDTH = 180
LABEL_WIDTH = 170
PANEL_HEIGHT = 130
CONSOLE_HEIGHT = 120
MIN_WINDOW_W = 1280
MIN_WINDOW_H = 760

SUMMARY_ROWS = [
    ("开关柜代号",          False),
    ("开关柜尺寸(WxDH)mm",  False),
    ("单元空间",            False),
    ("回路用途",            True),   # 可编辑Entry
    ("设备功率Pe(kW)",      True),   # 可编辑Entry(数字)
    ("计算电流Ic(A)",       False),
    ("断路器壳架电流(A)",    False),
    ("脱扣器额定电流In(A)",  False),
    ("配电形式",            True),   # Combobox下拉
    ("运行方式",            True),   # Combobox下拉
    ("接触器",              False),
    ("热继电器",            False),
    ("变频器",              False),
    ("电流互感器变比",       False),
    ("电力监控信号",         False),  # v9: 2行Label显示
    ("线缆型号规格",         False),
    ("线缆编号",            False),
]
ROW_NAMES = [r[0] for r in SUMMARY_ROWS]
MERGE_ROWS = {0, 1}
MONITOR_ROW = 14  # 电力监控信号行号

# ============================================================
# 配色 (v9: 优化深色主题)
# ============================================================
C = {
    "bg":        "#0A0E14",
    "surface":   "#12171D",
    "surface2":  "#181E25",
    "border":    "#2A3038",
    "text":      "#E6EDF3",
    "dim":       "#7A828E",
    "accent":    "#58A6FF",
    "success":   "#3FB950",
    "warn":      "#D29922",
    "danger":    "#F85149",
    "header":    "#0F1724",
    "input_bg":       "#1A2028",
    "input_hl":       "#162238",
    "input_fg":       "#E6EDF3",
    "locked_bg":      "#14111F",
    "editable_bg":    "#152028",
    "edit_entry_bg":  "#1B2635",
    "ro_entry_bg":    "#12171D",
    "card_bg":        "#12171D",
    "spare_bg":       "#16162A",
    "sep":            "#1E2630",
    "monitor_bg":     "#0F1620",
}

# ============================================================
# 计算引擎
# ============================================================
def calc_ic(pe: float) -> float:
    return pe * 2

def select_shell(ic: float) -> int:
    for s in SHELL_CURRENTS:
        if s >= ic: return s
    return 2000

def select_trip(ic: float) -> int:
    for r in TRIP_RATINGS:
        if r >= ic * 1.1: return r
    return 2000

def select_ct(ic: float) -> int:
    for r in CT_RATIOS:
        if r >= ic * 1.1: return r
    return 2000

def select_cable_model(ic, core_type, length_m, vdrop_limit):
    ct = core_type.strip()
    lkm = length_m / 1000.0
    start = 8 if ic > 300 else 1
    min2 = (ic > 300)
    for i in range(start, len(CABLE_TABLE)):
        if CABLE_TABLE[i][1] <= 0: return (f"载流量缺失:{CABLE_TABLE[i][0]}", -1, 0, 0)
        if CABLE_TABLE[i][2] <= 0: return (f"压降系数缺失:{CABLE_TABLE[i][0]}", -1, 0, 0)
    for i in range(start + 1, len(CABLE_TABLE)):
        if CABLE_TABLE[i][2] > CABLE_TABLE[i-1][2]:
            return (f"压降系数异常:{CABLE_TABLE[i][0]}>{CABLE_TABLE[i-1][0]}", -1, 0, 0)
    best_n, best_idx, found = 11, -1, False
    for i in range(start, len(CABLE_TABLE)):
        n1 = math.ceil(ic / CABLE_TABLE[i][1])
        if min2 and n1 < 2: n1 = 2
        if n1 <= 10:
            found = True
            if n1 < best_n: best_n, best_idx = n1, i
    if not found: return ("载流量不满足(需>10根)", -1, 0, 0)
    fn, fi = best_n, best_idx
    vcf = CABLE_TABLE[fi][2]; nd = math.ceil((vcf * ic * lkm) / vdrop_limit)
    if fn < nd:
        f2 = False
        for i in range(fi + 1, len(CABLE_TABLE)):
            nd = math.ceil((CABLE_TABLE[i][2] * ic * lkm) / vdrop_limit)
            if fn >= nd: fi = i; f2 = True; break
        if not f2:
            for r in range(fn + 1, 11):
                for i in range(start, len(CABLE_TABLE)):
                    nd = math.ceil((CABLE_TABLE[i][2] * ic * lkm) / vdrop_limit)
                    if r >= nd: fi = i; fn = r; f2 = True; break
                if f2: break
        if not f2: return ("压降不满足(已达10根185+95)", -1, 0, 0)
    sp = CABLE_TABLE[fi][0].replace(" ", "")
    pp = sp.find("+")
    ms = float(sp[:pp]) if pp > 0 else float(sp)
    ns = float(sp[pp+1:]) if pp > 0 else ms
    cm = {"3": 3, "4": 4, "5": 5, "3+2": 5, "4+1": 5}
    tc = cm.get(ct)
    if tc is None: return ("芯数类型错误", -1, 0, 0)
    if ms <= 16: desc = f"{tc}x{int(ms)}"
    elif ct == "3+2": desc = f"3x{int(ms)}+2x{int(ns)}"
    elif ct == "4+1": desc = f"4x{int(ms)}+1x{int(ns)}"
    else: desc = f"{tc}x{int(ms)}"
    cable_str = desc if fn == 1 else f"{fn}({desc})"
    avd = (CABLE_TABLE[fi][2] * ic * lkm) / fn
    return (cable_str, fi, fn, round(avd, 3))

def select_device(pe, run_mode):
    c, t, v = "/", "/", "/"
    for row in DEVICE_TABLE:
        if pe <= row[0]:
            if run_mode == "变频":
                c = "/"; t = "/"; v = f"{row[4]}kW"
            else:
                c = row[2]; t = row[3]; v = "/"
            break
    return c, t, v

def compute_row(cid: str, purpose: str, pe: float,
                cabinet_code: str, run_mode: str, dist_mode: str,
                core_type: str, cable_len: int, vdrop_limit: float,
                cabinet_type: str,
                manual_shell: int = None, manual_trip: int = None) -> dict:
    is_spare = ("备用" in str(purpose))
    ic = calc_ic(pe)
    if is_spare:
        shell = manual_shell or 100
        trip = manual_trip or 63
    else:
        shell = select_shell(ic)
        trip = select_trip(ic)
    cm, cix, cn, vdp = select_cable_model(ic, core_type, cable_len, vdrop_limit)
    if cix >= 0:
        sk = CABLE_TABLE[cix][0].split("+")[0]
        pipe = PIPE_MAP.get(float(sk), 100)
    else:
        pipe = 0
    us = UNIT_SPACE_MAP.get(shell, "8E/2")
    if is_spare:
        contactor, thermal, vfd = "/", "/", "/"
        ct_ratio = "/"
        monitor_line1 = "/"
        monitor_line2 = "/"
        cable_full = "/"
    else:
        ct_ratio = select_ct(ic) if dist_mode == "MCC" else "/"
        contactor, thermal, vfd = select_device(pe, run_mode)
        # v9: 电力监控信号拆为2行
        if dist_mode == "MCC" and pe >= 2:
            monitor_line1 = "三相电流,有功电度"
            monitor_line2 = "合/分,故障"
        else:
            monitor_line1 = "/"
            monitor_line2 = "/"
        cable_full = f"YJV-0.6/1kV {cm}" if cm else "/"
    cab_size = CABINET_SIZES.get(cabinet_type, "600×600×2200")
    return {
        "开关柜代号": cabinet_code,
        "开关柜尺寸(WxDH)mm": cab_size,
        "单元空间": us,
        "回路用途": purpose,
        "设备功率Pe(kW)": round(pe, 1),
        "计算电流Ic(A)": round(ic, 1),
        "断路器壳架电流(A)": shell,
        "脱扣器额定电流In(A)": trip,
        "配电形式": dist_mode,
        "运行方式": run_mode,
        "接触器": contactor,
        "热继电器": thermal,
        "变频器": vfd,
        "电流互感器变比": ct_ratio,
        "电力监控信号": monitor_line1,       # v9: 上行
        "电力监控信号2": monitor_line2,       # v9: 下行（内部用）
        "线缆型号规格": cable_full,
        "线缆编号": cid,
        "_pe": pe, "_cab_type": cabinet_type, "_cab_size": cab_size,
        "_core_type": core_type, "_cable_len": cable_len,
        "_vdrop_limit": vdrop_limit, "_locked": False,
        "_is_spare": is_spare, "_unit_e": unit_to_e(us),
        "_pipe": pipe,
    }


# ============================================================
# 柜号管理器
# ============================================================
class CabinetTracker:
    def __init__(self, base_name):
        self.base_name = base_name
        self.cabinets = []
    def _next_code(self):
        return f"{self.base_name}-AN{len(self.cabinets)+1:02d}"
    def assign(self, unit_e):
        if not self.cabinets:
            code = self._next_code()
            self.cabinets.append({"code": code, "used_e": unit_e})
            return code, None
        last = self.cabinets[-1]
        remaining = MAX_E_PER_CAB - last["used_e"]
        if unit_e > remaining:
            if 0 < remaining < unit_e:
                if remaining >= 4: warn = f"柜子剩余{remaining}E空间，可补备用回路"
                else: warn = f"柜子剩余{remaining}E空间不足"
            else: warn = None
            code = self._next_code()
            self.cabinets.append({"code": code, "used_e": unit_e})
            return code, warn
        last["used_e"] += unit_e
        new_remaining = MAX_E_PER_CAB - last["used_e"]
        if new_remaining > 0 and new_remaining < 8:
            return last["code"], f"柜子剩余{new_remaining}E，可补备用"
        if new_remaining == 0:
            return last["code"], f"柜子已满，下一条将创建{self._next_code()}"
        return last["code"], None
    def reset(self, base_name=None):
        if base_name: self.base_name = base_name
        self.cabinets = []
    def get_cabinet_groups(self, circuits):
        groups = {}
        for i, d in enumerate(circuits):
            cc = d.get("开关柜代号", "")
            groups.setdefault(cc, []).append(i)
        return groups
    def get_remaining_space(self, circuits):
        groups = self.get_cabinet_groups(circuits)
        result = {}
        for cab_code, indices in groups.items():
            used = sum(circuits[i].get("_unit_e", 0) for i in indices)
            remaining = MAX_E_PER_CAB - used
            result[cab_code] = (remaining, len(indices))
        return result


# ============================================================
# 备用断路器编辑弹窗
# ============================================================
class SpareBreakerDialog(tk.Toplevel):
    def __init__(self, parent, default_shell=100, default_trip=63):
        super().__init__(parent)
        self.title("备用回路 — 断路器参数")
        self.geometry("440x300")
        self.configure(bg=C["bg"])
        self.transient(parent); self.grab_set()
        self.result = None
        tk.Label(self, text="备用回路 — 手动设置断路器参数",
                 font=("Microsoft YaHei", 12),
                 fg=C["accent"], bg=C["bg"]).pack(pady=(16, 8))
        f = tk.Frame(self, bg=C["bg"]); f.pack(pady=10)
        tk.Label(f, text="断路器壳架电流(A)：", font=("Microsoft YaHei", 11),
                 fg=C["text"], bg=C["bg"]).grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.shell_var = tk.StringVar(value=str(default_shell))
        self._cb1 = SimpleCombo(f, values=[str(s) for s in SHELL_CURRENTS],
                              default=str(default_shell),
                              width=16, font=("Microsoft YaHei", 11),
                              state="readonly")
        self._cb1.grid(row=0, column=1, padx=8, pady=8)
        tk.Label(f, text="脱扣器额定电流In(A)：", font=("Microsoft YaHei", 11),
                 fg=C["text"], bg=C["bg"]).grid(row=1, column=0, sticky="e", padx=8, pady=8)
        self.trip_var = tk.StringVar(value=str(default_trip))
        self._cb2 = SimpleCombo(f, values=[str(t) for t in TRIP_RATINGS],
                              default=str(default_trip),
                              width=16, font=("Microsoft YaHei", 11),
                              state="readonly")
        self._cb2.grid(row=1, column=1, padx=8, pady=8)
        bf = tk.Frame(self, bg=C["bg"]); bf.pack(pady=(16, 10))
        tk.Button(bf, text="确  定", font=("Microsoft YaHei", 11),
                  bg=C["success"], fg="white", relief="flat", width=14, height=1,
                  command=self._ok).pack(side=tk.LEFT, padx=10)
        tk.Button(bf, text="取  消", font=("Microsoft YaHei", 11),
                  bg=C["danger"], fg="white", relief="flat", width=14, height=1,
                  command=self.destroy).pack(side=tk.LEFT, padx=10)
    def _ok(self):
        self.result = (int(self._cb1._var.get()), int(self._cb2._var.get()))
        self.destroy()


# ============================================================
# 数据库弹窗
# ============================================================
class LibraryPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("数据库管理"); self.geometry("920x640")
        self.configure(bg=C["bg"]); self.resizable(True, True)
        self.transient(parent); self.grab_set()
        self._locked_cable = True; self._locked_device = True
        nb = ttk.Notebook(self); nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        t1 = tk.Frame(nb, bg=C["bg"]); nb.add(t1, text="  电缆载流量库  ")
        self._build_cable_tab(t1)
        t2 = tk.Frame(nb, bg=C["bg"]); nb.add(t2, text="  低压电器选型库  ")
        self._build_device_tab(t2)
    # ... (数据库方法保持与v8一致，省略以节省篇幅)
    def _build_cable_tab(self, parent):
        top = tk.Frame(parent, bg=C["bg"]); top.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(top, text="电缆载流量数据表", font=("Microsoft YaHei", 12, "bold"),
                 fg=C["text"], bg=C["bg"]).pack(side=tk.LEFT)
        self._lock_btn_c = tk.Button(top, text="🔒 已锁定", font=("Microsoft YaHei", 10),
                                     bg=C["danger"], fg="white", relief="flat",
                                     cursor="hand2", width=12,
                                     command=self._toggle_cable_lock)
        self._lock_btn_c.pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="+ 新增行", font=("Microsoft YaHei", 10),
                  bg=C["accent"], fg="white", relief="flat", cursor="hand2",
                  command=self._add_cable_row).pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="− 删除行", font=("Microsoft YaHei", 10),
                  bg=C["danger"], fg="white", relief="flat", cursor="hand2",
                  command=self._del_cable_row).pack(side=tk.RIGHT, padx=4)
        cols = ["规格", "载流量(A)", "压降系数", "外径(4+1)", "外径(3+2)"]
        self._tree_c = ttk.Treeview(parent, columns=cols, show="headings", height=14, selectmode="browse")
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self._tree_c.yview)
        self._tree_c.configure(yscrollcommand=vsb.set)
        for c in cols:
            self._tree_c.heading(c, text=c); self._tree_c.column(c, width=110, anchor="center")
        for row in CABLE_TABLE:
            self._tree_c.insert("", "end", values=row)
        self._tree_c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=4)
        self._tree_c.bind("<Double-1>", lambda e: self._edit_cable_cell())
        bf = tk.Frame(parent, bg=C["bg"]); bf.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(bf, text="💾 保存修改到程序", font=("Microsoft YaHei", 11, "bold"),
                  bg=C["success"], fg="white", relief="flat", cursor="hand2",
                  command=self._save_cable_changes).pack()
    def _build_device_tab(self, parent):
        top = tk.Frame(parent, bg=C["bg"]); top.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(top, text="低压电器选型数据表", font=("Microsoft YaHei", 12, "bold"),
                 fg=C["text"], bg=C["bg"]).pack(side=tk.LEFT)
        self._lock_btn_d = tk.Button(top, text="🔒 已锁定", font=("Microsoft YaHei", 10),
                                     bg=C["danger"], fg="white", relief="flat",
                                     cursor="hand2", width=12,
                                     command=self._toggle_device_lock)
        self._lock_btn_d.pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="+ 新增行", font=("Microsoft YaHei", 10),
                  bg=C["accent"], fg="white", relief="flat", cursor="hand2",
                  command=self._add_device_row).pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="− 删除行", font=("Microsoft YaHei", 10),
                  bg=C["danger"], fg="white", relief="flat", cursor="hand2",
                  command=self._del_device_row).pack(side=tk.RIGHT, padx=4)
        cols = ["功率上限kW", "电流上限A", "接触器", "热继电器", "变频器kW"]
        self._tree_d = ttk.Treeview(parent, columns=cols, show="headings", height=14, selectmode="browse")
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self._tree_d.yview)
        self._tree_d.configure(yscrollcommand=vsb.set)
        for c in cols:
            self._tree_d.heading(c, text=c); self._tree_d.column(c, width=110, anchor="center")
        for row in DEVICE_TABLE:
            self._tree_d.insert("", "end", values=row)
        self._tree_d.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=4)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=4)
        self._tree_d.bind("<Double-1>", lambda e: self._edit_device_cell())
        bf = tk.Frame(parent, bg=C["bg"]); bf.pack(fill=tk.X, padx=10, pady=8)
        tk.Button(bf, text="💾 保存修改到程序", font=("Microsoft YaHei", 11, "bold"),
                  bg=C["success"], fg="white", relief="flat", cursor="hand2",
                  command=self._save_device_changes).pack()
    def _toggle_cable_lock(self):
        self._locked_cable = not self._locked_cable
        self._lock_btn_c.configure(
            text="🔒 已锁定" if self._locked_cable else "🔓 已解锁",
            bg=C["danger"] if self._locked_cable else C["success"])
    def _toggle_device_lock(self):
        self._locked_device = not self._locked_device
        self._lock_btn_d.configure(
            text="🔒 已锁定" if self._locked_device else "🔓 已解锁",
            bg=C["danger"] if self._locked_device else C["success"])
    def _edit_cable_cell(self):
        if self._locked_cable:
            messagebox.showinfo("提示", "数据库已锁定，请先解锁", parent=self); return
        self._edit_tree_cell(self._tree_c)

    def _edit_device_cell(self):
        if self._locked_device:
            messagebox.showinfo("提示", "数据库已锁定，请先解锁", parent=self); return
        self._edit_tree_cell(self._tree_d)

    def _edit_tree_cell(self, tree):
        """通用单元格编辑弹窗"""
        sel = tree.selection()
        if not sel: return
        item = sel[0]; vals = list(tree.item(item, "values"))
        col = tree.identify_column(
            tree.winfo_pointerx() - tree.winfo_rootx() + 10)
        ci = int(col.replace("#", "")) - 1
        if ci < 0: return
        pop = tk.Toplevel(self); pop.title("编辑单元格"); pop.geometry("300x140")
        pop.transient(self); pop.grab_set(); pop.configure(bg=C["bg"])
        tk.Label(pop, text=f"编辑 [{tree.heading(f'#{ci+1}')['text']}]",
                 fg=C["text"], bg=C["bg"], font=("Microsoft YaHei", 11)).pack(pady=10)
        sv = tk.StringVar(value=str(vals[ci]))
        e = tk.Entry(pop, textvariable=sv, font=("Microsoft YaHei", 11), bg=C["input_bg"],
                     fg=C["input_fg"], insertbackground="white", width=24)
        e.pack(pady=6); e.focus()
        def do_save():
            vals[ci] = sv.get()
            tree.item(item, values=tuple(vals))
            pop.destroy()
        e.bind("<Return>", lambda ev: do_save())
        tk.Button(pop, text="确定", command=do_save, bg=C["accent"], fg="white",
                  relief="flat", width=12).pack(pady=6)
    def _add_cable_row(self):
        if self._locked_cable: messagebox.showinfo("提示", "请先解锁数据库", parent=self); return
        self._tree_c.insert("", "end", values=("新规格", 0, 0, 0, 0))
    def _del_cable_row(self):
        if self._locked_cable: messagebox.showinfo("提示", "请先解锁数据库", parent=self); return
        sel = self._tree_c.selection()
        if sel: self._tree_c.delete(sel[0])
    def _add_device_row(self):
        if self._locked_device: messagebox.showinfo("提示", "请先解锁数据库", parent=self); return
        self._tree_d.insert("", "end", values=(0, 0, "新接触器", "新热继", 0))
    def _del_device_row(self):
        if self._locked_device: messagebox.showinfo("提示", "请先解锁数据库", parent=self); return
        sel = self._tree_d.selection()
        if sel: self._tree_d.delete(sel[0])
    def _save_cable_changes(self):
        global CABLE_TABLE
        new = []
        errors = []
        for item in self._tree_c.get_children():
            v = self._tree_c.item(item, "values")
            try:
                new.append((str(v[0]), float(v[1]), float(v[2]), float(v[3]), float(v[4])))
            except (ValueError, TypeError) as e:
                errors.append(f"  {v[0]}: {e}")
        if errors:
            messagebox.showerror("数据格式错误",
                f"以下行存在格式错误:\n{''.join(errors)}\n请修正后再保存", parent=self)
            return
        if not new:
            messagebox.showwarning("无数据", "表格为空", parent=self)
            return
        if not messagebox.askyesno("确认更新",
                f"将用 {len(new)} 条数据覆盖当前电缆载流量库，\n所有后续计算将使用新数据。确认？",
                parent=self):
            return
        CABLE_TABLE = new
        messagebox.showinfo("完成", f"电缆载流量库已更新 ({len(new)} 条)", parent=self)
    def _save_device_changes(self):
        global DEVICE_TABLE
        new = []
        errors = []
        for item in self._tree_d.get_children():
            v = self._tree_d.item(item, "values")
            try:
                new.append((float(v[0]), float(v[1]), str(v[2]), str(v[3]), float(v[4])))
            except (ValueError, TypeError) as e:
                errors.append(f"  {v[2]}: {e}")
        if errors:
            messagebox.showerror("数据格式错误",
                f"以下行存在格式错误:\n{''.join(errors)}\n请修正后再保存", parent=self)
            return
        if not new:
            messagebox.showwarning("无数据", "表格为空", parent=self)
            return
        if not messagebox.askyesno("确认更新",
                f"将用 {len(new)} 条数据覆盖当前低压电器选型库，\n所有后续计算将使用新数据。确认？",
                parent=self):
            return
        DEVICE_TABLE = new
        messagebox.showinfo("完成", f"低压电器选型库已更新 ({len(new)} 条)", parent=self)


# ============================================================
# 汇总表格 (v9: 内联编辑 + 监控信号2行 + 单击回填)
# ============================================================
class SummaryTable(tk.Frame):
    def __init__(self, parent, on_row_click, on_cell_edit, on_change):
        super().__init__(parent, bg=C["bg"])
        self.on_row_click = on_row_click      # 单击行→回填参数
        self.on_cell_edit = on_cell_edit      # 内联编辑→重算回路
        self.on_change = on_change            # 数据变化通知
        self.columns_data = []
        self._live_widgets = {}  # (ri, ci) → widget 引用（用于内联编辑控件）
        hsb = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        vsb = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0,
                                xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        hsb.config(command=self.canvas.xview)
        vsb.config(command=self.canvas.yview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.inner = tk.Frame(self.canvas, bg=C["bg"])
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(self._win, width=e.width))
        # 鼠标滚轮：垂直滚动
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        # Shift+滚轮：水平滚动
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self._build_row_labels()

    def _on_mousewheel(self, event):
        """鼠标滚轮 → 垂直滚动"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        """Shift+滚轮 → 水平滚动"""
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_row_labels(self):
        for ri, (name, editable) in enumerate(SUMMARY_ROWS):
            h = ROW_HEIGHT_MONITOR if ri == MONITOR_ROW else ROW_HEIGHT_NORMAL
            fc = tk.Frame(self.inner, width=LABEL_WIDTH, height=h,
                          bg=C["header"] if ri in MERGE_ROWS else (
                          C["surface"] if ri % 2 == 0 else C["surface2"]))
            fc.grid(row=ri, column=0, sticky="nsew")
            fc.grid_propagate(False)
            fw = "bold" if ri in MERGE_ROWS else "normal"
            lbl = tk.Label(fc, text=name, font=("Microsoft YaHei", 10, fw),
                           fg="#FFFFFF" if ri in MERGE_ROWS else C["text"],
                           bg=fc.cget("bg"), anchor="w", padx=10)
            lbl.pack(fill=tk.BOTH, expand=True)
        self.inner.grid_columnconfigure(0, minsize=LABEL_WIDTH)

    def add_column(self, data):
        self.columns_data.append(data)
        self._full_render()
        self.on_change()

    def update_column(self, ci, data):
        if ci - 1 < len(self.columns_data):
            self.columns_data[ci - 1] = data
        self._full_render()
        self.on_change()

    def remove_column(self, ci):
        if ci - 1 < len(self.columns_data):
            self.columns_data.pop(ci - 1)
            self._full_render()
            self.on_change()

    def _full_render(self):
        # 清除旧控件
        self._live_widgets.clear()
        for w in list(self.inner.grid_slaves()):
            c = w.grid_info().get("column", 0)
            if c > 0:
                w.destroy()
        n = len(self.columns_data)
        if n == 0: return
        tracker = CabinetTracker("")
        groups = tracker.get_cabinet_groups(self.columns_data)
        for ri, (name, editable) in enumerate(SUMMARY_ROWS):
            if ri in MERGE_ROWS:
                self._render_merge_row(ri, name, groups)
            elif ri == MONITOR_ROW:
                self._render_monitor_row(ri)
            elif editable:
                self._render_editable_row(ri, name)
            else:
                self._render_normal_row(ri)
        # 操作行
        op_row = len(SUMMARY_ROWS)
        for ci, d in enumerate(self.columns_data, 1):
            locked = d.get("_locked", False)
            is_spare = d.get("_is_spare", False)
            op_frame = tk.Frame(self.inner, width=COL_WIDTH, height=ROW_HEIGHT_OP, bg=C["bg"])
            op_frame.grid(row=op_row, column=ci, sticky="nsew", pady=(4, 0))
            op_frame.grid_propagate(False)
            lock_txt = "🔒" if locked else "🔓"
            lock_bg = C["danger"] if locked else C["warn"]
            lb = tk.Label(op_frame, text=lock_txt, font=("Arial", 11),
                          bg=lock_bg, fg="white", cursor="hand2", width=3, relief="flat")
            lb.pack(side=tk.LEFT, padx=3)
            lb.bind("<Button-1>", lambda e, c=ci: self._toggle_lock(c))
            if is_spare:
                eb = tk.Label(op_frame, text="⚡", font=("Arial", 11),
                              bg=C["accent"], fg="white", cursor="hand2", width=3, relief="flat")
                eb.pack(side=tk.LEFT, padx=3)
                eb.bind("<Button-1>", lambda e, c=ci: self._edit_spare_breaker(c))
            db = tk.Label(op_frame, text="✕", font=("Arial", 12, "bold"),
                          bg=C["danger"], fg="white", cursor="hand2", width=3, relief="flat")
            db.pack(side=tk.LEFT, padx=3)
            db.bind("<Button-1>", lambda e, c=ci: self._del_column(ci))

    def _render_merge_row(self, ri, row_name, groups):
        col = 1
        for cab_code, indices in groups.items():
            if not indices: continue
            span = len(indices)
            val = self.columns_data[indices[0]].get(row_name, "")
            fc = tk.Frame(self.inner, width=COL_WIDTH * span, height=ROW_HEIGHT_NORMAL,
                          bg="#0A1628")
            fc.grid(row=ri, column=col, columnspan=span, sticky="nsew")
            fc.grid_propagate(False)
            entry = tk.Entry(fc, font=("Microsoft YaHei", 10, "bold"),
                             fg=C["accent"], bg="#0A1628",
                             readonlybackground="#0A1628",
                             relief="flat", justify="center",
                             insertbackground=C["accent"])
            entry.insert(0, str(val))
            entry.configure(state="readonly")
            entry.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            entry.bind("<Button-1>", lambda e: e.widget.selection_range(0, tk.END))
            first_ci = indices[0] + 1
            # v9: 单击（非双击）也触发回调
            entry.bind("<Button-1>", lambda e, c=first_ci: self._handle_normal_click(e, c), add="+")
            col += span

    def _render_normal_row(self, ri):
        for ci, d in enumerate(self.columns_data, 1):
            locked = d.get("_locked", False)
            is_spare = d.get("_is_spare", False)
            val = d.get(ROW_NAMES[ri], "")
            row_bg = C["spare_bg"] if is_spare else (
                     C["locked_bg"] if locked else (
                     C["surface"] if ri % 2 == 0 else C["surface2"]))
            h = ROW_HEIGHT_MONITOR if ri == MONITOR_ROW else ROW_HEIGHT_NORMAL
            fc = tk.Frame(self.inner, width=COL_WIDTH, height=h, bg=row_bg)
            fc.grid(row=ri, column=ci, sticky="nsew")
            fc.grid_propagate(False)
            is_calc_row = (5 <= ri <= 15)
            if is_spare: txt_color = C["dim"]
            elif locked: txt_color = C["dim"]
            elif is_calc_row: txt_color = C["success"]
            else: txt_color = C["text"]
            display_val = f"⚡ {val}" if (is_spare and ri == 16) else val
            entry = tk.Entry(fc, font=("Microsoft YaHei", 10),
                             fg=txt_color, bg=row_bg,
                             readonlybackground=row_bg,
                             relief="flat", justify="center",
                             insertbackground=txt_color)
            entry.insert(0, str(display_val))
            entry.configure(state="readonly")
            entry.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            entry.bind("<Button-1>", lambda e: e.widget.selection_range(0, tk.END))
            # v9: 单击 → 选中行回填参数（双击也保留）
            if not locked:
                entry.bind("<Button-1>", lambda e, c=ci: self._handle_normal_click(e, c), add="+")

    def _render_editable_row(self, ri, row_name):
        """v9: 内联编辑 - 下拉框或可直接输入Entry，不再弹窗"""
        is_combo = (ri == 8 or ri == 9)  # 配电形式/运行方式→Combobox
        combo_options = DIST_MODES if ri == 8 else RUN_MODES
        for ci, d in enumerate(self.columns_data, 1):
            locked = d.get("_locked", False)
            is_spare = d.get("_is_spare", False)
            val = d.get(row_name, "")
            row_bg = C["locked_bg"] if locked else C["editable_bg"]
            if is_spare: row_bg = C["spare_bg"]
            fc = tk.Frame(self.inner, width=COL_WIDTH, height=ROW_HEIGHT_NORMAL, bg=row_bg)
            fc.grid(row=ri, column=ci, sticky="nsew")
            fc.grid_propagate(False)
            if locked or is_spare:
                # 只读Entry（锁定/备用）
                txt_color = C["dim"]
                entry = tk.Entry(fc, font=("Microsoft YaHei", 10),
                                 fg=txt_color, bg=row_bg,
                                 readonlybackground=row_bg,
                                 relief="flat", justify="center")
                entry.insert(0, str(val))
                entry.configure(state="readonly")
                entry.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
                entry.bind("<Button-1>", lambda e: e.widget.selection_range(0, tk.END))
            elif is_combo:
                # v11: 使用 SimpleCombo
                cb = SimpleCombo(fc, values=combo_options, default=str(val),
                                     width=14, font=("Microsoft YaHei", 10),
                                     bg=row_bg, fg=C["text"],
                                     highlightbackground=C["border"],
                                     highlightcolor=C["accent"],
                                     justify="center", state="readonly")
                cb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
                cb.bind("<<ComboboxSelected>>", lambda e, r=ri, c=ci: self._on_inline_combo_change(r, c, cb._var))
                self._live_widgets[(ri, ci)] = cb._var
            else:
                # 可编辑Entry（回路用途/功率）
                txt_color = C["warn"]
                sv = tk.StringVar(value=str(val))
                entry = tk.Entry(fc, textvariable=sv, font=("Microsoft YaHei", 10),
                                 fg=txt_color, bg=C["edit_entry_bg"],
                                 insertbackground=C["accent"],
                                 relief="solid", justify="center",
                                 highlightthickness=1, highlightbackground=C["border"])
                entry.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
                entry.bind("<Return>", lambda e, r=ri, c=ci, sv=sv: self._on_inline_entry_commit(r, c, sv))
                entry.bind("<FocusOut>", lambda e, r=ri, c=ci, sv=sv: self._on_inline_entry_commit(r, c, sv))
                self._live_widgets[(ri, ci)] = sv

    def _render_monitor_row(self, ri):
        """v9: 电力监控信号2行显示 - 使用Text支持复制"""
        for ci, d in enumerate(self.columns_data, 1):
            locked = d.get("_locked", False)
            is_spare = d.get("_is_spare", False)
            line1 = str(d.get("电力监控信号", "/"))
            line2 = str(d.get("电力监控信号2", "/"))
            full_text = f"{line1}\n{line2}" if line2 and line2 != "/" else line1
            row_bg = C["spare_bg"] if is_spare else C["monitor_bg"]
            if locked: row_bg = C["locked_bg"]
            fc = tk.Frame(self.inner, width=COL_WIDTH, height=ROW_HEIGHT_MONITOR, bg=row_bg)
            fc.grid(row=ri, column=ci, sticky="nsew")
            fc.grid_propagate(False)
            txt_color = C["dim"] if (locked or is_spare) else C["success"]
            # 使用Text控件支持多行显示+复制，文字居中
            txt = tk.Text(fc, font=("Microsoft YaHei", 10),
                          fg=txt_color, bg=row_bg,
                          relief="flat", wrap="word",
                          height=2, width=18, padx=4, pady=0)
            txt.insert("1.0", full_text)
            txt.tag_configure("center", justify="center")
            txt.tag_add("center", "1.0", "end")
            txt.configure(state="disabled")  # 只读但仍可选择复制
            txt.pack(fill=tk.BOTH, expand=True, padx=2, pady=1)
            # 单击选择文本并回填
            txt.bind("<Button-1>", lambda e: e.widget.selection_range("1.0", "end") if e.widget.cget("state")=="disabled" else None)
            if not locked:
                txt.bind("<Button-1>", lambda e, c=ci: self.on_row_click(c), add="+")

    def _handle_normal_click(self, event, ci):
        """处理正常单元格的单击：先允许文本选择，再触发回填"""
        # 如果点击的是Entry，先让Entry处理选择
        if isinstance(event.widget, tk.Entry):
            event.widget.selection_range(0, tk.END)
        # 触发回填
        self.on_row_click(ci)

    def _on_inline_combo_change(self, ri, ci, sv):
        """下拉框选择变化→直接更新数据并重算"""
        if ci - 1 >= len(self.columns_data): return
        new_val = sv.get()
        key = ROW_NAMES[ri]
        old_val = self.columns_data[ci - 1].get(key, "")
        if str(new_val) == str(old_val): return  # 无变化
        self.columns_data[ci - 1][key] = new_val
        # 重算整个回路
        self.on_cell_edit(ci)

    def _on_inline_entry_commit(self, ri, ci, sv):
        """Entry输入确认→直接更新数据并重算"""
        if ci - 1 >= len(self.columns_data): return
        new_val = sv.get().strip()
        if not new_val: return
        key = ROW_NAMES[ri]
        old_val = self.columns_data[ci - 1].get(key, "")
        if str(new_val) == str(old_val): return
        # 功率字段需同时更新 _pe
        if ri == 4:  # 设备功率Pe(kW)
            try:
                pe_val = float(new_val)
                self.columns_data[ci - 1]["_pe"] = pe_val
                self.columns_data[ci - 1][key] = round(pe_val, 1)
            except ValueError:
                messagebox.showwarning("格式错误", "功率请输入数字")
                sv.set(str(old_val))
                return
        else:
            self.columns_data[ci - 1][key] = new_val
        # 重算整个回路
        self.on_cell_edit(ci)

    def _edit_spare_breaker(self, ci):
        if ci - 1 >= len(self.columns_data): return
        d = self.columns_data[ci - 1]
        if not d.get("_is_spare"): return
        current_shell = d.get("断路器壳架电流(A)", 100)
        current_trip = d.get("脱扣器额定电流In(A)", 63)
        dlg = SpareBreakerDialog(self.winfo_toplevel(),
                                default_shell=int(current_shell),
                                default_trip=int(current_trip))
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result:
            d["断路器壳架电流(A)"] = dlg.result[0]
            d["脱扣器额定电流In(A)"] = dlg.result[1]
            us = UNIT_SPACE_MAP.get(dlg.result[0], "8E/2")
            d["单元空间"] = us
            d["_unit_e"] = unit_to_e(us)
            self._full_render()
            self.on_change()

    def _toggle_lock(self, ci):
        if ci - 1 < len(self.columns_data):
            d = self.columns_data[ci - 1]
            d["_locked"] = not d.get("_locked", False)
            self._full_render()
            self.on_change()

    def _del_column(self, ci):
        if ci - 1 >= len(self.columns_data): return
        d = self.columns_data[ci - 1]
        if d.get("_locked", False):
            messagebox.showwarning("已锁定", f"回路 {d.get('线缆编号','?')} 已锁定")
            return
        name = d.get("线缆编号", "?")
        if messagebox.askyesno("确认删除", f"删除回路 {name}？"):
            self.columns_data.pop(ci - 1)
            self._full_rebuild()

    def lock_all(self):
        for d in self.columns_data: d["_locked"] = True
        self._full_render()

    def unlock_all(self):
        for d in self.columns_data: d["_locked"] = False
        self._full_render()

    def _full_rebuild(self):
        self._full_render()
        self.on_change()

    def clear_all(self):
        for w in list(self.inner.grid_slaves()):
            if w.grid_info().get("column", 0) > 0:
                w.destroy()
        self._live_widgets.clear()
        self.columns_data = []

    def get_col_data(self, ci):
        if ci - 1 < len(self.columns_data): return self.columns_data[ci - 1]
        return None

    def col_count(self):
        return len(self.columns_data)

    def set_all_data(self, data_list):
        self.columns_data = data_list
        self._full_render()
        self.on_change()


# ============================================================
# 输入面板 (v9: 1行紧凑布局)
# ============================================================

# ============================================================
# 自定义下拉框（看起来像普通 Entry）
# ============================================================
class SimpleCombo(tk.Frame):
    """v12极简下拉框：只读Entry+小箭头，点击弹出白色Listbox（确保选项可见）"""
    def __init__(self, parent, values=None, default="", width=8, font=("Microsoft YaHei", 10),
                 bg="#1A2028", fg="#E6EDF3", relief="flat",
                 highlightthickness=1, highlightbackground="#2A3038", highlightcolor="#58A6FF",
                 justify="center", state="normal"):
        super().__init__(parent, bg=parent.cget("bg"),
                         relief=relief,
                         highlightthickness=highlightthickness,
                         highlightbackground=highlightbackground,
                         highlightcolor=highlightcolor)
        self._values = values or []
        self._var = tk.StringVar(value=default)
        self._state = state
        self._font = font
        self._bg = bg
        self._fg = fg

        # 只读 Entry — 看起来和普通输入框完全一样
        self.entry = tk.Entry(self, textvariable=self._var, width=width,
                              font=font, bg=bg, fg=fg,
                              readonlybackground=bg,
                              insertbackground="#58A6FF",
                              relief="flat", highlightthickness=0,
                              justify=justify,
                              state="readonly")
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=4)

        # 小型 ▾ 箭头（不突兀）
        self.arrow = tk.Label(self, text="▾", font=("Microsoft YaHei", 7),
                              bg=bg, fg=fg, padx=2, cursor="hand2")
        self.arrow.pack(side=tk.RIGHT, padx=(0, 2))

        # 绑定点击 → 弹出 Listbox
        self.entry.bind("<Button-1>", lambda e: self._popup())
        self.arrow.bind("<Button-1>", lambda e: self._popup())

    def _popup(self):
        if not self._values:
            return
        popup = tk.Toplevel(self)
        popup.wm_overrideredirect(True)
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        popup.wm_geometry(f"+{x}+{y}")

        # ★ 白色背景+黑色文字 Listbox — 确保在任何系统上都清晰可见
        lb = tk.Listbox(popup,
                        font=self._font,
                        bg="white", fg="black",
                        selectbackground="#58A6FF", selectforeground="white",
                        relief="solid", borderwidth=1,
                        height=min(len(self._values), 8),
                        width=(self.entry.cget("width") or 10))
        for v in self._values:
            lb.insert(tk.END, str(v))
        lb.pack()

        def on_select(event):
            sel = lb.curselection()
            if sel:
                self._var.set(lb.get(sel[0]))
            popup.destroy()
            self.event_generate("<<ComboboxSelected>>")

        lb.bind("<ButtonRelease-1>", on_select)
        lb.bind("<Return>", on_select)
        lb.bind("<Escape>", lambda e: popup.destroy())
        popup.bind("<FocusOut>", lambda e: popup.destroy())
        lb.focus_set()

    def get(self):
        return self._var.get()

    def configure(self, **kwargs):
        if "state" in kwargs:
            self._state = kwargs["state"]
            self.entry.configure(state=kwargs["state"])
            del kwargs["state"]
        if "values" in kwargs:
            self._values = kwargs["values"]
            del kwargs["values"]
        super().configure(**kwargs)

class InputPanel(tk.Frame):
    def __init__(self, parent, on_calc):
        super().__init__(parent, bg=C["card_bg"], height=PANEL_HEIGHT)
        self.pack_propagate(False)
        self.on_calc = on_calc
        self.fields = {}
        self._edit_ci = None
        self._build()

    def _build(self):
        card = tk.Frame(self, bg=C["card_bg"], bd=0,
                        highlightthickness=1, highlightbackground=C["border"])
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 标题行 - 标签字体改为9号
        title_frame = tk.Frame(card, bg=C["card_bg"])
        title_frame.pack(fill=tk.X, padx=14, pady=(6, 2))

        self._mode_lbl = tk.Label(title_frame, text="⚡ 新增回路",
                                   font=("Microsoft YaHei", 11, "bold"),
                                   fg=C["accent"], bg=C["card_bg"])
        self._mode_lbl.pack(side=tk.LEFT)

        # === 核心：1行10个字段 + 按钮 ===
        row_frame = tk.Frame(card, bg=C["card_bg"])
        row_frame.pack(fill=tk.X, padx=10, pady=(2, 8))

        # 字段定义：(标签, key, 默认值, 类型, 选项, 宽度, 必填)
        all_fields = [
            ("柜代号", "cabinet_base", "=X",    "entry", None,          8,  True),
            ("回路编号","cid",         "L1",    "entry", None,          8,  True),
            ("回路用途","purpose",     "1#进线","entry", None,         11,  True),
            ("功率kW",  "pe_kw",       "150",   "entry", None,          7,  True),
            ("运行方式","run_mode",    "变频",  "combo", RUN_MODES,     7,  False),
            ("配电形式","dist_mode",   "MCC",   "combo", DIST_MODES,    7,  False),
            ("柜型",    "cabinet_type","抽屉柜","combo", CABINET_TYPES, 8,  False),
            ("芯数",    "core_type",   "4+1",   "combo", CORE_TYPES,    6,  False),
            ("长度m",   "cable_len",   "100",   "entry_int", None,      6,  False),
            ("压降%",   "vdrop_limit", "3.0",   "entry", None,          6,  False),
        ]

        for label, key, default, ftype, options, w, is_required in all_fields:
            col_group = tk.Frame(row_frame, bg=C["card_bg"])
            col_group.pack(side=tk.LEFT, padx=4, pady=2)

            # 标签 - 字体改为9号，与输入数据字高接近
            label_text = f"＊{label}" if is_required else label
            label_fg = C["warn"] if is_required else C["dim"]
            tk.Label(col_group, text=label_text, font=("Microsoft YaHei", 9),
                     fg=label_fg, bg=C["card_bg"]).pack(anchor="w", padx=1)

            entry_bg = C["input_hl"] if is_required else C["input_bg"]

            if ftype == "entry" or ftype == "entry_int":
                sv = tk.StringVar(value=default)
                e = tk.Entry(col_group, textvariable=sv, width=w,
                             font=("Microsoft YaHei", 10),
                             bg=entry_bg, fg=C["input_fg"],
                             insertbackground=C["accent"], relief="flat",
                             highlightthickness=1, highlightbackground=C["border"],
                             highlightcolor=C["accent"],
                             justify="center")
                e.pack(ipady=4)
                e.bind("<Return>", lambda ev: self._trigger())
            elif ftype == "combo":
                # v11: 使用 SimpleCombo（看起来像普通 Entry）
                cb = SimpleCombo(col_group, values=options, default=default,
                                     width=w, font=("Microsoft YaHei", 10),
                                     bg=entry_bg, fg=C["input_fg"],
                                     highlightbackground=C["border"],
                                     highlightcolor=C["accent"],
                                     justify="center", state="readonly")
                cb.pack(ipady=0)
                self.fields[key] = cb._var
                continue
            self.fields[key] = sv

        # 按钮组
        btn_group = tk.Frame(row_frame, bg=C["card_bg"])
        btn_group.pack(side=tk.LEFT, padx=(8, 0), pady=(16, 0))

        self._calc_btn = tk.Button(btn_group, text="▶ 计算并添加",
                                    font=("Microsoft YaHei", 10, "bold"),
                                    bg=C["success"], fg="white", relief="flat",
                                    cursor="hand2", padx=14, pady=6,
                                    command=self._trigger)
        self._calc_btn.pack(side=tk.LEFT, padx=2)

        self._cancel_btn = tk.Button(btn_group, text="取消编辑",
                                      font=("Microsoft YaHei", 9),
                                      bg=C["danger"], fg="white", relief="flat",
                                      cursor="hand2", padx=8, pady=6,
                                      command=self.cancel_edit)

    def _trigger(self):
        self.on_calc(self._edit_ci)

    def set_edit_mode(self, ci, data):
        self._edit_ci = ci
        self._mode_lbl.configure(
            text=f"✎ 编辑回路 {data.get('线缆编号','?')}", fg=C["warn"])
        self._calc_btn.configure(text="▶ 保存修改", bg=C["warn"])
        self._cancel_btn.pack(side=tk.LEFT, padx=2)
        cab_code = data.get("开关柜代号", "")
        if "-AN" in cab_code:
            base = cab_code[:cab_code.rfind("-AN")]
        else:
            base = cab_code
        self.fields["cabinet_base"].set(base)
        self.fields["cid"].set(data.get("线缆编号", ""))
        self.fields["purpose"].set(data.get("回路用途", ""))
        self.fields["cabinet_type"].set(data.get("_cab_type", "抽屉柜"))
        self.fields["pe_kw"].set(str(data.get("_pe", data.get("设备功率Pe(kW)", 30))))
        self.fields["run_mode"].set(data.get("运行方式", "变频"))
        self.fields["dist_mode"].set(data.get("配电形式", "MCC"))
        self.fields["core_type"].set(data.get("_core_type", "4+1"))
        self.fields["cable_len"].set(str(data.get("_cable_len", 100)))
        self.fields["vdrop_limit"].set(str(data.get("_vdrop_limit", 3.0)))

    def set_new_mode(self):
        self._edit_ci = None
        self._mode_lbl.configure(text="⚡ 新增回路", fg=C["accent"])
        self._calc_btn.configure(text="▶ 计算并添加", bg=C["success"])
        self._cancel_btn.pack_forget()

    def cancel_edit(self):
        self.set_new_mode()

    def read_values(self):
        try:
            pe_kw = float(self.fields["pe_kw"].get().strip() or 0)
            if pe_kw <= 0:
                messagebox.showerror("输入错误", "功率Pe必须大于0 kW")
                return None
            cable_len = int(float(self.fields["cable_len"].get().strip() or 100))
            if cable_len <= 0:
                messagebox.showerror("输入错误", "电缆长度必须大于0 m")
                return None
            vdrop_limit = float(self.fields["vdrop_limit"].get().strip() or 3)
            if vdrop_limit <= 0 or vdrop_limit > 20:
                messagebox.showerror("输入错误", "压降限值应在0~20%之间")
                return None
            return {
                "cabinet_base": self.fields["cabinet_base"].get().strip() or "=X",
                "cid": self.fields["cid"].get().strip(),
                "purpose": self.fields["purpose"].get().strip(),
                "pe_kw": pe_kw,
                "run_mode": self.fields["run_mode"].get().strip(),
                "dist_mode": self.fields["dist_mode"].get().strip(),
                "core_type": self.fields["core_type"].get().strip(),
                "cable_len": cable_len,
                "vdrop_limit": vdrop_limit,
                "cabinet_type": self.fields["cabinet_type"].get().strip(),
            }
        except ValueError as e:
            messagebox.showerror("输入错误", f"数值格式错误: {e}")
            return None


# ============================================================
# 自动补备用弹窗
# ============================================================
class AutoSpareDialog(tk.Toplevel):
    def __init__(self, parent, remaining_info):
        super().__init__(parent)
        self.title("自动补充备用回路")
        self.geometry("580x440")
        self.configure(bg=C["bg"])
        self.transient(parent); self.grab_set()
        self.result = []
        self.remaining_info = remaining_info
        tk.Label(self, text="自动补充备用回路",
                 font=("Microsoft YaHei", 13, "bold"),
                 fg=C["accent"], bg=C["bg"]).pack(pady=(16, 6))
        tk.Label(self, text="以下柜子有剩余空间，将自动添加备用回路：",
                 font=("Microsoft YaHei", 10),
                 fg=C["dim"], bg=C["bg"]).pack(pady=(0, 10))
        list_frame = tk.Frame(self, bg=C["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)
        self._checks = []
        self._trip_vars = []
        for i, (cab_code, rem_e, spare_type, default_trip) in enumerate(remaining_info):
            row_f = tk.Frame(list_frame, bg=C["surface"], bd=0,
                             highlightthickness=1, highlightbackground=C["border"])
            row_f.pack(fill=tk.X, pady=4, ipady=6)
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(row_f, text=f"  {cab_code}  剩余{rem_e}E",
                                variable=var,
                                font=("Microsoft YaHei", 11, "bold"),
                                fg=C["accent"], bg=C["surface"],
                                selectcolor=C["surface"],
                                activebackground=C["surface"],
                                activeforeground=C["accent"])
            cb.pack(side=tk.LEFT, padx=12)
            self._checks.append(var)
            tk.Label(row_f, text=f"  ({spare_type}备用)",
                     font=("Microsoft YaHei", 10),
                     fg=C["dim"], bg=C["surface"]).pack(side=tk.LEFT, padx=6)
            tk.Label(row_f, text="脱扣器电流In(A)：",
                     font=("Microsoft YaHei", 10),
                     fg=C["text"], bg=C["surface"]).pack(side=tk.LEFT, padx=(24, 6))
            trip_cb = SimpleCombo(row_f, values=[str(t) for t in TRIP_RATINGS],
                                       default=str(default_trip),
                                       width=8, font=("Microsoft YaHei", 10),
                                       state="readonly")
            trip_cb.pack(side=tk.LEFT, padx=2)
            self._trip_vars.append(trip_cb._var)
        bf = tk.Frame(self, bg=C["bg"]); bf.pack(pady=(10, 14))
        tk.Button(bf, text="确定添加", font=("Microsoft YaHei", 12, "bold"),
                  bg=C["success"], fg="white", relief="flat", width=16,
                  command=self._ok).pack(side=tk.LEFT, padx=10)
        tk.Button(bf, text="取消", font=("Microsoft YaHei", 12),
                  bg=C["danger"], fg="white", relief="flat", width=12,
                  command=self.destroy).pack(side=tk.LEFT, padx=10)
    def _ok(self):
        self.result = []
        for i, (cab_code, rem_e, spare_type, default_trip) in enumerate(self.remaining_info):
            if i < len(self._checks) and self._checks[i].get():
                trip_val = int(self._trip_vars[i].get()) if i < len(self._trip_vars) else default_trip
                self.result.append((cab_code, spare_type, trip_val))
        self.destroy()


# ============================================================
# 调试控制台
# ============================================================
class LogPanel(tk.Frame):
    """底部调试控制台：显示计算日志和错误信息"""
    MAX_LINES = 200

    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"], height=CONSOLE_HEIGHT)
        self.pack_propagate(False)

        header = tk.Frame(self, bg=C["header"], height=22)
        header.pack(fill=tk.X); header.pack_propagate(False)
        tk.Label(header, text="▸ 控制台",
                 font=("Microsoft YaHei", 9, "bold"),
                 fg=C["dim"], bg=C["header"]).pack(side=tk.LEFT, padx=10, pady=2)
        self._clear_btn = tk.Label(header, text="清空",
                                    font=("Microsoft YaHei", 8),
                                    fg=C["dim"], bg=C["header"], cursor="hand2")
        self._clear_btn.pack(side=tk.RIGHT, padx=10, pady=2)
        self._clear_btn.bind("<Button-1>", lambda e: self.clear())

        self._text = tk.Text(self, font=("Consolas", 9),
                             bg="#0A0E14", fg=C["dim"],
                             relief="flat", wrap="word",
                             padx=8, pady=4,
                             insertbackground=C["accent"])
        self._text.pack(fill=tk.BOTH, expand=True)
        self._text.configure(state="disabled")

    def log(self, msg: str, level: str = "info"):
        """添加日志行"""
        colors = {"info": C["dim"], "warn": C["warn"], "error": C["danger"],
                  "success": C["success"], "data": C["accent"]}
        color = colors.get(level, C["dim"])
        ts = datetime.now().strftime("%H:%M:%S")
        self._text.configure(state="normal")
        self._text.insert(tk.END, f"[{ts}] ", ("ts",))
        self._text.insert(tk.END, f"{msg}\n", (level,))
        self._text.tag_configure("ts", foreground=C["dim"], font=("Consolas", 8))
        for tag in colors:
            self._text.tag_configure(tag, foreground=colors[tag])
        # 限制行数
        lines = int(self._text.index("end-1c").split(".")[0])
        if lines > self.MAX_LINES:
            self._text.delete("1.0", f"{lines - self.MAX_LINES}.0")
        self._text.configure(state="disabled")
        self._text.see(tk.END)

    def clear(self):
        self._text.configure(state="normal")
        self._text.delete("1.0", tk.END)
        self._text.configure(state="disabled")
        self.log("控制台已清空")


# ============================================================
# 主窗口
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("低压配电系统 回路参数计算工具 — 中国市政中南院李浩")
        self.root.configure(bg=C["bg"])
        try: self.root.state("zoomed")
        except: self.root.geometry("1440x900")
        self.root.minsize(MIN_WINDOW_W, MIN_WINDOW_H)
        self.counter = 1
        self.spare_counter = 0
        self.cab_tracker = CabinetTracker("=X")
        self._layout()
        self.console.log("低压配电计算工具 v13 启动", "success")
        self.console.log("提示: 底部控制台显示计算日志和异常信息", "info")
        self._set_status("就绪 | 填写参数点击「计算并添加」| 单击表格行可回填编辑 | Ctrl+C复制 | 中国市政中南院李浩")

    def _layout(self):
        # ── 顶部工具栏 ──
        top = tk.Frame(self.root, bg=C["header"], height=44)
        top.pack(fill=tk.X); top.pack_propagate(False)
        tk.Label(top, text="低压配电系统  回路参数计算工具",
                 font=("Microsoft YaHei", 13, "bold"),
                 fg="#FFFFFF", bg=C["header"]).pack(side=tk.LEFT, padx=16, pady=8)
        btn_bar = tk.Frame(top, bg=C["header"])
        btn_bar.pack(side=tk.RIGHT, padx=12, pady=4)
        for t, cmd, clr in [
            ("📚 数据库",    self._open_library,  "#6366F1"),
            ("🔌 补备用",    self._auto_spare,     C["warn"]),
            ("🔄 重算全部",  self._recalc_all,     C["accent"]),
            ("🔓 全部解锁",  self._unlock_all,     C["success"]),
            ("🔒 全部加锁",  self._lock_all,      C["danger"]),
            ("📊 导出Excel", self._export_excel,   "#6366F1"),
            ("🗑 清空全部",  self._clear_all,      C["danger"]),
        ]:
            tk.Button(btn_bar, text=t, command=cmd, font=("Microsoft YaHei", 9),
                      bg=clr, fg="white", relief="flat", cursor="hand2",
                      padx=8, pady=3).pack(side=tk.LEFT, padx=2)

        # ── 输入面板 (1行，高度130) ──
        self.input_panel = InputPanel(self.root, self._handle_calc)
        self.input_panel.pack(fill=tk.X, padx=10, pady=(6, 2))

        # 分隔线
        sep = tk.Frame(self.root, height=2, bg=C["accent"])
        sep.pack(fill=tk.X, padx=10, pady=(0, 2))

        # ── 汇总表格 ──
        self.table = SummaryTable(self.root,
                                  self._on_row_click,
                                  self._on_cell_edit,
                                  self._on_table_change)
        self.table.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        # ── 调试控制台 ──
        self.console = LogPanel(self.root)
        self.console.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 2))

        # ── 底部状态栏 ──
        st = tk.Frame(self.root, bg=C["bg"], height=26)
        st.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_lbl = tk.Label(st, font=("Microsoft YaHei", 9),
                                    fg=C["dim"], bg=C["bg"], anchor="w")
        self.status_lbl.pack(side=tk.LEFT, padx=12, pady=3)
        author_lbl = tk.Label(st, text="中国市政中南院 李浩",
                              font=("Microsoft YaHei", 9, "bold"),
                              fg=C["accent"], bg=C["bg"])
        author_lbl.pack(side=tk.RIGHT, padx=16, pady=3)
        # 快捷键
        self.root.bind("<Control-n>", lambda e: self._handle_calc(None))
        self.root.bind("<Control-r>", lambda e: self._recalc_all())
        self.root.bind("<Control-l>", lambda e: self._lock_all())
        self.root.bind("<Control-u>", lambda e: self._unlock_all())

    def _handle_calc(self, edit_ci):
        vals = self.input_panel.read_values()
        if vals is None: return
        cid = vals["cid"] or f"L{self.counter}"
        purpose = vals["purpose"]
        pe = vals["pe_kw"]
        cabinet_type = vals["cabinet_type"]
        is_spare = ("备用" in purpose)
        manual_shell = None
        manual_trip = None
        if is_spare:
            dlg = SpareBreakerDialog(self.root)
            self.root.wait_window(dlg)
            if dlg.result is None:
                self._set_status("取消备用回路添加")
                return
            manual_shell, manual_trip = dlg.result
        ic_temp = calc_ic(pe)
        if is_spare:
            shell_temp = manual_shell or 100
        else:
            shell_temp = select_shell(ic_temp)
        us_temp = UNIT_SPACE_MAP.get(shell_temp, "8E/2")
        unit_e = unit_to_e(us_temp)
        if edit_ci is not None:
            old = self.table.get_col_data(edit_ci)
            if old and old.get("_locked"):
                messagebox.showwarning("已锁定", "回路已锁定，无法修改")
                return
            cabinet_code = old.get("开关柜代号", "") if old else ""
        else:
            base = vals["cabinet_base"]
            if self.cab_tracker.base_name != base:
                self.cab_tracker.reset(base)
            cabinet_code, warn = self.cab_tracker.assign(unit_e)
            if warn:
                messagebox.showwarning("柜体空间提示", warn)
        try:
            result = compute_row(
                cid, purpose, pe, cabinet_code, vals["run_mode"], vals["dist_mode"],
                vals["core_type"], vals["cable_len"], vals["vdrop_limit"],
                cabinet_type, manual_shell, manual_trip)
        except Exception as e:
            self.console.log(f"计算回路 [{cid}] 失败: {e}", "error")
            messagebox.showerror("计算错误", f"回路 [{cid}] 计算失败:\n{e}")
            return
        if edit_ci is not None:
            old = self.table.get_col_data(edit_ci)
            result["_locked"] = old.get("_locked", False) if old else False
            self.table.update_column(edit_ci, result)
            self.input_panel.set_new_mode()
            self.console.log(f"已更新回路: {cid}", "data")
            self._set_status(f"已更新: {cid}")
        else:
            self.table.add_column(result)
            self.counter += 1
            self.input_panel.fields["cid"].set(f"L{self.counter}")
            self.console.log(f"已添加回路: {cid} | 柜号: {cabinet_code} | Pe={pe}kW Ic={ic_temp:.1f}A",
                           "success")
            self._set_status(f"已添加: {cid} | 柜号: {cabinet_code} | 共{self.table.col_count()}条回路")

    def _on_row_click(self, ci):
        """v9: 单击表格行任意位置→回填输入面板"""
        data = self.table.get_col_data(ci)
        if data and not data.get("_locked", False):
            self.input_panel.set_edit_mode(ci, data)
        elif data and data.get("_locked", False):
            self._set_status(f"回路 {data.get('线缆编号','?')} 已锁定，不可编辑")

    def _on_cell_edit(self, ci):
        """v9: 表格内联编辑触发→重算该回路"""
        if ci - 1 >= len(self.table.columns_data): return
        d = self.table.columns_data[ci - 1]
        if d.get("_locked") or d.get("_is_spare"): return
        # 使用当前数据重算
        new = compute_row(
            d.get("线缆编号", f"L{ci}"),
            d.get("回路用途", ""),
            d.get("_pe", d.get("设备功率Pe(kW)", 0)),
            d.get("开关柜代号", ""),
            d.get("运行方式", "变频"),
            d.get("配电形式", "MCC"),
            d.get("_core_type", "4+1"),
            d.get("_cable_len", 100),
            d.get("_vdrop_limit", 3),
            d.get("_cab_type", "抽屉柜"))
        new["_locked"] = d.get("_locked", False)
        new["_is_spare"] = d.get("_is_spare", False)
        # 保留内联编辑可能修改过但未在compute_row中体现的字段
        for key in ["回路用途", "设备功率Pe(kW)", "配电形式", "运行方式"]:
            if key in d: new[key] = d[key]
        self.table.columns_data[ci - 1] = new
        self.table._full_rebuild()
        self._set_status(f"回路 {d.get('线缆编号','?')} 已重算")

    def _auto_spare(self):
        if not self.table.columns_data:
            messagebox.showinfo("提示", "请先添加回路")
            return
        remaining = self.cab_tracker.get_remaining_space(self.table.columns_data)
        if not remaining:
            messagebox.showinfo("提示", "没有可补充的空间")
            return
        spare_info = []
        for cab_code, (rem_e, count) in sorted(remaining.items()):
            temp_rem = rem_e
            while temp_rem >= 8:
                spare_info.append((cab_code, temp_rem, "8E", 100))
                temp_rem -= 8
            if temp_rem >= 4:
                spare_info.append((cab_code, temp_rem, "8E/2", 63))
        if not spare_info:
            messagebox.showinfo("提示", "所有柜子已满")
            return
        dlg = AutoSpareDialog(self.root, spare_info)
        self.root.wait_window(dlg)
        if not dlg.result: return
        added = 0
        for cab_code, spare_type, trip_val in dlg.result:
            self.spare_counter += 1
            e_val = 8 if spare_type == "8E" else 4
            shell_val = 100 if spare_type == "8E" else 100
            spare_data = {
                "开关柜代号": cab_code,
                "开关柜尺寸(WxDH)mm": self.table.columns_data[0].get("开关柜尺寸(WxDH)mm", "600×600×2200") if self.table.columns_data else "600×600×2200",
                "单元空间": spare_type,
                "回路用途": f"备用{self.spare_counter}",
                "设备功率Pe(kW)": 0.0,
                "计算电流Ic(A)": 0.0,
                "断路器壳架电流(A)": shell_val,
                "脱扣器额定电流In(A)": trip_val,
                "配电形式": "/",
                "运行方式": "/",
                "接触器": "/",
                "热继电器": "/",
                "变频器": "/",
                "电流互感器变比": "/",
                "电力监控信号": "/",
                "电力监控信号2": "/",
                "线缆型号规格": "/",
                "线缆编号": f"备用{self.spare_counter}",
                "_pe": 0, "_cab_type": "抽屉柜", "_cab_size": "600×600×2200",
                "_core_type": "4+1", "_cable_len": 0, "_vdrop_limit": 3,
                "_locked": False, "_is_spare": True, "_unit_e": e_val,
                "_pipe": 0,
            }
            self.table.add_column(spare_data)
            added += 1
        if added:
            self._set_status(f"已补充 {added} 个备用回路")
        else:
            self._set_status("未添加备用回路")

    def _recalc_all(self):
        count = 0
        for ci, d in enumerate(self.table.columns_data):
            if d.get("_locked", False): continue
            is_spare = d.get("_is_spare", False)
            try:
                if is_spare:
                    shell_m = d.get("断路器壳架电流(A)", 100)
                    trip_m = d.get("脱扣器额定电流In(A)", 63)
                else:
                    shell_m = None; trip_m = None
                new = compute_row(
                    d.get("线缆编号", f"L{ci+1}"),
                    d.get("回路用途", ""),
                    d.get("_pe", d.get("设备功率Pe(kW)", 0)),
                    d.get("开关柜代号", ""),
                    d.get("运行方式", "变频"),
                    d.get("配电形式", "MCC"),
                    d.get("_core_type", "4+1"),
                    d.get("_cable_len", 100),
                    d.get("_vdrop_limit", 3),
                    d.get("_cab_type", "抽屉柜"),
                    shell_m, trip_m)
                new["_locked"] = False
                # 保留用户编辑的字段
                for key in ["回路用途", "设备功率Pe(kW)", "配电形式", "运行方式"]:
                    if key in d: new[key] = d[key]
                self.table.columns_data[ci] = new
                count += 1
            except Exception as e:
                cid = d.get("线缆编号", f"L{ci+1}")
                self.console.log(f"重算回路 [{cid}] 失败: {e}", "error")
        self.table._full_rebuild()
        failed = len(self.table.columns_data) - count
        if failed > 0:
            self.console.log(f"重算完成: {count}/{len(self.table.columns_data)} 成功, {failed} 失败", "warn")
        else:
            self.console.log(f"重算完成: {count}/{len(self.table.columns_data)} 条回路", "success")
        self._set_status(f"重算完成: {count}/{len(self.table.columns_data)} 条回路")

    def _lock_all(self):
        self.table.lock_all()
        self._set_status("所有回路已加锁")

    def _unlock_all(self):
        self.table.unlock_all()
        self._set_status("所有回路已解锁")

    def _clear_all(self):
        if self.table.columns_data:
            if not messagebox.askyesno("确认", "清空所有回路？"): return
        n = len(self.table.columns_data)
        self.table.clear_all()
        self.counter = 1
        self.spare_counter = 0
        self.cab_tracker.reset("=X")
        self.input_panel.set_new_mode()
        self.console.log(f"已清空全部 {n} 条回路", "warn")
        self._set_status("已清空")

    def _export_excel(self):
        try: import openpyxl
        except: messagebox.showerror("错误", "需要openpyxl"); return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile="低压配电系统_%s" % datetime.now().strftime("%Y%m%d_%H%M%S"),
            filetypes=[("Excel", "*.xlsx")])
        if not path: return
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "低压配电系统"
        # ★ v12: 白色背景，黑色文字，无任何填充
        font_normal = openpyxl.styles.Font(name="宋体", size=10, color="000000")
        font_bold = openpyxl.styles.Font(name="宋体", size=10, color="000000", bold=True)
        font_sig = openpyxl.styles.Font(name="宋体", size=10, color="000000", bold=True, italic=True)
        align = openpyxl.styles.Alignment(horizontal="center", vertical="center", wrap_text=True)
        border = openpyxl.styles.Border(
            left=openpyxl.styles.Side(style="thin", color="000000"),
            right=openpyxl.styles.Side(style="thin", color="000000"),
            top=openpyxl.styles.Side(style="thin", color="000000"),
            bottom=openpyxl.styles.Side(style="thin", color="000000"))
        n = len(self.table.columns_data)
        if n == 0:
            wb.save(path); messagebox.showinfo("完成", "已保存空表"); return
        # === 表头行：A1=参数, B1/C1/D1...=回路线缆编号 ===
        ws.cell(row=1, column=1, value="参数").font = font_bold
        for ci, d in enumerate(self.table.columns_data):
            cid = d.get("线缆编号", "L%d" % (ci+1))
            ws.cell(row=1, column=ci+2, value=cid).font = font_bold
        # === 数据行 ===
        for ri, (name, _) in enumerate(SUMMARY_ROWS):
            row = ri + 2
            ws.cell(row=row, column=1, value=name).font = font_normal
            for ci, d in enumerate(self.table.columns_data):
                col = ci + 2
                if ri == MONITOR_ROW:
                    line1 = str(d.get("电力监控信号", "/"))
                    line2 = str(d.get("电力监控信号2", "/"))
                    val = ("%s\n%s" % (line1, line2)) if (line2 and line2 != "/") else line1
                else:
                    val = d.get(name, "")
                ws.cell(row=row, column=col, value=val).font = font_normal
        # === 合并单元格（开关柜代号、开关柜尺寸） ===
        tracker = CabinetTracker("")
        groups = tracker.get_cabinet_groups(self.table.columns_data)
        for cab_code, indices in groups.items():
            if len(indices) <= 1: continue
            start_col = indices[0] + 2
            end_col = indices[-1] + 2
            ws.merge_cells(start_row=2, start_column=start_col, end_row=2, end_column=end_col)
            ws.merge_cells(start_row=3, start_column=start_col, end_row=3, end_column=end_col)
        # === 署名行 ===
        sig_row = len(SUMMARY_ROWS) + 3
        ws.cell(row=sig_row, column=1, value="中国市政中南院 李浩").font = font_sig
        # === 格式统一 ===
        for row in ws.iter_rows(min_row=1, max_row=sig_row, min_col=1, max_col=n+1):
            for cell in row:
                cell.alignment = align
                cell.border = border
        # 列宽
        ws.column_dimensions['A'].width = 22
        for i in range(2, n + 3):
            col_letter = openpyxl.utils.get_column_letter(i)
            ws.column_dimensions[col_letter].width = 20
        # 行高：监控信号行(含\n)设为2倍普通行高
        for row_idx in range(1, sig_row + 1):
            has_ml = False
            for col_idx in range(1, n + 2):
                cv = ws.cell(row=row_idx, column=col_idx).value
                if cv and isinstance(cv, str) and "\n" in cv:
                    has_ml = True; break
            ws.row_dimensions[row_idx].height = 36 if has_ml else 18
        wb.save(path)
        self.console.log(f"Excel 已导出: {os.path.basename(path)} ({n} 条回路)", "success")
        self._set_status("导出: %s" % os.path.basename(path))
        messagebox.showinfo("完成", "已保存:\n%s" % path)
    def _open_library(self):
        LibraryPopup(self.root)

    def _on_table_change(self):
        """数据变化时更新控制台统计"""
        n = len(self.table.columns_data) if hasattr(self, 'table') else 0
        locked = sum(1 for d in (self.table.columns_data or []) if d.get("_locked"))
        spare = sum(1 for d in (self.table.columns_data or []) if d.get("_is_spare"))
        if n > 0:
            self.console.log(f"当前回路: {n} 条 (锁定: {locked}, 备用: {spare})", "info")

    def _set_status(self, msg):
        self.status_lbl.configure(text=msg)


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(); style.theme_use("clam")
    style.configure("TCombobox",
                    font=("Microsoft YaHei", 10),
                    fieldbackground=C["input_bg"], background=C["input_bg"],
                    foreground=C["input_fg"], arrowcolor=C["dim"],
                    selectbackground=C["accent"])
    style.map("TCombobox",
              fieldbackground=[("readonly", C["input_bg"])],
              foreground=[("readonly", C["input_fg"])])
    app = App(root)
    root.mainloop()
