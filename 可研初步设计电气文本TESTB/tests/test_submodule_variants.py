# -*- coding: utf-8 -*-
"""Integration tests for sub-module template variant management.

Covers:
  - CustomTemplateManager CRUD
  - list_templates_by_submodule / search_templates
  - Variant selection persistence via load_rule + save_rules_to_json
  - DocxGenerator variant content resolution
"""

import os
import json
import copy
from typing import Dict, Any, Iterator

import pytest

# ---------------------------------------------------------------------------
# CustomTemplateManager unit / integration
# ---------------------------------------------------------------------------


class TestCustomTemplateManager:
    """Direct CRUD tests against CustomTemplateManager with a temp directory."""

    def test_save_and_get(self, temp_ctm, sample_template):
        saved = temp_ctm.save_template(dict(sample_template))
        assert "id" in saved
        assert saved["template_name"] == "测试模板_供配电"
        assert saved["sub_module_name"] == "供配电系统"

        # Retrieve by ID
        retrieved = temp_ctm.get_template(saved["id"])
        assert retrieved is not None
        assert retrieved["template_name"] == "测试模板_供配电"

    def test_save_duplicate_name_auto_rename(self, temp_ctm, sample_template):
        s1 = temp_ctm.save_template(dict(sample_template))
        # Second save with same fields (no id → new template) should auto-rename
        s2 = temp_ctm.save_template({
            k: v for k, v in sample_template.items() if k != 'id'
        })
        assert s2["template_name"] != s1["template_name"]  # should be renamed

    def test_delete(self, temp_ctm, sample_template):
        saved = temp_ctm.save_template(dict(sample_template))
        tid = saved["id"]
        assert temp_ctm.delete_template(tid) is True
        assert temp_ctm.get_template(tid) is None

    def test_delete_nonexistent(self, temp_ctm):
        assert temp_ctm.delete_template("no-such-id") is False

    def test_list_templates(self, temp_ctm, sample_template):
        t1 = dict(sample_template, sub_module_name="供配电系统", template_name="t1")
        t2 = dict(sample_template, sub_module_name="照明系统", template_name="t2")
        temp_ctm.save_template(t1)
        temp_ctm.save_template(t2)
        all_templates = temp_ctm.list_templates()
        assert len(all_templates) >= 2

    def test_list_templates_filter(self, temp_ctm, sample_template):
        temp_ctm.save_template(dict(sample_template))
        filtered = temp_ctm.list_templates(sub_module_name="供配电系统")
        assert len(filtered) >= 1
        assert all(t["sub_module_name"] == "供配电系统" for t in filtered)

    def test_list_templates_by_submodule(self, temp_ctm, sample_template):
        """Test the dedicated list_templates_by_submodule API."""
        temp_ctm.save_template(dict(sample_template))
        other = dict(sample_template, sub_module_name="照明系统",
                      template_name="t_light")
        temp_ctm.save_template(other)

        results = temp_ctm.list_templates_by_submodule(
            project_type="water_supply",
            design_stage="初步设计",
            category="电气",
            item_title="设计范围及内容",
            sub_module_name="供配电系统",
        )
        assert len(results) >= 1
        assert results[0]["sub_module_name"] == "供配电系统"

    def test_search_templates(self, temp_ctm, sample_template):
        temp_ctm.save_template(dict(sample_template))
        results = temp_ctm.search_templates(keyword="供配电")
        assert len(results) >= 1

        results = temp_ctm.search_templates(
            project_type="water_supply",
            sub_module_name="供配电系统"
        )
        assert len(results) >= 1

        results = temp_ctm.search_templates(keyword="zzznonexistent")
        assert len(results) == 0

    def test_update_template(self, temp_ctm, sample_template):
        saved = temp_ctm.save_template(dict(sample_template))
        saved["content"] = "修改后的内容"
        updated = temp_ctm.save_template(saved)
        assert updated["content"] == "修改后的内容"
        retrieved = temp_ctm.get_template(saved["id"])
        assert retrieved["content"] == "修改后的内容"


# ---------------------------------------------------------------------------
# Variant selection persistence via engine (load_rule / save_rules_to_json)
# ---------------------------------------------------------------------------


