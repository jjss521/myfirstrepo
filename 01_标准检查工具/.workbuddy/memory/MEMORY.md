# 工程建设标准有效性检查工具 — 项目记忆

## 项目概述
从 CAD/Word 截图中 OCR 识别标准编号 → 查询 csres.com 验证有效性 → 生成 TXT 报告。

## 核心架构

- **入口**: `main.py` (CLI) / `run_gui.py` (GUI 打包入口) / `gui_app.py` (GUI)
- **OCR 引擎**: `ocr_engine.py` (PaddleOCR 封装)
- **解析器**: `standard_parser.py` (正则提取 + OCR纠错 + 去重 + **文本解析**)
- **网络爬虫**: `web_scraper.py` (csres.com 搜索 + 替代信息)
- **报告生成**: `report_generator.py` (TXT 三部分报告)
- **数据模型**: `models.py` (StandardRef / ValidatedStandard 等 dataclass)
- **配置**: `config.py` (URL、正则、阈值)
- **工具**: `utils.py` (日志、限速器、重试)

## 2024-06-18: 新增文本输入功能
- `standard_parser.py`: `parse_standards_from_text()` — 纯文本 → StandardRef 列表
- `main.py`: `--text` / `--text-file` CLI 参数
- `gui_app.py`: 输入方式切换（截图/文本），文本模式下显示大文本框直接粘贴
