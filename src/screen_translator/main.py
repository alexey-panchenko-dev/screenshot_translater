from __future__ import annotations

import ctypes
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from screen_translator.capture.geometry import ScreenRegion
from screen_translator.capture.hotkeys import GlobalHotkeyService
from screen_translator.capture.screenshot import ScreenshotService
from screen_translator.core.artifacts import remove_capture, remove_stale_captures
from screen_translator.core.pipeline import CapturePipeline
from screen_translator.core.settings import AppSettings, migrate_legacy_history
from screen_translator.ocr.paddle_ocr import PaddleOCRService
from screen_translator.storage.worker import HistoryWorker
from screen_translator.translation.translator import GoogleWebTranslationService
from screen_translator.ui.icon import load_app_icon
from screen_translator.ui.main_window import MainWindow
from screen_translator.ui.overlay import SelectionOverlay
from screen_translator.ui.settings_dialog import SettingsDialog
from screen_translator.ui.translation_popup import TranslationPopup
from screen_translator.ui.tray import TrayController

logger = logging.getLogger(__name__)


def enable_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    try:
        per_monitor_v2 = ctypes.c_void_p(-4)
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(per_monitor_v2):
            return
    except (AttributeError, OSError):
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()


def configure_logging(log_directory: Path) -> None:
    log_directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_directory / "app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


