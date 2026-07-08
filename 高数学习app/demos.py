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
    plt.close(fig)


# ══════════════════════════════════════════════════════════════
#  CH2 空间曲面 — 每节独立图形演示
# ══════════════════════════════════════════════════════════════

def demo_surface_rotation():
    """旋转曲面生成过程"""
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('旋转曲面 — y²=2pz 绕 z 轴旋转', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(121)
    z = np.linspace(0, 3, 50)
    y = np.sqrt(2 * z)
    ax1.plot(y, z, 'b-', linewidth=2.5, label='母线: y²=2z')
    ax1.plot(-y, z, 'b--', linewidth=2.5, alpha=0.5)
    ax1.axhline(y=0, color='gray', linewidth=0.5)
    ax1.axvline(x=0, color='gray', linewidth=0.5)
    ax1.fill_betweenx(z, -y, y, alpha=0.15, color='blue')
    ax1.text(0, 2.5, '绕z轴旋转', fontsize=10, rotation=90, ha='center', color='red')
    ax1.annotate('', xy=(0, 0.5), xytext=(0, 3),
                 arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
    ax1.set_xlim(-3.5, 3.5)
    ax1.set_ylim(-0.5, 3.5)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('母线 (旋转前)', fontsize=11)
    ax1.set_xlabel('y')
    ax1.set_ylabel('z')

    ax2 = fig.add_subplot(122, projection='3d')
    theta = np.linspace(0, 2 * np.pi, 40)
    z2 = np.linspace(0, 3, 30)
    THETA, Z2 = np.meshgrid(theta, z2)
    R = np.sqrt(2 * Z2)
    X2 = R * np.cos(THETA)
    Y2 = R * np.sin(THETA)
    ax2.plot_surface(X2, Y2, Z2, alpha=0.6, cmap='coolwarm', edgecolor='none')
    ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')
    ax2.set_title('旋转抛物面 (旋转后)', fontsize=11)
    plt.tight_layout()
    plt.show()


def demo_surface_cylinder():
    """柱面几何演示"""
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('柱面 — 平行于定直线的曲面', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(121)
    theta = np.linspace(0, 2 * np.pi, 100)
    x = np.cos(theta)
    y = np.sin(theta)
    ax1.plot(x, y, 'b-', linewidth=2.5, label='准线: x²+y²=1')
    ax1.quiver(1, 0, 0, 1, angles='xy', scale_units='xy', scale=1, color='red', width=0.01)
    ax1.quiver(0, 1, 2, 0, angles='xy', scale_units='xy', scale=1, color='red', width=0.01)
    ax1.text(1.2, 0.8, '母线∥z轴', fontsize=10, color='red')
    ax1.set_xlim(-1.5, 1.5)
    ax1.set_ylim(-1.5, 1.5)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_title('准线 (xy平面)', fontsize=11)

    ax2 = fig.add_subplot(122, projection='3d')
    theta2 = np.linspace(0, 2 * np.pi, 40)
    z2 = np.linspace(-1.5, 1.5, 30)
    THETA2, Z2 = np.meshgrid(theta2, z2)
    X2 = np.cos(THETA2)
    Y2 = np.sin(THETA2)
    ax2.plot_surface(X2, Y2, Z2, alpha=0.5, cmap='Blues', edgecolor='none')
    ax2.plot(np.cos(theta2), np.sin(theta2), -1.5 * np.ones_like(theta2), 'r-', linewidth=1.5)
    ax2.plot(np.cos(theta2), np.sin(theta2), 1.5 * np.ones_like(theta2), 'r-', linewidth=1.5)
    ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')
    ax2.set_title('圆柱面: x²+y²=1 (平行z轴)', fontsize=11)
    plt.tight_layout()
    plt.show()


def demo_surface_quadric():
    """二次曲面 — 六种基本类型"""
    fig = plt.figure(figsize=(12, 8))
    fig.suptitle('二次曲面的六种基本类型', fontsize=14, fontweight='bold')

    axs = []
    for idx in range(6):
        axs.append(fig.add_subplot(2, 3, idx + 1, projection='3d'))

    u = np.linspace(0, 2 * np.pi, 40); v = np.linspace(0, np.pi, 40)
    x = 2 * np.outer(np.cos(u), np.sin(v)); y = 1.5 * np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u)), np.cos(v))
    axs[0].plot_surface(x, y, z, alpha=0.6, cmap='coolwarm', edgecolor='none')
    axs[0].set_title('椭球面')

    r = np.linspace(0, 2, 40); THETA = np.linspace(0, 2 * np.pi, 40); R, THETA = np.meshgrid(r, THETA)
    X = R * np.cos(THETA); Y = R * np.sin(THETA); Z = X**2 / 4 + Y**2 / 4
    axs[1].plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm', edgecolor='none')
    axs[1].set_title('椭圆抛物面')

    x = np.linspace(-2, 2, 40); y = np.linspace(-2, 2, 40); X, Y = np.meshgrid(x, y)
    Z = X**2 / 4 - Y**2 / 4
    axs[2].plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm', edgecolor='none')
    axs[2].set_title('双曲抛物面(鞍面)')

    u = np.linspace(0, 2 * np.pi, 40); v = np.linspace(-1.5, 1.5, 30)
    X = 1.5 * np.outer(np.cosh(v), np.cos(u)); Y = 1.5 * np.outer(np.cosh(v), np.sin(u))
    Z = np.outer(np.sinh(v), np.ones(np.size(u)))
    axs[3].plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm', edgecolor='none')
    axs[3].set_title('单叶双曲面')

    theta = np.linspace(0, 2 * np.pi, 40); z = np.linspace(-2, 2, 30); THETA, Z = np.meshgrid(theta, z)
    R = np.abs(Z); X = R * np.cos(THETA); Y = R * np.sin(THETA)
    axs[4].plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm', edgecolor='none')
    axs[4].set_title('二次锥面')

    theta = np.linspace(0, 2 * np.pi, 40); z = np.linspace(-2, 2, 30); THETA, Z = np.meshgrid(theta, z)
    X = np.cos(THETA); Y = np.sin(THETA)
    axs[5].plot_surface(X, Y, Z, alpha=0.6, cmap='coolwarm', edgecolor='none')
    axs[5].set_title('圆柱面')

    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════
#  CH3 直线与平面 — 每节独立演示
# ══════════════════════════════════════════════════════════════

