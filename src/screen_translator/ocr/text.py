from __future__ import annotations

import re

_HORIZONTAL_WHITESPACE = re.compile(r"[\t \u00a0]+")
_SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([,.;:!?])")
_SPACE_AFTER_OPENING = re.compile(r"([([{])\s+")


def cleanup_text(text: str) -> str:
    """Normalize OCR whitespace while retaining structure for larger blocks."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for raw_line in normalized.split("\n"):
        line = _HORIZONTAL_WHITESPACE.sub(" ", raw_line).strip()
        line = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", line)
        line = _SPACE_AFTER_OPENING.sub(r"\1", line)
        if line:
            lines.append(line)

    if len(lines) <= 3 and sum(map(len, lines)) <= 400:
        return " ".join(lines)
    return "\n".join(lines)


def has_meaningful_text(text: str) -> bool:
    return any(character.isalnum() for character in text)
