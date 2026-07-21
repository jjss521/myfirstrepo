# -*- coding: utf-8 -*-
"""
将 backend/data/rules/*.json 中的规范深度要求灌入 SQLite（幂等）。
运行：python backend/seed_data.py
"""
import os
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)  # backend 目录

from app.database import init_db, SessionLocal
from app.models import ProjectType, Section


def seed():
    init_db()
    db = SessionLocal()
    rules_dir = os.path.join(_HERE, 'data', 'rules')
    count_pt = 0
    count_sec = 0
    for fn in sorted(os.listdir(rules_dir)):
        if not fn.endswith('.json'):
            continue
        with open(os.path.join(rules_dir, fn), encoding='utf-8') as f:
            rule = json.load(f)
        code = fn[:-5]  # water_supply_preliminary
        pt = db.query(ProjectType).filter_by(code=code).first()
        if not pt:
            pt = ProjectType(code=code, name=rule.get('project_type', ''),
                             design_stage=rule.get('design_stage', ''),
                             description=rule.get('regulation_ref', ''))
            db.add(pt)
            db.flush()
            count_pt += 1
        else:
            pt.name = rule.get('project_type', pt.name)
            pt.design_stage = rule.get('design_stage', pt.design_stage)
        # 清空旧栏目后重写
        db.query(Section).filter_by(project_type_id=pt.id).delete()
        for cat, items in rule.get('categories', {}).items():
            for it in items:
                db.add(Section(
                    project_type_id=pt.id,
                    category=cat,
                    section_order=it.get('order', 0),
                    title=it.get('title', ''),
                    depth_requirement=it.get('requirement', ''),
                    has_calculation=it.get('has_calculation', False),
                    table_required=it.get('table_required', False),
                    calc_from_excel=it.get('calc_from_excel', False),
                    optional=it.get('optional', False),
                ))
                count_sec += 1
    db.commit()
    db.close()
    print(f'Seed 完成：project_types={count_pt}（新增/更新），sections={count_sec}')


if __name__ == '__main__':
    seed()
