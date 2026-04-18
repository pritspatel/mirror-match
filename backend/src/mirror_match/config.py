"""Runtime configuration.

Job store selection
-------------------
`MIRROR_MATCH_DB_URL` takes precedence. When it starts with `postgres://` or
`postgresql://`, the Postgres store is used (requires the `postgres` extra).
Otherwise, `MIRROR_MATCH_DB_PATH` (default `mirror-match.db`) selects the
SQLite file. Both env vars are read lazily so tests can monkeypatch them.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from .store.sqlite import SqliteJobStore


def _build_store() -> Any:
    url = os.environ.get("MIRROR_MATCH_DB_URL", "").strip()
    if url.startswith(("postgres://", "postgresql://")):
        from .store.postgres import PostgresJobStore

        return PostgresJobStore(url)
    path = os.environ.get("MIRROR_MATCH_DB_PATH", "mirror-match.db")
    parent = Path(path).parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    return SqliteJobStore(path)


@lru_cache(maxsize=1)
def get_job_store() -> Any:
    return _build_store()


def reset_job_store_cache() -> None:
    get_job_store.cache_clear()


def get_auth_token() -> str | None:
    return os.environ.get("MIRROR_MATCH_AUTH_TOKEN") or None
