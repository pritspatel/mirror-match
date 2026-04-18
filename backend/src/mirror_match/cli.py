"""`mirror-match` CLI.

Compares two local JSON files and emits the diff to stdout (summary) plus
optional CSV/HTML reports. The CLI deliberately avoids the HTTP server path:
it calls the diff engine directly so it can run offline.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from .diff.engine import compare, summarize
from .diff.models import CompareConfig
from .reporters.csv import to_csv
from .reporters.html import to_html


def _parse_array_keys(pairs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in pairs:
        if "=" not in raw:
            raise SystemExit(f"--array-key expects POINTER=field, got: {raw}")
        pointer, field = raw.split("=", 1)
        out[pointer] = field
    return out


def _load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mirror-match")
    sub = parser.add_subparsers(dest="cmd", required=True)

    cmp_p = sub.add_parser("compare", help="Compare two JSON files")
    cmp_p.add_argument("file_a")
    cmp_p.add_argument("file_b")
    cmp_p.add_argument("--csv", metavar="PATH", help="Write CSV report to PATH")
    cmp_p.add_argument("--html", metavar="PATH", help="Write HTML report to PATH")
    cmp_p.add_argument("--json", metavar="PATH", help="Write JSON changes to PATH")
    cmp_p.add_argument(
        "--array-key",
        action="append",
        default=[],
        metavar="POINTER=FIELD",
        help="Diff array at POINTER by FIELD. Repeatable.",
    )
    cmp_p.add_argument("--numeric-tolerance", type=float, default=0.0)
    cmp_p.add_argument("--case-insensitive", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd != "compare":
        parser.print_help()
        return 2

    a = _load(args.file_a)
    b = _load(args.file_b)
    cfg = CompareConfig(
        array_keys=_parse_array_keys(args.array_key),
        numeric_tolerance=args.numeric_tolerance,
        case_insensitive=args.case_insensitive,
    )
    changes = compare(a, b, config=cfg)
    summary = summarize(changes)
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")

    if args.csv:
        Path(args.csv).write_text(
            to_csv(changes, source_a_id=args.file_a, source_b_id=args.file_b, timestamp=timestamp),
            encoding="utf-8",
        )
    if args.html:
        Path(args.html).write_text(
            to_html(
                changes,
                source_a_id=args.file_a,
                source_b_id=args.file_b,
                timestamp=timestamp,
                summary=summary,
            ),
            encoding="utf-8",
        )
    if args.json:
        Path(args.json).write_text(
            json.dumps([c.model_dump() for c in changes], indent=2),
            encoding="utf-8",
        )

    sys.stdout.write(
        f"{summary['total']} changes: {summary['added']} added, "
        f"{summary['removed']} removed, {summary['modified']} modified\n"
    )
    return 0 if summary["total"] == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
