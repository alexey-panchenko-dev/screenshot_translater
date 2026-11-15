from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from screen_translator.core.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.setWindowTitle(f"{settings.app_name} — Settings")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(330)
        form = QFormLayout()
        form.addRow("Hotkey", QLabel(settings.hotkey_label))
        form.addRow("Popup timeout", QLabel(f"{settings.popup_timeout_ms / 1000:g} sec"))
        form.addRow("Languages", QLabel("Russian ⇄ English"))
        startup = QCheckBox("Launch on Windows startup")
        startup.setChecked(False)
        startup.setEnabled(False)
        startup.setToolTip("Startup integration will be enabled with the packaged application")
        form.addRow("Startup", startup)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)
