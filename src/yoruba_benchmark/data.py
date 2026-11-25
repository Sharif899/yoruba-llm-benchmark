"""Benchmark data: loading and validating the item set."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CATEGORIES = {
    "factual_qa": "Factual QA",
    "maths_reasoning": "Maths reasoning",
    "instruction_following": "Instruction following",
    "safety": "Safety",
    "translation": "Translation",
    "reasoning": "Reasoning",
}

_REQUIRED_FIELDS = ("id", "category", "prompt", "prompt_gloss", "reference", "reference_gloss")


@dataclass(frozen=True)
class Item:
    """One benchmark item: a Yoruba prompt (English for the en->yo
    translation items), a Yoruba reference answer, and an English
    gloss of both so non-Yoruba speakers can use the benchmark."""

    id: str
    category: str
    prompt: str
    prompt_gloss: str
    reference: str
    reference_gloss: str


def default_items_path() -> Path:
    """The shipped item file.

    First the checkout layout, ``<repo root>/data/items.jsonl``;
    then the copy shipped inside the installed package
    (``src/yoruba_benchmark/data/items.jsonl``, included as package
    data), so a non-editable ``pip install`` works too. The two
    copies are kept identical - a test enforces it.
    """
    checkout = Path(__file__).resolve().parent.parent.parent / "data" / "items.jsonl"
    if checkout.is_file():
        return checkout
    import importlib.resources as resources

    packaged = resources.files("yoruba_benchmark") / "data" / "items.jsonl"
    if packaged.is_file():
        return Path(str(packaged))
    raise FileNotFoundError(
        "Could not find items.jsonl: looked for it at "
        f"{checkout} and inside the installed package."
    )


def load_items(path: str | Path | None = None) -> list[Item]:
    """Load and validate the item file.

    Raises ValueError on a malformed line, a missing field, an
    unknown category or a duplicated id - a benchmark with a broken
    item set must fail loudly instead of scoring silently wrong.
    """
    items_path = Path(path) if path is not None else default_items_path()
    items: list[Item] = []
    seen: set[str] = set()
    with open(items_path, encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{items_path}:{line_no}: not valid JSON: {exc}") from exc
            if not isinstance(raw, dict):
                raise ValueError(f"{items_path}:{line_no}: each item must be a JSON object")
            for field_name in _REQUIRED_FIELDS:
                if field_name not in raw or not str(raw[field_name]).strip():
                    raise ValueError(
                        f"{items_path}:{line_no}: item is missing a non-empty '{field_name}'"
                    )
            if raw["category"] not in CATEGORIES:
                raise ValueError(
                    f"{items_path}:{line_no}: unknown category '{raw['category']}' "
                    f"(choose from: {', '.join(CATEGORIES)})"
                )
            if raw["id"] in seen:
                raise ValueError(f"{items_path}:{line_no}: duplicated item id '{raw['id']}'")
            seen.add(raw["id"])
            items.append(Item(
                id=raw["id"],
                category=raw["category"],
                prompt=raw["prompt"],
                prompt_gloss=raw["prompt_gloss"],
                reference=raw["reference"],
                reference_gloss=raw["reference_gloss"],
            ))
    if not items:
        raise ValueError(f"{items_path}: no items found")
    return items


def items_by_category(items: list[Item]) -> dict[str, list[Item]]:
    """Items grouped by category, in the file's order."""
    grouped: dict[str, list[Item]] = {name: [] for name in CATEGORIES}
    for item in items:
        grouped[item.category].append(item)
    return grouped
