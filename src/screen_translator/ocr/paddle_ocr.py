from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps

from screen_translator.ocr.base import OCRService, OCRServiceError, TextNotFoundError
from screen_translator.ocr.text import cleanup_text, has_meaningful_text

logger = logging.getLogger(__name__)


class PaddleOCRService(OCRService):
    """Lazy, reusable PaddleOCR adapter configured for Russian and English."""

    def __init__(
        self,
        language: str = "ru",
        score_threshold: float = 0.5,
        model_cache_directory: Path | None = None,
        engine_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._language = language
        self._score_threshold = score_threshold
        self._model_cache_directory = model_cache_directory
        self._engine_factory = engine_factory
        self._engine: Any | None = None

    def recognize(self, image_path: Path) -> str:
        if not image_path.is_file():
            raise OCRServiceError(f"Image does not exist: {image_path}")

        try:
            prepared_image = self._prepare_image(image_path)
            pages = self._get_engine().predict(input=prepared_image)
            raw_text = "\n".join(self._extract_text_lines(pages))
        except OCRServiceError:
            raise
        except Exception as error:
            raise OCRServiceError("PaddleOCR failed to process the image") from error

        text = cleanup_text(raw_text)
        if not has_meaningful_text(text):
            raise TextNotFoundError("Text not found")
        return text

    @staticmethod
    def _prepare_image(image_path: Path) -> np.ndarray:
        with Image.open(image_path) as source:
            image = source.convert("RGB")

        pixels = np.asarray(image)
        edge_pixels = np.concatenate(
            (pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]), axis=0
        )
        background = tuple(int(channel) for channel in np.median(edge_pixels, axis=0))
        padding = max(12, min(48, round(min(image.size) * 0.2)))
        prepared = ImageOps.expand(image, border=padding, fill=background)

        if prepared.height < 96:
            scale = 96 / prepared.height
            prepared = prepared.resize(
                (round(prepared.width * scale), 96), Image.Resampling.LANCZOS
            )

        logger.debug(
            "Prepared OCR image from %sx%s to %sx%s",
            image.width,
            image.height,
            prepared.width,
            prepared.height,
        )
        # Paddle's ndarray input follows OpenCV's BGR channel order.
        return np.asarray(prepared)[:, :, ::-1].copy()

    def _get_engine(self) -> Any:
        if self._engine is None:
            logger.info("Initializing PaddleOCR model for language %s", self._language)
            factory = self._engine_factory or self._import_engine_factory()
            self._engine = factory(
                device="cpu",
                enable_mkldnn=False,
                text_detection_model_name="PP-OCRv5_mobile_det",
                text_recognition_model_name=self._recognition_model_name(),
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                text_rec_score_thresh=self._score_threshold,
            )
        return self._engine

    def _recognition_model_name(self) -> str:
        if self._language == "ru":
            # The Eastern Slavic model recognizes Cyrillic and embedded English text.
            return "eslav_PP-OCRv5_mobile_rec"
        if self._language == "en":
            return "en_PP-OCRv5_mobile_rec"
        raise OCRServiceError(f"Unsupported OCR language: {self._language}")

    def _import_engine_factory(self) -> Callable[..., Any]:
        if self._model_cache_directory is not None:
            self._model_cache_directory.mkdir(parents=True, exist_ok=True)
            os.environ["PADDLE_PDX_CACHE_HOME"] = str(self._model_cache_directory)
        try:
            from paddleocr import PaddleOCR
        except ImportError as error:
            raise OCRServiceError(
                "PaddleOCR is not installed. Use the project's Python 3.12 environment."
            ) from error
        return PaddleOCR

    @staticmethod
    def _extract_text_lines(pages: Iterable[Any]) -> list[str]:
        lines: list[str] = []
        for page in pages:
            if not isinstance(page, Mapping):
                continue
            recognized = page.get("rec_texts", [])
            if not isinstance(recognized, Iterable) or isinstance(recognized, str):
                continue
            lines.extend(text for text in recognized if isinstance(text, str) and text.strip())
        return lines
