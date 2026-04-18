"""Tests for mirror-match CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mirror_match.cli import main


def _write(path: Path, data) -> str:
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_compare_no_diff_returns_zero(tmp_path, capsys):
    a = _write(tmp_path / "a.json", {"x": 1})
    b = _write(tmp_path / "b.json", {"x": 1})
    rc = main(["compare", a, b])
    assert rc == 0
    assert "0 changes" in capsys.readouterr().out


def test_compare_with_diff_returns_nonzero(tmp_path, capsys):
    a = _write(tmp_path / "a.json", {"x": 1})
    b = _write(tmp_path / "b.json", {"x": 2, "y": 3})
    rc = main(["compare", a, b])
    assert rc == 1
    out = capsys.readouterr().out
    assert "2 changes" in out
    assert "1 added" in out
    assert "1 modified" in out


def test_compare_writes_csv_and_html_and_json(tmp_path):
    a = _write(tmp_path / "a.json", {"x": 1})
    b = _write(tmp_path / "b.json", {"x": 2})
    csv_out = tmp_path / "out.csv"
    html_out = tmp_path / "out.html"
    json_out = tmp_path / "out.json"
    main(
        [
            "compare",
            a,
            b,
            "--csv",
            str(csv_out),
            "--html",
            str(html_out),
            "--json",
            str(json_out),
        ]
    )
    assert "Field_Path" in csv_out.read_text()
    assert "<html" in html_out.read_text().lower()
    parsed = json.loads(json_out.read_text())
    assert parsed[0]["path"] == "/x"


def test_compare_honors_array_key_option(tmp_path):
    a = _write(tmp_path / "a.json", {"items": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]})
    b = _write(tmp_path / "b.json", {"items": [{"id": 2, "v": "y"}, {"id": 1, "v": "z"}]})
    rc = main(["compare", a, b, "--array-key", "/items=id"])
    assert rc == 1  # still has 1 change (not 2)


def test_compare_array_key_bad_format_errors(tmp_path):
    a = _write(tmp_path / "a.json", {})
    b = _write(tmp_path / "b.json", {})
    with pytest.raises(SystemExit):
        main(["compare", a, b, "--array-key", "missing-equals"])


def test_compare_numeric_tolerance(tmp_path):
    a = _write(tmp_path / "a.json", {"p": 1.0001})
    b = _write(tmp_path / "b.json", {"p": 1.0002})
    rc = main(["compare", a, b, "--numeric-tolerance", "0.001"])
    assert rc == 0


def test_compare_case_insensitive(tmp_path):
    a = _write(tmp_path / "a.json", {"n": "Alice"})
    b = _write(tmp_path / "b.json", {"n": "ALICE"})
    rc = main(["compare", a, b, "--case-insensitive"])
    assert rc == 0
