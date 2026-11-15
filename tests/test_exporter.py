from datetime import UTC, datetime
from pathlib import Path

from screen_translator.storage.exporter import export_translations
from screen_translator.storage.models import TranslationRecord


def test_export_translations_creates_ai_readable_markdown(tmp_path: Path) -> None:
    output = tmp_path / "words.md"
    records = [
        TranslationRecord(
            "screen | translator",
            "экранный переводчик",
            "en",
            "ru",
            datetime(2026, 11, 15, 12, 30, tzinfo=UTC),
            is_learned=True,
        ),
        TranslationRecord(
            "словарь",
            "dictionary",
            "ru",
            "en",
            datetime(2026, 11, 15, 12, 31, tzinfo=UTC),
        ),
    ]

    export_translations(output, records)

    text = output.read_text(encoding="utf-8")
    assert "## EN → RU" in text
    assert "## RU → EN" in text
    assert "| Выучено | screen \\| translator | экранный переводчик |" in text
    assert "| Изучаю | словарь | dictionary |" in text
