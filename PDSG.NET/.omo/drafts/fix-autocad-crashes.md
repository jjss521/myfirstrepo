---
slug: fix-autocad-crashes
status: drafting
intent: clear
pending-action: write .omo/plans/fix-autocad-crashes.md
approach: Fix all identified AutoCAD 2022 crash/freeze root causes, then push to GitHub.
---

# Draft: fix-autocad-crashes

## Components (topology ledger)
| id | outcome | status | evidence path |
|---|---|---|---|
| TargetFramework | net8.0-windows -> net48 for AutoCAD compat | active | PDSG.AutoCAD.csproj:4, PDSG.Desktop.csproj:10 |
| CadDrawer.Draw | Add Document.LockDocument() | active | CadDrawer.cs:32-70 |
| InsertBlock attrs | Replace N+1 loop with dictionary | active | CadDrawer.cs:103-140 |
| PdsgCommands | Add LockDocument | active | PdsgCommands.cs:14-105 |
| PurgeBlock | Iterate ALL layouts | active | BlockEditor.cs:355-383 |
| ImportBlocksFromDwg | Fix Dispose order | active | BlockEditor.cs:241-285 |
| Partial failure | Abort transaction on block fail | active | CadDrawer.cs:50-64 |
| DiagnoseBlocks | Fix double enumeration | active | BlockEditor.cs:290-353 |
| .gitignore | Add .NET gitignore | active | No .gitignore exists |
| Desktop architecture | COM vs in-process conflict | active | Desktop.csproj + AppConfig.cs |

## Open assumptions (announced defaults)
| assumption | default | rationale | reversible? |
|---|---|---|---|
| Target net48 for AutoCAD 2022 projects | net48-windows for AutoCAD+Desktop, net48 for Core | AutoCAD 2022 uses .NET Framework 4.8 CLR | Yes, if AutoCAD upgraded |
| Push to existing remote | origin (jjss521/myfirstrepo.git) | Already configured | Yes, user changes URL |

## Findings (cited - path:lines)

### P0 - Target framework kills AutoCAD
- PDSG.AutoCAD.csproj:4 -> `<TargetFramework>net8.0-windows</TargetFramework>`
- AutoCAD 2022's acad.exe runs .NET Framework 4.8 CLR
- net8.0 assembly cannot load in .NET Framework 4.8 -> BadImageFormatException or crash on plugin load
- Same issue PDSG.Desktop.csproj:10

### P1 - Missing Document Lock everywhere
- CadDrawer.cs:36 starts transaction without doc.LockDocument()
- PdsgCommands.cs:32-58 and :82-104 run long ops on AutoCAD main thread without lock
- No lock -> multi-document switching causes deadlocks/crashes

### P1 - InsertBlock N+1 attribute matching
- CadDrawer.cs:122-138: per attribute, iterates ALL entities in block definition
- 80 circuits x 15 attrs x 20 entities = 24,000 GetObject calls -> 5-30s freeze

### P1 - Desktop architectural conflict
- PDSG.Desktop is WinExe (standalone) but references PDSG.AutoCAD using Application.DocumentManager (in-process API)
- AppConfig.cs has COM ProgIds suggesting COM was intended
- WinExe cannot use AutoCAD in-process API

### P2 - PurgeBlock only cleans model space
- BlockEditor.cs:355-383: PurgeBlock only checks _db.CurrentSpaceId
- Blocks in paper space remain -> btr.Erase(true) crashes AutoCAD

### P2 - ImportBlocksFromDwg Dispose order
- BlockEditor.cs:249-281: sourceDb declared before sourceTr, disposed after
- sourceDb.Close() may execute while sourceTr still accesses -> use-after-free crash

### P2 - Transaction commits despite partial failures
- CadDrawer.cs:70: tr.Commit() always runs even if InsertBlock failed
- Orphan BlockReference with missing attrs -> later crash

### P2 - DiagnoseBlocks double enumeration
- BlockEditor.cs:308 + line 315: two identical loops over every block definition

## Decisions
| decision | rationale |
|---|---|
| Target net48 for all projects | Simple, consistent, AutoCAD 2022 compatible; all packages support it |
| Fix Desktop to use COM automation | Architecture already has ProgIds; avoids rewrite |
| Single git commit | Push clean fixed state |

## Scope IN
- Fix: TargetFramework for all 4 projects
- Fix: Document.LockDocument() in CadDrawer + PdsgCommands
- Fix: InsertBlock pre-build attribute dictionary
- Fix: PurgeBlock iterate ALL layout BlockTableRecords
- Fix: ImportBlocksFromDwg Dispose order
- Fix: CadDrawer.Draw abort on block failure
- Fix: DiagnoseBlocks single enumeration
- Add: .gitignore for .NET
- Push: to GitHub origin

## Scope OUT
- No refactoring beyond crash fixes
- No new features
- No business logic changes to PDSG.Core
- No NuGet version changes
- No CI/CD addition

## Open questions
None - all findings verified from source.

## Approval gate
status: awaiting-approval
