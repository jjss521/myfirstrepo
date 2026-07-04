# 负荷计算系统 v4.0 - 架构审查与改进报告

## 改进概览

| 类别 | 改动内容 | 影响文件 |
|------|---------|---------|
| 🔴 P0 安全 | pickle序列化 → JSON存储（安全可读） | `data_persistence.py` |
| 🔴 P0 安全 | `os._exit(0)` 暴力退出 → `sys.exit(0)` 正常退出 | `main_window.py` |
| 🔴 P0 性能 | `from math import sqrt` 方法内 → 模块顶部 | `models.py` |
| 🔴 P0 依赖 | 创建 `requirements.txt` | 新建 |
| 🟡 P1 结构 | 硬编码设备数据 → JSON预设文件 | `data_loader.py` + `data/presets/` |
| 🟡 P1 日志 | `print()` → `logging` 框架 | `config.py`, `data_persistence.py`, `main_window.py`, `run_load_calc.py` |
| 🟡 P1 版本 | v3.0.0 → v4.0.0 统一 | `config.py`, `build.bat` |
| 🟡 P1 废弃 | 删除 `build_load_calc.bat`（旧版） | — |
| 🟢 P2 工程化 | 创建 `.gitignore` | 新建 |
| 🟢 P2 数据 | 创建 `data/presets/` 和 `data/saves/` 目录 | 目录结构 |

## 目录结构

```
02_负荷计算系统_v4/
├── run_load_calc.py              # 入口（+logging）
├── requirements.txt              # 依赖声明（新建）
├── .gitignore                    # 版本控制（新建）
├── build.bat                     # 打包脚本（v4.0）
├── 启动.bat                      # 快速启动
├── load_calc.xls                 # 原始数据
├── data/
│   └── presets/
│       └── default_project.json  # 预设设备数据（新建，86KB）
└── load_calc/
    ├── __init__.py
    ├── config.py                 # 全局配置 + logging
    ├── models.py                 # 数据模型（sqrt导入修复）
    ├── calc_engine.py            # 核心计算引擎
    ├── data_loader.py            # JSON加载器（重构）
    ├── data_persistence.py       # JSON序列化（重构）
    ├── reference_db.py           # CJJ/T 120-2018数据库
    ├── excel_exporter.py         # Excel报表导出
    ├── excel_importer.py         # Excel设备导入
    ├── widgets.py                # UI组件
    ├── main_window.py            # 主窗口（退出修复+logging）
    └── pages/
        ├── __init__.py
        ├── page_dashboard.py     # 仪表盘（sqrt导入修复）
        ├── page_10kv.py          # 10KV总览
        ├── page_380v.py          # 380V详情
        ├── page_distribution.py  # 配电系统
        ├── page_equipment.py     # 设备管理
        ├── page_report.py        # 报表导出
        └── equipment_dialogs.py  # 编辑对话框
```

## 后续建议

1. 添加单元测试（`calc_engine.py` 为核心目标）
2. 考虑 SQLite 替代 JSON 用于运行时数据持久化
3. reference_db.py 的 Kx 数据库可独立为 JSON 配置文件
4. 创建 CI/CD pipeline（GitHub Actions）
