from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TranslationRecord:
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    created_at: datetime
    is_saved: bool = False
    is_learned: bool = False
    record_id: int | None = None
