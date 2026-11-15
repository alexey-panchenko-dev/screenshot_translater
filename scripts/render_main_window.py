from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from screen_translator.storage.models import TranslationRecord
from screen_translator.ui.icon import load_app_icon
from screen_translator.ui.main_window import MainWindow


def main() -> None:
    app = QApplication([])
    root = Path(__file__).resolve().parents[1]
    window = MainWindow(
        "Screen Translator",
        "Alt+Q",
        load_app_icon(root / "assets" / "screen_translator.ico"),
    )
    now = datetime.now(UTC)
    window.set_records(
        [
            TranslationRecord(
                "screen", "экран", "en", "ru", now, is_learned=True, record_id=1
            ),
            TranslationRecord(
                "translator", "переводчик", "en", "ru", now, record_id=2
            ),
            TranslationRecord("нормально", "fine", "ru", "en", now, record_id=3),
        ]
    )
    window.show()

    def save() -> None:
        output_directory = root / "build"
        output_directory.mkdir(parents=True, exist_ok=True)
        window._tabs.setCurrentIndex(0)  # noqa: SLF001
        QApplication.processEvents()
        window.grab().save(str(output_directory / "home_preview.png"))
        window._tabs.setCurrentIndex(1)  # noqa: SLF001
        QApplication.processEvents()
        window.grab().save(str(output_directory / "dictionary_preview.png"))
        app.quit()

    QTimer.singleShot(700, save)
    app.exec()


if __name__ == "__main__":
    main()
