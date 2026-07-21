# -*- coding: utf-8 -*-
"""
项目台账 独立桌面程序 (Standalone Project Ledger)
================================================
复刻内网门户「工时管理 -> 项目台账」页面全部功能，本地 SQLite 存储，
无需登录网页，双击 EXE 即可操作。

功能：
  - 表格浏览（11 列，可排序、可勾选）
  - 快速搜索 + 高级搜索（可存为模板）
  - 左侧 5 个筛选预设视图
  - 新增 / 编辑 / 删除（单选 + 批量）
  - 批量共享（导出选中为共享包 JSON）
  - 导出当前视图为 CSV（Excel 可直接打开）
  - 导入 CSV（从网页导出一次后离线操作）
  - 分页（10/20/50/100 每页）
  - 【工时填报】第二个标签页：复刻门户「工时管理 -> 工时填报」表单
      · 基础信息（填报人/部门/专业所/所长/技术职称/职称级别/从事专业/工时所属日期必填/填报日期）
      · 工时信息明细表（多行：项目名称[联动项目台账]、项目编号、任务类别、工时h、出差工时d、实际出差工时天、工作内容、备注）
      · 添加/删除/复制行；保存 / 保存并新建；已填报记录查看与删除
  - 帮助

打包：pyinstaller --onefile --windowed --name 项目台账 main.py
"""

import os
import sys
import csv
import json
import sqlite3
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QComboBox, QLabel, QDialog,
    QFormLayout, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QCheckBox,
    QDoubleSpinBox, QSpinBox, QFileDialog, QMessageBox, QGroupBox,
    QAbstractItemView, QMenuBar, QStatusBar, QFrame, QInputDialog,
    QTabWidget, QDateEdit
)
from PySide6.QtCore import Qt, QSize, QDate
from PySide6.QtGui import QAction

# ----------------------------------------------------------------------------
# 路径：EXE 运行时用 sys._MEIPASS 或脚本目录；数据库放在程序同目录
# ----------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(APP_DIR, "project_ledger.db")

# ----------------------------------------------------------------------------
# 列定义
# ----------------------------------------------------------------------------
COLUMNS = [
    ("name", "项目名称", "text"),
    ("code", "项目编号", "text"),
    ("eng_cost", "工程费用(万元)", "num"),
    ("design_fee", "设计费(万元)", "num"),
    ("leader", "项目负责人", "text"),
    ("status", "项目状态", "text"),
    ("is_public", "是否公共项目", "bool"),
    ("display_order", "显示顺序", "int"),
    ("attribution", "项目归属", "text"),
    ("category", "项目类别", "text"),
    ("creator", "创建人", "text"),
]
COL_KEYS = [c[0] for c in COLUMNS]
COL_HEADERS = ["□"] + [c[1] for c in COLUMNS]  # 第0列放勾选框
SORT_COL_MAP = {i + 1: COLUMNS[i][0] for i in range(len(COLUMNS))}

STATUS_OPTIONS = ["全部", "进行中", "已完成", "暂停", "接洽"]
CATEGORY_OPTIONS = ["全部", "污水", "供水", "再生水", "管理", "行政", "其他"]

# 工时填报相关枚举
TITLE_OPTIONS = ["教授级高级工程师", "高级工程师", "工程师", "助理工程师"]
TITLE_LEVEL_OPTIONS = ["正高级", "副高级", "中级", "初级"]
MAJOR_OPTIONS = ["电气及自动化", "电气", "自动化", "给排水", "结构", "建筑", "暖通"]
TASK_CAT_OPTIONS = ["设计", "校核", "审核", "审定", "图纸", "现场服务", "调研", "管理", "其他"]
# 非项目类工时类别（与项目台账中的默认类别对应，网页预置行）
WORK_CATEGORIES = [
    ("请假（请假半天以上需在OA中申请）", "QJ-001"),
    ("管理（项目安排、人员安排等非技术类管理工作）", "GL-001"),
    ("行政（党建、团建、报奖、统计等非技术生产工作）", "XZ-001"),
    ("学习（培训、交流、调研、考察等学习或培训）", "XX-001"),
]

