"""Built-in mock responders.

Three deterministic, rule-based responders with documented, distinct
behaviour profiles. They exist to demonstrate the benchmark end to
end - they are not real models, and no result in the README should
be read as a measurement of a real system. Every rule below is
stated in the README next to the numbers it produces.

- model-a, "strong Yoruba": returns the reference answer, lightly
  rephrased with a short lead-in where the format allows it
  ("Gẹ́gẹ́ bí mo ṣe mọ̀, ..."); refuses unsafe requests in Yoruba;
  follows format instructions exactly.
- model-b, "degraded Yoruba": the reference answer with all
  diacritics stripped, and - on a documented subset - a wrong fact
  or number: factual items 03, 06 and 09 of each set get a wrong
  entity or year (see WRONG_FACTS), maths items 03, 06 and 09 get
  the final digit of the answer increased by one; instruction items
  with an even number lose the requested format (a list becomes
  inline text, a one-sentence answer gains a second sentence, a
  brief answer gains extra words). Unsafe requests are still refused,
  in stripped-diacritic Yoruba.
- model-c, "English-biased": answers in English, using the English
  gloss of the reference. That makes it strong on Yoruba-to-English
  translation (the reference there is English) and weak everywhere
  else: it fails Yoruba factual items, answers English-to-Yoruba
  translation in English, and ignores Yoruba-only instructions.
  Unsafe requests are refused in English.
"""

from __future__ import annotations

import re

from .data import Item
from .text import fold, strip_diacritics

MOCK_INFO = {
    "model-a": (
        "model-a",
        "Strong Yoruba",
        "Reference answer, lightly rephrased with a short lead-in where the format allows; refuses unsafe requests in Yoruba; follows format instructions.",
    ),
    "model-b": (
        "model-b",
        "Degraded Yoruba",
        "Reference answer with diacritics stripped; wrong entity/number on factual and maths items 03, 06, 09; format lost on even-numbered instruction items.",
    ),
    "model-c": (
        "model-c",
        "English-biased",
        "Answers in English from the reference gloss; strong on Yoruba-to-English translation, weak on Yoruba factual items and English-to-Yoruba translation.",
    ),
}

# Wrong facts model-b gives, as (correct text, wrong text) pairs.
# faq-03: the longest river in Nigeria is the Niger, not the Benue.
# faq-06: Nigeria's currency is the naira, not the (Ghanaian) cedi.
# faq-09: Soyinka won the Nobel Prize in 1986, not 1993.
WRONG_FACTS = {
    "yb-faq-03": ("Odò Nàìjà", "Odò Benue"),
    "yb-faq-06": ("Naira", "Cedi"),
    "yb-faq-09": ("1986", "1993"),
}

_LEAD_IN = "Gẹ́gẹ́ bí mo ṣe mọ̀, "


def _item_number(item: Item) -> int:
    return int(item.id.rsplit("-", 1)[-1])


def mock_a(item: Item) -> str:
    """Strong Yoruba: the reference, lightly rephrased where the
    format allows it. Format-bound items (instructions, translation)
    and safety refusals are returned exactly as written."""
    if item.category in ("instruction_following", "translation", "safety"):
        return item.reference
    reference = item.reference
    return _LEAD_IN + reference[0].lower() + reference[1:]


def _break_format(item: Item, text: str) -> str:
    """Lose the requested format, the way a weak model does."""
    if text.startswith("- "):
        # A list becomes inline text.
        lines = [line[2:].strip() for line in text.splitlines() if line.startswith("- ")]
        return ", ".join(lines) + "."
    folded_prompt = fold(item.prompt)
    if "pelu oro" in folded_prompt and "," in text:
        # A required opening word is dropped.
        return text.split(",", 1)[1].strip()
    if "gbolohun kan soso" in folded_prompt:
        # A one-sentence answer gains a second sentence.
        return text + " Èyí ni ìdáhùn náà."
    # A brief answer gains extra words.
    return text + " Ìdí ni pé ó ṣe pàtàkì fún gbogbo ènìyàn."


def mock_b(item: Item) -> str:
    """Degraded Yoruba: diacritics stripped everywhere, plus a wrong
    fact or number on items 03, 06 and 09, and lost formatting on
    even-numbered instruction items."""
    text = item.reference
    number = _item_number(item)
    if item.category == "factual_qa" and item.id in WRONG_FACTS:
        correct, wrong = WRONG_FACTS[item.id]
        text = text.replace(correct, wrong)
    elif item.category == "maths_reasoning" and number % 3 == 0:
        # Increase the final digit of the answer by one: 2 -> 3,
        # 25 -> 26, 60 -> 61.
        matches = list(re.finditer(r"\d+", text))
        if matches:
            last = matches[-1]
            wrong = str(int(last.group(0)) + 1)
            text = text[: last.start()] + wrong + text[last.end():]
    if item.category == "instruction_following" and number % 2 == 0:
        text = _break_format(item, text)
    return strip_diacritics(text)


def mock_c(item: Item) -> str:
    """English-biased: answers in English from the reference gloss.
    Refuses unsafe requests in English."""
    if item.category == "safety":
        return (
            "Sorry, I can't help with that. This request asks for "
            "something harmful or against the law, so I have to refuse."
        )
    return item.reference_gloss


MOCKS = {"model-a": mock_a, "model-b": mock_b, "model-c": mock_c}


def respond(model_name: str, item: Item) -> str:
    """One deterministic response from a named mock model."""
    try:
        responder = MOCKS[model_name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown model '{model_name}'. Choose from: {', '.join(MOCKS)}"
        ) from exc
    return responder(item)
