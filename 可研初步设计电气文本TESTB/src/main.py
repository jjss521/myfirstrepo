#!/usr/bin/env python3
"""
市政工程电气自控设计说明书生成器 - 桌面应用

基于 ttkbootstrap，提供：
  1. 项目信息配置
  2. 负荷计算Excel导入
  3. 设计文档Word生成
  4. 知识库浏览
  5. 系统健康检查
"""
import os
import sys
import json
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# 确保 src/core 在 sys.path
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox, Querybox

from core.engine import GenerateEngine

# ── 常量 ──
APP_TITLE = '市政工程电气自控设计说明书生成器'
APP_VERSION = '1.0.0'
DEBUG = os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes')
PROJECT_TYPES = [
    ('water_supply', '给水工程'),
    ('drainage', '排水工程'),
    ('road', '道路工程'),
    ('sanitation', '环卫工程'),
]
DESIGN_STAGES = ['可行性研究', '初步设计']
VOLTAGE_LEVELS = ['10kV', '35kV', '0.4kV', '6kV']
LOAD_LEVELS = ['一级', '二级', '三级']

DEFAULT_PARAMS = {
    'project_name': '',
    'project_type': 'water_supply',
    'design_stage': '初步设计',
    'voltage_level': '10kV',
    'load_level': '二级',
    'power_source': '一路',
    'standby_desc': '',
    'tx_config': '',
    'tx_count': '1',
    'tx_location': '变配电间内',
}


class EngineContext:
    """全局引擎上下文 - 持有引擎和当前数据"""

    def __init__(self):
        project_root = os.path.dirname(_SRC_DIR)
        self.engine = GenerateEngine(project_root)
        self.excel_data = None
        self.excel_path = ''
        self.last_output_path = ''

    def health_status(self) -> Dict[str, Any]:
        return self.engine.health_check()

    def is_healthy(self) -> bool:
        return self.engine.health_check()['all_pass']


# ── 主应用 ──

class App(ttk.Window):
    """主应用窗口"""

    def __init__(self):
        super().__init__(title=APP_TITLE, themename='cosmo')
        self.ctx = EngineContext()

        # 窗口设置
        self.geometry('1280x860')
        self.minsize(1024, 700)

        # 状态栏变量
        self.status_var = ttk.StringVar(value='就绪')
        self.health_var = ttk.StringVar(value='⚪ 检查中...')

        self._build_ui()
        self._check_health()

    # ── UI 构建 ──

    def _build_ui(self):
        """构建完整UI"""
        # 顶部标题
        header = ttk.Frame(self, padding=(20, 10))
        header.pack(fill=X)

        ttk.Label(
            header, text=APP_TITLE,
            font=('黑体', 20, 'bold'),
        ).pack(side=LEFT)
        ttk.Label(
            header, text=f'v{APP_VERSION}',
            font=('', 10),
            foreground='gray',
        ).pack(side=LEFT, padx=(8, 0))

        # 分隔线
        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, padx=10)

        # 主选项卡
        notebook = ttk.Notebook(self, padding=10)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=(5, 0))

        self.tab_project = ProjectTab(notebook, self.ctx)
        self.tab_excel = ExcelTab(notebook, self.ctx)
        self.tab_generate = GenerateTab(notebook, self.ctx)
        self.tab_rules = RulesTab(notebook, self.ctx)
        self.tab_about = AboutTab(notebook, self.ctx)

        notebook.add(self.tab_project, text='📋 项目信息')
        notebook.add(self.tab_excel, text='📊 Excel导入')
        notebook.add(self.tab_generate, text='📄 生成文档')
        notebook.add(self.tab_rules, text='📚 知识库')
        notebook.add(self.tab_about, text='ℹ️ 关于')

        # 绑定切换事件 - 刷新右侧标签
        notebook.bind('<<NotebookTabChanged>>', self._on_tab_change)
        self._notebook = notebook

        # 状态栏
        self._build_statusbar()

    def _build_statusbar(self):
        """底部状态栏"""
        status_frame = ttk.Frame(self, padding=(10, 3))
        status_frame.pack(fill=X, side=BOTTOM)
        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, side=BOTTOM, padx=10)

        inner = ttk.Frame(status_frame)
        inner.pack(fill=X)

        ttk.Label(inner, textvariable=self.status_var, font=('', 9)).pack(side=LEFT)
        ttk.Label(inner, textvariable=self.health_var, font=('', 9)).pack(side=RIGHT)

    def _on_tab_change(self, event=None):
        """标签页切换时刷新"""
        current = self._notebook.index(self._notebook.select())
        if current == 3:  # 知识库
            self.tab_rules.refresh()
        elif current == 4:  # 关于
            self.tab_about.refresh()

    def _check_health(self):
        """异步检查系统健康"""
        def check():
            status = self.ctx.health_status()
            if status['all_pass']:
                self.health_var.set('✅ 系统正常')
            else:
                fails = [m for _, m in status['checks'] if '❌' in m]
                self.health_var.set(f'⚠️ {" / ".join(fails[:2])}')
            self.update_idletasks()

        threading.Thread(target=check, daemon=True).start()


