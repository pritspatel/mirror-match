"""Core diff engine.

Walks two JSON-compatible values and emits ordered `FieldChange` records keyed
by JSON Pointer (RFC 6901) paths. Array strategy is configurable per path:
positional (default) or keyed-by-field via `CompareConfig.array_keys`.
"""

from __future__ import annotations

from typing import Any

from .models import ChangeType, CompareConfig, FieldChange

JsonValue = Any


def _escape_token(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _join(parent: str, token: str | int) -> str:
    return f"{parent}/{_escape_token(str(token)) if isinstance(token, str) else token}"


def compare(
    a: JsonValue,
    b: JsonValue,
    *,
    config: CompareConfig | None = None,
) -> list[FieldChange]:
    """Compare two JSON values and return a sorted list of field changes."""
    cfg = config or CompareConfig()
    changes: list[FieldChange] = []
    _walk("", a, b, changes, cfg)
    changes.sort(key=lambda c: c.path)
    return changes


def _walk(
    path: str,
    a: JsonValue,
    b: JsonValue,
    out: list[FieldChange],
    cfg: CompareConfig,
) -> None:
    if _equal(a, b, cfg):
        return

    if isinstance(a, dict) and isinstance(b, dict):
        _walk_dict(path, a, b, out, cfg)
        return

    if isinstance(a, list) and isinstance(b, list):
        key = cfg.array_keys.get(path)
        if key is not None:
            _walk_list_keyed(path, a, b, out, cfg, key)
        else:
            _walk_list_positional(path, a, b, out, cfg)
        return

    out.append(
        FieldChange(
            path=path,
            change_type=ChangeType.MODIFIED,
            value_a=a,
            value_b=b,
        )
    )


def _walk_dict(
    path: str,
    a: dict[str, Any],
    b: dict[str, Any],
    out: list[FieldChange],
    cfg: CompareConfig,
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
        _walk(_join(path, key), a[key], b[key], out, cfg)


def _walk_list_positional(
    path: str,
    a: list[Any],
    b: list[Any],
    out: list[FieldChange],
    cfg: CompareConfig,
) -> None:
    la, lb = len(a), len(b)
    for i in range(min(la, lb)):
        _walk(_join(path, i), a[i], b[i], out, cfg)
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


def _walk_list_keyed(
    path: str,
    a: list[Any],
    b: list[Any],
    out: list[FieldChange],
    cfg: CompareConfig,
    key: str,
) -> None:
    a_keyed, a_orphans = _index_by_key(a, key)
    b_keyed, b_orphans = _index_by_key(b, key)

    for k in a_keyed.keys() - b_keyed.keys():
        out.append(
            FieldChange(
                path=_join(path, str(k)),
                change_type=ChangeType.REMOVED,
                value_a=a_keyed[k],
                value_b=None,
            )
        )
    for k in b_keyed.keys() - a_keyed.keys():
        out.append(
            FieldChange(
                path=_join(path, str(k)),
                change_type=ChangeType.ADDED,
                value_a=None,
                value_b=b_keyed[k],
            )
        )
    for k in a_keyed.keys() & b_keyed.keys():
        _walk(_join(path, str(k)), a_keyed[k], b_keyed[k], out, cfg)

    # Elements lacking the declared key fall back to positional diff under
    # a synthetic sub-path so their JSON Pointers remain unique.
    if a_orphans or b_orphans:
        _walk_list_positional(_join(path, "~"), a_orphans, b_orphans, out, cfg)


def _index_by_key(items: list[Any], key: str) -> tuple[dict[Any, Any], list[Any]]:
    indexed: dict[Any, Any] = {}
    orphans: list[Any] = []
    for item in items:
        if isinstance(item, dict) and key in item:
            indexed[item[key]] = item
        else:
            orphans.append(item)
    return indexed, orphans


def _equal(a: JsonValue, b: JsonValue, cfg: CompareConfig) -> bool:
    if a is None and b is None:
        return True
    if cfg.case_insensitive and isinstance(a, str) and isinstance(b, str):
        return a.casefold() == b.casefold()
    if cfg.numeric_tolerance > 0 and _is_number(a) and _is_number(b):
        return abs(float(a) - float(b)) <= cfg.numeric_tolerance
    if type(a) is not type(b):
        return False
    return a == b


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


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
