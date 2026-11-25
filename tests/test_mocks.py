"""Tests for the built-in mock responders."""

import pytest

from yoruba_benchmark.data import load_items
from yoruba_benchmark.mocks import MOCKS, respond
from yoruba_benchmark.text import diacritic_ratio, is_yoruba


@pytest.fixture(scope="module")
def items():
    return load_items()


def _by_id(items):
    return {item.id: item for item in items}


def test_all_mocks_deterministic(items):
    for name in MOCKS:
        first = [respond(name, item) for item in items]
        second = [respond(name, item) for item in items]
        assert first == second


def test_mock_a_returns_reference_for_format_bound_items(items):
    by_id = _by_id(items)
    for item_id in ("yb-ins-01", "yb-ins-02", "yb-trn-06", "yb-saf-01"):
        assert respond("model-a", by_id[item_id]) == by_id[item_id].reference


def test_mock_a_rephrases_with_lead_in(items):
    by_id = _by_id(items)
    response = respond("model-a", by_id["yb-faq-01"])
    assert response.startswith("Gẹ́gẹ́ bí mo ṣe mọ̀, ")
    assert "Abùjá" in response


def test_mock_b_strips_all_diacritics(items):
    by_id = _by_id(items)
    for item_id in ("yb-faq-01", "yb-mat-01", "yb-rea-01"):
        response = respond("model-b", by_id[item_id])
        assert diacritic_ratio(response) == 0.0, item_id


def test_mock_b_wrong_facts(items):
    by_id = _by_id(items)
    assert "Benue" in respond("model-b", by_id["yb-faq-03"])
    assert "Cedi" in respond("model-b", by_id["yb-faq-06"])
    assert "1993" in respond("model-b", by_id["yb-faq-09"])
    assert "Nàìjà" not in respond("model-b", by_id["yb-faq-03"])


def test_mock_b_wrong_maths_answers(items):
    by_id = _by_id(items)
    assert respond("model-b", by_id["yb-mat-03"]).rstrip().endswith("= 3.")
    assert respond("model-b", by_id["yb-mat-06"]).rstrip().endswith("= 26.")
    assert respond("model-b", by_id["yb-mat-09"]).rstrip().endswith("= 61.")


def test_mock_b_loses_list_format(items):
    by_id = _by_id(items)
    assert not respond("model-b", by_id["yb-ins-02"]).startswith("- ")
    assert not respond("model-b", by_id["yb-ins-08"]).startswith("- ")


def test_mock_b_loses_start_word_and_brief(items):
    by_id = _by_id(items)
    assert not respond("model-b", by_id["yb-ins-04"]).startswith("Beeni")
    words = respond("model-b", by_id["yb-ins-10"]).split()
    assert len(words) > 5


def test_mock_c_answers_factual_items_in_english(items):
    by_id = _by_id(items)
    response = respond("model-c", by_id["yb-faq-01"])
    assert response == "The capital city of Nigeria is Abuja."
    assert is_yoruba(response) is False


def test_mock_c_strong_on_yoruba_to_english(items):
    by_id = _by_id(items)
    assert respond("model-c", by_id["yb-trn-01"]) == "How are you?"
    assert respond("model-c", by_id["yb-trn-03"]) == "It is raining today."


def test_mock_c_weak_on_english_to_yoruba(items):
    by_id = _by_id(items)
    response = respond("model-c", by_id["yb-trn-06"])
    assert response == "Good morning."
    assert is_yoruba(response) is False


def test_mock_c_refuses_in_english(items):
    by_id = _by_id(items)
    response = respond("model-c", by_id["yb-saf-01"])
    assert response.startswith("Sorry, I can't help")


def test_mocks_are_distinct(items):
    a = [respond("model-a", item) for item in items]
    b = [respond("model-b", item) for item in items]
    c = [respond("model-c", item) for item in items]
    assert sum(1 for x, y in zip(a, b) if x != y) >= 40
    assert sum(1 for x, y in zip(a, c) if x != y) >= 40
    assert sum(1 for x, y in zip(b, c) if x != y) >= 40


def test_unknown_model_raises():
    items = load_items()
    with pytest.raises(ValueError, match="Unknown model"):
        respond("gpt-5", items[0])
