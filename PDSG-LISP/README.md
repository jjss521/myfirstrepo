# PDSG-LISP 配电系统图自动生成程序

## 概述

将 PDSG.NET (C#) 转换为 AutoLISP 程序，用于 AutoCAD 中自动生成配电系统图。

## 文件结构

```
PDSG-LISP/
├── pdsg-main.lsp          # 主程序（命令入口）
├── pdsg-blocks.lsp        # 图块管理模块
├── pdsg-drawing.lsp       # 绘图工具模块
├── pdsg-config.yaml       # 配置文件
├── sample-data.csv        # 示例数据文件
└── README.md              # 说明文档
```

## 安装方法

1. 将所有 `.lsp` 文件复制到 AutoCAD 支持路径
2. 将 `pdsg-config.yaml` 复制到 AutoCAD 支持路径
3. 在 AutoCAD 命令行输入 `(load "pdsg-main")` 加载程序

## 使用方法

### 加载程序
```lisp
(load "pdsg-main")
(load "pdsg-blocks")
(load "pdsg-drawing")
```

### 可用命令

| 命令 | 说明 |
|------|------|
| `PDSG` | 生成配电系统图（主命令） |
| `PDSG_DRY` | 仅校验数据，不绘图 |
| `PDSG_BLOCKS` | 列出当前图形中的图块 |
| `PDSG_BCREATE` | 创建新回路图块 |
| `PDSG_BLIST` | 列出所有回路图块 |
| `PDSG_BDIAG` | 诊断图块信息 |
| `PDSG_BSTD` | 创建标准回路图块集合 |
| `PDSG_INFO` | 显示版本信息 |

### 工作流程

1. 准备 CSV 数据文件（参考 `sample-data.csv`）
2. 在 AutoCAD 中运行 `PDSG` 命令
3. 选择 CSV 文件
4. 程序自动生成配电系统图

## CSV 数据格式

| 列名 | 说明 | 示例 |
|------|------|------|
| 回路名称 | 回路编号 | WP-1 |
| 断路器类型 | MCCB/MCB/ACB/CONTACTOR/FUSE | MCCB |
| 断路器额定电流 | 额定电流值 | 100A |
| 电缆规格 | 电缆型号 | YJV-3×35+2×16 |
| 电缆长度 | 长度(m) | 50 |
| 负荷名称 | 负荷描述 | 照明配电箱 |
| 负荷功率 | 功率值 | 30kW |
| 负荷电流 | 电流值 | 45A |

## 配置说明

编辑 `pdsg-config.yaml` 修改以下设置：

- **图纸尺寸**: 默认 A3 (420×297mm)
- **母线位置**: Y 坐标默认 220mm
- **回路间距**: 默认 35mm
- **图块映射**: 断路器类型到图块名称的对应关系

## 图块说明

程序使用以下标准回路图块：

- `LOOP_MCCB` - 塑壳断路器回路
- `LOOP_MCB` - 微型断路器回路
- `LOOP_ACB` - 空气断路器回路
- `LOOP_CONTACTOR` - 接触器回路
- `LOOP_FUSE` - 熔断器回路
- `LOOP_DEFAULT` - 默认回路

如需自定义图块，可使用 `PDSG_BCREATE` 命令创建。

## 从 PDSG.NET 转换说明

本程序将 PDSG.NET 的以下功能转换为 LISP：

| PDSG.NET 模块 | PDSG-LISP 对应 |
|---------------|----------------|
| PDSG.AutoCAD.Commands | pdsg-main.lsp |
| PDSG.Core.Excel | pdsg-main.lsp (CSV读取) |
| PDSG.Core.Mapping | pdsg-blocks.lsp |
| PDSG.Core.Layout | pdsg-main.lsp (布局计算) |
| PDSG.AutoCAD.Drawing | pdsg-drawing.lsp |

### 主要变化

1. **数据格式**: Excel → CSV（LISP 不原生支持 Excel）
2. **图块操作**: 使用 AutoCAD 原生命令替代 .NET API
3. **配置方式**: YAML 文件手动解析
4. **错误处理**: 简化为基本的条件检查

## 注意事项

1. 确保 AutoCAD 中存在所需的图块定义
2. CSV 文件编码应为 UTF-8
3. 首次运行建议使用 `PDSG_DRY` 命令校验数据
4. 如需修改布局参数，请编辑 `pdsg-config.yaml`

## 版本历史

- v1.0.0 (2026-06-27) - 初始版本，从 PDSG.NET 转换
