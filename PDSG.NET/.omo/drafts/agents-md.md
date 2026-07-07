---
slug: agents-md
status: drafting
intent: clear
pending-action: write .omo/plans/agents-md.md
approach: Single-file write — create AGENTS.md at repo root with high-signal repo-specific guidance extracted from source exploration.
---

# Draft: agents-md

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|---|---|---|---|
| Chinese is the authoring language | Keep Chinese comments/UI text; write Agent guide in English | All comments, Excel column headers, load type names, UI text are in Chinese | No — domain language |
| No CI/CD or linting | Omit from guide | No .github/workflows, no .editorconfig, no pre-commit config found | Yes if added later |
| No README existed | Agent guide fills that gap | No README.* found in tree | N/A — creating from scratch |

## Findings (cited - path:lines)

### Solution structure
- 4 projects in `PDSG.sln`: PDSG.Core (net8.0), PDSG.AutoCAD (net8.0-windows), PDSG.Desktop (net8.0-windows WinExe), PDSG.Core.Tests (net8.0 xUnit)
- AutoCAD projects reference AutoCAD 2022 DLLs at `C:\Program Files\Autodesk\AutoCAD 2022\` with `<Private>false</Private>` (PDSG.AutoCAD.csproj:15-26)
- All projects enable `<ImplicitUsings>enable</ImplicitUsings>` and `<Nullable>enable</Nullable>`
- No Directory.Build.props, no .editorconfig, no global.json, no NuGet.config

### Pipeline (Excel → DWG)
- ConfigLoader.Load("config.yaml") → AppConfig (Config/ConfigLoader.cs:17-49)
- ExcelReader.ReadAndValidate(path, cfg) → returns (CircuitRecord[], ErrorRecord[]), supports Standard & Transposed format with auto-detect (Excel/ExcelReader.cs:16-29)
- BlockLibrary.LoadCatalog("block_catalog.yaml") → BlockCatalog (Mapping/BlockLibrary.cs:17-69)
- BlockMapper.MapCircuits → (CircuitWithBlock[], ErrorRecord[]) (Mapping/BlockMapper.cs:13-57)
- AttributeBuilder.BuildAllAttributes(mapped, catalog) — in-place (Mapping/AttributeBuilder.cs:72-81)
- LayoutEngine.Compute → LayoutResult with Placements, BusLine, GroupLabels, PaperSize, Table (Layout/LayoutEngine.cs:20-94)
- CadDrawer.Connect() / Draw(layout) / SaveAs(path) — managed AutoCAD API, not COM (Drawing/CadDrawer.cs:22-256)

### AutoCAD commands
- PdsgPlugin.cs implements IExtensionApplication, registers commands on load (PdsgPlugin.cs:10-21)
- Commands: PDSG (generate), PDSG_DRY (validation-only), PDSG_BLOCKS (list), PDSG_BCREATE (create), PDSG_BEDIT (edit), PDSG_BIMPORT (import), PDSG_BDELETE (delete), PDSG_BDIAG (diagnose) — see Commands/PdsgCommands.cs, Commands/BlockCommands.cs

### NuGet dependencies (PDSG.Core)
- ClosedXML 0.105.0 (Excel reading)
- Scriban 7.2.5 (HTML report template engine)
- YamlDotNet 18.0.0 (YAML config/catalog parsing)

### Test details
- 3 test files (8 tests total), xUnit 2.5.3 + coverlet 6.0.0 + Microsoft.NET.Test.Sdk 17.8.0
- Tests cover AttributeBuilder, BlockMapper, LayoutEngine — all pure logic, no AutoCAD dependency
- No integration or end-to-end tests

### Domain-specific conventions
- Chinese: all error messages, comments, UI, load type enum names, Excel column headers
- LoadType enum mapped to Chinese: 动力/照明/变频/空调/插座/备用/电容补偿 (Models/Enums.cs:15-24)
- Block naming prefixes: LOOP_, VFD_, LGT_, AC_, SKT_, SPR_, CAP_ (Commands/BlockCommands.cs:131, Drawing/BlockEditor.cs:58)
- BlockDef attributes filter: if BlockDefinition.Attributes is non-empty, only those tags are kept (Mapping/AttributeBuilder.cs:59-64)

### Config file format (config.yaml)
- Sections: autocad, block_library, excel, block_mapping, layout, sort, output
- Block catalog: YAML with top-level `blocks:` array, each entry has name/description/applicable/attributes

## Decisions (with rationale)
| decision | rationale |
|---|---|
| Single file AGENTS.md at repo root | Standard convention, no existing instruction files |
| English guide | Agents work in English; Chinese terms noted where essential |
| Omit obvious .NET defaults | ImplicitUsings/Nullable are standard, not worth calling out |
| Include full AutoCLI command table | Agents would otherwise need to grep attributes to find them |

## Scope IN
- Create AGENTS.md at D:\qoderwork\PDSG.NET\AGENTS.md
- Content: build/test commands, pipeline overview, AutoCAD commands table, config quirks, domain conventions, constraints

## Scope OUT (Must NOT have)
- Do not rewrite any existing source code or config
- Do not add README, .editorconfig, CI config
- Do not modify any .cs, .csproj, .yaml, .xaml, .sln files
- Do not generate sample config or block data files
- Do not duplicate content better stored in opencode.json instructions

## Open questions
None — all information extracted from codebase exploration.

## Approval gate
status: awaiting-approval — ready for your okay
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
