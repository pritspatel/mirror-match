"""Pre-diff normalization options."""

from __future__ import annotations

import json
from typing import Any


def as_set(value: Any) -> Any:
    """Recursively sort any list by canonical JSON representation.

    Lets arrays be compared as sets: position no longer matters, identical
    multi-sets produce no diff.
    """
    if isinstance(value, dict):
        return {k: as_set(v) for k, v in value.items()}
    if isinstance(value, list):
        normalized = [as_set(item) for item in value]
        normalized.sort(key=lambda x: json.dumps(x, sort_keys=True, default=str))
        return normalized
    return value
