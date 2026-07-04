# 代码审查报告 — 低压配电系统回路参数计算工具

> **审查日期**: 2026-06-18  
> **审查范围**: `lowvolt_calc.py` (1562行) + 配套文件  
> **版本**: v13  
> **审查人**: 代码审查专家 👁️

---

## 一、总体评价

这是一个经过 **13 次迭代** 的工程实用工具，核心计算逻辑正确，UI 交互设计用心（内联编辑、深色主题、快捷键支持）。但从软件工程角度看，存在几个结构性问题：**单文件 1562 行过于庞大**、**全局可变状态污染计算引擎**、以及 **多处异常吞噬导致静默错误**。建议优先处理 🔴 级问题，其余可在后续迭代中逐步改进。

---

## 二、问题清单

### 🔴 P0 — 必须修复

#### 1. 全局可变状态 — 计算引擎数据被 GUI 直接写入
**文件**: `lowvolt_calc.py`  
**位置**: Line 515-523, 526-535

```python
def _save_cable_changes(self):
    global CABLE_TABLE       # ← GUI 对话框直接修改全局计算数据
    CABLE_TABLE = new
```

**风险**: `LibraryPopup` 对话框关闭后，整个程序的计算引擎立即被覆盖。用户如果在编辑数据库时误输入非法值（如字符串代替数字），下一次计算将产生错误结果，且无回滚机制。

**建议**:
- 将 `CABLE_TABLE` / `DEVICE_TABLE` 封装为带校验的类，保存时验证所有行的数值类型
- 增加"确认覆盖"二次确认对话框
- 提供"恢复默认"按钮

---

#### 2. 异常静默吞噬 — 数据丢失风险
**位置**: Line 521, 532, 1445

```python
try:
    new.append((str(v[0]), float(v[1]), float(v[2]), float(v[3]), float(v[4])))
except: pass  # ← 任何转换失败都静默跳过，数据可能被截断
```

```python
def _recalc_all(self):
    for ci, d in enumerate(self.table.columns_data):
        try:
            ...
        except: pass  # ← 回路重算失败被静默吞噬，用户完全不知情
```

**风险**: `except: pass` 是最危险的 Python 模式之一。如果 100 条回路中有 1 条因数据格式问题重算失败，用户看到的仍是旧数据，毫不知情。

**建议**:
- 用 `except (ValueError, TypeError) as e: log_error(e); continue`
- `_recalc_all` 失败时应收集错误信息，汇总后弹窗通知用户

---

#### 3. 缺失输入校验 — 功率和长度可为负数
**位置**: `compute_row()` (Line 208) 和 `read_values()` (Line 1118)

```python
def read_values(self):
    return {
        "pe_kw": float(self.fields["pe_kw"].get().strip() or 0),  # 可以是负数
        "cable_len": int(float(self.fields["cable_len"].get().strip() or 100)),  # 可以是0或负数
    }
```

`calc_ic(pe) = pe * 2`，负功率将得出负电流，后续选型逻辑全部出错。电缆长度为 0 或负数也会导致选型异常。

**建议**: 增加合理范围校验：`pe_kw > 0`，`cable_len > 0`

---

### 🟡 P1 — 应该修复

#### 4. 单文件 1562 行 — 维护负担
整个应用程序（数据 + 计算引擎 + 7 个 GUI 类 + Excel 导出 + 全局配色）全部塞在一个文件里。任何一个改动都需要在 1500+ 行中定位。

**建议的分层结构**:
```
lowvolt_calc/
├── main.py            # 入口 + App 类
├── data.py            # CABLE_TABLE, DEVICE_TABLE, 配色常量
├── engine.py          # calc_ic, select_shell, select_cable_model, compute_row
├── models.py          # CabinetTracker, 数据类
├── ui/
│   ├── table.py       # SummaryTable
│   ├── panel.py       # InputPanel, SimpleCombo
│   ├── dialogs.py     # SpareBreakerDialog, AutoSpareDialog, LibraryPopup
│   └── widgets.py     # SimpleCombo
└── export.py          # Excel 导出逻辑
```

---

#### 5. `compute_row()` 参数过多 — 11 个参数
**位置**: Line 208

```python
def compute_row(cid, purpose, pe, cabinet_code, run_mode, dist_mode,
                core_type, cable_len, vdrop_limit, cabinet_type,
                manual_shell=None, manual_trip=None):
```

**建议**: 封装为数据类或使用 `**kwargs` 字典传递，减少函数签名长度

---

#### 6. 重复代码 — 单元格编辑逻辑
**位置**: Line 450-474 (`_edit_cable_cell`) 和 Line 475-499 (`_edit_device_cell`)

两个方法除了 `tree`、`locked` 标志、列名不同外，完全一致。约 25 行 × 2 = 50 行重复代码。

**建议**: 提取公共方法 `_edit_tree_cell(tree, locked_attr, columns)`

---

#### 7. `_full_render()` 全量重建 — 性能隐患
**位置**: Line 611

每次添加/编辑/删除任意一条回路，整个表格全部销毁重建。如果用户有 100+ 条回路，重建会明显卡顿。

**建议**:
- 增量更新：新增/删除仅操作单列，编辑仅刷新该列
- 全量重建仅保留给 `_clear_all` 和 `set_all_data`

---

#### 8. 0-based vs 1-based 列索引混用
**位置**: 全局

