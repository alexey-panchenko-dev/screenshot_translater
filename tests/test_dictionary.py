from datetime import UTC, datetime
from pathlib import Path

from screen_translator.storage.dictionary import TranslationDictionaryWriter
from screen_translator.storage.models import TranslationRecord


def test_dictionary_is_readable_and_appends_entries(tmp_path: Path) -> None:
    path = tmp_path / "dictionary.md"
    writer = TranslationDictionaryWriter(path)
    writer.append(
        TranslationRecord(
            "screen\ntranslator",
            "переводчик экрана",
            "en",
            "ru",
            datetime(2026, 11, 15, 1, 2, 3, tzinfo=UTC),
        )
    )
    writer.append(
        TranslationRecord(
            "нормально",
            "fine",
            "ru",
            "en",
            datetime(2026, 11, 15, 1, 3, 4, tzinfo=UTC),
        )
    )

    text = path.read_text(encoding="utf-8")
    assert text.count("# Screen Translator — словарь") == 1
    assert "## screen translator" in text
    assert "**Перевод:** переводчик экрана" in text
    assert "RU → EN" in text
    assert "## нормально" in text

    writer.clear()
    assert path.read_text(encoding="utf-8") == "# Screen Translator — словарь\n\n"
