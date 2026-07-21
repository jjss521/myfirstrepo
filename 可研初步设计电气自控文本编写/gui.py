# -*- coding: utf-8 -*-
"""
市政工程设计文件（电气与自控）生成器 — 桌面 GUI 版
====================================================
双击启动，无需 Web 服务、无需浏览器。
  * 浏览选择 Excel 负荷计算表
  * 选择工程类型 / 设计阶段 / 文档模板
  * 右侧实时预览（带格式），切换模板即时刷新
  * 一键生成 Word，导出前可确认内容与排版

依赖：tkinter(内置) + openpyxl + xlrd + python-docx
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

# 将 backend 加入导入路径
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, 'backend'))

from app.services.excel_parser import parse as parse_excel
from app.services.docx_generator import DocxGenerator, TEMPLATES


def cjk_w(s):
    """按 CJK 双宽估算字符串显示宽度。"""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in str(s))


# 工程类型与阶段选项
PROJECT_TYPES = [
    ('water_supply', '给水工程'),
    ('drainage', '排水工程'),
    ('road', '道路交通工程'),
    ('sanitation', '环境卫生工程'),
]
DESIGN_STAGES = ['初步设计', '可研']
LOAD_LEVELS = ['一级', '二级', '三级']
VOLTAGE_LEVELS = ['10kV', '20kV', '35kV', '0.4kV']


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('⚡ 市政工程设计文件电气自控生成器  v0.4')
        self.root.geometry('1180x760')

        self.excel_path = tk.StringVar()
        self.project_type_var = tk.StringVar(value='water_supply')
        self.stage_var = tk.StringVar(value='初步设计')
        self.name_var = tk.StringVar(value='新建项目')
        self.voltage_var = tk.StringVar(value='10kV')
        self.load_var = tk.StringVar(value='二级')
        self.template_var = tk.StringVar(value='standard')     # 内部 key
        self.excel_summary = {}
        self.output_path = None
        self.preview_hint = tk.StringVar(value='')

        self._build_ui()
        self._bind_shortcuts()

    # ---------------- UI ----------------
    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(top, text='⚡ 市政工程设计文件电气自控生成器',
                  font=('Microsoft YaHei', 14, 'bold')).pack(side=tk.LEFT)
        ttk.Label(top, text='依据《市政公用工程设计文件编制深度规定》（2025年版）',
                  font=('Microsoft YaHei', 9), foreground='#666').pack(side=tk.LEFT, padx=12)

        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left = ttk.Frame(main, width=380)
        right = ttk.Frame(main, width=760)
        main.add(left, weight=0)
        main.add(right, weight=1)

        self._build_left(left)
        self._build_right(right)

        self.status = ttk.Label(self.root, text='就绪 — 请选择负荷计算表 Excel',
                                relief=tk.SUNKEN, anchor=tk.W, font=('Microsoft YaHei', 9))
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    def _section(self, parent, title):
        f = ttk.LabelFrame(parent, text=title, padding=(8, 6))
        f.pack(fill=tk.X, pady=5)
        return f

    def _build_left(self, parent):
        # Excel
        f = self._section(parent, '📂 负荷计算表（Excel）')
        ttk.Entry(f, textvariable=self.excel_path, width=34).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(f, text='浏览...', command=self._browse, width=8).pack(side=tk.LEFT, padx=4)

        # 工程类型
        f = self._section(parent, '🏗 工程类型')
        cb = ttk.Combobox(f, textvariable=self.project_type_var,
                          values=[v[1] for v in PROJECT_TYPES], state='readonly', width=30)
        cb.pack(fill=tk.X)
        cb.bind('<<ComboboxSelected>>', lambda e: self._refresh_preview())
        self._type_disp = cb

        # 设计阶段
        f = self._section(parent, '📋 设计阶段')
        cb = ttk.Combobox(f, textvariable=self.stage_var, values=DESIGN_STAGES,
                          state='readonly', width=30)
        cb.pack(fill=tk.X)
        cb.bind('<<ComboboxSelected>>', lambda e: self._refresh_preview())

        # 文档模板
        f = self._section(parent, '🎨 文档模板（决定 Word 排版）')
        tpl_values = [f'{TEMPLATES[k]["label"]} — {TEMPLATES[k]["desc"]}' for k in TEMPLATES]
        self.cb_tpl_display = ttk.Combobox(f, textvariable=self._tpl_label_var(),
                                           values=tpl_values, state='readonly', width=40)
        self.cb_tpl_display.pack(fill=tk.X)
        self.cb_tpl_display.current(0)
        self.cb_tpl_display.bind('<<ComboboxSelected>>', self._on_template_display_change)

        # 项目信息
        f = self._section(parent, '📝 项目信息')
        ttk.Label(f, text='项目名称（封面/页眉）').pack(anchor=tk.W)
        ttk.Entry(f, textvariable=self.name_var, width=34).pack(fill=tk.X, pady=2)
        self.name_var.trace_add('write', lambda *a: self._refresh_preview())
        row = ttk.Frame(f)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text='电压等级').pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=self.voltage_var, values=VOLTAGE_LEVELS,
                     state='readonly', width=8).pack(side=tk.LEFT, padx=4)
        ttk.Label(row, text='负荷等级').pack(side=tk.LEFT, padx=(8, 0))
        ttk.Combobox(row, textvariable=self.load_var, values=LOAD_LEVELS,
                     state='readonly', width=8).pack(side=tk.LEFT, padx=4)
        self.voltage_var.trace_add('write', lambda *a: self._refresh_preview())
        self.load_var.trace_add('write', lambda *a: self._refresh_preview())

        # 操作按钮
        f = self._section(parent, '🚀 操作')
        ttk.Button(f, text='生成设计文件（Word）', command=self._do_work,
                   width=34).pack(fill=tk.X, pady=2)
        ttk.Button(f, text='仅查看负荷汇总', command=self._show_summary,
                   width=34).pack(fill=tk.X, pady=2)
        ttk.Button(f, text='打开输出文件', command=self._open_output,
                   width=34).pack(fill=tk.X, pady=2)

    def _tpl_label_var(self):
        # 维护一个隐藏变量，用于下拉显示 label 时反查内部 key
        if not hasattr(self, '_tpl_label'):
            self._tpl_label = tk.StringVar()
            self._tpl_label.trace_add('write', self._sync_tpl_key)
        return self._tpl_label

    def _sync_tpl_key(self, *a):
        label = self._tpl_label.get()
        for k in TEMPLATES:
            if TEMPLATES[k]['label'] in label:
                self.template_var.set(k)
                break

    def _build_right(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill=tk.BOTH, expand=True)
        # 预览
        pf = ttk.Frame(nb)
        nb.add(pf, text='📄 实时预览')
        self.preview = scrolledtext.ScrolledText(pf, wrap=tk.NONE,
                                                  font=('Microsoft YaHei', 10),
                                                  bg='white')
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.preview.config(state=tk.DISABLED)
        self._setup_tags()
        # 结果
        rf = ttk.Frame(nb)
        nb.add(rf, text='📊 负荷计算汇总')
        self.result = scrolledtext.ScrolledText(rf, wrap=tk.WORD,
                                                 font=('Consolas', 10), bg='#f7f7f7')
        self.result.pack(fill=tk.BOTH, expand=True)
        self.result.config(state=tk.DISABLED)

    def _setup_tags(self):
        pv = self.preview
        pv.tag_configure('cover', font=('Microsoft YaHei', 20, 'bold'),
                         justify='center', spacing1=40, spacing3=10,
                         foreground='#1a1a1a')
        pv.tag_configure('cover_sub', font=('Microsoft YaHei', 12, 'bold'),
                         justify='center', foreground='#444')
        pv.tag_configure('h1', font=('Microsoft YaHei', 13, 'bold'),
                         spacing1=10, spacing3=4, foreground='#1a1a1a')
        pv.tag_configure('h2', font=('Microsoft YaHei', 11, 'bold'),
                         spacing1=6, spacing3=2, foreground='#2E5C8A')
        pv.tag_configure('h3', font=('Microsoft YaHei', 10, 'bold'), spacing1=4, spacing3=1)
        pv.tag_configure('p', font=('Microsoft YaHei', 10), spacing1=1, spacing3=3)
        pv.tag_configure('table', font=('Consolas', 9))
        pv.tag_configure('sig', font=('Microsoft YaHei', 10, 'bold'), spacing1=8)

    # ---------------- 交互 ----------------
    def _bind_shortcuts(self):
        self.root.bind('<Control-o>', lambda e: self._browse())
        self.root.bind('<Control-g>', lambda e: self._do_work())

    def _browse(self):
        path = filedialog.askopenfilename(
            title='选择负荷计算表',
            filetypes=[('Excel', '*.xlsx;*.xls'), ('All', '*.*')])
        if path:
            self.excel_path.set(path)
            self._ensure_parsed()
            self._refresh_preview()

    def _ensure_parsed(self):
        p = self.excel_path.get()
        if not p or not os.path.exists(p):
            self.excel_summary = {}
            return
        try:
            self.excel_summary = parse_excel(p)
            s = self.excel_summary.get('summary', {})
            self.status.config(text=f'已解析：{s.get("total_devices", 0)} 台设备 / '
                                     f'{s.get("area_count", 0)} 区域 / 计算负荷 '
                                     f'{s.get("total_sc_before", 0)} kVA')
        except Exception as e:
            self.excel_summary = {}
            messagebox.showerror('解析失败', str(e))

    def _current_params(self):
        # 将界面显示的类型反查为内部 key
        disp = self._type_disp.get()
        ptype = 'water_supply'
        for k, v in PROJECT_TYPES:
            if v == disp:
                ptype = k
                break
        return {
            'project_name': self.name_var.get() or '新建项目',
            'voltage_level': self.voltage_var.get(),
            'load_level': self.load_var.get(),
            'project_type': ptype,
            'design_stage': self.stage_var.get(),
            'power_source': '两路',
            'standby_desc': '两路电源互为备用',
        }

    def _on_template_display_change(self, *a):
        self._sync_tpl_key()
        self._refresh_preview()

    def _refresh_preview(self):
        if not self.excel_summary:
            self._render_text('（请先选择负荷计算表 Excel，预览将自动显示）')
            return
        params = self._current_params()
        tpl = self.template_var.get()
        try:
            gen = DocxGenerator(template=tpl)
            blocks = gen.preview(params['project_type'], params['design_stage'],
                                 self.excel_summary, params)
            self._render_blocks(blocks)
            self.preview_hint.set(f'当前模板：{TEMPLATES[tpl]["label"]}')
        except Exception as e:
            self._render_text(f'预览生成出错：{e}')

    def _render_text(self, text):
        pv = self.preview
        pv.config(state=tk.NORMAL)
        pv.delete(1.0, tk.END)
        pv.insert(tk.END, text)
        pv.config(state=tk.DISABLED)

    def _render_blocks(self, blocks):
        pv = self.preview
        pv.config(state=tk.NORMAL)
        pv.delete(1.0, tk.END)
        for blk in blocks:
            kind = blk[0]
            if kind == 'cover':
                pv.insert(tk.END, '\n\n')
                pv.insert(tk.END, blk[1] + '\n', 'cover')
                pv.insert(tk.END, blk[2] + '\n', 'cover_sub')
                pv.insert(tk.END, blk[3] + '\n', 'cover_sub')
                pv.insert(tk.END, '\n' + '─' * 40 + '\n')
            elif kind == 'h1':
                pv.insert(tk.END, blk[1] + '\n', 'h1')
            elif kind == 'h2':
                pv.insert(tk.END, blk[1] + '\n', 'h2')
            elif kind == 'h3':
                pv.insert(tk.END, blk[1] + '\n', 'h3')
            elif kind == 'p':
                pv.insert(tk.END, blk[1] + '\n', 'p')
            elif kind == 'table':
                self._render_table(pv, blk[1], blk[2])
            elif kind == 'sig':
                pv.insert(tk.END, '\n编制与签署（会签栏）\n', 'sig')
        pv.config(state=tk.DISABLED)
        pv.see(1.0)

    def _render_table(self, pv, headers, rows):
        all_rows = [headers] + rows
        cols = len(headers)
        widths = [max(cjk_w(r[i]) for r in all_rows) for i in range(cols)]
        line = '┬'.join('─' * (w + 2) for w in widths)
        pv.insert(tk.END, '┌' + line + '┐\n', 'table')
        for ri, row in enumerate(all_rows):
            cells = []
            for i in range(cols):
                s = str(row[i])
                pad = widths[i] - cjk_w(s)
                cells.append(' ' + s + ' ' * max(0, pad) + ' ')
            pv.insert(tk.END, '│' + '│'.join(cells) + '│\n', 'table')
            if ri == 0:
                pv.insert(tk.END, '├' + line + '┤\n', 'table')
        pv.insert(tk.END, '└' + line + '┘\n', 'table')
        pv.insert(tk.END, '\n')

    def _show_summary(self):
        if not self.excel_summary:
            messagebox.showinfo('提示', '请先选择负荷计算表')
            return
        s = self.excel_summary.get('summary', {})
        areas = self.excel_summary.get('area_summaries', {})
        lines = []
        lines.append('=' * 46)
        lines.append('        负 荷 计 算 汇 总')
        lines.append('=' * 46)
        lines.append(f'设备总数        : {s.get("total_devices", 0)} 台')
        lines.append(f'安装容量        : {s.get("total_equip_power", 0)} kW')
        lines.append(f'总有功计算负荷  : {s.get("total_pjs", 0)} kW')
        lines.append(f'自然功率因数    : {s.get("cos_before", 0.85)}')
        lines.append(f'无功补偿容量    : {round(s.get("qc_compensation", 0))} kvar')
        lines.append(f'补偿后功率因数  : {s.get("cos_target", 0.92)}')
        lines.append(f'补偿后视在负荷  : {s.get("total_sc_after", 0)} kVA')
        lines.append(f'推荐变压器      : {s.get("recommended_transformer", "—")}')
        lines.append(f'变压器负荷率    : {round(s.get("load_rate", 0) * 100, 1)} %')
        lines.append('-' * 46)
        lines.append('区域负荷明细：')
        for k, v in areas.items():
            lines.append(f'  {k:<14} Pe={v.get("pe", 0):>8}kW  '
                         f'Sjs={v.get("sc", 0):>8}kVA')
        lines.append('=' * 46)
        self.result.config(state=tk.NORMAL)
        self.result.delete(1.0, tk.END)
        self.result.insert(tk.END, '\n'.join(lines))
        self.result.config(state=tk.DISABLED)
        messagebox.showinfo('负荷汇总', '已生成汇总，见“负荷计算汇总”标签页')

    def _do_work(self):
        if not self.excel_summary:
            messagebox.showwarning('未选择文件', '请先选择负荷计算表 Excel')
            return
        params = self._current_params()
        tpl = self.template_var.get()

        def worker():
            try:
                gen = DocxGenerator(template=tpl)
                out = gen.generate(params['project_type'], params['design_stage'],
                                   self.excel_summary, params)
                self.output_path = out
                self.root.after(0, lambda: messagebox.showinfo(
                    '生成完成', f'已生成：\n{out}'))
                self.root.after(0, lambda: self.status.config(
                    text=f'已生成（{TEMPLATES[tpl]["label"]}）：{os.path.basename(out)}'))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror('生成失败', str(e)))

        threading.Thread(target=worker, daemon=True).start()
        self.status.config(text='正在生成，请稍候...')

    def _open_output(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.startfile(self.output_path)
            except Exception:
                messagebox.showinfo('路径', self.output_path)
        else:
            messagebox.showinfo('提示', '尚未生成文件，请先点击“生成设计文件”')

    def run(self):
        self.root.mainloop()


def _check_deps():
    missing = []
    for m in ['openpyxl', 'xlrd', 'docx']:
        try:
            __import__(m)
        except ImportError:
            missing.append(m)
    if missing:
        print('缺少依赖：' + ', '.join(missing))
        print('请运行：pip install openpyxl xlrd python-docx')
        return False
    return True


if __name__ == '__main__':
    if not _check_deps():
        sys.exit(1)
    App().run()
