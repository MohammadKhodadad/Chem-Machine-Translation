from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    dataset: str
    source_id: str
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class TranslationResult:
    document: Document
    source_language: str
    target_language: str
    translated_text: str
    strategy: str
    model: str | None = None
    approved: bool | None = None
    review_rounds: int = 0
    review_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TranslationReview:
    approved: bool
    issues: list[str]
    required_changes: list[str]
    rationale: str
