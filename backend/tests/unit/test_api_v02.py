"""Tests for v0.2 additions: array-as-set, HTTP source via API, HTML export."""

from __future__ import annotations

import httpx
import respx
from fastapi.testclient import TestClient

from jsondiff.main import app

client = TestClient(app)


def test_array_as_set_treats_reordered_arrays_as_equal():
    payload = {
        "source_a": {"type": "raw", "data": {"tags": ["a", "b", "c"]}},
        "source_b": {"type": "raw", "data": {"tags": ["c", "a", "b"]}},
        "options": {"array_as_set": True},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200
    assert r.json()["summary"]["total"] == 0


def test_array_as_set_false_flags_positional_changes():
    payload = {
        "source_a": {"type": "raw", "data": {"tags": ["a", "b", "c"]}},
        "source_b": {"type": "raw", "data": {"tags": ["c", "a", "b"]}},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200
    assert r.json()["summary"]["total"] >= 2


@respx.mock
def test_http_source_through_api():
    respx.get("https://api.example.com/a").mock(
        return_value=httpx.Response(200, json={"v": 1})
    )
    respx.get("https://api.example.com/b").mock(
        return_value=httpx.Response(200, json={"v": 2})
    )
    payload = {
        "source_a": {"type": "http", "url": "https://api.example.com/a"},
        "source_b": {"type": "http", "url": "https://api.example.com/b"},
    }
    r = client.post("/api/v1/compare", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"]["modified"] == 1
    assert body["changes"][0]["path"] == "/v"


def test_html_export_endpoint():
    payload = {
        "source_a": {"type": "raw", "data": {"x": 1}, "identifier": "prod"},
        "source_b": {"type": "raw", "data": {"x": 2, "y": 9}, "identifier": "stg"},
    }
    r = client.post("/api/v1/compare.html", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "attachment" in r.headers["content-disposition"]
    body = r.text
    assert "prod" in body and "stg" in body
    assert "MODIFIED" in body
    assert "ADDED" in body
