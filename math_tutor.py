#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式数学教学程序 - 空间解析几何 & 微分学
基于 PDF 教材内容，以最浅显的教学方法帮助你完全掌握
"""
import sys
import os
import math

# 设置 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

try:
    import sympy as sp
    from sympy import symbols, sqrt, sin, cos, tan, ln, exp, pi, oo, limit, diff, integrate, simplify, Matrix, Rational
    from sympy import Function, Eq, solve, pprint, latex, init_printing
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False
    print("提示: 安装 sympy 可获得符号运算演示: pip install sympy")

try:
    import numpy as np
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import cm
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False
    print("提示: 安装 matplotlib 可获得图形演示: pip install matplotlib")

try:
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi']
    matplotlib.rcParams['axes.unicode_minus'] = False
except:
    pass

# ══════════════════════════════════════════════════════════════
#  第一部分：空间解析几何
# ══════════════════════════════════════════════════════════════

def chapter_vector_algebra():
    """向量代数教学"""
    print("\n" + "="*60)
    print("  第一章：向量代数")
    print("="*60)

    print("""
┌─────────────────────────────────────────────────────┐
│  1.1 向量的概念                                      │
├─────────────────────────────────────────────────────┤
│  向量 = 既有大小又有方向的量                          │
│                                                     │
│  • 向量的模：向量的长度（大小）                       │
│  • 单位向量：模为 1 的向量                            │
│  • 零向量：模为 0，方向不固定                         │
│  • 相等向量：大小相等，方向相同                       │
│  • 负向量：大小相同，方向相反                         │
│  • 向径：起点为原点的向量                             │
│                                                     │
│  几何表示：用有向线段 →  表示                         │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  1.2 向量的表示法                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  (1) 向量分解式：                                    │
│      a = aₓ·i + aᵧ·j + aᵤ·k                        │
│                                                     │
│  (2) 坐标表示式：                                    │
│      a = {aₓ, aᵧ, aᵤ}                               │
│                                                     │
│  其中 aₓ, aᵧ, aᵤ 是向量在 x, y, z 轴上的投影          │
│                                                     │
│  例：a = 3i + 2j - k  →  a = {3, 2, -1}             │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  1.3 向量的线性运算                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  设 a = {aₓ, aᵧ, aᵤ}, b = {bₓ, bᵧ, bᵤ}             │
│                                                     │
│  (1) 加法: a + b = {aₓ+bₓ, aᵧ+bᵧ, aᵤ+bᵤ}           │
│  (2) 减法: a - b = {aₓ-bₓ, aᵧ-bᵧ, aᵤ-bᵤ}           │
│  (3) 数乘: λa = {λaₓ, λaᵧ, λaᵤ}                    │
│                                                     │
│  几何意义：                                          │
│  • 加法 → 平行四边形法则 / 三角形法则                 │
│  • 减法 → a - b = a + (-b)                           │
│  • 数乘 → λ>0 同向拉伸, λ<0 反向                     │
│                                                     │
│  模长: |a| = √(aₓ² + aᵧ² + aᵤ²)                     │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  1.4 数量积（点积/内积）                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  定义: a · b = |a|·|b|·cosθ                          │
│                                                     │
│  坐标公式: a · b = aₓbₓ + aᵧbᵧ + aᵤbᵤ               │
│                                                     │
│  夹角余弦:                                           │
│       aₓbₓ + aᵧbᵧ + aᵤbᵤ                            │
│  cosθ = ─────────────────────                       │
│       √(aₓ²+aᵧ²+aᵤ²) · √(bₓ²+bᵧ²+bᵤ²)            │
│                                                     │
│  垂直条件: a ⊥ b ⟺ a · b = 0                         │
│                                                     │
│  性质: 交换律、结合律、分配律                         │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  1.5 向量积（叉积/外积）                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  定义: c = a × b                                    │
│  • c ⊥ a 且 c ⊥ b（右手规则）                        │
│  • |c| = |a|·|b|·sinθ                               │
│                                                     │
│  行列式公式:                                         │
│       | i   j   k  |                                │
│  a × b | aₓ  aᵧ  aᵤ |                               │
│       | bₓ  bᵧ  bᵤ |                                │
│                                                     │
│  = (aᵧbᵤ-aᵤbᵧ)i - (aₓbᵤ-aᵤbₓ)j + (aₓbᵧ-aᵧbₓ)k    │
│                                                     │
│  平行条件: a ∥ b ⟺ a × b = 0                         │
│                                                     │
│  几何意义: 以 a, b 为边的平行四边形面积               │
│  三角形面积: S = ½|a × b|                            │
└─────────────────────────────────────────────────────┘
""")

    if HAS_SYMPY and HAS_PLOT:
        input("按 Enter 查看向量运算演示...")
        vector_demo()
    else:
        input("按 Enter 继续...")


def vector_demo():
    """向量运算可视化演示"""
    fig = plt.figure(figsize=(14, 5))

    # 子图1: 向量加法
    ax1 = fig.add_subplot(131)
    a = np.array([3, 2])
    b = np.array([1, 3])
    ax1.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='red', label='a={3,2}')
    ax1.quiver(a[0], a[1], b[0], b[1], angles='xy', scale_units='xy', scale=1, color='blue', label='b={1,3}')
    ax1.quiver(0, 0, a[0]+b[0], a[1]+b[1], angles='xy', scale_units='xy', scale=1, color='green', label='a+b={4,5}')
    ax1.set_xlim(-1, 6); ax1.set_ylim(-1, 6)
    ax1.set_aspect('equal'); ax1.grid(True, alpha=0.3)
    ax1.set_title('向量加法 (平行四边形法则)', fontsize=11)
    ax1.legend(fontsize=9)

    # 子图2: 向量点积
    ax2 = fig.add_subplot(132)
    a2 = np.array([3, 1])
    b2 = np.array([1, 2])
    dot_product = np.dot(a2, b2)
    cos_theta = dot_product / (np.linalg.norm(a2) * np.linalg.norm(b2))
    theta = np.degrees(np.arccos(np.clip(cos_theta, -1, 1)))
    ax2.quiver(0, 0, a2[0], a2[1], angles='xy', scale_units='xy', scale=1, color='red', label=f'a={tuple(a2)}')
    ax2.quiver(0, 0, b2[0], b2[1], angles='xy', scale_units='xy', scale=1, color='blue', label=f'b={tuple(b2)}')
    # 画夹角弧
    angle = np.linspace(0, np.arctan2(b2[1], b2[0]), 30)
    ax2.plot(0.8*np.cos(angle), 0.8*np.sin(angle), 'k-', linewidth=0.8)
    ax2.text(0.6, 0.3, f'θ={theta:.1f}°', fontsize=10)
    ax2.set_xlim(-1, 5); ax2.set_ylim(-1, 4)
    ax2.set_aspect('equal'); ax2.grid(True, alpha=0.3)
    ax2.set_title(f'点积: a·b = {dot_product}', fontsize=11)
    ax2.legend(fontsize=9)

    # 子图3: 向量叉积 (面积)
    ax3 = fig.add_subplot(133)
    a3 = np.array([3, 1, 0])
    b3 = np.array([1, 3, 0])
    cross = np.cross(a3, b3)
    # 平行四边形
    verts = np.array([[0,0], a3[:2], a3[:2]+b3[:2], b3[:2]])
    from matplotlib.patches import Polygon
    poly = Polygon(verts, alpha=0.3, color='cyan', label=f'面积={abs(cross[2]):.1f}')
    ax3.add_patch(poly)
    ax3.quiver(0, 0, a3[0], a3[1], angles='xy', scale_units='xy', scale=1, color='red', label=f'a={tuple(a3[:2])}')
    ax3.quiver(0, 0, b3[0], b3[1], angles='xy', scale_units='xy', scale=1, color='blue', label=f'b={tuple(b3[:2])}')
    ax3.set_xlim(-1, 5); ax3.set_ylim(-1, 5)
    ax3.set_aspect('equal'); ax3.grid(True, alpha=0.3)
    ax3.set_title(f'叉积: |a×b| = {abs(cross[2]):.1f}', fontsize=11)
    ax3.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig('vector_demo.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("向量运算演示已显示!\n")


def chapter_surfaces():
    """空间曲面教学"""
    print("\n" + "="*60)
    print("  第二章：空间曲面")
    print("="*60)

    print("""
