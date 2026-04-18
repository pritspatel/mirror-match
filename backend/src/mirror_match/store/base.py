"""Job store protocol."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from ..diff.models import FieldChange


class JobRecord(BaseModel):
    job_id: str
    timestamp: str
    source_a_id: str
    source_b_id: str
    summary: dict[str, int]
    changes: list[FieldChange]
    request: dict[str, Any]


class JobStore(Protocol):
    def put(self, record: JobRecord) -> None: ...
    def get(self, job_id: str) -> JobRecord | None: ...
