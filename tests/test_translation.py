import asyncio

import httpx
import pytest

from screen_translator.translation.base import TranslationRateLimitError
from screen_translator.translation.translator import (
    GoogleWebTranslationService,
    MyMemoryTranslationService,
)


def test_translation_parses_provider_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["langpair"] == "en|ru"
        return httpx.Response(
            200,
            json={"responseStatus": 200, "responseData": {"translatedText": "Привет &amp; мир"}},
        )

    service = MyMemoryTranslationService(transport=httpx.MockTransport(handler))

    result = asyncio.run(service.translate("Hello world", "en", "ru"))

    assert result == "Привет & мир"


def test_translation_maps_rate_limit() -> None:
    service = MyMemoryTranslationService(
        transport=httpx.MockTransport(lambda request: httpx.Response(429))
    )

    with pytest.raises(TranslationRateLimitError):
        asyncio.run(service.translate("Hello", "en", "ru"))


def test_google_translation_joins_response_segments() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json=[[["Привет ", "Hello ", None], ["мир", "world", None]]]
        )
    )
    service = GoogleWebTranslationService(transport=transport)

    assert asyncio.run(service.translate("Hello world", "en", "ru")) == "Привет мир"