def demo_plane_equation():
    """空间平面方程可视化"""
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('空间平面方程 — 点法式与一般式', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(121, projection='3d')
    x = np.linspace(-2, 2, 20); y = np.linspace(-2, 2, 20); X, Y = np.meshgrid(x, y)
    Z = 2 - X - Y
    ax1.plot_surface(X, Y, Z, alpha=0.6, cmap='Blues', edgecolor='none')
    n = np.array([1, 1, 1]) / np.linalg.norm([1, 1, 1])
    ax1.quiver(0, 0, 2, n[0], n[1], n[2], color='red', linewidth=3, label='法向量 n')
    ax1.text(0, 0, 2, 'P₀(0,0,2)', fontsize=9, color='red')
    ax1.set_xlabel('X'); ax1.set_ylabel('Y'); ax1.set_zlabel('Z')
    ax1.set_title('平面: x+y+z=2\n法向量 n=(1,1,1)', fontsize=11)
    ax1.legend()

    ax2 = fig.add_subplot(122, projection='3d')
    x2 = np.linspace(-2, 2, 20); y2 = np.linspace(-2, 2, 20); X2, Y2 = np.meshgrid(x2, y2)
    Z2_1 = 1 + X2 - Y2; Z2_2 = 2 - X2 + Y2
    ax2.plot_surface(X2, Y2, Z2_1, alpha=0.4, cmap='Reds', edgecolor='none')
    ax2.plot_surface(X2, Y2, Z2_2, alpha=0.4, cmap='Blues', edgecolor='none')
    ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')
    ax2.set_title('两平面相交 → 交线', fontsize=11)
    plt.tight_layout()
    plt.show()


def demo_line_equation():
    """空间直线方程可视化"""
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('空间直线方程 — 对称式与参数式', fontsize=14, fontweight='bold')

    ax = fig.add_subplot(111, projection='3d')
    t = np.linspace(-2, 2, 100)
    x0, y0, z0 = 1, 1, 0; m, n, p = 1, 2, 1
    x = x0 + m * t; y = y0 + n * t; z = z0 + p * t
    ax.plot(x, y, z, 'b-', linewidth=3, label='直线 L')
    ax.plot([x0], [y0], [z0], 'ro', markersize=10, label=f'点P₀({x0},{y0},{z0})')
    s = np.array([m, n, p]) / np.linalg.norm([m, n, p])
    ax.quiver(x0, y0, z0, s[0], s[1], s[2], color='red', linewidth=2, label='方向向量 s')
    ax.text(x0 - 0.8, y0 - 0.8, z0 - 0.5, f'P₀({x0},{y0},{z0})', fontsize=10, color='red')
    ax.text(x0 + 1.5, y0 + 2.5, z0 + 1.5, f's=({m},{n},{p})', fontsize=10, color='red')
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title('直线: (x-1)/1 = (y-1)/2 = z/1', fontsize=11)
    ax.legend()
    ax.set_xlim(-2, 4); ax.set_ylim(-2, 5); ax.set_zlim(-2, 3)
    plt.tight_layout()
    plt.show()


def demo_plane_line_relations():
    """直线与平面的位置关系"""
    fig = plt.figure(figsize=(15, 5))
    fig.suptitle('直线与平面的位置关系', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(131, projection='3d')
    x = np.linspace(0, 2, 10); y = np.linspace(0, 2, 10); X, Y = np.meshgrid(x, y)
    ax1.plot_surface(X, Y, np.ones_like(X) * 1.5, alpha=0.4, cmap='Blues', edgecolor='none')
    t = np.linspace(-1, 3, 50)
    ax1.plot(t, np.ones_like(t) * 1, np.ones_like(t) * 1.5, 'r-', linewidth=3, label='直线在平面内')
    ax1.set_title('直线在平面内')

    ax2 = fig.add_subplot(132, projection='3d')
    x = np.linspace(0, 2, 10); y = np.linspace(0, 2, 10); X, Y = np.meshgrid(x, y)
    ax2.plot_surface(X, Y, np.ones_like(X) * 1.5, alpha=0.4, cmap='Blues', edgecolor='none')
    t = np.linspace(0, 2, 50)
    ax2.plot(t, np.ones_like(t) * 1, t, 'r-', linewidth=3, label='直线与平面相交')
    ax2.plot(1, 1, 1.5, 'go', markersize=10, label='交点')
    ax2.set_title('直线与平面相交')

    ax3 = fig.add_subplot(133, projection='3d')
    x = np.linspace(0, 2, 10); y = np.linspace(0, 2, 10); X, Y = np.meshgrid(x, y)
    ax3.plot_surface(X, Y, np.ones_like(X) * 1.5, alpha=0.4, cmap='Blues', edgecolor='none')
    t = np.linspace(0, 2, 50)
    ax3.plot(t, np.ones_like(t) * 1, np.ones_like(t) * 3, 'r-', linewidth=3, label='直线平行平面')
    ax3.set_title('直线平行于平面')

    for ax in [ax1, ax2, ax3]:
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        ax.legend(fontsize=8)
        ax.set_xlim(0, 2); ax.set_ylim(0, 2); ax.set_zlim(0, 3)
    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════
#  CH4 极限与连续 — 每节独立演示
# ══════════════════════════════════════════════════════════════

def demo_function_graph():
    """基本初等函数图形"""
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle('六种基本初等函数的图像', fontsize=14, fontweight='bold')

    x = np.linspace(-3, 3, 400); x_pos = np.linspace(0.01, 3, 400)

    axes[0, 0].plot(x, x**2, 'b-', linewidth=2); axes[0, 0].set_title('y=x² 幂函数'); axes[0, 0].grid(True, alpha=0.3)
    axes[0, 1].plot(x, np.sin(x), 'r-', linewidth=2); axes[0, 1].set_title('y=sinx 三角函数'); axes[0, 1].grid(True, alpha=0.3)
    axes[0, 2].plot(x, np.cos(x), 'g-', linewidth=2); axes[0, 2].set_title('y=cosx 三角函数'); axes[0, 2].grid(True, alpha=0.3)
    axes[1, 0].plot(x, np.exp(x), 'b-', linewidth=2); axes[1, 0].set_title('y=eˣ 指数函数'); axes[1, 0].grid(True, alpha=0.3)
    axes[1, 1].plot(x_pos, np.log(x_pos), 'r-', linewidth=2); axes[1, 1].set_title('y=lnx 对数函数'); axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].axhline(y=0, color='gray', linewidth=0.5); axes[1, 1].axvline(x=0, color='gray', linewidth=0.5)
    axes[1, 2].plot(x, np.arctan(x), 'purple', linewidth=2); axes[1, 2].set_title('y=arctanx 反三角函数'); axes[1, 2].grid(True, alpha=0.3)
    axes[1, 2].axhline(y=np.pi/2, color='gray', linestyle='--', alpha=0.5)
    axes[1, 2].axhline(y=-np.pi/2, color='gray', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()


def demo_limits_geometric():
    """极限的几何意义 — 逼近过程"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('极限的几何意义 — 无限逼近', fontsize=14, fontweight='bold')

    ax = axes[0]
    x = np.linspace(-4, 4, 500); y = np.sin(x) / np.where(np.abs(x) < 1e-8, 1e-8, x)
    ax.plot(x, y, 'b-', linewidth=2, label='f(x)=sin(x)/x')
    ax.axhline(y=1, color='r', linestyle='--', alpha=0.6)
    ax.plot(0, 1, 'ro', markersize=10, label='极限点 (0,1)')
    ax.set_xlim(-4, 4); ax.set_ylim(-0.3, 1.5)
    ax.grid(True, alpha=0.3); ax.legend(); ax.set_title('lim sin(x)/x = 1', fontsize=11)

    ax = axes[1]
    x2 = np.linspace(0.001, 5, 400); y2 = 1 / x2
    ax.plot(x2, y2, 'b-', linewidth=2, label='f(x)=1/x')
    ax.axhline(y=0, color='gray', linewidth=0.5); ax.axvline(x=0, color='gray', linewidth=0.5)
    ax.annotate('x→+∞', xy=(4, 0.25), fontsize=11, color='red', arrowprops=dict(arrowstyle='->', color='red'))
    ax.annotate('x→0⁺', xy=(0.3, 3.5), fontsize=11, color='red', arrowprops=dict(arrowstyle='->', color='red'))
    ax.set_xlim(-0.5, 5); ax.set_ylim(-0.5, 5)
    ax.grid(True, alpha=0.3); ax.legend(); ax.set_title('lim 1/x (x→+∞)=0', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_lhospital():
    """洛必达法则几何示意"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('洛必达法则 — 比较变化率', fontsize=14, fontweight='bold')

    ax = axes[0]
    x = np.linspace(-2, 2, 400)
    ax.plot(x, np.sin(x), 'b-', linewidth=2, label='f(x)=sinx')
    ax.plot(x, x, 'r-', linewidth=2, label='g(x)=x')
    ax.plot(0, 0, 'go', markersize=10, label='0/0型')
    ax.set_xlim(-2, 2); ax.set_ylim(-2, 2)
    ax.grid(True, alpha=0.3); ax.legend()
    ax.set_title('0/0型: lim sin(x)/x', fontsize=10)

    ax = axes[1]
    x = np.linspace(0.5, 5, 400)
    ax.plot(x, np.exp(x), 'b-', linewidth=2, label='f(x)=eˣ')
    ax.plot(x, x**2, 'r-', linewidth=2, label='g(x)=x²')
    ax.set_xlim(0.5, 5); ax.set_ylim(0, 150)
    ax.grid(True, alpha=0.3); ax.legend()
    ax.set_title('∞/∞型: lim eˣ/x²', fontsize=10)

    plt.tight_layout()
    plt.show()


def demo_continuity():
    """连续性几何示意"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle('连续与间断的几何区别', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(-2, 2, 400)
    ax.plot(x, x**3 - x + 1, 'b-', linewidth=2)
    ax.set_title('连续: 一笔画成', fontsize=11); ax.grid(True, alpha=0.3)

    ax = axes[1]; x = np.linspace(-2, 3, 400)
    y = np.where(np.abs(x - 1) > 0.01, (x**2 - 1) / (x - 1), np.nan)
    ax.plot(x, y, 'g-', linewidth=2)
    ax.plot(1, 2, 'go', markersize=12, markerfacecolor='white', markeredgewidth=2, label='可去间断')
    ax.set_title('可去间断', fontsize=11); ax.grid(True, alpha=0.3); ax.legend()

    ax = axes[2]; x = np.linspace(-2, 2, 400); y = np.sign(x)
    ax.plot(x, y, 'r-', linewidth=2)
    ax.plot(0, 1, 'ro', markersize=10); ax.plot(0, -1, 'ro', markersize=10, markerfacecolor='white', markeredgewidth=2)
    ax.set_title('跳跃间断', fontsize=11); ax.set_ylim(-1.5, 1.5); ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════
#  CH5 导数与微分 — 每节独立演示
# ══════════════════════════════════════════════════════════════

def demo_derivative_definition():
    """导数定义 — 切线形成过程"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('导数的定义 — 割线→切线', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(-1, 3, 400); f = lambda x: x**2
    ax.plot(x, f(x), 'b-', linewidth=2, label='f(x)=x²')
    x0 = 1.5; hs = [1.2, 0.6, 0.2]; colors = ['#FF6B6B', '#FFD93D', '#6BCB77']
    for h, c in zip(hs, colors):
        x1 = x0 + h; sec_x = np.linspace(x0 - 0.3, x1 + 0.3, 10)
        sec_y = f(x0) + (f(x1) - f(x0)) / (x1 - x0) * (sec_x - x0)
        ax.plot(sec_x, sec_y, '--', color=c, linewidth=1.5, label=f'h={h}')
    t_x = np.linspace(x0 - 1, x0 + 1, 100); t_y = f(x0) + 2 * x0 * (t_x - x0)
    ax.plot(t_x, t_y, 'r-', linewidth=2.5, label='切线(h→0)')
    ax.plot(x0, f(x0), 'go', markersize=10)
    ax.set_xlim(-1.5, 3.5); ax.set_ylim(-1, 10)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8); ax.set_title('割线→切线', fontsize=11)

    ax = axes[1]; x = np.linspace(-2, 2, 400)
    ax.plot(x, np.abs(x), 'b-', linewidth=2.5, label='f(x)=|x|')
    ax.plot(0, 0, 'ro', markersize=10)
    ax.annotate('尖点: 不可导', xy=(0, 0), xytext=(0.5, 1.5), arrowprops=dict(arrowstyle='->', color='red'), fontsize=11, color='red')
    ax.set_xlim(-2.5, 2.5); ax.set_ylim(-0.5, 2.5)
    ax.grid(True, alpha=0.3); ax.legend(); ax.set_title('|x|在x=0处不可导', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_derivative_rules():
    """求导法则可视化"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle('求导法则的几何意义', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(-2 * np.pi, 2 * np.pi, 400)
    ax.plot(x, np.sin(x), 'b-', linewidth=2, label='sinx')
    ax.plot(x, np.cos(x), 'r--', linewidth=2, label="(sinx)'=cosx")
    ax.axhline(y=0, color='gray', linewidth=0.5)
    ax.set_title("(sinx)'=cosx", fontsize=10); ax.grid(True, alpha=0.3); ax.legend()

    ax = axes[1]; x = np.linspace(-2, 2, 400); u = x**2; v = np.sin(x)
    uv_p = np.gradient(u * v, x); formula = 2 * x * v + u * np.cos(x)
    ax.plot(x, uv_p, 'b-', linewidth=2, label="(uv)'数值")
    ax.plot(x, formula, 'r--', linewidth=2, label="u'v+uv'")
    ax.set_title("积法则", fontsize=10); ax.grid(True, alpha=0.3); ax.legend()

    ax = axes[2]; x = np.linspace(-2, 2, 400)
    outer = np.exp(x**2)
    ax.plot(x, np.gradient(outer, x), 'b-', linewidth=2, label="链式结果")
    ax.plot(x, 2 * x * np.exp(x**2), 'r--', linewidth=2, label="公式")
    ax.set_title('链式法则', fontsize=10); ax.grid(True, alpha=0.3); ax.legend()

    plt.tight_layout()
    plt.show()


def demo_implicit_diff():
    """隐函数求导几何示意"""
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('隐函数求导 — 圆的切线', fontsize=14, fontweight='bold')

    ax = fig.add_subplot(121)
    theta = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(theta), np.sin(theta), 'b-', linewidth=2.5, label='x²+y²=1')
    for x0, y0 in [(np.sqrt(2)/2, np.sqrt(2)/2), (1, 0), (0, 1), (-0.7, 0.7)]:
        if abs(y0) > 1e-6:
            slope = -x0 / y0; tx = np.linspace(x0 - 0.5, x0 + 0.5, 10)
            ax.plot(tx, y0 + slope * (tx - x0), '--', linewidth=1.5)
        ax.plot(x0, y0, 'ro', markersize=6)
    ax.set_aspect('equal'); ax.grid(True, alpha=0.3); ax.legend()
    ax.set_title("隐函数: y'=-x/y", fontsize=11)

    ax = fig.add_subplot(122); x = np.linspace(0.01, 3, 300)
    ax.plot(x, x**x, 'b-', linewidth=2.5, label='y=xˣ')
    ax.plot(x, x**x * (1 + np.log(x)), 'r--', linewidth=2, label="y'")
    ax.grid(True, alpha=0.3); ax.legend(); ax.set_title("对数求导法", fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_higher_order():
    """高阶导数与微分的几何意义"""
    fig = plt.figure(figsize=(14, 5))
    fig.suptitle('高阶导数与微分的几何意义', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(121); x = np.linspace(-2 * np.pi, 2 * np.pi, 400)
    ax1.plot(x, np.sin(x), 'b-', linewidth=2, label='y=sinx')
    ax1.plot(x, np.cos(x), 'r--', linewidth=2, label="y'=cosx")
    ax1.plot(x, -np.sin(x), 'g-.', linewidth=2, label="y''=-sinx")
    ax1.axhline(y=0, color='gray', linewidth=0.5)
    ax1.grid(True, alpha=0.3); ax1.legend(); ax1.set_title('三阶导数', fontsize=11)

    ax2 = fig.add_subplot(122); x0, dx = 1.5, 0.5; f = lambda x: x**2
    x = np.linspace(0.5, 2.5, 400)
    ax2.plot(x, f(x), 'b-', linewidth=2, label='y=x²')
    t_x = np.linspace(x0 - 0.5, x0 + dx + 0.5, 100); t_y = f(x0) + 2 * x0 * (t_x - x0)
    ax2.plot(t_x, t_y, 'r--', linewidth=1.5, label='切线')
    ax2.plot(x0, f(x0), 'ro', markersize=8)
    ax2.annotate('dx', xy=(x0 + dx/2, f(x0)-0.3), fontsize=11, color='green', ha='center')
    ax2.grid(True, alpha=0.3); ax2.legend(); ax2.set_title('微分: dy≈Δy', fontsize=11)

    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════
#  CH6 多元函数微分 — 每节独立演示
# ══════════════════════════════════════════════════════════════

def demo_multi_concept():
    """多元函数 — 曲面图形"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), subplot_kw={'projection': '3d'})
    fig.suptitle('二元函数 z=f(x,y) 的几何表示', fontsize=14, fontweight='bold')

    x = np.linspace(-2, 2, 40); y = np.linspace(-2, 2, 40); X, Y = np.meshgrid(x, y)

    axes[0].plot_surface(X, Y, X**2 + Y**2, alpha=0.7, cmap='coolwarm', edgecolor='none')
    axes[0].set_title('z=x²+y² 旋转抛物面')

    Z2 = np.sqrt(np.maximum(0, 4 - X**2 - Y**2))
    axes[1].plot_surface(X, Y, Z2, alpha=0.7, cmap='Blues', edgecolor='none')
    axes[1].set_title('z=√(4-x²-y²) 上半球面')

    axes[2].plot_surface(X, Y, X**2 - Y**2, alpha=0.7, cmap='coolwarm', edgecolor='none')
    axes[2].set_title('z=x²-y² 鞍面')

    for ax in axes: ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    plt.tight_layout()
    plt.show()


def demo_partial_derivative():
    """偏导数几何意义 — 切线斜率"""
    fig = plt.figure(figsize=(14, 6))
    fig.suptitle('偏导数的几何意义 — 曲面截痕的切线', fontsize=14, fontweight='bold')

    ax = fig.add_subplot(121, projection='3d')
    x = np.linspace(-2, 2, 40); y = np.linspace(-2, 2, 40); X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2
    ax.plot_surface(X, Y, Z, alpha=0.5, cmap='coolwarm', edgecolor='none')
    y0 = 0.8; ax.contour(X, Y, Z, levels=[y0**2], colors='red', linewidths=2)
    x_c = np.linspace(-2, 2, 50); z_c = x_c**2 + y0**2
    ax.plot(x_c, np.ones_like(x_c) * y0, z_c, 'r-', linewidth=2.5, label=f'y={y0}截痕')
    ax.set_title('∂z/∂x: 沿x方向切线斜率', fontsize=10)
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z'); ax.legend(fontsize=8)

    ax = fig.add_subplot(122, projection='3d')
    ax.plot_surface(X, Y, Z, alpha=0.5, cmap='coolwarm', edgecolor='none')
    x0 = 0.8; y_c = np.linspace(-2, 2, 50); z_c2 = x0**2 + y_c**2
    ax.plot(np.ones_like(y_c) * x0, y_c, z_c2, 'r-', linewidth=2.5, label=f'x={x0}截痕')
    ax.set_title('∂z/∂y: 沿y方向切线斜率', fontsize=10)
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z'); ax.legend(fontsize=8)

    plt.tight_layout()
    plt.show()


def demo_total_differential():
    """全微分 — 切平面"""
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('全微分 — 切平面近似曲面', fontsize=14, fontweight='bold')

    ax = fig.add_subplot(121, projection='3d')
    x = np.linspace(-2, 2, 30); y = np.linspace(-2, 2, 30); X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2
    ax.plot_surface(X, Y, Z, alpha=0.5, cmap='coolwarm', edgecolor='none')
    x0, y0 = 0.5, 0.5; z0 = x0**2 + y0**2
    Z_tan = z0 + 2 * x0 * (X - x0) + 2 * y0 * (Y - y0)
    ax.plot_surface(X, Y, Z_tan, alpha=0.3, cmap='Reds', edgecolor='none')
    ax.plot([x0], [y0], [z0], 'ko', markersize=10)
    ax.set_title('切平面(红)贴合曲面', fontsize=10)
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')

    ax = fig.add_subplot(122, projection='3d')
    Z_diff = np.abs(Z - Z_tan)
    ax.plot_surface(X, Y, Z_diff, alpha=0.7, cmap='Reds', edgecolor='none')
    ax.set_title('误差: 越靠近切点误差越小', fontsize=10)
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('误差')

    plt.tight_layout()
    plt.show()


def demo_chain_rule():
    """复合函数链式法则 — 路径图"""
    if not HAS_SYMPY:
        print("sympy 未安装，请安装 sympy: pip install sympy")
        return
    x, y, t = sp.symbols('x y t')
    print("\n【链式法则示例】")
    print("=" * 45)
    print("设 z = f(x,y), x=φ(t), y=ψ(t)")
    print("  dz/dt = (∂z/∂x)(dx/dt) + (∂z/∂y)(dy/dt)")
    print("-" * 45)
    z_expr = x**2 + y**2; x_expr = sp.cos(t); y_expr = sp.sin(t)
    dz_dx = sp.diff(z_expr, x); dz_dy = sp.diff(z_expr, y)
    dx_dt = sp.diff(x_expr, t); dy_dt = sp.diff(y_expr, t)
    dz_dt = dz_dx.subs(x, x_expr) * dx_dt + dz_dy.subs(y, y_expr) * dy_dt
    print(f"z=x²+y², x=cos(t), y=sin(t)")
    print(f"∂z/∂x={dz_dx}, dx/dt={dx_dt}")
    print(f"∂z/∂y={dz_dy}, dy/dt={dy_dt}")
    print(f"dz/dt={sp.simplify(dz_dt)}")
    print(f"直接代入: z=cos²t+sin²t=1, dz/dt=0 ✓")
    print("=" * 45)
    print("【偏导链式法则示意图】")
    print("     z")
    print("    / \\")
    print("   x   y")
    print("   |   |")
    print("   多路径相乘再相加")


def demo_gradient():
    """梯度可视化"""
    fig = plt.figure(figsize=(14, 6))
    fig.suptitle('梯度 — 函数增长最快的方向', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(121)
    x = np.linspace(-2, 2, 30); y = np.linspace(-2, 2, 30); X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2
    cp = ax1.contour(X, Y, Z, levels=np.linspace(0.5, 8, 10), colors='gray', linewidths=1)
    ax1.clabel(cp, inline=True, fontsize=8)
    for xi, yi in [(1, 1), (-1, 1), (1.5, -0.5)]:
        gx, gy = 2 * xi, 2 * yi; mag = np.sqrt(gx**2 + gy**2)
        ax1.quiver(xi, yi, gx/mag, gy/mag, color='red', scale=5, width=0.02)
    ax1.set_aspect('equal'); ax1.grid(True, alpha=0.3)
    ax1.set_title('梯度⊥等值线, 指向增长方向', fontsize=11)

    ax2 = fig.add_subplot(122, projection='3d')
    x = np.linspace(-2, 2, 40); y = np.linspace(-2, 2, 40); X, Y = np.meshgrid(x, y)
    ax2.plot_surface(X, Y, X**2 + Y**2, alpha=0.6, cmap='coolwarm', edgecolor='none')
    ax2.quiver(1, 1, 2, 2, 2, 4, color='red', linewidth=3)
    ax2.set_title('负梯度=最速下降方向', fontsize=11)
    ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')

    plt.tight_layout()
    plt.show()


def demo_multi_extreme():
    """多元函数极值可视化"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), subplot_kw={'projection': '3d'})
    fig.suptitle('多元函数的极值类型', fontsize=14, fontweight='bold')

    x = np.linspace(-2, 2, 40); y = np.linspace(-2, 2, 40); X, Y = np.meshgrid(x, y)

    axes[0].plot_surface(X, Y, X**2 + Y**2, alpha=0.7, cmap='Blues', edgecolor='none')
    axes[0].plot([0], [0], [0], 'ro', markersize=10)
    axes[0].set_title('极小值 (碗底)', fontsize=10)

    axes[1].plot_surface(X, Y, -X**2 - Y**2, alpha=0.7, cmap='Reds', edgecolor='none')
    axes[1].plot([0], [0], [0], 'ro', markersize=10)
    axes[1].set_title('极大值 (峰顶)', fontsize=10)

    axes[2].plot_surface(X, Y, X**2 - Y**2, alpha=0.7, cmap='coolwarm', edgecolor='none')
    axes[2].plot([0], [0], [0], 'ro', markersize=10)
    axes[2].set_title('鞍点 (非极值)', fontsize=10)

    for ax in axes: ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════
#  CH7 微分学应用 — 每节独立演示
# ══════════════════════════════════════════════════════════════

def demo_mean_value_theorems():
    """微分中值定理演示"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle('微分中值定理', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(0, 4, 400)
    f = lambda x: -(x - 1) * (x - 3) + 3
    ax.plot(x, f(x), 'b-', linewidth=2, label='f(x)')
    ax.plot([0, 4], [f(0), f(4)], 'ro', markersize=8)
    ax.axhline(y=f(0), color='gray', linestyle='--', alpha=0.5)
    ax.plot(2, f(2), 'go', markersize=10, label="ξ=2, f'(ξ)=0")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('罗尔定理: f(a)=f(b)⇒f\'(ξ)=0', fontsize=10)

    ax = axes[1]; x = np.linspace(0, 4, 400)
    f2 = lambda x: 0.5 * x**2
    ax.plot(x, f2(x), 'b-', linewidth=2, label='f(x)=0.5x²')
    ax.plot([0, 4], [f2(0), f2(4)], 'r--', linewidth=2)
    c2 = 2; tan_x = np.linspace(c2-1, c2+1, 10)
    ax.plot(tan_x, f2(c2) + c2*(tan_x-c2), 'g-', linewidth=2, label='切线∥弦')
    ax.plot(c2, f2(c2), 'go', markersize=10)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('拉格朗日: f(b)-f(a)=f\'(ξ)(b-a)', fontsize=10)

    ax = axes[2]; x = np.linspace(0, 3, 400)
    ax.plot(x, np.sin(x), 'b-', linewidth=2, label='sinx')
    ax.plot(x, x, 'r--', linewidth=2, alpha=0.7); ax.plot(x, -x, 'r--', linewidth=2, alpha=0.7)
    ax.set_title('|sinb-sina|≤|b-a|', fontsize=10)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)

    plt.tight_layout()
    plt.show()


def demo_taylor():
    """泰勒展开可视化"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('泰勒公式 — 多项式逼近函数', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(-2*np.pi, 2*np.pi, 400)
    ax.plot(x, np.sin(x), 'k-', linewidth=2.5, label='sinx')
    colors = ['#FF6B6B', '#FFD93D', '#6BCB77', '#4D96FF']
    for n, c in zip([1, 3, 5, 7], colors):
        approx = np.zeros_like(x)
        for k in range(0, n+1, 2):
            approx += (-1)**(k//2) * x**(k+1) / np.math.factorial(k+1)
        ax.plot(x, approx, '--', color=c, linewidth=1.5, label=f'{n}阶')
    ax.set_ylim(-2, 2); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('sinx的泰勒展开', fontsize=11)

    ax = axes[1]; x = np.linspace(-2, 3, 400)
    ax.plot(x, np.exp(x), 'k-', linewidth=2.5, label='eˣ')
    for n, c in zip([1, 2, 3, 4], colors):
        approx = np.ones_like(x); term = np.ones_like(x)
        for k in range(1, n+1): term *= x/k; approx += term
        ax.plot(x, approx, '--', color=c, linewidth=1.5, label=f'{n}阶')
    ax.set_ylim(-1, 8); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('eˣ的泰勒展开', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_monotonicity():
    """单调性与极值"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('函数的单调性与极值', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(-2, 2.5, 400); f = x**3 - 3*x; fp = 3*x**2 - 3
    ax.plot(x, f, 'b-', linewidth=2.5, label='f(x)=x³-3x')
    ax.fill_between(x, f, where=(fp > 0), alpha=0.3, color='#FF6B6B', label="f'>0↑")
    ax.fill_between(x, f, where=(fp < 0), alpha=0.3, color='#4D96FF', label="f'<0↓")
    ax.plot(-1, 2, 'ro', markersize=10, label='极大值'); ax.plot(1, -2, 'go', markersize=10, label='极小值')
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8); ax.set_title("f'(x)决定增减", fontsize=11)

    ax = axes[1]; x = np.linspace(-2, 2, 400)
    ax.plot(x, 0.25*x**4 - 0.5*x**2 + 1, 'b-', linewidth=2.5, label='f(x)')
    for xc in [-1, 0, 1]: ax.plot(xc, 0.25*xc**4 - 0.5*xc**2 + 1, 'ro', markersize=8)
    ax.grid(True, alpha=0.3); ax.legend(); ax.set_title('驻点不一定是极值点', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_asymptote():
    """渐近线和函数作图"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('渐近线与函数作图', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(0.1, 5, 400)
    ax.plot(x, 1/x, 'b-', linewidth=2, label='y=1/x')
    ax.plot(x, x+1/x, 'r-', linewidth=2, label='y=x+1/x')
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7, label='水平渐近线')
    ax.axvline(x=0, color='gray', linestyle=':', alpha=0.7, label='垂直渐近线')
    ax.plot(x, x, 'g--', linewidth=1.5, alpha=0.7, label='斜渐近线')
    ax.set_xlim(0, 5); ax.set_ylim(-1, 6); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('三种渐近线', fontsize=11)

    ax = axes[1]; x_d = np.linspace(-3, 3, 400)
    mask = np.abs(np.abs(x_d) - 1) > 0.05
    ax.plot(x_d[mask], x_d[mask]**3/(x_d[mask]**2-1), 'b-', linewidth=2, label='y=x³/(x²-1)')
    ax.axvline(x=1, color='red', linestyle='--', alpha=0.7); ax.axvline(x=-1, color='red', linestyle='--', alpha=0.7)
    ax.plot(x_d, x_d, 'g--', linewidth=1.5, alpha=0.7)
    ax.set_ylim(-10, 10); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('函数作图分析', fontsize=11)

    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════
#  CH8 不定积分 — 每节独立演示
# ══════════════════════════════════════════════════════════════

def demo_antiderivative():
    """原函数与不定积分 — 曲线族"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('原函数与不定积分 — 曲线族', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(-3, 3, 400)
    f = x**2
    for C in [-3, -2, -1, 0, 1, 2, 3]:
        ax.plot(x, x**3/3 + C, '-', linewidth=1.5, alpha=0.6)
    ax.plot(x, f, 'r-', linewidth=2.5, label='f(x)=x² (斜率)')
    ax.set_title('∫x²dx = x³/3+C\n曲线族斜率相同', fontsize=11)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8); ax.set_ylim(-6, 6)

    ax = axes[1]; x = np.linspace(-2*np.pi, 2*np.pi, 400)
    for C in [-2, -1, 0, 1, 2]:
        ax.plot(x, -np.cos(x)+C, '-', linewidth=1.5, alpha=0.6)
    ax.plot(x, np.sin(x), 'r-', linewidth=2.5, label='f(x)=sinx (斜率)')
    ax.set_title('∫sinxdx = -cosx+C', fontsize=11)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)

    plt.tight_layout()
    plt.show()