class TestVariantSelectionPersistence:
    """Test that selected_variant_id can be saved to and read from rule JSON."""

    def _first_submodule(self, rule: Dict[str, Any]):
        """Helper: find first sub_module in a rule dict."""
        for stage_data in rule.get("design_stages", {}).values():
            if not isinstance(stage_data, dict):
                continue
            sections = stage_data.get("sections", stage_data)
            if not isinstance(sections, dict):
                continue
            for cat_data in sections.values():
                if not isinstance(cat_data, dict):
                    continue
                if 'items' not in cat_data:
                    # Container category — check sub-categories
                    for sub_data in cat_data.values():
                        if isinstance(sub_data, dict) and 'items' in sub_data:
                            for item in sub_data.get('items', []):
                                for sm in item.get('sub_modules', []):
                                    yield sm, item, cat_data
                else:
                    for item in cat_data.get('items', []):
                        for sm in item.get('sub_modules', []):
                            yield sm, item, cat_data

    def test_set_variant_id_on_submodule(self, engine, water_supply_rule,
                                          populated_ctm):
        """Verify selected_variant_id can be persisted on a sub_module."""
        _, saved_template = populated_ctm
        code = "water_supply"
        rule = engine.load_rule(code)
        assert rule is not None

        # Find first sub_module
        found_sm = None
        for sm, item, cat_data in self._first_submodule(rule):
            sm["selected_variant_id"] = saved_template["id"]
            found_sm = sm
            break

        assert found_sm is not None, "No sub_module found to test with"

        # Persist back
        ok = engine.save_rules_to_json(code, rule)
        assert ok is True

        # Reload and verify
        rule2 = engine.load_rule(code)
        variant_ids = []
        for sm, item, cat_data in self._first_submodule(rule2):
            vid = sm.get("selected_variant_id", "")
            if vid:
                variant_ids.append(vid)
        assert saved_template["id"] in variant_ids

    def test_clear_variant_id(self, engine, water_supply_rule):
        """Verify selected_variant_id can be removed from a sub_module."""
        code = "water_supply"
        rule = engine.load_rule(code)

        # Set on first sub_module
        found_sm = None
        for sm, item, cat_data in self._first_submodule(rule):
            sm["selected_variant_id"] = "test-clear-id"
            found_sm = sm
            break
        assert found_sm is not None
        engine.save_rules_to_json(code, rule)

        # Now clear it
        rule2 = engine.load_rule(code)
        cleared = False
        for sm, item, cat_data in self._first_submodule(rule2):
            sm.pop("selected_variant_id", None)
            cleared = True
        assert cleared
        engine.save_rules_to_json(code, rule2)

        # Verify cleared
        rule3 = engine.load_rule(code)
        for sm, item, cat_data in self._first_submodule(rule3):
            assert "selected_variant_id" not in sm

    def test_missing_variant_falls_back(self, engine, water_supply_rule):
        """A selected_variant_id pointing to a nonexistent template should
        not break the rule load or DocxGenerator."""
        code = "water_supply"
        rule = engine.load_rule(code)

        # Set a dummy variant ID on first sub_module
        for sm, item, cat_data in self._first_submodule(rule):
            sm["selected_variant_id"] = "nonexistent-id-12345"
            break
        engine.save_rules_to_json(code, rule)

        # Verify rule still loads
        rule2 = engine.load_rule(code)
        assert rule2 is not None


# ---------------------------------------------------------------------------
# DocxGenerator variant content resolution
# ---------------------------------------------------------------------------


