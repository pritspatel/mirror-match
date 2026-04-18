"""Tests for v1.0 diff compare options.

Covers keyed arrays, numeric tolerance, and case-insensitive strings.
"""

from __future__ import annotations

from mirror_match.diff.engine import compare
from mirror_match.diff.models import ChangeType, CompareConfig


def test_keyed_array_matches_by_id_not_position():
    a = {"items": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]}
    b = {"items": [{"id": 2, "v": "y"}, {"id": 1, "v": "z"}]}
    cfg = CompareConfig(array_keys={"/items": "id"})
    changes = compare(a, b, config=cfg)
    # Only /items[id=1]/v should diff; positional diff would flag both.
    assert len(changes) == 1
    assert changes[0].change_type is ChangeType.MODIFIED
    assert changes[0].value_a == "x"
    assert changes[0].value_b == "z"


def test_keyed_array_detects_added_and_removed_by_id():
    a = {"items": [{"id": 1, "v": "x"}]}
    b = {"items": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]}
    cfg = CompareConfig(array_keys={"/items": "id"})
    changes = compare(a, b, config=cfg)
    assert len(changes) == 1
    assert changes[0].change_type is ChangeType.ADDED
    assert changes[0].value_b == {"id": 2, "v": "y"}


def test_keyed_array_removed():
    a = {"items": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]}
    b = {"items": [{"id": 1, "v": "x"}]}
    cfg = CompareConfig(array_keys={"/items": "id"})
    changes = compare(a, b, config=cfg)
    assert len(changes) == 1
    assert changes[0].change_type is ChangeType.REMOVED
    assert changes[0].value_a == {"id": 2, "v": "y"}


def test_numeric_tolerance_hides_small_float_diffs():
    a = {"p": 1.0001}
    b = {"p": 1.0002}
    cfg = CompareConfig(numeric_tolerance=1e-3)
    assert compare(a, b, config=cfg) == []


def test_numeric_tolerance_still_flags_exceeding_delta():
    a = {"p": 1.0}
    b = {"p": 1.5}
    cfg = CompareConfig(numeric_tolerance=0.1)
    changes = compare(a, b, config=cfg)
    assert len(changes) == 1
    assert changes[0].change_type is ChangeType.MODIFIED


def test_numeric_tolerance_does_not_affect_non_numbers():
    # String comparisons must ignore numeric_tolerance.
    a = {"s": "abc"}
    b = {"s": "abd"}
    cfg = CompareConfig(numeric_tolerance=10.0)
    assert len(compare(a, b, config=cfg)) == 1


def test_case_insensitive_string_match():
    a = {"name": "Alice"}
    b = {"name": "ALICE"}
    cfg = CompareConfig(case_insensitive=True)
    assert compare(a, b, config=cfg) == []


def test_case_insensitive_still_flags_different_text():
    a = {"name": "Alice"}
    b = {"name": "Bob"}
    cfg = CompareConfig(case_insensitive=True)
    assert len(compare(a, b, config=cfg)) == 1


def test_all_options_combine():
    a = {"users": [{"id": 1, "name": "Alice", "score": 1.00}]}
    b = {"users": [{"id": 1, "name": "ALICE", "score": 1.001}]}
    cfg = CompareConfig(
        array_keys={"/users": "id"},
        numeric_tolerance=1e-2,
        case_insensitive=True,
    )
    assert compare(a, b, config=cfg) == []


def test_missing_key_on_keyed_array_falls_back_to_positional():
    # Elements lacking the declared key are compared positionally within their
    # remainder — and a MODIFIED is emitted when content differs.
    a = {"items": [{"id": 1, "v": "x"}, {"v": "orphan"}]}
    b = {"items": [{"id": 1, "v": "x"}, {"v": "different"}]}
    cfg = CompareConfig(array_keys={"/items": "id"})
    changes = compare(a, b, config=cfg)
    # The id=1 element matches cleanly; the orphan pair diffs on /v.
    paths = [c.path for c in changes]
    assert any("orphan" not in str(c.value_b) for c in changes)
    assert any("/items/" in p and p.endswith("/v") for p in paths)
