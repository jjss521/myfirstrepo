# 高数学习app — 内容补充与功能增强计划

## TL;DR (For humans)

**What you'll get:** A review of the 高数学习app with recommendations for (1) adding 积分学 (the largest missing chapter, ~40% of a standard 高数上册), (2) adding auto-grading to existing exercises, (3) building a formula reference sheet, (4) adding progress tracking, and (5) modularizing the codebase.

**Why this approach:** The app covers 空间解析几何 and 微分学 well — the biggest gap is 积分学 which naturally follows the current content. Feature improvements (auto-grading, formula reference) are low-effort, high-impact additions.

**What it will NOT do:** Rewrite the app, change the pedagogy, add user accounts/cloud sync, convert to web/mobile, or modify the PDF textbooks.

**Effort:** Large (5-8 days for full implementation)
**Risk:** Medium — codebase needs modularization first (GUI file is 1796 lines)
**Decisions to sanity-check:** Priority ordering of new chapters, modularization timing

Your next move: Approve this plan to start work.

---

> TL;DR (machine): LARGE effort, MEDIUM risk — review identifies 4 missing 高数 chapters and 6 feature gaps; plan recommends 积分学 as Wave 1 + auto-grading as quick win + modularization to keep code maintainable.

## Scope
### Must have
- Review of existing content coverage (7 chapters, 2 source PDFs)
- Content gap analysis vs standard 高等数学 curriculum
- Feature gap analysis
- Prioritized recommendations
- Concrete work plan

### Must NOT have
- No PDF modification
- No app rewrite
- No non-math content
- No web/mobile port
- No user accounts or cloud sync
- No framework change

---

## 综合审查报告

### 一、现有内容覆盖 ✅

| 章节 | CLI | GUI | 演示功能 |
|------|-----|-----|---------|
| 1. 向量代数 | 完整 5 节 + vector_demo() | 完整 5 节 + 6 内联演示 | 2D/3D 向量图, 点积/叉积 |
| 2. 空间曲面 | 3 节 + surfaces_demo() | 3 节 + 3D 演示按钮 | 6 种二次曲面 3D |
| 3. 直线与平面 | 3 节 + lines_planes_demo() | 3 节 + sympy 演示 | 方程求解 |
| 4. 极限与连续 | 4 节 + limits_demo() | 4 节 + 演示按钮 | 重要极限, 间断点分类 |
| 5. 导数与微分 | 4 节 + derivatives_demo() | 4 节 + 演示按钮 | 切线, 单调性, 凹凸性 |
| 6. 多元函数 | 4 节 + multivariable_demo() | 4 节 + 演示按钮 | 偏导数符号计算 |
| 7. 微分学应用 | 4 节 | 4 节 + 演示按钮 | 极值与拐点图 |
| 8. 练习题 | ❌ 无 | 8 道题 (提示+几何意义) | 交互式按钮 |

### 二、内容缺口 🔴

#### P0 — 积分学 (完全缺失, ~40% 高数上册)

| 子主题 | 重要度 | 说明 |
|--------|--------|------|
| 不定积分基本公式与性质 | **关键** | 原函数概念, 基本积分表, 线性性质 |
| 换元积分法 | **关键** | 第一类(凑微分), 第二类(三角代换) |
| 分部积分法 | **关键** | 乘积积分, 选择 u,v 技巧 |
| 有理函数的积分 | 中等 | 部分分式分解 |
| 定积分概念与性质 | **关键** | 黎曼和, 定积分定义, 估值定理 |
| 微积分基本定理 | **关键** | 牛顿-莱布尼茨公式 |
| 定积分的计算 | 中等 | 定积分换元+分部法 |
| 定积分的应用 | **关键** | 面积, 体积, 弧长, 旋转体 |
| 广义积分 | 中等 | 无穷限/无界函数积分 |
| 重积分 | 中等 | 二重(直角/极坐标), 三重(柱/球坐标) |

**代码影响:** 需在 CLI 和 GUI 中各添加 ~3 章节 (~400 行内容 + ~200 行演示)

#### P1 — 无穷级数
- 数项级数审敛法, 幂级数, 泰勒展开 (中等重要度)

#### P2 — 常微分方程
- 一阶微分方程, 二阶线性微分方程 (中等重要度)

### 三、功能缺口 🔴

| # | 功能 | 当前 | 建议 |
|---|------|------|------|
| F1 | 练习自动批改 | ❌ | 输入框 + sympy 比对 |
| F2 | 公式速查表 | ❌ | 分类可折叠卡片 |
| F3 | 随机出题 | ❌ | 参数化模板 + 难度选择 |
| F4 | 学习进度跟踪 | ❌ | JSON 持久化 + 进度条 |
| F5 | 全文搜索 | ❌ | 章节标题/内容搜索 |
| F6 | 代码模块化 | ⚠️ | 拆分 content/demos/exercises |

### 四、代码质量评级

| 维度 | 评级 | 说明 |
|------|------|------|
| 内容呈现 | ⭐⭐⭐⭐ | 教学逻辑清晰, 几何意义解释到位 |
| 可视化 | ⭐⭐⭐⭐ | matplotlib 丰富, 3D 曲面精美 |
| 代码组织 | ⭐⭐ | 单文件 1796 行, 无类型注解, 无测试 |
| 交互设计 | ⭐⭐⭐ | 美观但缺少搜索/进度/批改 |
| 跨平台 | ⭐⭐ | 字体 Windows-centric |
| 可扩展性 | ⭐ | 添加新章节需修改 4+ 处 |

