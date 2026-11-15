from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationError(RuntimeError):
    user_message = "Unable to translate"


class TranslationTimeoutError(TranslationError):
    user_message = "Translation timed out"


class TranslationNetworkError(TranslationError):
    user_message = "No internet connection"


class TranslationRateLimitError(TranslationError):
    user_message = "Translation rate limit reached"


class TranslationAuthenticationError(TranslationError):
    user_message = "Invalid translation API key"


class TranslationService(ABC):
    @abstractmethod
    async def translate(
        self, text: str, source_language: str, target_language: str
    ) -> str:
        """Translate text between two language codes."""
