from __future__ import annotations

from datetime import datetime
from pathlib import Path

from screen_translator.storage.models import TranslationRecord


class TranslationDictionaryWriter:
    """Append successful translations to a human-readable Markdown dictionary."""

    _HEADER = "# Screen Translator — словарь\n\n"

    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, record: TranslationRecord) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists() or self._path.stat().st_size == 0:
            self._path.write_text(self._HEADER, encoding="utf-8")
        timestamp = _format_time(record.created_at)
        original = _single_line(record.original_text)
        translated = _single_line(record.translated_text)
        entry = (
            f"## {original}\n\n"
            f"- **Перевод:** {translated}\n"
            f"- **Направление:** {record.source_language.upper()} → "
            f"{record.target_language.upper()}\n"
            f"- **Добавлено:** {timestamp}\n\n"
        )
        with self._path.open("a", encoding="utf-8", newline="\n") as dictionary:
            dictionary.write(entry)

    def clear(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(self._HEADER, encoding="utf-8")


def _single_line(text: str) -> str:
    return " ".join(text.split())


def _format_time(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")
