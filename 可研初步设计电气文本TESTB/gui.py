#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
市政工程设计文件电气自控生成器 — 桌面 GUI 版
双击运行，无需命令行，无需 Web 服务。

特性：
  * 选择工程类型 / 设计阶段 / 文档模板
  * 一键生成 Word（四种排版模板）
  * 实时文档预览：切换模板/参数即时刷新，导出前确认内容与格式
依赖：tkinter(标准库) + openpyxl + xlrd + python-docx
启动：python gui.py
"""
import os
import sys
import threading

# ─── 启动自检 ───
def _check_deps():
    missing = []
    try:
        import tkinter as tk
    except ImportError:
        missing.append('tkinter (请安装完整版 Python)')
    try:
        import openpyxl
    except ImportError:
        missing.append('openpyxl (pip install openpyxl)')
    try:
        import xlrd
    except ImportError:
        missing.append('xlrd (pip install xlrd)')
    try:
        from docx import Document
    except ImportError:
        missing.append('python-docx (pip install python-docx)')
    if missing:
        msg = '缺少以下依赖包，请安装后重试：\n\n' + '\n'.join(f'  x {m}' for m in missing)
        msg += '\n\n安装命令：\n  pip install openpyxl xlrd python-docx'
        try:
            import tkinter.messagebox as mb
            mb.showerror('启动失败', msg)
        except Exception:
            print(msg)
        sys.exit(1)

_check_deps()

from tkinter import ttk, filedialog, messagebox, scrolledtext
import tkinter as tk
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from app.services.excel_parser import ExcelLoadParser
from app.services.docx_generator import DocxGenerator, TEMPLATES
from app.config import RULES_DIR, OUTPUT_DIR, PROJECT_TYPES


class App:
    WIDTH = 980
    HEIGHT = 640
    TITLE = '市政工程设计文件电气自控生成器'

    ENGINEERING_TYPES = [
        ('water_supply', '给水工程 — 净水厂/泵站'),
        ('drainage',    '排水工程 — 污水厂/泵站'),
        ('sanitation',  '环卫工程 — 垃圾焚烧/填埋/转运'),
        ('road',        '道路工程 — 城市道路/BRT'),
    ]
    DESIGN_STAGES = ['初步设计', '可研']
    LOAD_LEVELS = ['一级', '二级', '三级']

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.TITLE)
        self.root.geometry(f'{self.WIDTH}x{self.HEIGHT}')
        self.root.minsize(820, 560)
        self.root.resizable(True, True)

        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f'{self.WIDTH}x{self.HEIGHT}+{(sw-self.WIDTH)//2}+{(sh-self.HEIGHT)//2}')

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.COLOR_BG = '#f5f7fa'
        self.COLOR_PRIMARY = '#409EFF'
        self.COLOR_SUCCESS = '#67C23A'
        self.COLOR_WARNING = '#E6A23C'
        self.COLOR_DANGER = '#F56C6C'
        self.COLOR_TEXT = '#303133'
        self.COLOR_TEXT_SEC = '#909399'
        self.root.configure(bg=self.COLOR_BG)

        # 变量
        self.excel_var = tk.StringVar()
        self.type_var = tk.StringVar(value='water_supply')
        self.stage_var = tk.StringVar(value='初步设计')
        self.template_var = tk.StringVar(value='standard')
        self.name_var = tk.StringVar(value='')
        self.voltage_var = tk.StringVar(value='10kV')
        self.load_var = tk.StringVar(value='二级')
        self.status_var = tk.StringVar(value='就绪 — 请选择负荷计算 Excel 文件')

        self.output_path = None
        self.excel_data = None
        self.excel_summary = None

        self._build_ui()
        self._bind_events()

    # ─────────────────────────────────────────────
    # UI 构建
    # ─────────────────────────────────────────────
    def _build_ui(self):
        # 顶部标题栏
        header = tk.Frame(self.root, bg=self.COLOR_PRIMARY, height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text='⚡ ' + self.TITLE, font=('Microsoft YaHei', 14, 'bold'),
                 fg='white', bg=self.COLOR_PRIMARY).pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(header, text='v0.3', font=('Microsoft YaHei', 9),
                 fg='#a0cfff', bg=self.COLOR_PRIMARY).pack(side=tk.RIGHT, padx=20, pady=12)

        main = tk.Frame(self.root, bg=self.COLOR_BG)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # ===== 左侧：参数 =====
        left = tk.Frame(main, bg=self.COLOR_BG, width=320)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        frm_file = self._section(left, '📂 负荷计算表')
        tk.Entry(frm_file, textvariable=self.excel_var, font=('Consolas', 10),
                 relief=tk.SOLID, bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        tk.Button(frm_file, text=' 浏览... ', command=self._browse_excel, bg=self.COLOR_PRIMARY,
                  fg='white', relief=tk.FLAT, font=('Microsoft YaHei', 9), cursor='hand2',
                  padx=10).pack(side=tk.RIGHT, padx=(6, 0))

        frm_type = self._section(left, '🏗 工程类型')
        ttk.Combobox(frm_type, textvariable=self.type_var,
                     values=[v for _, v in self.ENGINEERING_TYPES],
                     state='readonly', font=('Microsoft YaHei', 10)).pack(fill=tk.X, ipady=2)

        frm_stage = self._section(left, '📋 设计阶段')
        ttk.Combobox(frm_stage, textvariable=self.stage_var, values=self.DESIGN_STAGES,
                     state='readonly', font=('Microsoft YaHei', 10)).pack(fill=tk.X, ipady=2)

        # 模板选择
        frm_tpl = self._section(left, '🎨 文档模板（决定 Word 排版）')
        tpl_values = [f'{TEMPLATES[k]["label"]} — {TEMPLATES[k]["desc"]}' for k in TEMPLATES]
        self._tpl_label_var = tk.StringVar()
        self.cb_tpl_display = ttk.Combobox(frm_tpl, textvariable=self._tpl_label_var,
                                           values=tpl_values, state='readonly', font=('Microsoft YaHei', 9))
        self.cb_tpl_display.pack(fill=tk.X, ipady=2)
        self.cb_tpl_display.current(0)
        self.cb_tpl_display.bind('<<ComboboxSelected>>', self._on_template_display_change)

        frm_name = self._section(left, '📝 项目名称')
        tk.Entry(frm_name, textvariable=self.name_var, font=('Microsoft YaHei', 10),
                 relief=tk.SOLID, bd=1).pack(fill=tk.X, ipady=3)

        frm_params = tk.Frame(left, bg=self.COLOR_BG)
        frm_params.pack(fill=tk.X, pady=4)
        frm_v = tk.Frame(frm_params, bg=self.COLOR_BG)
        frm_v.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        tk.Label(frm_v, text='电压等级', font=('Microsoft YaHei', 9), fg=self.COLOR_TEXT_SEC,
                 bg=self.COLOR_BG).pack(anchor=tk.W)
        tk.Entry(frm_v, textvariable=self.voltage_var, font=('Microsoft YaHei', 10),
                 relief=tk.SOLID, bd=1, width=10).pack(fill=tk.X, ipady=3)
        frm_l = tk.Frame(frm_params, bg=self.COLOR_BG)
        frm_l.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))
        tk.Label(frm_l, text='负荷等级', font=('Microsoft YaHei', 9), fg=self.COLOR_TEXT_SEC,
                 bg=self.COLOR_BG).pack(anchor=tk.W)
        ttk.Combobox(frm_l, textvariable=self.load_var, values=self.LOAD_LEVELS,
                     state='readonly', font=('Microsoft YaHei', 10)).pack(fill=tk.X, ipady=2)

        # 操作按钮
        btn_frame = tk.Frame(left, bg=self.COLOR_BG)
        btn_frame.pack(fill=tk.X, pady=(12, 4))
        self.btn_gen = tk.Button(btn_frame, text='  🚀  生成设计文件  ', command=self._generate,
                                 bg=self.COLOR_SUCCESS, fg='white', font=('Microsoft YaHei', 12, 'bold'),
                                 relief=tk.FLAT, cursor='hand2', padx=12, pady=8)
        self.btn_gen.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_summary = tk.Button(btn_frame, text='  📊  仅汇总  ', command=self._summary_only,
                                     bg='#e6a23c', fg='white', font=('Microsoft YaHei', 10),
                                     relief=tk.FLAT, cursor='hand2', padx=8, pady=8)
        self.btn_summary.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_preview = tk.Button(left, text='  🔄  刷新预览  ', command=self._refresh_preview,
                                     bg=self.COLOR_PRIMARY, fg='white', font=('Microsoft YaHei', 10),
                                     relief=tk.FLAT, cursor='hand2', padx=8, pady=6)
        self.btn_preview.pack(fill=tk.X, pady=(4, 0))

        # 进度条（预览区下方）
        self.progress = ttk.Progressbar(left, mode='indeterminate', length=200)
        self.progress.pack(fill=tk.X, pady=(6, 0))

        # ===== 右侧：Notebook（预览 / 结果）=====
        right = tk.Frame(main, bg='white', relief=tk.SOLID, bd=1)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        nb = ttk.Notebook(right)
        nb.pack(fill=tk.BOTH, expand=True)
        self.notebook = nb

        # Tab1 预览
        preview_frame = tk.Frame(nb, bg='white')
        nb.add(preview_frame, text='  📄 实时预览  ')
        phead = tk.Frame(preview_frame, bg='#ecf5ff', height=26)
        phead.pack(fill=tk.X)
        phead.pack_propagate(False)
        self.preview_hint = tk.StringVar(value='预览将随模板/参数实时更新（导出前请确认内容格式）')
        tk.Label(phead, textvariable=self.preview_hint, font=('Microsoft YaHei', 9),
                 fg='#409EFF', bg='#ecf5ff').pack(side=tk.LEFT, padx=10, pady=3)
        self.preview = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD,
                                                 font=('Microsoft YaHei', 10), relief=tk.FLAT,
                                                 padx=10, pady=8, bg='white', fg=self.COLOR_TEXT,
                                                 state=tk.DISABLED)
        self.preview.pack(fill=tk.BOTH, expand=True)
        self._setup_preview_tags()

        # Tab2 结果
        result_frame = tk.Frame(nb, bg='white')
        nb.add(result_frame, text='  📊 生成结果  ')
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD,
                                                     font=('Microsoft YaHei', 9), relief=tk.FLAT,
                                                     padx=10, pady=10, state=tk.DISABLED,
                                                     bg='#fafbfc', fg=self.COLOR_TEXT)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 右侧底部按钮
        result_btns = tk.Frame(right, bg='white')
        result_btns.pack(fill=tk.X, padx=8, pady=6)
        self.btn_open = tk.Button(result_btns, text='📂 打开文件', command=self._open_output,
                                  state=tk.DISABLED, bg=self.COLOR_PRIMARY, fg='white',
                                  font=('Microsoft YaHei', 9), relief=tk.FLAT, cursor='hand2', padx=12, pady=4)
        self.btn_open.pack(side=tk.LEFT)
        self.btn_clear = tk.Button(result_btns, text='清空', command=self._clear_result,
                                   font=('Microsoft YaHei', 9), relief=tk.FLAT, cursor='hand2', padx=12, pady=4)
        self.btn_clear.pack(side=tk.RIGHT)

        # 状态栏
        status_bar = tk.Frame(self.root, bg='#ebeef5', height=28)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        tk.Label(status_bar, textvariable=self.status_var, font=('Microsoft YaHei', 9),
                 fg=self.COLOR_TEXT_SEC, bg='#ebeef5').pack(side=tk.LEFT, padx=12, pady=4)
        tk.Label(status_bar, text='规范依据：《市政公用工程设计文件编制深度规定》（2025年版）',
                 font=('Microsoft YaHei', 9), fg=self.COLOR_TEXT_SEC, bg='#ebeef5').pack(side=tk.RIGHT, padx=12, pady=4)

    def _setup_preview_tags(self):
        pv = self.preview
        pv.tag_configure('cover', justify='center', font=('Microsoft YaHei', 16, 'bold'),
                         spacing1=10, spacing3=10, foreground='#1F4E79')
        pv.tag_configure('h1', font=('Microsoft YaHei', 14, 'bold'), spacing1=10, spacing3=4,
                         foreground='#1F4E79')
        pv.tag_configure('h2', font=('Microsoft YaHei', 13, 'bold'), spacing1=8, spacing3=3,
                         foreground='#2E5C8A')
        pv.tag_configure('h3', font=('Microsoft YaHei', 11, 'bold'), spacing1=5, spacing3=2,
                         foreground='#303133')
        pv.tag_configure('p', font=('Microsoft YaHei', 10), spacing1=2, spacing3=2)
        pv.tag_configure('b', font=('Microsoft YaHei', 10), spacing1=1, spacing3=1, lmargin1=16, lmargin2=16)
        pv.tag_configure('table', font=('Consolas', 9), spacing1=4, spacing3=4, foreground='#222222')
        pv.tag_configure('sep', font=('Microsoft YaHei', 9), foreground='#bbbbbb', justify='center')
        pv.tag_configure('sig', font=('Consolas', 9), spacing1=4, spacing3=4)

    def _section(self, parent, label_text):
        frm = tk.Frame(parent, bg=self.COLOR_BG)
        frm.pack(fill=tk.X, pady=3)
        tk.Label(frm, text=label_text, font=('Microsoft YaHei', 10, 'bold'),
                 fg=self.COLOR_TEXT, bg=self.COLOR_BG).pack(anchor=tk.W, pady=(0, 2))
        return frm

    # ─────────────────────────────────────────────
    # 事件
    # ─────────────────────────────────────────────
    def _bind_events(self):
        self.root.bind('<Control-o>', lambda e: self._browse_excel())
        self.root.bind('<Control-g>', lambda e: self._generate())
        self.type_var.trace_add('write', lambda *a: self._on_param_change())
        self.stage_var.trace_add('write', lambda *a: self._on_param_change())
        self.name_var.trace_add('write', lambda *a: self._on_param_change())
        self.voltage_var.trace_add('write', lambda *a: self._on_param_change())
        self.load_var.trace_add('write', lambda *a: self._on_param_change())
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _on_template_change(self, event=None):
        # 隐藏的内部 key 变化（未使用显示框）
        pass

    def _on_template_display_change(self, event=None):
        idx = self.cb_tpl_display.current()
        keys = list(TEMPLATES.keys())
        if 0 <= idx < len(keys):
            self.template_var.set(keys[idx])
        self._on_param_change()

    def _on_param_change(self):
        # 参数变化 → 若已解析 Excel，实时刷新预览
        if self.excel_data is not None:
            self._refresh_preview()

    # ─────────────────────────────────────────────
    # 文件 / 解析
    # ─────────────────────────────────────────────
    def _browse_excel(self):
        filename = filedialog.askopenfilename(
            title='选择负荷计算表',
            filetypes=[('Excel files', '*.xlsx *.xls'), ('All files', '*.*')])
        if filename:
            self.excel_var.set(filename)
            self.status_var.set(f'已选择: {os.path.basename(filename)} — 正在解析...')
            try:
                self._ensure_parsed()
                self.status_var.set(
                    f'已解析：{self.excel_summary["total_devices"]} 台设备，'
                    f'计算负荷 {self.excel_summary["total_sc_k"]:.0f} kVA')
                self._refresh_preview()
            except Exception as e:
                messagebox.showerror('解析失败', str(e))
                self.status_var.set(f'❌ 解析失败：{str(e)[:50]}')
                self.excel_data = None

    def _ensure_parsed(self):
        if self.excel_data is None:
            parser = ExcelLoadParser()
            self.excel_data = parser.parse(self.excel_var.get())
            self.excel_summary = self.excel_data['summary']

    # ─────────────────────────────────────────────
    # 生成
    # ─────────────────────────────────────────────
    def _generate(self):
        if not self.excel_var.get().strip():
            messagebox.showwarning('提示', '请先选择负荷计算 Excel 文件！')
            return
        if not os.path.exists(self.excel_var.get()):
            messagebox.showerror('错误', f'文件不存在：\n{self.excel_var.get()}')
            return
        self._run_task(full_generate=True)

    def _summary_only(self):
        if not self.excel_var.get().strip():
            messagebox.showwarning('提示', '请先选择负荷计算 Excel 文件！')
            return
        if not os.path.exists(self.excel_var.get()):
            messagebox.showerror('错误', f'文件不存在：\n{self.excel_var.get()}')
            return
        self._run_task(full_generate=False)

    def _run_task(self, full_generate=True):
        self.btn_gen.config(state=tk.DISABLED, text='  ⏳  处理中...  ')
        self.btn_summary.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=(6, 0))
        self.progress.start(10)
        task = threading.Thread(target=self._do_work if full_generate else self._do_summary, daemon=True)
        task.start()

    def _get_type_code(self):
        display = self.type_var.get()
        for code, label in self.ENGINEERING_TYPES:
            if display == label:
                return code
        return 'water_supply'

    def _do_work(self):
        try:
            self._ensure_parsed()
            self.excel_summary = self.excel_data['summary']
            self._update_status('正在生成 Word 文档...')
            gen = DocxGenerator(rules_dir=RULES_DIR, output_dir=OUTPUT_DIR, template=self.template_var.get())
            params = self._build_params()
            self.output_path = gen.generate(self._get_type_code(), self.stage_var.get(), self.excel_data, params)
            self._update_status('✅ 生成成功！')
            self._refresh_preview()
            self._show_result(self.excel_data, generated=True)
        except Exception as e:
            self._show_error(str(e))

    def _do_summary(self):
        try:
            self._ensure_parsed()
            self.excel_summary = self.excel_data['summary']
            self._update_status('✅ 汇总完成！')
            self._show_result(self.excel_data, generated=False)
        except Exception as e:
            self._show_error(str(e))

    def _build_params(self):
        lv = self.load_var.get()
        return {
            'project_name': self.name_var.get() or '新建项目',
            'voltage_level': self.voltage_var.get() or '10kV',
            'load_level': lv,
            'project_type': self._get_type_code(),
            'power_source': '两路' if lv == '一级' else '一路',
            'standby_desc': '两路电源互为备用，当一路电源故障时另一路可承担全部负荷。' if lv in ('一级', '二级') else '',
        }

    # ─────────────────────────────────────────────
    # 预览（核心）
    # ─────────────────────────────────────────────
    def _refresh_preview(self):
        try:
            if self.excel_data is None:
                self._render_preview_hint('请先选择并解析负荷计算 Excel 文件，预览将自动显示。')
                return
            gen = DocxGenerator(rules_dir=RULES_DIR, output_dir=OUTPUT_DIR, template=self.template_var.get())
            blocks = gen.preview(self._get_type_code(), self.stage_var.get(), self.excel_data, self._build_params())
            label = TEMPLATES[self.template_var.get()]['label']
            self.preview_hint.set(
                f'当前模板：{label} ｜ 工程：{self.name_var.get() or "(未命名)"} ｜ 共 {len(blocks)} 个内容块（未导出，仅供预览）')
            self._render_blocks(blocks)
        except Exception as e:
            self._render_preview_hint(f'预览生成失败：{e}')

    def _render_preview_hint(self, msg):
        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.insert(tk.END, msg + '\n', 'sep')
        self.preview.config(state=tk.DISABLED)

    def _render_blocks(self, blocks):
        pv = self.preview
        pv.config(state=tk.NORMAL)
        pv.delete(1.0, tk.END)
        for blk in blocks:
            kind = blk[0]
            if kind == 'cover':
                _, name, subtitle, info = blk
                pv.insert(tk.END, name + '\n', 'cover')
                pv.insert(tk.END, subtitle + '\n', 'cover')
                for line in info:
                    pv.insert(tk.END, line + '\n', 'cover')
                pv.insert(tk.END, '\n', 'p')
            elif kind == 'pagebreak':
                pv.insert(tk.END, '─' * 40 + '  分页  ' + '─' * 40 + '\n', 'sep')
            elif kind in ('h1', 'h2', 'h3'):
                pv.insert(tk.END, blk[1] + '\n', kind)
            elif kind == 'p':
                pv.insert(tk.END, blk[1] + '\n', 'p')
            elif kind == 'b':
                pv.insert(tk.END, '• ' + blk[1] + '\n', 'b')
            elif kind == 'table':
                _, _, headers, rows = blk
                self._insert_table(pv, headers, rows)
            elif kind == 'sig':
                _, headers, rows = blk
                self._insert_table(pv, headers, rows, tag='sig')
        pv.config(state=tk.DISABLED)
        pv.see(1.0)

    @staticmethod
    def _cjk_w(s):
        return sum(2 if ord(ch) > 0x2E80 else 1 for ch in str(s))

    def _insert_table(self, pv, headers, rows, tag='table'):
        all_rows = [headers] + rows
        cols = len(headers)
        widths = [max(self._cjk_w(r[i]) for r in all_rows) for i in range(cols)]
        line = '┬'.join('─' * (widths[i] + 2) for i in range(cols))
        pv.insert(tk.END, '┌' + line + '┐\n', tag)
        for ri, row in enumerate(all_rows):
            cells = []
            for i in range(cols):
                s = str(row[i])
                pad = widths[i] - self._cjk_w(s)
                cells.append(' ' + s + ' ' * max(0, pad) + ' ')
            pv.insert(tk.END, '│' + '│'.join(cells) + '│\n', tag)
            if ri == 0:
                pv.insert(tk.END, '├' + line + '┤\n', tag)
        pv.insert(tk.END, '└' + line + '┘\n', tag)

    # ─────────────────────────────────────────────
    # 结果 / 错误
    # ─────────────────────────────────────────────
    def _update_status(self, msg):
        self.root.after(0, lambda: self.status_var.set(msg))

    def _show_result(self, excel_data, generated=False):
        s = excel_data['summary']
        area = excel_data['area_summaries']
        lines = []
        lines.append('=' * 50)
        lines.append('  设计文件生成完成！' if generated else '  负荷计算汇总结果')
        lines.append('=' * 50)
        lines.append('')
        lines.append(f'  📊 设备总数：{s["total_devices"]} 台')
        lines.append(f'  ⚡ 安装容量：{s["total_equip_power"]:.1f} kW')
        lines.append(f'  📐 计算负荷：{s["total_sc_k"]:.1f} kVA')
        lines.append(f'  🔌 补偿容量：{s["qc_compensation"]:.1f} kvar')
        lines.append(f'  🔄 补偿前 cosφ：{s["cos_before"]}')
        lines.append(f'  🏭 推荐变压器：{s["recommended_transformer"]}')
        lines.append('')
        if self.output_path:
            lines.append(f'  📄 输出文件：')
            lines.append(f'     {self.output_path}')
            lines.append('')
        lines.append(f'  📋 各区域负荷明细（共{len(area)}个区域）：')
        lines.append('  ' + '-' * 46)
        for area_name, data in area.items():
            lines.append(f'  {area_name:<16s} 设备{data["device_count"]:>3d}台 '
                         f'{data["equip_power"]:>8.1f}kW → {data["sc"]:>7.1f}kVA')
        lines.append('')
        if generated:
            lines.append('  💡 可在右侧"实时预览"中查看完整内容与排版，确认后导出 Word。')

        def update():
            self.notebook.select(1)
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, '\n'.join(lines))
            self.result_text.config(state=tk.DISABLED)
            self.result_text.see(tk.END)
            self.progress.stop()
            self.progress.pack_forget()
            self.btn_gen.config(state=tk.NORMAL, text='  🚀  重新生成  ', bg=self.COLOR_WARNING)
            self.btn_summary.config(state=tk.NORMAL)
            if self.output_path:
                self.btn_open.config(state=tk.NORMAL)
        self.root.after(0, update)

    def _show_error(self, msg):
        def update():
            self.progress.stop()
            self.progress.pack_forget()
            self.btn_gen.config(state=tk.NORMAL, text='  🚀  生成设计文件  ', bg=self.COLOR_SUCCESS)
            self.btn_summary.config(state=tk.NORMAL)
            self.status_var.set(f'❌ 失败：{msg[:60]}')
            messagebox.showerror('生成失败', msg)
        self.root.after(0, update)

    def _open_output(self):
        if self.output_path and os.path.exists(self.output_path):
            os.startfile(self.output_path)

    def _clear_result(self):
        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.config(state=tk.DISABLED)
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.output_path = None
        self.excel_data = None
        self.excel_summary = None
        self.btn_open.config(state=tk.DISABLED)
        self.btn_gen.config(text='  🚀  生成设计文件  ', bg=self.COLOR_SUCCESS)
        self.status_var.set('就绪 — 请选择负荷计算 Excel 文件')

    def _on_close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app = App()
    app.run()


if __name__ == '__main__':
    main()
