"""PDSG GUI — 配电柜系统图自动生成程序 图形界面

基于 tkinter/ttk 实现，包含:
- 配置标签页: 文件选择、图块映射、布局参数、图框设置
- 数据预览标签页: Excel 数据表格、映射统计
- 执行标签页: 运行控制、实时日志、结果展示
"""
import logging
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from datetime import datetime

# 确保 src 在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config_loader import load_config
from src.data_model import AppConfig, BlockMappingRule, BlockMappingConfig, PaperSizeDef
from src.errors import (
    PDSGError, ExcelReadError, ConfigError, BlockLibraryError,
    AcadConnectionError, AcadOperationError,
)
from src import excel_reader, block_mapper, attribute_builder, layout_engine, block_library, reporter

logger = logging.getLogger("pdsg.gui")


# ================================================================
# 日志处理: 将 logging 输出导向 GUI 日志窗口
# ================================================================

class GUILogHandler(logging.Handler):
    """线程安全的 GUI 日志处理器（通过队列中转）"""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
        self.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put((msg, record.levelno))
        except Exception:
            pass


# ================================================================
# 主窗口
# ================================================================

class PDSGApp:
    """PDSG 图形界面主窗口"""

    APP_TITLE = "PDSG 配电柜系统图自动生成工具 v1.0"
    WINDOW_SIZE = "1060x720"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(self.APP_TITLE)
        self.root.geometry(self.WINDOW_SIZE)
        self.root.minsize(900, 600)

        # 状态
        self.cfg: AppConfig = None
        self.excel_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.records = []
        self.errors = []
        self.mapped = []
        self.layout_result = None
        self.is_running = False

        # 日志队列
        self.log_queue: queue.Queue = queue.Queue()

        # 样式
        self.style = ttk.Style()
        self._apply_style()

        # 构建界面
        self._build_menu()
        self._build_main_layout()
        self._setup_logging()

        # 加载默认配置
        self._load_default_config()

        # 启动日志轮询
        self._poll_log_queue()

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------------------------------------------
    # 样式
    # ----------------------------------------------------------------

    def _apply_style(self):
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure("Title.TLabel", font=("Microsoft YaHei", 11, "bold"))
        self.style.configure("Success.TLabel", foreground="#27ae60", font=("Microsoft YaHei", 10, "bold"))
        self.style.configure("Warning.TLabel", foreground="#e67e22", font=("Microsoft YaHei", 10, "bold"))
        self.style.configure("Error.TLabel", foreground="#e74c3c", font=("Microsoft YaHei", 10, "bold"))
        self.style.configure("Info.TLabel", font=("Microsoft YaHei", 10))
        self.style.configure("Status.TLabel", font=("Microsoft YaHei", 9))
        self.style.configure("Run.TButton", font=("Microsoft YaHei", 10, "bold"))

    # ----------------------------------------------------------------
    # 菜单
    # ----------------------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        # 文件
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开 Excel...", command=self._browse_excel, accelerator="Ctrl+O")
        file_menu.add_command(label="打开配置文件...", command=self._browse_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 工具
        tool_menu = tk.Menu(menubar, tearoff=0)
        tool_menu.add_command(label="校验预览 (Dry-Run)", command=self._run_dry_run)
        tool_menu.add_command(label="生成 DWG", command=self._run_generate)
        tool_menu.add_separator()
        tool_menu.add_command(label="图块编辑器...", command=self._open_block_editor)
        tool_menu.add_command(label="生成示例图块目录", command=self._generate_sample_catalog)
        menubar.add_cascade(label="工具", menu=tool_menu)

        # 帮助
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用教程", command=self._open_user_guide)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)
        self.root.bind("<Control-o>", lambda e: self._browse_excel())

    # ----------------------------------------------------------------
    # 主布局
    # ----------------------------------------------------------------

    def _build_main_layout(self):
        # 顶部: 文件选择条
        self._build_file_bar()

        # 中部: 标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 0))

        self._build_config_tab()
        self._build_preview_tab()
        self._build_execute_tab()

        # 底部: 状态栏
        self._build_status_bar()

    def _build_file_bar(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.X, padx=8, pady=(6, 2))

        ttk.Label(frame, text="Excel:", font=("Microsoft YaHei", 9, "bold")).pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.excel_path, width=55).pack(
            side=tk.LEFT, padx=(4, 4), fill=tk.X, expand=True
        )
        ttk.Button(frame, text="浏览...", width=8, command=self._browse_excel).pack(side=tk.LEFT)

        ttk.Separator(frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Label(frame, text="输出:", font=("Microsoft YaHei", 9, "bold")).pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.output_path, width=35).pack(
            side=tk.LEFT, padx=(4, 4), fill=tk.X, expand=True
        )
        ttk.Button(frame, text="浏览...", width=8, command=self._browse_output).pack(side=tk.LEFT)

    def _build_status_bar(self):
        bar = ttk.Frame(self.root)
        bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=(0, 3))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(bar, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.LEFT)

        self.time_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.time_var, style="Status.TLabel").pack(side=tk.RIGHT)

    # ----------------------------------------------------------------
    # 配置标签页
    # ----------------------------------------------------------------

    def _build_config_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  配置  ")

        canvas = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Excel 读取 ---
        self._section_label(scroll_frame, "Excel 读取")
        excel_frame = ttk.LabelFrame(scroll_frame, text="Excel 格式")
        excel_frame.pack(fill=tk.X, padx=10, pady=5)

        self.format_auto_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            excel_frame, text="自动检测 Excel 格式（标准/转置）",
            variable=self.format_auto_detect_var,
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)

        self.sheet_name_var = tk.StringVar(value="低压配电系统")
        ttk.Label(excel_frame, text="Sheet 名称:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=3)
        ttk.Entry(excel_frame, textvariable=self.sheet_name_var, width=30).grid(
            row=1, column=1, sticky=tk.W, padx=10, pady=3
        )

        self.default_breaker_var = tk.StringVar(value="NSX100N")
        ttk.Label(excel_frame, text="默认断路器型号:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=3)
        ttk.Entry(excel_frame, textvariable=self.default_breaker_var, width=20).grid(
            row=2, column=1, sticky=tk.W, padx=10, pady=3
        )

        ttk.Label(
            excel_frame,
            text="提示: 转置格式（参数在A列、回路在B/C/...列）会自动识别",
            font=("Microsoft YaHei", 8),
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(0, 5))

        # --- AutoCAD ---
        self._section_label(scroll_frame, "AutoCAD 连接")
        acad_frame = ttk.LabelFrame(scroll_frame, text="AutoCAD")
        acad_frame.pack(fill=tk.X, padx=10, pady=5)

        self.acad_visible_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(acad_frame, text="AutoCAD 可见", variable=self.acad_visible_var).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(acad_frame, text="ProgID 列表（逗号分隔）:").grid(row=1, column=0, sticky=tk.W, padx=10)
        self.progids_var = tk.StringVar(
            value="AutoCAD.Application.24.1, AutoCAD.Application.23.1"
        )
        ttk.Entry(acad_frame, textvariable=self.progids_var, width=60).grid(
            row=1, column=1, sticky=tk.EW, padx=10, pady=5
        )
        acad_frame.columnconfigure(1, weight=1)

        # --- 图块库 ---
        self._section_label(scroll_frame, "图块库")
        lib_frame = ttk.LabelFrame(scroll_frame, text="图块库文件")
        lib_frame.pack(fill=tk.X, padx=10, pady=5)

        self.block_lib_path = tk.StringVar(value="./blocks/block_library.dwg")
        self.block_catalog_path = tk.StringVar(value="./blocks/block_catalog.yaml")
        self.default_block_var = tk.StringVar(value="LOOP_POWER_A")

        row = 0
        for label, var in [
            ("图块库 DWG:", self.block_lib_path),
            ("图块目录 YAML:", self.block_catalog_path),
            ("默认图块:", self.default_block_var),
        ]:
            ttk.Label(lib_frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=10, pady=3)
            ttk.Entry(lib_frame, textvariable=var, width=50).grid(
                row=row, column=1, sticky=tk.EW, padx=10, pady=3
            )
            row += 1
        lib_frame.columnconfigure(1, weight=1)

        # --- 布局参数 ---
        self._section_label(scroll_frame, "布局参数")
        layout_frame = ttk.LabelFrame(scroll_frame, text="布局")
        layout_frame.pack(fill=tk.X, padx=10, pady=5)

        self.paper_var = tk.StringVar(value="自动选择")
        self.bus_x_var = tk.StringVar(value="100")
        self.spacing_var = tk.StringVar(value="70")
        self.offset_x_var = tk.StringVar(value="15")

        row = 0
        for label, var, vals in [
            ("图纸幅面:", self.paper_var, ["自动选择", "A2", "A1", "A0"]),
            ("母线 X (mm):", self.bus_x_var, None),
            ("图块偏移 X (mm):", self.offset_x_var, None),
            ("回路间距 (mm):", self.spacing_var, None),
        ]:
            ttk.Label(layout_frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=10, pady=3)
            if vals:
                ttk.Combobox(layout_frame, textvariable=var, values=vals, state="readonly", width=15).grid(
                    row=row, column=1, sticky=tk.W, padx=10, pady=3
                )
            else:
                ttk.Entry(layout_frame, textvariable=var, width=15).grid(
                    row=row, column=1, sticky=tk.W, padx=10, pady=3
                )
            row += 1

        # 排序分组
        self.group_sep_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(layout_frame, text="启用分组分隔标签", variable=self.group_sep_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5
        )

        # --- 图框 ---
        self._section_label(scroll_frame, "图框")
        title_frame = ttk.LabelFrame(scroll_frame, text="图框/标题栏")
        title_frame.pack(fill=tk.X, padx=10, pady=5)

        self.title_block_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(title_frame, text="插入图框", variable=self.title_block_var).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.project_name_var = tk.StringVar()
        self.designer_var = tk.StringVar()
        ttk.Label(title_frame, text="项目名称:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Entry(title_frame, textvariable=self.project_name_var, width=30).grid(
            row=1, column=1, sticky=tk.W, padx=10, pady=2
        )
        ttk.Label(title_frame, text="设计人:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
        ttk.Entry(title_frame, textvariable=self.designer_var, width=30).grid(
            row=2, column=1, sticky=tk.W, padx=10, pady=2
        )

    def _section_label(self, parent, text):
        ttk.Label(parent, text=text, style="Title.TLabel").pack(anchor=tk.W, padx=10, pady=(10, 2))

    # ----------------------------------------------------------------
    # 预览标签页
    # ----------------------------------------------------------------

    def _build_preview_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  数据预览  ")

        # 工具栏
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill=tk.X, padx=8, pady=(6, 2))
        ttk.Button(toolbar, text="加载 Excel 数据", command=self._load_excel_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="映射预览", command=self._preview_mapping).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清空", command=self._clear_preview).pack(side=tk.LEFT, padx=2)

        # 表格
        columns = (
            "circuit_id", "circuit_name", "load_type", "power", "current",
            "breaker", "poles", "ct_ratio", "block_name", "status",
        )
        col_names = (
            "回路编号", "回路名称", "负荷类型", "功率(kW)", "电流(A)",
            "断路器", "极数", "CT变比", "匹配图块", "状态",
        )
        col_widths = (80, 110, 70, 70, 70, 90, 50, 70, 140, 60)

        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        self.preview_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set,
        )
        tree_scroll_y.config(command=self.preview_tree.yview)
        tree_scroll_x.config(command=self.preview_tree.xview)

        for col_id, col_name, width in zip(columns, col_names, col_widths):
            self.preview_tree.heading(col_id, text=col_name)
            self.preview_tree.column(col_id, width=width, minwidth=50)

        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 行颜色
        self.preview_tree.tag_configure("ok", background="#e8f5e9")
        self.preview_tree.tag_configure("error", background="#ffebee")
        self.preview_tree.tag_configure("warning", background="#fff8e1")

        # 统计
        stats_frame = ttk.Frame(tab)
        stats_frame.pack(fill=tk.X, padx=8, pady=(2, 6))
        self.preview_stats_var = tk.StringVar(value="点击「加载 Excel 数据」开始")
        ttk.Label(stats_frame, textvariable=self.preview_stats_var, style="Info.TLabel").pack(side=tk.LEFT)

    # ----------------------------------------------------------------
    # 执行标签页
    # ----------------------------------------------------------------

    def _build_execute_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  执行  ")

        # 按钮栏
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        self.dry_run_btn = ttk.Button(
            btn_frame, text="校验预览 (Dry-Run)", command=self._run_dry_run, style="Run.TButton"
        )
        self.dry_run_btn.pack(side=tk.LEFT, padx=4)

        self.gen_btn = ttk.Button(
            btn_frame, text="生成 DWG", command=self._run_generate, style="Run.TButton"
        )
        self.gen_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self._stop_run, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=12)
        ttk.Button(btn_frame, text="打开报告", command=self._open_report).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="打开输出目录", command=self._open_output_dir).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="清空日志", command=self._clear_log).pack(side=tk.RIGHT, padx=4)

        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(tab, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress.pack(fill=tk.X, padx=8, pady=2)

        # 日志
        log_frame = ttk.LabelFrame(tab, text="运行日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 2))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=("Consolas", 9), state=tk.DISABLED, bg="#1e1e1e", fg="#cccccc",
            insertbackground="#cccccc", selectbackground="#264f78",
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 日志颜色
        self.log_text.tag_configure("DEBUG", foreground="#888888")
        self.log_text.tag_configure("INFO", foreground="#cccccc")
        self.log_text.tag_configure("WARNING", foreground="#e67e22")
        self.log_text.tag_configure("ERROR", foreground="#e74c3c")
        self.log_text.tag_configure("CRITICAL", foreground="#ff0000", font=("Consolas", 9, "bold"))

        # 结果统计
        result_frame = ttk.LabelFrame(tab, text="结果统计")
        result_frame.pack(fill=tk.X, padx=8, pady=(2, 6))

        stats_inner = ttk.Frame(result_frame)
        stats_inner.pack(fill=tk.X, padx=10, pady=6)

        self.stat_total = tk.StringVar(value="总回路: -")
        self.stat_ok = tk.StringVar(value="成功: -")
        self.stat_warn = tk.StringVar(value="警告: -")
        self.stat_err = tk.StringVar(value="跳过: -")
        self.stat_paper = tk.StringVar(value="幅面: -")
        self.stat_time = tk.StringVar(value="耗时: -")

        ttk.Label(stats_inner, textvariable=self.stat_total).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_inner, textvariable=self.stat_ok, style="Success.TLabel").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_inner, textvariable=self.stat_warn, style="Warning.TLabel").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_inner, textvariable=self.stat_err, style="Error.TLabel").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_inner, textvariable=self.stat_paper).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_inner, textvariable=self.stat_time).pack(side=tk.RIGHT)

    # ----------------------------------------------------------------
    # 日志系统
    # ----------------------------------------------------------------

    def _setup_logging(self):
        gui_handler = GUILogHandler(self.log_queue)
        gui_handler.setLevel(logging.DEBUG)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(gui_handler)

        # 同时保留控制台输出
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
        root_logger.addHandler(console)

    def _poll_log_queue(self):
        """轮询日志队列，写入日志文本框"""
        while True:
            try:
                msg, level = self.log_queue.get_nowait()
                tag = logging.getLevelName(level)
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, msg + "\n", tag)
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
            except queue.Empty:
                break
        self.root.after(100, self._poll_log_queue)

    def _append_log(self, msg: str, tag: str = "INFO"):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    # ----------------------------------------------------------------
    # 文件操作
    # ----------------------------------------------------------------

    def _browse_excel(self):
        path = filedialog.askopenfilename(
            title="选择 Excel 回路清单",
            filetypes=[("Excel 文件", "*.xlsx"), ("所有文件", "*.*")],
        )
        if path:
            self.excel_path.set(path)
            self.status_var.set(f"已选择: {os.path.basename(path)}")

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="选择输出 DWG 路径",
            filetypes=[("AutoCAD DWG", "*.dwg"), ("所有文件", "*.*")],
            defaultextension=".dwg",
        )
        if path:
            self.output_path.set(path)

    def _browse_config(self):
        path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("YAML", "*.yaml *.yml"), ("所有文件", "*.*")],
        )
        if path:
            self._load_config(path)

    def _load_default_config(self):
        config_path = os.path.join(PROJECT_ROOT, "config.yaml")
        self._load_config(config_path)

    def _load_config(self, path: str):
        try:
            self.cfg = load_config(path)
            self._sync_config_to_ui()
            self.status_var.set(f"配置已加载: {os.path.basename(path)}")
            logger.info("配置文件加载成功: %s", path)
        except ConfigError as e:
            logger.warning("配置加载失败: %s（使用默认值）", e)
            self.cfg = AppConfig()
            self._sync_config_to_ui()

    def _sync_config_to_ui(self):
        """将 AppConfig 同步到 UI 控件"""
        if not self.cfg:
            return
        self.format_auto_detect_var.set(self.cfg.excel.format_auto_detect)
        self.sheet_name_var.set(self.cfg.excel.sheet_name)
        self.default_breaker_var.set(self.cfg.excel.default_breaker_model)
        self.acad_visible_var.set(self.cfg.autocad.visible)
        self.progids_var.set(", ".join(self.cfg.autocad.progids))
        self.block_lib_path.set(self.cfg.block_library.path)
        self.block_catalog_path.set(self.cfg.block_library.catalog)
        self.default_block_var.set(self.cfg.block_library.default_block)
        self.bus_x_var.set(str(int(self.cfg.layout.bus_x)))
        self.offset_x_var.set(str(int(self.cfg.layout.block_offset_x)))
        self.spacing_var.set(str(int(self.cfg.layout.vertical_spacing)))
        self.group_sep_var.set(self.cfg.sort.group_separator_enabled)
        self.title_block_var.set(self.cfg.title_block.enabled)
        if self.cfg.output.dwg_path:
            self.output_path.set(self.cfg.output.dwg_path)

    def _sync_ui_to_config(self):
        """将 UI 控件值同步回 AppConfig"""
        if not self.cfg:
            self.cfg = AppConfig()

        self.cfg.excel.format_auto_detect = self.format_auto_detect_var.get()
        self.cfg.excel.sheet_name = self.sheet_name_var.get()
        self.cfg.excel.default_breaker_model = self.default_breaker_var.get()

        self.cfg.autocad.visible = self.acad_visible_var.get()
        self.cfg.autocad.progids = [
            p.strip() for p in self.progids_var.get().split(",") if p.strip()
        ]
        self.cfg.block_library.path = self.block_lib_path.get()
        self.cfg.block_library.catalog = self.block_catalog_path.get()
        self.cfg.block_library.default_block = self.default_block_var.get()

        try:
            self.cfg.layout.bus_x = float(self.bus_x_var.get())
            self.cfg.layout.block_offset_x = float(self.offset_x_var.get())
            self.cfg.layout.vertical_spacing = float(self.spacing_var.get())
        except ValueError:
            pass

        self.cfg.sort.group_separator_enabled = self.group_sep_var.get()
        self.cfg.title_block.enabled = self.title_block_var.get()
        self.cfg.title_block.attributes["PROJECT_NAME"] = self.project_name_var.get()
        self.cfg.title_block.attributes["DESIGNER"] = self.designer_var.get()
        self.cfg.title_block.attributes["DATE"] = datetime.now().strftime("%Y-%m-%d")

        if self.output_path.get():
            self.cfg.output.dwg_path = self.output_path.get()

        # 幅面
        paper_name = self.paper_var.get()
        if paper_name != "自动选择":
            self.cfg.layout.paper.auto_select = False
            size_map = {"A2": (594, 420), "A1": (841, 594), "A0": (1189, 841)}
            if paper_name in size_map:
                w, h = size_map[paper_name]
                self.cfg.layout.paper.sizes = [PaperSizeDef(paper_name, w, h)]
        else:
            self.cfg.layout.paper.auto_select = True

    # ----------------------------------------------------------------
    # 数据预览
    # ----------------------------------------------------------------

    def _load_excel_data(self):
        excel_path = self.excel_path.get().strip()
        if not excel_path or not os.path.isfile(excel_path):
            messagebox.showwarning("提示", "请先选择有效的 Excel 文件")
            return

        self._sync_ui_to_config()
        logger.info("正在读取 Excel: %s", excel_path)

        try:
            self.records, self.errors = excel_reader.read_and_validate(excel_path, self.cfg.excel)
        except ExcelReadError as e:
            messagebox.showerror("Excel 读取失败", str(e))
            logger.error("Excel 读取失败: %s", e)
            return

        # 填充表格
        self.preview_tree.delete(*self.preview_tree.get_children())

        for r in self.records:
            self.preview_tree.insert("", tk.END, values=(
                r.circuit_id, r.circuit_name, r.load_type.value,
                f"{r.rated_power_kw:.2f}", f"{r.rated_current_a:.2f}",
                r.breaker_model, f"{r.breaker_poles}P", r.ct_ratio,
                "-", "OK",
            ), tags=("ok",))

        for e in self.errors:
            self.preview_tree.insert("", tk.END, values=(
                e.circuit_id or "-", "-", "-", "-", "-", "-", "-", "-",
                "-", "跳过",
            ), tags=("error",))

        total = len(self.records) + len(self.errors)
        self.preview_stats_var.set(
            f"总 {total} 行: 有效 {len(self.records)} | 跳过 {len(self.errors)} | "
            f"文件: {os.path.basename(excel_path)}"
        )
        self.status_var.set(f"已加载 {len(self.records)} 条回路")

    def _preview_mapping(self):
        if not self.records:
            self._load_excel_data()
            if not self.records:
                return

        self._sync_ui_to_config()

        # 加载图块目录
        catalog = None
        try:
            catalog = block_library.load_catalog(self.cfg.block_library.catalog)
        except BlockLibraryError as e:
            logger.warning("图块目录加载失败: %s", e)

        self.mapped, warnings = block_mapper.map_circuits(
            self.records, self.cfg.block_mapping, catalog
        )

        # 更新表格中的图块列
        children = self.preview_tree.get_children()
        for i, cwb in enumerate(self.mapped):
            if i < len(children):
                item = children[i]
                vals = list(self.preview_tree.item(item, "values"))
                vals[8] = cwb.block_name  # 匹配图块列
                self.preview_tree.item(item, values=vals)

        # 统计
        block_counts = {}
        for cwb in self.mapped:
            block_counts[cwb.block_name] = block_counts.get(cwb.block_name, 0) + 1

        stats = " | ".join(f"{k}: {v}" for k, v in sorted(block_counts.items()))
        warn_count = len(warnings)
        self.preview_stats_var.set(
            f"映射完成: {len(self.mapped)} 回路, {warn_count} 警告 | {stats}"
        )

    def _clear_preview(self):
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_stats_var.set("已清空")
        self.records = []
        self.errors = []
        self.mapped = []

    # ----------------------------------------------------------------
    # 执行: Dry-Run
    # ----------------------------------------------------------------

    def _run_dry_run(self):
        excel_path = self.excel_path.get().strip()
        if not excel_path or not os.path.isfile(excel_path):
            messagebox.showwarning("提示", "请先选择有效的 Excel 文件")
            return

        self._set_running(True)
        self.progress_var.set(10)
        self.notebook.select(2)  # 切到执行标签页

        # Dry-run不需要AutoCAD，可以在后台线程执行
        thread = threading.Thread(target=self._execute_pipeline, args=(excel_path, True), daemon=True)
        thread.start()

    # ----------------------------------------------------------------
    # 执行: 生成 DWG
    # ----------------------------------------------------------------

    def _run_generate(self):
        excel_path = self.excel_path.get().strip()
        if not excel_path or not os.path.isfile(excel_path):
            messagebox.showwarning("提示", "请先选择有效的 Excel 文件")
            return

        output = self.output_path.get().strip()
        if not output:
            messagebox.showwarning("提示", "请指定输出 DWG 路径")
            return

        self._set_running(True)
        self.progress_var.set(10)
        self.notebook.select(2)

        # AutoCAD COM操作必须在主线程执行，否则会死锁
        # 使用 after() 在主线程中执行
        self.root.after(100, lambda: self._execute_pipeline_main_thread(excel_path, False))

    def _stop_run(self):
        self.is_running = False
        self._append_log("[用户中断] 正在停止...", "WARNING")

    def _execute_pipeline(self, excel_path: str, dry_run: bool):
        """后台执行完整管线"""
        start_time = time.time()

        try:
            self._sync_ui_to_config()
            self.root.after(0, lambda: self.progress_var.set(15))

            # Step 1: 读取 Excel
            logger.info("=" * 50)
            logger.info("开始处理: %s", excel_path)
            if dry_run:
                logger.info("=== DRY-RUN 模式 ===")

            records, errors = excel_reader.read_and_validate(excel_path, self.cfg.excel)
            logger.info("Excel 读取完成: 有效 %d / 跳过 %d", len(records), len(errors))
            self.root.after(0, lambda: self.progress_var.set(30))

            if not records:
                logger.error("无有效回路数据")
                self.root.after(0, lambda: self._finish_run(0, 0, 0, None, start_time))
                return

            if not self.is_running:
                return

            # Step 2: 图块目录
            catalog = None
            try:
                catalog = block_library.load_catalog(self.cfg.block_library.catalog)
            except BlockLibraryError as e:
                logger.warning("图块目录加载失败: %s", e)
            self.root.after(0, lambda: self.progress_var.set(40))

            # Step 3: 映射
            mapped, warnings = block_mapper.map_circuits(records, self.cfg.block_mapping, catalog)
            logger.info("图块映射完成: %d 回路, %d 警告", len(mapped), len(warnings))
            self.root.after(0, lambda: self.progress_var.set(50))

            if not self.is_running:
                return

            # Step 4: 属性
            attribute_builder.build_all_attributes(mapped, catalog)
            self.root.after(0, lambda: self.progress_var.set(55))

            # Step 5: 布局
            layout = layout_engine.compute(mapped, self.cfg.layout, self.cfg.sort)
            logger.info("布局完成: %s 幅面, %d 回路", layout.paper_size.name, len(layout.placements))
            self.root.after(0, lambda: self.progress_var.set(65))

            if not self.is_running:
                return

            # Step 6: 绘图 或 Dry-Run
            placements = layout.placements
            if dry_run:
                logger.info("--- Dry-Run 结果 ---")
                logger.info("幅面: %s (%.0fx%.0fmm)", layout.paper_size.name,
                            layout.paper_size.width, layout.paper_size.height)
                logger.info("回路数: %d", len(layout.placements))
                logger.info("母线: X=%.1f, Y=[%.1f ~ %.1f]",
                            layout.bus_line.x, layout.bus_line.y_start, layout.bus_line.y_end)
                logger.info("分组标签: %d 个", len(layout.group_labels))
                for p in layout.placements[:10]:
                    logger.info("  %s @ (%.1f, %.1f) -> %s", p.circuit_id, p.x, p.y, p.block_name)
                if len(layout.placements) > 10:
                    logger.info("  ... 及另外 %d 个回路", len(layout.placements) - 10)
                self.root.after(0, lambda: self.progress_var.set(90))
            else:
                # 连接 AutoCAD 绘图
                self.root.after(0, lambda: self.progress_var.set(70))
                logger.info("正在连接 AutoCAD...")
                success = self._draw_in_autocad(layout)
                if not success:
                    self.root.after(0, lambda: self._finish_run(
                        len(mapped), len(errors), len(warnings), layout, start_time
                    ))
                    return
                self.root.after(0, lambda: self.progress_var.set(90))

            # Step 7: 生成报告
            self._generate_report(errors, mapped, warnings, excel_path, placements)
            self.root.after(0, lambda: self.progress_var.set(100))

            # 完成
            self.root.after(0, lambda: self._finish_run(
                len(mapped), len(errors), len(warnings), layout, start_time
            ))

        except PDSGError as e:
            logger.error("处理失败: %s", e)
            self.root.after(0, lambda: self._finish_run(0, 0, 0, None, start_time))
        except Exception as e:
            logger.error("未预期的错误: %s", e)
            logger.debug("错误详情:", exc_info=True)
            self.root.after(0, lambda: self._finish_run(0, 0, 0, None, start_time))

    def _execute_pipeline_main_thread(self, excel_path: str, dry_run: bool):
        """在主线程执行完整管线（用于AutoCAD COM操作）"""
        start_time = time.time()
        
        try:
            self._sync_ui_to_config()
            self.progress_var.set(15)
            
            # Step 1: 读取 Excel
            logger.info("=" * 50)
            logger.info("开始处理: %s", excel_path)
            
            records, errors = excel_reader.read_and_validate(excel_path, self.cfg.excel)
            logger.info("Excel 读取完成: 有效 %d / 跳过 %d", len(records), len(errors))
            self.progress_var.set(30)
            
            if not records:
                logger.error("无有效回路数据")
                self._finish_run(0, 0, 0, None, start_time)
                return
            
            # Step 2: 图块目录
            catalog = None
            try:
                catalog = block_library.load_catalog(self.cfg.block_library.catalog)
            except BlockLibraryError as e:
                logger.warning("图块目录加载失败: %s", e)
            self.progress_var.set(40)
            
            # Step 3: 映射
            mapped, warnings = block_mapper.map_circuits(records, self.cfg.block_mapping, catalog)
            logger.info("图块映射完成: %d 回路, %d 警告", len(mapped), len(warnings))
            self.progress_var.set(50)
            
            # Step 4: 属性
            attribute_builder.build_all_attributes(mapped, catalog)
            self.progress_var.set(55)
            
            # Step 5: 布局
            layout = layout_engine.compute(mapped, self.cfg.layout, self.cfg.sort)
            logger.info("布局完成: %s 幅面, %d 回路", layout.paper_size.name, len(layout.placements))
            self.progress_var.set(65)
            
            # Step 6: AutoCAD 绘图（在主线程执行，避免COM死锁）
            self.progress_var.set(70)
            logger.info("正在连接 AutoCAD...")
            success = self._draw_in_autocad(layout)
            if not success:
                self._finish_run(len(mapped), len(errors), len(warnings), layout, start_time)
                return
            self.progress_var.set(90)
            
            # Step 7: 生成报告
            self._generate_report(errors, mapped, warnings, excel_path, layout.placements)
            self.progress_var.set(100)
            
            # 完成
            self._finish_run(len(mapped), len(errors), len(warnings), layout, start_time)
            
        except PDSGError as e:
            logger.error("处理失败: %s", e)
            self._finish_run(0, 0, 0, None, start_time)
        except Exception as e:
            logger.error("未预期的错误: %s", e)
            logger.debug("错误详情:", exc_info=True)
            self._finish_run(0, 0, 0, None, start_time)

    def _draw_in_autocad(self, layout) -> bool:
        """连接 AutoCAD 并绘图（在主线程调用可能有 COM 问题，这里仍尝试）"""
        from src.cad_drawer import CadDrawer
        cad = CadDrawer()
        try:
            cad.connect(self.cfg.autocad)
        except AcadConnectionError as e:
            logger.error("AutoCAD 连接失败: %s", e)
            logger.error("请确认 AutoCAD 已启动后重试")
            return False

        try:
            cad.open_library_as_working_doc(self.cfg.block_library)
            cad.draw(layout, self.cfg.layout)
            if self.cfg.title_block.enabled:
                cad.insert_title_block(self.cfg.title_block)
            cad.save_as(self.cfg.output.dwg_path)
            logger.info("DWG 已保存: %s", self.cfg.output.dwg_path)
        except (AcadOperationError, BlockLibraryError) as e:
            logger.error("绘图失败: %s", e)
            cad.close()
            return False

        cad.close()
        return True

    def _generate_report(self, errors, mapped, warnings, source_file, placements=None):
        try:
            report_path = self.cfg.output.report_path
            os.makedirs(os.path.dirname(os.path.abspath(report_path)), exist_ok=True)
            reporter.generate(
                errors=errors,
                mapped=mapped,
                warnings=warnings,
                source_file=source_file,
                report_path=report_path,
                placements=placements,
            )
        except Exception as e:
            logger.warning("报告生成失败: %s", e)

    def _finish_run(self, success: int, errors: int, warnings: int, layout, start_time: float):
        """运行结束回调"""
        elapsed = time.time() - start_time
        self._set_running(False)

        self.stat_total.set(f"总回路: {success + errors}")
        self.stat_ok.set(f"成功: {success}")
        self.stat_warn.set(f"警告: {warnings}")
        self.stat_err.set(f"跳过: {errors}")
        self.stat_paper.set(f"幅面: {layout.paper_size.name if layout else '-'}")
        self.stat_time.set(f"耗时: {elapsed:.1f}s")

        if success > 0:
            self.status_var.set(f"完成: 成功 {success} / 跳过 {errors}")
        else:
            self.status_var.set("处理失败")

    # ----------------------------------------------------------------
    # 辅助
    # ----------------------------------------------------------------

    def _set_running(self, running: bool):
        self.is_running = running
        state = tk.DISABLED if running else tk.NORMAL
        self.dry_run_btn.config(state=state)
        self.gen_btn.config(state=state)
        self.stop_btn.config(state=tk.NORMAL if running else tk.DISABLED)

    def _open_report(self):
        if not self.cfg:
            return
        path = os.path.abspath(self.cfg.output.report_path)
        if os.path.isfile(path):
            os.startfile(path)
        else:
            messagebox.showinfo("提示", "报告尚未生成，请先执行处理")

    def _open_output_dir(self):
        if not self.cfg:
            return
        path = os.path.dirname(os.path.abspath(self.cfg.output.dwg_path))
        if os.path.isdir(path):
            os.startfile(path)
        else:
            os.makedirs(path, exist_ok=True)
            os.startfile(path)

    def _generate_sample_catalog(self):
        path = filedialog.asksaveasfilename(
            title="保存示例图块目录",
            filetypes=[("YAML", "*.yaml")],
            defaultextension=".yaml",
            initialfile="block_catalog.yaml",
        )
        if path:
            block_library.create_sample_catalog(path)
            messagebox.showinfo("完成", f"示例图块目录已生成:\n{path}")

    def _open_block_editor(self):
        """打开图块编辑器窗口"""
        try:
            from block_editor_gui import launch_block_editor
            self._sync_ui_to_config()
            launch_block_editor(parent=self.root, cfg=self.cfg)
        except ImportError as e:
            messagebox.showerror(
                "启动失败",
                f"无法加载图块编辑器模块:\n{e}\n\n"
                f"请确认 block_editor_gui.py 存在。"
            )
        except Exception as e:
            messagebox.showerror("图块编辑器错误", str(e))

    def _open_user_guide(self):
        guide_path = os.path.join(PROJECT_ROOT, "docs", "用户手册.md")
        if os.path.isfile(guide_path):
            os.startfile(guide_path)
        else:
            messagebox.showinfo("提示", "用户手册文件不存在")

    def _show_about(self):
        messagebox.showinfo(
            "关于 PDSG",
            "PDSG — 配电柜系统图自动生成工具\n"
            "版本: 1.0.0\n\n"
            "从 Excel 回路清单自动生成 AutoCAD\n"
            "配电系统单线图。\n\n"
            "架构: 五层 Python + pyautocad (COM)\n"
            "支持: AutoCAD 2020 / 2022",
        )

    def _on_close(self):
        self.is_running = False
        self.root.destroy()


# ================================================================
# 入口
# ================================================================

def launch_gui():
    """启动 GUI"""
    root = tk.Tk()
    # 设置 DPI 感知（Windows 高 DPI 显示器）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = PDSGApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
