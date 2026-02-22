"""Tests for templates.py - name structure templates."""

from src.templates import (
    TEMPLATES,
    NameTemplate,
    SegmentRole,
    SegmentSpec,
    format_name,
    get_template_by_label,
    list_templates,
    select_templates,
)


class TestNameTemplate:
    def test_total_min(self):
        t = NameTemplate(
            "Test",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 7),
                SegmentSpec(SegmentRole.LAST, 3, 8),
            ],
        )
        assert t.total_min() == 6

    def test_total_max(self):
        t = NameTemplate(
            "Test",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 7),
                SegmentSpec(SegmentRole.LAST, 3, 8),
            ],
        )
        assert t.total_max() == 15


class TestSelectTemplates:
    def test_returns_templates(self):
        templates = select_templates(10)
        assert len(templates) > 0

    def test_all_viable(self):
        templates = select_templates(10)
        for t in templates:
            assert t.total_min() <= 10 <= t.total_max()

    def test_no_hyphen_for_short(self):
        templates = select_templates(8)
        for t in templates:
            roles = [s.role for s in t.segments]
            assert SegmentRole.HYPHENATED_LAST not in roles

    def test_very_short_gets_fallback(self):
        templates = select_templates(3)
        assert len(templates) >= 1

    def test_max_five_templates(self):
        templates = select_templates(12)
        assert len(templates) <= 5

    def test_required_roles_filters(self):
        templates = select_templates(10, required_roles={SegmentRole.FIRST})
        for t in templates:
            roles = {s.role for s in t.segments}
            assert SegmentRole.FIRST in roles

    def test_required_roles_excludes_mononym_for_last(self):
        templates = select_templates(6, required_roles={SegmentRole.LAST})
        for t in templates:
            roles = {s.role for s in t.segments}
            assert SegmentRole.LAST in roles


class TestGetTemplateByLabel:
    def test_exact_match(self):
        t = get_template_by_label("First Last")
        assert t is not None
        assert t.label == "First Last"

    def test_case_insensitive(self):
        t = get_template_by_label("first m. last")
        assert t is not None
        assert t.label == "First M. Last"

    def test_not_found(self):
        assert get_template_by_label("Nonexistent") is None

    def test_strips_whitespace(self):
        t = get_template_by_label("  First Last  ")
        assert t is not None


class TestListTemplates:
    def test_returns_all_templates(self):
        result = list_templates()
        assert len(result) == len(TEMPLATES)

    def test_entry_shape(self):
        result = list_templates()
        for label, min_l, max_l in result:
            assert isinstance(label, str)
            assert isinstance(min_l, int)
            assert isinstance(max_l, int)
            assert min_l <= max_l


class TestFormatName:
    def test_first_last(self):
        template = NameTemplate(
            "First Last",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 7),
                SegmentSpec(SegmentRole.LAST, 3, 8),
            ],
        )
        result = format_name(["alice", "smith"], template)
        assert result == "Alice Smith"

    def test_initial(self):
        template = NameTemplate(
            "First M. Last",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 7),
                SegmentSpec(SegmentRole.INITIAL, 1, 1),
                SegmentSpec(SegmentRole.LAST, 3, 8),
            ],
        )
        result = format_name(["alice", "m", "smith"], template)
        assert result == "Alice M. Smith"

    def test_hyphenated_last(self):
        template = NameTemplate(
            "First Last-Last",
            [
                SegmentSpec(SegmentRole.FIRST, 3, 7),
                SegmentSpec(SegmentRole.LAST, 3, 8),
                SegmentSpec(SegmentRole.HYPHENATED_LAST, 3, 8),
            ],
        )
        result = format_name(["alice", "smith", "jones"], template)
        assert result == "Alice Smith-Jones"