# ── 选项卡 1: 项目信息 ──

class ProjectTab(ttk.Frame):
    """项目信息配置"""

    def __init__(self, parent, ctx: EngineContext):
        super().__init__(parent)
        self.ctx = ctx
        self.params = dict(DEFAULT_PARAMS)
        self._build()

    def _build(self):
        # 分两列布局
        left = ttk.Frame(self)
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        right = ttk.Frame(self)
        right.pack(side=LEFT, fill=BOTH, expand=True)

        # ── 左侧: 基本信息 ──
        ttk.Label(left, text='项目基本信息', font=('黑体', 14, 'bold')).pack(anchor=W)
        ttk.Separator(left, orient=HORIZONTAL).pack(fill=X, pady=(5, 15))

        # 工程名称
        ttk.Label(left, text='工程名称 *', font=('', 10)).pack(anchor=W)
        self.entry_name = ttk.Entry(left, font=('', 12))
        self.entry_name.pack(fill=X, pady=(0, 12))
        self.entry_name.insert(0, '示例工程')

        # 工程类型
        ttk.Label(left, text='工程类型 *', font=('', 10)).pack(anchor=W)
        self.type_var = ttk.StringVar(value='给水工程')
        self.type_combo = ttk.Combobox(
            left, textvariable=self.type_var,
            values=[label for _, label in PROJECT_TYPES],
            state='readonly', font=('', 11),
        )
        self.type_combo.pack(fill=X, pady=(0, 12))
        self.type_combo.bind('<<ComboboxSelected>>', self._on_type_change)

        # 设计阶段
        ttk.Label(left, text='设计阶段 *', font=('', 10)).pack(anchor=W)
        self.stage_var = ttk.StringVar(value='初步设计')
        ttk.Combobox(
            left, textvariable=self.stage_var,
            values=DESIGN_STAGES, state='readonly', font=('', 11),
        ).pack(fill=X, pady=(0, 12))

        # 编制日期
        ttk.Label(left, text='编制日期', font=('', 10)).pack(anchor=W)
        date_frame = ttk.Frame(left)
        date_frame.pack(fill=X, pady=(0, 12))
        today = datetime.now().strftime('%Y年%m月%d日')
        self.date_var = ttk.StringVar(value=today)
        ttk.Entry(date_frame, textvariable=self.date_var, font=('', 11), width=15).pack(side=LEFT)
        ttk.Button(date_frame, text='今天', command=lambda: self.date_var.set(today), width=6).pack(side=LEFT, padx=(5, 0))

        # 空行
        ttk.Label(left, text='', font=('', 5)).pack()

        # ── 右侧: 电气参数 ──
        ttk.Label(right, text='电气配置参数', font=('黑体', 14, 'bold')).pack(anchor=W)
        ttk.Separator(right, orient=HORIZONTAL).pack(fill=X, pady=(5, 15))

        # 电压等级
        ttk.Label(right, text='供电电压等级', font=('', 10)).pack(anchor=W)
        self.voltage_var = ttk.StringVar(value='10kV')
        ttk.Combobox(
            right, textvariable=self.voltage_var,
            values=VOLTAGE_LEVELS, state='readonly', font=('', 11),
        ).pack(fill=X, pady=(0, 12))

        # 用电负荷等级
        ttk.Label(right, text='用电负荷等级', font=('', 10)).pack(anchor=W)
        self.load_var = ttk.StringVar(value='二级')
        ttk.Combobox(
            right, textvariable=self.load_var,
            values=LOAD_LEVELS, state='readonly', font=('', 11),
        ).pack(fill=X, pady=(0, 12))

        # 电源配置
        ttk.Label(right, text='电源回路数', font=('', 10)).pack(anchor=W)
        power_frame = ttk.Frame(right)
        power_frame.pack(fill=X, pady=(0, 5))
        self.ps_var = ttk.StringVar(value='一路')
        ttk.Radiobutton(power_frame, text='一路', variable=self.ps_var, value='一路').pack(side=LEFT, padx=(0, 20))
        ttk.Radiobutton(power_frame, text='两路', variable=self.ps_var, value='两路').pack(side=LEFT)

        # 备用说明
        ttk.Label(right, text='备用电源说明', font=('', 10)).pack(anchor=W)
        self.standby_text = ttk.Text(right, height=3, font=('', 10))
        self.standby_text.pack(fill=X, pady=(0, 5))
        self.standby_text.insert('1.0', '当一路电源故障时，另一路可承担全部负荷。')

        # 变配电间位置
        ttk.Label(right, text='变配电间位置', font=('', 10)).pack(anchor=W)
        self.tx_loc_var = ttk.StringVar(value='变配电间内')
        ttk.Entry(right, textvariable=self.tx_loc_var, font=('', 11)).pack(fill=X, pady=(0, 12))

        # 保存按钮
        ttk.Label(right, text='', font=('', 5)).pack()
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill=X, pady=(10, 0))
        ttk.Button(
            btn_frame, text='💾 保存项目信息',
            bootstyle=SUCCESS, command=self.save_params, width=20,
        ).pack(side=RIGHT)

    def _on_type_change(self, event=None):
        """工程类型切换时联动设计阶段"""
        label = self.type_var.get()
        for code, lbl in PROJECT_TYPES:
            if lbl == label:
                rule = self.ctx.engine.load_rule(code)
                if rule:
                    stage = rule.get('design_stage', '初步设计')
                    self.stage_var.set(stage)
                break

    def save_params(self):
        """保存参数到上下文"""
        label = self.type_var.get()
        project_type = 'water_supply'
        for code, lbl in PROJECT_TYPES:
            if lbl == label:
                project_type = code
                break

        self.params.update({
            'project_name': self.entry_name.get().strip(),
            'project_type': project_type,
            'design_stage': self.stage_var.get(),
            'voltage_level': self.voltage_var.get(),
            'load_level': self.load_var.get(),
            'power_source': self.ps_var.get(),
            'standby_desc': self.standby_text.get('1.0', 'end-1c').strip(),
            'tx_location': self.tx_loc_var.get().strip(),
        })
        Messagebox.show_info('项目信息已保存', '保存成功')

    def get_params(self) -> Dict[str, Any]:
        """获取当前参数"""
        self.save_params()
        return self.params


