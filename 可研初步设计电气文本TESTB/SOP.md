# SOP.md — 市政工程设计文件电气自控自动生成系统

## 项目定位
为电气工程师贾瑟构建一套"文档管理+模板系统+Python自动生成"工具，用于将负荷计算书Excel自动转换为符合《市政公用工程设计文件编制深度规定》（2025年版）要求的电气自控说明及设备材料表Word文档。

## 工程类型覆盖
- 给水工程（净水厂/泵站/输配水管网）
- 排水工程（污水厂/泵站/管网）
- 环卫工程（垃圾焚烧厂/填埋场/转运站/渗沥液处理等）
- 道路工程（城市道路/BRT/交通枢纽/广场）

## 核心依据
《市政公用工程设计文件编制深度规定》（2025年版）— 已提取四大工程类型"初步设计"阶段的电气和自控深度要求，结构化存储于 `backend/data/rules/*.json`

## 技术栈
- 后端：Python FastAPI + SQLite
- 前端：Vue 3 + Element Plus + Vite
- 生成引擎：python-docx + openpyxl（可独立命令行运行）
- 部署：本地单机

## 项目结构
```
根目录/
├── 总体规划方案.md          ← 完整规划文档
├── backend/                  ← 后端代码
│   ├── data/rules/          ← 规范深度要求（JSON种子数据）
│   │   ├── water_supply.json
│   │   ├── drainage.json
│   │   ├── road.json
│   │   └── sanitation.json
│   ├── uploads/             ← 参考文档上传存储
│   ├── templates/           ← Word模板存储
│   └── output/              ← 生成文件输出
├── frontend/                 ← 前端代码（待创建）
└── generator/                ← Python生成引擎（可独立运行）
```

## 当前进度
- [x] 2025规范PDF解析，提取四大工程类型电气/自控深度要求
- [x] 深度要求结构化JSON种子数据
- [x] 总体规划方案文档
- [x] 后端框架搭建（FastAPI + SQLite, 4类工程/85栏目）
- [x] Python生成引擎（Excel解析 + Word生成）
- [x] 命令行工具（generator/gen.py）
- [x] Web前端（frontend/index.html, Vue3+Element Plus）
- [x] 桌面GUI（gui.py）
- [ ] 前端Vue 3工程化重构（当前为CDN单文件）
- [ ] .xls格式兼容完善
