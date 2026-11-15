from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from screen_translator.capture.geometry import ScreenRegion
from screen_translator.ui.translation_popup import TranslationPopup


def main() -> None:
    app = QApplication([])
    root = Path(__file__).resolve().parents[1]
    popup = TranslationPopup(30_000)
    popup.show_result(
        "Quick transfer",
        "Быстрый перевод",
        "/kwɪk tɹænsfɝ/",
        "en",
        "ru",
        ScreenRegion(100, 100, 300, 80),
        root / "build" / "preview-placeholder.png",
    )

    def save() -> None:
        output = root / "build" / "popup_preview.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        popup.grab().save(str(output))
        app.quit()

    QTimer.singleShot(400, save)
    app.exec()


if __name__ == "__main__":
    main()
