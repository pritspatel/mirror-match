"""Standalone HTML report renderer (inline CSS, no CDN)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .. import __version__
from ..diff.models import FieldChange

BADGES = {"ADDED": "+", "REMOVED": "-", "MODIFIED": "~"}


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    autoescape=select_autoescape(["html", "j2"]),
)


def to_html(
    changes: list[FieldChange],
    *,
    source_a_id: str,
    source_b_id: str,
    timestamp: str,
    summary: dict[str, int],
) -> str:
    template = _env.get_template("report.html.j2")
    return template.render(
        changes=changes,
        source_a_id=source_a_id,
        source_b_id=source_b_id,
        timestamp=timestamp,
        summary=summary,
        version=__version__,
        BADGES=BADGES,
        fmt=_fmt,
    )
