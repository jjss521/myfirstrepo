"""数据库种子数据 - 导入规范深度要求"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, init_db
from app.models import Base, ProjectType, Section


def seed_rules():
    """从JSON文件导入规范深度要求到数据库"""
    rules_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'rules')

    init_db()
    db = SessionLocal()

    try:
        existing = db.query(ProjectType).count()
        if existing > 0:
            print(f'数据库已有 {existing} 条工程类型记录，跳过种子导入。')
            return

        for code in ['water_supply', 'drainage', 'road', 'sanitation']:
            filepath = os.path.join(rules_dir, f'{code}.json')
            if not os.path.exists(filepath):
                print(f'  [跳过] 文件不存在: {filepath}')
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                rule = json.load(f)

            # 按设计阶段分别创建工程类型
            for stage_name, stage_data in rule.get('design_stages', {}).items():
                stage_code = 'feasibility' if '可行' in stage_name else 'preliminary'
                pt = ProjectType(
                    code=f'{code}_{stage_code}',
                    name=f'{rule["project_type"]}',
                    design_stage=stage_name,
                    description=rule.get('regulation_ref', ''),
                )
                db.add(pt)
                db.flush()  # 获取id

                # 环卫工程(sanitation)使用嵌套 sections 结构
                categories = stage_data.get('sections', stage_data) if isinstance(stage_data, dict) else {}
                total_items = 0
                def _iter_cats(cats):
                    for k, v in cats.items():
                        if not isinstance(v, dict): continue
                        if 'items' in v: yield k, v
                        else:
                            for sk, sv in v.items():
                                if isinstance(sv, dict) and 'items' in sv: yield sk, sv
                for category_name, category_data in _iter_cats(categories):
                    for item in category_data.get('items', []):
                        section = Section(
                            project_type_id=pt.id,
                            category=category_name,
                            section_order=item['order'],
                            title=item['title'],
                            depth_requirement=item.get('requirement', ''),
                            has_calculation=item.get('has_calculation', False),
                            table_required=item.get('table_required', False),
                            calc_from_excel=item.get('calc_from_excel', False),
                            is_required=True,
                            optional=item.get('optional', False),
                        )
                        db.add(section)
                        total_items += 1

                cat_count = len(categories)
                print(f'  [✓] {rule["project_type"]} ({stage_name}) - {cat_count}类{total_items}个栏目')

        db.commit()
        print(f'\n种子数据导入完成！')

        # 验证
        total = db.query(ProjectType).count()
        sections = db.query(Section).count()
        print(f'工程类型: {total}, 栏目总数: {sections}')

    except Exception as e:
        db.rollback()
        print(f'导入失败: {e}')
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_rules()
