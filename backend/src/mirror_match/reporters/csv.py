"""CSV reporter.

Columns: Field_Path, Change_Type, Value_in_Doc_A, Value_in_Doc_B.
Values serialized as JSON so nested structures round-trip safely.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from typing import Any

from ..diff.models import FieldChange

HEADERS = ["Field_Path", "Change_Type", "Value_in_Doc_A", "Value_in_Doc_B"]


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def to_csv(
    changes: Iterable[FieldChange],
    *,
    source_a_id: str = "",
    source_b_id: str = "",
    timestamp: str = "",
) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    if timestamp or source_a_id or source_b_id:
        writer.writerow([f"# Generated: {timestamp}"])
        writer.writerow([f"# Source A: {source_a_id}"])
        writer.writerow([f"# Source B: {source_b_id}"])
    writer.writerow(HEADERS)
    for c in changes:
        writer.writerow(
            [
                c.path,
                c.change_type.value,
                _cell(c.value_a),
                _cell(c.value_b),
            ]
        )
    return buf.getvalue()
