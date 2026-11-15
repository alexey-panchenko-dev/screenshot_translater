from __future__ import annotations

import re


class LanguageDetectionError(ValueError):
    pass


def detect_language(text: str) -> str:
    cyrillic_words = len(re.findall(r"[\u0400-\u04ff]+", text))
    latin_words = len(re.findall(r"[A-Za-z]+", text))
    cyrillic = sum("\u0400" <= char <= "\u04ff" for char in text)
    latin = sum("a" <= char.lower() <= "z" for char in text)
    if cyrillic == latin == 0:
        raise LanguageDetectionError("Language not detected")
    if cyrillic_words != latin_words:
        return "ru" if cyrillic_words > latin_words else "en"
    return "ru" if cyrillic > latin else "en"


def target_language(source_language: str) -> str:
    if source_language == "en":
        return "ru"
    if source_language == "ru":
        return "en"
    raise LanguageDetectionError(f"Unsupported language: {source_language}")
