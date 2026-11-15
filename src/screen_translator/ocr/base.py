from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class OCRServiceError(RuntimeError):
    """Base error raised by an OCR provider."""


class TextNotFoundError(OCRServiceError):
    """The image contains no meaningful recognized text."""


class OCRService(ABC):
    @abstractmethod
    def recognize(self, image_path: Path) -> str:
        """Return cleaned text recognized in an image."""
        raise NotImplementedError
