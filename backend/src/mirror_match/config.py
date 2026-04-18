"""Runtime configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .store.sqlite import SqliteJobStore


@lru_cache(maxsize=1)
def get_job_store() -> SqliteJobStore:
    path = os.environ.get("MIRROR_MATCH_DB_PATH", "mirror-match.db")
    parent = Path(path).parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    return SqliteJobStore(path)


def reset_job_store_cache() -> None:
    get_job_store.cache_clear()


def get_auth_token() -> str | None:
    return os.environ.get("MIRROR_MATCH_AUTH_TOKEN") or None
