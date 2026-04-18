"""Tests for the diff engine."""

from mirror_match.diff.engine import compare
from mirror_match.diff.models import ChangeType, FieldChange


def _by_path(changes: list[FieldChange]) -> dict[str, FieldChange]:
    return {c.path: c for c in changes}


def test_identical_objects_produce_no_changes():
    assert compare({"a": 1}, {"a": 1}) == []


def test_identical_empty_objects():
    assert compare({}, {}) == []


def test_added_top_level_key():
    changes = compare({"a": 1}, {"a": 1, "b": 2})
    assert changes == [
        FieldChange(path="/b", change_type=ChangeType.ADDED, value_a=None, value_b=2)
    ]


def test_removed_top_level_key():
    changes = compare({"a": 1, "b": 2}, {"a": 1})
    assert changes == [
        FieldChange(path="/b", change_type=ChangeType.REMOVED, value_a=2, value_b=None)
    ]


def test_modified_primitive():
    changes = compare({"a": 1}, {"a": 2})
    assert changes == [
        FieldChange(path="/a", change_type=ChangeType.MODIFIED, value_a=1, value_b=2)
    ]


def test_nested_object_modification():
    changes = compare({"u": {"name": "A", "id": 1}}, {"u": {"name": "B", "id": 1}})
    by = _by_path(changes)
    assert len(changes) == 1
    assert by["/u/name"].change_type == ChangeType.MODIFIED
    assert by["/u/name"].value_a == "A"
    assert by["/u/name"].value_b == "B"


def test_deeply_nested_added():
    changes = compare({"a": {"b": {}}}, {"a": {"b": {"c": 3}}})
    assert changes == [
        FieldChange(path="/a/b/c", change_type=ChangeType.ADDED, value_a=None, value_b=3)
    ]


def test_type_change_is_modification():
    changes = compare({"x": 1}, {"x": "1"})
    assert changes == [
        FieldChange(path="/x", change_type=ChangeType.MODIFIED, value_a=1, value_b="1")
    ]


def test_null_to_value_is_modification():
    changes = compare({"x": None}, {"x": 5})
    assert changes[0].change_type == ChangeType.MODIFIED


def test_array_positional_added_element():
    changes = compare({"items": [1, 2]}, {"items": [1, 2, 3]})
    assert changes == [
        FieldChange(
            path="/items/2", change_type=ChangeType.ADDED, value_a=None, value_b=3
        )
    ]


def test_array_positional_removed_element():
    changes = compare({"items": [1, 2, 3]}, {"items": [1, 2]})
    assert changes == [
        FieldChange(
            path="/items/2", change_type=ChangeType.REMOVED, value_a=3, value_b=None
        )
    ]


def test_array_positional_modified_element():
    changes = compare({"items": [1, 2, 3]}, {"items": [1, 9, 3]})
    assert changes == [
        FieldChange(
            path="/items/1", change_type=ChangeType.MODIFIED, value_a=2, value_b=9
        )
    ]


def test_array_of_objects():
    a = {"items": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]}
    b = {"items": [{"id": 1, "v": "x"}, {"id": 2, "v": "z"}]}
    changes = compare(a, b)
    assert changes == [
        FieldChange(
            path="/items/1/v",
            change_type=ChangeType.MODIFIED,
            value_a="y",
            value_b="z",
        )
    ]


def test_json_pointer_escapes_slash_and_tilde():
    changes = compare({"a/b": 1, "c~d": 2}, {"a/b": 2, "c~d": 3})
    paths = {c.path for c in changes}
    assert paths == {"/a~1b", "/c~0d"}


def test_root_scalar_modification():
    changes = compare(1, 2)
    assert changes == [
        FieldChange(path="", change_type=ChangeType.MODIFIED, value_a=1, value_b=2)
    ]


def test_root_type_swap_object_to_array():
    changes = compare({"a": 1}, [1, 2])
    assert len(changes) == 1
    assert changes[0].path == ""
    assert changes[0].change_type == ChangeType.MODIFIED


def test_multiple_changes_sorted_by_path():
    a = {"a": 1, "b": 2, "c": 3}
    b = {"a": 10, "c": 3, "d": 4}
    changes = compare(a, b)
    paths = [c.path for c in changes]
    assert paths == ["/a", "/b", "/d"]


def test_empty_array_vs_populated():
    changes = compare({"items": []}, {"items": [1]})
    assert changes == [
        FieldChange(
            path="/items/0", change_type=ChangeType.ADDED, value_a=None, value_b=1
        )
    ]


def test_summary_counts():
    from mirror_match.diff.engine import summarize

    a = {"a": 1, "b": 2}
    b = {"a": 9, "c": 3}
    changes = compare(a, b)
    summary = summarize(changes)
    assert summary == {"added": 1, "removed": 1, "modified": 1, "total": 3}
