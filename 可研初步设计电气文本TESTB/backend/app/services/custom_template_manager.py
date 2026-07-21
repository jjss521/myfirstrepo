"""
自定义模板管理器 - 文件级 CRUD 服务

管理用户对子模块内容的编辑模板。
模板存储在 backend/data/custom_templates/ 目录中，
采用 {project_type}/{design_stage}/{category}/{item_title}/templates.json 结构存储。

特性：
  * 线程安全：每个模板文件一个 threading.Lock
  * 原子写入：先写临时文件再 os.replace，避免写入中断导致数据损坏
  * 自动创建缺失目录
  * 损坏 JSON 文件自动降级处理（记录警告，返回空列表）
  * 模板名称冲突时自动递增编号
"""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CustomTemplateManager:
    """自定义模板管理器 — 基于文件的 CRUD 服务"""

    # 线程安全的文件级锁 — 每个文件路径对应一个 Lock
    _locks: Dict[str, threading.Lock] = {}
    _locks_lock: threading.Lock = threading.Lock()

    def __init__(self, data_dir: Optional[str] = None):
        """初始化模板管理器。

        Args:
            data_dir: 模板存储根目录。默认值为 backend/data/custom_templates/
        """
        if data_dir is None:
            # 默认路径：相对于此文件，回到 backend/data/custom_templates/
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data', 'custom_templates',
            )
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    # ── 内部辅助方法 ──────────────────────────────────────────────────

    @classmethod
    def _get_file_lock(cls, filepath: str) -> threading.Lock:
        """获取或创建指定文件路径的线程锁。"""
        with cls._locks_lock:
            if filepath not in cls._locks:
                cls._locks[filepath] = threading.Lock()
            return cls._locks[filepath]

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """清理文件名，将空格和特殊字符替换为下划线。"""
        name = re.sub(r'[\\/:*?"<>|#%&\s]+', '_', name)
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')
        return name or 'unnamed'

    @staticmethod
    def _generate_id() -> str:
        """生成唯一模板 ID。"""
        return str(uuid.uuid4())

    @staticmethod
    def _now_iso() -> str:
        """获取当前 ISO 格式时间戳。"""
        return datetime.now().isoformat()

    def _get_item_dir(self, project_type: str, design_stage: str,
                      category: str, item_title: str) -> str:
        """获取指定 item 的存储目录路径。"""
        safe_stage = self._sanitize_filename(design_stage)
        safe_category = self._sanitize_filename(category)
        safe_item = self._sanitize_filename(item_title)
        return os.path.join(
            self.data_dir, project_type, safe_stage, safe_category, safe_item,
        )

    def _get_item_file(self, project_type: str, design_stage: str,
                       category: str, item_title: str) -> str:
        """获取指定 item 的 templates.json 文件路径。"""
        return os.path.join(
            self._get_item_dir(project_type, design_stage, category, item_title),
            'templates.json',
        )

    def _load_templates_from_file(self, filepath: str) -> List[dict]:
        """从 JSON 文件加载模板列表；损坏文件返回空列表。"""
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            logger.warning("模板文件格式不正确（期望 list 类型）: %s", filepath)
            return []
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.warning("无法读取模板文件 %s: %s", filepath, e)
            return []

    def _save_templates_to_file(self, filepath: str, templates: List[dict]) -> None:
        """原子写入模板列表（先写临时文件再 rename）。"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        dir_name = os.path.dirname(filepath)
        fd, tmp_path = tempfile.mkstemp(
            suffix='.json', prefix='templates_', dir=dir_name,
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            # Windows 上 os.replace 可跨驱动器原子替换
            os.replace(tmp_path, filepath)
        except Exception:
            # 写入失败时清理临时文件
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    def _iter_all_template_files(self) -> List[str]:
        """遍历所有 templates.json 文件路径。"""
        result = []
        if not os.path.isdir(self.data_dir):
            return result
        for root, _dirs, files in os.walk(self.data_dir):
            if 'templates.json' in files:
                result.append(os.path.join(root, 'templates.json'))
        return result

    @staticmethod
    def _match_filter(template: dict,
                      project_type: Optional[str] = None,
                      design_stage: Optional[str] = None,
                      category: Optional[str] = None,
                      item_title: Optional[str] = None,
                      sub_module_name: Optional[str] = None) -> bool:
        """检查模板是否匹配所有过滤条件。"""
        if project_type is not None and template.get('project_type') != project_type:
            return False
        if design_stage is not None and template.get('design_stage') != design_stage:
            return False
        if category is not None and template.get('category') != category:
            return False
        if item_title is not None and template.get('item_title') != item_title:
            return False
        if sub_module_name is not None:
            if template.get('sub_module_name', '') != sub_module_name:
                return False
        return True

    # ── 公共 API ──────────────────────────────────────────────────────

    def list_templates(self,
                       project_type: Optional[str] = None,
                       design_stage: Optional[str] = None,
                       category: Optional[str] = None,
                       item_title: Optional[str] = None,
                       sub_module_name: Optional[str] = None) -> List[dict]:
        """列出模板，支持可选过滤条件。

        Args:
            project_type: 工程类型（如 "water_supply"）。
            design_stage: 设计阶段（如 "可行性研究"、"初步设计"）。
            category: 分类（"电气" 或 "自控"）。
            item_title: 条目标题（如 "设计范围及依据"）。
            sub_module_name: 子模块名称，可选过滤。

        Returns:
            模板记录列表。
        """
        results: List[dict] = []

        # 如果提供了完整的定位路径，只加载单个文件
        if project_type and design_stage and category and item_title:
            filepath = self._get_item_file(project_type, design_stage, category, item_title)
            templates = self._load_templates_from_file(filepath)
            for tmpl in templates:
                if self._match_filter(tmpl, project_type, design_stage,
                                      category, item_title, sub_module_name):
                    results.append(tmpl)
        else:
            # 无完整路径时遍历所有文件
            for filepath in self._iter_all_template_files():
                templates = self._load_templates_from_file(filepath)
                for tmpl in templates:
                    if self._match_filter(tmpl, project_type, design_stage,
                                          category, item_title, sub_module_name):
                        results.append(tmpl)

        return results

    def save_template(self, template: dict) -> dict:
        """保存模板。缺少 ID 则生成，缺少时间戳则补全。返回完整模板记录。

        Args:
            template: 模板字典，必含 project_type, design_stage, category,
                      item_title, template_name, content。

        Returns:
            已保存的完整模板记录。

        Raises:
            ValueError: 缺少必填字段时抛出。
        """
        if not isinstance(template, dict):
            raise ValueError("template 必须为 dict 类型")

        # 校验必填字段
        required = ['project_type', 'design_stage', 'category',
                    'item_title', 'template_name', 'content']
        for field in ['project_type', 'design_stage', 'category',
                      'item_title', 'template_name']:
            if not template.get(field):
                raise ValueError(
                    f"缺少必填字段: {field}"
                )

        # 记录空内容警告（但不阻止保存）
        content = template.get('content', '')
        if isinstance(content, str) and not content.strip():
            logger.warning(
                "模板 '%s' 的内容为空",
                template.get('template_name', 'unknown'),
            )

        # 生成 ID
        if not template.get('id'):
            template['id'] = self._generate_id()

        # 设置时间戳
        now = self._now_iso()
        if not template.get('created_at'):
            template['created_at'] = now
        template['updated_at'] = now

        # 补全可选字段
        template.setdefault('is_rich_text', False)
        template.setdefault('sub_module_name', '')
        template.setdefault('source_doc', '')
        template.setdefault('tags', [])

        filepath = self._get_item_file(
            template['project_type'], template['design_stage'],
            template['category'], template['item_title'],
        )

        lock = self._get_file_lock(filepath)
        with lock:
            templates = self._load_templates_from_file(filepath)

            # 名称冲突检测：同名不同 ID 时自动追加编号
            same_name = [
                t for t in templates
                if t.get('template_name') == template['template_name']
                and t.get('id') != template['id']
            ]
            if same_name:
                base_name = template['template_name']
                counter = len(same_name) + 1
                template['template_name'] = f"{base_name} ({counter})"

            # 更新已有记录或追加新记录
            existing_idx = None
            for i, t in enumerate(templates):
                if t.get('id') == template['id']:
                    existing_idx = i
                    break

            if existing_idx is not None:
                templates[existing_idx] = template
            else:
                templates.append(template)

            self._save_templates_to_file(filepath, templates)

        return dict(template)

    def get_template(self, template_id: str) -> Optional[dict]:
        """根据 ID 获取单个模板。

        Args:
            template_id: 模板唯一标识。

        Returns:
            模板记录或 None。
        """
        if not template_id:
            return None

        for filepath in self._iter_all_template_files():
            templates = self._load_templates_from_file(filepath)
            for tmpl in templates:
                if tmpl.get('id') == template_id:
                    return dict(tmpl)

        return None

    def delete_template(self, template_id: str) -> bool:
        """删除指定 ID 的模板。

        Args:
            template_id: 模板唯一标识。

        Returns:
            True 表示已成功删除，False 表示未找到。
        """
        if not template_id:
            return False

        for filepath in self._iter_all_template_files():
            lock = self._get_file_lock(filepath)
            with lock:
                templates = self._load_templates_from_file(filepath)
                for i, tmpl in enumerate(templates):
                    if tmpl.get('id') == template_id:
                        deleted = templates.pop(i)
                        self._save_templates_to_file(filepath, templates)
                        logger.info(
                            "已删除模板: %s (%s)",
                            deleted.get('template_name', ''), template_id,
                        )
                        return True

        return False

    def get_templates_for_item(self, project_type: str, design_stage: str,
                               category: str, item_title: str) -> List[dict]:
        """获取指定 item 的所有模板（常见查询的快捷方法）。

        Args:
            project_type: 工程类型。
            design_stage: 设计阶段。
            category: 分类。
            item_title: 条目标题。

        Returns:
            该 item 的模板列表。
        """
        return self.list_templates(
            project_type=project_type,
            design_stage=design_stage,
            category=category,
            item_title=item_title,
        )

    def list_templates_by_submodule(self, project_type: str, design_stage: str,
                                    category: str, item_title: str,
                                    sub_module_name: str) -> List[dict]:
        """List all templates matching a specific sub-module context.

        Args:
            project_type, design_stage, category, item_title: locate the item's template file
            sub_module_name: filter by sub-module name

        Returns:
            List of matching template records, ordered by updated_at desc.
        """
        filepath = self._get_item_file(project_type, design_stage, category, item_title)
        templates = self._load_templates_from_file(filepath)
        results = []
        for tmpl in templates:
            if tmpl.get('sub_module_name', '') == sub_module_name:
                results.append(tmpl)
        results.sort(key=lambda t: t.get('updated_at', ''), reverse=True)
        return results

    def search_templates(self, project_type: Optional[str] = None,
                         sub_module_name: Optional[str] = None,
                         keyword: Optional[str] = None) -> List[dict]:
        """Search templates across all files with flexible filters.
        Useful for the template library browsing page.

        Args:
            project_type: filter by project type (optional)
            sub_module_name: filter by sub-module name (optional)
            keyword: search in template_name and content text (optional)

        Returns:
            List of matching template records.
        """
        results = []
        for filepath in self._iter_all_template_files():
            templates = self._load_templates_from_file(filepath)
            for tmpl in templates:
                if project_type and tmpl.get('project_type') != project_type:
                    continue
                if sub_module_name and tmpl.get('sub_module_name', '') != sub_module_name:
                    continue
                if keyword:
                    kw = keyword.lower()
                    name = tmpl.get('template_name', '').lower()
                    content = tmpl.get('content', '').lower()
                    if kw not in name and kw not in content:
                        continue
                results.append(tmpl)
        return results
