from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from screen_translator.capture.geometry import ScreenPoint, ScreenRegion


class SelectionOverlay(QWidget):
    selection_finished = Signal(object)
    selection_cancelled = Signal()

    def __init__(self, minimum_selection_size: int) -> None:
        super().__init__()
        self._minimum_selection_size = minimum_selection_size
        self._drag_start: QPoint | None = None
        self._drag_current: QPoint | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def begin_selection(self) -> None:
        self._drag_start = None
        self._drag_current = None
        virtual_geometry = QRect()
        for screen in QGuiApplication.screens():
            virtual_geometry = virtual_geometry.united(screen.geometry())
        self.setGeometry(virtual_geometry)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        self.update()

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 105))

        selection = self._selection_rect()
        if selection.isNull():
            return

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(selection, Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setPen(QPen(QColor(70, 160, 255), 2))
        painter.drawRect(selection.adjusted(1, 1, -1, -1))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
            self._drag_current = self._drag_start
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None:
            self._drag_current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._drag_start is None:
            return

        self._drag_current = event.position().toPoint()
        global_offset = self.geometry().topLeft()
        start = self._drag_start + global_offset
        end = self._drag_current + global_offset
        logical_region = ScreenRegion.from_points(
            ScreenPoint(start.x(), start.y()), ScreenPoint(end.x(), end.y())
        )

        self.hide()
        self._drag_start = None
        self._drag_current = None
        if logical_region.is_large_enough(self._minimum_selection_size):
            screen = QGuiApplication.screenAt(QRect(start, end).normalized().center())
            scale_factor = screen.devicePixelRatio() if screen is not None else 1.0
            self.selection_finished.emit(logical_region.scaled(scale_factor))
        else:
            self.selection_cancelled.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_selection()
            return
        super().keyPressEvent(event)

    def cancel_selection(self) -> None:
        self.hide()
        self._drag_start = None
        self._drag_current = None
        self.selection_cancelled.emit()

    def _selection_rect(self) -> QRect:
        if self._drag_start is None or self._drag_current is None:
            return QRect()
        return QRect(self._drag_start, self._drag_current).normalized()
