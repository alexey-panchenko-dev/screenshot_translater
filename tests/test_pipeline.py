from pathlib import Path
from time import sleep

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from screen_translator.capture.geometry import ScreenRegion
from screen_translator.core.pipeline import CapturePipeline
from screen_translator.ocr.base import OCRService
from screen_translator.translation.base import TranslationService

_APP = QCoreApplication.instance() or QCoreApplication([])


class FakeScreenshotService:
    def __init__(self, result: Path) -> None:
        self.result = result
        self.calls: list[tuple[ScreenRegion, Path]] = []

    def capture_to_file(self, region: ScreenRegion, output_directory: Path) -> Path:
        self.calls.append((region, output_directory))
        return self.result


class BrokenScreenshotService:
    def capture_to_file(self, region: ScreenRegion, output_directory: Path) -> Path:
        del region, output_directory
        raise OSError("capture unavailable")


class FakeOCRService(OCRService):
    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay
        self.calls: list[Path] = []

    def recognize(self, image_path: Path) -> str:
        self.calls.append(image_path)
        if self.delay:
            sleep(self.delay)
        return image_path.stem


class FakeTranslationService(TranslationService):
    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        return f"translated:{text}:{source_language}:{target_language}"


def test_pipeline_emits_saved_path(tmp_path: Path) -> None:
    result = tmp_path / "capture.png"
    service = FakeScreenshotService(result)
    pipeline = CapturePipeline(
        service, FakeOCRService(), FakeTranslationService(), tmp_path  # type: ignore[arg-type]
    )
    emitted: list[tuple[Path, ScreenRegion]] = []
    pipeline.capture_succeeded.connect(lambda path, region: emitted.append((path, region)))
    region = ScreenRegion(10, 20, 300, 100)

    pipeline.capture(region)

    assert service.calls == [(region, tmp_path)]
    assert emitted == [(result, region)]
    pipeline.shutdown()


def test_pipeline_converts_capture_exception_to_user_error(tmp_path: Path) -> None:
    pipeline = CapturePipeline(
        BrokenScreenshotService(),
        FakeOCRService(),
        FakeTranslationService(),
        tmp_path,  # type: ignore[arg-type]
    )
    errors: list[str] = []
    pipeline.capture_failed.connect(errors.append)

    pipeline.capture(ScreenRegion(0, 0, 100, 100))

    assert errors == ["Unable to capture the selected area"]
    pipeline.shutdown()


def test_pipeline_keeps_only_latest_pending_ocr_request(tmp_path: Path) -> None:
    class RegionScreenshotService:
        def capture_to_file(
            self, region: ScreenRegion, output_directory: Path
        ) -> Path:
            return output_directory / f"{region.left}.png"

    ocr_service = FakeOCRService(delay=0.05)
    pipeline = CapturePipeline(
        RegionScreenshotService(),
        ocr_service,
        FakeTranslationService(),
        tmp_path,  # type: ignore[arg-type]
    )
    results: list[str] = []
    loop = QEventLoop()

    def collect(text: str, region: ScreenRegion, image_path: Path) -> None:
        del region, image_path
        results.append(text)
        loop.quit()

    pipeline.ocr_succeeded.connect(collect)
    pipeline.capture(ScreenRegion(1, 0, 100, 100))
    pipeline.capture(ScreenRegion(2, 0, 100, 100))
    pipeline.capture(ScreenRegion(3, 0, 100, 100))
    QTimer.singleShot(2_000, loop.quit)
    loop.exec()
    pipeline.shutdown()

    assert results == ["3"]
    assert [path.stem for path in ocr_service.calls] == ["1", "3"]