def demo_integral_formulas():
    """基本积分公式验证"""
    if not HAS_SYMPY:
        print("sympy 未安装，请安装 sympy: pip install sympy")
        return
    x = sp.symbols('x')
    print("\n【基本积分公式验证 (求导逆运算)】")
    print("=" * 50)
    formulas = [
        (x**3, "∫x³dx", x**4/4), (sp.sin(x), "∫sinxdx", -sp.cos(x)),
        (sp.cos(x), "∫cosxdx", sp.sin(x)), (sp.exp(x), "∫eˣdx", sp.exp(x)),
        (1/x, "∫(1/x)dx", sp.log(sp.Abs(x))), (1/(1+x**2), "∫dx/(1+x²)", sp.atan(x)),
    ]
    for f, name, correct in formulas:
        result = sp.integrate(f, x)
        status = "✓" if sp.simplify(result - correct) == 0 else "?"
        print(f"  {status} {name} = {result} + C")
    print("=" * 50)
    print("验证: 对结果求导应等于被积函数")


def demo_substitution():
    """换元积分法演示"""
    if not HAS_SYMPY:
        print("sympy 未安装，请安装 sympy: pip install sympy")
        return
    x = sp.symbols('x')
    print("\n【第一类换元法: 凑微分】")
    print("=" * 45)
    print("∫f(g(x))·g'(x)dx = ∫f(u)du, u=g(x)")
    print("-" * 45)
    examples = [
        (x*sp.cos(x**2), "∫x·cos(x²)dx", sp.sin(x**2)/2),
        (sp.sin(3*x), "∫sin(3x)dx", -sp.cos(3*x)/3),
        (sp.log(x)/x, "∫(lnx/x)dx", sp.log(x)**2/2),
    ]
    for f, desc, result in examples:
        computed = sp.integrate(f, x)
        print(f"\n  {desc} = {result} + C")
        print(f"  验证: {computed} {'✓' if sp.simplify(computed-result)==0 else '?'}")

    print("\n【第二类换元法(三角代换)】")
    print("-" * 45)
    print("  √(a²-x²)→x=a·sint, √(a²+x²)→x=a·tant, √(x²-a²)→x=a·sect")
    r = sp.integrate(sp.sqrt(1-x**2), x)
    print(f"  ∫√(1-x²)dx = {sp.simplify(r)} + C (令 x=sint)")


