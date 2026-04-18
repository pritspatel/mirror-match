"""Tests for /api/v1/compare routes."""

from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from jsondiff.main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/api/v1/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_compare_json_basic():
    payload = {
        "source_a": {"type": "raw", "data": {"x": 1, "y": 2}, "identifier": "A"},
        "source_b": {"type": "raw", "data": {"x": 1, "y": 3, "z": 4}, "identifier": "B"},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source_a_id"] == "A"
    assert body["source_b_id"] == "B"
    assert body["summary"]["added"] == 1
    assert body["summary"]["modified"] == 1
    assert body["summary"]["total"] == 2
    paths = [c["path"] for c in body["changes"]]
    assert paths == ["/y", "/z"]


def test_compare_json_raw_string_input():
    payload = {
        "source_a": {"type": "raw", "data": '{"a": 1}'},
        "source_b": {"type": "raw", "data": '{"a": 2}'},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200
    assert r.json()["changes"][0]["change_type"] == "MODIFIED"


def test_compare_ignore_paths():
    payload = {
        "source_a": {"type": "raw", "data": {"keep": 1, "meta": {"ts": "2026-01-01"}}},
        "source_b": {"type": "raw", "data": {"keep": 2, "meta": {"ts": "2026-04-18"}}},
        "options": {"ignore_paths": ["/meta"]},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200
    paths = [c["path"] for c in r.json()["changes"]]
    assert paths == ["/keep"]


def test_compare_csv_export():
    payload = {
        "source_a": {"type": "raw", "data": {"x": 1}, "identifier": "prod"},
        "source_b": {"type": "raw", "data": {"x": 2, "y": 9}, "identifier": "stg"},
    }
    r = client.post("/api/v1/compare.csv", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]

    text = r.text
    assert "# Source A: prod" in text
    assert "# Source B: stg" in text

    # Parse the data rows (after the three comment lines).
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    header_idx = next(i for i, row in enumerate(rows) if row and row[0] == "Field_Path")
    data = rows[header_idx + 1 :]
    by_path = {r[0]: r for r in data}
    assert by_path["/x"][1] == "MODIFIED"
    assert by_path["/x"][2] == "1"
    assert by_path["/x"][3] == "2"
    assert by_path["/y"][1] == "ADDED"


def test_compare_empty_rejects_malformed():
    r = client.post("/api/v1/compare", json={"source_a": {"type": "raw"}})
    assert r.status_code == 422
