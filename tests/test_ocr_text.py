from screen_translator.ocr.text import cleanup_text, has_meaningful_text


def test_cleanup_joins_short_ocr_lines() -> None:
    text = "I   have been\nworking here\nfor two years ."

    assert cleanup_text(text) == "I have been working here for two years."


def test_cleanup_preserves_larger_multiline_block() -> None:
    text = "First line\nSecond line\nThird line\nFourth line"

    assert cleanup_text(text) == text


def test_cleanup_removes_blank_lines_and_nonbreaking_spaces() -> None:
    assert cleanup_text("  Hello\u00a0 world  \n\n  again ") == "Hello world again"


def test_meaningful_text_accepts_numbers_and_rejects_punctuation() -> None:
    assert has_meaningful_text("123")
    assert has_meaningful_text("example.com")
    assert not has_meaningful_text("... --- !!!")