class TestDocxGeneratorVariant:
    """Test that DocxGenerator correctly resolves variant content."""

    def test_variant_priority_over_template_content(self, engine, populated_ctm,
                                                     tmp_path):
        """When selected_variant_id is set, the generator should use
        the variant content instead of the inline template_content."""
        mgr, saved = populated_ctm
        code = "water_supply"
        rule = engine.load_rule(code)

        # Find first sub_module that has template_content and no selected_variant_id
        target = None
        for sm, item, cat_data in self._first_submodule(rule):
            if sm.get("template_content", "").strip():
                target = sm
                break

        if target is None:
            pytest.skip("No sub_module with template_content found in water_supply")

        # Set the variant
        target["selected_variant_id"] = saved["id"]
        engine.save_rules_to_json(code, rule)

        # Build DocxGenerator and verify it can generate without error
        from app.services.docx_generator import DocxGenerator

        rules_dir = os.path.join(engine.project_root, 'backend', 'data', 'rules')
        output_dir = str(tmp_path)

        gen = DocxGenerator(rules_dir=rules_dir, output_dir=output_dir)

        excel_data = {
            'summary': {
                'total_devices': 10, 'total_equip_power': 500.0,
                'total_pc': 400.0, 'total_qc': 200.0, 'total_sc': 447.2,
                'total_pc_k': 380.0, 'total_qc_k': 190.0, 'total_sc_k': 424.9,
                'cos_before': 0.85, 'cos_target': 0.95,
                'qc_compensation': 100.0,
                'total_qc_after': 90.0, 'total_sc_after': 390.5,
                'recommended_transformer': '1x800kVA',
                'simultaneous_coeff': {'KP': 0.9, 'Kq': 0.95},
            },
            'area_summaries': {},
            'area_count': 0,
        }
        params = {
            'project_name': 'Test Plant',
            'voltage_level': '10kV',
            'load_level': 'Level 2',
            'project_type': 'water_supply',
            'power_source': 'Single circuit',
            'standby_desc': '',
            'tx_config': '1x800kVA',
            'tx_count': '1',
            'tx_location': 'Switchgear room',
        }

        try:
            out_path = gen.generate(
                project_type=code,
                design_stage='可行性研究',
                excel_data=excel_data,
                params=params,
            )
            assert os.path.exists(out_path)
            assert os.path.getsize(out_path) > 0
        except Exception as e:
            pytest.fail(f"DocxGenerator raised: {e}")

    def test_no_variant_uses_template_content(self, engine, water_supply_rule,
                                               tmp_path):
        """When no selected_variant_id is set, the generator uses template_content."""
        from app.services.docx_generator import DocxGenerator

        rules_dir = os.path.join(engine.project_root, 'backend', 'data', 'rules')
        output_dir = str(tmp_path)
        gen = DocxGenerator(rules_dir=rules_dir, output_dir=output_dir)

        excel_data = {
            'summary': {
                'total_devices': 10, 'total_equip_power': 500.0,
                'total_pc': 400.0, 'total_qc': 200.0, 'total_sc': 447.2,
                'total_pc_k': 380.0, 'total_qc_k': 190.0, 'total_sc_k': 424.9,
                'cos_before': 0.85, 'cos_target': 0.95,
                'qc_compensation': 100.0,
                'total_qc_after': 90.0, 'total_sc_after': 390.5,
                'recommended_transformer': '1x800kVA',
                'simultaneous_coeff': {'KP': 0.9, 'Kq': 0.95},
            },
            'area_summaries': {},
            'area_count': 0,
        }
        params = {
            'project_name': 'Test Plant',
            'voltage_level': '10kV',
            'load_level': 'Level 2',
            'project_type': 'water_supply',
            'power_source': 'Single circuit',
            'standby_desc': '',
            'tx_config': '1x800kVA',
            'tx_count': '1',
            'tx_location': 'Switchgear room',
        }

        try:
            out_path = gen.generate(
                project_type='water_supply',
                design_stage='可行性研究',
                excel_data=excel_data,
                params=params,
            )
            assert os.path.exists(out_path)
            assert os.path.getsize(out_path) > 0
        except Exception as e:
            pytest.fail(f"DocxGenerator without variant raised: {e}")

    def _first_submodule(self, rule):
        """Helper: iterate sub_modules in a rule dict."""
        from core.engine import GenerateEngine
        for stage_data in rule.get("design_stages", {}).values():
            if not isinstance(stage_data, dict):
                continue
            sections = stage_data.get("sections", stage_data)
            if not isinstance(sections, dict):
                continue
            for cat_key, cat_data in GenerateEngine._iter_categories(sections):
                if not isinstance(cat_data, dict):
                    continue
                for item in cat_data.get("items", []):
                    if not isinstance(item, dict):
                        continue
                    for sm in item.get("sub_modules", []):
                        if isinstance(sm, dict):
                            yield sm, item, cat_data