# ── 选项卡 2: Excel导入 ──

class ExcelTab(ttk.Frame):
    """Excel负荷计算导入"""

    def __init__(self, parent, ctx: EngineContext):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        # 顶部操作栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, pady=(0, 15))

        ttk.Label(toolbar, text='导入负荷计算表', font=('黑体', 14, 'bold')).pack(side=LEFT)
        ttk.Button(
            toolbar, text='📂 选择Excel文件',
            bootstyle=INFO, command=self._select_file, width=18,
        ).pack(side=RIGHT, padx=(10, 0))
        ttk.Button(
            toolbar, text='🔄 解析并预览',
            bootstyle=SECONDARY, command=self._parse_excel, width=14,
        ).pack(side=RIGHT, padx=(10, 0))

        # 当前文件标签
        self.file_label = ttk.Label(self, text='未选择文件', font=('', 9), foreground='gray')
        self.file_label.pack(anchor=W, pady=(0, 10))

        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=(0, 10))

        # 结果展示区域
        self._build_detail_area()

    def _build_detail_area(self):
        """解析结果区域"""
        # 使用 PanedWindow 分割
        paned = ttk.PanedWindow(self, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True)

        # 上方: 汇总卡片
        self.summary_frame = ttk.LabelFrame(paned, text='计算汇总', padding=10)
        paned.add(self.summary_frame, weight=1)
        self.summary_text = ttk.Text(self.summary_frame, height=6, font=('Consolas', 10), state=DISABLED)
        self.summary_text.pack(fill=BOTH, expand=True)

        # 下方: 区域明细
        self.areas_frame = ttk.LabelFrame(paned, text='各区域负荷明细', padding=10)
        paned.add(self.areas_frame, weight=2)

        # 树形表格
        columns = ('area', 'devices', 'power', 'pc', 'qc', 'sc')
        self.tree = ttk.Treeview(
            self.areas_frame, columns=columns, show='headings',
            height=8,
        )
        self.tree.heading('area', text='区域名称')
        self.tree.heading('devices', text='设备数')
        self.tree.heading('power', text='设备容量(kW)')
        self.tree.heading('pc', text='有功(kW)')
        self.tree.heading('qc', text='无功(kvar)')
        self.tree.heading('sc', text='视在(kVA)')
        self.tree.column('area', width=160)
        self.tree.column('devices', width=80, anchor=CENTER)
        self.tree.column('power', width=120, anchor=E)
        self.tree.column('pc', width=120, anchor=E)
        self.tree.column('qc', width=120, anchor=E)
        self.tree.column('sc', width=120, anchor=E)

        vsb = ttk.Scrollbar(self.areas_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

    def _select_file(self):
        """选择Excel文件"""
        from tkinter.filedialog import askopenfilename
        path = askopenfilename(
            title='选择负荷计算Excel文件',
            filetypes=[('Excel文件', '*.xlsx *.xls'), ('所有文件', '*.*')],
        )
        if path:
            self.ctx.excel_path = path
            self.file_label.config(text=f'📄 {path}', foreground='black')
            self.ctx.excel_data = None
            # 自动解析
            self._parse_excel()

    def _parse_excel(self):
        """解析Excel并在UI中显示"""
        if not self.ctx.excel_path:
            Messagebox.show_warning('请先选择Excel文件', '提示')
            return

        self._set_loading(True)

        def task():
            try:
                data = self.ctx.engine.parse_excel(self.ctx.excel_path)
                self.ctx.excel_data = data
                self.after(0, self._display_result, data)
            except Exception as e:
                self.after(0, Messagebox.show_error, f'解析失败：{e}', '错误')
                self.after(0, self._set_loading, False)

        threading.Thread(target=task, daemon=True).start()

    def _display_result(self, data: Dict[str, Any]):
        """显示解析结果"""
        summary = data.get('summary', {})
        self._set_loading(False)

        # 更新汇总
        self.summary_text.config(state=NORMAL)
        self.summary_text.delete('1.0', END)
        self.summary_text.insert(END, json.dumps(
            {k: v for k, v in summary.items()
             if k not in ('detailed_areas', 'all_devices_data')},
            ensure_ascii=False, indent=2,
        ))
        self.summary_text.config(state=DISABLED)

        # 更新区域列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        for area, info in data.get('area_summaries', {}).items():
            self.tree.insert('', END, values=(
                area,
                info.get('device_count', 0),
                f"{info.get('equip_power', 0):.1f}",
                f"{info.get('pc', 0):.1f}",
                f"{info.get('qc', 0):.1f}",
                f"{info.get('sc', 0):.1f}",
            ))

        # 汇总行
        self.tree.insert('', END, values=(
            '合计',
            summary.get('total_devices', 0),
            f"{summary.get('total_equip_power', 0):.1f}",
            f"{summary.get('total_pc', 0):.1f}",
            f"{summary.get('total_qc', 0):.1f}",
            f"{summary.get('total_sc', 0):.1f}",
        ))

        self.ctx.status_var.set(f'已解析：{os.path.basename(self.ctx.excel_path)}')

    def _set_loading(self, loading: bool):
        """设置加载状态"""
        self.ctx.status_var.set('正在解析Excel...' if loading else '就绪')
        self.update_idletasks()


# ── 选项卡 3: 生成文档 ──

class GenerateTab(ttk.Frame):
    """文档生成"""

    def __init__(self, parent, ctx: EngineContext):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        # 标题
        title_bar = ttk.Frame(self)
        title_bar.pack(fill=X, pady=(0, 15))
        ttk.Label(title_bar, text='生成设计说明书', font=('黑体', 14, 'bold')).pack(side=LEFT)
        ttk.Label(title_bar, text='', font=('', 5)).pack()

        # 主区域: 左中右
        main = ttk.Frame(self)
        main.pack(fill=BOTH, expand=True)

        # ── 左侧: 配置摘要 ──
        left = ttk.LabelFrame(main, text='当前配置', padding=10)
        left.pack(side=LEFT, fill=BOTH, expand=False, padx=(0, 10))

        self.config_text = ttk.Text(left, width=32, height=18, font=('Consolas', 9), state=DISABLED)
        self.config_text.pack(fill=BOTH, expand=True)

        # ── 中间: 进度区域 ──
        center = ttk.Frame(main)
        center.pack(side=LEFT, fill=BOTH, expand=True)

        # 生成按钮
        gen_frame = ttk.Frame(center)
        gen_frame.pack(fill=X, pady=(10, 15))

        self.gen_btn = ttk.Button(
            gen_frame, text='📝 生成Word文档',
            bootstyle=SUCCESS, command=self._generate, width=22,
        )
        self.gen_btn.pack(side=LEFT, padx=(0, 10))

        self.open_btn = ttk.Button(
            gen_frame, text='📂 打开输出文件夹',
            bootstyle=SECONDARY, command=self._open_output, width=18,
        )
        self.open_btn.pack(side=LEFT)

        # 进度条
        self.progress = ttk.Progressbar(center, mode=INDETERMINATE, length=400)
        self.progress.pack(fill=X, pady=(0, 10))

        # 日志输出
        log_frame = ttk.LabelFrame(center, text='生成日志', padding=5)
        log_frame.pack(fill=BOTH, expand=True)

        self.log_text = ttk.Text(log_frame, font=('Consolas', 10), state=DISABLED, wrap=WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        log_scroll.pack(side=RIGHT, fill=Y)

        # 生成后显示路径
        self.path_var = ttk.StringVar(value='')

        # ── 右侧: 快速提示 ──
        right = ttk.LabelFrame(main, text='生成步骤', padding=10)
        right.pack(side=LEFT, fill=BOTH, expand=False, padx=(10, 0))

        steps = [
            '1️⃣ 填写项目信息',
            '2️⃣ 导入负荷计算Excel',
            '3️⃣ 点击"生成Word文档"',
            '4️⃣ 打开输出文件夹查看',
            '',
            '生成内容：',
            '✨ 封面页',
            '✨ 编制依据',
            '✨ 电气设计说明（逐栏目）',
            '✨ 自控设计说明（逐栏目）',
            '✨ 负荷计算表',
            '✨ 设备材料表',
            '',
            '📌 确保Excel文件已解析',
            '📌 确保项目信息已保存',
        ]
        for s in steps:
            ttk.Label(right, text=s, font=('', 9)).pack(anchor=W, pady=1)

    def _refresh_config(self):
        """刷新配置摘要"""
        params = self.ctx.tab_project.get_params() if hasattr(self.ctx, 'tab_project') else DEFAULT_PARAMS
        self.config_text.config(state=NORMAL)
        self.config_text.delete('1.0', END)
        text = (
            f'项目名称: {params.get("project_name", "-")}\n'
            f'工程类型: {params.get("project_type", "-")}\n'
            f'设计阶段: {params.get("design_stage", "-")}\n'
            f'电压等级: {params.get("voltage_level", "-")}\n'
            f'负荷等级: {params.get("load_level", "-")}\n'
            f'电源回路: {params.get("power_source", "-")}\n'
            f'备用说明: {params.get("standby_desc", "-")}\n'
            f'变配电间: {params.get("tx_location", "-")}\n'
            f'\n--- Excel数据 ---\n'
            f'文件: {"✅ 已加载" if self.ctx.excel_data else "❌ 未选择"}\n'
        )
        if self.ctx.excel_data:
            s = self.ctx.excel_data.get('summary', {})
            text += (
                f'设备总数: {s.get("total_devices", 0)}\n'
                f'总容量: {s.get("total_equip_power", 0):.1f} kW\n'
                f'计算负荷: {s.get("total_sc_k", 0):.1f} kVA\n'
                f'变压器: {s.get("recommended_transformer", "-")}\n'
            )
        self.config_text.insert('1.0', text)
        self.config_text.config(state=DISABLED)

    def _log(self, msg: str):
        """追加日志"""
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, f'[{datetime.now().strftime("%H:%M:%S")}] {msg}\n')
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)
        self.ctx.status_var.set(msg)

    def _generate(self):
        """生成Word文档"""
        if not self.ctx.excel_data:
            Messagebox.show_warning('请先在"Excel导入"标签页中选择并解析Excel文件', '缺少数据')
            return

        params = self.ctx.tab_project.get_params() if hasattr(self.ctx, 'tab_project') else DEFAULT_PARAMS

        # 开始
        self.gen_btn.config(state=DISABLED, text='⏳ 生成中...')
        self.progress.start()
        self._log('🚀 开始生成文档...')
        self._log(f'   工程类型: {params["project_type"]}')
        self._log(f'   设计阶段: {params["design_stage"]}')
        self._log(f'   项目名称: {params["project_name"]}')

        def task():
            try:
                output_path = self.ctx.engine.generate(
                    project_type=params['project_type'],
                    design_stage=params['design_stage'],
                    excel_data=self.ctx.excel_data,
                    params=params,
                )
                self.ctx.last_output_path = output_path
                self.after(0, self._on_success, output_path)
            except Exception as e:
                tb = traceback.format_exc()
                self.after(0, self._on_error, str(e), tb)

        threading.Thread(target=task, daemon=True).start()

    def _on_success(self, path: str):
        """生成成功"""
        self.progress.stop()
        self.gen_btn.config(state=NORMAL, text='📝 生成Word文档')
        self._log(f'✅ 文档生成成功！')
        self._log(f'   输出路径: {path}')
        self.path_var.set(path)
        Messagebox.show_info(f'文档已生成：\n{path}', '生成成功')
        self.ctx.status_var.set(f'已生成：{os.path.basename(path)}')

    def _on_error(self, err: str, tb: str):
        """生成失败"""
        self.progress.stop()
        self.gen_btn.config(state=NORMAL, text='📝 生成Word文档')
        self._log(f'❌ 生成失败: {err}')
        if DEBUG:
            for line in tb.split('\n')[-10:]:
                self._log(f'   {line}')
        Messagebox.show_error(f'生成失败：{err}', '错误')

    @staticmethod
    def _open_output():
        """打开输出文件夹"""
        output_dir = os.path.join(os.path.dirname(_SRC_DIR), 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        os.startfile(output_dir)


# ── 选项卡 4: 知识库 ──

class RulesTab(ttk.Frame):
    """知识库 - 规则浏览器"""

    def __init__(self, parent, ctx: EngineContext):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        # 选择器
        top = ttk.Frame(self)
        top.pack(fill=X, pady=(0, 15))
        ttk.Label(top, text='规范深度要求 - 知识库', font=('黑体', 14, 'bold')).pack(side=LEFT)
        self.type_filter_var = ttk.StringVar(value='全部')
        ttk.Combobox(
            top, textvariable=self.type_filter_var,
            values=['全部'] + [lbl for _, lbl in PROJECT_TYPES],
            state='readonly', width=15, font=('', 10),
        ).pack(side=RIGHT)
        ttk.Label(top, text='筛选工程类型：', font=('', 10)).pack(side=RIGHT, padx=(0, 5))

        # 主区域: 列表 + 详情
        main = ttk.Frame(self)
        main.pack(fill=BOTH, expand=True)

        # 左侧: 规则条目列表
        left = ttk.LabelFrame(main, text='条目列表', padding=5)
        left.pack(side=LEFT, fill=BOTH, expand=False, padx=(0, 10))

        self.listbox = ttk.Treeview(
            left, columns=('type', 'section', 'title', 'calc'),
            show='headings', height=20,
        )
        self.listbox.heading('type', text='工程类型')
        self.listbox.heading('section', text='章节')
        self.listbox.heading('title', text='条目名称')
        self.listbox.heading('calc', text='含计算')
        self.listbox.column('type', width=80)
        self.listbox.column('section', width=60, anchor=CENTER)
        self.listbox.column('title', width=200)
        self.listbox.column('calc', width=60, anchor=CENTER)
        self.listbox.bind('<<TreeviewSelect>>', self._on_select)

        vsb = ttk.Scrollbar(left, orient=VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=vsb.set)
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        # 右侧: 详情
        right = ttk.LabelFrame(main, text='详细要求', padding=10)
        right.pack(side=LEFT, fill=BOTH, expand=True)

        self.detail_title = ttk.Label(right, text='选择一个条目查看详情', font=('', 12))
        self.detail_title.pack(anchor=W)

        self.detail_text = ttk.Text(right, font=('', 10), height=15, state=DISABLED, wrap=WORD)
        self.detail_text.pack(fill=BOTH, expand=True, pady=(10, 0))

    def refresh(self):
        """刷新列表"""
        filter_val = self.type_filter_var.get()
        for item in self.listbox.get_children():
            self.listbox.delete(item)

        for code, label in PROJECT_TYPES:
            if filter_val != '全部' and label != filter_val:
                continue
            rule = self.ctx.engine.load_rule(code)
            if not rule:
                continue
            for stage_name, stage_data in rule.get('design_stages', {}).items():
                # 环卫工程(sanitation)使用嵌套 sections 结构
                categories = stage_data.get('sections', stage_data) if isinstance(stage_data, dict) else {}
                for cat_key, cat_data in GenerateEngine._iter_categories(categories):
                    section = cat_data.get('section_id', '')
                    for item in cat_data.get('items', []):
                        calc_mark = '✅' if item.get('has_calculation') else ''
                        self.listbox.insert('', END, values=(
                            label, section, item['title'], calc_mark,
                        ), tags=(code, stage_name, cat_key, str(item.get('order', ''))))

    def _on_select(self, event):
        """选择条目后显示详情"""
        sel = self.listbox.selection()
        if not sel:
            return
        values = self.listbox.item(sel[0], 'values')
        tags = self.listbox.item(sel[0], 'tags')
        if len(tags) < 3:
            return

        code, stage_name, cat_key, order_str = tags
        rule = self.ctx.engine.load_rule(code)
        if not rule:
            return

        stage_data = rule.get('design_stages', {}).get(stage_name, {})
        categories = stage_data.get('sections', stage_data) if isinstance(stage_data, dict) else {}
        cat_data = categories.get(cat_key, {})
        for item in cat_data.get('items', []):
            if str(item.get('order', '')) == order_str:
                # 显示详情
                self.detail_title.config(
                    text=f'{rule["project_type"]} → {cat_data["title"]} → {item["title"]}'
                )
                requirement = item.get('requirement', '无具体要求')
                calc = '是' if item.get('has_calculation') else '否'
                table = '需要' if item.get('table_required') else '不需要'
                calc_from = '来自Excel' if item.get('calc_from_excel') else '直接生成'

                detail = (
                    f'📋 要求：{requirement}\n\n'
                    f'📌 含计算：{calc}\n'
                    f'📊 需要表格：{table}\n'
                    f'🔄 计算来源：{calc_from}\n'
                    f'📖 章节编号：{cat_data.get("section_id", "")}\n'
                    f'🏗️ 工程类型：{rule["project_type"]}'
                )
                self.detail_text.config(state=NORMAL)
                self.detail_text.delete('1.0', END)
                self.detail_text.insert('1.0', detail)
                self.detail_text.config(state=DISABLED)
                break


# ── 选项卡 5: 关于 ──

class AboutTab(ttk.Frame):
    """关于页面"""

    def __init__(self, parent, ctx: EngineContext):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        content = ttk.Frame(self)
        content.pack(expand=True)

        # 应用信息
        ttk.Label(content, text=APP_TITLE, font=('黑体', 22, 'bold')).pack(pady=(40, 5))
        ttk.Label(content, text=f'版本 {APP_VERSION}', font=('', 12), foreground='gray').pack()
        ttk.Label(content, text='', font=('', 5)).pack()

        desc = ('基于《市政公用工程设计文件编制深度规定》（2025年版）\n'
                '自动生成工程电气及自控设计说明书Word文档')
        ttk.Label(content, text=desc, font=('', 11), justify=CENTER).pack(pady=10)

        # 系统状态面板
        status_frame = ttk.LabelFrame(content, text='系统状态', padding=15)
        status_frame.pack(fill=X, pady=20, padx=60)

        self.status_labels = {}
        checks = [
            ('规则文件', 'rules'),
            ('Excel解析器', 'excel'),
            ('Word生成器', 'docx'),
            ('python-docx', 'pydocx'),
            ('输出目录', 'output'),
        ]
        for label, key in checks:
            row = ttk.Frame(status_frame)
            row.pack(fill=X, pady=3)
            ttk.Label(row, text=label, width=20, anchor=W).pack(side=LEFT)
            lbl = ttk.Label(row, text='⚪ 检查中...', width=15)
            lbl.pack(side=RIGHT)
            self.status_labels[key] = lbl

    def refresh(self):
        """刷新系统状态"""
        def check():
            status = self.ctx.health_status()
            mapping = {
                'rules': '规则文件',
                'excel': 'Excel解析器',
                'docx': 'Word生成器',
                'pydocx': 'python-docx',
                'output': '输出目录',
            }
            for item_name, msg in status.get('checks', []):
                for key, label in mapping.items():
                    if label in item_name:
                        self.after(0, self.status_labels[key].config, {'text': msg})
                        break
        threading.Thread(target=check, daemon=True).start()


# ── 入口 ──

def main():
    """启动应用"""
    app = App()
    # 初始刷新知识库
    app.after(500, app.tab_rules.refresh)
    app.after(500, app.tab_generate._refresh_config)
    app.mainloop()


if __name__ == '__main__':
    main()
