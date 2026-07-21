# -*- coding: utf-8 -*-
"""Shared fixtures for sub-module variant integration tests."""

import os
import sys
import tempfile
import json
from typing import Dict, Any, Iterator

import pytest

# Ensure project backend and src are importable
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJ, 'backend'))
sys.path.insert(0, os.path.join(PROJ, 'src'))


@pytest.fixture
def temp_ctm():
    """Create a CustomTemplateManager backed by a temporary directory."""
    from app.services.custom_template_manager import CustomTemplateManager
    tmpdir = tempfile.mkdtemp(prefix='ctm_test_')
    mgr = CustomTemplateManager(data_dir=tmpdir)
    yield mgr
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_template() -> Dict[str, Any]:
    """Return a minimal template dict for saving."""
    return {
        "project_type": "water_supply",
        "design_stage": "初步设计",
        "category": "电气",
        "item_title": "设计范围及内容",
        "sub_module_name": "供配电系统",
        "template_name": "测试模板_供配电",
        "content": "测试内容：供配电系统设计范围。",
        "is_rich_text": True,
    }


@pytest.fixture
def populated_ctm(temp_ctm, sample_template) -> Iterator:
    """CTM fixture with one pre-saved template."""
    saved = temp_ctm.save_template(sample_template)
    yield temp_ctm, saved


@pytest.fixture
def engine():
    """Return a GenerateEngine instance pointing at the real project data."""
    from core.engine import GenerateEngine
    eng = GenerateEngine(project_root=PROJ)
    return eng


@pytest.fixture
def water_supply_rule(engine) -> Dict[str, Any]:
    """Load the water_supply rule JSON."""
    rule = engine.load_rule('water_supply')
    assert rule is not None, "water_supply.json must exist"
    return rule
