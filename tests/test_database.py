import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from screen_translator.storage.database import TranslationHistoryRepository
from screen_translator.storage.models import TranslationRecord


def test_database_saves_counts_and_marks_translation(tmp_path: Path) -> None:
    repository = TranslationHistoryRepository(tmp_path / "history.db")
    repository.initialize()
    repository.add(
        TranslationRecord("although", "хотя", "en", "ru", datetime.now(UTC))
    )
    repository.add(
        TranslationRecord("Although", "хотя", "en", "ru", datetime.now(UTC))
    )

    assert repository.count_original("although", "en") == 2
    repository.mark_latest_saved("Although", "ru")

    with repository._connect() as connection:  # noqa: SLF001
        saved = connection.execute(
            "SELECT is_saved FROM translations ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert saved == (1,)
    records = repository.list_all()
    assert [record.original_text for record in records] == ["Although", "although"]
    assert records[0].is_saved
    assert records[0].record_id is not None
    repository.set_learned(records[0].record_id, True)
    assert repository.list_all()[0].is_learned
    repository.clear_all()
    assert repository.list_all() == []


def test_database_migrates_existing_history(tmp_path: Path) -> None:
    database_path = tmp_path / "old-history.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TABLE translations ("
            "id INTEGER PRIMARY KEY, original_text TEXT, translated_text TEXT, "
            "source_language TEXT, target_language TEXT, created_at TEXT, "
            "is_saved INTEGER NOT NULL DEFAULT 0)"
        )

    repository = TranslationHistoryRepository(database_path)
    repository.initialize()
    with repository._connect() as connection:  # noqa: SLF001
        columns = {row[1] for row in connection.execute("PRAGMA table_info(translations)")}
    assert "is_learned" in columns
