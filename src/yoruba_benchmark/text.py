"""Yoruba-aware text handling.

Yoruba is written with the letters ẹ, ọ and ṣ plus tone marks
(á é í ó ú for high tone, à è ì ò ù for low tone, mid tone usually
unmarked). Real model output often drops the diacritics, so matching
is done on a *folded* form — diacritics stripped, lower case — while
the original text is kept for the diacritic-quality signal. A correct
answer written without tone marks still matches; the missing
diacritics are reported honestly instead of being punished twice.
"""

from __future__ import annotations

import re
import unicodedata

# Yoruba number words, counting form and attributive (with-noun) form,
# mapped to their value. Keys are matched after folding, so a word
# written without tone marks matches too. Verified against standard
# Yoruba counting (vigesimal system): 15 = mẹ́ẹ̀ẹ́dógún, 25 =
# mẹ́ẹ̀ẹ́dọ́gbọ̀n, 32 = méjìlélọ́gbọ̀n, 60 = ọgọ́ta, 100 = ọgọ́rùn-ún.
YORUBA_NUMBERS = {
    "ẹni": 1, "ọ̀kan": 1,
    "èjì": 2, "méjì": 2,
    "ẹ̀ta": 3, "mẹ́ta": 3,
    "ẹ̀rin": 4, "mẹ́rin": 4,
    "àrún": 5, "márùn-ún": 5,
    "ẹ̀fà": 6, "mẹ́fà": 6,
    "èje": 7, "méje": 7,
    "ẹ̀jọ": 8, "mẹ́jọ": 8,
    "ẹ̀sán": 9, "mẹ́sàn-án": 9,
    "ẹ̀wá": 10, "mẹ́wàá": 10,
    "ọ̀kànlá": 11, "mọ́kànlá": 11,
    "èjìlá": 12, "méjìlá": 12,
    "ẹ̀tàlá": 13, "mẹ́tàlá": 13,
    "ẹ̀rìnlá": 14, "mẹ́rìnlá": 14,
    "ẹ̀ẹ́dógún": 15, "mẹ́ẹ̀ẹ́dógún": 15,
    "ẹ̀rìndínlógún": 16, "mẹ́rìndínlógún": 16,
    "ẹ̀tàdínlógún": 17, "mẹ́tàdínlógún": 17,
    "èjìdínlógún": 18, "méjìdínlógún": 18,
    "ọ̀kàndínlógún": 19, "mọ́kàndínlógún": 19,
    "ogún": 20,
    "ọ̀kànlélógún": 21, "mọ́kànlélógún": 21,
    "èjìlélógún": 22, "méjìlélógún": 22,
    "ẹ̀tàlélógún": 23, "mẹ́tàlélógún": 23,
    "ẹ̀rìnlélógún": 24, "mẹ́rìnlélógún": 24,
    "ẹ̀ẹ́dọ́gbọ̀n": 25, "mẹ́ẹ̀ẹ́dọ́gbọ̀n": 25,
    "ọgbọ̀n": 30,
    "èjìlélọ́gbọ̀n": 32, "méjìlélọ́gbọ̀n": 32,
    "ogójì": 40,
    "àádọ́ta": 50,
    "ọgọ́ta": 60,
    "ọgọ́rùn": 100, "ọgọ́rùn-ún": 100,
}

# Words carrying no content for recall matching (folded forms).
STOPWORDS = {
    # Yoruba function words.
    "ni", "ti", "o", "se", "ko", "si", "lo", "wa", "je", "fun", "bi",
    "pelu", "ninu", "lori", "yio", "won", "yi", "naa", "re", "mi", "ki",
    "to", "ba", "le", "a", "e", "i", "n", "julo", "so", "gege",
    "kini", "ta", "wo", "meloo", "sile", "dipo",
    # English function words.
    "the", "a", "an", "is", "are", "was", "were", "it", "its", "of",
    "in", "on", "to", "and", "or", "for", "with", "by", "as", "at",
    "from", "that", "this", "be", "has", "have", "do", "does", "did",
}

# Yoruba function words that mark a response as Yoruba (folded).
YORUBA_FUNCTION_WORDS = {
    "ni", "ti", "o", "se", "ko", "si", "lo", "wa", "je", "fun", "bi",
    "pelu", "ninu", "lori", "won", "naa", "re", "mi", "ki", "to", "ba",
    "le", "julo", "so", "gege", "bawo", "nitori", "akoko",
}

_DOT_BELOW = {"ẹ": "e", "ọ": "o", "ṣ": "s", "Ẹ": "E", "Ọ": "O", "Ṣ": "S"}


