from __future__ import annotations

import asyncio
import logging
from time import perf_counter

from PySide6.QtCore import QObject, Signal, Slot

from screen_translator.core.transcription import english_to_ipa
from screen_translator.translation.base import TranslationError, TranslationService

logger = logging.getLogger(__name__)


class TranslationWorker(QObject):
    succeeded = Signal(int, str, str, float)
    failed = Signal(int, str, float)

    def __init__(self, service: TranslationService) -> None:
        super().__init__()
        self._service = service

    @Slot(int, str, str, str)
    def translate(self, request_id: int, text: str, source: str, target: str) -> None:
        started = perf_counter()
        try:
            translated = asyncio.run(self._service.translate(text, source, target))
        except TranslationError as error:
            logger.exception("Translation provider error")
            self.failed.emit(request_id, error.user_message, perf_counter() - started)
        except Exception:
            logger.exception("Unexpected translation error")
            self.failed.emit(request_id, "Unable to translate", perf_counter() - started)
        else:
            transcription = english_to_ipa(text) if source == "en" else ""
            self.succeeded.emit(
                request_id, translated, transcription, perf_counter() - started
            )