┌─────────────────────────────────────────────────────┐
│  2.1 旋转曲面                                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  定义：平面曲线绕其平面上的一条定直线旋转一周          │
│       所成的曲面                                      │
│                                                     │
│  方程特点（以曲线 L: f(x,y)=0, z=0 为例）：           │
│                                                     │
│  (1) 绕 x 轴旋转: f(x, ±√(y²+z²)) = 0               │
│  (2) 绕 y 轴旋转: f(±√(x²+z²), y) = 0               │
│                                                     │
│  例: y² = 2pz 绕 z 轴旋转                            │
│  → x² + y² = 2pz （旋转抛物面）                      │
│                                                     │
│  例: x²/a² + y²/b² = 1 绕 x 轴旋转                  │
│  → x²/a² + y²/b² + z²/b² = 1 （椭球面）             │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  2.2 柱面                                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  定义：平行于定直线并沿定曲线 C 移动的直线 L          │
│       所形成的曲面                                    │
│                                                     │
│  • 定曲线 C → 准线                                   │
│  • 动直线 L → 母线                                   │
│                                                     │
│  特征：                                              │
│  • 方程中缺少哪个变量，曲面就平行于哪个坐标轴         │
│  • 例: x² + y² = R² （圆柱面，平行于 z 轴）          │
│  • 例: y² = 2px （抛物柱面，平行于 z 轴）            │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  2.3 二次曲面                                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  (1) 椭球面: x²/a² + y²/b² + z²/c² = 1              │
│                                                     │
│  (2) 椭圆抛物面: x²/(2p) + y²/(2q) = z (p,q同号)    │
│      特例 p=q: 旋转抛物面                            │
│                                                     │
│  (3) 双曲抛物面(鞍面): -x²/(2p) + y²/(2q) = z       │
│                                                     │
│  (4) 单叶双曲面: x²/a² + y²/b² - z²/c² = 1          │
│                                                     │
│  (5) 双叶双曲面: x²/a² + y²/b² - z²/c² = -1         │
│                                                     │
│  (6) 二次锥面: x²/a² + y²/b² - z²/c² = 0            │
└─────────────────────────────────────────────────────┘
""")

    if HAS_PLOT:
        input("按 Enter 查看二次曲面演示...")
        surfaces_demo()
    else:
        input("按 Enter 继续...")


def surfaces_demo():
    """二次曲面3D可视化"""
    fig = plt.figure(figsize=(15, 10))

    # 1. 椭球面
    ax1 = fig.add_subplot(231, projection='3d')
    u = np.linspace(0, 2*np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    x = 2*np.outer(np.cos(u), np.sin(v))
    y = 1.5*np.outer(np.sin(u), np.sin(v))
    z = 1*np.outer(np.ones(np.size(u)), np.cos(v))
    ax1.plot_surface(x, y, z, alpha=0.6, cmap='coolwarm')
    ax1.set_title('椭球面\nx²/4+y²/2.25+z²=1', fontsize=10)

    # 2. 椭圆抛物面
    ax2 = fig.add_subplot(232, projection='3d')
    r = np.linspace(0, 2, 40)
    theta = np.linspace(0, 2*np.pi, 40)
    R, THETA = np.meshgrid(r, theta)
    X = R*np.cos(THETA)
    Y = R*np.sin(THETA)
    Z = X**2/4 + Y**2/4
    ax2.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax2.set_title('旋转抛物面\n(x²+y²)/4 = z', fontsize=10)

    # 3. 双曲抛物面(鞍面)
    ax3 = fig.add_subplot(233, projection='3d')
    x = np.linspace(-2, 2, 50)
    y = np.linspace(-2, 2, 50)
    X, Y = np.meshgrid(x, y)
    Z = X**2/4 - Y**2/4
    ax3.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax3.set_title('双曲抛物面(鞍面)\nx²/4 - y²/4 = z', fontsize=10)

    # 4. 单叶双曲面
    ax4 = fig.add_subplot(234, projection='3d')
    u = np.linspace(0, 2*np.pi, 50)
    v = np.linspace(-1.5, 1.5, 30)
    X = 1.5*np.outer(np.cosh(v), np.cos(u))
    Y = 1.5*np.outer(np.cosh(v), np.sin(u))
    Z = np.outer(np.sinh(v), np.ones(np.size(u)))
    ax4.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax4.set_title('单叶双曲面\nx²+y²-z²=1', fontsize=10)

    # 5. 二次锥面
    ax5 = fig.add_subplot(235, projection='3d')
    theta = np.linspace(0, 2*np.pi, 50)
    z = np.linspace(-2, 2, 30)
    THETA, Z = np.meshgrid(theta, z)
    R = np.abs(Z)
    X = R*np.cos(THETA)
    Y = R*np.sin(THETA)
    ax5.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax5.set_title('二次锥面\nx²+y²=z²', fontsize=10)

    # 6. 圆柱面
    ax6 = fig.add_subplot(236, projection='3d')
    theta = np.linspace(0, 2*np.pi, 50)
    z = np.linspace(-2, 2, 30)
    THETA, Z = np.meshgrid(theta, z)
    X = np.cos(THETA)
    Y = np.sin(THETA)
    ax6.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax6.set_title('圆柱面\nx²+y²=1', fontsize=10)

    for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')

    plt.tight_layout()
    plt.savefig('surfaces_demo.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("二次曲面演示已显示!\n")


def chapter_lines_planes():
    """直线与平面教学"""
    print("\n" + "="*60)
    print("  第三章：空间直线与平面")
    print("="*60)

    print("""
