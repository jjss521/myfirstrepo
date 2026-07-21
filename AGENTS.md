# AGENTS.md — D:\qoderwork

This workspace is a loose collection of independent electrical-engineering utilities, not a unified monorepo. There is no root build/test/lint config and no shared package manager. Treat each numbered directory as its own project.

## Workspace facts

- `README.md` at the root is **binary/encrypted** (starts with `%TSD-Header-###%`). Do not rely on it for setup instructions.
- No CI workflows, pre-commit hooks, Makefile, Taskfile, or justfile exist anywhere. Do not assume any enforced command order.
- Only `01_标准检查工具` has linter/typechecker config (`ruff` + `basedpyright` in `pyproject.toml`). Other projects have none.
- Several projects keep context notes under `.workbuddy/memory/MEMORY.md` or dated `.md` files. Read those first when starting work in `01_标准检查工具`, `02_负荷计算系统_v4`, `05 配电柜设计\2026-06-17-21-49-46`, `07 EXCEL-AUTOCAD`, or any `可研初步设计电气*` project.
- Root-level `fetch_*.py` scripts are ad-hoc scrapers, not part of any project.
- `04_临时文件` is temp/test scripts (not a real project).

## Project map and entrypoints

| Directory | Stack | Run it | Build / test |
|---|---|---|---|
| `01_标准检查工具` | Python, customtkinter/PySide6, PaddleOCR | `python main.py --text "..."` or `start.bat` (installs deps + launches GUI — uses customtkinter). PySide6 variant: `python run_gui.py` | `pytest` (50 tests, project dir); `ruff check .` + `basedpyright .` via pyproject.toml |
| `02_负荷计算系统` (v3) | Python, tkinter/ttkbootstrap, JSON persistence | `python run_load_calc.py` or `启动.bat` | `build.bat` → PyInstaller |
| `02_负荷计算系统_v4` (v4) | Python, tkinter/ttkbootstrap, JSON persistence | `python run_load_calc.py` or `启动.bat` | `build.bat` → PyInstaller (adds `--add-data` for assets) |
| `03_配电系统接线图生成器` | Python, PySide6, comtypes | `python main.py` or `启动.bat` | None configured |
| `05 配电柜设计\2026-06-17-21-49-46` | Python, tkinter | `python lowvolt_calc.py` | PyInstaller via `.spec` |
| `06 excel-autocad` | Python 3.10+, setuptools | `python main.py <excel>` or `pdsg <excel>` after `pip install -e .` | `pytest` in project root |
| `07 EXCEL-AUTOCAD` | Python 3.10+ + C++ (xlnt/yaml-cpp) | Same as `06 excel-autocad` | `build_all_libs.bat` (VS 2019 x64) → `pip install -e .` → `pytest` |
| `可研初步设计电气文本编写` | Python, FastAPI (stub — rules only) | N/A (only `backend/data/rules/water_supply.json`) | N/A |
| `可研初步设计电气文本TESTB` | Python FastAPI + tkinter GUI + Vue3 frontend + macOS customtkinter variant | `python gui.py` or `启动.bat` (tkinter); `python src/macos_gui.py` (customtkinter) | `backend/requirements.txt` via pip |
| `可研初步设计电气自控文本编写` | Python FastAPI + tkinter GUI + Vue3 frontend | `python gui.py` or `启动.bat` (tkinter) | `backend/requirements.txt` via pip |
| `项目台账EXE` | Python, PySide6, SQLite | `项目台账.exe` (standalone, double-click), or `python main.py` | PyInstaller: `--onefile --windowed --name 项目台账 main.py` |
| `IMADOWNLOAD` | Python, customtkinter, Playwright, requests | `python ima_gui.py` (GUI) or `python ima_downloader.py --url <share_id>` (CLI) | `pip install requests playwright` + `python -m playwright install chromium` |
| `PDSG.NET` | C# .NET Framework 4.8 (WPF desktop + AutoCAD plugin) | `dotnet build PDSG.sln` | `dotnet test PDSG.Core.Tests` |
| `PDSG-LISP` | AutoLISP | Load `pdsg-main.lsp` in AutoCAD, run `PDSG` command | N/A |
| `高数学习app` | Python, customtkinter, sympy, matplotlib | `python math_tutor.py` or `python math_tutor_gui.py` | None configured |

## Parallel implementation notes

- `02_负荷计算系统` and `02_负荷计算系统_v4` are parallel major versions (v3 vs v4) of the same load-calc tool. v4 adds JSON persistence, logging, and structured project layout.
- `06 excel-autocad` and `07 EXCEL-AUTOCAD` are parallel Python/COM implementations. `07` adds native C++ libraries (`xlnt`, `yaml-cpp`) that must be built before use.
- `可研初步设计电气文本编写` → `可研初步设计电气文本TESTB` → `可研初步设计电气自控文本编写` form an evolution of the municipal engineering doc-gen system. TESTB is the active dev branch; 自控文本编写 is a parallel sibling.

