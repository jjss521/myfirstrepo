"""模型层测试：StandardRef, ValidatedStandard, StandardStatus 等"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from models import (
    MergedTextLine,
    OcrTextRegion,
    ReplacementInfo,
    SearchResult,
    StandardRef,
    StandardStatus,
    ValidatedStandard,
)


class TestStandardStatus:
    """StandardStatus 枚举值测试"""

    def test_values(self):
        assert StandardStatus.ACTIVE.value == "现行"
        assert StandardStatus.ABOLISHED.value == "作废"
        assert StandardStatus.REPEALED.value == "废止"
        assert StandardStatus.UPCOMING.value == "即将实施"
        assert StandardStatus.UNKNOWN.value == "未知"

    def test_membership(self):
        assert StandardStatus("现行") is StandardStatus.ACTIVE
        assert StandardStatus("作废") is StandardStatus.ABOLISHED


class TestStandardRef:
    """StandardRef 冻结数据类测试"""

    def test_create_with_all_fields(self):
        ref = StandardRef(
            number="GB 50016-2014",
            name="建筑设计防火规范",
            source_files=["img1.png", "img2.png"],
            confidence=0.95,
            raw_text="GB 50016-2014 建筑设计防火规范",
        )
        assert ref.number == "GB 50016-2014"
        assert ref.name == "建筑设计防火规范"
        assert ref.source_files == ["img1.png", "img2.png"]
        assert ref.confidence == 0.95
        assert ref.raw_text == "GB 50016-2014 建筑设计防火规范"

    def test_create_with_defaults(self):
        ref = StandardRef(number="GB/T 50352-2019", name="")
        assert ref.number == "GB/T 50352-2019"
        assert ref.name == ""
        assert ref.source_files == []
        assert ref.confidence == 0.0
        assert ref.raw_text == ""

    def test_frozen_immutability(self):
        ref = StandardRef(
            number="JGJ 3-2010",
            name="高层建筑混凝土结构技术规程",
        )
        with pytest.raises(FrozenInstanceError):
            ref.number = "GB 50016-2014"
        with pytest.raises(FrozenInstanceError):
            ref.name = "其他名称"
        with pytest.raises(FrozenInstanceError):
            ref.source_files = ["new.png"]
        with pytest.raises(FrozenInstanceError):
            ref.confidence = 0.5
        with pytest.raises(FrozenInstanceError):
            ref.raw_text = "其他文本"

    def test_repr(self):
        ref = StandardRef(number="GB 50016-2014", name="建筑设计防火规范")
        r = repr(ref)
        assert "StandardRef" in r
        assert "GB 50016-2014" in r
        assert "建筑设计防火规范" in r

    def test_equality(self):
        """frozen dataclass 默认按字段值判等"""
        a = StandardRef(number="GB 50016-2014", name="建筑设计防火规范")
        b = StandardRef(number="GB 50016-2014", name="建筑设计防火规范")
        assert a == b
        c = StandardRef(number="GB 50016-2014", name="其他名称")
        assert a != c


class TestOcrTextRegion:
    """OcrTextRegion 冻结数据类测试"""

    def test_create(self):
        region = OcrTextRegion(
            bbox=[[10, 20], [30, 20], [30, 40], [10, 40]],
            text="GB 50016-2014",
            confidence=0.85,
        )
        assert region.text == "GB 50016-2014"
        assert region.confidence == 0.85
        assert len(region.bbox) == 4

    def test_frozen(self):
        region = OcrTextRegion(
            bbox=[[0, 0], [1, 0], [1, 1], [0, 1]],
            text="test",
            confidence=0.5,
        )
        with pytest.raises(FrozenInstanceError):
            region.text = "changed"


class TestMergedTextLine:
    """MergedTextLine 冻结数据类测试"""

    def test_create(self):
        line = MergedTextLine(
            text="GB 50016-2014 建筑设计防火规范",
            confidence=0.9,
            y_center=120.5,
        )
        assert line.text == "GB 50016-2014 建筑设计防火规范"
        assert line.confidence == 0.9
        assert line.y_center == 120.5

    def test_frozen(self):
        line = MergedTextLine(text="test", confidence=0.5, y_center=100.0)
        with pytest.raises(FrozenInstanceError):
            line.y_center = 200.0


class TestSearchResult:
    """SearchResult 冻结数据类测试"""

    def test_create_with_all_fields(self):
        ref = StandardRef(number="GB 50016-2014", name="建筑设计防火规范")
        result = SearchResult(
            standard_ref=ref,
            status=StandardStatus.ACTIVE,
            csres_number="GB 50016-2014",
            csres_name="建筑设计防火规范",
            detail_url="http://www.csres.com/detail/123.html",
            department="住房和城乡建设部",
            effective_date="2015-05-01",
        )
        assert result.standard_ref is ref
        assert result.status is StandardStatus.ACTIVE
        assert result.detail_url == "http://www.csres.com/detail/123.html"
        assert result.department == "住房和城乡建设部"
        assert result.effective_date == "2015-05-01"


class TestReplacementInfo:
    """ReplacementInfo 冻结数据类测试"""

    def test_create(self):
        info = ReplacementInfo(
            old_number="GB 50016-2006",
            old_name="建筑设计防火规范（2006版）",
            replacement_number="GB 50016-2014",
            replacement_name="建筑设计防火规范",
            abolished_date="2015-05-01",
            replacement_notes="代替 GB 50016-2006",
        )
        assert info.old_number == "GB 50016-2006"
        assert info.replacement_number == "GB 50016-2014"
        assert info.replacement_notes == "代替 GB 50016-2006"


class TestValidatedStandard:
    """ValidatedStandard 冻结数据类测试"""

    def test_create_with_search_result(self):
        ref = StandardRef(number="GB 50016-2014", name="建筑设计防火规范")
        sr = SearchResult(
            standard_ref=ref,
            status=StandardStatus.ACTIVE,
            csres_number="GB 50016-2014",
            csres_name="建筑设计防火规范",
            detail_url="http://www.csres.com/detail/123.html",
        )
        vs = ValidatedStandard(standard_ref=ref, search_result=sr)
        assert vs.standard_ref is ref
        assert vs.search_result is sr
        assert vs.replacement_info is None

    def test_create_with_search_result_none(self):
        ref = StandardRef(number="GB 50016-2014", name="建筑设计防火规范")
        vs = ValidatedStandard(standard_ref=ref, search_result=None)
        assert vs.standard_ref is ref
        assert vs.search_result is None
        assert vs.replacement_info is None

    def test_create_with_all_optionals(self):
        ref = StandardRef(number="GB 50016-2014", name="建筑设计防火规范")
        sr = SearchResult(
            standard_ref=ref,
            status=StandardStatus.ACTIVE,
            csres_number="GB 50016-2014",
            csres_name="建筑设计防火规范",
            detail_url="http://www.csres.com/detail/123.html",
        )
        ri = ReplacementInfo(
            old_number="GB 50016-2006",
            old_name="建筑设计防火规范（2006版）",
        )
        vs = ValidatedStandard(standard_ref=ref, search_result=sr, replacement_info=ri)
        assert vs.search_result is sr
        assert vs.replacement_info is ri