# ----------------------------------------------------------------------------
# 种子数据（真实风格，市政设计院项目）
# ----------------------------------------------------------------------------
SEED = [
    ("JQ-001", "新项目接洽", 0, 0, "贾瑟", "接洽", 0, 1, "经营部", "其他", "贾瑟"),
    ("FW-001", "以往项目服务", 0, 0, "崔亚伟", "已完成", 0, 2, "水务所", "污水", "崔亚伟"),
    ("GL-001", "管理类综合项目", 0, 0, "蒋奇", "进行中", 1, 3, "总院", "管理", "蒋奇"),
    ("XZ-001", "行政事务管理", 0, 0, "晶晶", "进行中", 1, 4, "行政部", "行政", "晶晶"),
    ("XX-001", "学习培训专项", 0, 0, "贾瑟", "进行中", 0, 5, "人力资源部", "其他", "贾瑟"),
    ("QJ-001", "请假备案登记", 0, 0, "贾瑟", "已完成", 0, 6, "行政部", "行政", "贾瑟"),
    ("WH-2024-001", "武汉新城葛华片区污水处理厂设备更新改造工程（EPC）", 18650.0, 932.0, "蒋奇", "进行中", 1, 7, "水务所", "污水", "蒋奇"),
    ("YC-2024-002", "宜城市经济开发区污水处理厂改扩建项目 EPC 总承包", 24300.0, 1215.0, "崔亚伟", "进行中", 1, 8, "水务所", "污水", "崔亚伟"),
    ("CH-2023-003", "巢湖流域污水处理设施更新改造（一期）", 31200.0, 1560.0, "周畅", "进行中", 1, 9, "水务所", "污水", "周畅"),
    ("TY-2022-004", "太原市杨家堡污水厂提标改造工程", 9800.0, 490.0, "王磊", "已完成", 1, 10, "华北分院", "污水", "王磊"),
    ("JQ-2024-005", "酒泉市再生水利用工程", 15600.0, 780.0, "李娜", "进行中", 1, 11, "西北分院", "再生水", "李娜"),
    ("ZY-2024-006", "张掖市供水二期工程", 12800.0, 640.0, "赵强", "进行中", 1, 12, "西北分院", "供水", "赵强"),
    ("TM-2025-007", "图木舒克二期污水厂电气工程", 4200.0, 210.0, "贾瑟", "进行中", 0, 13, "电气所", "污水", "贾瑟"),
    ("Z-2025-008", "枣阳二次供水可研", 1800.0, 90.0, "贾瑟", "进行中", 0, 14, "供水所", "供水", "贾瑟"),
    ("YC-2025-009", "宜城工业厂施工图", 5600.0, 280.0, "贾瑟", "进行中", 0, 15, "电气所", "污水", "贾瑟"),
    ("WUH-2023-010", "武汉市江南再生水厂及管网工程", 28900.0, 1445.0, "陈宇", "进行中", 1, 16, "水务所", "再生水", "陈宇"),
    ("HZ-2022-011", "杭州城西污水处理厂提标工程", 13400.0, 670.0, "孙琳", "已完成", 1, 17, "华东分院", "污水", "孙琳"),
    ("CD-2024-012", "成都天府新区供水一体化工程", 21700.0, 1085.0, "刘洋", "进行中", 1, 18, "西南分院", "供水", "刘洋"),
    ("XA-2023-013", "西安浐灞再生水回用工程", 9900.0, 495.0, "马涛", "已完成", 1, 19, "西北分院", "再生水", "马涛"),
    ("GZ-2025-014", "广州南沙工业废水处理厂", 17600.0, 880.0, "黄伟", "进行中", 1, 20, "华南分院", "污水", "黄伟"),
]

# 额外批量生成，凑足样本量（非真实，仅为演示/测试数据量）
_EXTRA_CITIES = ["昆明", "贵阳", "兰州", "西宁", "银川", "乌鲁木齐", "呼和浩特", "南宁", "海口", "拉萨",
                 "沈阳", "长春", "哈尔滨", "石家庄", "太原", "郑州", "济南", "合肥", "南昌", "福州"]
for i, city in enumerate(_EXTRA_CITIES):
    idx = 100 + i
    cat = ["污水", "供水", "再生水"][i % 3]
    st = ["进行中", "已完成", "暂停"][i % 3]
    SEED.append((
        f"XM-{idx}", f"{city}市{cat}处理厂新建工程",
        round(5000 + i * 320.5, 1), round(250 + i * 16.0, 1),
        ["贾瑟", "崔亚伟", "蒋奇", "周畅", "王磊", "李娜"][i % 6],
        st, 1 if i % 2 == 0 else 0, idx,
        ["水务所", "供水所", "电气所", "西北分院"][i % 4], cat,
        ["贾瑟", "崔亚伟", "蒋奇"][i % 3]
    ))


# ----------------------------------------------------------------------------
# 数据库
# ----------------------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT,
            eng_cost REAL,
            design_fee REAL,
            leader TEXT,
            status TEXT,
            is_public INTEGER DEFAULT 0,
            display_order INTEGER,
            attribution TEXT,
            category TEXT,
            creator TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS search_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            filters TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS work_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fill_person TEXT,
            dept TEXT,
            major_office TEXT,
            office_head TEXT,
            title TEXT,
            title_level TEXT,
            major TEXT,
            work_date TEXT,
            fill_date TEXT,
            details TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    cnt = cur.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if cnt == 0:
        cur.executemany(
            "INSERT INTO projects (code,name,eng_cost,design_fee,leader,status,"
            "is_public,display_order,attribution,category,creator) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            SEED,
        )
        conn.commit()
    conn.close()


# ----------------------------------------------------------------------------
# 查询构建
# ----------------------------------------------------------------------------
def build_where(filters):
    """filters: dict，返回 (where_clause, params)"""
    clauses = []
    params = []
    if filters.get("q"):  # 快速搜索：名称/编号/负责人 包含
        q = "%" + filters["q"] + "%"
        clauses.append("(name LIKE ? OR code LIKE ? OR leader LIKE ?)")
        params.extend([q, q, q])
    if filters.get("name"):
        clauses.append("name LIKE ?"); params.append("%" + filters["name"] + "%")
    if filters.get("code"):
        clauses.append("code LIKE ?"); params.append("%" + filters["code"] + "%")
    if filters.get("leader"):
        clauses.append("leader LIKE ?"); params.append("%" + filters["leader"] + "%")
    if filters.get("attribution"):
        clauses.append("attribution LIKE ?"); params.append("%" + filters["attribution"] + "%")
    if filters.get("creator"):
        clauses.append("creator LIKE ?"); params.append("%" + filters["creator"] + "%")
    if filters.get("status") and filters["status"] != "全部":
        clauses.append("status = ?"); params.append(filters["status"])
    if filters.get("category") and filters["category"] != "全部":
        clauses.append("category = ?"); params.append(filters["category"])
    if filters.get("is_public") and filters["is_public"] != "全部":
        clauses.append("is_public = ?"); params.append(1 if filters["is_public"] == "是" else 0)
    if filters.get("min_eng") not in (None, ""):
        clauses.append("eng_cost >= ?"); params.append(float(filters["min_eng"]))
    if filters.get("min_fee") not in (None, ""):
        clauses.append("design_fee >= ?"); params.append(float(filters["min_fee"]))
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


