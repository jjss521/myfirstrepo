#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练习题模块 —— 8 道精选题的数据和卡片渲染。
支持答案自动批改（需 sympy）。
"""

import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkEntry

import math
import random

from mac_colors import MacColors

# ══════════════════════════════════════════════════════════════
#  Sympy 可用性检测
# ══════════════════════════════════════════════════════════════

try:
    import sympy as sp
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False
    sp = None

# ══════════════════════════════════════════════════════════════
#  练习题数据: (主题, 题目, 提示, 几何意义)
# ══════════════════════════════════════════════════════════════

EXERCISE_DATA = [
    (
        "向量代数",
        "已知 a={1,2,-1}, b={2,-1,3}, 求:\n(1) a·b   (2) a×b   (3) a与b的夹角",
        "点积 = 1×2+2×(-1)+(-1)×3 = -1\n叉积 = 用行列式计算\n夹角用 cosθ = (a·b)/(|a|·|b|)",
        "【几何意义】\n• a·b = -1 表示两向量夹角为钝角（投影方向相反）\n• a×b 的模 = 以a,b为边的平行四边形面积\n• 夹角θ是两向量在平面上张开的角度",
    ),
    (
        "空间曲面",
        "曲线 y²=2pz 绕 z 轴旋转，求旋转曲面方程",
        "绕 z 轴旋转: 用 ±√(x²+y²) 替换 y\n得 x²+y²=2pz (旋转抛物面)",
        "【几何意义】\n• 旋转曲面上每个点到z轴的距离相等\n• 截面是圆，越往上圆越大\n• 像一个碗，开口向上",
    ),
    (
        "直线与平面",
        "求过点(1,2,3)且与平面 2x+y-z+4=0 垂直的直线方程",
        "直线方向向量 = 平面法向量 = (2,1,-1)\n对称式: (x-1)/2 = (y-2)/1 = (z-3)/(-1)",
        "【几何意义】\n• 直线方向与平面法向量平行\n• 直线像一根针，垂直穿过平面\n• 法向量指向平面的「正面」方向",
    ),
    (
        "极限",
        "求 lim(x→0) [sin(3x)/sin(5x)]",
        "用等价无穷小: sin(3x)~3x, sin(5x)~5x\n结果 = 3/5",
        "【几何意义】\n• sin(3x) 在x→0时近似为 3x（小角度近似）\n• 比值就是两个无穷小的「速度比」\n• 几何上：两条曲线在原点处的斜率比",
    ),
    (
        "导数",
        "求 y = e^(sinx) · ln(x²+1) 的导数",
        "用乘法法则: (uv)' = u'v + uv'\n注意链式法则",
        "【几何意义】\n• 导数 = 曲线在该点的切线斜率\n• e^(sinx) 的导数描述其增长率\n• ln(x²+1) 的导数描述其变化快慢\n• 乘积的导数 = 两函数变化率的组合",
    ),
    (
        "隐函数求导",
        "x²+y²=1, 求 dy/dx",
        "两边对x求导: 2x+2y·(dy/dx)=0\ndy/dx = -x/y",
        "【几何意义】\n• x²+y²=1 是单位圆\n• dy/dx = -x/y 是圆上某点的切线斜率\n• 在(1,0)处斜率为0（水平切线）\n• 在(0,1)处斜率不存在（垂直切线）",
    ),
    (
        "极值",
        "求 f(x) = x³-3x 的极值",
        "f'(x) = 3x²-3 = 3(x-1)(x+1)\n驻点 x=±1\nf''(1)=6>0→极小值\nf''(-1)=-6<0→极大值",
        "【几何意义】\n• 极值点是曲线的「山顶」或「谷底」\n• f'(x)=0 表示切线水平（山顶/谷底）\n• f''(x)判断凹凸：上凸→极大，下凸→极小\n• 几何上：曲线先上升后下降=极大，反之=极小",
    ),
    (
        "偏导数",
        "z = x²y + sin(xy), 求 ∂z/∂x, ∂z/∂y",
        "∂z/∂x = 2xy + y·cos(xy)\n∂z/∂y = x² + x·cos(xy)",
        "【几何意义】\n• ∂z/∂x：沿x方向切面的斜率\n• ∂z/∂y：沿y方向切面的斜率\n• 偏导数是「固定一个变量」时的变化率\n• 几何上：曲面在某点沿两个方向的陡峭程度",
    ),
]

# ══════════════════════════════════════════════════════════════
#  正确答案 (sympy 可解析形式)
# ══════════════════════════════════════════════════════════════

CORRECT_ANSWERS = [
    "-1",                    # 题1: a·b = -1
    "x**2 + y**2 = 2*p*z",  # 题2: 旋转抛物面
    "(x-1)/2 = (y-2)/1 = (z-3)/(-1)",  # 题3: 直线对称式
    "3/5",                   # 题4: sin(3x)/sin(5x) → 3/5
    "exp(sin(x))*cos(x)*log(x**2+1) + exp(sin(x))*(2*x)/(x**2+1)",  # 题5: e^(sinx)·ln(x²+1) 的导数
    "-x/y",                  # 题6: dy/dx = -x/y
    "2",                     # 题7: 极小值 f(1)=-2, 极大值 f(-1)=2 (答案可以填 -2 或 2)
    "2*x*y + y*cos(x*y)",   # 题8: ∂z/∂x
]

# 某些题目有多个等价的正确答案
ACCEPTABLE_ANSWERS = {
    7: ["-2"],  # 题7: 极小值 -2 也算对
}


# ══════════════════════════════════════════════════════════════
#  随机出题状态
# ══════════════════════════════════════════════════════════════

_random_state = {
    'card_frame': None,
    'correct_answer': '',
    'acceptable_answers': [],
}


def _destroy_random_card():
    """销毁当前随机练习题卡片。"""
    if _random_state['card_frame'] is not None:
        try:
            _random_state['card_frame'].destroy()
        except Exception:
            pass
        _random_state['card_frame'] = None


# ══════════════════════════════════════════════════════════════
#  随机出题模板生成器 (12 个)
# ══════════════════════════════════════════════════════════════

def _rand_ints(n, lo, hi):
    """生成 n 个在 [lo, hi] 内的非零随机整数。"""
    result = []
    for _ in range(n):
        v = 0
        while v == 0:
            v = random.randint(lo, hi)
        result.append(v)
    return result


def _gen_vector_dot(difficulty):
    """向量点积 a·b"""
    ranges = {'easy': (1, 5), 'medium': (2, 10), 'hard': (3, 15)}
    lo, hi = ranges.get(difficulty, (2, 10))
    a1, a2, a3 = _rand_ints(3, lo, hi)
    b1, b2, b3 = _rand_ints(3, lo, hi)
    problem = f"已知 a = {{{a1}, {a2}, {a3}}}, b = {{{b1}, {b2}, {b3}}}，求 a·b"
    dot = a1 * b1 + a2 * b2 + a3 * b3
    sign_hint = ">0 → 锐角" if dot > 0 else ("<0 → 钝角" if dot < 0 else "=0 → 垂直")
    hint = (
        f"a·b = {a1}×{b1} + ({a2})×({b2}) + ({a3})×({b3})\n"
        f"= {a1*b1} + {a2*b2} + {a3*b3} = {dot}\n"
        f"({sign_hint})"
    )
    geometry = (
        "【几何意义】\n"
        "• a·b = |a||b|cosθ\n"
        "• 正数 → 锐角 ，负数 → 钝角 ，零 → 垂直\n"
        "• 点积反映两个向量在方向上的投影关系"
    )
    return (problem, hint, geometry, str(dot), [])


def _gen_vector_cross_mag(difficulty):
    """向量叉积模长 |a×b|"""
    ranges = {'easy': (1, 3), 'medium': (2, 8), 'hard': (3, 12)}
    lo, hi = ranges.get(difficulty, (2, 8))
    a1, a2, a3 = _rand_ints(3, lo, hi)
    b1, b2, b3 = _rand_ints(3, lo, hi)
    problem = f"已知 a = {{{a1}, {a2}, {a3}}}, b = {{{b1}, {b2}, {b3}}}，求 |a×b|"
    cx = a2 * b3 - a3 * b2
    cy = a3 * b1 - a1 * b3
    cz = a1 * b2 - a2 * b1
    mag_sq = cx ** 2 + cy ** 2 + cz ** 2
    root = int(math.isqrt(mag_sq))
    if root * root == mag_sq:
        ans = str(root)
    elif HAS_SYMPY:
        ans = f"sqrt({mag_sq})"
    else:
        ans = f"sqrt({mag_sq})"
    hint = (
        f"a×b = ({cx}, {cy}, {cz})\n"
        f"|a×b| = √({cx}² + ({cy})² + ({cz})²) = √{mag_sq}"
    )
    if root * root == mag_sq:
        hint += f" = {root}"
    geometry = (
        "【几何意义】\n"
        "• |a×b| = 以 a, b 为邻边的平行四边形面积\n"
        "• |a×b| = |a||b|sinθ\n"
        "• 方向遵循右手定则"
    )
    return (problem, hint, geometry, ans, [])


def _gen_limit_sin(difficulty):
    """极限 lim(x→0) sin(kx)/sin(mx)"""
    ranges = {'easy': (1, 5), 'medium': (3, 10), 'hard': (5, 15)}
    lo, hi = ranges.get(difficulty, (3, 10))
    k, m = _rand_ints(2, lo, hi)
    while k == m:
        m = random.randint(lo, hi)
        if m == 0:
            m = 1
    problem = f"求 lim(x→0) [sin({k}x) / sin({m}x)]"
    if HAS_SYMPY:
        ans = str(sp.Rational(k, m))
    else:
        ans = f"{k}/{m}"
    hint = (
        f"等价无穷小替换: sin({k}x) ~ {k}x , sin({m}x) ~ {m}x\n"
        f"原式 ≈ lim(x→0) ({k}x)/({m}x) = {k}/{m}"
    )
    geometry = (
        "【几何意义】\n"
        f"• sin({k}x) 在 x=0 附近近似为直线 y={k}x\n"
        f"• sin({m}x) 在 x=0 附近近似为直线 y={m}x\n"
        "• 极限 = 两条近似直线的斜率比"
    )
    return (problem, hint, geometry, ans, [])


def _gen_limit_e(difficulty):
    """重要极限 lim(x→∞) (1 + a/x)^(bx) → e^(ab)"""
    ranges = {'easy': (1, 3), 'medium': (2, 5), 'hard': (3, 8)}
    lo, hi = ranges.get(difficulty, (2, 5))
    a, b = _rand_ints(2, lo, hi)
    problem = f"求 lim(x→∞) (1 + {a}/x)^({b}x)"
    if HAS_SYMPY:
        ans = f"exp({a * b})"
    else:
        ans = f"exp({a * b})"
    hint = (
        f"利用重要极限: lim(n→∞) (1 + k/n)^n = e^k\n"
        f"令 k = {a}, 指数中有 {b}x\n"
        f"= [ (1 + {a}/x)^x ]^{b} → e^({a}×{b}) = e^{a*b}"
    )
    geometry = (
        "【几何意义】\n"
        "• e 是自然增长的极限常数\n"
        "• (1 + a/x)^x → e^a 描述连续复利增长\n"
        "• 指数函数 e^x 在 x=0 处切线斜率为 1"
    )
    return (problem, hint, geometry, ans, [])


def _gen_poly_derivative(difficulty):
    """多项式求导"""
    if difficulty == 'easy':
        n = random.randint(2, 3)
        a = random.randint(1, 5)
        m = max(1, n - 1)
        b = random.randint(1, 4)
        c = random.randint(1, 5)
        problem = f"求 f(x) = {a}x^{n} + {b}x^{m} + {c} 的导数"
    elif difficulty == 'medium':
        n = random.randint(3, 5)
        a = random.randint(2, 7)
        m = max(2, n - 2)
        b = random.randint(1, 6)
        c = random.randint(3, 10)
        problem = f"求 f(x) = {a}x^{n} + {b}x^{m} + {c} 的导数"
    else:
        n = random.randint(4, 6)
        a = random.randint(3, 10)
        m = max(2, n - 2)
        b = random.randint(2, 8)
        c = random.randint(5, 15)
        problem = f"求 f(x) = {a}x^{n} + {b}x^{m} + {c} 的导数"
    if HAS_SYMPY:
        x = sp.Symbol('x')
        expr = a * x ** n + b * x ** m + c
        ans = str(sp.diff(expr, x))
    else:
        ans = f"{a * n}*x**{n - 1} + {b * m}*x**{m - 1}"
    hint = (
        "幂法则: d(x^n)/dx = n·x^(n - 1)\n"
        "常数项导数为 0\n"
        "逐项求导即可"
    )
    geometry = (
        "【几何意义】\n"
        "• 导数 f'(x) 是曲线 y=f(x) 在各点的切线斜率\n"
        "• 多项式的导数降一次\n"
        "• f'(x)=0 对应的 x 是可能的极值点"
    )
    return (problem, hint, geometry, ans, [])


def _gen_trig_derivative(difficulty):
    """三角函数求导"""
    ranges = {'easy': (1, 3), 'medium': (2, 6), 'hard': (4, 10)}
    lo, hi = ranges.get(difficulty, (2, 6))
    k = _rand_ints(1, lo, hi)[0]
    fn_name = random.choice(['sin', 'cos'])
    problem = f"求 d/dx [{fn_name}({k}x)]"
    if HAS_SYMPY:
        x = sp.Symbol('x')
        expr = sp.sin(k * x) if fn_name == 'sin' else sp.cos(k * x)
        ans = str(sp.diff(expr, x))
    else:
        ans = f"{k}*cos({k}*x)" if fn_name == 'sin' else f"-{k}*sin({k}*x)"
    hint = (
        f"链式法则: d({fn_name}({k}x))/dx = {fn_name}'({k}x) · {k}\n"
        f"{'sin → cos' if fn_name == 'sin' else 'cos → -sin'}, 再乘 {k}"
    )
    geometry = (
        "【几何意义】\n"
        f"• {fn_name}({k}x) 在任意点的切线斜率就是其导数\n"
        "• 三角函数的导数仍是同频率的三角函数\n"
        "• 导数符号反映函数的增减区间"
    )
    return (problem, hint, geometry, ans, [])


def _gen_implicit_diff(difficulty):
    """隐函数求导 x² + y² = r² → dy/dx"""
    scales = {'easy': (1, 5), 'medium': (2, 10), 'hard': (5, 20)}
    lo, hi = scales.get(difficulty, (2, 10))
    r = _rand_ints(1, lo, hi)[0]
    rsq = r * r
    problem = f"由方程 x² + y² = {rsq} 确定的隐函数 y=y(x)，求 dy/dx"
    ans = "-x/y"
    hint = (
        f"两边对 x 求导:\n"
        f"d(x²)/dx + d(y²)/dx = d({rsq})/dx\n"
        f"2x + 2y·(dy/dx) = 0\n"
        f"→ dy/dx = -x/y"
    )
    geometry = (
        "【几何意义】\n"
        f"• x² + y² = {rsq} 是半径为 {r} 的圆\n"
        "• dy/dx = -x/y 是圆上点 (x, y) 处的切线斜率\n"
        "• 在 (r, 0) 处斜率不存在（垂直切线）\n"
        "• 在 (0, r) 处斜率为 0（水平切线）"
    )
    return (problem, hint, geometry, ans, [])


def _gen_poly_extrema(difficulty):
    """多项式极值 f(x) = x³ - kx"""
    scales = {'easy': (1, 3), 'medium': (2, 5), 'hard': (4, 8)}
    lo, hi = scales.get(difficulty, (2, 5))
    k = _rand_ints(1, lo, hi)[0]
    problem = f"求 f(x) = x³ - {k}x 的极值"
    if HAS_SYMPY:
        x = sp.Symbol('x')
        sqrt_term = sp.sqrt(k / 3)
        # 极小值: f(√(k/3)); 极大值: f(-√(k/3))
        val_max = sp.simplify((-sqrt_term) ** 3 - k * (-sqrt_term))
        val_min = sp.simplify(sqrt_term ** 3 - k * sqrt_term)
        ans = str(val_min)
        alt_ans = str(val_max)
    else:
        ans = f"-2*{k}/3*sqrt({k}/3)"
        alt_ans = f"2*{k}/3*sqrt({k}/3)"
    hint = (
        f"f'(x) = 3x² - {k} = 0\n"
        f"→ 驻点 x = ±√({k}/3)\n"
        f"f''(x) = 6x\n"
        f"当 x = √({k}/3): f'' > 0 → 极小值\n"
        f"当 x = -√({k}/3): f'' < 0 → 极大值"
    )
    geometry = (
        "【几何意义】\n"
        "• 导数为零的点（驻点）是可能的极值点\n"
        "• f''(x) 判断曲线的凹凸性\n"
        "• f'' > 0: 曲线下凸 → 极小值点\n"
        "• f'' < 0: 曲线上凸 → 极大值点"
    )
    return (problem, hint, geometry, ans, [alt_ans])


def _gen_partial_derivative(difficulty):
    """偏导数 ∂z/∂x"""
    scales = {'easy': (1, 3), 'medium': (2, 5), 'hard': (4, 8)}
    lo, hi = scales.get(difficulty, (2, 5))
    a, n = _rand_ints(2, lo, hi)
    m = random.randint(1, max(2, n - 1))
    if difficulty == 'easy':
        m = min(m, 2)
    problem = f"z = {a}x^{n}y^{m} + sin(xy)，求 ∂z/∂x"
    if HAS_SYMPY:
        x, y = sp.symbols('x y')
        expr = a * x ** n * y ** m + sp.sin(x * y)
        ans = str(sp.diff(expr, x))
    else:
        ans = f"{a * n}*x**{n - 1}*y**{m} + y*cos(x*y)"
    hint = (
        "∂z/∂x 的含义: 把 y 当作常数，对 x 求偏导\n"
        f"∂({a}x^{n}y^{m})/∂x = {a * n}x^{n - 1}y^{m} (y^{m} 视为常数)\n"
        "∂sin(xy)/∂x = y·cos(xy) (链式法则)"
    )
    geometry = (
        "【几何意义】\n"
        "• ∂z/∂x 表示曲面 z=f(x,y) 沿 x 轴方向的斜率\n"
        "• 相当于用平行于 xOz 的平面截曲面，所得曲线的切线斜率\n"
        "• 固定 y 不变，只看 x 变化时 z 的变化率"
    )
    return (problem, hint, geometry, ans, [])


def _gen_indefinite_power(difficulty):
    """不定积分 ∫x^n dx"""
    scales = {'easy': (1, 5), 'medium': (3, 10), 'hard': (6, 15)}
    lo, hi = scales.get(difficulty, (3, 10))
    n = _rand_ints(1, lo, hi)[0]
    problem = f"求不定积分 ∫ x^{n} dx"
    if HAS_SYMPY:
        ans = f"x**{n + 1}/{n + 1}"
    else:
        ans = f"x**{n + 1}/{n + 1}"
    hint = (
        f"幂函数积分公式: ∫ x^n dx = x^(n+1) / (n+1) + C\n"
        f"这里 n = {n}, 所以原函数 = x^{n+1} / {n+1} + C"
    )
    geometry = (
        "【几何意义】\n"
        f"• 原函数 F(x) = x^{n+1}/{n+1} 满足 F'(x) = x^{n}\n"
        "• 不定积分 = 反导数家族 (相差常数 C)\n"
        "• 加上常数 C 表示一族平行曲线"
    )
    return (problem, hint, geometry, ans, [])


def _gen_indefinite_trig(difficulty):
    """不定积分 ∫sin(kx) dx"""
    scales = {'easy': (1, 3), 'medium': (2, 6), 'hard': (4, 10)}
    lo, hi = scales.get(difficulty, (4, 10))
    k = _rand_ints(1, lo, hi)[0]
    problem = f"求不定积分 ∫ sin({k}x) dx"
    if HAS_SYMPY:
        ans = f"-cos({k}*x)/{k}"
    else:
        ans = f"-cos({k}*x)/{k}"
    hint = (
        f"基本积分公式: ∫ sin(kx) dx = -cos(kx)/k + C\n"
        f"这里 k = {k}, 所以 = -cos({k}x)/{k} + C"
    )
    geometry = (
        "【几何意义】\n"
        f"• -cos({k}x)/{k} 的导数 = sin({k}x)\n"
        "• 原函数曲线在任意点的斜率 = sin(kx) 在该点的值\n"
        "• 积分常数 C 对应曲线的上下平移"
    )
    return (problem, hint, geometry, ans, [])


def _gen_definite_integral(difficulty):
    """定积分 ∫_a^b x^n dx"""
    scales = {'easy': (1, 3), 'medium': (2, 5), 'hard': (4, 10)}
    lo, hi = scales.get(difficulty, (2, 5))
    n = _rand_ints(1, lo, hi)[0]
    if difficulty == 'hard':
        a = random.randint(0, 5)
        b = a + random.randint(2, 8)
    else:
        a = random.randint(0, 3)
        b = a + random.randint(1, 5)
    problem = f"求定积分 ∫_{{{a}}}^{{{b}}} x^{n} dx"
    if HAS_SYMPY:
        x = sp.Symbol('x')
        result = sp.integrate(x ** n, (x, a, b))
        ans = str(sp.simplify(result))
    else:
        ans = f"({b}**{n + 1} - {a}**{n + 1})/{n + 1}"
    hint = (
        f"牛顿-莱布尼茨公式: ∫_a^b f(x)dx = F(b) - F(a)\n"
        f"原函数 F(x) = x^{n+1} / ({n+1})\n"
        f"= {b}^{n+1}/{n+1} - {a}^{n+1}/{n+1}"
    )
    geometry = (
        "【几何意义】\n"
        f"• 定积分 = 曲线 y=x^{n} 在 [{a}, {b}] 上与 x 轴围成的面积\n"
        "• 牛顿-莱布尼茨公式将面积计算转化为原函数求值\n"
        "• 定积分是原函数在两个端点的差值"
    )
    return (problem, hint, geometry, ans, [])


# ── 模板注册表 ──

RANDOM_TEMPLATES = [
    {'topic': '向量代数', 'generate': _gen_vector_dot},
    {'topic': '向量代数', 'generate': _gen_vector_cross_mag},
    {'topic': '极限',     'generate': _gen_limit_sin},
    {'topic': '极限',     'generate': _gen_limit_e},
    {'topic': '导数',     'generate': _gen_poly_derivative},
    {'topic': '导数',     'generate': _gen_trig_derivative},
    {'topic': '隐函数求导', 'generate': _gen_implicit_diff},
    {'topic': '极值',     'generate': _gen_poly_extrema},
    {'topic': '偏导数',   'generate': _gen_partial_derivative},
    {'topic': '不定积分', 'generate': _gen_indefinite_power},
    {'topic': '不定积分', 'generate': _gen_indefinite_trig},
    {'topic': '定积分',   'generate': _gen_definite_integral},
]


def generate_random_exercise(difficulty='medium'):
    """生成随机练习题。

    Args:
        difficulty: 难度等级 — 'easy' | 'medium' | 'hard'

    Returns:
        dict: 包含 topic, problem, hint, geometry, correct_answer, acceptable_answers
    """
    if difficulty not in ('easy', 'medium', 'hard'):
        difficulty = 'medium'
    template = random.choice(RANDOM_TEMPLATES)
    problem, hint, geometry, correct, acceptables = template['generate'](difficulty)
    return {
        'topic': template['topic'],
        'problem': problem,
        'hint': hint,
        'geometry': geometry,
        'correct_answer': correct,
        'acceptable_answers': acceptables,
    }


# ══════════════════════════════════════════════════════════════
#  答案批改引擎
# ══════════════════════════════════════════════════════════════

def _to_expression(s):
    """将字符串转换为 sympy 表达式。
    如果包含 '='，则转为各部分列表。
    返回 (first_expr, is_equation, parsed_parts)"""
    if not HAS_SYMPY:
        return None, False, []

    s = s.strip()
    if '=' not in s:
        try:
            return sp.sympify(s), False, []
        except Exception:
            return None, False, []

    # 等式: 拆分为各部分
    parts = [p.strip() for p in s.split('=')]
    try:
        parsed_parts = [sp.sympify(p) for p in parts]
    except Exception:
        return None, True, []

    return parsed_parts[0], True, parsed_parts


def _expressions_equal(a, b):
    """比较两个 sympy 表达式是否等价（多重策略）"""
    # 策略1: 直接相减简化
    try:
        diff = sp.simplify(a - b)
        if diff == 0:
            return True
    except Exception:
        pass

    # 策略2: 比值简化 (排除除法问题，如分母为0)
    try:
        ratio = sp.simplify(a / b - 1)
        if ratio == 0:
            return True
    except Exception:
        pass

    # 策略3: 展开后相减再简化
    try:
        if sp.simplify(sp.expand(a - b)) == 0:
            return True
    except Exception:
        pass

    return False


def check_answer(user_input, correct_str):
    """批改用户答案。返回 (is_correct, feedback_text)
    is_correct: True / False / None (None 表示解析错误)
    """
    if not HAS_SYMPY:
        return None, "⚠ 需要安装 sympy: pip install sympy"

    if not user_input.strip():
        return None, "⚠ 请输入答案"

    # 解析用户输入和正确答案
    user_expr, user_is_eq, user_parts = _to_expression(user_input)
    correct_expr, correct_is_eq, correct_parts = _to_expression(correct_str)

    if user_expr is None or correct_expr is None:
        return None, "⚠ 输入格式有误，请检查"

    # ── 将等式转为差式列表 ──
    if correct_is_eq and len(correct_parts) >= 2:
        correct_diffs = [
            sp.simplify(correct_parts[j] - correct_parts[j + 1])
            for j in range(len(correct_parts) - 1)
        ]
    else:
        correct_diffs = [correct_expr]

    if user_is_eq and len(user_parts) >= 2:
        user_diffs = [
            sp.simplify(user_parts[j] - user_parts[j + 1])
            for j in range(len(user_parts) - 1)
        ]
    else:
        user_diffs = [user_expr]

    # ── 比较所有差式对 ──
    for ud in user_diffs:
        for cd in correct_diffs:
            # 符号比较
            if _expressions_equal(ud, cd):
                return True, "✓ 正确！"

            # 数值比较
            try:
                val = abs(sp.N(ud - cd))
                if val < 1e-6:
                    return True, "✓ 正确！"
            except Exception:
                continue

    # ── 直接数值比较原始表达式（非等式场景）──
    if not correct_is_eq and not user_is_eq:
        try:
            val = abs(sp.N(user_expr - correct_expr))
            if val < 1e-6:
                return True, "✓ 正确！"
        except Exception:
            pass

    # ── 等式场景：用户可能输入等式单边 ──
    if correct_is_eq and len(correct_parts) >= 2:
        for cp in correct_parts:
            if _expressions_equal(user_expr, cp):
                return True, "✓ 正确！"

    return False, "✗ 不对，再想想"


# ══════════════════════════════════════════════════════════════
#  随机题目卡片
# ══════════════════════════════════════════════════════════════

def _create_random_exercise_card(parent, topic, problem, hint, geometry):
    """创建随机练习题卡片（样式与静态卡片一致，使用 _random_state 保存答案）。"""
    _destroy_random_card()

    card = CTkFrame(
        parent,
        fg_color=MacColors.CARD_BG,
        corner_radius=12,
        border_width=2,
        border_color=MacColors.WARNING,
    )
    card.pack(fill="x", pady=10)
    _random_state['card_frame'] = card

    # ── 题号和主题 ──
    header = CTkFrame(card, fg_color="transparent")
    header.pack(fill="x", padx=20, pady=(15, 5))

    CTkLabel(
        header,
        text="🎲 随机题目",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=MacColors.WARNING,
    ).pack(side="left")

    CTkLabel(
        header,
        text=topic,
        font=ctk.CTkFont(size=12),
        text_color=MacColors.TEXT_SECONDARY,
    ).pack(side="left", padx=(10, 0))

    # ── 题目内容 ──
    CTkLabel(
        card,
        text=problem,
        font=ctk.CTkFont(size=13),
        text_color=MacColors.TEXT_PRIMARY,
        justify="left",
        wraplength=700,
    ).pack(anchor="w", padx=20, pady=(5, 10))

    # ── 按钮区域 ──
    btn_frame = CTkFrame(card, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 10))

    show_hint = [False]
    hint_label = CTkLabel(
        card, text="",
        font=ctk.CTkFont(size=12),
        text_color=MacColors.SUCCESS,
        justify="left", wraplength=700,
    )

    def toggle_hint():
        if show_hint[0]:
            hint_label.configure(text="")
            show_hint[0] = False
        else:
            hint_label.configure(text=f"💡 提示:\n{hint}")
            show_hint[0] = True

    CTkButton(
        btn_frame,
        text="💡 查看提示",
        font=ctk.CTkFont(size=12),
        fg_color=MacColors.SUCCESS,
        hover_color="#2DA44E",
        height=32, corner_radius=8,
        command=toggle_hint,
    ).pack(side="left")

    show_geometry = [False]
    geometry_label = CTkLabel(
        card, text="",
        font=ctk.CTkFont(size=12),
        text_color=MacColors.CH1,
        justify="left", wraplength=700,
    )

    def toggle_geometry():
        if show_geometry[0]:
            geometry_label.configure(text="")
            show_geometry[0] = False
        else:
            geometry_label.configure(text=geometry)
            show_geometry[0] = True

    CTkButton(
        btn_frame,
        text="📐 查看几何意义",
        font=ctk.CTkFont(size=12),
        fg_color=MacColors.CH1,
        hover_color="#E85D5D",
        height=32, corner_radius=8,
        command=toggle_geometry,
    ).pack(side="left", padx=(10, 0))

    hint_label.pack(anchor="w", pady=(5, 0))
    geometry_label.pack(anchor="w", pady=(5, 0))

    # ── 答案提交区域 ──
    feedback_label = CTkLabel(
        card, text="",
        font=ctk.CTkFont(size=13),
        justify="left", wraplength=700,
    )

    def submit_answer():
        user_input = entry.get()
        correct = _random_state['correct_answer']
        is_correct, msg = check_answer(user_input, correct)

        if is_correct is not True:
            for alt in _random_state.get('acceptable_answers', []):
                alt_ok, _ = check_answer(user_input, alt)
                if alt_ok is True:
                    is_correct = True
                    msg = "✓ 正确！"
                    break

        if is_correct is True:
            feedback_label.configure(text=msg, text_color=MacColors.SUCCESS)
        elif is_correct is False:
            feedback_label.configure(text=msg, text_color=MacColors.DANGER)
        else:
            feedback_label.configure(text=msg, text_color=MacColors.WARNING)

    answer_frame = CTkFrame(card, fg_color="transparent")
    answer_frame.pack(fill="x", padx=20, pady=(10, 5))

    entry = CTkEntry(
        answer_frame,
        placeholder_text="输入你的答案...",
        width=300, height=32,
        font=ctk.CTkFont(size=13),
        border_color=MacColors.BORDER,
        fg_color=MacColors.CARD_BG,
        text_color=MacColors.TEXT_PRIMARY,
    )
    entry.pack(side="left", padx=(0, 10))
    entry.bind("<Return>", lambda e: submit_answer())

    CTkButton(
        answer_frame,
        text="提交答案",
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#007AFF",
        hover_color="#0056CC",
        text_color="#FFFFFF",
        height=32, corner_radius=8,
        command=submit_answer,
    ).pack(side="left")

    feedback_label.pack(anchor="w", padx=20, pady=(5, 10))


# ══════════════════════════════════════════════════════════════
#  练习卡片渲染
# ══════════════════════════════════════════════════════════════

def render_exercises(parent):
    """在 parent 控件中渲染随机出题面板 + 8 道静态练习题卡片"""
    # ── 随机出题控制面板 ──
    random_panel = CTkFrame(
        parent,
        fg_color=MacColors.CARD_BG,
        corner_radius=12,
        border_width=1,
        border_color=MacColors.BORDER,
    )
    random_panel.pack(fill="x", pady=(0, 15))

    # 面板标题行
    panel_header = CTkFrame(random_panel, fg_color="transparent")
    panel_header.pack(fill="x", padx=20, pady=(15, 10))

    CTkLabel(
        panel_header,
        text="🎲 随机出题",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=MacColors.TEXT_PRIMARY,
    ).pack(side="left")

    CTkLabel(
        panel_header,
        text="系统随机生成题目，自动批改",
        font=ctk.CTkFont(size=12),
        text_color=MacColors.TEXT_SECONDARY,
    ).pack(side="left", padx=(10, 0))

    # 控制行：难度选择 + 生成按钮
    control_row = CTkFrame(random_panel, fg_color="transparent")
    control_row.pack(fill="x", padx=20, pady=(0, 15))

    difficulty_var = ctk.StringVar(value="中等")
    difficulty_menu = ctk.CTkOptionMenu(
        control_row,
        values=["简单", "中等", "困难"],
        variable=difficulty_var,
        font=ctk.CTkFont(size=12),
        fg_color=MacColors.HOVER_BG,
        text_color=MacColors.TEXT_PRIMARY,
        button_color=MacColors.ACCENT,
        button_hover_color=MacColors.ACCENT_HOVER,
        dropdown_fg_color=MacColors.CARD_BG,
        dropdown_text_color=MacColors.TEXT_PRIMARY,
        width=100,
        height=32,
        corner_radius=8,
    )
    difficulty_menu.pack(side="left")

    def on_generate():
        diff_map = {"简单": "easy", "中等": "medium", "困难": "hard"}
        diff = diff_map.get(difficulty_var.get(), "medium")
        ex = generate_random_exercise(diff)
        _random_state['correct_answer'] = ex['correct_answer']
        _random_state['acceptable_answers'] = ex.get('acceptable_answers', [])
        _create_random_exercise_card(
            parent, ex['topic'], ex['problem'],
            ex['hint'], ex['geometry'],
        )

    CTkButton(
        control_row,
        text="🎲 随机出题",
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color=MacColors.WARNING,
        hover_color="#E68600",
        text_color="#FFFFFF",
        height=32,
        corner_radius=8,
        command=on_generate,
    ).pack(side="left", padx=(10, 0))

    # ── 静态练习题（8 道）──
    for i, (topic, problem, hint, geometry) in enumerate(EXERCISE_DATA, 1):
        _create_exercise_card(parent, i, topic, problem, hint, geometry)


def _create_exercise_card(parent, i, topic, problem, hint, geometry):
    """创建单道练习题卡片（含提示、几何意义、自动批改）"""
    # 题目卡片
    card = CTkFrame(
        parent,
        fg_color=MacColors.CARD_BG,
        corner_radius=12,
        border_width=1,
        border_color=MacColors.BORDER,
    )
    card.pack(fill="x", pady=10)

    # 题号和主题
    header = CTkFrame(card, fg_color="transparent")
    header.pack(fill="x", padx=20, pady=(15, 5))

    CTkLabel(
        header,
        text=f"第 {i} 题",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=MacColors.ACCENT,
    ).pack(side="left")

    CTkLabel(
        header,
        text=topic,
        font=ctk.CTkFont(size=12),
        text_color=MacColors.TEXT_SECONDARY,
    ).pack(side="left", padx=(10, 0))

    # 题目内容
    CTkLabel(
        card,
        text=problem,
        font=ctk.CTkFont(size=13),
        text_color=MacColors.TEXT_PRIMARY,
        justify="left",
        wraplength=700,
    ).pack(anchor="w", padx=20, pady=(5, 10))

    # ── 按钮区域（提示 / 几何意义）──
    btn_frame = CTkFrame(card, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 10))

    # 提示按钮
    show_hint = [False]
    hint_label = CTkLabel(
        card,
        text="",
        font=ctk.CTkFont(size=12),
        text_color=MacColors.SUCCESS,
        justify="left",
        wraplength=700,
    )

    def toggle_hint():
        if show_hint[0]:
            hint_label.configure(text="")
            show_hint[0] = False
        else:
            hint_label.configure(text=f"💡 提示:\n{hint}")
            show_hint[0] = True

    CTkButton(
        btn_frame,
        text="💡 查看提示",
        font=ctk.CTkFont(size=12),
        fg_color=MacColors.SUCCESS,
        hover_color="#2DA44E",
        height=32,
        corner_radius=8,
        command=toggle_hint,
    ).pack(side="left")

    # 几何意义按钮
    show_geometry = [False]
    geometry_label = CTkLabel(
        card,
        text="",
        font=ctk.CTkFont(size=12),
        text_color=MacColors.CH1,
        justify="left",
        wraplength=700,
    )

    def toggle_geometry():
        if show_geometry[0]:
            geometry_label.configure(text="")
            show_geometry[0] = False
        else:
            geometry_label.configure(text=geometry)
            show_geometry[0] = True

    CTkButton(
        btn_frame,
        text="📐 查看几何意义",
        font=ctk.CTkFont(size=12),
        fg_color=MacColors.CH1,
        hover_color="#E85D5D",
        height=32,
        corner_radius=8,
        command=toggle_geometry,
    ).pack(side="left", padx=(10, 0))

    # 提示/几何意义标签（按钮下方）
    hint_label.pack(anchor="w", pady=(5, 0))
    geometry_label.pack(anchor="w", pady=(5, 0))

    # ── 答案提交区域 ──

    feedback_label = CTkLabel(
        card,
        text="",
        font=ctk.CTkFont(size=13),
        justify="left",
        wraplength=700,
    )

    def submit_answer():
        user_input = entry.get()
        correct = CORRECT_ANSWERS[i - 1]
        is_correct, msg = check_answer(user_input, correct)

        # 检查替代正确答案
        if is_correct is not True and i in ACCEPTABLE_ANSWERS:
            for alt in ACCEPTABLE_ANSWERS[i]:
                alt_ok, _ = check_answer(user_input, alt)
                if alt_ok is True:
                    is_correct = True
                    msg = "✓ 正确！"
                    break

        if is_correct is True:
            feedback_label.configure(text=msg, text_color=MacColors.SUCCESS)
        elif is_correct is False:
            feedback_label.configure(text=msg, text_color=MacColors.DANGER)
        else:
            feedback_label.configure(text=msg, text_color=MacColors.WARNING)

    # 输入行
    answer_frame = CTkFrame(card, fg_color="transparent")
    answer_frame.pack(fill="x", padx=20, pady=(10, 5))

    entry = CTkEntry(
        answer_frame,
        placeholder_text="输入你的答案...",
        width=300,
        height=32,
        font=ctk.CTkFont(size=13),
        border_color=MacColors.BORDER,
        fg_color=MacColors.CARD_BG,
        text_color=MacColors.TEXT_PRIMARY,
    )
    entry.pack(side="left", padx=(0, 10))

    # 回车键提交
    entry.bind("<Return>", lambda e: submit_answer())

    CTkButton(
        answer_frame,
        text="提交答案",
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color="#007AFF",
        hover_color="#0056CC",
        text_color="#FFFFFF",
        height=32,
        corner_radius=8,
        command=submit_answer,
    ).pack(side="left")

    feedback_label.pack(anchor="w", padx=20, pady=(5, 10))
