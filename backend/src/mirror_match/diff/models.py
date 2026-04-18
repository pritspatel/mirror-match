"""Diff data models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChangeType(StrEnum):
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


class CompareConfig(BaseModel):
    """Runtime knobs for the diff engine.

    - `array_keys`: map JSON-Pointer path to the field name used to match
      elements across arrays. Paths without a mapping use positional diff.
    - `numeric_tolerance`: absolute delta below which two numbers are equal.
    - `case_insensitive`: treat string values as equal ignoring ASCII case.
    """

    model_config = ConfigDict(frozen=True)

    array_keys: dict[str, str] = Field(default_factory=dict)
    numeric_tolerance: float = 0.0
    case_insensitive: bool = False
