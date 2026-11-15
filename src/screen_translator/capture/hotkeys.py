from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MOD_ALT = 0x0001
MOD_NOREPEAT = 0x4000
HOTKEY_ID = 1


class GlobalHotkeyService(QThread):
    """Listen for Alt+Q using the native Windows message queue."""

    activated = Signal()
    registration_failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread_id: int | None = None

    def run(self) -> None:
        if sys.platform != "win32":
            self.registration_failed.emit("Global hotkeys are supported only on Windows.")
            return

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = int(kernel32.GetCurrentThreadId())

        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_ALT | MOD_NOREPEAT, ord("Q")):
            error_code = ctypes.get_last_error()
            logger.error("RegisterHotKey failed with Windows error %s", error_code)
            self.registration_failed.emit(
                "Alt+Q is already in use by another application."
            )
            self._thread_id = None
            return

        logger.info("Global hotkey Alt+Q registered")
        message = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
                    self.activated.emit()
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)
            self._thread_id = None
            logger.info("Global hotkey unregistered")

    def stop(self) -> None:
        if self._thread_id is not None and sys.platform == "win32":
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        self.wait(2_000)
