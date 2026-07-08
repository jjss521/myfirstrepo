#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学演示函数 —— 所有 matplotlib / SymPy 可视化演示。
每个函数创建并显示自己的图形，不依赖外部状态。
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — used implicitly by projection='3d'
from matplotlib import cm  # noqa: F401 — available for use
from matplotlib.patches import Polygon

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi']
matplotlib.rcParams['axes.unicode_minus'] = False

# SymPy is optional for demos that use symbolic computation
try:
    import sympy as sp
    from sympy import symbols, sin, cos, tan, ln, exp, pi, oo, limit, diff, integrate, simplify, Matrix, Rational, Function, Eq, solve  # noqa: F401
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False


# ══════════════════════════════════════════════════════════════
#  演示函数
# ══════════════════════════════════════════════════════════════

def demo_vectors():
    """向量运算可视化"""
    fig = plt.figure(figsize=(14, 5))

    ax1 = fig.add_subplot(131)
    a = np.array([3, 2])
    b = np.array([1, 3])
    ax1.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='red', label='a={3,2}')
    ax1.quiver(a[0], a[1], b[0], b[1], angles='xy', scale_units='xy', scale=1, color='blue', label='b={1,3}')
    ax1.quiver(0, 0, a[0] + b[0], a[1] + b[1], angles='xy', scale_units='xy', scale=1, color='green', label='a+b')
    ax1.set_xlim(-1, 6)
    ax1.set_ylim(-1, 6)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('向量加法')
    ax1.legend()

    ax2 = fig.add_subplot(132)
    a2 = np.array([3, 1])
    b2 = np.array([1, 2])
    ax2.quiver(0, 0, a2[0], a2[1], angles='xy', scale_units='xy', scale=1, color='red', label='a')
    ax2.quiver(0, 0, b2[0], b2[1], angles='xy', scale_units='xy', scale=1, color='blue', label='b')
    ax2.set_xlim(-1, 5)
    ax2.set_ylim(-1, 4)
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.set_title(f'点积: a·b = {np.dot(a2, b2)}')
    ax2.legend()

    ax3 = fig.add_subplot(133)
    verts = np.array([[0, 0], [3, 1], [4, 4], [1, 3]])
    poly = Polygon(verts, alpha=0.3, color='cyan', label='面积=8')
    ax3.add_patch(poly)
    ax3.quiver(0, 0, 3, 1, angles='xy', scale_units='xy', scale=1, color='red', label='a')
    ax3.quiver(0, 0, 1, 3, angles='xy', scale_units='xy', scale=1, color='blue', label='b')
    ax3.set_xlim(-1, 5)
    ax3.set_ylim(-1, 5)
    ax3.set_aspect('equal')
    ax3.grid(True, alpha=0.3)
    ax3.set_title('叉积面积')
    ax3.legend()

    plt.tight_layout()
    plt.show()


