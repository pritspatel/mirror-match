"""Tests for job-store selection in config."""

from __future__ import annotations

from mirror_match import config as cfg
from mirror_match.store.sqlite import SqliteJobStore


def test_defaults_to_sqlite(monkeypatch, tmp_path):
    monkeypatch.delenv("MIRROR_MATCH_DB_URL", raising=False)
    monkeypatch.setenv("MIRROR_MATCH_DB_PATH", str(tmp_path / "x.db"))
    cfg.reset_job_store_cache()
    assert isinstance(cfg.get_job_store(), SqliteJobStore)


def test_postgres_url_selects_postgres_store(monkeypatch):
    sentinel = object()
    calls: list[str] = []

    def fake_pg(dsn: str):
        calls.append(dsn)
        return sentinel

    import mirror_match.store.postgres as pg_mod

    monkeypatch.setattr(pg_mod, "PostgresJobStore", fake_pg)
    monkeypatch.setenv("MIRROR_MATCH_DB_URL", "postgresql://u:p@h/db")
    cfg.reset_job_store_cache()
    assert cfg.get_job_store() is sentinel
    assert calls == ["postgresql://u:p@h/db"]


def test_postgres_scheme_variant(monkeypatch):
    sentinel = object()
    import mirror_match.store.postgres as pg_mod

    monkeypatch.setattr(pg_mod, "PostgresJobStore", lambda _: sentinel)
    monkeypatch.setenv("MIRROR_MATCH_DB_URL", "postgres://u:p@h/db")
    cfg.reset_job_store_cache()
    assert cfg.get_job_store() is sentinel


def test_non_postgres_url_falls_back_to_sqlite(monkeypatch, tmp_path):
    monkeypatch.setenv("MIRROR_MATCH_DB_URL", "")
    monkeypatch.setenv("MIRROR_MATCH_DB_PATH", str(tmp_path / "x.db"))
    cfg.reset_job_store_cache()
    assert isinstance(cfg.get_job_store(), SqliteJobStore)