# 左侧预设视图
PRESETS = [
    ("全部项目（项目台账）", {}),
    ("公共项目", {"is_public": "是"}),
    ("非公共项目", {"is_public": "否"}),
    ("有工程费用(>0)", {"min_eng": 0.01}),
    ("进行中项目", {"status": "进行中"}),
]


# ----------------------------------------------------------------------------
# 新增/编辑对话框
# ----------------------------------------------------------------------------
class EditDialog(QDialog):
    def __init__(self, parent=None, row=None):
        super().__init__(parent)
        self.setWindowTitle("新增项目" if row is None else "编辑项目")
        self.resize(420, 360)
        form = QFormLayout(self)

        self.code = QLineEdit(row["code"] if row else "")
        self.name = QLineEdit(row["name"] if row else "")
        self.eng = QDoubleSpinBox(); self.eng.setMaximum(9999999); self.eng.setDecimals(2)
        self.fee = QDoubleSpinBox(); self.fee.setMaximum(9999999); self.fee.setDecimals(2)
        self.leader = QLineEdit(row["leader"] if row else "")
        self.status = QComboBox(); self.status.addItems(STATUS_OPTIONS[1:])
        self.is_pub = QCheckBox(); self.is_pub.setChecked(bool(row["is_public"]) if row else False)
        self.order = QSpinBox(); self.order.setMaximum(999999)
        self.attribution = QLineEdit(row["attribution"] if row else "")
        self.category = QComboBox(); self.category.addItems(CATEGORY_OPTIONS[1:])
        self.creator = QLineEdit(row["creator"] if row else "贾瑟")

        if row:
            self.eng.setValue(row["eng_cost"] or 0)
            self.fee.setValue(row["design_fee"] or 0)
            if row["status"] in STATUS_OPTIONS: self.status.setCurrentText(row["status"])
            self.order.setValue(row["display_order"] or 0)
            if row["category"] in CATEGORY_OPTIONS: self.category.setCurrentText(row["category"])

        form.addRow("项目编号*", self.code)
        form.addRow("项目名称*", self.name)
        form.addRow("工程费用(万元)", self.eng)
        form.addRow("设计费(万元)", self.fee)
        form.addRow("项目负责人", self.leader)
        form.addRow("项目状态", self.status)
        form.addRow("是否公共项目", self.is_pub)
        form.addRow("显示顺序", self.order)
        form.addRow("项目归属", self.attribution)
        form.addRow("项目类别", self.category)
        form.addRow("创建人", self.creator)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def data(self):
        return {
            "code": self.code.text().strip(),
            "name": self.name.text().strip(),
            "eng_cost": self.eng.value(),
            "design_fee": self.fee.value(),
            "leader": self.leader.text().strip(),
            "status": self.status.currentText(),
            "is_public": 1 if self.is_pub.isChecked() else 0,
            "display_order": self.order.value(),
            "attribution": self.attribution.text().strip(),
            "category": self.category.currentText(),
            "creator": self.creator.text().strip() or "贾瑟",
        }


