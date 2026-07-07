# fix-autocad-crashes - Work Plan

## TL;DR (For humans)

**What you'll get:** The PDSG.NET plugin will stop crashing AutoCAD 2022 at load time, stop freezing during drawing generation, and stop crashing when importing/deleting blocks. The fixed code will be pushed to your GitHub repo.

**Why this approach:** The #1 killer is targeting `.NET 8.0` when AutoCAD 2022 requires `.NET Framework 4.8`. Fixing that plus adding proper AutoCAD document locks and fixing three resource-handling bugs eliminates all identified crash/freeze causes.

**What it will NOT do:** Not add new features, not refactor business logic, not change NuGet packages.

**Effort:** Medium
**Risk:** Medium - target framework change affects all projects; existing tests must still pass
**Decisions to sanity-check:** Whether PDSG.Desktop should use COM automation or stay as WinExe

Your next move: **Approve** to begin execution. Full detail below.

---

> TL;DR (machine): Medium | Medium | Fix P0 target framework (net8.0 -> net48), add Document.LockDocument(), fix 3 resource bugs, add .gitignore, push to GitHub.

## Scope
### Must have
- PDSG.AutoCAD.csproj: TargetFramework net8.0-windows -> net48-windows
- PDSG.Desktop.csproj: TargetFramework net8.0-windows -> net48-windows
- PDSG.Core.csproj: TargetFramework net8.0 -> net48
- PDSG.Core.Tests.csproj: TargetFramework net8.0 -> net48
- CadDrawer.cs: Add using (doc.LockDocument()) in Draw()
- CadDrawer.cs: Optimize InsertBlock - pre-build tag->ObjectId dictionary
- CadDrawer.cs: Abort transaction if any InsertBlock fails
- BlockEditor.cs: Fix PurgeBlock - iterate all layouts not just model space
- BlockEditor.cs: Fix ImportBlocksFromDwg Dispose ordering
- BlockEditor.cs: Fix DiagnoseBlocks - single enumeration
- PdsgCommands.cs: Add using (doc.LockDocument()) in PDSG + PDSG_DRY
- Create .gitignore for .NET
- git commit + push to origin

