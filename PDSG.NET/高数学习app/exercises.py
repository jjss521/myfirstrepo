#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练习题模块 —— 8 道精选题的数据和卡片渲染。
支持答案自动批改（需 sympy）。
"""

import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkEntry

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
#  练习卡片渲染
# ══════════════════════════════════════════════════════════════

def render_exercises(parent):
    """在 parent 控件中渲染全部 8 道练习题卡片"""
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
