"""Tests for /api/v1/compare routes."""

from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from mirror_match.main import app

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


def test_compare_keyed_array_option():
    payload = {
        "source_a": {"type": "raw", "data": {"items": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]}},
        "source_b": {"type": "raw", "data": {"items": [{"id": 2, "v": "y"}, {"id": 1, "v": "z"}]}},
        "options": {"array_keys": {"/items": "id"}},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total"] == 1
    assert body["changes"][0]["value_a"] == "x"
    assert body["changes"][0]["value_b"] == "z"


def test_compare_numeric_tolerance_option():
    payload = {
        "source_a": {"type": "raw", "data": {"p": 1.0001}},
        "source_b": {"type": "raw", "data": {"p": 1.0002}},
        "options": {"numeric_tolerance": 1e-3},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200
    assert r.json()["summary"]["total"] == 0


def test_job_permalink_roundtrip():
    payload = {
        "source_a": {"type": "raw", "data": {"x": 1}, "identifier": "A"},
        "source_b": {"type": "raw", "data": {"x": 2}, "identifier": "B"},
    }
    post = client.post("/api/v1/compare", json=payload)
    assert post.status_code == 200
    job_id = post.json()["job_id"]

    got = client.get(f"/api/v1/jobs/{job_id}")
    assert got.status_code == 200
    body = got.json()
    assert body["job_id"] == job_id
    assert body["source_a_id"] == "A"
    assert body["summary"]["modified"] == 1


def test_job_csv_and_html_permalinks():
    payload = {
        "source_a": {"type": "raw", "data": {"x": 1}, "identifier": "A"},
        "source_b": {"type": "raw", "data": {"x": 2}, "identifier": "B"},
    }
    job_id = client.post("/api/v1/compare", json=payload).json()["job_id"]

    csv_resp = client.get(f"/api/v1/jobs/{job_id}/csv")
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert "Field_Path" in csv_resp.text

    html_resp = client.get(f"/api/v1/jobs/{job_id}/html")
    assert html_resp.status_code == 200
    assert "<html" in html_resp.text.lower()


def test_job_missing_returns_404():
    r = client.get("/api/v1/jobs/does-not-exist")
    assert r.status_code == 404


def test_compare_case_insensitive_option():
    payload = {
        "source_a": {"type": "raw", "data": {"name": "Alice"}},
        "source_b": {"type": "raw", "data": {"name": "ALICE"}},
        "options": {"case_insensitive": True},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200
    assert r.json()["summary"]["total"] == 0
