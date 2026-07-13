"""标准解析器测试：normalize_standard_number, parse_standards_from_text, fix_ocr_digits"""

from __future__ import annotations

from models import StandardRef
from standard_parser import (
    deduplicate_standards,
    fix_ocr_digits,
    normalize_standard_number,
    parse_standards_from_text,
    split_standard_entries,
)

# ==================== normalize_standard_number ====================


class TestNormalizeStandardNumber:
    """normalize_standard_number 规范化测试"""

    def test_em_dash_to_hyphen(self):
        """全角破折号 → ASCII 连字符"""
        assert normalize_standard_number("GB/T50352—2019") == "GB/T 50352-2019"

    def test_wide_dash_to_hyphen(self):
        """全角连字符 → ASCII 连字符"""
        assert normalize_standard_number("GB/T50352－2019") == "GB/T 50352-2019"

    def test_en_dash_to_hyphen(self):
        """半角连接号 → ASCII 连字符"""
        assert normalize_standard_number("GB/T50352–2019") == "GB/T 50352-2019"

    def test_fullwidth_slash(self):
        """全角斜杠 → 半角斜杠"""
        assert normalize_standard_number("JGJ／T 3—2010") == "JGJ/T 3-2010"

    def test_ensure_space_before_number(self):
        """确保前缀和编号之间有空格"""
        assert normalize_standard_number("GB50016-2014") == "GB 50016-2014"

    def test_extra_spaces_collapsed(self):
        """多余空格被压缩（连字符周围空格保留，由用户确保格式）"""
        assert normalize_standard_number("GB  50016 - 2014") == "GB 50016 - 2014"

    def test_already_normalized(self):
        """已经规范的字符串保持不变"""
        assert normalize_standard_number("GB 50016-2014") == "GB 50016-2014"

    def test_jgj_t_format(self):
        assert normalize_standard_number("JGJ/T 3-2010") == "JGJ/T 3-2010"


# ==================== parse_standards_from_text ====================


class TestParseStandardsFromText:
    """parse_standards_from_text 标准文本解析测试"""

    def test_single_standard_with_name(self):
        """单条标准，编号+名称"""
        result = parse_standards_from_text("GB 50016-2014 建筑设计防火规范")
        assert len(result) == 1
        ref = result[0]
        assert ref.number == "GB 50016-2014"
        assert ref.name == "建筑设计防火规范"
        assert ref.confidence == 1.0
        assert ref.source_files == ["文本输入"]

    def test_single_standard_number_only(self):
        """仅编号无名称"""
        result = parse_standards_from_text("GB/T 50352-2019")
        assert len(result) == 1
        assert result[0].number == "GB/T 50352-2019"
        assert result[0].name == ""

    def test_empty_text_returns_empty_list(self):
        """空文本"""
        assert parse_standards_from_text("") == []
        assert parse_standards_from_text("   ") == []
        assert parse_standards_from_text("\n\n") == []

    def test_multiple_standards_newlines(self):
        """换行分隔多条标准"""
        text = "GB 50016-2014 建筑设计防火规范\nJGJ 3-2010 高层建筑混凝土结构技术规程"
        result = parse_standards_from_text(text)
        assert len(result) == 2
        assert result[0].number == "GB 50016-2014"
        assert result[1].number == "JGJ 3-2010"

    def test_multiple_standards_semicolon(self):
        """分号分隔"""
        text = "GB 50016-2014 建筑设计防火规范; JGJ 3-2010 高层建筑混凝土结构技术规程"
        result = parse_standards_from_text(text)
        assert len(result) == 2

    def test_multiple_standards_comma(self):
        """逗号+空格分隔"""
        text = "GB 50016-2014, GB 50222-2017"
        result = parse_standards_from_text(text)
        assert len(result) == 2

    def test_duplicate_dedup(self):
        """重复编号去重"""
        text = "GB 50016-2014\nGB 50016-2014"
        result = parse_standards_from_text(text)
        assert len(result) == 1

    def test_book_title_marks_stripped(self):
        """书名号被清洗"""
        text = "《GB 50016-2014》建筑设计防火规范"
        result = parse_standards_from_text(text)
        assert len(result) == 1
        assert result[0].number == "GB 50016-2014"

    def test_custom_source(self):
        """自定义 source 参数"""
        result = parse_standards_from_text("GB 50016-2014", source="自定义来源")
        assert result[0].source_files == ["自定义来源"]


