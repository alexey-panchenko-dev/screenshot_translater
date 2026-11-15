from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from screen_translator.storage.database import TranslationHistoryRepository
from screen_translator.storage.dictionary import TranslationDictionaryWriter
from screen_translator.storage.exporter import export_translations
from screen_translator.storage.models import TranslationRecord

logger = logging.getLogger(__name__)


class HistoryWorker(QObject):
    records_loaded = Signal(object)
    history_changed = Signal()
    export_completed = Signal(object)
    export_failed = Signal(str)

    def __init__(self, database_path: Path, dictionary_path: Path) -> None:
        super().__init__()
        self._repository = TranslationHistoryRepository(database_path)
        self._dictionary = TranslationDictionaryWriter(dictionary_path)

    @Slot(str, str, str, str)
    def record(self, original: str, translated: str, source: str, target: str) -> None:
        try:
            self._repository.initialize()
            record = TranslationRecord(
                original, translated, source, target, datetime.now(UTC)
            )
            self._repository.add(record)
            self._dictionary.append(record)
            self.history_changed.emit()
        except Exception:
            logger.exception("Unable to save translation history")

    @Slot(str, str)
    def mark_saved(self, original: str, target: str) -> None:
        try:
            self._repository.initialize()
            self._repository.mark_latest_saved(original, target)
        except Exception:
            logger.exception("Unable to mark translation as saved")

    @Slot(int, bool)
    def set_learned(self, record_id: int, learned: bool) -> None:
        try:
            self._repository.initialize()
            self._repository.set_learned(record_id, learned)
            self.history_changed.emit()
        except Exception:
            logger.exception("Unable to update learned state")

    @Slot()
    def load_records(self) -> None:
        try:
            self._repository.initialize()
            self.records_loaded.emit(self._repository.list_all())
        except Exception:
            logger.exception("Unable to load translation history")
            self.records_loaded.emit([])

    @Slot()
    def clear_history(self) -> None:
        try:
            self._repository.initialize()
            self._repository.clear_all()
            self._dictionary.clear()
            self.history_changed.emit()
        except Exception:
            logger.exception("Unable to clear translation history")

    @Slot(object)
    def export_history(self, output_path: Path) -> None:
        try:
            self._repository.initialize()
            export_translations(output_path, self._repository.list_all())
            self.export_completed.emit(output_path)
        except Exception:
            logger.exception("Unable to export translation history")
            self.export_failed.emit("Не удалось сохранить файл словаря")
