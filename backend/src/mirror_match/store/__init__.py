"""Job persistence."""

from .base import JobRecord, JobStore
from .sqlite import SqliteJobStore

__all__ = ["JobRecord", "JobStore", "SqliteJobStore"]


def PostgresJobStore(dsn: str):  # pragma: no cover - thin re-export
    from .postgres import PostgresJobStore as _Pg

    return _Pg(dsn)