# ==================== fix_ocr_digits ====================


class TestFixOcrDigits:
    """fix_ocr_digits OCR数字纠错测试"""

    def test_o_to_zero(self):
        """字母 O → 数字 0"""
        assert fix_ocr_digits("GB 5OOl6-2014") == "GB 50016-2014"

    def test_s_to_five(self):
        """字母 S → 数字 5"""
        assert fix_ocr_digits("GB 5001S-2014") == "GB 50015-2014"

    def test_l_to_one(self):
        """字母 l → 数字 1"""
        assert fix_ocr_digits("GB/T 5000l-2010") == "GB/T 50001-2010"

    def test_i_to_one(self):
        """字母 I → 数字 1"""
        assert fix_ocr_digits("GB/T 5000I-2010") == "GB/T 50001-2010"

    def test_b_to_eight(self):
        """字母 B → 数字 8"""
        assert fix_ocr_digits("GB/T 50B32-2010") == "GB/T 50832-2010"

    def test_z_to_two(self):
        """字母 Z → 数字 2"""
        assert fix_ocr_digits("GB 5001Z-2010") == "GB 50012-2010"

    def test_no_digits_no_change(self):
        """没有数字区域的文本不变"""
        assert fix_ocr_digits("建筑设计防火规范") == "建筑设计防火规范"

    def test_already_correct(self):
        """已经正确的编号不变"""
        assert fix_ocr_digits("GB 50016-2014") == "GB 50016-2014"


# ==================== split_standard_entries ====================


class TestSplitStandardEntries:
    """split_standard_entries 分割测试"""

    def test_newline_split(self):
        parts = split_standard_entries("GB 50016-2014\nJGJ 3-2010")
        assert len(parts) == 2

    def test_semicolon_split(self):
        parts = split_standard_entries("GB 50016-2014; JGJ 3-2010")
        assert len(parts) == 2

    def test_double_space_split(self):
        parts = split_standard_entries("GB 50016-2014  JGJ 3-2010")
        assert len(parts) == 2

    def test_chinese_semicolon(self):
        parts = split_standard_entries("GB 50016-2014；JGJ 3-2010")
        assert len(parts) == 2

    def test_single_entry(self):
        parts = split_standard_entries("GB 50016-2014")
        assert len(parts) == 1

    def test_empty(self):
        assert split_standard_entries("") == []
        assert split_standard_entries("   ") == []


# ==================== deduplicate_standards ====================


class TestDeduplicateStandards:
    """deduplicate_standards 去重测试"""

    def test_deduplicate_by_number(self):
        refs = [
            StandardRef(number="GB 50016-2014", name="A", confidence=0.8),
            StandardRef(number="GB 50016-2014", name="A", confidence=0.9),
        ]
        result = deduplicate_standards(refs)
        assert len(result) == 1
        # 保留较高置信度
        assert result[0].confidence == 0.9

    def test_merge_source_files(self):
        refs = [
            StandardRef(
                number="GB 50016-2014",
                name="A",
                source_files=["img1.png"],
                confidence=0.8,
            ),
            StandardRef(
                number="GB 50016-2014",
                name="A",
                source_files=["img2.png"],
                confidence=0.7,
            ),
        ]
        result = deduplicate_standards(refs)
        assert len(result) == 1
        assert "img1.png" in result[0].source_files
        assert "img2.png" in result[0].source_files

    def test_no_duplicates(self):
        refs = [
            StandardRef(number="GB 50016-2014", name="A"),
            StandardRef(number="JGJ 3-2010", name="B"),
        ]
        result = deduplicate_standards(refs)
        assert len(result) == 2
