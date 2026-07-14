#!/usr/bin/env python
"""
市政工程设计文件电气自控生成器 — 命令行版

使用方法:
    python gen.py 负荷计算表.xlsx --type water_supply --name "XX水厂" --stage 初步设计

示例:
    python gen.py "D:/00-水厂负荷计算表.xlsx" --type water_supply --name "赤壁中心水厂"
    python gen.py "F:/负荷表.xls" --type drainage --name "XX污水厂" --stage 可研
"""
import argparse
import sys
import os
import json
from datetime import datetime

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app.services.excel_parser import ExcelLoadParser
from app.services.docx_generator import DocxGenerator
from app.config import RULES_DIR, OUTPUT_DIR, PROJECT_TYPES

os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description='市政工程设计文件电气自控说明生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('excel', help='负荷计算Excel文件路径 (.xlsx或.xls)')
    parser.add_argument('--type', '-t', required=True,
                        choices=['water_supply', 'drainage', 'road', 'sanitation'],
                        help='工程类型')
    parser.add_argument('--name', '-n', default='新建项目', help='项目名称')
    parser.add_argument('--stage', '-s', default='初步设计',
                        choices=['可研', '初步设计', '施工图'], help='设计阶段')
    parser.add_argument('--voltage', '-v', default='10kV', help='供电电压等级')
    parser.add_argument('--load-level', '-l', default='二级', help='负荷等级')
    parser.add_argument('--summary', action='store_true', help='仅打印负荷汇总（不生成文档）')
    parser.add_argument('--output-dir', '-o', default=None, help='输出目录')

    args = parser.parse_args()

    if not os.path.exists(args.excel):
        print(f'❌ 文件不存在: {args.excel}')
        sys.exit(1)

    print(f'=' * 60)
    print(f'市政工程设计文件电气自控说明生成器')
    print(f'=' * 60)
    print(f'输入文件: {args.excel}')
    print(f'工程类型: {PROJECT_TYPES.get(args.type, args.type)}')
    print(f'设计阶段: {args.stage}')
    print(f'项目名称: {args.name}')
    print()

    # 1. 解析Excel
    print('📊 正在解析负荷计算表...')
    excel_parser = ExcelLoadParser()
    excel_data = excel_parser.parse(args.excel)

    summary = excel_data['summary']
    print(f'  设备总数: {summary["total_devices"]} 台')
    print(f'  安装容量: {summary["total_equip_power"]:.1f} kW')
    print(f'  计算负荷: {summary["total_sc_k"]:.1f} kVA')
    print(f'  补偿前功率因数: {summary["cos_before"]}')
    print(f'  需补偿: {summary["qc_compensation"]:.1f} kvar')
    print(f'  推荐变压器: {summary["recommended_transformer"]}')
    print()

    if args.summary:
        print('📋 各区域负荷汇总:')
        for area_name, data in excel_data['area_summaries'].items():
            print(f'  {area_name}: {data["device_count"]}台, '
                  f'设备功率{data["equip_power"]:.1f}kW, '
                  f'计算负荷{data["sc"]:.1f}kVA')
        return

    # 2. 生成文档
    print('📝 正在生成设计文件...')
    output_dir = args.output_dir or OUTPUT_DIR
    gen = DocxGenerator(rules_dir=RULES_DIR, output_dir=output_dir)

    params = {
        'project_name': args.name,
        'voltage_level': args.voltage,
        'load_level': args.load_level,
        'project_type': args.type,
    }
    output_path = gen.generate(args.type, args.stage, excel_data, params)

    # 3. 结果
    file_size = os.path.getsize(output_path)
    print(f'\n✅ 生成完成！')
    print(f'   文件: {output_path}')
    print(f'   大小: {file_size:,} 字节')
    print(f'\n💡 提示: 当前生成为TXT预览版，Word正式版敬请期待。')


if __name__ == '__main__':
    main()
