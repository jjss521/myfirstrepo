# PDSG 重构方案：Python + COM → C++ + ObjectARX 2022

> 配电柜系统图自动生成程序（PDSG）从"进程外 COM 驱动"重构为"进程内 ObjectARX 原生插件"的完整工程方案

**目标平台**: AutoCAD 2022 | **SDK**: ObjectARX 2022 | **语言**: C++ 17 / VS2019 | **输出**: .arx 插件 | **编制日期**: 2026-06-24

---

| 指标 | 值 |
|------|-----|
| COM 卡死根因 | **6** |
| 重构模块 | **8** |
| 迁移阶段 | **4** |
| 进程外 RPC 调用（目标） | **0** |

> **一句话结论：** 当前程序所有稳定性问题都源于"Python 进程通过 COM 跨进程驱动 AutoCAD"。改用 ObjectARX 后，插件直接运行在 AutoCAD 进程内，**跨进程 RPC、STA 线程、文件锁、硬编码 sleep、索引重排**这五类问题将**从架构上彻底消失**，无需任何重试/补丁代码。

---

## 目录

- [1. 现状诊断：COM 为何卡死](#1-现状诊断com-为何卡死)
- [2. 技术选型论证](#2-技术选型论证)
- [3. 目标架构设计](#3-目标架构设计)
- [4. 数据模型 C++ 重设计](#4-数据模型-c-重设计)
- [5. 各模块重构详细方案](#5-各模块重构详细方案)
- [6. COM→ObjectARX API 映射表](#6-comobjectarx-api-映射表)
- [7. 开发环境与构建](#7-开发环境与构建)
- [8. 迁移路线图（4 阶段）](#8-迁移路线图4-阶段)
- [9. 风险与对策](#9-风险与对策)
- [10. 测试策略](#10-测试策略)
- [11. 附录：关键代码骨架](#11-附录关键代码骨架)

---

## 1. 现状诊断：COM 为何卡死

> 从 `src/cad_drawer.py` 中提取的所有"补丁代码"，反推出 6 类卡死根因。每一类都是 COM 跨进程架构的固有缺陷，无法通过优化消除。

### 1.1 现状架构

```
Python 进程 → comtypes → COM RPC（跨进程） → AutoCAD 进程
```

Python 与 AutoCAD 是两个独立进程，所有绘图操作都要经 COM 接口跨进程通信（RPC）。这是全部问题的总根源。

### 1.2 六类卡死根因（附代码证据）

| 色码 | 根因 | 代码证据 | 本质问题 |
|------|------|----------|----------|
| 🔴 致命 | **RPC 调用被拒绝** (RPC_E_CALL_REJECTED) | 定义常量 `RPC_E_CALL_REJECTED = -2147418111`；全局 `_com_retry()` 重试包装器包裹了**每一次** COM 调用（绘图、插入块、画线、写文字、保存） | 跨进程 RPC 在 AutoCAD 忙碌时直接拒绝调用，Python 只能 sleep 后盲重试 |
| 🔴 致命 | **硬编码 sleep 等待** | `open_library_as_working_doc` 中 `time.sleep(2)`；`load_blocks` 中 `time.sleep(1.5)` × N 次、`time.sleep(2)`；`_clean_model_space` 后 `time.sleep(1)` | COM 是异步的，Python 不知道 AutoCAD 何时完成。只能靠 sleep 猜测，猜短了卡死、猜长了慢 |
| 🟡 严重 | **STA 线程模式地狱** | `_ensure_sta_com()` 处理 `RPC_E_WRONG_THREAD` / `RPC_E_CHANGED_MODE`，`CoInitialize`/`CoUninitialize` 反复切换 | COM 要求单线程单元(STA)，与 Python GUI(tkinter)多线程模型冲突，线程亲和性导致随机崩溃 |
| 🟡 严重 | **实体删除索引重排** | `_clean_model_space` 用 **20 轮循环**倒序删除，每轮检查 `Count`，因为"某些实体删除后索引重排" | COM 集合在删除时索引实时变化，无法稳定遍历。ObjectARX 用事务/迭代器无此问题 |
| 🟡 严重 | **文件锁与保存失败** | `save_as` 需先 `_close_other_documents()` 释放锁；主路径失败还要用**带时间戳的备用路径**兜底 | 跨进程持有 DWG 时文件锁状态不可控，保存常因锁冲突失败 |
| 🔵 次要 | **SendCommand 字符串注入** | `load_blocks` 用 `self.doc.SendCommand('(command "-INSERT" ...)\n')` 拼字符串导入图块 | 命令行注入不可靠（引号转义、命令状态机、UI焦点），且无法获知执行结果 |

> ⚠️ **核心结论：** 这 6 类问题**无法通过优化 Python 代码解决**——它们是"跨进程 COM"架构的必然产物。即便把 `_com_retry` 的重试次数调到 100、sleep 调到 10 秒，也只能"减少"而非"消除"卡死。唯一根治路径：**把绘图代码搬进 AutoCAD 进程内**。

---

## 2. 技术选型论证

### 2.1 三种 AutoCAD 二次开发技术对比

| 维度 | COM / ActiveX（现状） | .NET AutoCAD API | ObjectARX C++（推荐） |
|------|----------------------|------------------|----------------------|
| **运行位置** | 进程外（Python↔AutoCAD） | 进程内（DLL 加载到 acad.exe） | 🟢 进程内（.arx = DLL） |
| **通信开销** | 跨进程 RPC，高延迟 | 进程内直接调用 | 🟢 进程内直接调用，零 RPC |
| **API 完整度** | 仅暴露 ActiveX 子集 | 较完整（托管包装） | 🟢 100% 完整，含 AcGe/AcBr/AcGi |
| **性能** | 🔴 最慢（RPC 序列化） | 🟡 中等（托管层开销） | 🟢 最快（原生指针） |
| **稳定性** | 🔴 需大量重试补丁 | 🟢 稳定 | 🟢 最稳定（事务原子性） |
| **开发难度** | 🟢 低（Python） | 🟡 中（C#） | 🔴 高（C++ + 手动内存/事务管理） |
| **Excel/生态** | 🟢 pandas/openpyxl 成熟 | 🟢 EPPlus/ClosedXML 成熟 | 🔴 需第三方库或自实现 |
| **部署形态** | 外部 exe + Python 环境 | .dll + acad.exe.config | .arx 文件，APPLOAD 加载 |
| **版本绑定** | 弱（多 ProgID 探测） | 中（每版本需重编译） | 强（每版本需重编译） |

### 2.2 选型结论

> ✅ **采用 C++ + ObjectARX 2022**，理由：
> 1. **根治卡死**：进程内运行，RPC/sleep/STA/文件锁五类问题架构性消失——这是本次重构的首要目标。
> 2. **API 完整**：直接访问 `AcDbDatabase`、块表记录、事务管理器，块定义复制、属性写入、几何扫描都是原生操作，无需 SendCommand。
> 3. **用户明确指定**："采用 C++ 重新编程，利用 AutoCAD 2022 的 ObjectARX"。

> ⚠️ **.NET 方案为何不选：** 虽然 .NET 开发难度更低且也能进程内运行，但用户明确要求 C++/ObjectARX；且 C++ 方案在块表直接操作、几何计算(AcGe)、大批量实体处理上性能与控制力更强，契合"200 回路"规模。

---

## 3. 目标架构设计

### 3.1 重构后架构（进程内）

```
AutoCAD 2022 进程 → PDSG.arx 插件（进程内） → AcDb 数据库直接操作
```

PDSG.arx 作为 ObjectARX 插件加载到 AutoCAD 进程内，所有绘图操作通过 AcDb API 直接读写数据库，零跨进程通信。

### 3.2 模块划分（8 大模块）

| 模块 | 职责 | 原 Python 文件 | 重构后 C++ 实现要点 |
|------|------|---------------|-------------------|
| **数据模型** | 回路/图块/布局/配置的数据结构 | `data_model.py` | struct/class + 枚举，头文件集中定义 |
| **Excel 读取** | 读取 .xlsx，标准/转置双格式 | `excel_reader.py` | 第三方库 xlnt 或 libxlsxreader |
| **配置加载** | 解析 config.yaml + catalog.yaml | `config_loader.py` | yaml-cpp 库 |
| **图块映射** | 回路→图块名规则匹配 | `block_mapper.py` | 纯逻辑，直接移植 |
| **属性构建** | 填充图块属性字典 | `attribute_builder.py` | 纯逻辑，直接移植 |
| **布局引擎** | 坐标/母线/表格/幅面计算 | `layout_engine.py` | 纯逻辑，直接移植 |
| **绘图器（核心）** | 操作 AutoCAD 绘制 DWG | `cad_drawer.py` | 🔴 彻底重写 ObjectARX AcDb API |
| **报告生成** | HTML 处理报告 | `reporter.py` | 字符串拼接 + 模板（Jinja2→自写） |
| **命令/UI 入口** | 用户交互入口 | `main.py / gui.py` | 注册 AutoCAD 命令 + MFC 对话框 |

> **关键洞察：** 8 个模块中，**只有"绘图器"需要彻底重写**（COM→ObjectARX）。其余 7 个模块是**纯计算逻辑**，可几乎逐行移植到 C++。这意味着重构风险高度集中、可控。

### 3.3 数据流

```
Excel → CircuitRecord[] → 映射+属性 → CircuitWithBlock[] → 布局引擎 → LayoutResult → ObjectARX 绘图 → DWG + 报告
```

---

## 4. 数据模型 C++ 重设计

> 将 Python dataclass 映射为 C++ struct/class。数据模型层是其余模块的基础，必须先定型。

### 4.1 Python → C++ 类型映射规则

| Python | C++ | 说明 |
|--------|-----|------|
| `dataclass` | `struct` / `class` | 纯数据用 struct，带逻辑用 class |
| `str` | `std::wstring` / `AcString` | AutoCAD 内部用宽字符，统一用 wstring |
| `Optional[T]` | `std::optional<T>` | C++17 |
| `List[T]` | `std::vector<T>` | — |
| `Dict[str,str]` | `std::map` / `std::unordered_map` | 属性字典用 map\<wstring,wstring\> |
| `Enum(str,Enum)` | `enum class` + 转换函数 | 保留中文字符串值 |
| `float` | `double` | 坐标统一 double（mm） |

### 4.2 核心数据类设计（示意）

```cpp
// pdsg_types.h — 核心数据模型
enum class LoadType { Power, Lighting, Vfd, Ac, Socket, Spare, Capacitor };

struct CircuitRecord {
    int row_number;
    std::wstring circuit_id;
    std::wstring circuit_name;
    LoadType load_type;
    double rated_power_kw;
    double rated_current_a;
    std::wstring breaker_model;
    int breaker_poles;
    double breaker_trip_current_a;
    std::wstring ct_ratio;
    std::wstring cable_type;
    std::wstring cable_section;
    std::optional<std::wstring> vfd_model;
    std::optional<double>       vfd_power_kw;
    // ... v1.1 扩展字段 cabinet_code / contactor / ...
};

struct Placement {
    std::wstring block_name;
    double x, y;
    std::map<std::wstring, std::wstring> attributes;
    std::wstring circuit_id;
};

struct LayoutResult {
    std::vector<Placement>  placements;
    BusLine                  bus_line;
    std::vector<GroupLabel> group_labels;
    PaperSize                paper_size;
    std::optional<TableLayout> table;
};
```

---

## 5. 各模块重构详细方案

### 5.1 🔴 绘图器（核心重写）— COM → ObjectARX

> 这是本次重构的主战场。下表逐个列出原 COM 方法对应的 ObjectARX 实现方案。

| 原 COM 方法 | 痛点 | ObjectARX 实现方案 | 关键 API |
|-------------|------|-------------------|----------|
| `connect()` (GetActiveObject) | 🔴 RPC | **删除**。插件已在进程内，无需连接 | — |
| `open_library_as_working_doc` (Documents.Open + sleep) | 🔴 sleep/锁 | `acdbHostApplicationServices->workingDatabase()` 取当前库；或 `AcDbDatabase::readDwgFile()` 读取图块库到内存库 | AcDbDatabase::readDwgFile |
| `_clean_model_space` (20轮循环删除) | 🟡 索引重排 | 事务内遍历块表记录，`erase()` 每个实体。事务保证一致性，无需多轮 | AcDbBlockTableRecord + AcDbObjectIterator |
| `_scan_block_geometry` (逐个读 COM 属性) | 🔵 慢 | 打开块表记录，遍历实体，`AcDbLine::startPoint()/endPoint()` 直接取几何 | AcDbLine, AcGePoint3d |
| `load_blocks` (SendCommand 注入) | 🟡 不可靠 | `AcDbDatabase::insert()` 或 `acdbTransactionManager->wblockCloneObjects()` 从库文件克隆块定义 | AcDbDatabase::insert / wblockCloneObjects |
| `_place_block_at` (InsertBlock + GetAttributes) | 🔴 重试 | 新建 `AcDbBlockReference`，设置插入点/比例/旋转，`appendAcDbEntity` 入库；`attributeMap()` 找属性定义，新建 `AcDbAttribute` 填值 | AcDbBlockReference + AcDbAttribute |
| `draw_bus` (AddLine + Lineweight) | 🔴 重试 | 新建 `AcDbLine`，`setLineweight()`，append 入库 | AcDbLine::setLineweight |
| `_safe_add_text` (AddText + Alignment) | 🔴 重试 | 新建 `AcDbText`（或 AcDbMText 中文友好），`setAlignment()` 设置对齐 | AcDbText / AcDbMText |
| `draw_table` (线段+文字循环) | 🟡 慢 | 可改用 `AcDbTable` 原生表格实体，一次创建整表；或保持线段方案但批量 append | AcDbTable（推荐） |
| `insert_title_block` | 🟡 | 同 _place_block_at，块引用+属性 | AcDbBlockReference |
| `save_as` (SaveAs + 备用路径) | 🔴 锁/失败 | `AcDbDatabase::saveAs()` 或 `acDocManager->lockDocument()+dbSaveAs`。进程内无外部锁冲突 | AcDbDatabase::saveAs |
| `_set_paper_limits` | 🔵 | `acedSetVar(_T("LIMMIN"),...)` 或直接改系统变量 | acedSetVar |

### 5.2 📗 Excel 读取层

Python 用 openpyxl/pandas，C++ 没有等价标准库。三个方案：

| 方案 | 库 | 优点 | 缺点 |
|------|----|------|------|
| 🟢 **方案A（推荐）** | **xlnt 库**（C++ 原生 xlsx 读写库，MIT） | 纯 C++，无 COM；支持单元格/合并/格式 | 需自行编译，大体型 |
| 🔵 方案B | **libxlsxreader**（C 库） | 轻量 | 只读、格式支持有限 |
| 🟡 方案C | **OLE DB / ADO 读 Excel** | Windows 原生 | 又回到 COM（Excel 的），但非 AutoCAD，不影响主目标 |

> **双格式处理保留：** 标准格式（行=回路）和转置格式（列=回路）的自动检测逻辑、列名别名模糊匹配，全部按 `excel_reader.py` 原逻辑移植到 C++。A1 含"参数"判定转置格式的规则不变。

### 5.3 📗 配置加载层

- **库**：`yaml-cpp`（成熟开源 C++ YAML 库）
- **配置结构**：对应 `AppConfig` 及 10 个子配置类的 C++ struct，逐字段映射
- **两份配置**：`config.yaml`（主配置）+ `block_catalog.yaml`（图块目录）
- **列名别名映射**：`std::map<wstring,wstring>`，保留全部中英文别名

### 5.4 📗 图块映射 + 属性构建层

> 纯逻辑模块，几乎逐行移植。

- **映射规则**：按 `load_type + breaker_poles` 匹配，首个命中决定图块名，否则用 default_block
- **属性构建**：将 CircuitRecord 字段格式化后填入 11 个标准属性 Tag + 变频/扩展属性
- C++ 实现为自由函数，输入 `vector<CircuitRecord>`，输出 `vector<CircuitWithBlock>`

### 5.5 📗 布局引擎层

> 纯几何计算，逐行移植。

- 水平布局：回路从左到右，间距 `horizontal_spacing`，水平母线在顶部
- 分组排序：`load_type` 分组 + 自然排序（L1/L2/L10）
- 参数表格：列=回路、行=参数，列宽=间距
- 幅面自动选择：A2/A1/A0 + 横向判断
- C++ 用 `std::regex` 替代 Python `re` 实现自然排序

### 5.6 📗 报告生成层

- Python 用 Jinja2 模板，C++ 改用**字符串流拼接 + 预定义 HTML 模板常量**
- 报告内容（汇总统计/图块使用/回路清单/错误明细）数据结构不变
- 中文字符串注意用 `std::wstring` + UTF-8 写文件

### 5.7 📗 命令/UI 入口层

> 从"独立 GUI 程序"变为"AutoCAD 内命令 + 对话框"。

| 原方案 | 重构后 |
|--------|--------|
| `python main.py --gui` 启动 tkinter 窗口 | AutoCAD 命令行输入 `PDSG` 弹出 MFC 模态对话框 |
| `python main.py excel.xlsx` CLI | 命令 `PDSG_GEN`（或对话框内"生成"按钮） |
| — | 命令 `PDSG_DRYRUN` 仅校验不绘图 |
| — | 命令 `PDSG_CONFIG` 打开配置编辑 |

> ⚠️ **UI 技术选型：** ObjectARX 原生支持 **MFC**（推荐，与 SDK 模板一致）。对话框含：Excel 路径选择、输出路径、配置参数、数据预览表格、执行按钮、日志区。可用 `acedGetFileNavDialog` 或 MFC `CFileDialog` 选文件。

---

## 6. COM→ObjectARX API 映射速查表

| COM 操作 | ObjectARX 等价 API | 说明 |
|----------|-------------------|------|
| `app.ActiveDocument` | `acdbCurDwg()` | 当前图形数据库 |
| `doc.ModelSpace` | `AcDbBlockTableRecord`（*Model_Space） | 打开块表记录获取模型空间 |
| `model.AddLine(p1,p2)` | `new AcDbLine(p1,p2)` + `appendAcDbEntity` | 需事务包裹 |
| `model.InsertBlock(pt,name,sx,sy,sz,rot)` | `new AcDbBlockReference` + `setBlockName/setLocation/setScaleFactors/setRotation` | 块引用 |
| `blockRef.GetAttributes()` | `blockRef->attributeMap()` + 遍历 + `new AcDbAttribute` | 写属性需先查块定义的 AttDef |
| `doc.Blocks.Item(name)` | `AcDbBlockTable::getAt(name,...)` | 块定义查找 |
| `model.AddText(text,pt,h)` | `new AcDbText(pt,normal,text,style,h,rot)` | — |
| `doc.Documents.Open(path)` | `AcDbDatabase::readDwgFile(path)` | 读到内存库，不影响当前文档 |
| `doc.SendCommand(str)` | 🟢 **删除**，改用原生 API | 彻底告别命令注入 |
| `doc.SaveAs(path,fmt)` | `db->saveAs(path)` | 进程内无锁冲突 |
| `doc.SetVariable(name,val)` | `acedSetVar(name,res)` | 系统变量 |
| `line.Lineweight=50` | `line->setLineweight(50)` | 线宽 |
| `text.Alignment=10` | `text->setHorizontalMode(kTextMid)` | 对齐 |
| `_com_retry(fn)` | 🟢 **删除** | 无需重试 |
| `time.sleep(n)` | 🟢 **删除** | 无需等待 |
| `_ensure_sta_com()` | 🟢 **删除** | 无 COM 线程问题 |

---

## 7. 开发环境与构建

### 7.1 工具链版本（严格匹配 AutoCAD 2022）

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| AutoCAD | 2022（内部版本 24.1） | 运行宿主 |
| ObjectARX SDK | 2022（对应 acad.exe 24.1） | 从 Autodesk 开发者中心下载 |
| Visual Studio | 2019（VC++ 14.2x，v142 工具集） | **必须**用 VS2019，ARX 2022 不支持 VS2022 |
| Windows SDK | 10.0.19041+ | — |
| C++ 标准 | C++17 | 用 std::optional / std::filesystem |
| 项目类型 | Win32 DLL（.arx 即重命名 DLL） | 用 ObjectARX 工程向导 |

### 7.2 第三方库依赖

| 库 | 用途 | 集成方式 |
|----|------|---------|
| yaml-cpp | 读 config.yaml / catalog.yaml | vcpkg 或源码编译，静态链接 |
| xlnt | 读 .xlsx | vcpkg，静态链接 |
| MFC | 对话框 UI | VS2019 安装时勾选 |

### 7.3 构建产物与部署

| 对比项 | 现状（Python） | 重构后（C++ ObjectARX） |
|--------|---------------|------------------------|
| 构建产物 | Python 源码 + 依赖包 | `PDSG.arx`（单文件 DLL）+ `PDSG.resources`（可选资源） |
| 环境要求 | 需安装 Python 3.10+，需 AutoCAD 已启动 | 无需 Python 环境 |
| 加载方式 | 双击 exe | 用户在 AutoCAD 内 `APPLOAD` 加载即可 |

---

## 8. 迁移路线图（4 阶段）

> 采用"由内向外、风险隔离"策略，每阶段都可独立验证。

| 阶段 | 目标 | 工作内容 | 交付物 | 风险色码 |
|------|------|----------|--------|---------|
| **P1** | 搭骨架，跑通"Hello ARX" | 建 VS2019 工程、配 ObjectARX SDK、注册 `PDSG` 命令、弹出空对话框、能加载到 AutoCAD | 可加载的空 .arx | 🟢 低 |
| **P2** | 纯逻辑层移植（不碰 AutoCAD） | 数据模型 / Excel 读取(xlnt) / 配置(yaml-cpp) / 映射 / 属性 / 布局引擎 全部 C++ 化，单元测试覆盖 | libpdsg_core 静态库 + 测试 | 🟢 低 |
| **P3** | ObjectARX 绘图器（核心战场） | AcDb 绘图器：读图块库/清理模型空间/块引用插入/属性写入/母线/表格/图框/保存；块几何扫描 | 可生成 DWG 的 .arx | 🔴 高 |
| **P4** | UI + 报告 + 收尾 | MFC 对话框（文件选择/配置/预览/执行/日志）、HTML 报告、DryRun 命令、错误处理、文档 | 完整 PDSG.arx | 🟡 中 |

> ⚠️ **关键里程碑建议：** P2 完成后，用 **Python 旧版绘图器 + C++ 核心库** 做一次"数据层先行验证"——即 C++ 算好 LayoutResult 输出 JSON，Python 读 JSON 调 COM 绘图。这能提前发现数据模型迁移的偏差，降低 P3 风险。

---

## 9. 风险与对策

| 色码 | 风险 | 影响 | 对策 |
|------|------|------|------|
| 🔴 高 | ObjectARX 学习曲线陡 | 事务/对象指针/关闭顺序误用导致崩溃或内存泄漏 | P3 严格用 RAII 包装 AcDbObject 指针；开启 `MEMTRACE`；先抄官方 sample |
| 🔴 高 | 版本严格绑定 | ARX 2022 的 .arx 无法在 2020/2024 加载 | 明确声明仅支持 2022；如需多版本，每个版本独立编译分支 |
| 🟡 中 | xlnt/yaml-cpp 编译集成 | vcpkg 不可用时手动编译耗时；字符编码(中文路径)踩坑 | 统一用 vcpkg manifest 模式；路径统一 wstring + UTF-8 转换层 |
| 🟡 中 | 块属性写入语义差异 | COM 的 GetAttributes 与 ARX 的 attributeMap + AcDbAttribute 流程不同，易漏属性 | P3 单独写"块属性写入"测试用例，对照旧版输出逐 Tag 校验 |
| 🔵 低 | 中文显示乱码 | AcDbText 用 SimSun，但样式表/字体映射不当会出? | 统一创建 PDSG_TEXT 文字样式，字体 gbcbig.shx + bigfont |
| 🔵 低 | 用户习惯变化 | 从"双击 exe"变"AutoCAD 内 APPLOAD + 命令" | 文档 + 首次使用引导；可做 `bundle` 自动加载 |

---

## 10. 测试策略

### 10.1 分层测试

| 层 | 测试内容 | 工具 |
|----|----------|------|
| **核心逻辑层（P2）** | Excel 读取/映射/布局 计算结果与 Python 版逐字段对比 | Google Test / Catch2 |
| **绘图器层（P3）** | 生成 DWG 后用 `acdbHostApplicationServices` 反读，校验实体数/属性值/坐标 | ARX 测试命令 + 回读校验 |
| **对比回归（P3-P4）** | 同一 Excel 用旧 Python 版和新 ARX 版各生成一次，对比实体数、属性、坐标一致性 | 自写对比脚本 |
| **规模压测** | 200 回路 Excel，验证无卡死、无崩溃、耗时可接受 | — |

### 10.2 回归用例集（直接复用）

> 现有 `tests/fixtures/` 下 5 个 .xlsx 样本可直接作为 C++ 版回归输入，保证行为一致性。

---

## 11. 附录：关键代码骨架

### 11.1 命令注册与入口（arx 入口）

```cpp
// pdsg_app.cpp — ObjectARX 应用入口
#include "aced.h"
#include "rxregsvc.h"

// 注册命令 PDSG：弹出对话框
void cmdPDSG() {
    CPdsgDlg dlg;
    dlg.DoModal();
}

// 注册命令 PDSG_GEN：直接生成
void cmdPDSGGen() {
    auto cfg = pdsg::LoadConfig(L"config.yaml");
    auto records = pdsg::ReadExcel(cfg.excel);
    auto mapped   = pdsg::MapCircuits(records, cfg.block_mapping);
    pdsg::BuildAttributes(mapped);
    auto layout   = pdsg::ComputeLayout(mapped, cfg.layout, cfg.sort);

    pdsg::ArxDrawer drawer;          // ObjectARX 绘图器
    drawer.OpenLibrary(cfg.block_library);
    drawer.Draw(layout, cfg.layout);
    if (cfg.title_block.enabled)
        drawer.InsertTitleBlock(cfg.title_block, layout.paper_size);
    drawer.SaveAs(cfg.output.dwg_path);

    pdsg::GenerateReport(records, mapped, cfg);
}

// ARX 初始化：注册命令
extern "C" AcRx::AppRetCode acrxEntryPoint(AcRx::AppMsgCode msg, void* pkt) {
    switch (msg) {
    case AcRx::kInitAppMsg:
        acrxUnlockApplication(pkt);
        acedRegCmds->addCommand(L"PDSG", L"PDSG", L"PDSG", ACRX_CMD_MODAL, cmdPDSG);
        acedRegCmds->addCommand(L"PDSG", L"PDSG_GEN", L"PDSG_GEN", ACRX_CMD_MODAL, cmdPDSGGen);
        break;
    case AcRx::kUnloadAppMsg:
        acedRegCmds->removeGroup(L"PDSG");
        break;
    }
    return AcRx::kRetOK;
}
```

### 11.2 ObjectARX 绘图器核心片段（块引用+属性，无重试无 sleep）

```cpp
// arx_drawer.cpp — 对比 COM 版的 _place_block_at
void ArxDrawer::PlaceBlock(const Placement& p) {
    AcDbDatabase* db = acdbCurDwg();

    // 事务包裹，自动管理对象打开/关闭
    AcTransaction* tr = acdbTransactionManager->startTransaction();
    AcDbBlockTableRecord* ms = /* 打开 *Model_Space */;

    // 新建块引用
    AcDbBlockReference* ref = new AcDbBlockReference;
    ref->setBlockName(p.block_name.c_str());
    ref->setLocation(AcGePoint3d(p.x, p.y, 0));
    ref->setScaleFactors(AcGeScale3d(1, 1, 1));
    ref->setRotation(0);

    AcDbObjectId refId;
    ms->appendAcDbEntity(refId, ref);

    // 写属性：查块定义里的 AttDef，逐个建 Attribute
    AcDbBlockTableRecord* blkDef = /* 打开块定义 */;
    AcDbObjectIterator* it = blkDef->newIterator();
    for (; !it->done(); it->step()) {
        AcDbEntity* ent = /* 打开 */;
        auto* attDef = AcDbAttributeDefinition::cast(ent);
        if (!attDef) continue;
        auto tag = attDef->tag();
        auto it = p.attributes.find(tag.constPtr());
        if (it == p.attributes.end()) continue;

        AcDbAttribute* attr = new AcDbAttribute;
        attr->setPropertiesFrom(attDef);
        attr->setTag(tag);
        attr->setTextString(it->second.c_str());
        ref->appendAttribute(attr);   // 原子操作，无索引重排
    }
    delete it;

    acdbTransactionManager->endTransaction();   // 一次性提交
}
// 注意：全程无 _com_retry、无 time.sleep、无 SendCommand、无文件锁兜底
```

> **对比：** 原 COM 版 `_place_block_at` 含 `_com_retry` + `GetAttributes` 循环 + 异常吞咽共 ~30 行补丁代码。ObjectARX 版核心逻辑约 20 行，且**零重试、零等待、原子提交**。

### 11.3 项目目录建议

```
pdsg-arx/
├── pdsg-arx.vcxproj          # VS2019 DLL 工程
├── inc/
│   ├── pdsg_types.h          # 数据模型（对应 data_model.py）
│   ├── excel_reader.h        # Excel 读取（对应 excel_reader.py）
│   ├── config_loader.h       # 配置加载
│   ├── block_mapper.h        # 图块映射
│   ├── attribute_builder.h   # 属性构建
│   ├── layout_engine.h       # 布局引擎
│   ├── arx_drawer.h          # ObjectARX 绘图器（核心，对应 cad_drawer.py）
│   └── reporter.h            # 报告
├── src/
│   ├── pdsg_app.cpp          # ARX 入口 + 命令注册
│   ├── excel_reader.cpp
│   ├── config_loader.cpp
│   ├── block_mapper.cpp
│   ├── attribute_builder.cpp
│   ├── layout_engine.cpp
│   ├── arx_drawer.cpp        # AcDb 绘图实现
│   └── reporter.cpp
├── ui/
│   ├── PdsgDlg.cpp/.h        # MFC 主对话框
│   └── PdsgDlg.rc            # 对话框资源
├── third_party/
│   ├── yaml-cpp/
│   └── xlnt/
└── vcpkg.json                # 依赖清单
```

---

> **方案总结：** 本重构以"**消灭跨进程 COM**"为唯一核心目标，通过 ObjectARX 进程内运行从根本上消除 6 类卡死根因。8 个模块中仅绘图器需彻底重写，其余 7 个为纯逻辑可逐行移植，风险高度集中可控。建议按 4 阶段推进，P2 后用"数据层先行验证"提前暴露偏差。

---

*PDSG ObjectARX 重构方案 · 编制 2026-06-24 · 面向 AutoCAD 2022 / ObjectARX 2022 / VS2019*
