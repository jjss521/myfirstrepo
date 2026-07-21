"""
核心引擎 - 协调 Excel解析器、知识规则、Word生成器

整合 backend/app/services/excel_parser.py 和 docx_generator.py
"""
import os
import sys
import json
import traceback
from typing import Optional, Dict, Any

# 将 backend 添加到 sys.path
_BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend')
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

try:
    from app.services.excel_parser import ExcelLoadParser
except ImportError as e:
    ExcelLoadParser = None
    _import_error = str(e)

try:
    from app.services.docx_generator import DocxGenerator
except ImportError as e:
    DocxGenerator = None
    _docx_import_error = str(e)


class GenerateEngine:
    """文档生成引擎 - 统一入口"""

    PROJECT_TYPES = {
        'water_supply': {'label': '给水工程', 'icon': '💧'},
        'drainage':     {'label': '排水工程', 'icon': '🌊'},
        'road':         {'label': '道路工程', 'icon': '🛣️'},
        'sanitation':   {'label': '环卫工程', 'icon': '♻️'},
    }

    DESIGN_STAGES = ['可行性研究', '初步设计']

    # Numbering constants — stage name → numeric key
    STAGE_NUM_MAP = {'可行性研究': 1, '初步设计': 2}

    # Default numbering config written when no config file exists
    DEFAULT_NUMBERING_CONFIG = {
        'enabled': True,
        'show_in_tree': True,
        'format': 'decimal',
        'updated_at': '2026-07-14T00:00:00',
    }

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.dirname(os.path.dirname(_BACKEND_DIR))
        self.rules_dir = os.path.join(self.project_root, 'backend', 'data', 'rules')
        self.output_dir = os.path.join(self.project_root, 'output')
        self.numbering_config_path = os.path.join(
            self.project_root, 'backend', 'data', 'numbering_config.json')

        os.makedirs(self.output_dir, exist_ok=True)

        self._rules_cache = {}
        self._excel_parser = None
        self._docx_generator = None
        self._template_manager = None
        self._numbering_config = None  # lazy-loaded on first access

    # ── 规则文件操作 ──

    @staticmethod
    def _iter_categories(categories: dict):
        """迭代分类数据，处理标准分类（含items）和容器分类（含子分类）两种结构
        
        road.json 的"初步设计→自控"是容器，内含"交通管理设施"、"智慧枢纽智能系统"等子分类。
        """
        for key, data in categories.items():
            if not isinstance(data, dict):
                continue
            if 'items' in data:
                yield key, data
            else:
                # 容器分类 - 迭代子分类
                for sub_key, sub_data in data.items():
                    if isinstance(sub_data, dict) and 'items' in sub_data:
                        yield sub_key, sub_data

    def list_rules(self) -> list:
        """列出所有可用的规则文件"""
        results = []
        for code, info in self.PROJECT_TYPES.items():
            path = os.path.join(self.rules_dir, f'{code}.json')
            if os.path.exists(path):
                results.append({
                    'code': code,
                    'label': info['label'],
                    'path': path,
                    'loaded': code in self._rules_cache,
                })
        return results

    def load_rule(self, project_type: str) -> Optional[Dict[str, Any]]:
        """加载单个工程类型的规则"""
        if project_type in self._rules_cache:
            return self._rules_cache[project_type]

        path = os.path.join(self.rules_dir, f'{project_type}.json')
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._rules_cache[project_type] = data
        return data

    def save_rules_to_json(self, project_type: str, rule_data: dict) -> bool:
        """保存规则数据到JSON文件"""
        path = os.path.join(self.rules_dir, f'{project_type}.json')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(rule_data, f, ensure_ascii=False, indent=2)
            # 清除缓存，下次重新加载
            self._rules_cache.pop(project_type, None)
            return True
        except Exception:
            traceback.print_exc()
            return False

    def get_rule_summary(self, project_type: str) -> Dict[str, Any]:
        """获取规则的摘要信息（不含完整 items，用于快速展示）"""
        rule = self.load_rule(project_type)
        if not rule:
            return {}
        summary = {
            'project_type': rule.get('project_type', ''),
            'regulation_ref': rule.get('regulation_ref', ''),
            'categories': [],
        }
        for stage_name, stage_data in rule.get('design_stages', {}).items():
            # 环卫工程(sanitation)使用嵌套 sections 结构，其他工程直接在阶段下
            categories = stage_data.get('sections', stage_data) if isinstance(stage_data, dict) else {}
            for cat_key, cat_data in self._iter_categories(categories):
                items = cat_data.get('items', [])
                summary['categories'].append({
                    'key': cat_key,
                    'stage': stage_name,
                    'title': cat_data.get('title', ''),
                    'section_id': cat_data.get('section_id', ''),
                    'item_count': len(items),
                    'has_calculation': any(it.get('has_calculation') for it in items),
                    'required_items': [it['title'] for it in items if not it.get('optional')],
                })
        return summary

    # ── 编号配置 ──────────────────────────────────────────────────────────

    def _load_numbering_config(self) -> dict:
        """Load numbering config from JSON file. Returns defaults if file missing/invalid."""
        if not os.path.exists(self.numbering_config_path):
            return dict(self.DEFAULT_NUMBERING_CONFIG)
        try:
            with open(self.numbering_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            traceback.print_exc()
            return dict(self.DEFAULT_NUMBERING_CONFIG)

    def get_numbering_config(self) -> Dict[str, Any]:
        """Return the current numbering configuration dict (lazy-loads from file)."""
        if self._numbering_config is None:
            self._numbering_config = self._load_numbering_config()
        return self._numbering_config

    def set_numbering_config(self, config_dict: Dict[str, Any]) -> bool:
        """Save numbering configuration to JSON file. Returns True on success."""
        try:
            os.makedirs(os.path.dirname(self.numbering_config_path), exist_ok=True)
            with open(self.numbering_config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            self._numbering_config = config_dict
            return True
        except Exception:
            traceback.print_exc()
            return False

    def get_numbered_title(self, stage_name: str, cat_order: int,
                           item_order: int, title: str) -> str:
        """Return a hierarchically-numbered display title.

        Args:
            stage_name: Design stage name ("可行性研究" or "初步设计").
            cat_order:  1-based category order within the stage.
            item_order: 1-based item order (``item.order`` in JSON).
            title:      Clean item title (without number prefix).

        Returns:
            ``"1.1.1 标题内容"`` when numbering is enabled, otherwise the raw title.
            For intermediate levels (cat_order or item_order == 0) a shorter
            prefix is produced: ``"1 可行性研究"`` or ``"1.1 电气设计"``.
        """
        if not self.get_numbering_config().get('enabled', True):
            return title

        stage_num = self.STAGE_NUM_MAP.get(stage_name, 0)
        if stage_num == 0:
            return title

        if cat_order <= 0:
            # Stage-only level: "1 可行性研究"
            return f'{stage_num} {title}'
        if item_order <= 0:
            # Category level: "1.1 电气设计"
            return f'{stage_num}.{cat_order} {title}'
        # Item level: "1.1.1 设计范围及内容"
        return f'{stage_num}.{cat_order}.{item_order} {title}'

    # ── Excel 操作 ──

    def parse_excel(self, excel_path: str) -> Dict[str, Any]:
        """解析负荷计算Excel"""
        if ExcelLoadParser is None:
            raise RuntimeError(f'ExcelLoadParser 导入失败: {_import_error}')
        if self._excel_parser is None:
            self._excel_parser = ExcelLoadParser()
        return self._excel_parser.parse(excel_path)

    # ── Word 生成 ──

    def generate(
        self,
        project_type: str,
        design_stage: str,
        excel_data: Dict[str, Any],
        params: Dict[str, Any],
    ) -> str:
        """生成Word文档"""
        if DocxGenerator is None:
            raise RuntimeError(f'DocxGenerator 导入失败: {_docx_import_error}')
        if self._docx_generator is None:
            self._docx_generator = DocxGenerator(
                rules_dir=self.rules_dir,
                output_dir=self.output_dir,
            )
        return self._docx_generator.generate(project_type, design_stage, excel_data, params)

    # ── 健康检查 ──

    def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        checks = []

        # rules
        rules_ok = all(
            os.path.exists(os.path.join(self.rules_dir, f'{code}.json'))
            for code in self.PROJECT_TYPES
        )
        checks.append(('规则文件', '[OK]' if rules_ok else '[FAIL]'))

        # excel parser
        excel_ok = ExcelLoadParser is not None
        checks.append(('Excel解析器', '[OK]' if excel_ok else f'[FAIL] {_import_error}'))

        # docx generator
        docx_ok = DocxGenerator is not None
        checks.append(('Word生成器', '[OK]' if docx_ok else f'[FAIL] {_docx_import_error}'))

        # python-docx
        try:
            from docx import Document
            _ = Document()
            checks.append(('python-docx', '[OK]'))
        except Exception as e:
            checks.append(('python-docx', f'[FAIL] {e}'))

        # output dir
        checks.append(('输出目录', '[OK]' if os.path.isdir(self.output_dir) else '[FAIL]'))

        return {'all_pass': all('[OK]' in msg for _, msg in checks), 'checks': checks}

    # ── 自定义模板管理 ──

    @property
    def template_manager(self):
        """懒加载自定义模板管理器实例。"""
        if self._template_manager is None:
            from app.services.custom_template_manager import CustomTemplateManager
            self._template_manager = CustomTemplateManager(
                os.path.join(self.project_root, 'backend', 'data', 'custom_templates')
            )
        return self._template_manager

    def list_custom_templates(self, **filters) -> list:
        """列出自定义模板，支持与 list_templates() 相同的过滤参数。"""
        return self.template_manager.list_templates(**filters)

    def save_custom_template(self, template: dict) -> dict:
        """保存一个自定义模板，返回完整模板记录。"""
        return self.template_manager.save_template(template)

    def delete_custom_template(self, template_id: str) -> bool:
        """删除指定 ID 的自定义模板，返回是否删除成功。"""
        return self.template_manager.delete_template(template_id)
