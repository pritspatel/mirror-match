"""Tests for the HTML reporter."""

from __future__ import annotations

from jsondiff.diff.models import ChangeType, FieldChange
from jsondiff.reporters.html import to_html


def test_html_report_contains_required_sections():
    changes = [
        FieldChange(path="/x", change_type=ChangeType.MODIFIED, value_a=1, value_b=2),
        FieldChange(path="/z", change_type=ChangeType.ADDED, value_a=None, value_b=9),
    ]
    html = to_html(
        changes,
        source_a_id="prod",
        source_b_id="stg",
        timestamp="2026-04-18T00:00:00+00:00",
        summary={"added": 1, "removed": 0, "modified": 1, "total": 2},
    )
    assert "<!doctype html>" in html.lower()
    assert "JSONDiff Report" in html
    assert "prod" in html and "stg" in html
    assert "2026-04-18T00:00:00+00:00" in html
    assert "/x" in html and "/z" in html
    assert "MODIFIED" in html and "ADDED" in html
    assert "http://" not in html  # standalone — no external resources


def test_html_report_empty_changes_shows_empty_state():
    html = to_html(
        [],
        source_a_id="a",
        source_b_id="b",
        timestamp="t",
        summary={"added": 0, "removed": 0, "modified": 0, "total": 0},
    )
    assert "identical" in html.lower()


def test_html_report_escapes_html_in_values():
    changes = [
        FieldChange(
            path="/x",
            change_type=ChangeType.MODIFIED,
            value_a="<script>",
            value_b="ok",
        )
    ]
    html = to_html(
        changes,
        source_a_id="a",
        source_b_id="b",
        timestamp="t",
        summary={"added": 0, "removed": 0, "modified": 1, "total": 1},
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
