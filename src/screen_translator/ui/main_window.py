from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QIcon, QShowEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from screen_translator.storage.models import TranslationRecord


class MainWindow(QMainWindow):
    enabled_changed = Signal(bool)
    refresh_requested = Signal()
    learned_changed = Signal(int, bool)
    clear_history_requested = Signal()
    export_history_requested = Signal(object)

    def __init__(self, app_name: str, hotkey: str, icon: QIcon) -> None:
        super().__init__()
        self._enabled = True
        self.setWindowTitle(app_name)
        self.setWindowIcon(icon)
        self.setMinimumSize(820, 600)
        self.resize(980, 720)

        root = QWidget()
        root.setObjectName("root")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(20, 18, 20, 20)
        root_layout.setSpacing(14)

        heading = QHBoxLayout()
        heading.setSpacing(16)
        app_icon = QLabel()
        app_icon.setObjectName("appIcon")
        app_icon.setPixmap(icon.pixmap(54, 54))
        app_icon.setFixedSize(54, 54)
        title = QLabel(app_name)
        title.setObjectName("appTitle")
        subtitle = QLabel(f"Быстрый перевод текста с экрана · {hotkey}")
        subtitle.setObjectName("subtitle")
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        heading.addWidget(app_icon)
        heading.addLayout(title_block)
        heading.addStretch()
        root_layout.addLayout(heading)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.addTab(self._create_home(hotkey), "Главная")
        self._tabs.addTab(self._create_dictionary(), "Словарь")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        root_layout.addWidget(self._tabs, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(_STYLESHEET)
        self.set_enabled(True)

    def _create_home(self, hotkey: str) -> QWidget:
        page = QWidget()
        page.setObjectName("homePage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(14)

        status_strip = QFrame()
        status_strip.setObjectName("statusStrip")
        status_layout = QHBoxLayout(status_strip)
        status_layout.setContentsMargins(18, 12, 18, 12)
        status_layout.setSpacing(10)
        self._status_dot = QLabel("●")
        self._status_dot.setObjectName("statusDot")
        self._status = QLabel()
        self._status.setObjectName("statusLine")
        self._hotkey_state = QLabel()
        self._hotkey_state.setObjectName("statusDescription")
        keycap = QLabel(f"⌨  {hotkey}")
        keycap.setObjectName("keycap")
        status_layout.addWidget(self._status_dot)
        status_layout.addWidget(self._status)
        status_layout.addWidget(_vertical_separator("statusSeparator"))
        status_layout.addWidget(self._hotkey_state, 1)
        status_layout.addWidget(keycap)
        layout.addWidget(status_strip)

        service_card = QFrame()
        service_card.setObjectName("serviceCard")
        service_layout = QHBoxLayout(service_card)
        service_layout.setContentsMargins(18, 16, 18, 16)
        service_layout.setSpacing(16)
        capture_icon = QLabel("⌗")
        capture_icon.setObjectName("captureIcon")
        capture_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        capture_icon.setFixedSize(48, 48)
        service_text = QVBoxLayout()
        service_text.setSpacing(2)
        self._service_title = QLabel()
        self._service_title.setObjectName("serviceTitle")
        self._service_description = QLabel()
        self._service_description.setObjectName("muted")
        self._service_description.setWordWrap(True)
        service_text.addWidget(self._service_title)
        service_text.addWidget(self._service_description)
        self._toggle = QPushButton()
        self._toggle.setObjectName("toggleButton")
        self._toggle.setMinimumHeight(44)
        self._toggle.clicked.connect(self._request_toggle)
        service_layout.addWidget(capture_icon)
        service_layout.addLayout(service_text, 1)
        service_layout.addWidget(self._toggle)
        layout.addWidget(service_card)

        workflow = QFrame()
        workflow.setObjectName("workflowCard")
        workflow_layout = QVBoxLayout(workflow)
        workflow_layout.setContentsMargins(18, 16, 18, 16)
        workflow_layout.setSpacing(4)
        workflow_title = QLabel("ПОРЯДОК РАБОТЫ")
        workflow_title.setObjectName("eyebrow")
        workflow_layout.addWidget(workflow_title)
        workflow_layout.addSpacing(4)
        steps = (
            ("01", "Включите переводчик", "✓  Готово"),
            ("02", f"Нажмите {hotkey} в любом приложении или окне", "Глобальный хоткей"),
            ("03", "Выделите мышью прямоугольную область экрана с текстом", "Выбор области"),
            ("04", "Дождитесь локального распознавания и перевода", "PaddleOCR"),
            ("05", "Перевод появится рядом с выделенной областью", "Popup"),
        )
        for number, instruction, detail in steps:
            workflow_layout.addLayout(_workflow_row(number, instruction, detail))
        layout.addWidget(workflow)
        layout.addStretch()

        tray_hint = QFrame()
        tray_hint.setObjectName("infoStrip")
        tray_layout = QHBoxLayout(tray_hint)
        tray_layout.setContentsMargins(12, 8, 12, 8)
        tray_text = QLabel(
            "ⓘ  При закрытии окно сворачивается в системный трей Windows"
        )
        tray_text.setObjectName("infoText")
        tray_layout.addWidget(tray_text)
        tray_layout.addStretch()
        tray_layout.addWidget(QLabel("Qt · QSystemTrayIcon"))
        layout.addWidget(tray_hint)
        return page

    def _create_dictionary(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)
        dictionary_header = QHBoxLayout()
        description = QLabel(
            "Все успешные переводы. Нажмите круг справа, когда слово выучено."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        export_button = QPushButton("⇩")
        export_button.setObjectName("exportHistoryButton")
        export_button.setFixedSize(38, 38)
        export_button.setToolTip("Скачать словарь в файл")
        export_button.clicked.connect(self._choose_export_path)
        clear_button = QPushButton("🗑")
        clear_button.setObjectName("clearHistoryButton")
        clear_button.setFixedSize(38, 38)
        clear_button.setToolTip("Очистить словарь")
        clear_button.clicked.connect(self._confirm_clear_history)
        dictionary_header.addWidget(description, 1)
        dictionary_header.addWidget(export_button, 0, Qt.AlignmentFlag.AlignTop)
        dictionary_header.addWidget(clear_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(dictionary_header)
        self._dictionary_tabs = QTabWidget()
        self._dictionary_tabs.setObjectName("dictionaryTabs")
        self._en_list, en_page = _dictionary_page("Пока нет переводов с английского")
        self._ru_list, ru_page = _dictionary_page("Пока нет переводов с русского")
        self._dictionary_tabs.addTab(en_page, "English → Русский")
        self._dictionary_tabs.addTab(ru_page, "Русский → English")
        layout.addWidget(self._dictionary_tabs, 1)
        return page

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self._toggle.blockSignals(True)
        self._toggle.setText("Выключить переводчик" if enabled else "Включить переводчик")
        self._toggle.setProperty("active", enabled)
        self._toggle.style().unpolish(self._toggle)
        self._toggle.style().polish(self._toggle)
        self._toggle.blockSignals(False)
        if enabled:
            self._status_dot.setText("●")
            self._status.setText("Переводчик включён")
            self._hotkey_state.setText(
                "Горячая клавиша активна — можно выделять текст на экране"
            )
            self._service_title.setText("Служба захвата активна")
            self._service_description.setText(
                "Перехват экранных координат и фоновый OCR-процесс запущены"
            )
        else:
            self._status_dot.setText("○")
            self._status.setText("Переводчик выключен")
            self._hotkey_state.setText("Горячая клавиша временно не обрабатывается")
            self._service_title.setText("Служба захвата приостановлена")
            self._service_description.setText(
                "История и словарь доступны; захват экрана отключён"
            )

    def set_records(self, records: Iterable[TranslationRecord]) -> None:
        en_records = [record for record in records if record.source_language == "en"]
        ru_records = [record for record in records if record.source_language == "ru"]
        _fill_dictionary(self._en_list, en_records, self.learned_changed.emit)
        _fill_dictionary(self._ru_list, ru_records, self.learned_changed.emit)
        self._dictionary_tabs.setTabText(0, f"English → Русский  ({len(en_records)})")
        self._dictionary_tabs.setTabText(1, f"Русский → English  ({len(ru_records)})")

    def show_and_activate(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.refresh_requested.emit()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide()
        event.ignore()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.refresh_requested.emit()

    def _on_tab_changed(self, index: int) -> None:
        if index == 1:
            self.refresh_requested.emit()

    def _request_toggle(self) -> None:
        self.enabled_changed.emit(not self._enabled)

    def _confirm_clear_history(self) -> None:
        answer = QMessageBox.question(
            self,
            "Очистить словарь",
            "Точно удалить все переведённые слова?\n\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.clear_history_requested.emit()

    def _choose_export_path(self) -> None:
        suggested_name = f"screen-translator-words-{datetime.now():%Y-%m-%d}.md"
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Скачать словарь",
            suggested_name,
            "Markdown (*.md)",
        )
        if not selected_path:
            return
        output_path = Path(selected_path)
        if output_path.suffix.lower() != ".md":
            output_path = output_path.with_suffix(".md")
        self.export_history_requested.emit(output_path)


def _workflow_row(number: str, instruction: str, detail: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(12)
    number_label = QLabel(number)
    number_label.setObjectName("stepNumber")
    number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    number_label.setFixedSize(30, 28)
    text_label = QLabel(instruction)
    text_label.setObjectName("stepText")
    detail_label = QLabel(detail)
    detail_label.setObjectName("stepDetail")
    detail_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    detail_label.setMinimumWidth(125)
    row.addWidget(number_label)
    row.addWidget(text_label, 1)
    row.addWidget(detail_label)
    return row


def _vertical_separator(name: str) -> QFrame:
    separator = QFrame()
    separator.setObjectName(name)
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setFixedWidth(1)
    return separator


def _dictionary_page(empty_text: str) -> tuple[QVBoxLayout, QWidget]:
    page = QWidget()
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    container = QWidget()
    entries = QVBoxLayout(container)
    entries.setContentsMargins(4, 8, 8, 8)
    entries.setSpacing(10)
    entries.setAlignment(Qt.AlignmentFlag.AlignTop)
    placeholder = QLabel(empty_text)
    placeholder.setObjectName("emptyState")
    placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
    placeholder.setProperty("placeholder", True)
    entries.addWidget(placeholder)
    scroll.setWidget(container)
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(scroll)
    return entries, page


def _fill_dictionary(
    layout: QVBoxLayout,
    records: list[TranslationRecord],
    learned_changed: Callable[[int, bool], None],
) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
    if not records:
        empty = QLabel("Словарь пока пуст")
        empty.setObjectName("emptyState")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(empty)
        return
    for record in records:
        layout.addWidget(_translation_card(record, learned_changed))


def _translation_card(
    record: TranslationRecord, learned_changed: Callable[[int, bool], None]
) -> QFrame:
    card = QFrame()
    card.setObjectName("translationCard")
    card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 13, 16, 12)
    layout.setSpacing(8)

    columns = QGridLayout()
    columns.setContentsMargins(0, 0, 0, 0)
    columns.setHorizontalSpacing(22)
    columns.setColumnStretch(0, 1)
    columns.setColumnStretch(2, 1)
    columns.setColumnMinimumWidth(1, 1)

    source_name = "ENGLISH" if record.source_language == "en" else "РУССКИЙ"
    target_name = "РУССКИЙ" if record.target_language == "ru" else "ENGLISH"
    left = _word_column(source_name, record.original_text, "wordOriginal")
    right = _word_column(target_name, record.translated_text, "wordTranslated")
    divider = _vertical_separator("columnDivider")

    learned = QPushButton("✓" if record.is_learned else "")
    learned.setObjectName("learnedButton")
    learned.setCheckable(True)
    learned.setChecked(record.is_learned)
    learned.setFixedSize(30, 30)
    learned.setToolTip(
        "Снять отметку «Выучено»" if record.is_learned else "Отметить как выученное"
    )
    if record.record_id is None:
        learned.setEnabled(False)
    else:
        learned.toggled.connect(
            lambda checked, button=learned, record_id=record.record_id: (
                button.setText("✓" if checked else ""),
                learned_changed(record_id, checked),
            )
        )

    right_layout = QHBoxLayout()
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(10)
    right_layout.addWidget(right, 1)
    right_layout.addWidget(learned, 0, Qt.AlignmentFlag.AlignTop)
    right_container = QWidget()
    right_container.setLayout(right_layout)

    columns.addWidget(left, 0, 0)
    columns.addWidget(divider, 0, 1)
    columns.addWidget(right_container, 0, 2)
    layout.addLayout(columns)

    date = QLabel(record.created_at.astimezone().strftime("%d.%m.%Y · %H:%M"))
    date.setObjectName("wordDate")
    layout.addWidget(date)
    return card


def _word_column(language: str, text: str, object_name: str) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)
    language_label = QLabel(language)
    language_label.setObjectName("languageLabel")
    word = QLabel(text)
    word.setObjectName(object_name)
    word.setWordWrap(True)
    layout.addWidget(language_label)
    layout.addWidget(word)
    return widget


_STYLESHEET = """
#root { background: #0d0f13; color: #f1f3f4; }
QWidget { color: #f1f3f4; font-family: "Segoe UI"; font-size: 13px; }
#appIcon { background: #5b9cff; border-radius: 9px; }
#appTitle { font-size: 24px; font-weight: 700; }
#subtitle { color: #b8c9eb; font-size: 15px; }
#muted, #wordDate, #stepDetail, #infoStrip QLabel { color: #96a0b4; }
#page { background: #17191f; border: 1px solid #2b3038; border-radius: 10px; }
#homePage { background: transparent; }
#statusStrip, #serviceCard, #workflowCard, #infoStrip {
    background: #1a1d22; border: 1px solid #20242b; border-radius: 5px;
}
#statusLine { font-weight: 700; color: #f1f3f4; }
#statusDot { color: #5b9cff; font-size: 16px; }
#statusDescription { color: #c6d3ed; }
#statusSeparator, #columnDivider { color: #343a45; background: #343a45; }
#keycap { color: #a9c8ff; font-weight: 700; }
#captureIcon { background: #242830; color: #5b9cff; border-radius: 6px;
               font-size: 25px; font-weight: 700; }
#serviceTitle { font-size: 18px; font-weight: 700; }
#eyebrow, #languageLabel { color: #a9c8ff; font-size: 11px; font-weight: 700; }
#stepNumber { background: #252a33; color: #8bb8ff; font-weight: 700; }
#stepText { font-size: 14px; }
#translationCard { background: #202329; border: 1px solid #343943; border-radius: 10px; }
#translationCard:hover { border-color: #5b9cff; }
#wordOriginal { color: #8bb8ff; font-size: 17px; font-weight: 650; }
#wordTranslated { color: #f1f3f4; font-size: 17px; font-weight: 650; }
#wordDate { font-size: 11px; }
#emptyState { color: #777d86; padding: 50px; }
QPushButton { background: #2d6fc4; border: 1px solid #5b9cff; border-radius: 7px;
              padding: 9px 16px; font-weight: 650; }
QPushButton:hover { background: #347fdc; }
#toggleButton[active="true"] { background: #25292f; color: #f1f3f4; border-color: #30353e; }
#learnedButton { background: transparent; border: 2px solid #5b9cff; border-radius: 15px;
                 color: #ffffff; font-size: 16px; padding: 0; }
#learnedButton:hover { background: rgba(91, 156, 255, 45); }
#learnedButton:checked { background: #5b9cff; }
#clearHistoryButton, #exportHistoryButton { background: transparent; color: #5b9cff;
    border: 1px solid #343943; border-radius: 7px; font-size: 18px; padding: 0; }
#clearHistoryButton:hover, #exportHistoryButton:hover {
    background: #252a33; border-color: #5b9cff;
}
QTabWidget::pane { border: none; }
QTabBar::tab { background: transparent; color: #9aa0a6; padding: 10px 18px;
               border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #8bb8ff; border-bottom: 2px solid #5b9cff; }
QTabBar::tab:hover { color: #dbe7ff; }
QScrollArea { background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: #17191f; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #3b424d; border-radius: 5px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
