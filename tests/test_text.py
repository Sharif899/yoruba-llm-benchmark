"""Tests for Yoruba-aware text handling."""

from yoruba_benchmark.text import (
    YORUBA_NUMBERS,
    content_tokens,
    diacritic_ratio,
    fold,
    is_yoruba,
    list_lines,
    normalize,
    numbers_in,
    numbers_ordered,
    proper_nouns,
    sentence_count,
    strip_diacritics,
    tokens,
    word_count,
)


def test_fold_maps_underdots():
    assert fold("ẹ") == "e"
    assert fold("ọ") == "o"
    assert fold("ṣ") == "s"
    assert fold("Ẹ̀bà") == "eba"


def test_fold_strips_tone_marks():
    assert fold("mẹ́ta") == "meta"
    assert fold("márùn-ún") == "marun-un"
    assert fold("Abùjá") == "abuja"


def test_fold_lowercases():
    assert fold("Ìwé") == "iwe"


def test_normalize_nfc_composes():
    decomposed = "m\u1eb9\u0301ta"
    assert normalize(decomposed) == "mẹ́ta"


def test_strip_diacritics_keeps_case():
    assert strip_diacritics("Mẹ́ta") == "Meta"
    assert strip_diacritics("Ìbàdàn") == "Ibadan"


def test_tokens_keep_hyphenated_words():
    assert tokens("márùn-ún méjì") == ["marun-un", "meji"]


def test_content_tokens_drop_stopwords():
    result = content_tokens("Olú ìlú Nàìjíríà ni Abùjá")
    assert result == {"olu", "ilu", "naijiria", "abuja"}


def test_numbers_in_digits():
    assert numbers_in("3 + 3 = 6") == {3, 6}


def test_numbers_in_yoruba_words():
    assert numbers_in("Adé ní ọ̀sàn mẹ́ta") == {3}
    assert numbers_in("ẹyin márùn-ún") == {5}
    assert numbers_in("ọmọ mẹ́ẹ̀ẹ́dógún") == {15}


def test_numbers_in_verified_tricky_words():
    assert numbers_in("ọmọ mẹ́ẹ̀ẹ́dọ́gbọ̀n") == {25}
    assert numbers_in("ìwé méjìlélọ́gbọ̀n") == {32}
    assert numbers_in("naira ọgọ́ta") == {60}
    assert numbers_in("ogún") == {20}
    assert numbers_in("ọgọ́rùn-ún") == {100}


def test_numbers_in_folded_words_match():
    # A number word written without diacritics still matches.
    assert numbers_in("omo meeedogun") == {15}
    assert numbers_in("meta") == {3}


def test_numbers_ordered_keeps_order():
    assert numbers_ordered("10 ÷ 5 = 2") == [10, 5, 2]
    assert numbers_ordered("ìwé méjì, nítorí 10 ÷ 5 = 2") == [2, 10, 5, 2]


def test_proper_nouns_skip_sentence_initial():
    assert proper_nouns("Abùjá ni olú ìlú Nàìjíríà.") == {"naijiria"}
    assert proper_nouns("Wole Soyinka ni ọmọ Nàìjíríà.") == {"soyinka", "naijiria"}


def test_diacritic_ratio_with_marks():
    assert diacritic_ratio("Ìbàdàn olú ìlú Ọ̀yọ́") == 1.0
    assert diacritic_ratio("Ibadan ni olu ilu Oyo") == 0.0


def test_diacritic_ratio_partial():
    ratio = diacritic_ratio("Ìbàdàn is the capital")
    assert 0.0 < ratio < 1.0


def test_diacritic_ratio_empty():
    assert diacritic_ratio("") == 0.0


def test_word_count():
    assert word_count("Ìbàdàn ni olú ìlú Ọ̀yọ́") == 5


def test_sentence_count():
    assert sentence_count("Ìwé kan. Ìwé méjì.") == 2
    assert sentence_count("Ìwé kan") == 1
    assert sentence_count("- Àmàlà\n- Ẹ̀bà") == 1


def test_list_lines():
    assert list_lines("- Àmàlà\n- Ẹ̀bà\n- Ìyán") == 3
    assert list_lines("Àmàlà, Ẹ̀bà, Ìyán.") == 0
    assert list_lines("1. Àmàlà\n2. Ẹ̀bà") == 2


def test_is_yoruba():
    assert is_yoruba("Ìbàdàn ni olú ìlú Ọ̀yọ́") is True
    assert is_yoruba("Ibadan ni olu ilu Oyo") is True
    assert is_yoruba("Ibadan is the capital of Oyo State.") is False


def test_yoruba_numbers_map_values():
    assert YORUBA_NUMBERS["mẹ́ta"] == 3
    assert YORUBA_NUMBERS["márùn-ún"] == 5
    assert YORUBA_NUMBERS["mẹ́wàá"] == 10
    assert YORUBA_NUMBERS["ogún"] == 20
    assert YORUBA_NUMBERS["ọgbọ̀n"] == 30
    assert YORUBA_NUMBERS["ogójì"] == 40
    assert YORUBA_NUMBERS["àádọ́ta"] == 50
