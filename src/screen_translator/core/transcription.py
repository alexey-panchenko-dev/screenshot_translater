from __future__ import annotations

import re
from functools import lru_cache

import cmudict

_WORD_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_ARPABET_TO_IPA = {
    "AA": "ɑ",
    "AE": "æ",
    "AH": "ʌ",
    "AO": "ɔ",
    "AW": "aʊ",
    "AY": "aɪ",
    "B": "b",
    "CH": "tʃ",
    "D": "d",
    "DH": "ð",
    "EH": "ɛ",
    "ER": "ɝ",
    "EY": "eɪ",
    "F": "f",
    "G": "ɡ",
    "HH": "h",
    "IH": "ɪ",
    "IY": "i",
    "JH": "dʒ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "ŋ",
    "OW": "oʊ",
    "OY": "ɔɪ",
    "P": "p",
    "R": "ɹ",
    "S": "s",
    "SH": "ʃ",
    "T": "t",
    "TH": "θ",
    "UH": "ʊ",
    "UW": "u",
    "V": "v",
    "W": "w",
    "Y": "j",
    "Z": "z",
    "ZH": "ʒ",
}


@lru_cache(maxsize=1)
def _pronunciations() -> dict[str, list[list[str]]]:
    return cmudict.dict()


def english_to_ipa(text: str) -> str:
    """Return a readable offline IPA transcription for an English phrase."""
    words = _WORD_PATTERN.findall(text)
    if not words:
        return ""

    dictionary = _pronunciations()
    transcription: list[str] = []
    for word in words:
        variants = dictionary.get(word.lower())
        if not variants:
            return ""
        phonemes = variants[0]
        converted = "".join(
            _ARPABET_TO_IPA.get(phoneme.rstrip("012"), "") for phoneme in phonemes
        )
        if not converted:
            return ""
        transcription.append(converted)
    return f"/{' '.join(transcription)}/"
