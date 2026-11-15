import pytest

from screen_translator.core.language import (
    LanguageDetectionError,
    detect_language,
    target_language,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Use React component here", "en"),
        ("Открой Settings и нажми Save", "ru"),
        ("Google", "en"),
        ("нормально", "ru"),
    ],
)
def test_detect_language(text: str, expected: str) -> None:
    assert detect_language(text) == expected


def test_language_requires_letters() -> None:
    with pytest.raises(LanguageDetectionError):
        detect_language("123 !!!")


def test_target_language() -> None:
    assert target_language("en") == "ru"
    assert target_language("ru") == "en"
