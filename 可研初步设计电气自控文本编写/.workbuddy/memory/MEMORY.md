# 项目长期记忆：市政工程设计文件电气自控生成软件

## 项目定位
本地运行的市政工程设计文件（可研/初步设计）电气与自控说明 + 设备材料表 生成器。
纯本地 Python（tkinter GUI + 命令行），后端 FastAPI+SQLAlchemy 预留作未来 Web 服务。

## 技术栈
- Python 3.13.12（WorkBuddy 内置 venv：`C:/Users/Administrator/.workbuddy/binaries/python/envs/default`）
- 解析：openpyxl + xlrd（需要系数法负荷计算）
- 生成：python-docx（4 模板 standard/compact/report/modern）
- 后端：FastAPI + SQLAlchemy + SQLite（backend/data/app.db）
- 前端：Vue3 + Vite（未来 Web，未实测）

## 目录结构
- gui.py — 桌面 GUI（工程类型/设计阶段/模板下拉 + 实时预览）
- backend/app/services/excel_parser.py — Excel 负荷解析（已修 Kx 误匹配、多 sheet 问题）
- backend/app/services/docx_generator.py — Word 生成引擎（preview/generate 共用 _build_blocks）
- generator/gen.py — 命令行工具
- backend/data/rules/*.json — 8 个规范文件（4类×2阶段）
- backend/seed_data.py — 从 rules JSON 灌库（幂等）

## 关键约定
- 设计阶段：初步设计→preliminary，可研→feasibility（config.STAGE_CODE）
- 可研阶段：非计算栏目直接渲染规范条文（轻深度）；用电负荷栏目仍按 Excel 出负荷汇总表。
- 四类工程：water_supply（给水）/ drainage（排水）/ road（道路）/ sanitation（环卫）
- 负荷计算表真实数据示例：61设备/10区域/计算负荷5002kVA/推荐 2×2500kVA。

## 易错点（已修复，备忘）
- excel_parser：COL_RULES 的 kx 关键词不能含单字母 'k'（会误匹配"功率(kW)"导致 Kx=110）。
- 多 sheet 工作簿只取第一个含设备 sheet。
- docx_generator 页码域须逐段独立 run（避免段错误）。
- 二级标题去"设计"前缀避免"电气设计设计范围"式重复（可研标题会显示"范围及内容"等，属预期）。

## 环境坑
- 沙箱偶发段错误：循环/批量命令、部分 pdfplumber 页易崩，重试或拆单条命令。
- 沙箱 safe-delete 拦截删除：临时文件需用户手动删。
