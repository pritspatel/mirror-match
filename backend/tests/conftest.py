"""Global test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolated_job_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / "jobs.db"
    monkeypatch.setenv("MIRROR_MATCH_DB_PATH", str(db))
    from mirror_match import config as cfg

    cfg.reset_job_store_cache()
    yield
    cfg.reset_job_store_cache()
