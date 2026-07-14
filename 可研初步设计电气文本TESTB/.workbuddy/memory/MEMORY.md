# 项目记忆 — 可研初步设计电气自控文本编写

## 项目目标
构建一套软件系统，实现市政工程设计文件电气自控说明的自动生成。

## 核心规范依据
《市政公用工程设计文件编制深度规定》（2025年版）— 位于 D:\D盘\360安全浏览器下载\ 
PDF共297页，已提取四大工程类型的初步设计阶段电气/自控深度要求。

## 已提取的深度要求（结构化JSON）
- `backend/data/rules/water_supply.json` — 给水工程
- `backend/data/rules/drainage.json` — 排水工程
- `backend/data/rules/road.json` — 道路工程
- `backend/data/rules/sanitation.json` — 环卫工程

## 技术栈
- 后端：Python FastAPI + SQLite
- 前端：Vue 3 + Element Plus + Vite
- 生成引擎：python-docx + openpyxl
- 桌面GUI：tkinter（gui.py，双击启动.bat）

## 生成引擎能力（docx_generator.py）
- 4种Word模板：standard(标准)/compact(紧凑)/report(报批,含会签栏)/modern(现代蓝,含页眉)
- `generate()`写docx；`preview()`返回blocks（cover/h1-h3/p/b/table/pagebreak/sig）供GUI实时渲染
- 内容引擎：GENERIC_CONTENT通用 + TYPE_CONTENT类型特有 + 兜底合成真实陈述句（无占位符）
- 设备表数量按真实区域数计算（非公式瞎算）
- 章节编号用cn_num()顺序生成，不依赖栏目数巧合

## 四大工程类型电气/自控差异
| 类型 | 电气特点 | 自控特点 |
|------|---------|---------|
| 给水 | 标准11项电气栏目，含商业计量 | 14项自控，含智慧给水管控平台 |
| 排水 | 8项供配电，侧重可靠性和防爆 | 15项自控，含智慧排水管控平台 |
| 道路 | 侧重照明和交通管理设施 | 侧重监控/信号/智能交通 |
| 环卫 | 含保安电源/谐波保护/过电压保护 | 含仪表配管设计 |

## 负荷计算Excel约定列
设备名称、单台功率(kW)、数量、工作数量、备用数量、需要系数(Kx)、功率因数(cosφ)、安装位置、电压等级(V)、备注