def demo_integration_by_parts():
    """分部积分法演示"""
    if not HAS_SYMPY:
        print("sympy 未安装，请安装 sympy: pip install sympy")
        return
    x = sp.symbols('x')
    print("\n【分部积分公式: ∫u·dv = u·v - ∫v·du】")
    print("=" * 50)
    print("选u口诀: 反对幂指三")
    print("-" * 50)
    examples = [
        (x*sp.exp(x), "∫x·eˣdx", "u=x, dv=eˣdx"),
        (x*sp.cos(x), "∫x·cosxdx", "u=x, dv=cosxdx"),
        (sp.log(x), "∫lnxdx", "u=lnx, dv=dx"),
    ]
    for f, desc, hint in examples:
        result = sp.integrate(f, x)
        print(f"\n  {desc}  (令{hint})")
        print(f"    = {result} + C")
    print("\n  循环型: ∫eˣ·sinxdx = eˣ(sinx-cosx)/2 + C")


def demo_rational_integral():
    """有理函数积分"""
    if not HAS_SYMPY:
        print("sympy 未安装，请安装 sympy: pip install sympy")
        return
    x = sp.symbols('x')
    print("\n【有理函数积分 — 部分分式分解】")
    print("=" * 50)
    print("步骤: 多项式除法→因式分解→部分分式→积分")
    print("-" * 50)
    for f, desc in [( (x+3)/(x**2-5*x+6), "∫(x+3)/(x²-5x+6)dx" ),
                    ( 1/(1+x**2), "∫dx/(1+x²)" ),
                    ( 1/(x**2-1), "∫dx/(x²-1)" )]:
        result = sp.integrate(f, x)
        print(f"  {desc} = {sp.simplify(result)} + C")


