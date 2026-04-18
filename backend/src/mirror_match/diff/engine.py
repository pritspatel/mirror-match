"""Core diff engine.

Walks two JSON-compatible values and emits ordered `FieldChange` records keyed
by JSON Pointer (RFC 6901) paths. Arrays are compared positionally in v0.1.
"""

from __future__ import annotations

from typing import Any

from .models import ChangeType, FieldChange

JsonValue = Any


def _escape_token(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _join(parent: str, token: str | int) -> str:
    return f"{parent}/{_escape_token(str(token)) if isinstance(token, str) else token}"


def compare(a: JsonValue, b: JsonValue) -> list[FieldChange]:
    """Compare two JSON values and return a sorted list of field changes."""
    changes: list[FieldChange] = []
    _walk("", a, b, changes)
    changes.sort(key=lambda c: c.path)
    return changes


def _walk(path: str, a: JsonValue, b: JsonValue, out: list[FieldChange]) -> None:
    if _equal(a, b):
        return

    if isinstance(a, dict) and isinstance(b, dict):
        _walk_dict(path, a, b, out)
        return

    if isinstance(a, list) and isinstance(b, list):
        _walk_list(path, a, b, out)
        return

    # Scalar or type change → single MODIFIED at this path.
    out.append(
        FieldChange(
            path=path,
            change_type=ChangeType.MODIFIED,
            value_a=a,
            value_b=b,
        )
    )


def _walk_dict(
    path: str, a: dict[str, Any], b: dict[str, Any], out: list[FieldChange]
) -> None:
    for key in a.keys() - b.keys():
        out.append(
            FieldChange(
                path=_join(path, key),
                change_type=ChangeType.REMOVED,
                value_a=a[key],
                value_b=None,
            )
        )
    for key in b.keys() - a.keys():
        out.append(
            FieldChange(
                path=_join(path, key),
                change_type=ChangeType.ADDED,
                value_a=None,
                value_b=b[key],
            )
        )
    for key in a.keys() & b.keys():
        _walk(_join(path, key), a[key], b[key], out)


def _walk_list(
    path: str, a: list[Any], b: list[Any], out: list[FieldChange]
) -> None:
    la, lb = len(a), len(b)
    for i in range(min(la, lb)):
        _walk(_join(path, i), a[i], b[i], out)
    if la > lb:
        for i in range(lb, la):
            out.append(
                FieldChange(
                    path=_join(path, i),
                    change_type=ChangeType.REMOVED,
                    value_a=a[i],
                    value_b=None,
                )
            )
    elif lb > la:
        for i in range(la, lb):
            out.append(
                FieldChange(
                    path=_join(path, i),
                    change_type=ChangeType.ADDED,
                    value_a=None,
                    value_b=b[i],
                )
            )


def _equal(a: JsonValue, b: JsonValue) -> bool:
    # Preserve type distinctions (1 != "1", True != 1).
    if type(a) is not type(b):
        return False
    return a == b


def summarize(changes: list[FieldChange]) -> dict[str, int]:
    added = sum(1 for c in changes if c.change_type is ChangeType.ADDED)
    removed = sum(1 for c in changes if c.change_type is ChangeType.REMOVED)
    modified = sum(1 for c in changes if c.change_type is ChangeType.MODIFIED)
    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "total": added + removed + modified,
    }