### Must NOT have
- No new features, no API changes
- No business logic changes in PDSG.Core
- No NuGet version changes
- No CI/CD

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + dotnet build + dotnet test for all fixes
- Evidence: .omo/evidence/*.txt

## Execution strategy
### Waves
- Wave 1: TargetFramework changes (all 4 csproj) - parallel
- Wave 2: Document locks + InsertBlock optimization - parallel
- Wave 3: Resource/transaction fixes (PurgeBlock, Import, Diagnose, CadDrawer abort) - parallel
- Wave 4: .gitignore + build + test + push

### Dependency matrix
| Todo | Depends on | Blocks | Parallel with |
|---|---|---|---|
| 1. Fix TargetFramework (4 files) | None | 2,3,4 | - |
| 2. Fix DocLocks + InsertBlock | 1 | None | 3 |
| 3. Fix resource bugs (4 files) | 1 | None | 2 |
| 4. .gitignore + build+test+push | 1,2,3 | None | - |

## Todos

- [ ] 1. Fix TargetFramework in all 4 .csproj files
  What to do / Must NOT do: Change TargetFramework in all 4 project files. PDSG.Core and PDSG.Core.Tests -> net48. PDSG.AutoCAD and PDSG.Desktop -> net48-windows. Must NOT change anything else in the csproj files.
  Wave 1 | Blocked by: none | Blocks: 2,3,4
  References:
    - PDSG.AutoCAD\PDSG.AutoCAD.csproj:4 -> net48-windows
    - PDSG.Desktop\PDSG.Desktop.csproj:10 -> net48-windows
    - PDSG.Core\PDSG.Core.csproj:4 -> net48
    - PDSG.Core.Tests\PDSG.Core.Tests.csproj:4 -> net48
  Acceptance: grep TargetFramework in each csproj matches expected value; dotnet build PDSG.sln succeeds
  QA: dotnet build PDSG.sln, check no errors
  Commit: N (one combined commit at end)

- [ ] 2. Add Document.LockDocument() to CadDrawer.Draw() and PdsgCommands
  What to do / Must NOT do:
    - CadDrawer.cs: In Draw(), before StartTransaction, add: `using var docLock = _doc!.LockDocument();`
    - PdsgCommands.cs: In PdsgGenerate() and PdsgDryRun(), after null-check on doc, add: `using var docLock = doc.LockDocument();`
    - Must NOT change method signatures or behavior
  Wave 2 | Blocked by: 1 | Blocks: none | Parallel with: 3
  References:
    - CadDrawer.cs:36 (before `using var tr`)
    - PdsgCommands.cs:17 and :67 (after doc null check)
  Acceptance: grep for LockDocument in both files; dotnet build succeeds
  QA: dotnet build, verify LockDocument() call present
  Commit: N

- [ ] 3. Optimize InsertBlock - pre-build attribute dictionary
  What to do / Must NOT do:
    - CadDrawer.cs: InsertBlock method (line 103-140)
    - Before the outer attribute loop, iterate block definition entities ONCE
    - Build a `Dictionary<string, ObjectId>` mapping Tag -> AttributeDefinition ObjectId
    - Then iterate p.Attributes and look up in dictionary (O(1) per attr)
    - Must NOT throw for blocks without attributes
  Wave 2 | Blocked by: 1 | Blocks: none | Parallel with: 3
  References:
    - CadDrawer.cs:103-140
  Acceptance: InsertBlock has no nested iteration over blockDef entities per attribute; dotnet build
  QA: dotnet build, code review shows dictionary pattern
  Commit: N

- [ ] 4. Fix CadDrawer.Draw - abort transaction on block failure
  What to do / Must NOT do:
    - CadDrawer.cs:50-64: Track if ANY InsertBlock failed
    - If failed > 0: call `tr.Abort()` instead of `tr.Commit()`
    - Or: let `using var tr` auto-abort (don't call Commit)
    - Must NOT leave incomplete block references in drawing
  Wave 3 | Blocked by: 1 | Blocks: none | Parallel with: 2
  References:
    - CadDrawer.cs:50-70
  Acceptance: When block insertion fails, transaction is aborted (not committed)
  QA: Code review, dotnet build
  Commit: N

- [ ] 5. Fix PurgeBlock - iterate all layouts
  What to do / Must NOT do:
    - BlockEditor.cs:355-383: Instead of only `_db.CurrentSpaceId`, iterate ALL `BlockTableRecord` entries in the block table that are layouts (`btr.IsLayout`)
    - For each layout, scan for BlockReference with matching name and erase
    - Then erase the block definition
  Wave 3 | Blocked by: 1 | Blocks: none | Parallel with: 2
  References:
    - BlockEditor.cs:355-383
  Acceptance: PurgeBlock scans all layouts, not just model space
  QA: dotnet build, code review
  Commit: N

- [ ] 6. Fix ImportBlocksFromDwg - Dispose ordering
  What to do / Must NOT do:
    - BlockEditor.cs:241-285: Restructure to explicitly call `.Dispose()`/`.Close()` in correct order
    - `sourceTr` must be disposed/closed BEFORE `sourceDb`
    - Use explicit try/finally blocks or nested `using` scopes
  Wave 3 | Blocked by: 1 | Blocks: none | Parallel with: 2
  References:
    - BlockEditor.cs:241-285
  Acceptance: sourceDb is closed after sourceTr with explicit ordering
  QA: dotnet build, code review
  Commit: N

- [ ] 7. Fix DiagnoseBlocks - single enumeration
  What to do / Must NOT do:
    - BlockEditor.cs:308: Replace `btr.Cast<object>().Count()` with a counter variable incremented in the existing `foreach (var entId in btr)` loop
    - Eliminate the separate Count() call
  Wave 3 | Blocked by: 1 | Blocks: none | Parallel with: 2
  References:
    - BlockEditor.cs:290-353
  Acceptance: Single enumeration of btr entities, no Cast<object>().Count()
  QA: dotnet build, code review
  Commit: N

- [ ] 8. Add .gitignore and push to GitHub
  What to do / Must NOT do:
    - Create `.gitignore` at D:\qoderwork\PDSG.NET with standard .NET entries (bin/, obj/, *.user, .vs/, etc.)
    - `git add -A && git commit -m "fix: AutoCAD 2022 crash fixes - target net48, add locks, fix resource bugs"`
    - `git push origin master` (or main)
  Wave 4 | Blocked by: 1,2,3 | Blocks: none
  References:
    - No .gitignore exists at repo root
    - Remote: https://github.com/jjss521/myfirstrepo.git
  Acceptance: git push succeeds; verify on GitHub
  QA: git status shows clean; git push completes
  Commit: Y | fix: AutoCAD 2022 crash fixes - target net48, add Document.LockDocument(), fix resource bugs

## Final verification wave
- [ ] F1. dotnet build PDSG.sln succeeds
- [ ] F2. dotnet test PDSG.Core.Tests succeeds
- [ ] F3. All 7 modified source files have correct changes (spot-check)
- [ ] F4. git status shows only the expected files modified + .gitignore added
- [ ] F5. git push verified on GitHub

## Commit strategy
Single commit: `fix: AutoCAD 2022 crash fixes - target net48, add Document.LockDocument(), fix PurgeBlock/ImportBlocks/DiagnoseBlocks resource bugs, optimize InsertBlock`

## Success criteria
- PDSG.AutoCAD targets net48-windows (loadable by AutoCAD 2022)
- All drawing operations acquire Document.LockDocument()
- InsertBlock uses O(1) attribute lookup instead of O(n) scan
- Failed block insertion aborts the transaction
- PurgeBlock cleans all layouts
- ImportBlocksFromDwg has correct Dispose order
- DiagnoseBlocks enumerates entities once
- .gitignore exists
- Code is pushed to GitHub
