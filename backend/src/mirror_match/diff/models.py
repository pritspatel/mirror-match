"""Diff data models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChangeType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"


class FieldChange(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    change_type: ChangeType
    value_a: Any = None
    value_b: Any = None


class DiffSummary(BaseModel):
    added: int
    removed: int
    modified: int
    total: int
