from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from screen_translator.storage.models import TranslationRecord


class TranslationHistoryRepository:
    def __init__(self, database_path: Path) -> None:
        self._path = database_path

    def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                source_language TEXT NOT NULL,
                target_language TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_saved INTEGER NOT NULL DEFAULT 0,
                is_learned INTEGER NOT NULL DEFAULT 0
                )"""
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(translations)")
            }
            if "is_learned" not in columns:
                connection.execute(
                    "ALTER TABLE translations "
                    "ADD COLUMN is_learned INTEGER NOT NULL DEFAULT 0"
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_translations_original "
                "ON translations(original_text, source_language)"
            )

    def add(self, record: TranslationRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO translations "
                "(original_text, translated_text, source_language, target_language, "
                "created_at, is_saved) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.original_text,
                    record.translated_text,
                    record.source_language,
                    record.target_language,
                    record.created_at.isoformat(),
                    int(record.is_saved),
                ),
            )

    def mark_latest_saved(self, original_text: str, target_language: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE translations SET is_saved = 1 WHERE id = ("
                "SELECT id FROM translations WHERE original_text = ? AND target_language = ? "
                "ORDER BY id DESC LIMIT 1)",
                (original_text, target_language),
            )

    def set_learned(self, record_id: int, learned: bool) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE translations SET is_learned = ? WHERE id = ?",
                (int(learned), record_id),
            )

    def clear_all(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM translations")
            connection.execute(
                "DELETE FROM sqlite_sequence WHERE name = 'translations'"
            )
            connection.commit()
            connection.execute("VACUUM")

    def count_original(self, original_text: str, source_language: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM translations "
                "WHERE lower(original_text) = lower(?) AND source_language = ?",
                (original_text, source_language),
            ).fetchone()
        return int(row[0]) if row else 0

    def list_all(self) -> list[TranslationRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, original_text, translated_text, source_language, "
                "target_language, created_at, is_saved, is_learned FROM translations "
                "ORDER BY id DESC"
            ).fetchall()
        return [
            TranslationRecord(
                record_id=row[0],
                original_text=row[1],
                translated_text=row[2],
                source_language=row[3],
                target_language=row[4],
                created_at=datetime.fromisoformat(row[5]),
                is_saved=bool(row[6]),
                is_learned=bool(row[7]),
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=5)
