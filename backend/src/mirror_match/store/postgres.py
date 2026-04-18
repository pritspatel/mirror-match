"""Postgres-backed job store.

Activated when `MIRROR_MATCH_DB_URL` starts with `postgres://` or
`postgresql://`. Requires the optional `psycopg[binary]` dependency.

Design mirrors `SqliteJobStore`: one row per job, JSON blobs for summary /
changes / request. Uses `jsonb` columns so ad-hoc queries (`SELECT
request->'source_a'->>'type' ...`) stay ergonomic.
"""

from __future__ import annotations

import json
from typing import Any

from .base import JobRecord


class PostgresJobStore:
    def __init__(self, dsn: str) -> None:
        try:
            import psycopg  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "Postgres job store requires the `postgres` extra: "
                "pip install 'mirror-match[postgres]'"
            ) from e
        self._dsn = dsn
        self._init_schema()

    def _connect(self) -> Any:
        import psycopg

        return psycopg.connect(self._dsn)

    def _init_schema(self) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    source_a_id TEXT NOT NULL,
                    source_b_id TEXT NOT NULL,
                    summary JSONB NOT NULL,
                    changes JSONB NOT NULL,
                    request JSONB NOT NULL
                )
                """
            )

    def put(self, record: JobRecord) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs (job_id, timestamp, source_a_id, source_b_id,
                                  summary, changes, request)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
                ON CONFLICT (job_id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    source_a_id = EXCLUDED.source_a_id,
                    source_b_id = EXCLUDED.source_b_id,
                    summary = EXCLUDED.summary,
                    changes = EXCLUDED.changes,
                    request = EXCLUDED.request
                """,
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
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT job_id, timestamp, source_a_id, source_b_id, "
                "summary, changes, request FROM jobs WHERE job_id = %s",
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
            summary=row[4],
            changes=row[5],
            request=row[6],
        )