def demo_vector_meaning():
    """向量几何意义详解图"""
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle('向量 a = 3i + 2j 的几何意义详解', fontsize=16, fontweight='bold')

    # 图1: 向量分解图
    ax1 = fig.add_subplot(221)
    a = np.array([3, 2])
    ax1.annotate('', xy=(5, 0), xytext=(-0.5, 0),
                 arrowprops=dict(arrowstyle='->', color='black', lw=1))
    ax1.annotate('', xy=(0, 4), xytext=(0, -0.5),
                 arrowprops=dict(arrowstyle='->', color='black', lw=1))
    ax1.annotate('', xy=(3, 0), xytext=(0, 0),
                 arrowprops=dict(arrowstyle='->', color='#FF6B6B', lw=3))
    ax1.text(1.5, -0.3, '3i (向右走3格)', fontsize=10, color='#FF6B6B', ha='center')
    ax1.annotate('', xy=(3, 2), xytext=(3, 0),
                 arrowprops=dict(arrowstyle='->', color='#4ECDC4', lw=3))
    ax1.text(3.3, 1, '2j\n(向上走2格)', fontsize=10, color='#4ECDC4')
    ax1.annotate('', xy=(3, 2), xytext=(0, 0),
                 arrowprops=dict(arrowstyle='->', color='#007AFF', lw=4))
    ax1.plot(3, 2, 'o', color='#007AFF', markersize=10)
    ax1.text(3.2, 2.2, 'a = (3,2)', fontsize=12, color='#007AFF', fontweight='bold')
    ax1.plot([3, 3], [0, 2], '--', color='gray', alpha=0.5)
    ax1.plot([0, 3], [2, 2], '--', color='gray', alpha=0.5)
    ax1.set_xlim(-0.5, 4.5)
    ax1.set_ylim(-0.5, 3.5)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('向量分解: a = 3i + 2j', fontsize=12)
    ax1.set_xlabel('x (i方向)')
    ax1.set_ylabel('y (j方向)')

    # 图2: 位移路径图
    ax2 = fig.add_subplot(222)
    ax2.plot(0, 0, 'go', markersize=12, label='起点 (0,0)')
    ax2.annotate('', xy=(3, 0), xytext=(0, 0),
                 arrowprops=dict(arrowstyle='->', color='#FF6B6B', lw=3, linestyle='--'))
    ax2.text(1.5, -0.4, '向东走3步', fontsize=10, color='#FF6B6B', ha='center')
    ax2.annotate('', xy=(3, 2), xytext=(3, 0),
                 arrowprops=dict(arrowstyle='->', color='#4ECDC4', lw=3, linestyle='--'))
    ax2.text(3.4, 1, '向北走2步', fontsize=10, color='#4ECDC4')
    ax2.annotate('', xy=(3, 2), xytext=(0, 0),
                 arrowprops=dict(arrowstyle='->', color='#007AFF', lw=4))
    ax2.plot(3, 2, 'ro', markersize=12, label='终点 (3,2)')
    ax2.text(1.2, 1.5, '直达路径\n(向量a)', fontsize=11, color='#007AFF', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='#E6F1FB', alpha=0.8))
    ax2.set_xlim(-0.5, 4.5)
    ax2.set_ylim(-1, 3.5)
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')
    ax2.set_title('物理理解: 位移路径', fontsize=12)
    ax2.set_xlabel('x (东西方向)')
    ax2.set_ylabel('y (南北方向)')

    # 图3: 三种等价理解
    ax3 = fig.add_subplot(223)
    ax3.axis('off')
    text_content = """
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        📌 三种等价理解方式：

        1️⃣ 坐标理解：
           a 就是点 (3, 2) 的位置向量
           → "从原点到 (3,2) 怎么走"

        2️⃣ 分解理解：
           a = 水平分量 + 竖直分量
           = 3i（横着走 3）+ 2j（竖着走 2）

        3️⃣ 物理理解：
           从原点出发：
           • 先向东走 3 步 → 到达 (3, 0)
           • 再向北走 2 步 → 到达 (3, 2)
           这条直达路径就是向量 a

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
    ax3.text(0.1, 0.95, text_content, transform=ax3.transAxes,
             fontsize=11, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    ax3.set_title('三种理解方式', fontsize=12)

    # 图4: 单位向量与坐标表示
    ax4 = fig.add_subplot(224)
    ax4.annotate('', xy=(1, 0), xytext=(0, 0),
                 arrowprops=dict(arrowstyle='->', color='#FF6B6B', lw=2))
    ax4.text(0.5, -0.3, 'i = (1,0)', fontsize=10, color='#FF6B6B', ha='center')
    ax4.annotate('', xy=(0, 1), xytext=(0, 0),
                 arrowprops=dict(arrowstyle='->', color='#4ECDC4', lw=2))
    ax4.text(-0.3, 0.5, 'j = (0,1)', fontsize=10, color='#4ECDC4', rotation=90)
    ax4.annotate('', xy=(3, 2), xytext=(0, 0),
                 arrowprops=dict(arrowstyle='->', color='#007AFF', lw=3))
    ax4.text(1.5, 1.3, 'a = 3i + 2j', fontsize=12, color='#007AFF', fontweight='bold')
    ax4.text(3, -0.3, 'aₓ = 3', fontsize=10, color='#FF6B6B', ha='center')
    ax4.text(-0.5, 2, 'aᵧ = 2', fontsize=10, color='#4ECDC4')
    ax4.set_xlim(-1, 4.5)
    ax4.set_ylim(-1, 3.5)
    ax4.set_aspect('equal')
    ax4.grid(True, alpha=0.3)
    ax4.set_title('单位向量与坐标表示', fontsize=12)
    ax4.set_xlabel('x')
    ax4.set_ylabel('y')

    plt.tight_layout()
    plt.show()


def demo_vector_concept():
    """向量概念图：大小和方向"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle('向量的基本概念', fontsize=14, fontweight='bold')

    ax = axes[0]
    ax.quiver(0, 0, 3, 2, angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015)
    ax.quiver(0, 0, 2, 3, angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015)
    ax.annotate('a={3,2}', xy=(1.5, 1), fontsize=11, color='#FF6B6B')
    ax.annotate('b={2,3}', xy=(0.5, 1.8), fontsize=11, color='#4ECDC4')
    ax.set_xlim(-0.5, 4)
    ax.set_ylim(-0.5, 4)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('向量有方向', fontsize=11)
    ax.set_xlabel('x')
    ax.set_ylabel('y')

    ax = axes[1]
    ax.quiver(0, 0, 3, 0, angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015)
    ax.quiver(0, 0, 0, 4, angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015)
    ax.plot([0, 3], [0, 0], 'r--', alpha=0.5)
    ax.plot([0, 0], [0, 4], 'c--', alpha=0.5)
    ax.annotate('|a|=3', xy=(1.5, -0.4), fontsize=11, color='#FF6B6B')
    ax.annotate('|b|=4', xy=(-0.8, 2), fontsize=11, color='#4ECDC4')
    ax.set_xlim(-1, 4.5)
    ax.set_ylim(-1, 5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('向量有大小(模)', fontsize=11)

    ax = axes[2]
    length = np.sqrt(3**2 + 2**2)
    ax.quiver(0, 0, 3 / length, 2 / length, angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015)
    circle = plt.Circle((0, 0), 1, fill=False, color='gray', linestyle='--', linewidth=1)
    ax.add_patch(circle)
    ax.annotate('i', xy=(0.6, 0.2), fontsize=12, color='#FF6B6B', fontweight='bold')
    ax.annotate('|i|=1', xy=(0.3, -0.5), fontsize=11, color='gray')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('单位向量(模=1)', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_vector_decompose():
    """向量分解图：3D坐标表示"""
    fig = plt.figure(figsize=(10, 5))

    ax1 = fig.add_subplot(121)
    a = np.array([3, 2])
    ax1.quiver(0, 0, a[0], 0, angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='aₓ=3')
    ax1.quiver(3, 0, 0, a[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='aᵧ=2')
    ax1.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.02, label='a={3,2}')
    ax1.plot([3, 3], [0, 2], 'k--', alpha=0.3)
    ax1.plot([0, 3], [2, 2], 'k--', alpha=0.3)
    ax1.set_xlim(-0.5, 4.5)
    ax1.set_ylim(-0.5, 3.5)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_title('2D向量分解: a = 3i + 2j', fontsize=11)
    ax1.set_xlabel('x (i方向)')
    ax1.set_ylabel('y (j方向)')

    ax2 = fig.add_subplot(122, projection='3d')
    a3 = np.array([3, 2, -1])
    ax2.quiver(0, 0, 0, 3, 0, 0, color='#FF6B6B', arrow_length_ratio=0.1, linewidth=2)
    ax2.quiver(3, 0, 0, 0, 2, 0, color='#4ECDC4', arrow_length_ratio=0.1, linewidth=2)
    ax2.quiver(3, 2, 0, 0, 0, -1, color='#FFEAA7', arrow_length_ratio=0.1, linewidth=2)
    ax2.quiver(0, 0, 0, 3, 2, -1, color='#007AFF', arrow_length_ratio=0.1, linewidth=3)
    ax2.plot([3, 3], [0, 2], [0, 0], 'k--', alpha=0.3)
    ax2.plot([0, 3], [2, 2], [0, 0], 'k--', alpha=0.3)
    ax2.plot([3, 3], [2, 2], [0, -1], 'k--', alpha=0.3)
    ax2.text(1.5, 0, 0, 'aₓ=3', color='#FF6B6B', fontsize=10)
    ax2.text(3, 1, 0, 'aᵧ=2', color='#4ECDC4', fontsize=10)
    ax2.text(3, 2, -0.6, 'aᵤ=-1', color='#FFEAA7', fontsize=10)
    ax2.text(1.5, 1.2, -0.3, 'a={3,2,-1}', color='#007AFF', fontsize=11, fontweight='bold')
    ax2.set_xlabel('X (i)')
    ax2.set_ylabel('Y (j)')
    ax2.set_zlabel('Z (k)')
    ax2.set_title('3D向量分解: a = 3i + 2j - k', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_vector_add():
    """向量加法图"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle('向量加法的两种法则', fontsize=14, fontweight='bold')

    a = np.array([3, 1])
    b = np.array([1, 3])

    ax = axes[0]
    ax.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a={3,1}')
    ax.quiver(a[0], a[1], b[0], b[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='b={1,3}')
    ax.quiver(0, 0, a[0] + b[0], a[1] + b[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.02, label='a+b={4,4}')
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-0.5, 5.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
    ax.set_title('三角形法则', fontsize=11)

    ax = axes[1]
    verts = np.array([[0, 0], a, a + b, b])
    poly = Polygon(verts, alpha=0.2, color='#007AFF')
    ax.add_patch(poly)
    ax.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a')
    ax.quiver(0, 0, b[0], b[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='b')
    ax.quiver(0, 0, a[0] + b[0], a[1] + b[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.02, label='a+b')
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-0.5, 5.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
    ax.set_title('平行四边形法则', fontsize=11)

    ax = axes[2]
    a2 = np.array([2, 1])
    ax.quiver(0, 0, a2[0], a2[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a={2,1}')
    ax.quiver(0, 0, 2 * a2[0], 2 * a2[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.02, label='2a={4,2}')
    ax.quiver(0, 0, -a2[0], -a2[1], angles='xy', scale_units='xy', scale=1, color='#FF3B30', width=0.015, label='-a={-2,-1}')
    ax.set_xlim(-3, 5.5)
    ax.set_ylim(-2, 4)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
    ax.set_title('数乘: λa', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_vector_dot():
    """点积几何意义"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('数量积(点积)的几何意义', fontsize=14, fontweight='bold')

    ax = axes[0]
    a = np.array([4, 1])
    b = np.array([2, 3])
    ax.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a')
    ax.quiver(0, 0, b[0], b[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='b')
    theta = np.linspace(0, np.arctan2(b[1], b[0]), 30)
    ax.plot(1.2 * np.cos(theta), 1.2 * np.sin(theta), 'k-', linewidth=1)
    ax.text(0.8, 0.4, 'θ', fontsize=12)
    dot = np.dot(a, b)
    ax.text(2, 0.5, f'a·b = {dot}', fontsize=11, color='#007AFF', fontweight='bold')
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-0.5, 4.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    ax.set_title(f'a·b = |a|·|b|·cosθ = {dot}', fontsize=11)

    ax = axes[1]
    a2 = np.array([4, 2])
    b2 = np.array([3, 3])
    proj = np.dot(a2, b2) / np.dot(b2, b2) * b2
    ax.quiver(0, 0, a2[0], a2[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a')
    ax.quiver(0, 0, b2[0], b2[1], angles='xy', scale_units='xy', scale=1, color='#4ECDC4', width=0.015, label='b')
    ax.quiver(0, 0, proj[0], proj[1], angles='xy', scale_units='xy', scale=1, color='#FFEAA7', width=0.02, label='Prj_a(b)')
    ax.plot([a2[0], proj[0]], [a2[1], proj[1]], 'k--', alpha=0.5)
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-0.5, 4.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    ax.set_title('投影: Prj_b(a) = (a·b/|b|²)·b', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_vector_cross():
    """叉积几何意义"""
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('向量积(叉积)的几何意义', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(121)
    a = np.array([3, 1])
    b = np.array([1, 3])
    cross_val = a[0] * b[1] - a[1] * b[0]
    verts = np.array([[0, 0], a, a + b, b])
    poly = Polygon(verts, alpha=0.3, color='#4ECDC4')
    ax1.add_patch(poly)
    ax1.quiver(0, 0, a[0], a[1], angles='xy', scale_units='xy', scale=1, color='#FF6B6B', width=0.015, label='a={3,1}')
    ax1.quiver(0, 0, b[0], b[1], angles='xy', scale_units='xy', scale=1, color='#007AFF', width=0.015, label='b={1,3}')
    ax1.text(1.5, 1.5, f'面积={cross_val}', fontsize=12, color='#007AFF', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax1.set_xlim(-0.5, 5)
    ax1.set_ylim(-0.5, 5)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_title(f'|a×b| = 平行四边形面积 = {cross_val}', fontsize=11)

    ax2 = fig.add_subplot(122, projection='3d')
    a3 = np.array([2, 1, 0])
    b3 = np.array([1, 2, 0])
    c3 = np.cross(a3, b3)
    ax2.quiver(0, 0, 0, a3[0], a3[1], a3[2], color='#FF6B6B', arrow_length_ratio=0.1, linewidth=2, label='a')
    ax2.quiver(0, 0, 0, b3[0], b3[1], b3[2], color='#007AFF', arrow_length_ratio=0.1, linewidth=2, label='b')
    ax2.quiver(0, 0, 0, 0, 0, c3[2], color='#34C759', arrow_length_ratio=0.1, linewidth=3, label='a×b')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    ax2.legend(fontsize=10)
    ax2.set_title(f'右手规则: a×b ⊥ a, a×b ⊥ b\na×b = (0,0,{c3[2]})', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_surfaces():
    """二次曲面3D"""
    fig = plt.figure(figsize=(15, 10))

    ax1 = fig.add_subplot(231, projection='3d')
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    x = 2 * np.outer(np.cos(u), np.sin(v))
    y = 1.5 * np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u)), np.cos(v))
    ax1.plot_surface(x, y, z, alpha=0.6, cmap='coolwarm')
    ax1.set_title('椭球面')

    ax2 = fig.add_subplot(232, projection='3d')
    r = np.linspace(0, 2, 40)
    theta = np.linspace(0, 2 * np.pi, 40)
    R, THETA = np.meshgrid(r, theta)
    X = R * np.cos(THETA)
    Y = R * np.sin(THETA)
    Z = X**2 / 4 + Y**2 / 4
    ax2.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax2.set_title('旋转抛物面')

    ax3 = fig.add_subplot(233, projection='3d')
    x = np.linspace(-2, 2, 50)
    y = np.linspace(-2, 2, 50)
    X, Y = np.meshgrid(x, y)
    Z = X**2 / 4 - Y**2 / 4
    ax3.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax3.set_title('鞍面')

    ax4 = fig.add_subplot(234, projection='3d')
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(-1.5, 1.5, 30)
    X = 1.5 * np.outer(np.cosh(v), np.cos(u))
    Y = 1.5 * np.outer(np.cosh(v), np.sin(u))
    Z = np.outer(np.sinh(v), np.ones(np.size(u)))
    ax4.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax4.set_title('单叶双曲面')

    ax5 = fig.add_subplot(235, projection='3d')
    theta = np.linspace(0, 2 * np.pi, 50)
    z = np.linspace(-2, 2, 30)
    THETA, Z = np.meshgrid(theta, z)
    R = np.abs(Z)
    X = R * np.cos(THETA)
    Y = R * np.sin(THETA)
    ax5.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax5.set_title('二次锥面')

    ax6 = fig.add_subplot(236, projection='3d')
    theta = np.linspace(0, 2 * np.pi, 50)
    z = np.linspace(-2, 2, 30)
    THETA, Z = np.meshgrid(theta, z)
    X = np.cos(THETA)
    Y = np.sin(THETA)
    ax6.plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm')
    ax6.set_title('圆柱面')

    plt.tight_layout()
    plt.show()


def demo_limits():
    """极限几何意义演示"""
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle('极限与连续性的几何意义', fontsize=16, fontweight='bold')

    # 图1: lim sin(x)/x = 1
    ax1 = fig.add_subplot(221)
    x = np.linspace(-8, 8, 500)
    x_safe = x.copy()
    x_safe[x_safe == 0] = 1e-10
    y = np.sin(x_safe) / x_safe
    ax1.plot(x, y, 'b-', linewidth=2, label='sin(x)/x')
    ax1.axhline(y=1, color='r', linestyle='--', alpha=0.5, label='y=1 (极限值)')
    ax1.plot(0, 1, 'ro', markersize=10, label='极限点 (0,1)')
    ax1.fill_between(x, y, 1, alpha=0.2, color='yellow', label='逼近过程')
    ax1.set_xlim(-8, 8)
    ax1.set_ylim(-0.3, 1.5)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    ax1.set_title('lim(sinx/x) = 1\n曲线无限逼近y=1', fontsize=12)
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')

    # 图2: lim (1+1/x)^x = e
    ax2 = fig.add_subplot(222)
    x2 = np.linspace(1, 100, 200)
    y2 = (1 + 1 / x2)**x2
    ax2.plot(x2, y2, 'b-', linewidth=2, label='(1+1/x)^x')
    ax2.axhline(y=np.e, color='r', linestyle='--', alpha=0.5, label=f'y=e≈{np.e:.4f} (极限值)')
    ax2.fill_between(x2, y2, np.e, alpha=0.2, color='yellow', label='逼近过程')
    ax2.set_xlim(0, 105)
    ax2.set_ylim(2, 3)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    ax2.set_title('lim(1+1/x)^x = e\n曲线无限逼近y=e', fontsize=12)
    ax2.set_xlabel('x')
    ax2.set_ylabel('y')

    # 图3: 连续性
    ax3 = fig.add_subplot(223)
    x3 = np.linspace(-2, 3, 500)
    y3_cont = np.sin(x3) + 1
    ax3.plot(x3, y3_cont, 'b-', linewidth=2, label='连续: sin(x)+1')
    y3_removable = np.where(x3 != 1, (x3**2 - 1) / (x3 - 1), 0)
    ax3.plot(x3, y3_removable, 'g--', linewidth=2, label='可去间断点')
    ax3.plot(1, 2, 'go', markersize=10, markerfacecolor='white', markeredgewidth=2)
    ax3.set_xlim(-2.5, 3.5)
    ax3.set_ylim(-0.5, 3)
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)
    ax3.set_title('连续 vs 可去间断点\n连续=一笔画成，可去=有个洞', fontsize=12)
    ax3.set_xlabel('x')
    ax3.set_ylabel('y')

    # 图4: 间断点类型
    ax4 = fig.add_subplot(224)
    x4 = np.linspace(-3, 3, 500)
    y4_jump = np.where(x4 < 0, -1, 1)
    ax4.step(x4, y4_jump, 'b-', linewidth=2, where='mid', label='跳跃间断点')
    ax4.plot(0, -1, 'bo', markersize=8, markerfacecolor='white', markeredgewidth=2)
    ax4.plot(0, 1, 'bo', markersize=8)
    x4_inf = x4[np.abs(x4) > 0.3]
    y4_inf = 1 / x4_inf
    ax4.plot(x4_inf, y4_inf, 'r-', linewidth=2, label='无穷间断点')
    ax4.set_xlim(-3, 3)
    ax4.set_ylim(-5, 5)
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=9)
    ax4.set_title('跳跃间断点 vs 无穷间断点\n跳跃=突然跳变，无穷=冲向∞', fontsize=12)
    ax4.set_xlabel('x')
    ax4.set_ylabel('y')

    plt.tight_layout()
    plt.show()


def demo_derivatives():
    """导数几何意义演示"""
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle('导数的几何意义', fontsize=16, fontweight='bold')

    # 图1: 切线斜率
    ax1 = fig.add_subplot(221)
    x = np.linspace(-2, 3, 500)
    y = x**3 - 3 * x + 2
    ax1.plot(x, y, 'b-', linewidth=2, label='f(x) = x³-3x+2')
    x0 = 1
    y0 = x0**3 - 3 * x0 + 2
    slope = 3 * x0**2 - 3
    tangent_x = np.linspace(x0 - 1.5, x0 + 1.5, 100)
    tangent_y = y0 + slope * (tangent_x - x0)
    ax1.plot(tangent_x, tangent_y, 'r--', linewidth=2, label=f'切线 (斜率={slope})')
    ax1.plot(x0, y0, 'go', markersize=10, label=f'切点 ({x0},{y0})')
    ax1.set_xlim(-2.5, 3.5)
    ax1.set_ylim(-3, 6)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_title("f'(x₀) = 切线斜率", fontsize=12)
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')

    # 图2: 单调性
    ax2 = fig.add_subplot(222)
    x2 = np.linspace(-2, 2.5, 500)
    y2 = x2**3 - 3 * x2
    y2_prime = 3 * x2**2 - 3
    ax2.plot(x2, y2, 'b-', linewidth=2, label='f(x) = x³-3x')
    ax2.fill_between(x2, y2, where=(y2_prime > 0), alpha=0.3, color='green', label="f'(x)>0 递增")
    ax2.fill_between(x2, y2, where=(y2_prime < 0), alpha=0.3, color='red', label="f'(x)<0 递减")
    ax2.plot(1, -2, 'go', markersize=10, label='极小值 f(1)=-2')
    ax2.plot(-1, 2, 'rs', markersize=10, label='极大值 f(-1)=2')
    ax2.set_xlim(-2.5, 3)
    ax2.set_ylim(-4, 4)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    ax2.set_title("f'(x) 判断单调性", fontsize=12)
    ax2.set_xlabel('x')
    ax2.set_ylabel('y')

    # 图3: 凹凸性
    ax3 = fig.add_subplot(223)
    x3 = np.linspace(-2, 2, 500)
    y3 = x3**4 - 4 * x3**2 + 5
    y3_double = 12 * x3**2 - 8
    ax3.plot(x3, y3, 'b-', linewidth=2, label='f(x) = x⁴-4x²+5')
    ax3.fill_between(x3, y3, where=(y3_double > 0), alpha=0.3, color='cyan', label="f''(x)>0 凹")
    ax3.fill_between(x3, y3, where=(y3_double < 0), alpha=0.3, color='yellow', label="f''(x)<0 凸")
    inflection_x = np.sqrt(2 / 3)
    inflection_y = inflection_x**4 - 4 * inflection_x**2 + 5
    ax3.plot([-inflection_x, inflection_x], [inflection_y, inflection_y], 'mo', markersize=10, label='拐点')
    ax3.set_xlim(-2.2, 2.2)
    ax3.set_ylim(0, 6)
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)
    ax3.set_title("f''(x) 判断凹凸性", fontsize=12)
    ax3.set_xlabel('x')
    ax3.set_ylabel('y')

    # 图4: 极值判别
    ax4 = fig.add_subplot(224)
    x4 = np.linspace(-2, 2, 500)
    y4_prime = 3 * x4**2 - 3
    y4_double = 6 * x4
    ax4.plot(x4, y4_prime, 'b-', linewidth=2, label="f'(x) = 3x²-3")
    ax4.plot(x4, y4_double, 'r--', linewidth=2, label="f''(x) = 6x")
    ax4.axhline(y=0, color='k', linewidth=0.5)
    ax4.plot([-1, 1], [0, 0], 'go', markersize=10)
    ax4.text(-1, 0.5, "f'(-1)=0\nf''(-1)=-6<0\n极大值", fontsize=9, ha='center', color='green')
    ax4.text(1, -0.5, "f'(1)=0\nf''(1)=6>0\n极小值", fontsize=9, ha='center', color='green')
    ax4.set_xlim(-2.5, 2.5)
    ax4.set_ylim(-8, 10)
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    ax4.set_title('极值判别法', fontsize=12)
    ax4.set_xlabel('x')
    ax4.set_ylabel('y')

    plt.tight_layout()
    plt.show()


def demo_multivariable():
    """偏导数演示（终端输出）"""
    if not HAS_SYMPY:
        print("sympy 未安装，无法运行偏导数演示")
        return
    x, y = symbols('x y')
    print("\n【偏导数演示】")
    f = x**2 + 3 * x * y + y**2
    print(f"  f(x,y) = {f}")
    print(f"  ∂f/∂x = {diff(f, x)}")
    print(f"  ∂f/∂y = {diff(f, y)}")


def demo_calculus_apps():
    """微分学应用演示"""
    fig = plt.figure(figsize=(14, 5))

    ax1 = fig.add_subplot(121)
    x = np.linspace(-0.5, 3, 500)
    f = 2 * x**3 - 9 * x**2 + 12 * x - 3
    fp = 6 * x**2 - 18 * x + 12
    ax1.plot(x, f, 'b-', linewidth=2, label='f(x)=2x³-9x²+12x-3')
    ax1.plot(x, fp, 'r--', linewidth=1.5, alpha=0.7, label="f'(x)")
    ax1.plot(1, 2, 'go', markersize=8, label='极大值 f(1)=2')
    ax1.plot(2, 1, 'rs', markersize=8, label='极小值 f(2)=1')
    ax1.axhline(y=0, color='k', linewidth=0.5)
    ax1.set_title('单调性与极值')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = fig.add_subplot(122)
    x2 = np.linspace(-1, 3, 500)
    f2 = 3 * x2**4 - 4 * x2**3 + 1
    f2p = 36 * x2**2 - 24 * x2
    ax2.plot(x2, f2, 'b-', linewidth=2, label='f(x)=3x⁴-4x³+1')
    ax2.plot(x2, f2p, 'r--', linewidth=1.5, alpha=0.7, label="f''(x)")
    ax2.plot(2 / 3, 3 * (2 / 3)**4 - 4 * (2 / 3)**3 + 1, 'mo', markersize=8, label='拐点')
    ax2.axhline(y=0, color='k', linewidth=0.5)
    ax2.set_title('凹凸性与拐点')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def demo_lines_planes():
    """直线平面方程演示（终端输出）"""
    if not HAS_SYMPY:
        print("sympy 未安装，无法运行直线平面方程演示")
        return
    x, y, z = symbols('x y z')
    print("\n【例题1】求过三点 A(1,2,3), B(3,4,5), C(-2,4,7) 的平面方程")
    AB = Matrix([2, 2, 2])
    AC = Matrix([-3, 2, 4])
    n = AB.cross(AC)
    print(f"  法向量 n = {n.T}")
    plane = n[0] * (x - 1) + n[1] * (y - 2) + n[2] * (z - 3)
    print(f"  平面方程: {sp.expand(plane)} = 0")


# ══════════════════════════════════════════════════════════════
#  积分学演示
# ══════════════════════════════════════════════════════════════

def demo_indefinite_integral():
    """不定积分演示"""
    if not HAS_SYMPY:
        print("sympy 未安装，无法运行不定积分演示")
        return
    x = sp.symbols('x')
    print("\n【不定积分公式验证】")
    print("-" * 50)
    funcs = [
        (x**3, "∫x³dx"),
        (sp.sin(x), "∫sinxdx"),
        (sp.exp(x), "∫eˣdx"),
        (1/x, "∫(1/x)dx"),
        (sp.cos(x), "∫cosxdx"),
        (sp.tan(x), "∫tanxdx"),
        (1/(1+x**2), "∫dx/(1+ x²)"),
    ]
    for f, name in funcs:
        result = sp.integrate(f, x)
        print(f"  {name} = {result} + C")

    print("\n【换元积分演示】")
    print("-" * 50)
    f1 = sp.sin(3*x)
    r1 = sp.integrate(f1, x)
    print(f"  ∫sin(3x)dx = {r1} + C")

    f2 = x*sp.sin(x**2)
    r2 = sp.integrate(f2, x)
    print(f"  ∫xsin(x²)dx = {r2} + C")

    print("\n【分部积分演示】")
    print("-" * 50)
    f3 = x*sp.exp(x)
    r3 = sp.integrate(f3, x)
    print(f"  ∫xeˣdx = {r3} + C")

    f4 = sp.log(x)
    r4 = sp.integrate(f4, x)
    print(f"  ∫lnxdx = {r4} + C")


def demo_definite_integral():
    """定积分几何意义 (黎曼和)"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('定积分的几何意义 — 黎曼和逼近', fontsize=14, fontweight='bold')

    x = np.linspace(0, 4, 400)
    f = lambda x: 0.5 * (x - 2)**2 + 0.5

    for idx, n in enumerate([4, 8, 20]):
        ax = axes[idx]
        ax.plot(x, f(x), 'b-', linewidth=2, label=f'f(x) = (x-2)²/2 + 0.5')

        xi = np.linspace(0, 4, n+1)[:-1]
        width = 4 / n
        for i in range(n):
            rect = plt.Rectangle((xi[i], 0), width, f(xi[i]),
                                  alpha=0.3, color='#FF6B6B', edgecolor='#CC4444', linewidth=0.5)
            ax.add_patch(rect)

        approx = sum(f(xi) * width)
        ax.set_xlim(-0.2, 4.2)
        ax.set_ylim(-0.2, 3)
        ax.grid(True, alpha=0.3)
        ax.set_title(f'n = {n} (近似值 = {approx:.4f})', fontsize=11)
        ax.set_xlabel('x')
        ax.set_ylabel('y')

    plt.tight_layout()
    plt.show()


def demo_integral_applications():
    """定积分应用可视化"""
    fig = plt.figure(figsize=(15, 5))
    fig.suptitle('定积分应用', fontsize=14, fontweight='bold')

    # 图1: 求面积
    ax1 = fig.add_subplot(131)
    x = np.linspace(0, 2*np.pi, 400)
    y1 = np.sin(x)
    y2 = np.zeros_like(x)
    ax1.fill_between(x, y1, y2, where=(y1 >= 0), alpha=0.3, color='#FF6B6B', label='正面积')
    ax1.fill_between(x, y1, y2, where=(y1 < 0), alpha=0.3, color='#4ECDC4', label='负面积')
    ax1.plot(x, y1, 'b-', linewidth=2)
    ax1.axhline(y=0, color='gray', linewidth=0.5)
    ax1.grid(True, alpha=0.3)
    ax1.set_title('面积: ∫sin(x)dx', fontsize=11)
    ax1.legend()

    # 图2: 旋转体 (绕x轴)
    ax2 = fig.add_subplot(132, projection='3d')
    x2 = np.linspace(0, np.pi, 100)
    theta = np.linspace(0, 2*np.pi, 30)
    X2, THETA2 = np.meshgrid(x2, theta)
    R2 = np.sin(X2)
    Y2 = R2 * np.cos(THETA2)
    Z2 = R2 * np.sin(THETA2)
    ax2.plot_surface(X2, Y2, Z2, alpha=0.6, cmap='coolwarm')
    ax2.set_xlabel('x'); ax2.set_ylabel('y'); ax2.set_zlabel('z')
    ax2.set_title('y=sinx绕x轴旋转', fontsize=11)

    # 图3: 弧长
    ax3 = fig.add_subplot(133)
    t = np.linspace(0, 2*np.pi, 500)
    x3 = 3 * np.cos(t)
    y3 = 2 * np.sin(t)
    ax3.plot(x3, y3, 'b-', linewidth=2, label='椭圆')
    # 标记一段弧
    t_seg = np.linspace(0, np.pi/2, 50)
    x_seg = 3 * np.cos(t_seg)
    y_seg = 2 * np.sin(t_seg)
    ax3.plot(x_seg, y_seg, 'r-', linewidth=3, alpha=0.7, label='弧长微元')
    ax3.scatter(x_seg[0], y_seg[0], 50, 'r', zorder=5)
    ax3.scatter(x_seg[-1], y_seg[-1], 50, 'r', zorder=5)
    ax3.set_aspect('equal')
    ax3.grid(True, alpha=0.3)
    ax3.set_title('弧长: s=∫√(dx²+dy²)', fontsize=11)
    ax3.legend()

    plt.tight_layout()
    plt.show()
