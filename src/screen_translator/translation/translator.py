from __future__ import annotations

import html

import httpx

from screen_translator.translation.base import (
    TranslationAuthenticationError,
    TranslationError,
    TranslationNetworkError,
    TranslationRateLimitError,
    TranslationService,
    TranslationTimeoutError,
)


class GoogleWebTranslationService(TranslationService):
    """Keyless Google web endpoint adapter for short interactive translations."""

    def __init__(
        self,
        endpoint: str = "https://translate.googleapis.com/translate_a/single",
        timeout_seconds: float = 8.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._timeout = timeout_seconds
        self._transport = transport

    async def translate(
        self, text: str, source_language: str, target_language: str
    ) -> str:
        if not text.strip():
            raise TranslationError("Empty translation request")
        if len(text) > 5_000:
            raise TranslationError("Selected text is too long")
        params = {
            "client": "gtx",
            "sl": source_language,
            "tl": target_language,
            "dt": "t",
            "q": text,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(self._endpoint, params=params)
        except httpx.TimeoutException as error:
            raise TranslationTimeoutError from error
        except httpx.NetworkError as error:
            raise TranslationNetworkError from error
        if response.status_code == 429:
            raise TranslationRateLimitError
        if response.status_code >= 400:
            raise TranslationError(f"Translation API returned HTTP {response.status_code}")
        try:
            translated = "".join(
                segment[0] for segment in response.json()[0] if segment and segment[0]
            )
        except (IndexError, TypeError, ValueError) as error:
            raise TranslationError("Invalid translation API response") from error
        if not translated.strip():
            raise TranslationError("Translation API returned an empty result")
        return html.unescape(translated).strip()


class MyMemoryTranslationService(TranslationService):
    """Keyless MyMemory REST provider for short screen-text segments."""

    def __init__(
        self,
        endpoint: str = "https://api.mymemory.translated.net/get",
        timeout_seconds: float = 8.0,
        contact_email: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._timeout = timeout_seconds
        self._contact_email = contact_email
        self._transport = transport

    async def translate(
        self, text: str, source_language: str, target_language: str
    ) -> str:
        if not text.strip():
            raise TranslationError("Empty translation request")
        if len(text.encode("utf-8")) > 500:
            raise TranslationError("Selected text is too long (maximum 500 UTF-8 bytes)")

        params = {"q": text, "langpair": f"{source_language}|{target_language}", "mt": "1"}
        if self._contact_email:
            params["de"] = self._contact_email
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(self._endpoint, params=params)
        except httpx.TimeoutException as error:
            raise TranslationTimeoutError from error
        except httpx.NetworkError as error:
            raise TranslationNetworkError from error

        if response.status_code in {401, 403}:
            raise TranslationAuthenticationError
        if response.status_code == 429:
            raise TranslationRateLimitError
        if response.status_code >= 500:
            raise TranslationError("Translation API is unavailable")
        if response.status_code >= 400:
            raise TranslationError(f"Translation API returned HTTP {response.status_code}")

        try:
            payload = response.json()
            status = int(payload.get("responseStatus", 200))
            translated = payload["responseData"]["translatedText"]
        except (KeyError, TypeError, ValueError) as error:
            raise TranslationError("Invalid translation API response") from error
        if status == 429:
            raise TranslationRateLimitError
        if status != 200 or not isinstance(translated, str) or not translated.strip():
            raise TranslationError("Translation API returned an empty result")
        return html.unescape(translated).strip()
