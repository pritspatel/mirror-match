"""Tests for SQLite job store."""

from __future__ import annotations

from pathlib import Path

from mirror_match.diff.models import ChangeType, FieldChange
from mirror_match.store.base import JobRecord
from mirror_match.store.sqlite import SqliteJobStore


def _sample_record(job_id: str = "job-1") -> JobRecord:
    return JobRecord(
        job_id=job_id,
        timestamp="2026-04-18T12:00:00+00:00",
        source_a_id="A",
        source_b_id="B",
        summary={"added": 1, "removed": 0, "modified": 1, "total": 2},
        changes=[
            FieldChange(path="/x", change_type=ChangeType.MODIFIED, value_a=1, value_b=2),
            FieldChange(path="/y", change_type=ChangeType.ADDED, value_a=None, value_b=3),
        ],
        request={"source_a": {"type": "raw", "data": {"x": 1}}},
    )


def test_put_and_get_roundtrip(tmp_path: Path):
    store = SqliteJobStore(tmp_path / "jobs.db")
    rec = _sample_record()
    store.put(rec)
    got = store.get("job-1")
    assert got is not None
    assert got.job_id == "job-1"
    assert got.source_a_id == "A"
    assert got.summary["total"] == 2
    assert len(got.changes) == 2
    assert got.changes[0].path == "/x"
    assert got.changes[0].change_type is ChangeType.MODIFIED


def test_get_missing_returns_none(tmp_path: Path):
    store = SqliteJobStore(tmp_path / "jobs.db")
    assert store.get("nope") is None


def test_put_is_idempotent(tmp_path: Path):
    store = SqliteJobStore(tmp_path / "jobs.db")
    store.put(_sample_record())
    store.put(_sample_record())
    assert store.get("job-1") is not None


def test_store_survives_reopen(tmp_path: Path):
    path = tmp_path / "jobs.db"
    store_a = SqliteJobStore(path)
    store_a.put(_sample_record("persist-me"))
    store_b = SqliteJobStore(path)
    assert store_b.get("persist-me") is not None


def test_persisted_request_is_redacted(tmp_path: Path, monkeypatch):
    """E2E: secrets in the submitted request must not survive to the DB."""
    import respx
    from fastapi.testclient import TestClient

    from mirror_match import config as cfg
    from mirror_match.api.redact import REDACTED
    from mirror_match.main import app

    db = tmp_path / "jobs.db"
    monkeypatch.setenv("MIRROR_MATCH_DB_PATH", str(db))
    cfg.reset_job_store_cache()
    client = TestClient(app)

    with respx.mock:
        respx.get("https://api.example.com/a").respond(200, json={"ok": 1})
        respx.get("https://api.example.com/b").respond(200, json={"ok": 2})
        payload = {
            "source_a": {
                "type": "http",
                "url": "https://api.example.com/a",
                "auth": {"kind": "bearer", "token": "LEAKED-TOKEN"},
                "headers": {"X-API-Key": "HEADER-TOKEN"},
            },
            "source_b": {
                "type": "http",
                "url": "https://api.example.com/b",
                "auth": {"kind": "basic", "username": "svc", "password": "pw"},
                "headers": {},
            },
        }
        resp = client.post("/api/v1/compare", json=payload)
        assert resp.status_code == 200, resp.text
        job_id = resp.json()["job_id"]

    record = SqliteJobStore(db).get(job_id)
    assert record is not None
    blob = str(record.request)
    assert "LEAKED-TOKEN" not in blob
    assert "HEADER-TOKEN" not in blob
    assert "pw" not in blob
    assert REDACTED in blob