class ApplicationController(QObject):
    _record_history = Signal(str, str, str, str)
    _mark_history_saved = Signal(str, str)
    _load_history = Signal()
    _set_learned = Signal(int, bool)
    _clear_history = Signal()
    _export_history = Signal(object)

    def __init__(
        self, app: QApplication, settings: AppSettings, icon: QIcon
    ) -> None:
        super().__init__()
        self._app = app
        self._settings = settings
        self._enabled = True
        self._capture_generation = 0
        self._stopping = False

        self._overlay = SelectionOverlay(settings.minimum_selection_size)
        self._popup = TranslationPopup(settings.popup_timeout_ms)
        self._settings_dialog = SettingsDialog(settings)
        self._main_window = MainWindow(
            settings.app_name, settings.hotkey_label, icon
        )
        self._pipeline = CapturePipeline(
            ScreenshotService(),
            PaddleOCRService(model_cache_directory=settings.ocr_model_cache_directory),
            GoogleWebTranslationService(),
            settings.debug_screenshot_directory,
        )
        self._tray = TrayController(settings.app_name, icon)
        self._hotkey = GlobalHotkeyService(self)
        self._history_thread = QThread(self)
        self._history_worker = HistoryWorker(
            settings.database_path, settings.dictionary_path
        )
        self._history_worker.moveToThread(self._history_thread)
        self._record_history.connect(self._history_worker.record)
        self._mark_history_saved.connect(self._history_worker.mark_saved)
        self._load_history.connect(self._history_worker.load_records)
        self._set_learned.connect(self._history_worker.set_learned)
        self._clear_history.connect(self._history_worker.clear_history)
        self._export_history.connect(self._history_worker.export_history)
        self._history_worker.records_loaded.connect(self._main_window.set_records)
        self._history_worker.history_changed.connect(
            self._history_worker.load_records
        )
        self._history_worker.export_completed.connect(self._on_export_completed)
        self._history_worker.export_failed.connect(self._on_export_failed)
        self._history_thread.start()

        self._hotkey.activated.connect(self._begin_capture)
        self._hotkey.registration_failed.connect(self._on_hotkey_error)
        self._overlay.selection_finished.connect(self._on_selection_finished)
        self._overlay.selection_cancelled.connect(self._on_selection_cancelled)
        self._pipeline.capture_succeeded.connect(self._on_capture_succeeded)
        self._pipeline.capture_failed.connect(self._on_capture_failed)
        self._pipeline.ocr_succeeded.connect(self._on_ocr_succeeded)
        self._pipeline.ocr_failed.connect(self._on_ocr_failed)
        self._pipeline.translation_started.connect(self._on_translation_started)
        self._pipeline.translation_succeeded.connect(self._on_translation_succeeded)
        self._pipeline.translation_failed.connect(self._on_translation_failed)
        self._tray.enabled_changed.connect(self._set_enabled)
        self._tray.settings_requested.connect(self._settings_dialog.show)
        self._tray.show_window_requested.connect(self._main_window.show_and_activate)
        self._tray.exit_requested.connect(self.stop)
        self._main_window.enabled_changed.connect(self._set_enabled)
        self._main_window.refresh_requested.connect(self._load_history.emit)
        self._main_window.learned_changed.connect(self._set_learned.emit)
        self._main_window.clear_history_requested.connect(self._clear_history.emit)
        self._main_window.export_history_requested.connect(self._export_history.emit)
        self._popup.save_requested.connect(self._on_save_requested)
        self._popup.dismissed.connect(self._delete_screenshot)
        self._app.aboutToQuit.connect(self._shutdown)

    def start(self) -> None:
        logger.info("Starting %s", self._settings.app_name)
        self._tray.show()
        self._hotkey.start()
        self._main_window.show_and_activate()
        self._tray.show_message(
            self._settings.app_name,
            f"Ready — press {self._settings.hotkey_label} to capture",
        )

    def stop(self) -> None:
        if self._stopping:
            return
        self._stopping = True
        logger.info("Application exit requested")
        self._overlay.hide()
        self._main_window.hide()
        self._shutdown()
        self._app.quit()

    def _shutdown(self) -> None:
        self._popup.dismiss()
        if self._hotkey.isRunning():
            self._hotkey.stop()
        self._pipeline.shutdown()
        self._history_thread.quit()
        self._history_thread.wait()

    def _begin_capture(self) -> None:
        logger.info("Hotkey activated")
        if not self._enabled:
            return
        self._capture_generation += 1
        self._pipeline.cancel_pending()
        self._overlay.begin_selection()

    def _on_selection_finished(self, region: ScreenRegion) -> None:
        generation = self._capture_generation

        def capture_if_current() -> None:
            if generation == self._capture_generation:
                self._pipeline.capture(region)

        QTimer.singleShot(self._settings.compositor_delay_ms, capture_if_current)

    def _on_selection_cancelled(self) -> None:
        logger.info("Screen selection cancelled or too small")

    def _on_capture_succeeded(self, output_path: Path, region: ScreenRegion) -> None:
        del region
        self._tray.show_message(
            self._settings.app_name,
            f"Recognizing text in {output_path.name}…",
        )

    def _on_capture_failed(self, message: str) -> None:
        self._tray.show_message(self._settings.app_name, message)

    def _on_ocr_succeeded(
        self, text: str, region: ScreenRegion, image_path: Path
    ) -> None:
        del region, image_path
        preview = " ".join(text.split())
        if len(preview) > 160:
            preview = f"{preview[:157]}…"
        logger.info("Recognized preview: %s", preview)

    def _on_ocr_failed(self, message: str) -> None:
        self._tray.show_message(self._settings.app_name, message)

    def _on_translation_started(self) -> None:
        self._tray.show_message(self._settings.app_name, "Translating…", 1500)

    def _on_translation_succeeded(
        self,
        original: str,
        translated: str,
        transcription: str,
        source: str,
        target: str,
        region: ScreenRegion,
        image_path: Path,
    ) -> None:
        self._record_history.emit(original, translated, source, target)
        self._popup.show_result(
            original,
            translated,
            transcription,
            source,
            target,
            region,
            image_path,
        )

    def _on_translation_failed(self, message: str) -> None:
        self._tray.show_message(self._settings.app_name, message, 5000)

    def _on_save_requested(
        self, original: str, translated: str, source: str, target: str
    ) -> None:
        del translated, source
        self._mark_history_saved.emit(original, target)
        self._tray.show_message(self._settings.app_name, "Saved to history", 1500)

    def _on_hotkey_error(self, message: str) -> None:
        logger.error("Hotkey registration failed: %s", message)
        self._tray.show_message(self._settings.app_name, message, 5000)

    def _on_export_completed(self, output_path: Path) -> None:
        self._tray.show_message(
            self._settings.app_name,
            f"Словарь сохранён: {output_path.name}",
            4000,
        )

    def _on_export_failed(self, message: str) -> None:
        self._tray.show_message(self._settings.app_name, message, 5000)

    def _set_enabled(self, enabled: bool) -> None:
        if enabled == self._enabled:
            return
        self._enabled = enabled
        self._main_window.set_enabled(enabled)
        self._tray.set_enabled(enabled)
        if enabled:
            if not self._hotkey.isRunning():
                self._hotkey.start()
        else:
            self._capture_generation += 1
            self._pipeline.cancel_pending()
            self._overlay.hide()
            self._hotkey.stop()
        logger.info("Capture enabled: %s", enabled)

    def _delete_screenshot(self, image_path: Path) -> None:
        if remove_capture(image_path, self._settings.debug_screenshot_directory):
            logger.info("Screenshot removed: %s", image_path)


def main() -> int:
    enable_windows_dpi_awareness()
    settings = AppSettings()
    migrated_count = migrate_legacy_history(settings)
    configure_logging(settings.log_directory)
    if migrated_count:
        logger.info("Migrated %s persistent history file(s)", migrated_count)
    stale_count = remove_stale_captures(settings.debug_screenshot_directory)
    if stale_count:
        logger.info("Removed %s stale screenshot(s)", stale_count)

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    icon = load_app_icon(settings.icon_path)
    app.setWindowIcon(icon)
    app.setQuitOnLastWindowClosed(False)

    if not TrayController.is_available():
        QMessageBox.critical(None, settings.app_name, "System tray is not available")
        return 1

    controller = ApplicationController(app, settings, icon)
    controller.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
