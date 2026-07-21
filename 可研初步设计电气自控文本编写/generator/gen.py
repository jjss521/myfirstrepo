# -*- coding: utf-8 -*-
"""
命令行生成工具
==============
用法：
  python generator/gen.py "负荷计算表.xlsx" --type water_supply --name "赤壁中心水厂"
  python generator/gen.py "负荷计算表.xlsx" --type drainage --stage 初步设计 --template modern
  python generator/gen.py "负荷计算表.xlsx" --summary        # 仅打印负荷汇总
"""
import os
import sys
import json
import argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'backend'))

from app.services.excel_parser import parse as parse_excel
from app.services.docx_generator import DocxGenerator, TEMPLATES

PROJECT_TYPES = ['water_supply', 'drainage', 'road', 'sanitation']
STAGES = ['初步设计', '可研']


def main():
    ap = argparse.ArgumentParser(description='市政工程设计文件电气自控生成器（命令行）')
    ap.add_argument('excel', help='负荷计算表 Excel 路径')
    ap.add_argument('--type', default='water_supply', choices=PROJECT_TYPES, help='工程类型')
    ap.add_argument('--stage', default='初步设计', choices=STAGES, help='设计阶段')
    ap.add_argument('--name', default='新建项目', help='项目名称')
    ap.add_argument('--template', default='standard', choices=list(TEMPLATES), help='Word 模板')
    ap.add_argument('--voltage', default='10kV', help='电压等级')
    ap.add_argument('--load', default='二级', help='负荷等级')
    ap.add_argument('--summary', action='store_true', help='仅打印负荷汇总，不生成文件')
    ap.add_argument('--output', default=None, help='输出目录（默认 backend/output/generated）')
    args = ap.parse_args()

    if not os.path.exists(args.excel):
        print('文件不存在：', args.excel)
        sys.exit(1)

    ed = parse_excel(args.excel)
    s = ed.get('summary', {})
    print(f'解析：{s.get("total_devices", 0)} 台设备 / {s.get("area_count", 0)} 区域 / '
          f'计算负荷 {s.get("total_sc_before", 0)} kVA')

    if args.summary:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return

    params = {
        'project_name': args.name,
        'voltage_level': args.voltage,
        'load_level': args.load,
        'project_type': args.type,
        'design_stage': args.stage,
        'power_source': '两路',
        'standby_desc': '两路电源互为备用',
    }
    gen = DocxGenerator(template=args.template)
    if args.output:
        gen.output_dir = args.output
    out = gen.generate(args.type, args.stage, ed, params)
    print('已生成：', out)


if __name__ == '__main__':
    main()
