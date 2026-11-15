from __future__ import annotations

from PySide6.QtCore import QObject, QSignalBlocker, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class TrayController(QObject):
    enabled_changed = Signal(bool)
    settings_requested = Signal()
    show_window_requested = Signal()
    exit_requested = Signal()

    def __init__(self, app_name: str, icon: QIcon) -> None:
        super().__init__()
        self._tray = QSystemTrayIcon(icon, self)
        self._tray.setToolTip(app_name)

        self._menu = QMenu()
        title_action = QAction(app_name, self._menu)
        title_action.setEnabled(False)
        self._menu.addAction(title_action)
        self._menu.addSeparator()

        open_action = QAction("Open", self._menu)
        open_action.triggered.connect(self.show_window_requested)
        self._menu.addAction(open_action)

        self._enabled_action = QAction("Enabled", self._menu)
        self._enabled_action.setCheckable(True)
        self._enabled_action.setChecked(True)
        self._enabled_action.toggled.connect(self.enabled_changed)
        self._menu.addAction(self._enabled_action)

        settings_action = QAction("Settings", self._menu)
        settings_action.triggered.connect(self.settings_requested)
        self._menu.addAction(settings_action)
        self._menu.addSeparator()

        exit_action = QAction("Exit", self._menu)
        exit_action.triggered.connect(self.exit_requested)
        self._menu.addAction(exit_action)

        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)

    def show(self) -> None:
        self._tray.show()

    def show_message(self, title: str, message: str, timeout_ms: int = 2500) -> None:
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, timeout_ms)

    def set_enabled(self, enabled: bool) -> None:
        blocker = QSignalBlocker(self._enabled_action)
        self._enabled_action.setChecked(enabled)
        del blocker

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_window_requested.emit()