# ----------------------------------------------------------------------------
# 工时填报 部件（复刻内网门户 工时管理 -> 工时填报 表单）
# ----------------------------------------------------------------------------
class WorkHoursWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._proj_map = {}
        self._build_ui()
        self.load_projects()
        self.add_row()  # 默认一行

    def _build_ui(self):
        root = QVBoxLayout(self)

        # ---- 基础信息 ----
        gb_info = QGroupBox("基础信息")
        fl = QFormLayout(gb_info)
        self.w_fill_person = QLineEdit("贾瑟"); self.w_fill_person.setReadOnly(True)
        self.w_dept = QLineEdit("四院本部"); self.w_dept.setReadOnly(True)
        self.w_office = QLineEdit("电气所"); self.w_office.setReadOnly(True)
        self.w_head = QLineEdit("周畅"); self.w_head.setReadOnly(True)
        self.w_title = QComboBox(); self.w_title.addItems(TITLE_OPTIONS)
        self.w_level = QComboBox(); self.w_level.addItems(TITLE_LEVEL_OPTIONS)
        self.w_major = QComboBox(); self.w_major.addItems(MAJOR_OPTIONS)
        self.w_work_date = QDateEdit(); self.w_work_date.setCalendarPopup(True)
        self.w_work_date.setDisplayFormat("yyyy-MM-dd")
        self.w_fill_date = QDateEdit(); self.w_fill_date.setCalendarPopup(True)
        self.w_fill_date.setDisplayFormat("yyyy-MM-dd")
        self.w_fill_date.setDate(QDate.currentDate())
        self.w_fill_date.setReadOnly(True)
        fl.addRow("填报人", self.w_fill_person)
        fl.addRow("部门", self.w_dept)
        fl.addRow("所属专业所", self.w_office)
        fl.addRow("专业所所长", self.w_head)
        fl.addRow("技术职称", self.w_title)
        fl.addRow("职称级别", self.w_level)
        fl.addRow("从事专业", self.w_major)
        fl.addRow("工时所属日期 *", self.w_work_date)
        fl.addRow("填报日期", self.w_fill_date)
        root.addWidget(gb_info)

        # ---- 工时信息 ----
        gb_detail = QGroupBox("工时信息（可添加多行）")
        dv = QVBoxLayout(gb_detail)
        bar = QHBoxLayout()
        b_add = QPushButton("添加行"); b_del = QPushButton("删除行"); b_copy = QPushButton("复制行")
        b_add.clicked.connect(self.add_row)
        b_del.clicked.connect(self.delete_row)
        b_copy.clicked.connect(self.copy_row)
        bar.addWidget(b_add); bar.addWidget(b_del); bar.addWidget(b_copy)
        bar.addStretch(1)
        dv.addLayout(bar)

        self.grid = QTableWidget()
        self.grid.setColumnCount(10)
        self.grid.setHorizontalHeaderLabels(
            ["", "序号", "项目名称", "项目编号", "任务类别",
             "工时(h)", "出差工时(d)", "实际出差工时(天)", "工作内容", "备注"])
        self.grid.verticalHeader().setVisible(False)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        dv.addWidget(self.grid, 1)
        root.addWidget(gb_detail)

        # ---- 操作按钮 ----
        op = QHBoxLayout()
        b_save = QPushButton("保存"); b_savenew = QPushButton("保存并新建")
        b_save.clicked.connect(lambda: self.save(False))
        b_savenew.clicked.connect(lambda: self.save(True))
        op.addWidget(b_save); op.addWidget(b_savenew)
        op.addStretch(1)
        root.addLayout(op)

        # ---- 已填报记录 ----
        gb_rec = QGroupBox("已填报记录")
        rv = QVBoxLayout(gb_rec)
        rbar = QHBoxLayout()
        b_refresh = QPushButton("刷新"); b_view = QPushButton("查看明细"); b_delrec = QPushButton("删除记录")
        b_refresh.clicked.connect(self.load_records)
        b_view.clicked.connect(self.view_record)
        b_delrec.clicked.connect(self.delete_record)
        rbar.addWidget(b_refresh); rbar.addWidget(b_view); rbar.addWidget(b_delrec)
        rbar.addStretch(1)
        rv.addLayout(rbar)
        self.rec_table = QTableWidget()
        self.rec_table.setColumnCount(5)
        self.rec_table.setHorizontalHeaderLabels(["填报人", "工时所属日期", "填报日期", "明细条数", "ID"])
        self.rec_table.setColumnHidden(4, True)
        self.rec_table.verticalHeader().setVisible(False)
        self.rec_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rec_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        rv.addWidget(self.rec_table)
        root.addWidget(gb_rec)
        self.load_records()

    # ---------- 项目来源（联动项目台账） ----------
    def load_projects(self):
        conn = get_conn()
        rows = conn.execute("SELECT name, code FROM projects ORDER BY display_order").fetchall()
        conn.close()
        self._proj_map = {r["name"]: r["code"] for r in rows}
        for nm, cd in WORK_CATEGORIES:
            self._proj_map.setdefault(nm, cd)
        names = list(self._proj_map.keys())
        for r in range(self.grid.rowCount()):
            cb = self.grid.cellWidget(r, 2)
            if isinstance(cb, QComboBox):
                cur = cb.currentText()
                cb.clear(); cb.addItems(names)
                if cur in names:
                    cb.setCurrentText(cur)

    # ---------- 明细行 ----------
    def add_row(self, copy_from=None):
        r = self.grid.rowCount()
        self.grid.insertRow(r)
        cb = QTableWidgetItem()
        cb.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        cb.setCheckState(Qt.Unchecked)
        self.grid.setItem(r, 0, cb)
        self.grid.setItem(r, 1, QTableWidgetItem(str(r + 1)))
        pcb = QComboBox(); pcb.setEditable(True); pcb.addItems(list(self._proj_map.keys()))
        pcb.currentTextChanged.connect(lambda txt, row=r: self._on_proj(row, txt))
        if copy_from:
            pcb.setCurrentText(copy_from.get("name", ""))
        self.grid.setCellWidget(r, 2, pcb)
        code = QLineEdit(); code.setReadOnly(True)
        if copy_from:
            code.setText(copy_from.get("code", ""))
        self.grid.setCellWidget(r, 3, code)
        tcb = QComboBox(); tcb.addItems(TASK_CAT_OPTIONS)
        if copy_from:
            tcb.setCurrentText(copy_from.get("task", "设计"))
        self.grid.setCellWidget(r, 4, tcb)
        h = QDoubleSpinBox(); h.setMaximum(999); h.setDecimals(1)
        if copy_from:
            h.setValue(copy_from.get("hours", 0))
        self.grid.setCellWidget(r, 5, h)
        td = QDoubleSpinBox(); td.setMaximum(999); td.setDecimals(1)
        if copy_from:
            td.setValue(copy_from.get("trip", 0))
        self.grid.setCellWidget(r, 6, td)
        tda = QDoubleSpinBox(); tda.setMaximum(999); tda.setDecimals(1)
        if copy_from:
            tda.setValue(copy_from.get("trip_actual", 0))
        self.grid.setCellWidget(r, 7, tda)
        content = QLineEdit()
        if copy_from:
            content.setText(copy_from.get("content", ""))
        self.grid.setCellWidget(r, 8, content)
        remark = QLineEdit()
        if copy_from:
            remark.setText(copy_from.get("remark", ""))
        self.grid.setCellWidget(r, 9, remark)
        self._renumber()

    def _on_proj(self, row, txt):
        w = self.grid.cellWidget(row, 3)
        if isinstance(w, QLineEdit):
            w.setText(self._proj_map.get(txt, ""))

    def _renumber(self):
        for r in range(self.grid.rowCount()):
            it = self.grid.item(r, 1)
            if it:
                it.setText(str(r + 1))

    def delete_row(self):
        for r in range(self.grid.rowCount() - 1, -1, -1):
            it = self.grid.item(r, 0)
            if it and it.checkState() == Qt.Checked:
                self.grid.removeRow(r)
        self._renumber()

    def copy_row(self):
        sel = [r for r in range(self.grid.rowCount())
               if self.grid.item(r, 0) and self.grid.item(r, 0).checkState() == Qt.Checked]
        if not sel:
            QMessageBox.information(self, "提示", "请先勾选要复制的行")
            return
        self.add_row(copy_from=self._row_data(sel[0]))

    def _row_data(self, r):
        def gw(c):
            w = self.grid.cellWidget(r, c)
            if isinstance(w, QComboBox):
                return w.currentText()
            if isinstance(w, QDoubleSpinBox):
                return w.value()
            if isinstance(w, QLineEdit):
                return w.text()
            return ""
        code_w = self.grid.cellWidget(r, 3)
        return {
            "name": gw(2),
            "code": code_w.text() if isinstance(code_w, QLineEdit) else "",
            "task": gw(4), "hours": gw(5), "trip": gw(6), "trip_actual": gw(7),
            "content": gw(8), "remark": gw(9),
        }

    def _collect(self):
        details = []
        for r in range(self.grid.rowCount()):
            w2 = self.grid.cellWidget(r, 2)
            name = w2.currentText().strip() if isinstance(w2, QComboBox) else ""
            if not name:
                continue

            def gw(c):
                w = self.grid.cellWidget(r, c)
                if isinstance(w, QComboBox):
                    return w.currentText()
                if isinstance(w, QDoubleSpinBox):
                    return w.value()
                if isinstance(w, QLineEdit):
                    return w.text().strip()
                return ""
            code_w = self.grid.cellWidget(r, 3)
            code = code_w.text().strip() if isinstance(code_w, QLineEdit) else ""
            details.append({
                "name": name, "code": code, "task": gw(4),
                "hours": gw(5), "trip": gw(6), "trip_actual": gw(7),
                "content": gw(8), "remark": gw(9),
            })
        return details

    # ---------- 保存 ----------
    def save(self, new_after):
        work_date = self.w_work_date.date().toString("yyyy-MM-dd")
        if not work_date:
            QMessageBox.warning(self, "提示", "工时所属日期为必填项")
            return
        details = self._collect()
        if not details:
            QMessageBox.warning(self, "提示", "请至少填写一行工时明细")
            return
        conn = get_conn()
        conn.execute(
            "INSERT INTO work_hours (fill_person,dept,major_office,office_head,title,"
            "title_level,major,work_date,fill_date,details,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (self.w_fill_person.text(), self.w_dept.text(), self.w_office.text(),
             self.w_head.text(), self.w_title.currentText(), self.w_level.currentText(),
             self.w_major.currentText(), work_date,
             self.w_fill_date.date().toString("yyyy-MM-dd"),
             json.dumps(details, ensure_ascii=False),
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()
        QMessageBox.information(self, "完成", "工时填报已保存（%d 条明细）" % len(details))
        self.load_records()
        if new_after:
            self.clear_form()

    def clear_form(self):
        self.grid.setRowCount(0)
        self.add_row()
        self.w_fill_date.setDate(QDate.currentDate())

    # ---------- 记录列表 ----------
    def load_records(self):
        conn = get_conn()
        rows = conn.execute("SELECT * FROM work_hours ORDER BY id DESC").fetchall()
        conn.close()
        self._rec_rows = rows
        self.rec_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            try:
                n = len(json.loads(row["details"]))
            except Exception:
                n = 0
            self.rec_table.setItem(r, 0, QTableWidgetItem(row["fill_person"] or ""))
            self.rec_table.setItem(r, 1, QTableWidgetItem(row["work_date"] or ""))
            self.rec_table.setItem(r, 2, QTableWidgetItem(row["fill_date"] or ""))
            self.rec_table.setItem(r, 3, QTableWidgetItem(str(n)))
            self.rec_table.setItem(r, 4, QTableWidgetItem(str(row["id"])))

    def view_record(self):
        r = self.rec_table.currentRow()
        if r < 0 or not hasattr(self, "_rec_rows"):
            return
        row = self._rec_rows[r]
        try:
            details = json.loads(row["details"])
        except Exception:
            details = []
        lines = []
        for i, d in enumerate(details, 1):
            lines.append("%d. %s [%s] %s 工时%sh 出差%sd 内容:%s 备注:%s" % (
                i, d.get("name", ""), d.get("code", ""), d.get("task", ""),
                d.get("hours", 0), d.get("trip", 0),
                d.get("content", ""), d.get("remark", "")))
        msg = ("填报人: %s\n工时所属日期: %s\n填报日期: %s\n\n%s" %
               (row["fill_person"], row["work_date"], row["fill_date"], "\n".join(lines)))
        QMessageBox.information(self, "工时填报明细", msg)

    def delete_record(self):
        r = self.rec_table.currentRow()
        if r < 0 or not hasattr(self, "_rec_rows"):
            return
        row = self._rec_rows[r]
        if QMessageBox.question(self, "确认", "删除该工时填报记录（ID %s）？" % row["id"]) == QMessageBox.Yes:
            conn = get_conn()
            conn.execute("DELETE FROM work_hours WHERE id=?", (row["id"],))
            conn.commit(); conn.close()
            self.load_records()


# ----------------------------------------------------------------------------
# 主窗口
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("项目台账 — 独立桌面程序")
        self.resize(1180, 720)
        self.filters = {}
        self.sort_col = "id"
        self.sort_dir = "ASC"
        self.page = 1
        self.page_size = 10
        self.selected_ids = set()
        self._build_ui()
        self.load_templates()
        self.apply_preset(0)
        self.refresh()

    # ---------------- UI ----------------
    def _build_ui(self):
        menubar = self.menuBar()
        m = menubar.addMenu("文件")
        m.addAction(QAction("导入CSV", self, triggered=self.import_csv))
        m.addAction(QAction("导出CSV", self, triggered=self.export_csv))
        m.addSeparator()
        m.addAction(QAction("退出", self, triggered=self.close))
        mh = menubar.addMenu("帮助")
        mh.addAction(QAction("使用说明", self, triggered=self.show_help))

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        tab_ledger = QWidget()
        root = QVBoxLayout(tab_ledger)

        # 顶部工具栏
        tb = QHBoxLayout()
        self.quick = QLineEdit(); self.quick.setPlaceholderText("快速搜索：名称/编号/负责人")
        self.quick.returnPressed.connect(self.do_quick)
        btn_quick = QPushButton("搜索"); btn_quick.clicked.connect(self.do_quick)
        self.btn_add = QPushButton("新增")
        self.btn_del = QPushButton("删除")
        self.btn_share = QPushButton("批量共享")
        self.btn_export = QPushButton("导出")
        self.btn_import = QPushButton("导入")
        self.btn_help = QPushButton("帮助")
        self.btn_add.clicked.connect(self.add_record)
        self.btn_del.clicked.connect(self.delete_selected)
        self.btn_share.clicked.connect(self.batch_share)
        self.btn_export.clicked.connect(self.export_csv)
        self.btn_import.clicked.connect(self.import_csv)
        self.btn_help.clicked.connect(self.show_help)
        for w in [QLabel("🔎"), self.quick, btn_quick, self.btn_add, self.btn_del,
                  self.btn_share, self.btn_export, self.btn_import, self.btn_help]:
            tb.addWidget(w)
        tb.addStretch(1)
        root.addLayout(tb)

        # 中部：左预设 + 右表格/高级搜索
        mid = QHBoxLayout()
        # 左：预设视图
        left = QVBoxLayout()
        left.addWidget(QLabel("视图"))
        self.preset_list = QTableWidget(); self.preset_list.setColumnCount(1)
        self.preset_list.setHorizontalHeaderLabels(["筛选视图"])
        self.preset_list.setRowCount(len(PRESETS))
        self.preset_list.setMaximumWidth(180)
        self.preset_list.verticalHeader().setVisible(False)
        self.preset_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preset_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        for i, (label, _) in enumerate(PRESETS):
            self.preset_list.setItem(i, 0, QTableWidgetItem(label))
        self.preset_list.cellClicked.connect(lambda r, c: self.apply_preset(r))
        left.addWidget(self.preset_list)
        left.addStretch(1)

        # 右：高级搜索 + 表格
        right = QVBoxLayout()
        self.adv = QGroupBox("高级搜索（可存为模板）")
        advl = QFormLayout(self.adv)
        self.f_name = QLineEdit(); self.f_code = QLineEdit()
        self.f_leader = QLineEdit(); self.f_attr = QLineEdit()
        self.f_creator = QLineEdit()
        self.f_status = QComboBox(); self.f_status.addItems(STATUS_OPTIONS)
        self.f_cat = QComboBox(); self.f_cat.addItems(CATEGORY_OPTIONS)
        self.f_pub = QComboBox(); self.f_pub.addItems(["全部", "是", "否"])
        self.f_meng = QLineEdit(); self.f_mfee = QLineEdit()
        advl.addRow("项目名称", self.f_name)
        advl.addRow("项目编号", self.f_code)
        advl.addRow("项目负责人", self.f_leader)
        advl.addRow("项目归属", self.f_attr)
        advl.addRow("创建人", self.f_creator)
        advl.addRow("项目状态", self.f_status)
        advl.addRow("项目类别", self.f_cat)
        advl.addRow("是否公共", self.f_pub)
        advl.addRow("工程费用≥", self.f_meng)
        advl.addRow("设计费≥", self.f_mfee)
        adv_btn = QHBoxLayout()
        b_search = QPushButton("搜索"); b_search.clicked.connect(self.do_advanced)
        b_reset = QPushButton("重置"); b_reset.clicked.connect(self.reset_adv)
        self.tpl_combo = QComboBox(); self.tpl_combo.addItem("（加载模板）")
        b_load = QPushButton("载入"); b_load.clicked.connect(self.load_template)
        b_save = QPushButton("存为模板"); b_save.clicked.connect(self.save_template)
        adv_btn.addWidget(b_search); adv_btn.addWidget(b_reset)
        adv_btn.addWidget(self.tpl_combo); adv_btn.addWidget(b_load); adv_btn.addWidget(b_save)
        advl.addRow(adv_btn)
        self.adv.setCheckable(True); self.adv.setChecked(False); self.adv.collapsed = True
        # 简单折叠：勾选展开
        self.adv.toggled.connect(lambda v: self.adv.setVisible(True))
        right.addWidget(self.adv)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(len(COL_HEADERS))
        self.table.setHorizontalHeaderLabels(COL_HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_click)
        self.table.cellClicked.connect(self.on_cell_click)
        right.addWidget(self.table, 1)

        # 分页
        pg = QHBoxLayout()
        self.lbl_total = QLabel("共 0 条")
        self.page_size_combo = QComboBox(); self.page_size_combo.addItems(["10", "20", "50", "100"])
        self.page_size_combo.setCurrentText("10")
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        self.b_first = QPushButton("第一页"); self.b_prev = QPushButton("上一页")
        self.b_next = QPushButton("下一页"); self.b_last = QPushButton("最后一页")
        self.lbl_page = QLabel("第 1 页")
        self.jump = QLineEdit(); self.jump.setFixedWidth(50); self.jump.setPlaceholderText("页")
        self.b_jump = QPushButton("跳转")
        self.b_first.clicked.connect(lambda: self.goto_page(1))
        self.b_prev.clicked.connect(lambda: self.goto_page(self.page - 1))
        self.b_next.clicked.connect(lambda: self.goto_page(self.page + 1))
        self.b_last.clicked.connect(self.goto_last)
        self.b_jump.clicked.connect(self.do_jump)
        for w in [self.lbl_total, QLabel("每页"), self.page_size_combo, self.b_first,
                  self.b_prev, self.lbl_page, self.b_next, self.b_last,
                  QLabel("跳"), self.jump, self.b_jump]:
            pg.addWidget(w)
        pg.addStretch(1)
        right.addLayout(pg)

        mid.addLayout(left, 0)
        mid.addLayout(right, 1)
        root.addLayout(mid)

        self.tabs.addTab(tab_ledger, "项目台账")

        # 第二页：工时填报
        self.wh_widget = WorkHoursWidget()
        self.tabs.addTab(self.wh_widget, "工时填报")

        self.statusBar().showMessage("就绪")

    # ---------------- 数据加载 ----------------
    def current_where(self):
        return build_where(self.filters)

    def refresh(self):
        where, params = self.current_where()
        conn = get_conn()
        total = conn.execute("SELECT COUNT(*) FROM projects" + where, params).fetchone()[0]
        order = f" ORDER BY {self.sort_col} {self.sort_dir}"
        offset = (self.page - 1) * self.page_size
        rows = conn.execute(
            "SELECT * FROM projects" + where + order + " LIMIT ? OFFSET ?",
            params + [self.page_size, offset],
        ).fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            cb = QTableWidgetItem()
            cb.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            cb.setCheckState(Qt.Checked if row["id"] in self.selected_ids else Qt.Unchecked)
            self.table.setItem(r, 0, cb)
            for c, key in enumerate(COL_KEYS):
                val = row[key]
                if key == "is_public":
                    val = "是" if val else "否"
                elif val is None:
                    val = ""
                item = QTableWidgetItem(str(val))
                if key == "is_public":
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c + 1, item)
            self.table.setRowHeight(r, 26)
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, 36)

        # 分页信息
        pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.page > pages:
            self.page = pages
        self.lbl_total.setText(f"共 {total} 条")
        self.lbl_page.setText(f"第 {self.page}/{pages} 页")
        self._rows = rows

    # ---------------- 交互 ----------------
    def on_header_click(self, idx):
        if idx == 0:
            return
        col = SORT_COL_MAP.get(idx, "id")
        if self.sort_col == col:
            self.sort_dir = "DESC" if self.sort_dir == "ASC" else "ASC"
        else:
            self.sort_col = col
            self.sort_dir = "ASC"
        self.refresh()

    def on_cell_click(self, row, col):
        if col == 0:
            item = self.table.item(row, 0)
            rid = self._rows[row]["id"]
            if item.checkState() == Qt.Checked:
                self.selected_ids.add(rid)
            else:
                self.selected_ids.discard(rid)

    def do_quick(self):
        q = self.quick.text().strip()
        self.filters = {"q": q} if q else {}
        self.page = 1
        self.refresh()

    def do_advanced(self):
        self.filters = {
            "name": self.f_name.text().strip(),
            "code": self.f_code.text().strip(),
            "leader": self.f_leader.text().strip(),
            "attribution": self.f_attr.text().strip(),
            "creator": self.f_creator.text().strip(),
            "status": self.f_status.currentText(),
            "category": self.f_cat.currentText(),
            "is_public": self.f_pub.currentText(),
            "min_eng": self.f_meng.text().strip(),
            "min_fee": self.f_mfee.text().strip(),
        }
        self.page = 1
        self.refresh()

    def reset_adv(self):
        for w in [self.f_name, self.f_code, self.f_leader, self.f_attr,
                  self.f_creator, self.f_meng, self.f_mfee]:
            w.clear()
        self.f_status.setCurrentIndex(0)
        self.f_cat.setCurrentIndex(0)
        self.f_pub.setCurrentIndex(0)

    def apply_preset(self, idx):
        self.preset_list.selectRow(idx)
        label, f = PRESETS[idx]
        self.filters = dict(f)
        self.quick.clear()
        self.reset_adv()
        # 把预设条件回填到高级搜索框（便于可见）
        if "is_public" in f:
            self.f_pub.setCurrentText(f["is_public"])
        if "status" in f:
            self.f_status.setCurrentText(f["status"])
        if "min_eng" in f:
            self.f_meng.setText(str(f["min_eng"]))
        self.page = 1
        self.refresh()

    def change_page_size(self, txt):
        self.page_size = int(txt)
        self.page = 1
        self.refresh()

    def goto_page(self, p):
        self.page = max(1, p)
        self.refresh()

    def goto_last(self):
        where, params = self.current_where()
        conn = get_conn()
        total = conn.execute("SELECT COUNT(*) FROM projects" + where, params).fetchone()[0]
        conn.close()
        pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.goto_page(pages)

    def do_jump(self):
        try:
            p = int(self.jump.text().strip())
            self.goto_page(p)
        except ValueError:
            pass

    # ---------------- CRUD ----------------
    def add_record(self):
        dlg = EditDialog(self)
        if dlg.exec() == QDialog.Accepted:
            d = dlg.data()
            if not d["code"] or not d["name"]:
                QMessageBox.warning(self, "提示", "项目编号与名称为必填项")
                return
            conn = get_conn()
            conn.execute(
                "INSERT INTO projects (code,name,eng_cost,design_fee,leader,status,"
                "is_public,display_order,attribution,category,creator) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (d["code"], d["name"], d["eng_cost"], d["design_fee"], d["leader"],
                 d["status"], d["is_public"], d["display_order"], d["attribution"],
                 d["category"], d["creator"]),
            )
            conn.commit(); conn.close()
            self.refresh()

    def delete_selected(self):
        if not self.selected_ids:
            QMessageBox.information(self, "提示", "请先勾选要删除的行")
            return
        n = len(self.selected_ids)
        if QMessageBox.question(self, "确认", f"确定删除选中的 {n} 条记录？") == QMessageBox.Yes:
            conn = get_conn()
            conn.execute("DELETE FROM projects WHERE id IN (%s)" %
                         ",".join("?" * n), list(self.selected_ids))
            conn.commit(); conn.close()
            self.selected_ids.clear()
            self.refresh()

    def batch_share(self):
        if not self.selected_ids:
            QMessageBox.information(self, "提示", "请先勾选要共享的行")
            return
        conn = get_conn()
        rows = conn.execute("SELECT * FROM projects WHERE id IN (%s)" %
                           ",".join("?" * len(self.selected_ids)),
                           list(self.selected_ids)).fetchall()
        conn.close()
        data = [dict(r) for r in rows]
        path, _ = QFileDialog.getSaveFileName(
            self, "保存共享包", os.path.join(APP_DIR, f"共享导出_{datetime.now():%Y%m%d_%H%M%S}.json"),
            "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "完成", f"已将 {len(data)} 条记录导出为共享包：\n{path}")

    def export_csv(self):
        where, params = self.current_where()
        order = f" ORDER BY {self.sort_col} {self.sort_dir}"
        conn = get_conn()
        rows = conn.execute("SELECT * FROM projects" + where + order, params).fetchall()
        conn.close()
        path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", os.path.join(APP_DIR, "项目台账导出.csv"), "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(COL_HEADERS[1:])
            for r in rows:
                line = []
                for key in COL_KEYS:
                    v = r[key]
                    if key == "is_public":
                        v = "是" if v else "否"
                    line.append("" if v is None else v)
                w.writerow(line)
        QMessageBox.information(self, "完成", f"已导出 {len(rows)} 条到：\n{path}")

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入CSV", APP_DIR, "CSV (*.csv)")
        if not path:
            return
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return
            # 表头中文 -> 列键
            hmap = {COLUMNS[i][1]: COLUMNS[i][0] for i in range(len(COLUMNS))}
            idx = {hmap.get(h.strip(), None): i for i, h in enumerate(header)}
            conn = get_conn()
            cnt = 0
            for row in reader:
                if not row or not any(row):
                    continue
                vals = {}
                for key in COL_KEYS:
                    ci = idx.get(key)
                    raw = row[ci].strip() if (ci is not None and ci < len(row)) else ""
                    if key in ("eng_cost", "design_fee"):
                        try: vals[key] = float(raw) if raw else 0.0
                        except ValueError: vals[key] = 0.0
                    elif key == "is_public":
                        vals[key] = 1 if raw in ("是", "1", "true", "True") else 0
                    elif key == "display_order":
                        try: vals[key] = int(raw) if raw else 0
                        except ValueError: vals[key] = 0
                    else:
                        vals[key] = raw
                if not vals.get("code") or not vals.get("name"):
                    continue
                conn.execute(
                    "INSERT INTO projects (code,name,eng_cost,design_fee,leader,status,"
                    "is_public,display_order,attribution,category,creator) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (vals["code"], vals["name"], vals["eng_cost"], vals["design_fee"],
                     vals["leader"], vals["status"], vals["is_public"],
                     vals["display_order"], vals["attribution"], vals["category"], vals["creator"]),
                )
                cnt += 1
            conn.commit(); conn.close()
        QMessageBox.information(self, "完成", f"成功导入 {cnt} 条记录")
        self.refresh()

    # ---------------- 模板 ----------------
    def load_templates(self):
        conn = get_conn()
        rows = conn.execute("SELECT id,name FROM search_templates ORDER BY id").fetchall()
        conn.close()
        self._tpls = {r["name"]: r["filters"] for r in rows}
        self.tpl_combo.clear()
        self.tpl_combo.addItem("（加载模板）")
        for name in self._tpls:
            self.tpl_combo.addItem(name)

    def save_template(self):
        name, ok = QInputDialog.getText(self, "存为模板", "模板名称：")
        if not ok or not name.strip():
            return
        self.do_advanced()
        conn = get_conn()
        conn.execute("INSERT INTO search_templates (name,filters) VALUES (?,?)",
                     (name.strip(), json.dumps(self.filters, ensure_ascii=False)))
        conn.commit(); conn.close()
        self.load_templates()
        QMessageBox.information(self, "完成", f"模板「{name.strip()}」已保存")

    def load_template(self):
        name = self.tpl_combo.currentText()
        if name == "（加载模板）" or name not in self._tpls:
            return
        self.filters = json.loads(self._tpls[name])
        # 回填
        self.reset_adv()
        f = self.filters
        self.f_name.setText(f.get("name", ""))
        self.f_code.setText(f.get("code", ""))
        self.f_leader.setText(f.get("leader", ""))
        self.f_attr.setText(f.get("attribution", ""))
        self.f_creator.setText(f.get("creator", ""))
        if f.get("status"): self.f_status.setCurrentText(f["status"])
        if f.get("category"): self.f_cat.setCurrentText(f["category"])
        if f.get("is_public"): self.f_pub.setCurrentText(f["is_public"])
        self.f_meng.setText(str(f["min_eng"]) if f.get("min_eng") not in (None, "") else "")
        self.f_mfee.setText(str(f["min_fee"]) if f.get("min_fee") not in (None, "") else "")
        self.page = 1
        self.refresh()

    # ---------------- 帮助 ----------------
    def show_help(self):
        QMessageBox.information(
            self, "使用说明",
            "本程序是内网门户「工时管理→项目台账」的离线独立版，无需登录网页。\n\n"
            "【数据】首次运行自动在程序同目录生成 project_ledger.db 并写入样本数据。\n"
            "【搜索】顶部快速搜索按 名称/编号/负责人；「高级搜索」可多条件组合，并可「存为模板」复用。\n"
            "【视图】左侧 5 个预设对应网页左侧 5 个图标子菜单（网页无文字标签），此处给出可读筛选。\n"
            "【编辑】「新增」录入；在表格行首勾选后，「删除」可批量删、「批量共享」导出选中为 JSON 共享包。\n"
            "【导入】从网页导出 CSV 后，用「导入」一次性载入真实 487 条，之后完全离线操作。\n"
            "【导出】「导出」把当前筛选结果存为 CSV（Excel 直接打开，中文不乱码）。\n"
            "【排序】点击列头排序；【分页】右下角切换每页条数与页码。\n\n"
            "数据文件 project_ledger.db 与程序同目录，备份/迁移时一起拷贝即可。"
        )


# ----------------------------------------------------------------------------
def main():
    init_db()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