## PDSG-specific conventions (`06 excel-autocad` / `07 EXCEL-AUTOCAD`)

- **Always run `--dry-run` first** before connecting to AutoCAD; real runs require AutoCAD to be fully loaded.
- AutoCAD COM ProgIDs are version-specific and tried in fallback order (`AutoCAD.Application.24.1`, `23.1`, etc.).
- Excel sheet name fallback: `低压配电系统` → `回路清单`.
- Block names are strict: `LOOP_PWR_3P_01`, `LOOP_VFD_3P_01`, `LOOP_LGT_1P_01`, etc.
- Block attributes are ALL_CAPS with underscores: `CIRCUIT_ID`, `BREAKER_MODEL`, `CABLE_SECTION`, etc.
- Circuit sort order: 动力 → 变频 → 空调 → 照明 → 插座 → 备用 → 电容补偿.
- Per-circuit errors are skipped and logged; environment/connection errors abort.

## 可研初步设计电气文本 projects — key conventions

These three projects generate municipal engineering electrical/control design docs (`python-docx` output). They share common conventions:

- **Design stage codes**: 初步设计 → `preliminary`, 可研 → `feasibility` (in `config.py` `STAGE_CODE`).
- **Rule JSON structure**: 4 project types (`water_supply`, `drainage`, `road`, `sanitation`) × 2 design stages, stored in `backend/data/rules/*.json`.
- **Seed DB**: `python backend/seed_data.py` loads rules JSON into SQLite (idempotent).
- **Word templates**: 4 variants — `standard`, `compact`, `report` (with sign-off column), `modern` (blue header).
- **Feasibility stage**: non-calculation sections render regulation text verbatim; load calculation sections still use Excel-derived summary tables.
- **Load calc Excel columns**: 设备名称, 单台功率(kW), 数量, 工作数量, 备用数量, 需要系数(Kx), 功率因数(cosφ), 安装位置, 电压等级(V), 备注.

### 可研 projects — known pitfalls (from workbuddy)

- **excel_parser COL_RULES**: Kx keywords must NOT contain single letter `'k'` (will mis-match column header `"功率(kW)"` and produce Kx=110). Use full word `需要系数` or composite patterns.
- **Multi-sheet workbooks**: Only the first sheet containing equipment data is read. Others are ignored.
- **docx_generator page fields**: Word page-number fields must be per-paragraph independent runs. One run per paragraph or it causes segment faults in Word.
- **Secondary title de-duplication**: Section titles automatically strip `设计` prefix to avoid repeats like `电气设计设计范围`. This is expected behavior.
- **Sandbox occasional segfault**: pdfplumber batch processing and large loop commands may crash. Rerun or split into single commands.

## Testing

- `01_标准检查工具` (pytest, 50 tests), `06 excel-autocad` / `07 EXCEL-AUTOCAD` (pytest), and `PDSG.NET` (dotnet test) are the only projects with tests.
- `pyproject.toml` defines `testpaths = ["tests"]` and `python_files = ["test_*.py"]` for pytest-enabled projects.
- Tests add the project root to `sys.path` in `tests/conftest.py`; they are designed to run from the project directory with `pytest`, not necessarily after `pip install -e .`.
- AutoCAD is mocked; Excel reading uses real `.xlsx` fixtures generated by `tests/generate_fixtures.py`.
- `PDSG.NET` tests: `dotnet test PDSG.Core.Tests` (nunit, 3 test files covering attribute builder, block mapper, layout engine).

## Gotchas

- `07 EXCEL-AUTOCAD` contains vendored C++ dependencies (`vcpkg/`, `xlnt/`, `yaml-cpp/`). Build outputs go to `third_party/` which is gitignored.
- `PDSG.NET` hardcodes AutoCAD 2022 DLL paths (`C:\Program Files\Autodesk\AutoCAD 2022\`). Builds will fail without AutoCAD installed or without retargeting.
- PaddleOCR in `01_标准检查工具` downloads ~1 GB of models on first run.
- Several GUI apps assume Windows (`comtypes`, `pywin32`, PyInstaller one-dir/one-file builds).
- **PySide6 thread safety**: The `01_标准检查工具` PySide6 GUI runs pipeline in a `threading.Thread`. QWidget methods (`setPlainText`, `setCurrentIndex`, etc.) must NOT be called from a non-main thread. Use `QTimer.singleShot(0, lambda: ...)` or signals to delegate to the main thread. Direct calls cause `QObject::startTimer` errors and crash the GUI.
- `IMADOWNLOAD` requires Playwright with Chromium browser installed (`python -m playwright install chromium`).
- `项目台账EXE` uses `PySide6` + `PyInstaller` one-file build. The `.exe` and `project_ledger.db` must stay in the same directory.