def normalize(text: str) -> str:
    """Unicode NFC normalisation, so composed and decomposed forms compare equal."""
    return unicodedata.normalize("NFC", text or "")


def fold(text: str) -> str:
    """Fold text for matching: NFKD, strip combining marks, map ẹ/ọ/ṣ
    to e/o/s, lower case. 'mẹ́ta' and 'meta' both fold to 'meta'."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    out = []
    for char in decomposed:
        if unicodedata.combining(char):
            continue
        out.append(_DOT_BELOW.get(char, char))
    return "".join(out).lower()


def strip_diacritics(text: str) -> str:
    """Remove tone marks and underdots, keeping case and word shape.
    'Mẹ́ta' becomes 'Meta'."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    out = []
    for char in decomposed:
        if unicodedata.combining(char):
            continue
        out.append(_DOT_BELOW.get(char, char))
    return "".join(out)


# The number-word map with folded keys, for matching folded text.
_FOLDED_NUMBERS = {fold(word): value for word, value in YORUBA_NUMBERS.items()}


def tokens(text: str) -> list[str]:
    """Folded word tokens, hyphenated words kept whole."""
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", fold(text))


def content_tokens(text: str) -> set[str]:
    """Tokens carrying content: stopwords removed."""
    return {tok for tok in tokens(text) if tok not in STOPWORDS}


def yoruba_number_value(word: str) -> int | None:
    """The value of a Yoruba number word, or None when it is not one.
    Matching is folded, so "meta" and "mẹ́ta" both give 3."""
    return _FOLDED_NUMBERS.get(fold(word))


def numbers_in(text: str) -> set[int]:
    """Numbers mentioned in text: Arabic digits plus Yoruba number words."""
    return set(numbers_ordered(text))


def numbers_ordered(text: str) -> list[int]:
    """Numbers mentioned in text, in order of appearance: Arabic
    digits plus Yoruba number words. The last number is usually the
    answer, so order matters for checking it."""
    found: list[tuple[int, int]] = []
    for match in re.finditer(r"\d+", text or ""):
        found.append((match.start(), int(match.group(0))))
    folded = fold(text)
    for word, value in _FOLDED_NUMBERS.items():
        for match in re.finditer(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", folded):
            found.append((match.start(), value))
    found.sort()
    return [value for _, value in found]


def proper_nouns(text: str) -> set[str]:
    """Capitalised words that are not sentence-initial, folded.

    Used to spot an entity substitution: a response that names a
    different proper noun in place of the reference's (Lagos for
    Abuja) is contradicting the reference, even if it shares many
    ordinary words with it.
    """
    nouns: set[str] = set()
    for sentence in re.split(r"(?<=[.!?])\s+", (text or "").strip()):
        words = sentence.split()
        for word in words[1:]:
            clean = re.sub(r"[^A-Za-zÀ-ÿ\u1e00-\u1eff]", "", word)
            if len(clean) >= 3 and clean[0].isupper():
                nouns.add(fold(clean))
    return nouns


def diacritic_ratio(text: str) -> float:
    """Fraction of word tokens that carry Yoruba diacritics
    (ẹ, ọ, ṣ or a tone mark). Informational only: it is reported
    next to a score, never used to compute one. 0.0 when the text
    has no words."""
    words = re.findall(r"[A-Za-zÀ-ÿ\u1e00-\u1eff]+(?:-[A-Za-zÀ-ÿ\u1e00-\u1eff]+)*", text or "")
    if not words:
        return 0.0
    with_marks = sum(1 for word in words if strip_diacritics(word) != word)
    return round(with_marks / len(words), 3)


def word_count(text: str) -> int:
    """Number of word tokens in the text."""
    return len(tokens(text))


def sentence_count(text: str) -> int:
    """Number of sentences: text split on . ! ? with empty parts dropped.
    A list with no sentence terminators counts as one sentence."""
    parts = [part for part in re.split(r"[.!?]+", text or "") if part.strip()]
    return len(parts)


def list_lines(text: str) -> int:
    """Number of list entries: lines starting with '- ', '* ' or a number."""
    count = 0
    for line in (text or "").splitlines():
        if re.match(r"\s*[-*•]\s+\S", line) or re.match(r"\s*\d+[.)]\s+\S", line):
            count += 1
    return count


def is_yoruba(text: str) -> bool:
    """Best-effort check that a response is Yoruba, not English:
    it either carries Yoruba diacritics or uses Yoruba function words."""
    if diacritic_ratio(text) > 0:
        return True
    return bool(set(tokens(text)) & YORUBA_FUNCTION_WORDS)