┌─────────────────────────────────────────────────────┐
│  3.1 空间平面方程                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  (1) 一般式: Ax + By + Cz + D = 0                    │
│      法向量 n = (A, B, C)                             │
│                                                     │
│  (2) 点法式: A(x-x₀) + B(y-y₀) + C(z-z₀) = 0       │
│      过点 (x₀,y₀,z₀)，法向量 n=(A,B,C)               │
│                                                     │
│  (3) 截距式: x/a + y/b + z/c = 1                     │
│      三个截距分别为 a, b, c                           │
│                                                     │
│  (4) 三点式:                                         │
│      |x-x₁  y-y₁  z-z₁|                             │
│      |x₂-x₁  y₂-y₁  z₂-z₁| = 0                     │
│      |x₃-x₁  y₃-y₁  z₃-z₁|                         │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  3.2 空间直线方程                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  (1) 一般式（两平面交线）:                            │
│      A₁x + B₁y + C₁z + D₁ = 0                       │
│      A₂x + B₂y + C₂z + D₂ = 0                       │
│                                                     │
│  (2) 对称式（点向式）:                               │
│      (x-x₀)/m = (y-y₀)/n = (z-z₀)/p                │
│      点 (x₀,y₀,z₀)，方向向量 s=(m,n,p)               │
│                                                     │
│  (3) 参数式:                                         │
│      x = x₀ + mt                                    │
│      y = y₀ + nt                                    │
│      z = z₀ + pt                                    │
│                                                     │
│  解题思路: 先找一点，再找方向向量                      │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  3.3 位置关系                                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  【平面与平面】                                       │
│  垂直: n₁ · n₂ = 0                                   │
│  平行: n₁ × n₂ = 0  (即 A₁/A₂ = B₁/B₂ = C₁/C₂)      │
│  夹角: cosθ = (n₁·n₂)/(|n₁|·|n₂|)                   │
│                                                     │
│  【直线与直线】                                       │
│  垂直: s₁ · s₂ = 0                                   │
│  平行: s₁ × s₂ = 0                                   │
│  夹角: cosθ = (s₁·s₂)/(|s₁|·|s₂|)                   │
│                                                     │
│  【直线与平面】                                       │
│  垂直: s ∥ n  (s × n = 0)                            │
│  平行: s ⊥ n  (s · n = 0)                            │
│  夹角: sinφ = (s·n)/(|s|·|n|)                        │
│                                                     │
│  点到平面距离:                                        │
│       |Ax₀ + By₀ + Cz₀ + D|                         │
│  d = ─────────────────────                          │
│        √(A² + B² + C²)                              │
└─────────────────────────────────────────────────────┘
""")

    if HAS_SYMPY:
        input("按 Enter 查看直线平面方程演示...")
        lines_planes_demo()
    else:
        input("按 Enter 继续...")


def lines_planes_demo():
    """直线与平面方程求解演示"""
    print("\n【例题1】求过三点 A(1,2,3), B(3,4,5), C(-2,4,7) 的平面方程")
    print("-" * 50)

    if HAS_SYMPY:
        x, y, z = symbols('x y z')
        # 法向量 = AB × AC
        AB = Matrix([3-1, 4-2, 5-3])  # {2,2,2}
        AC = Matrix([-2-1, 4-2, 7-3])  # {-3,2,4}
        n = AB.cross(AC)
        print(f"  AB = {AB.T}")
        print(f"  AC = {AC.T}")
        print(f"  法向量 n = AB × AC = {n.T}")
        # 平面方程
        plane = n[0]*(x-1) + n[1]*(y-2) + n[2]*(z-3)
        plane_expanded = sp.expand(plane)
        print(f"  平面方程: {plane_expanded} = 0")
        print(f"  简化: {sp.simplify(plane_expanded)} = 0")

    print("\n【例题2】求直线 (x-1)/2 = (y+1)/(-1) = (z-2)/3 与平面 x+y+z=6 的交点")
    print("-" * 50)

    if HAS_SYMPY:
        t = symbols('t')
        # 参数方程
        x_val = 1 + 2*t
        y_val = -1 - t
        z_val = 2 + 3*t
        print(f"  参数方程: x={x_val}, y={y_val}, z={z_val}")
        # 代入平面方程
        eq = x_val + y_val + z_val - 6
        t_sol = solve(eq, t)[0]
        print(f"  代入平面方程: {x_val} + ({y_val}) + ({z_val}) = 6")
        print(f"  解得 t = {t_sol}")
        ix = x_val.subs(t, t_sol)
        iy = y_val.subs(t, t_sol)
        iz = z_val.subs(t, t_sol)
        print(f"  交点坐标: ({ix}, {iy}, {iz})")


# ══════════════════════════════════════════════════════════════
#  第二部分：微分学
# ══════════════════════════════════════════════════════════════

def chapter_limits():
    """函数、极限、连续教学"""
    print("\n" + "="*60)
    print("  第四章：函数、极限、连续")
    print("="*60)

    print("""