# ══════════════════════════════════════════════════════════════
#  CH9 定积分 — 每节独立演示
# ══════════════════════════════════════════════════════════════

def demo_riemann_sum():
    """定积分 — 黎曼和逼近"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('定积分 — 黎曼和', fontsize=14, fontweight='bold')

    f = lambda x: 0.5*(x-2)**2 + 0.5; x = np.linspace(0, 4, 400)
    for idx, n in enumerate([4, 16]):
        ax = axes[idx]; ax.plot(x, f(x), 'b-', linewidth=2)
        xi = np.linspace(0, 4, n+1)[:-1]; width = 4/n
        for i in range(n):
            ax.add_patch(plt.Rectangle((xi[i], 0), width, f(xi[i]), alpha=0.3, color='#FF6B6B', edgecolor='#CC4444', linewidth=0.5))
        ax.set_title(f'n={n} (≈{sum(f(xi)*width):.4f})', fontsize=11)
        ax.set_xlim(-0.2, 4.2); ax.set_ylim(-0.2, 3); ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def demo_definite_properties():
    """定积分性质 — 估值定理"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('定积分的性质', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(0, np.pi, 400)
    ax.plot(x, np.sin(x), 'b-', linewidth=2.5, label='f(x)=sinx')
    ax.fill_between(x, np.sin(x), alpha=0.2, color='#FF6B6B')
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5, label='M=1')
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5, label='m=0')
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('估值: m(b-a)≤∫f≤M(b-a)', fontsize=11)

    ax = axes[1]; x = np.linspace(0, 4, 400); f = lambda x: np.exp(-x)
    ax.plot(x, f(x), 'b-', linewidth=2.5, label='f(x)=e⁻ˣ')
    mid_val = f(1.5)
    ax.fill_between(x, f(x), alpha=0.2, color='#4ECDC4')
    ax.axhline(y=mid_val, color='r', linestyle='--', alpha=0.5)
    ax.plot(1.5, mid_val, 'ro', markersize=10)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('中值定理: ∃ξ, ∫f=f(ξ)(b-a)', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_ftc():
    """微积分基本定理"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('微积分基本定理 — 连接微分与积分', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(-2, 2, 400)
    Phi = lambda x_arr: np.array([0.5*t**2 - 0.5*4 for t in x_arr])
    ax.plot(x, x, 'r-', linewidth=2, label='f(t)=t')
    ax.plot(x, Phi(x), 'b-', linewidth=2, label='Φ(x)=∫[-2→x]t dt')
    ax.axhline(y=0, color='gray', linewidth=0.5)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=9)
    ax.set_title("Φ'(x)=f(x)", fontsize=11)

    ax = axes[1]; x = np.linspace(-2, 2, 400)
    ax.plot(x, np.cos(x), 'r-', linewidth=2, label='f(x)=cosx')
    ax.plot(x, np.sin(x)-np.sin(-2), 'b-', linewidth=2, label='F(x)-F(a)')
    ax.fill_between(x, np.cos(x), alpha=0.2, color='#4ECDC4')
    ax.grid(True, alpha=0.3); ax.legend(fontsize=9)
    ax.set_title('∫[a→b]f = F(b)-F(a)', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_definite_calc():
    """定积分计算示例"""
    if not HAS_SYMPY:
        print("sympy 未安装，请安装 sympy: pip install sympy")
        return
    x = sp.symbols('x')
    print("\n【定积分计算 — 换元法】")
    print("=" * 45)
    print("原则: 换元必换限")
    r1 = sp.integrate(sp.sin(2*x), (x, 0, sp.pi/2))
    print(f"  ∫[0→π/2] sin(2x)dx = {r1}  (令 u=2x)")
    print("\n【定积分 — 分部法】")
    r2 = sp.integrate(x*sp.exp(x), (x, 0, 1))
    print(f"  ∫[0→1] x·eˣdx = {r2}")


def demo_improper_integral():
    """广义积分 — 收敛与发散"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('广义积分 — 有限 vs 无限面积', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(1, 10, 400)
    ax.plot(x, 1/x**2, 'b-', linewidth=2.5, label='1/x² (收敛)')
    ax.plot(x, 1/x, 'r-', linewidth=2.5, label='1/x (发散)')
    ax.fill_between(x, 1/x**2, alpha=0.3, color='blue', label='∫=1')
    ax.fill_between(x, 1/x, alpha=0.1, color='red')
    ax.set_xlim(1, 10); ax.set_ylim(0, 2); ax.grid(True, alpha=0.3); ax.legend(fontsize=9)
    ax.set_title('无穷限积分', fontsize=11)

    ax = axes[1]; x = np.linspace(0.01, 1, 400)
    ax.plot(x, 1/np.sqrt(x), 'b-', linewidth=2.5, label='1/√x (收敛)')
    ax.plot(x, 1/x, 'r-', linewidth=2.5, label='1/x (发散)')
    ax.fill_between(x, 1/np.sqrt(x), alpha=0.3, color='blue')
    ax.set_xlim(0, 1); ax.set_ylim(0, 5); ax.grid(True, alpha=0.3); ax.legend(fontsize=9)
    ax.set_title('无界函数积分', fontsize=11)

    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════
#  CH10 定积分应用 — 每节独立演示
# ══════════════════════════════════════════════════════════════

def demo_area_calc():
    """平面图形面积"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('定积分求面积 — 微元法', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(0, 2*np.pi, 400)
    ax.plot(x, np.sin(x), 'b-', linewidth=2, label='y=sinx')
    ax.fill_between(x, np.sin(x), where=(np.sin(x)>=0), alpha=0.3, color='#FF6B6B')
    ax.fill_between(x, np.sin(x), where=(np.sin(x)<0), alpha=0.3, color='#4ECDC4')
    ax.axhline(y=0, color='gray', linewidth=0.5); ax.grid(True, alpha=0.3); ax.legend()
    ax.set_title('A=∫|f(x)|dx', fontsize=11)

    ax = axes[1]; x = np.linspace(-2, 2, 400)
    ax.plot(x, 4-x**2, 'b-', linewidth=2, label='y=4-x²'); ax.plot(x, x**2, 'r-', linewidth=2, label='y=x²')
    ax.fill_between(x, x**2, 4-x**2, where=(4-x**2 > x**2), alpha=0.3, color='purple')
    ax.grid(True, alpha=0.3); ax.legend()
    ax.set_title('A=∫[f上-f下]dx', fontsize=11)

    plt.tight_layout()
    plt.show()


def demo_volume():
    """旋转体体积 — 圆盘法"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('旋转体体积 — 圆盘法', fontsize=14, fontweight='bold')

    ax = axes[0]; x = np.linspace(0, np.pi, 400)
    ax.plot(x, np.sin(x), 'b-', linewidth=2.5, label='y=sinx')
    for xi in np.linspace(0.3, np.pi-0.3, 8):
        ax.plot([xi, xi], [0, np.sin(xi)], 'r-', linewidth=1, alpha=0.5)
    ax.fill_between(x, np.sin(x), alpha=0.15, color='blue')
    ax.grid(True, alpha=0.3); ax.legend(); ax.set_xlim(0, np.pi); ax.set_ylim(-0.2, 1.3)
    ax.set_title('绕x轴: V=π∫f²dx', fontsize=10)

    ax = axes[1]; x = np.linspace(-1, 1, 400); y = np.sqrt(1-x**2)
    ax.plot(x, y, 'b-', linewidth=2.5, label='半圆'); ax.plot(x, -y, 'b-', linewidth=2.5)
    for xi in np.linspace(-0.8, 0.8, 7):
        ri = np.sqrt(1-xi**2); ax.plot([xi, xi], [-ri, ri], 'r-', linewidth=1, alpha=0.5)
    ax.fill_between(x, y, alpha=0.15, color='blue')
    ax.set_aspect('equal'); ax.grid(True, alpha=0.3)
    ax.set_title('绕x轴→球体 V=4πR³/3', fontsize=10)

    plt.tight_layout()
    plt.show()


def demo_arc_length():
    """曲线弧长"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('曲线弧长 — 微元累积', fontsize=14, fontweight='bold')

    ax = axes[0]; t = np.linspace(0, 2*np.pi, 500)
    ax.plot(3*np.cos(t), 2*np.sin(t), 'b-', linewidth=2.5, label='椭圆')
    t_seg = np.linspace(0, np.pi/2, 20); ax.plot(3*np.cos(t_seg), 2*np.sin(t_seg), 'r-', linewidth=3, alpha=0.7)
    ax.scatter(3*np.cos(t_seg), 2*np.sin(t_seg), s=15, c='red', alpha=0.5)
    ax.set_aspect('equal'); ax.grid(True, alpha=0.3); ax.legend(fontsize=9)
    ax.set_title('s=∫√(1+y\'²)dx', fontsize=10)

    ax = axes[1]; x = np.linspace(0, 4, 400)
    ax.plot(x, x**1.5, 'b-', linewidth=2.5)
    ds_x = np.linspace(0.5, 3.5, 10); ds_y = ds_x**1.5
    for i in range(len(ds_x)-1):
        ax.plot([ds_x[i], ds_x[i+1]], [ds_y[i], ds_y[i+1]], 'r-', linewidth=1.5, alpha=0.6)
    ax.grid(True, alpha=0.3); ax.set_title('ds=√(dx²+dy²)', fontsize=10)

    plt.tight_layout()
    plt.show()


def demo_surface_area():
    """旋转体侧面积"""
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('旋转体的侧面积', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(121); x = np.linspace(0, np.pi, 400); y = np.sin(x)
    ax1.plot(x, y, 'b-', linewidth=2.5, label='y=sinx')
    for xi in np.linspace(0.2, np.pi-0.2, 6):
        ax1.plot([xi, xi], [0, np.sin(xi)], 'r-', linewidth=1, alpha=0.4)
    ax1.fill_between(x, y, alpha=0.15, color='blue')
    ax1.grid(True, alpha=0.3); ax1.legend()
    ax1.set_title('S=2π∫f·√(1+f\'²)dx', fontsize=10)

    ax2 = fig.add_subplot(122); x = np.linspace(0, np.pi, 400)
    fp = np.cos(x); integrand = 2*np.pi*np.sin(x)*np.sqrt(1+fp**2)
    ax2.plot(x, integrand, 'r-', linewidth=2.5, label='2πf·√(1+f\'²)')
    ax2.fill_between(x, integrand, alpha=0.3, color='#FF6B6B')
    ax2.grid(True, alpha=0.3); ax2.legend()
    ax2.set_title('被积函数: 周长×弧长因子', fontsize=10)

    plt.tight_layout()
    plt.show()