### 五、优先级排序 (性价比)

| 优先级 | 项目 | 影响 | 工作量 |
|--------|------|------|--------|
| **P0** | 积分学内容 (不定/定积分) | 极高 | 大 |
| **P1** | 练习自动批改 | 高 | 小 |
| **P2** | 公式速查表 | 高 | 小 |
| **P3** | 代码模块化 | 中 | 中 |
| **P4** | 随机出题 + 进度跟踪 | 中 | 中 |
| **P5** | 无穷级数 / 常微分方程 | 中 | 大 |

---

## Execution strategy

### Wave 1 — 基础增强
- Task 1: 代码模块化重构
- Task 2: 添加积分学内容 (不定积分 + 定积分)

### Wave 2 — 交互增强
- Task 3: 练习自动批改
- Task 4: 公式速查表

### Wave 3 — 锦上添花
- Task 5: 学习进度跟踪
- Task 6: 随机出题

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. 模块化重构 | — | 2,3,4 | — |
| 2. 积分学内容 | 1 | — | 3,4 |
| 3. 自动批改 | 1 | 6 | 2,4 |
| 4. 公式速查表 | 1 | — | 2,3 |
| 5. 进度跟踪 | 1 | — | 6 |
| 6. 随机出题 | 3 | — | 5 |

---

## Todos

- [ ] 1. 代码模块化重构 math_tutor_gui.py
  What to do: 将 math_tutor_gui.py (1796 行) 拆分为 content.py (章节内容数据), demos.py (matplotlib 演示函数), exercises.py (练习题逻辑), math_tutor_gui.py (仅 UI 框架和导航). 保留 __init__.py. 不修改 math_tutor.py.
  Parallelization: Wave 1 | Blocked by: — | Blocks: 2,3,4
  References: D:\qoderwork\高数学习app\math_tutor_gui.py (full file)
  Acceptance criteria:
    1. All module imports succeed
    2. GUI launches with identical appearance and behavior
    3. All 8 chapters display correctly
    4. All demo buttons and exercise toggles work
  Commit: Y | refactor: modularize 1796-line GUI into content/demos/exercises

- [ ] 2. 添加积分学章节
  What to do: 在 CLI 和 GUI 中添加 3 新章节 "不定积分" "定积分" "定积分应用". 格式与现有一致: 定义/公式/例子/几何意义 + sympy 演示 + matplotlib 可视化. 更新侧边栏按钮, 标题映射, 内容路由. 演示包括: 不定积分表, 换元/分部法, 定积分几何意义, FTC, 旋转体.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: —
  Acceptance criteria:
    1. 3 new chapters appear in sidebar
    2. Each has 3+ subsections with formulas and geometric explanations
    3. sympy demos work (from sympy import integrate)
    4. matplotlib visualizations show correctly
  Commit: Y | feat(integrals): add indefinite/definite integral chapters

- [ ] 3. 练习自动批改
  What to do: 在 exercises.py 每个题目下方添加 CTkEntry 输入框 + "提交" 按钮. 使用 sympy 化简比对 (sp.simplify(user - correct) == 0). 处理无效输入. 保留现有提示/几何意义按钮.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 6
  Acceptance criteria:
    1. Answer input box + submit button on each exercise
    2. Correct → green feedback
    3. Wrong → red feedback (no answer reveal)
    4. Invalid → yellow format error
  Commit: Y | feat(exercises): add sympy-based auto-grading

- [ ] 4. 公式速查表
  What to do: 添加 "公式" 页面汇总所有公式, 分类可折叠卡片 (导数/积分/三角/极限/向量/曲面/中值定理). 侧边栏按钮进入.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: —
  Acceptance criteria:
    1. "公式速查" sidebar button exists
    2. All formulas from chapters 1-7 included
    3. Categories expand/collapse
  Commit: Y | feat(formula): add expandable formula reference sheet

- [ ] 5. 学习进度跟踪
  What to do: JSON 文件 (.omo/progress.json) 记录章节查看状态. 侧边栏显示进度指示点 + 进度百分比.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: —
  Acceptance criteria:
    1. Progress persists across restarts
    2. Sidebar shows colored indicators and percentage
  Commit: Y | feat(progress): add local progress tracking

- [ ] 6. 随机出题
  What to do: 预定义 10+ 题目模板 (向量/极限/导数/偏导/积分), 参数随机化, sympy 自动计算答案. 难度选择 (简单/中等/困难). 复用 task 3 批改.
  Parallelization: Wave 3 | Blocked by: 3 | Blocks: —
  Acceptance criteria:
    1. Random problem generator produces valid unique problems
    2. Auto-grading works correctly
  Commit: Y | feat(exercises): add random problem generator

---

## Final verification wave
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Manual QA — launch GUI, navigate all chapters, test exercises
- [ ] F4. Scope fidelity — no feature creep

## Commit strategy
- One commit per todo, format: <type>(<scope>): <description>
- Types: refactor, feat

## Success criteria
1. 积分学内容完整 (公式/几何意义/可视化)
2. 练习自动批改正常工作
3. 公式速查表包含所有主要公式
4. 学习进度持久化
5. 随机出题生成有效题目
6. 代码模块化为三模块
7. 所有现有功能不变