┌─────────────────────────────────────────────────────┐
│  4.1 函数                                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  定义: 设 D ⊂ R，函数为特殊的映射                     │
│  f: D → f(D) ⊂ R                                     │
│                                                     │
│  函数要素: 定义域、对应法则、值域                      │
│                                                     │
│  基本初等函数:                                        │
│  • 常数函数 y = C                                    │
│  • 幂函数 y = xⁿ                                    │
│  • 指数函数 y = aˣ (a>0, a≠1)                       │
│  • 对数函数 y = logₐx                                │
│  • 三角函数 sinx, cosx, tanx, cotx...                │
│  • 反三角函数 arcsinx, arccosx, arctanx...           │
│                                                     │
│  初等函数 = 基本初等函数经有限次四则运算              │
│            与复合而成的函数                          │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  4.2 极限                                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  等价定义: lim f(x) = A  ⟺  f(x) = A + α            │
│           x→x₀            其中 α 为无穷小            │
│                                                     │
│  无穷小的性质:                                       │
│  • 无穷小 × 有界量 = 无穷小                          │
│  • 有限个无穷小之和 = 无穷小                          │
│                                                     │
│  等价无穷小代换（常用）:                              │
│  sinx ~ x     tanx ~ x     arcsinx ~ x              │
│  arctanx ~ x  1-cosx ~ x²/2   ln(1+x) ~ x          │
│  eˣ-1 ~ x    aˣ-1 ~ x·lna   (1+x)ᵝ-1 ~ βx          │
│                                                     │
│  两个重要极限:                                       │
│  lim(sinx/x) = 1     lim(1+1/x)ˣ = e               │
│  x→0                  x→∞                            │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  4.3 洛必达法则                                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  适用条件: 0/0 型 或 ∞/∞ 型                          │
│                                                     │
│  若 lim f(x) = lim F(x) = 0 (∞)                     │
│      x→a      x→a                                   │
│  且 f(x), F(x) 在 U(a) 内可导, F'(x)≠0              │
│                                                     │
│  则: lim f(x)/F(x) = lim f'(x)/F'(x)               │
│      x→a              x→a                           │
│                                                     │
│  说明: x→a 可换为 x→a⁺, x→a⁻, x→∞, x→+∞, x→-∞     │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  4.4 函数的连续性                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  连续定义: lim f(x) = f(x₀)                          │
│           x→x₀                                      │
│                                                     │
│  即: lim Δy = lim [f(x₀+Δx) - f(x₀)] = 0            │
│      Δx→0                                           │
│                                                     │
│  间断点分类:                                         │
│  ┌──────────────┬───────────────────────────┐       │
│  │ 第一类间断点   │ 左右极限都存在             │       │
│  │ (可去间断点)   │ 左极限 = 右极限 ≠ f(x₀)   │       │
│  │ (跳跃间断点)   │ 左极限 ≠ 右极限            │       │
│  ├──────────────┼───────────────────────────┤       │
│  │ 第二类间断点   │ 左右极限至少有一个不存在    │       │
│  │ (无穷间断点)   │ 极限为 ∞                   │       │
│  │ (振荡间断点)   │ 极限振荡不存在             │       │
│  └──────────────┴───────────────────────────┘       │
└─────────────────────────────────────────────────────┘
""")

    if HAS_SYMPY and HAS_PLOT:
        input("按 Enter 查看极限与连续性演示...")
        limits_demo()
    else:
        input("按 Enter 继续...")


def limits_demo():
    """极限与连续性可视化"""
    fig = plt.figure(figsize=(14, 5))

    # 子图1: sin(x)/x → 1
    ax1 = fig.add_subplot(131)
    x = np.linspace(-10, 10, 500)
    x_safe = x.copy()
    x_safe[x_safe == 0] = 1e-10
    y = np.sin(x_safe) / x_safe
    ax1.plot(x, y, 'b-', linewidth=2, label='sin(x)/x')
    ax1.axhline(y=1, color='r', linestyle='--', alpha=0.5, label='y=1 (极限值)')
    ax1.axvline(x=0, color='gray', linestyle=':', alpha=0.3)
    ax1.plot(0, 1, 'ro', markersize=8, label='lim = 1')
    ax1.set_xlabel('x'); ax1.set_ylabel('y')
    ax1.set_title('重要极限: lim sin(x)/x = 1\nx→0', fontsize=11)
    ax1.legend(fontsize=9); ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.3, 1.5)

    # 子图2: (1+1/x)^x → e
    ax2 = fig.add_subplot(132)
    x2 = np.linspace(1, 100, 200)
    y2 = (1 + 1/x2)**x2
    ax2.plot(x2, y2, 'b-', linewidth=2, label='(1+1/x)^x')
    ax2.axhline(y=np.e, color='r', linestyle='--', alpha=0.5, label=f'y=e≈{np.e:.4f}')
    ax2.set_xlabel('x'); ax2.set_ylabel('y')
    ax2.set_title('重要极限: lim (1+1/x)^x = e\nx→∞', fontsize=11)
    ax2.legend(fontsize=9); ax2.grid(True, alpha=0.3)

    # 子图3: 间断点示例
    ax3 = fig.add_subplot(133)
    x3 = np.linspace(-3, 3, 500)
    # 可去间断点
    y3 = np.where(x3 != 0, np.sin(x3)/x3, 0)
    ax3.plot(x3, y3, 'b-', linewidth=2, label='sin(x)/x (可去间断点)')
    ax3.plot(0, 0, 'ro', markersize=8)
    ax3.plot(0, 1, 'go', markersize=8, label='实际值=1')
    # 跳跃间断点
    x_jump = np.linspace(-3, 3, 500)
    y_jump = np.where(x_jump >= 0, 1, -1)
    ax3_twin = ax3.twinx()
    ax3_twin.plot(x_jump, y_jump, 'm--', linewidth=1.5, alpha=0.6, label='sgn(x) (跳跃间断点)')
    ax3.set_xlabel('x'); ax3.set_ylabel('y')
    ax3.set_title('间断点类型', fontsize=11)
    ax3.legend(loc='upper left', fontsize=8)
    ax3_twin.legend(loc='upper right', fontsize=8)
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('limits_demo.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("极限与连续性演示已显示!\n")


def chapter_derivatives():
    """导数与微分教学"""
    print("\n" + "="*60)
    print("  第五章：导数与微分")
    print("="*60)

    print("""
