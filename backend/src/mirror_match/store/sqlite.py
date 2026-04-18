"""SQLite-backed job store.

Stores diff jobs keyed by UUID. Uses one row per job; the full request and
change list are serialized as JSON blobs. Connections are created per call so
the store is safe to share across threads (FastAPI worker model).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .base import JobRecord


class SqliteJobStore:
    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    source_a_id TEXT NOT NULL,
                    source_b_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    changes TEXT NOT NULL,
                    request TEXT NOT NULL
                )
                """
            )

    def put(self, record: JobRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    record.job_id,
                    record.timestamp,
                    record.source_a_id,
                    record.source_b_id,
                    json.dumps(record.summary),
                    json.dumps([c.model_dump() for c in record.changes]),
                    json.dumps(record.request),
                ),
            )

    def get(self, job_id: str) -> JobRecord | None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT job_id, timestamp, source_a_id, source_b_id, summary, changes, request "
                "FROM jobs WHERE job_id = ?",
                (job_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return JobRecord(
            job_id=row[0],
            timestamp=row[1],
            source_a_id=row[2],
            source_b_id=row[3],
            summary=json.loads(row[4]),
            changes=json.loads(row[5]),
            request=json.loads(row[6]),
        )
