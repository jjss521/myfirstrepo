# agents-md - Work Plan

## TL;DR (For humans)

**What you'll get:** A concise `AGENTS.md` file at the repo root that tells any future OpenCode session how to build, test, and navigate this .NET solution, what AutoCAD commands exist, and what domain quirks matter.

**Why this approach:** Single file write — no existing instructions to reconcile. All content was extracted by reading every `.csproj`, entrypoint, config loader, test file, and command register in the repo.

**What it will NOT do:** Not modify any source code, config, or project files. Not add CI, README, or editor config. Not generate sample data files.

**Effort:** Quick
**Risk:** Low - single file write, no code changes
**Decisions to sanity-check:** Whether to keep this as AGENTS.md vs. opencode.json `instructions` reference; whether Chinese content notes are sufficient.

Your next move: **Approve** to proceed with writing the file. Full execution detail follows below.

---

> TL;DR (machine): Quick | Low | Create AGENTS.md at repo root with build commands, pipeline overview, AutoCAD command table, config quirks, domain conventions, and constraints.

## Scope
### Must have
- AGENTS.md at `D:\qoderwork\PDSG.NET\AGENTS.md`
- Sections: repo structure, build/test commands, pipeline (Excel→DWG), AutoCAD commands table, config/data file quirks, Excel format quirks, domain conventions (Chinese), test details, key constraints

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No changes to any `.cs`, `.csproj`, `.yaml`, `.xaml`, `.sln` files
- No new CI, README, .editorconfig, or other config files
- No generated sample data
- No long tutorials or exhaustive file trees
- No generic .NET advice (only repo-specific gotchas)

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: none (documentation file, no code to test)
- Evidence: Read the written file to verify content matches the draft findings

## Execution strategy
### Parallel execution waves
> Single todo, single wave.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Write AGENTS.md | None | None | N/A |

## Todos
> Implementation + review = ONE todo.

<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [ ] 1. Write AGENTS.md at PDSG.NET/AGENTS.md
  What to do / Must NOT do: Create AGENTS.md with the content synthesized from all exploration findings in the draft. The file must be compact, high-signal, repo-specific. Every line must answer "Would an agent likely miss this without help?" Must NOT add generic advice, code changes, or unrelated files.
  Parallelization: Wave 1 | Blocked by: none | Blocks: none
  References (executor has NO interview context - be exhaustive):
    - Draft: .omo/drafts/agents-md.md (all findings, decisions, scope)
    - Source files:
      - PDSG.sln: project listing
      - PDSG.Core/PDSG.Core.csproj: packages (ClosedXML 0.105.0, Scriban 7.2.5, YamlDotNet 18.0.0)
      - PDSG.AutoCAD/PDSG.AutoCAD.csproj: AutoCAD 2022 refs, Private=false
      - PDSG.Desktop/PDSG.Desktop.csproj: WinExe, WPF, depends on Core+AutoCAD
      - PDSG.Core.Tests/PDSG.Core.Tests.csproj: xUnit 2.5.3, coverlet 6.0.0, SDK 17.8.0
      - PDSG.AutoCAD/PdsgPlugin.cs: IExtensionApplication, registers PDSG/PDSG_DRG
      - PDSG.AutoCAD/Commands/PdsgCommands.cs: PDSG, PDSG_DRY command methods
      - PDSG.AutoCAD/Commands/BlockCommands.cs: PDSG_BLOCKS, PDSG_BCREATE, PDSG_BEDIT, PDSG_BIMPORT, PDSG_BDELETE, PDSG_BDIAG
      - PDSG.Core/Config/ConfigLoader.cs: loads config.yaml
      - PDSG.Core/Excel/ExcelReader.cs: Standard/Transposed, Chinese column headers
      - PDSG.Core/Models/Enums.cs: LoadType Chinese mappings, abbreviations
      - PDSG.Core/Mapping/BlockLibrary.cs: block_catalog.yaml reader
      - PDSG.Core/Mapping/AttributeBuilder.cs: attribute filtering by BlockDefinition
      - PDSG.AutoCAD/Drawing/CadDrawer.cs: managed API, not COM
      - PDSG.AutoCAD/Drawing/BlockEditor.cs: block prefixes LOOP_/VFD_/LGT_/AC_/SKT_/SPR_/CAP_
    - Directory listings: PDSG.Core/, PDSG.AutoCAD/, PDSG.Desktop/, PDSG.Core.Tests/
  Acceptance criteria (agent-executable):
    - File exists at D:\qoderwork\PDSG.NET\AGENTS.md
    - File is non-empty, starts with "# PDSG.NET — Agent Guide"
    - Contains all required sections: "Build & test", "Pipeline", "AutoCAD commands", "Config & data files", "Excel quirks", "Domain conventions", "Testing", "Key constraints"
    - No source code files were modified (verify with git diff --name-only)
  QA scenarios:
    - Happy: Read file to verify sections present and accurate against the draft findings
    - Failure: Check no uncommitted changes exist outside AGENTS.md
    - Evidence: .omo/evidence/task-1-agents-md.readout
  Commit: Y | docs: add AGENTS.md with repo-specific agent guidance

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit — verify the written AGENTS.md matches the scope and draft findings exactly
- [ ] F2. Content accuracy — spot-check 3 claims against source code
- [ ] F3. No collateral damage — git diff shows only AGENTS.md
- [ ] F4. Scope fidelity — no Must NOT have items were violated

## Commit strategy
Single commit: `docs: add AGENTS.md with repo-specific agent guidance`

## Success criteria
- `D:\qoderwork\PDSG.NET\AGENTS.md` exists and contains verified, high-signal guidance
- No other files modified
- All claims in the file can be traced to specific source files