┌─────────────────────────────────────────────────────┐
│  5.1 导数的定义                                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  f'(x₀) = lim [f(x₀+Δx) - f(x₀)] / Δx              │
│           Δx→0                                      │
│       = lim [f(x) - f(x₀)] / (x - x₀)              │
│          x→x₀                                      │
│                                                     │
│  几何意义: 切线斜率                                   │
│  物理意义: 瞬时变化率                                 │
│                                                     │
│  可导 ⟺ 可微                                        │
│  左导数 f'₋(x₀) = lim Δx→0⁻ [f(x₀+Δx)-f(x₀)]/Δx   │
│  右导数 f'₊(x₀) = lim Δx→0⁺ [f(x₀+Δx)-f(x₀)]/Δx   │
│                                                     │
│  可导 ⟺ 左导数 = 右导数                              │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  5.2 求导公式和法则（必须记住！）                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  基本公式:                                           │
│  (C)' = 0          (xⁿ)' = nxⁿ⁻¹                   │
│  (sinx)' = cosx    (cosx)' = -sinx                  │
│  (tanx)' = sec²x   (cotx)' = -csc²x                 │
│  (aˣ)' = aˣlna     (eˣ)' = eˣ                      │
│  (logₐx)' = 1/(xlna)  (lnx)' = 1/x                 │
│                                                     │
│  法则:                                               │
│  (u ± v)' = u' ± v'                                  │
│  (uv)' = u'v + uv'                                   │
│  (u/v)' = (u'v - uv') / v²                           │
│                                                     │
│  复合函数求导（链式法则）:                            │
│  [f(g(x))]' = f'(g(x)) · g'(x)                      │
│  口诀: 由外向内逐层求导                              │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  5.3 隐函数求导法                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  方法: 方程两边同时对 x 求导，解出 dy/dx              │
│                                                     │
│  例: y⁵ + 2y - x - 3x⁷ = 0, 求 x=0 时的 dy/dx      │
│                                                     │
│  解: 两边对 x 求导:                                  │
│      5y⁴·(dy/dx) + 2·(dy/dx) - 1 - 21x⁶ = 0        │
│      dy/dx = (1 + 21x⁶) / (5y⁴ + 2)                 │
│                                                     │
│  当 x=0 时 y=0, 所以 dy/dx|ₓ₌₀ = 1/2                │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  5.4 高阶导数                                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  f''(x) = [f'(x)]'   二阶导数                       │
│  f⁽ⁿ⁾(x) = [f⁽ⁿ⁻¹⁾(x)]'   n阶导数                   │
│                                                     │
│  常用高阶导数公式:                                   │
│  (eˣ)⁽ⁿ⁾ = eˣ                                       │
│  (sinx)⁽ⁿ⁾ = sin(x + nπ/2)                          │
│  (xⁿ)⁽ⁿ⁾ = n!                                       │
│  (lnx)⁽ⁿ⁾ = (-1)ⁿ⁻¹·(n-1)!/xⁿ                      │
└─────────────────────────────────────────────────────┘
""")

    if HAS_SYMPY:
        input("按 Enter 查看导数计算演示...")
        derivatives_demo()
    else:
        input("按 Enter 继续...")


def derivatives_demo():
    """导数计算演示"""
    x = symbols('x')

    print("\n【导数公式验证】")
    print("-" * 50)
    funcs = [
        (sin(x), "sin(x)"),
        (cos(x), "cos(x)"),
        (x**3 + 2*x**2 - 5*x + 3, "x³+2x²-5x+3"),
        (exp(x), "eˣ"),
        (ln(x), "ln(x)"),
        (1/x, "1/x"),
    ]

    for f, name in funcs:
        f_prime = diff(f, x)
        print(f"  [{name}]' = {f_prime}")

    print("\n【链式法则演示】")
    print("-" * 50)
    # 复合函数
    f1 = sin(x**2)
    f1_prime = diff(f1, x)
    print(f"  [sin(x²)]' = {sp.simplify(f1_prime)}")

    f2 = exp(3*x + 1)
    f2_prime = diff(f2, x)
    print(f"  [e^(3x+1)]' = {f2_prime}")

    f3 = ln(x**2 + 1)
    f3_prime = diff(f3, x)
    print(f"  [ln(x²+1)]' = {sp.simplify(f3_prime)}")

    print("\n【隐函数求导演示】")
    print("-" * 50)
    y = Function('y')
    eq = y(x)**5 + 2*y(x) - x - 3*x**7
    # 隐函数求导
    dydx = sp.diff(eq, x)
    print(f"  方程: y⁵ + 2y - x - 3x⁷ = 0")
    print(f"  两边对x求导: {dydx} = 0")
    sol = solve(dydx, sp.diff(y(x), x))
    print(f"  dy/dx = {sol}")


def chapter_multivariable():
    """多元函数微分学教学"""
    print("\n" + "="*60)
    print("  第六章：多元函数微分学")
    print("="*60)

    print("""
┌─────────────────────────────────────────────────────┐
│  6.1 偏导数                                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  定义: z = f(x,y)                                    │
│                                                     │
│  对x的偏导: ∂z/∂x = lim [f(x+Δx,y)-f(x,y)] / Δx     │
│                        Δx→0                         │
│  对y的偏导: ∂z/∂y = lim [f(x,y+Δy)-f(x,y)] / Δy     │
│                        Δy→0                         │
│                                                     │
│  求法: 将其余变量视为常数，对该变量求导                │
│                                                     │
│  例: z = x² + 3xy + y²                               │
│  ∂z/∂x = 2x + 3y    ∂z/∂y = 3x + 2y                │
│                                                     │
│  在点(1,2)处:                                        │
│  ∂z/∂x|(1,2) = 2+6 = 8    ∂z/∂y|(1,2) = 3+4 = 7    │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  6.2 全微分                                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  定义: dz = fₓ(x,y)dx + fᵧ(x,y)dy                   │
│                                                     │
│  其中 fₓ = ∂f/∂x,  fᵧ = ∂f/∂y                       │
│                                                     │
│  重要关系:                                           │
│  函数连续 ⟸ 函数可微 ⟹ 函数可导                     │
│  偏导数连续 ⟹ 函数可微                               │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  6.3 复合函数求偏导（链式法则）                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  设 z = f(u,v), u = φ(t), v = ψ(t)                  │
│  则: dz/dt = (∂z/∂u)(du/dt) + (∂z/∂v)(dv/dt)        │
│                                                     │
│  设 z = f(u,v), u = φ(x,y), v = ψ(x,y)             │
│  则: ∂z/∂x = (∂z/∂u)(∂u/∂x) + (∂z/∂v)(∂v/∂x)       │
│      ∂z/∂y = (∂z/∂u)(∂u/∂y) + (∂z/∂v)(∂v/∂y)       │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  6.4 隐函数求偏导                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  设 F(x,y,z) = 0                                    │
│                                                     │
│  则: ∂z/∂x = -Fₓ/Fᵤ = -Fₓ/Fᵤ                        │
│      ∂z/∂y = -Fᵧ/Fᵤ                                 │
│                                                     │
│  例: x² + y² + z² - 4z = 0, 求 ∂z/∂x               │
│                                                     │
│  解: F = x² + y² + z² - 4z                          │
│      Fₓ = 2x,  Fᵤ = 2z - 4                          │
│      ∂z/∂x = -2x/(2z-4) = x/(2-z)                  │
└─────────────────────────────────────────────────────┘
""")

    if HAS_SYMPY:
        input("按 Enter 查看偏导数演示...")
        multivariable_demo()
    else:
        input("按 Enter 继续...")


def multivariable_demo():
    """偏导数和全微分演示"""
    x, y, z = symbols('x y z')

    print("\n【偏导数计算】")
    print("-" * 50)

    f = x**2 + 3*x*y + y**2
    print(f"  f(x,y) = {f}")
    fx = diff(f, x)
    fy = diff(f, y)
    print(f"  ∂f/∂x = {fx}")
    print(f"  ∂f/∂y = {fy}")
    print(f"  ∂f/∂x|(1,2) = {fx.subs([(x,1),(y,2)])}")
    print(f"  ∂f/∂y|(1,2) = {fy.subs([(x,1),(y,2)])}")

    print("\n【隐函数偏导数】")
    print("-" * 50)
    F = x**2 + y**2 + z**2 - 4*z
    print(f"  F(x,y,z) = {F} = 0")
    Fx = diff(F, x)
    Fz = diff(F, z)
    print(f"  Fₓ = {Fx}")
    print(f"  Fᵤ = {Fz}")
    print(f"  ∂z/∂x = -Fₓ/Fᵤ = {-Fx/Fz} = x/(2-z)")

    print("\n【二阶偏导数】")
    print("-" * 50)
    f2 = sin(x*y)
    print(f"  f(x,y) = sin(xy)")
    fxx = diff(f2, x, 2)
    fyy = diff(f2, y, 2)
    fxy = diff(diff(f2, x), y)
    print(f"  ∂²f/∂x² = {sp.simplify(fxx)}")
    print(f"  ∂²f/∂y² = {sp.simplify(fyy)}")
    print(f"  ∂²f/∂x∂y = {sp.simplify(fxy)}")


def chapter_calculus_apps():
    """微分学应用教学"""
    print("\n" + "="*60)
    print("  第七章：微分学应用")
    print("="*60)

    print("""
┌─────────────────────────────────────────────────────┐
│  7.1 中值定理                                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  【罗尔定理】                                        │
│  条件: f(x) 在 [a,b] 连续, (a,b) 可导, f(a)=f(b)    │
│  结论: ∃ξ∈(a,b), 使得 f'(ξ) = 0                      │
│                                                     │
│  【拉格朗日中值定理】                                 │
│  条件: f(x) 在 [a,b] 连续, (a,b) 可导               │
│  结论: ∃ξ∈(a,b), 使得                               │
│        f(b)-f(a) = f'(ξ)                             │
│        ─────────                                    │
│           b-a                                       │
│                                                     │
│  【柯西中值定理】                                     │
│  条件: f(x), F(x) 在 [a,b] 连续, (a,b) 可导         │
│        F'(x) ≠ 0                                    │
│  结论: ∃ξ∈(a,b), 使得                               │
│        f(b)-f(a)   f'(ξ)                            │
│        ───────── = ─────                            │
│        F(b)-F(a)   F'(ξ)                            │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  7.2 函数的单调性与极值                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  单调性判别:                                         │
│  • f'(x) > 0 → f(x) 单调递增                        │
│  • f'(x) < 0 → f(x) 单调递减                        │
│                                                     │
│  极值的第一判别法:                                   │
│  • f'(x₀) = 0 (驻点)                                │
│  • f'(x) 在 x₀ 左右 "左正右负" → 极大值              │
│  • f'(x) 在 x₀ 左右 "左负右正" → 极小值              │
│  • f'(x) 在 x₀ 左右不变号 → 无极值                   │
│                                                     │
│  极值的第二判别法:                                   │
│  • f'(x₀) = 0, f''(x₀) ≠ 0                          │
│  • f''(x₀) < 0 → 极大值                             │
│  • f''(x₀) > 0 → 极小值                             │
└─────────────────────────────────────────────────────┘
""")

    input("按 Enter 继续...")
    print("""
┌─────────────────────────────────────────────────────┐
│  7.3 函数的凹凸性与拐点                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  凹凸性判别:                                         │
│  • f''(x) > 0 → f(x) 是凹的（下凸）                 │
│  • f''(x) < 0 → f(x) 是凸的（上凸）                 │
│                                                     │
│  拐点: 凹弧与凸弧的分界点                            │
│  求法: 令 f''(x) = 0, 检验左右两侧 f''(x) 是否变号   │
│                                                     │
│  例: f(x) = 2x³ - 9x² + 12x - 3                     │
│  f'(x) = 6x² - 18x + 12 = 6(x-1)(x-2)              │
│  令 f'(x) = 0 → x=1, x=2                            │
│  单调增区间: (-∞,1), (2,+∞)                          │
│  单调减区间: (1,2)                                   │
│  极大值: f(1) = 2    极小值: f(2) = 1                │
└─────────────────────────────────────────────────────┘
""")

    if HAS_SYMPY and HAS_PLOT:
        input("按 Enter 查看微分学应用演示...")
        calculus_apps_demo()
    else:
        input("按 Enter 继续...")


def calculus_apps_demo():
    """微分学应用可视化"""
    fig = plt.figure(figsize=(14, 10))

    x = symbols('x')

    # 1. 中值定理
    ax1 = fig.add_subplot(221)
    x_vals = np.linspace(0.5, 4, 500)
    f = lambda x: np.sqrt(x)
    f_prime = lambda x: 0.5 / np.sqrt(x)
    y_vals = f(x_vals)
    ax1.plot(x_vals, y_vals, 'b-', linewidth=2, label='f(x)=√x')
    # 中值定理: f(b)-f(a) = f'(ξ)(b-a)
    a_val, b_val = 1, 4
    secant_slope = (f(b_val)-f(a_val))/(b_val-a_val)
    xi = 2.25  # f'(ξ) = 0.5/√ξ = secant_slope → ξ = 1/(4*secant²)
    ax1.plot([a_val, b_val], [f(a_val), f(b_val)], 'r--', linewidth=1.5, label=f'割线斜率={secant_slope:.3f}')
    ax1.plot(xi, f(xi), 'go', markersize=8, label=f'ξ={xi:.2f}, f\'(ξ)={f_prime(xi):.3f}')
    ax1.axvline(x=xi, color='g', linestyle=':', alpha=0.5)
    ax1.set_title('拉格朗日中值定理\nf(b)-f(a)=f\'(ξ)(b-a)', fontsize=11)
    ax1.legend(fontsize=9); ax1.grid(True, alpha=0.3)

    # 2. 单调性与极值
    ax2 = fig.add_subplot(222)
    x2 = np.linspace(-0.5, 3, 500)
    f2 = 2*x2**3 - 9*x2**2 + 12*x2 - 3
    f2_prime = 6*x2**2 - 18*x2 + 12
    ax2.plot(x2, f2, 'b-', linewidth=2, label='f(x)=2x³-9x²+12x-3')
    ax2.plot(x2, f2_prime, 'r--', linewidth=1.5, alpha=0.7, label="f'(x)=6x²-18x+12")
    ax2.axhline(y=0, color='k', linewidth=0.5)
    ax2.plot(1, 2, 'go', markersize=8, label='极大值 f(1)=2')
    ax2.plot(2, 1, 'rs', markersize=8, label='极小值 f(2)=1')
    ax2.set_title('单调性与极值', fontsize=11)
    ax2.legend(fontsize=8); ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-5, 8)

    # 3. 凹凸性与拐点
    ax3 = fig.add_subplot(223)
    x3 = np.linspace(-1, 3, 500)
    f3 = 3*x3**4 - 4*x3**3 + 1
    f3_double = 36*x3**2 - 24*x3
    ax3.plot(x3, f3, 'b-', linewidth=2, label='f(x)=3x⁴-4x³+1')
    ax3.plot(x3, f3_double, 'r--', linewidth=1.5, alpha=0.7, label="f''(x)=36x²-24x")
    # 拐点
    x_inflect = [0, 2/3]
    y_inflect = [1, 3*(2/3)**4 - 4*(2/3)**3 + 1]
    ax3.plot(x_inflect, y_inflect, 'mo', markersize=8, label=f'拐点 ({x_inflect[1]:.2f}, {y_inflect[1]:.2f})')
    ax3.axhline(y=0, color='k', linewidth=0.5)
    ax3.set_title('凹凸性与拐点', fontsize=11)
    ax3.legend(fontsize=8); ax3.grid(True, alpha=0.3)
    ax3.set_ylim(-3, 5)

    # 4. 等价无穷小
    ax4 = fig.add_subplot(224)
    x4 = np.linspace(-3, 3, 500)
    x4_safe = x4.copy()
    x4_safe[x4_safe == 0] = 1e-10
    y_sin = np.sin(x4_safe)
    y_tan = np.tan(x4_safe)
    y_1cos = 1 - np.cos(x4_safe)
    ax4.plot(x4, y_sin, 'b-', linewidth=2, label='sin(x)')
    ax4.plot(x4, x4, 'r--', linewidth=1.5, label='x (等价无穷小)')
    ax4.plot(x4, y_1cos*2, 'g-', linewidth=1.5, alpha=0.7, label='2(1-cosx)≈x²')
    ax4.set_title('等价无穷小: sin(x)~x', fontsize=11)
    ax4.legend(fontsize=9); ax4.grid(True, alpha=0.3)
    ax4.set_xlim(-3, 3); ax4.set_ylim(-3, 3)

    plt.tight_layout()
    plt.savefig('calculus_apps_demo.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("微分学应用演示已显示!\n")


# ══════════════════════════════════════════════════════════════
#  练习题模块
# ══════════════════════════════════════════════════════════════

def practice_exercises():
    """练习题"""
    print("\n" + "="*60)
    print("  练习题")
    print("="*60)

    exercises = [
        {
            "title": "【向量代数】",
            "problem": "已知 a={1,2,-1}, b={2,-1,3}, 求:\n  (1) a·b   (2) a×b   (3) a与b的夹角",
            "hint": "点积 = 1×2+2×(-1)+(-1)×3\n叉积 = 用行列式计算\n夹角用 cosθ = (a·b)/(|a|·|b|)",
        },
        {
            "title": "【空间曲面】",
            "problem": "曲线 y²=2pz 绕 z 轴旋转，求旋转曲面方程",
            "hint": "绕 z 轴旋转: 用 ±√(x²+y²) 替换 y\n得 x²+y²=2pz (旋转抛物面)",
        },
        {
            "title": "【直线与平面】",
            "problem": "求过点(1,2,3)且与平面 2x+y-z+4=0 垂直的直线方程",
            "hint": "直线方向向量 = 平面法向量 = (2,1,-1)\n对称式: (x-1)/2 = (y-2)/1 = (z-3)/(-1)",
        },
        {
            "title": "【极限】",
            "problem": "求 lim(x→0) [sin(3x)/sin(5x)]",
            "hint": "用等价无穷小: sin(3x)~3x, sin(5x)~5x\n结果 = 3/5",
        },
        {
            "title": "【导数】",
            "problem": "求 y = e^(sinx) · ln(x²+1) 的导数",
            "hint": "用乘法法则: (uv)' = u'v + uv'\n注意链式法则",
        },
        {
            "title": "【隐函数求导】",
            "problem": "x²+y²=1, 求 dy/dx",
            "hint": "两边对x求导: 2x+2y·(dy/dx)=0\ndy/dx = -x/y",
        },
        {
            "title": "【极值】",
            "problem": "求 f(x) = x³-3x 的极值",
            "hint": "f'(x) = 3x²-3 = 3(x-1)(x+1)\n驻点 x=±1\nf''(x)=6x, f''(1)=6>0→极小值\nf''(-1)=-6<0→极大值",
        },
        {
            "title": "【多元函数偏导】",
            "problem": "z = x²y + sin(xy), 求 ∂z/∂x, ∂z/∂y",
            "hint": "∂z/∂x = 2xy + y·cos(xy)\n∂z/∂y = x² + x·cos(xy)",
        },
    ]

    for i, ex in enumerate(exercises, 1):
        print(f"\n{'─'*55}")
        print(f"  第 {i} 题 {ex['title']}")
        print(f"{'─'*55}")
        print(f"  题目: {ex['problem']}")
        ans = input("\n  输入你的答案（或按 Enter 查看提示）: ").strip()
        if not ans:
            print(f"  💡 提示:\n  {ex['hint']}")
        else:
            print(f"  你输入了: {ans}")
            show = input("  按 Enter 查看标准答案...").strip()
            print(f"  💡 标准答案提示:\n  {ex['hint']}")
        print()


# ══════════════════════════════════════════════════════════════
#  主程序
# ══════════════════════════════════════════════════════════════

def main_menu():
    """主菜单"""
    while True:
        print("\n" + "═"*60)
        print("  ╔════════════════════════════════════════════════╗")
        print("  ║  交互式数学教学程序                          ║")
        print("  ║  空间解析几何 & 微分学                        ║")
        print("  ╠════════════════════════════════════════════════╣")
        print("  ║  [1] 向量代数                                ║")
        print("  ║  [2] 空间曲面                                ║")
        print("  ║  [3] 直线与平面                              ║")
        print("  ║  [4] 函数、极限、连续                        ║")
        print("  ║  [5] 导数与微分                              ║")
        print("  ║  [6] 多元函数微分学                          ║")
        print("  ║  [7] 微分学应用                              ║")
        print("  ║  [8] 练习题                                  ║")
        print("  ║  [0] 退出                                    ║")
        print("  ╚════════════════════════════════════════════════╝")
        print("═"*60)

        choice = input("\n  请选择 (0-8): ").strip()

        if choice == '1':
            chapter_vector_algebra()
        elif choice == '2':
            chapter_surfaces()
        elif choice == '3':
            chapter_lines_planes()
        elif choice == '4':
            chapter_limits()
        elif choice == '5':
            chapter_derivatives()
        elif choice == '6':
            chapter_multivariable()
        elif choice == '7':
            chapter_calculus_apps()
        elif choice == '8':
            practice_exercises()
        elif choice == '0':
            print("\n  再见！学习愉快！📚\n")
            break
        else:
            print("  无效选择，请输入 0-8")


if __name__ == "__main__":
    print("正在加载数学教学程序...")
    if HAS_SYMPY:
        print("  ✓ sympy 符号运算引擎已加载")
    else:
        print("  ✗ sympy 未安装 (pip install sympy)")
    if HAS_PLOT:
        print("  ✓ matplotlib 图形引擎已加载")
    else:
        print("  ✗ matplotlib 未安装 (pip install matplotlib)")
    main_menu()
