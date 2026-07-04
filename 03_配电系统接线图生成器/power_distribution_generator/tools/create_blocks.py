"""
CAD图块创建辅助工具

参照《氛围化编程指令书_配电系统图生成器.md》第4章。

当 blocks/ 目录中缺少DWG文件时，本工具可通过AutoCAD COM接口
自动创建标准回路图块。

用法：
    python create_blocks.py          # 通过COM在AutoCAD中创建所有图块
    python create_blocks.py --export  # 创建图块并导出到DWG文件

DWG文件缺失时的替代方案：
    程序内置了 create_temp_block() 方法（cad_driver.py），
    可在内存中创建简易图块（仅含属性定义文字占位），
    无需DWG文件即可完成图块插入和属性填充。
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# blocks目录
BLOCKS_DIR = Path(__file__).resolve().parent.parent / "blocks"


# 图块属性定义（第4.2节）
# (标签, 提示文字, X坐标, Y坐标)
BLOCK_ATTRIBUTES = {
    "进线回路": [
        ("CIRCUIT_NAME", "回路名称", 50, 280),
        ("CIRCUIT_NO", "回路编号", 50, 260),
        ("PE_POWER", "功率(kW)", 50, 240),
        ("IC_CURRENT", "电流(A)", 50, 220),
        ("FRAME_CURRENT", "壳架(A)", 50, 200),
        ("IN_RATED", "In(A)", 50, 180),
        ("IS1", "Is1(A)", 50, 160),
        ("IS2", "Is2(A)", 200, 160),
        ("IS3", "Is3(A)", 350, 160),
        ("CT_RATIO", "CT变比", 50, 140),
        ("MONITOR", "监控信号", 50, 120),
        ("CABLE_SPEC", "线缆型号", 50, 100),
        ("CABLE_NO", "线缆编号", 260, 100),
        ("UNIT_SPACE", "单元空间", 260, 280),
    ],
    "馈线回路": [
        ("CIRCUIT_NAME", "回路名称", 50, 280),
        ("CIRCUIT_NO", "回路编号", 50, 260),
        ("PE_POWER", "功率(kW)", 50, 240),
        ("IC_CURRENT", "电流(A)", 50, 220),
        ("FRAME_CURRENT", "壳架(A)", 50, 200),
        ("IN_RATED", "In(A)", 50, 180),
        ("IS1", "Is1(A)", 50, 160),
        ("IS2", "Is2(A)", 200, 160),
        ("IS3", "Is3(A)", 350, 160),
        ("CT_RATIO", "CT变比", 50, 140),
        ("MONITOR", "监控信号", 50, 120),
        ("CABLE_SPEC", "线缆型号", 50, 100),
        ("CABLE_NO", "线缆编号", 260, 100),
        ("UNIT_SPACE", "单元空间", 260, 280),
    ],
    "备用回路": [
        ("CIRCUIT_NAME", "回路名称", 50, 240),
        ("FRAME_CURRENT", "壳架(A)", 50, 200),
        ("IN_RATED", "In(A)", 50, 160),
    ],
}


def create_block_in_autocad(block_name: str, export_dwg: bool = False):
    """在AutoCAD中创建标准回路图块

    图块以左上角(0,0)为基准点（第4.3节），包含：
    - 外框矩形（800×400）
    - 所有属性定义（AttDef）
    - 左侧母线连接点标记

    Args:
        block_name: 图块名称
        export_dwg: 是否导出为DWG文件
    """
    import comtypes.client
    from comtypes import COMError

    try:
        acad = comtypes.client.GetActiveObject("AutoCAD.Application")
        acad.Visible = True
        doc = acad.ActiveDocument
        blocks = doc.Blocks
    except (COMError, AttributeError):
        print("❌ 无法连接AutoCAD，请确保AutoCAD已启动")
        return False

    # 检查图块是否已存在
    for i in range(blocks.Count):
        if blocks.Item(i).Name == block_name:
            print(f"图块 '{block_name}' 已存在，跳过")
            return True

    # 获取属性定义列表
    attrs = BLOCK_ATTRIBUTES.get(block_name, BLOCK_ATTRIBUTES["馈线回路"])

    # 创建图块定义（基准点设在0,0左上角）
    origin = comtypes.client.CreateObject("AutoCAD.APoint", (0, 0, 0))
    temp_block = blocks.Add(origin, block_name)

    # 绘制外框矩形
    corners = [
        (0, 0, 0),
        (450, 0, 0),
        (450, 320, 0),
        (0, 320, 0),
        (0, 0, 0),
    ]
    for i in range(len(corners) - 1):
        start = comtypes.client.CreateObject(
            "AutoCAD.APoint", corners[i]
        )
        end = comtypes.client.CreateObject(
            "AutoCAD.APoint", corners[i + 1]
        )
        temp_block.AddLine(start, end)

    # 添加属性定义
    for tag, prompt, x_pos, y_pos in attrs:
        att_def = temp_block.AddAttribute(
            1,  # acAttributeModeVerify
            1,  # InsertionPoint
            tag,
            prompt,
            tag,  # 默认值=标签名
        )
        att_def.InsertionPoint = comtypes.client.CreateObject(
            "AutoCAD.APoint", (float(x_pos), float(y_pos), 0)
        )
        att_def.Height = 15.0
        att_def.Alignment = 1  # acAlignmentLeft

    # 添加母线连接点标记（左侧中部的小圆）
    center = comtypes.client.CreateObject(
        "AutoCAD.APoint", (0, 160, 0)
    )
    temp_block.AddCircle(center, 10)

    print(f"✅ 图块 '{block_name}' 已创建")

    # 导出DWG
    if export_dwg:
        dwg_path = str(BLOCKS_DIR / f"{block_name}.dwg")
        try:
            # 将图块定义写入DWG文件
            doc.Export(dwg_path.replace(".dwg", ""), "dwg",
                       temp_block)
            print(f"✅ 已导出: {dwg_path}")
        except Exception as e:
            print(f"⚠ 导出失败: {e}")

    return True


def create_all_blocks(export: bool = False):
    """创建所有标准图块

    Args:
        export: 是否导出为DWG文件
    """
    for block_name in ["进线回路", "馈线回路", "备用回路"]:
        create_block_in_autocad(block_name, export)


def show_alternative_methods():
    """显示DWG缺失时的替代方案说明"""
    print("=" * 60)
    print("DWG图块文件替代方案")
    print("=" * 60)
    print()
    print("方案1：使用本脚本通过AutoCAD COM创建标准图块")
    print("  python create_blocks.py")
    print()
    print("方案2：使用程序内置的临时图块（推荐）")
    print("  cad_driver.create_temp_block() 方法会自动在")
    print("  AutoCAD内存中创建简易图块并填充属性。")
    print("  当 blocks/*.dwg 不存在时，程序自动使用此方案。")
    print()
    print("方案3：手动创建DWG文件")
    print("  1. 在AutoCAD中新建空白图纸")
    print("  2. 定义属性(ATT DEF)：CIRCUIT_NAME, PE_POWER, ...")
    print("  3. 创建图块(BLOCK)，基准点设为左上角(0,0)")
    print("  4. 保存为 blocks/进线回路.dwg（或其他文件名）")
    print()
    print("图块规范（第4.3节）：")
    print("- 基准点统一设在左上角(0,0)")
    print("- X方向向右排列回路，间距3000单位")
    print("- 母线连接点设在图块左侧中部")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="配电系统图CAD图块创建工具"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="创建图块并导出为DWG文件"
    )
    parser.add_argument(
        "--help-blocks", action="store_true",
        help="显示DWG替代方案说明"
    )

    args = parser.parse_args()

    if args.help_blocks:
        show_alternative_methods()
    else:
        create_all_blocks(export=args.export)
