---
slug: math-app-supplement
status: awaiting-approval
intent: clear
pending-action: write .omo/plans/math-app-supplement.md
approach: Review the 高数学习app (CLI + GUI versions) against standard 高等数学 curriculum, identify content gaps and feature deficiencies, and produce concrete recommendations for supplementary material and interactive features.
---

# Draft: math-app-supplement

## Components (topology ledger)
| id | outcome | status |
|---|---|---|
| app-content-review | 7 chapters covering 空间解析几何 + 微分学 identified | active |
| feature-set-review | CLI + GUI versions, matplotlib plots, sympy demos | active |
| content-gap-analysis | 积分学, 无穷级数, 常微分方程, 向量函数 are missing | active |
| feature-gap-analysis | No auto-grading, no progress tracking, no search, no formula reference, no random problem generation | active |
| pdf-textbook-audit | 2 source PDFs present; extracted .txt files are binary-garbled; PDF text extraction via pdfplumber deferred | deferred |

## Findings (cited)

### Content Coverage
- **math_tutor.py** (D:\qoderwork\高数学习app\math_tutor.py): CLI version, 7 chapters covering 向量代数→微分学应用, with sympy + matplotlib demos
- **math_tutor_gui.py** (D:\qoderwork\高数学习app\math_tutor_gui.py): GUI version, same 7 chapters + exercises chapter (8), macOS-style customtkinter UI, 1796 lines
- **read_pdf.py** (D:\qoderwork\高数学习app\read_pdf.py): 40-line PDF text extraction using pdfplumber
- **PDF textbooks**: 1.空间解析几何.pdf and 2微分学.pdf in the app directory

### Content Gaps (vs standard 高等数学 curriculum)
1. **P0 积分学** — completely absent (largest single gap, ~40% of 高数上册)
   - 不定积分 (Indefinite Integrals): basic formulas, substitution, integration by parts, partial fractions
   - 定积分 (Definite Integrals): Riemann sums, FTC, properties
   - 定积分应用: area, volume, arc length, solids of revolution
   - 广义积分 (Improper Integrals)
   - 重积分 (Multiple Integrals: double, triple)
2. **P1 无穷级数** — absent
3. **P2 常微分方程** — absent
4. **向量函数** — absent

### Feature Gaps
| # | Feature | Status | Impact |
|---|---------|--------|--------|
| F1 | 练习自动批改 | ❌ | High, low effort |
| F2 | 公式速查表 | ❌ | High, low effort |
| F3 | 随机出题 | ❌ | Medium, medium effort |
| F4 | 学习进度跟踪 | ❌ | Medium, low effort |
| F5 | 全文搜索 | ❌ | Low, medium effort |
| F6 | 代码模块化 (1796-line GUI) | ⚠️ | Maintenance risk |

### Code Quality Notes
- GUI file is 1796 lines — exceeds 250 LOC ceiling
- Heavy duplication between CLI and GUI demo functions
- No type annotations, no tests
- Windows-centric matplotlib font config
- Adding new chapters requires touching 4+ spots (button list, title map, content generator routing, sidebar)

## Decisions (with rationale)
1. **积分学 as P0** — Largest missing topic, natural successor to 微分学, meets student expectations
2. **Auto-grading as quick win** — Low effort, high engagement impact on existing content
3. **Modularize before adding content** — Current code structure makes additions fragile and error-prone
4. **Formula reference as P2** — Reuses existing content text, provides immediate utility

## Scope IN
- Review codebase thoroughly
- Identify content gaps vs standard curriculum
- Identify feature gaps
- Prioritized recommendations with rationale
- Concrete work plan

## Scope OUT
- No PDF modification
- No app rewrite
- No non-math content
- No pedagogical change
- No web/mobile port
- No user accounts or cloud sync

## Open questions
All resolved via codebase exploration — no user questions needed.

## Approval gate
status: awaiting-approval
