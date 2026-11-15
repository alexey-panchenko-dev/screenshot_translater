from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QEnterEvent, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from screen_translator.capture.geometry import ScreenRegion


class TranslationPopup(QWidget):
    save_requested = Signal(str, str, str, str)
    dismissed = Signal(Path)

    def __init__(self, timeout_ms: int) -> None:
        super().__init__()
        self._timeout_ms = timeout_ms
        self._languages = ("", "")
        self._image_path: Path | None = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        frame = QFrame(self)
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 12)
        layout.setSpacing(8)
        self._original = QLabel()
        self._original.setWordWrap(True)
        self._original.setObjectName("original")
        self._transcription = QLabel()
        self._transcription.setWordWrap(True)
        self._transcription.setObjectName("transcription")
        self._transcription.hide()
        self._translation = QLabel()
        self._translation.setWordWrap(True)
        self._translation.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._translation.setObjectName("translation")
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(28, 28)
        close_button.setToolTip("Close")
        close_button.clicked.connect(self.dismiss)
        header = QHBoxLayout()
        header.addWidget(self._original, 1)
        header.addWidget(close_button, 0, Qt.AlignmentFlag.AlignTop)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        buttons = QHBoxLayout()
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self._copy_translation)
        save_button = QPushButton("☆ Save")
        save_button.clicked.connect(self._save)
        buttons.addWidget(copy_button)
        buttons.addStretch()
        buttons.addWidget(save_button)
        layout.addLayout(header)
        layout.addWidget(self._transcription)
        layout.addWidget(separator)
        layout.addWidget(self._translation)
        layout.addLayout(buttons)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.addWidget(frame)
        self.setFixedWidth(420)
        self.setStyleSheet(
            "#card {background:#202124; border:1px solid #3c4043; border-radius:12px;}"
            "QLabel {color:#f1f3f4;}"
            "#original {color:#5b9cff; font-size:16px; font-weight:600;}"
            "#transcription {color:#8f969f; font-size:12px; font-style:italic;}"
            "#translation {color:#f1f3f4; font-size:16px; font-weight:600;}"
            "QPushButton {color:#8ab4f8; border:none; padding:5px 8px;}"
            "QPushButton:hover {background:#303134; border-radius:5px;}"
            "#closeButton {color:#bdc1c6; font-size:22px; padding:0;}"
            "#closeButton:hover {color:#ffffff; background:#3c4043; border-radius:14px;}"
        )
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)

    def show_result(
        self,
        original: str,
        translation: str,
        transcription: str,
        source: str,
        target: str,
        physical_region: ScreenRegion,
        image_path: Path,
    ) -> None:
        self._release_image()
        self._image_path = image_path
        self._original.setText(original)
        self._transcription.setText(transcription)
        self._transcription.setVisible(bool(transcription) and source == "en")
        self._translation.setText(translation)
        self._languages = (source, target)
        self.adjustSize()

        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            scale = screen.devicePixelRatio()
            available = screen.availableGeometry()
            preferred_x = round((physical_region.left + physical_region.width) / scale) + 10
            preferred_y = round(physical_region.top / scale)
            if preferred_x + self.width() > available.right():
                preferred_x = round(physical_region.left / scale) - self.width() - 10
            x = max(available.left(), min(preferred_x, available.right() - self.width()))
            y = max(available.top(), min(preferred_y, available.bottom() - self.height()))
            self.move(x, y)
        self.show()
        self.raise_()
        self._timer.start(self._timeout_ms)

    def dismiss(self) -> None:
        self._timer.stop()
        self.hide()
        self._release_image()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._timer.stop()
        self._release_image()
        event.accept()

    def enterEvent(self, event: QEnterEvent) -> None:
        self._timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._timer.start(self._timeout_ms)
        super().leaveEvent(event)

    def _copy_translation(self) -> None:
        QApplication.clipboard().setText(self._translation.text())
        self._timer.start(self._timeout_ms)

    def _save(self) -> None:
        source, target = self._languages
        self.save_requested.emit(
            self._original.text(), self._translation.text(), source, target
        )
        self._timer.start(self._timeout_ms)

    def _release_image(self) -> None:
        image_path = self._image_path
        self._image_path = None
        if image_path is not None:
            self.dismissed.emit(image_path)
