from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter

from PySide6.QtCore import QObject, Signal, Slot

from screen_translator.ocr.base import OCRService, TextNotFoundError

logger = logging.getLogger(__name__)


class OCRWorker(QObject):
    succeeded = Signal(int, str, float)
    failed = Signal(int, str, float)

    def __init__(self, service: OCRService) -> None:
        super().__init__()
        self._service = service

    @Slot(int, object)
    def recognize(self, request_id: int, image_path_value: object) -> None:
        image_path = Path(image_path_value)
        started_at = perf_counter()
        try:
            text = self._service.recognize(image_path)
        except TextNotFoundError:
            duration = perf_counter() - started_at
            logger.info("OCR found no text in %.3f seconds", duration)
            self.failed.emit(request_id, "Text not found", duration)
        except Exception:
            duration = perf_counter() - started_at
            logger.exception("OCR failed after %.3f seconds", duration)
            self.failed.emit(request_id, "Unable to recognize text", duration)
        else:
            duration = perf_counter() - started_at
            self.succeeded.emit(request_id, text, duration)