```python
# SummaryTable 内部以 0-based 存数据
self.columns_data[ci - 1] = data  

# 但对外接口 ci 是 1-based
def add_column(self, data):  # ci 从 1 开始
```

**建议**: 统一使用 0-based 索引，在需要显示时 `+1`

---

#### 9. `requirements.txt` 不完整
**当前内容**:
```
pyinstaller>=6.0
openpyxl>=3.1
```

**缺失**: 该程序运行依赖 `tkinter`（标准库，但 Python 安装需勾选）、`math`、`os`、`copy`、`datetime`（均为标准库，无需列出）。但 `openpyxl` 是唯一显式依赖。

**建议**: 虽然目前仅依赖 openpyxl，但应注明 Python 版本要求 (`>=3.8` 用于 f-string 和 `:=` 操作符)

---

#### 10. PyInstaller `.spec` 文件过于简陋
**文件**: `低压配电计算工具.spec`

```python
a = Analysis(
    hiddenimports=[],  # ← 空列表
    excludes=[],       # ← 空列表
    datas=[],          # ← 空列表
)
```

与负荷计算系统项目的 spec 相比，缺少：
- 无 `hiddenimports` 声明（虽然此程序依赖较少）
- 无 UPX 压缩排除项
- 无多余的 Qt/PySide 排除

**建议**: 参考负荷计算系统的 spec 补充完整配置

---

#### 11. `select_cable_model` 中的空循环
**位置**: Line 153-156

```python
for i in range(start, len(CABLE_TABLE)):
    if CABLE_TABLE[i][1] <= 0: return (...)
    if CABLE_TABLE[i][2] <= 0: return (...)
```

这个循环只是遍历校验数据合法性，但数据在程序启动时是固定的。校验逻辑应该放在数据加载阶段（`if __name__ == "__main__"` 之前），而不是每次计算都跑一遍。**这是性能微优化，非功能性 bug**。

---

### 💭 P2 — 改进建议

#### 12. 硬编码魔法数字
**位置**: 全局

```python
height=58   # 表格行高
height=56   # 电力监控行高（为什么少了2px？）
height=130  # 输入面板高度
width=180   # 列宽
MAX_E_PER_CAB = 72  # 每柜最大E数
```

**建议**: 提取为命名常量，放在文件顶部

---

#### 13. `on_change` 回调为空操作
**位置**: Line 1543

```python
def _on_table_change(self):
    pass
```

如果无意使用，应删除。如果预留扩展，应添加注释说明意图。

---

#### 14. 无类型注解
全文件 1562 行零类型注解。Python 3.8+ 支持 `typing` 模块的类型提示。

**建议**: 至少对核心函数签名添加类型注解：
```python
def calc_ic(pe: float) -> float:
    return pe * 2

def compute_row(...) -> dict[str, Any]:
```

---

#### 15. 无可测试性
所有逻辑耦合在 tkinter GUI 中。计算引擎（`calc_ic`, `select_shell`, `select_cable_model`, `compute_row`）虽然是纯函数，但没有测试覆盖。

**建议**: 将计算引擎提取到独立模块后，为关键算法编写单元测试

---

#### 16. 文件名异常
**文件**: `d:fix_typos.py` — 文件名含冒号，建议删除或改为 `fix_typos.py`

---

#### 17. 无 README 文档
项目根目录无 README.md，新用户无法快速了解：
- 项目用途
- 如何运行
- 依赖要求
- 快捷键列表（Ctrl+N, Ctrl+R, Ctrl+L, Ctrl+U）

---

## 三、代码审查流程建议

基于以上问题，建议团队建立以下审查标准：

### 提交前自查清单
- [ ] 无 `except: pass`（至少记录错误信息）
- [ ] 用户输入已校验（范围、类型）
- [ ] 无全局可变状态被 GUI 直接修改
- [ ] 新增代码无 80% 以上的重复
- [ ] 函数参数不超过 6 个（超过需封装）

### 审查关注点（按优先级）
| 优先级 | 关注项 | 检查方式 |
|--------|--------|----------|
| 🔴 | 静默异常吞噬 | grep `except:\s*(pass|$)` |
| 🔴 | 输入未校验 | 查看所有 `float()`/`int()` 转换 |
| 🟡 | 单文件 >500 行 | 建议拆分 |
| 🟡 | 函数参数 >6 个 | 建议封装数据类 |
| 🟡 | 重复代码块 | 提取公共方法 |
| 💭 | 缺失类型注解 | 补充核心函数签名 |

### 审查流程
```
开发者提交 → 自查清单 → Peer Review →
  ├─ 通过：合并
  └─ 不通过：标注优先级（🔴/🟡/💭）→ 修复 → 重新提交
```

---

## 四、总结

| 统计项 | 数值 |
|--------|------|
| 总行数 | 1562 |
| 🔴 必须修复 | 3 项 |
| 🟡 应该修复 | 8 项 |
| 💭 改进建议 | 6 项 |
| 项目成熟度 | ★★★★☆（功能完整，代码结构待优化） |

这个工具的核心计算逻辑（VBA SelectCable_Model 算法、电器选型、柜体空间管理）是扎实的，13 次迭代体现了持续改进的工程态度。当前最紧迫的是修复 🔴 级别的三个问题——特别是静默异常吞噬，这在长期使用中会导致隐蔽的数据错误。

> **审查人**: 代码审查专家 👁️  
> **中国市政中南院 · 李浩**
