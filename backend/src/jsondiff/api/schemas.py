"""API request/response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..diff.models import DiffSummary, FieldChange


class RawSource(BaseModel):
    type: Literal["raw"]
    data: Any
    identifier: str | None = None


SourceConfig = RawSource  # v0.1 — raw only; extended in v0.2 (ES, HTTP).


class CompareOptions(BaseModel):
    ignore_paths: list[str] = Field(default_factory=list)


class CompareRequest(BaseModel):
    source_a: SourceConfig
    source_b: SourceConfig
    options: CompareOptions = Field(default_factory=CompareOptions)


class CompareResponse(BaseModel):
    job_id: str
    timestamp: str
    source_a_id: str
    source_b_id: str
    summary: DiffSummary
    changes: list[FieldChange]
