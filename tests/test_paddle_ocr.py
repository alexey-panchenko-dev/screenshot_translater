from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image

from screen_translator.ocr.base import TextNotFoundError
from screen_translator.ocr.paddle_ocr import PaddleOCRService


class FakeEngine:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.pages = pages
        self.inputs: list[np.ndarray] = []

    def predict(self, input: np.ndarray) -> list[dict[str, Any]]:  # noqa: A002
        self.inputs.append(input)
        return self.pages


def test_paddle_adapter_extracts_and_cleans_recognized_lines(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    Image.new("RGB", (120, 24), "white").save(image_path)
    engine = FakeEngine([{"rec_texts": [" Hello   world ", " Привет "]}])
    configurations: list[dict[str, Any]] = []

    def factory(**kwargs: Any) -> FakeEngine:
        configurations.append(kwargs)
        return engine

    service = PaddleOCRService(engine_factory=factory)

    assert service.recognize(image_path) == "Hello world Привет"
    assert service.recognize(image_path) == "Hello world Привет"
    assert len(configurations) == 1
    assert configurations[0]["text_detection_model_name"] == "PP-OCRv5_mobile_det"
    assert configurations[0]["text_recognition_model_name"] == "eslav_PP-OCRv5_mobile_rec"
    assert configurations[0]["enable_mkldnn"] is False
    assert len(engine.inputs) == 2
    assert engine.inputs[0].shape[0] == 96
    assert engine.inputs[0].shape[1] > 120


def test_paddle_adapter_reports_empty_result(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    Image.new("RGB", (120, 24), "white").save(image_path)
    service = PaddleOCRService(
        engine_factory=lambda **kwargs: FakeEngine([{"rec_texts": ["---", "..."]}])
    )

    with pytest.raises(TextNotFoundError):
        service.recognize(image_path)
