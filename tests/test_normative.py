"""Tests for the normative-reasoning set (paired Yoruba/English scenarios).

The set is 20 original scenarios, each in Yoruba (yb-nor-NN) and in
English (yb-nor-en-NN), the same situation in both languages, so the
Yoruba-versus-English gap is measured on the same content. The
scenarios are written for this benchmark, inspired by the idea of
AfriNORM (normative and social reasoning) but not copied from it or
from any dataset.
"""

import pytest

from yoruba_benchmark.data import load_items
from yoruba_benchmark.mocks import respond
from yoruba_benchmark.runner import run_model
from yoruba_benchmark.scorer import (
    _REASONING_REQUESTED_MARKERS,
    _UNSAFE_PROMPT_MARKERS,
    _contains_phrase,
    score_response,
)
from yoruba_benchmark.text import diacritic_ratio, fold, is_yoruba


@pytest.fixture(scope="module")
def normative():
    return [i for i in load_items() if i.category == "normative_reasoning"]


@pytest.fixture(scope="module")
def by_id(normative):
    return {item.id: item for item in normative}


def test_forty_normative_items_twenty_per_language(normative):
    assert len(normative) == 40
    yoruba = [i for i in normative if i.id.startswith("yb-nor-") and "-en-" not in i.id]
    english = [i for i in normative if i.id.startswith("yb-nor-en-")]
    assert len(yoruba) == 20
    assert len(english) == 20


def test_pairs_match_by_number(by_id):
    """Every Yoruba scenario has the same scenario in English, and the
    Yoruba item's glosses ARE the English item's prompt and reference,
    so the pair tests the same content in both languages."""
    for num in range(1, 21):
        yo_id = f"yb-nor-{num:02d}"
        en_id = f"yb-nor-en-{num:02d}"
        assert yo_id in by_id, yo_id
        assert en_id in by_id, en_id
        yo, en = by_id[yo_id], by_id[en_id]
        assert yo.prompt_gloss == en.prompt, yo_id
        assert yo.reference_gloss == en.reference, yo_id
        assert en.prompt_gloss == en.prompt, en_id
        assert en.reference_gloss == en.reference, en_id


def test_yoruba_items_are_yoruba_and_english_items_are_english(normative):
    """Yoruba items carry diacritics; English items carry none. The
    language check is the diacritic ratio, not ``is_yoruba``: that
    heuristic also fires on English words like "to" and "so", which
    happen to be Yoruba function words too."""
    for item in normative:
        if item.id.startswith("yb-nor-en-"):
            assert diacritic_ratio(item.prompt) == 0.0, item.id
            assert diacritic_ratio(item.reference) == 0.0, item.id
        else:
            assert is_yoruba(item.prompt), item.id
            assert diacritic_ratio(item.reference) > 0, item.id


def test_all_normative_prompts_ask_for_reasoning(normative):
    """Every prompt asks 'why' or 'explain', so the rubric's reasoning
    criterion is scored rather than neutral."""
    for item in normative:
        folded = fold(item.prompt)
        assert any(m in folded for m in _REASONING_REQUESTED_MARKERS), item.id


def test_all_normative_references_show_steps(normative):
    """Every reference states the appropriate action and the reason in
    steps (Àkọ́kọ́ / Ẹlẹ́ẹ̀kejì in Yoruba, First / Second in English),
    so a structured answer can score 5 on reasoning."""
    for item in normative:
        folded = fold(item.reference)
        if item.id.startswith("yb-nor-en-"):
            assert "first" in folded and "second" in folded, item.id
        else:
            assert "akoko" in folded and "eleekeji" in folded, item.id


def test_no_normative_item_trips_the_safety_markers(normative):
    """No prompt or reference may contain a phrase the scorer reads
    as a harmful request: a normative question about gossip or theft
    is not a request to create fake news or steal, and the scorer
    must not treat it as one."""
    for item in normative:
        for field_name in ("prompt", "reference"):
            folded = fold(getattr(item, field_name))
            hits = [m for m in _UNSAFE_PROMPT_MARKERS if _contains_phrase(folded, m)]
            assert not hits, (item.id, field_name, hits)


def test_no_normative_reference_contains_a_digit(normative):
    """A number in the reference would let a conflicting final number
    cap the factual score; normative references state a judgement
    and a reason, not a number."""
    import re

    for item in normative:
        assert not re.search(r"\d", item.reference), item.id


def test_model_a_passes_every_normative_item(normative):
    """The strong mock returns the reference, so it must pass every
    normative item in both languages."""
    for item in normative:
        response = respond("model-a", item)
        result = score_response(item.prompt, response, item.reference, item.category)
        assert result.passed, (item.id, result.mean)
        assert result.mean >= 4.6, (item.id, result.mean)


def test_model_c_gap_is_visible_in_the_mocks(normative):
    """The English-biased mock answers the Yoruba items in English
    (low) and the English items in English (high): the paired set
    must show that gap, or it cannot measure one."""
    records = run_model("model-c", normative)
    yo = [r for r in records if not r["item_id"].startswith("yb-nor-en-")]
    en = [r for r in records if r["item_id"].startswith("yb-nor-en-")]
    yo_mean = sum(r["mean"] for r in yo) / len(yo)
    en_mean = sum(r["mean"] for r in en) / len(en)
    assert en_mean - yo_mean >= 1.0, (yo_mean, en_mean)
    assert sum(1 for r in yo if r["passed"]) == 0
    assert sum(1 for r in en if r["passed"]) == len(en)
