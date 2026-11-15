from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from screen_translator.capture.geometry import ScreenRegion
from screen_translator.capture.screenshot import ScreenshotService
from screen_translator.core.artifacts import remove_capture
from screen_translator.core.language import LanguageDetectionError, detect_language, target_language
from screen_translator.ocr.base import OCRService
from screen_translator.ocr.worker import OCRWorker
from screen_translator.translation.base import TranslationService
from screen_translator.translation.worker import TranslationWorker

logger = logging.getLogger(__name__)


class CapturePipeline(QObject):
    """Coordinate screenshot capture and a single replaceable OCR workload."""

    capture_succeeded = Signal(Path, object)
    capture_failed = Signal(str)
    ocr_succeeded = Signal(str, object, Path)
    ocr_failed = Signal(str)
    translation_started = Signal()
    translation_succeeded = Signal(str, str, str, str, str, object, Path)
    translation_failed = Signal(str)
    _ocr_requested = Signal(int, object)
    _translation_requested = Signal(int, str, str, str)

    def __init__(
        self,
        screenshot_service: ScreenshotService,
        ocr_service: OCRService,
        translation_service: TranslationService,
        output_directory: Path,
    ) -> None:
        super().__init__()
        self._screenshot_service = screenshot_service
        self._output_directory = output_directory
        self._generation = 0
        self._busy = False
        self._accepting_work = True
        self._active_context: tuple[int, Path, ScreenRegion] | None = None
        self._pending_context: tuple[int, Path, ScreenRegion] | None = None
        self._translation_busy = False
        self._active_translation: tuple[int, str, str, str, Path, ScreenRegion] | None = None
        self._pending_translation: tuple[int, str, str, str, Path, ScreenRegion] | None = None

        self._ocr_thread = QThread(self)
        self._ocr_worker = OCRWorker(ocr_service)
        self._ocr_worker.moveToThread(self._ocr_thread)
        self._ocr_requested.connect(self._ocr_worker.recognize)
        self._ocr_worker.succeeded.connect(self._on_ocr_succeeded)
        self._ocr_worker.failed.connect(self._on_ocr_failed)
        self._ocr_thread.start()

        self._translation_thread = QThread(self)
        self._translation_worker = TranslationWorker(translation_service)
        self._translation_worker.moveToThread(self._translation_thread)
        self._translation_requested.connect(self._translation_worker.translate)
        self._translation_worker.succeeded.connect(self._on_translation_succeeded)
        self._translation_worker.failed.connect(self._on_translation_failed)
        self._translation_thread.start()

    def capture(self, region: ScreenRegion) -> None:
        if not self._accepting_work:
            return
        self._generation += 1
        request_id = self._generation
        logger.info("Capturing screen region %sx%s", region.width, region.height)
        try:
            output_path = self._screenshot_service.capture_to_file(
                region, self._output_directory
            )
        except Exception:
            logger.exception("Screen capture failed")
            self.capture_failed.emit("Unable to capture the selected area")
            return

        logger.info("Screenshot saved to %s", output_path)
        self.capture_succeeded.emit(output_path, region)
        self._queue_ocr((request_id, output_path, region))

    def cancel_pending(self) -> None:
        self._generation += 1
        if self._pending_context is not None:
            self._remove_image(self._pending_context[1])
        if self._pending_translation is not None:
            self._remove_image(self._pending_translation[4])
        self._pending_context = None
        self._pending_translation = None

    def shutdown(self) -> None:
        if not self._accepting_work:
            return
        self._accepting_work = False
        self.cancel_pending()
        self._ocr_thread.quit()
        self._ocr_thread.wait()
        self._translation_thread.quit()
        self._translation_thread.wait()
        if self._active_context is not None:
            self._remove_image(self._active_context[1])
        if self._active_translation is not None:
            self._remove_image(self._active_translation[4])

    def _queue_ocr(self, context: tuple[int, Path, ScreenRegion]) -> None:
        if self._busy:
            if self._pending_context is not None:
                self._remove_image(self._pending_context[1])
            self._pending_context = context
            logger.info("Replaced pending OCR request with generation %s", context[0])
            return
        self._dispatch_ocr(context)

    def _dispatch_ocr(self, context: tuple[int, Path, ScreenRegion]) -> None:
        request_id, image_path, _ = context
        self._busy = True
        self._active_context = context
        self._ocr_requested.emit(request_id, image_path)

    def _on_ocr_succeeded(self, request_id: int, text: str, duration: float) -> None:
        context = self._complete_active_request(request_id)
        logger.info("OCR completed in %.3f seconds", duration)
        if context is not None and request_id == self._generation:
            _, image_path, region = context
            logger.info("OCR text: %s", text)
            self.ocr_succeeded.emit(text, region, image_path)
            try:
                source = detect_language(text)
                target = target_language(source)
            except LanguageDetectionError as error:
                self.translation_failed.emit(str(error))
                self._remove_image(image_path)
            else:
                self._queue_translation(
                    (request_id, text, source, target, image_path, region)
                )
        elif context is not None:
            self._remove_image(context[1])
        self._dispatch_latest_pending()

    def _on_ocr_failed(self, request_id: int, message: str, duration: float) -> None:
        context = self._complete_active_request(request_id)
        logger.info("OCR request finished with an error in %.3f seconds", duration)
        if context is not None and request_id == self._generation:
            self.ocr_failed.emit(message)
        if context is not None:
            self._remove_image(context[1])
        self._dispatch_latest_pending()

    def _complete_active_request(
        self, request_id: int
    ) -> tuple[int, Path, ScreenRegion] | None:
        context = self._active_context
        if context is None or context[0] != request_id:
            logger.warning("Ignoring unexpected OCR result for generation %s", request_id)
            return None
        self._busy = False
        self._active_context = None
        return context

    def _dispatch_latest_pending(self) -> None:
        context = self._pending_context
        self._pending_context = None
        if (
            self._accepting_work
            and context is not None
            and context[0] == self._generation
        ):
            self._dispatch_ocr(context)

    def _queue_translation(
        self, context: tuple[int, str, str, str, Path, ScreenRegion]
    ) -> None:
        if self._translation_busy:
            if self._pending_translation is not None:
                self._remove_image(self._pending_translation[4])
            self._pending_translation = context
            return
        self._dispatch_translation(context)

    def _dispatch_translation(
        self, context: tuple[int, str, str, str, Path, ScreenRegion]
    ) -> None:
        request_id, text, source, target, _, _ = context
        self._translation_busy = True
        self._active_translation = context
        self.translation_started.emit()
        self._translation_requested.emit(request_id, text, source, target)

    def _on_translation_succeeded(
        self, request_id: int, translated: str, transcription: str, duration: float
    ) -> None:
        context = self._complete_translation(request_id)
        logger.info("Translation completed in %.3f seconds", duration)
        if context is not None and request_id == self._generation:
            _, original, source, target, image_path, region = context
            logger.info("Translation result: %s", translated)
            self.translation_succeeded.emit(
                original,
                translated,
                transcription,
                source,
                target,
                region,
                image_path,
            )
        elif context is not None:
            self._remove_image(context[4])
        self._dispatch_latest_translation()

    def _on_translation_failed(
        self, request_id: int, message: str, duration: float
    ) -> None:
        context = self._complete_translation(request_id)
        logger.info("Translation failed in %.3f seconds", duration)
        if context is not None and request_id == self._generation:
            self.translation_failed.emit(message)
        if context is not None:
            self._remove_image(context[4])
        self._dispatch_latest_translation()

    def _complete_translation(
        self, request_id: int
    ) -> tuple[int, str, str, str, Path, ScreenRegion] | None:
        context = self._active_translation
        if context is None or context[0] != request_id:
            return None
        self._translation_busy = False
        self._active_translation = None
        return context

    def _dispatch_latest_translation(self) -> None:
        context = self._pending_translation
        self._pending_translation = None
        if self._accepting_work and context is not None and context[0] == self._generation:
            self._dispatch_translation(context)

    def _remove_image(self, image_path: Path) -> None:
        remove_capture(image_path, self._output_directory)
