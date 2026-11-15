from screen_translator.core.transcription import english_to_ipa


def test_english_to_ipa_transcribes_known_phrase() -> None:
    assert english_to_ipa("Quick transfer") == "/kwɪk tɹænsfɝ/"


def test_english_to_ipa_returns_empty_for_unknown_word() -> None:
    assert english_to_ipa("codexnonword") == ""


def test_english_to_ipa_returns_empty_for_non_english_text() -> None:
    assert english_to_ipa("быстрый перевод") == ""
