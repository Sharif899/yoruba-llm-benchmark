"""Tests for the benchmark data set itself."""

from collections import Counter

from yoruba_benchmark.data import CATEGORIES, load_items

EXPECTED_COUNTS = {
    "factual_qa": 10,
    "maths_reasoning": 10,
    "instruction_following": 10,
    "safety": 10,
    "translation": 10,
    "reasoning": 10,
}


def test_packaged_data_matches_repo_data():
    """The item file ships twice - at the repo root and inside the
    installed package, so a non-editable install works. The copies
    must stay identical."""
    import importlib.resources as resources

    from yoruba_benchmark.data import default_items_path

    repo_copy = default_items_path().read_bytes()
    packaged = resources.files("yoruba_benchmark") / "data" / "items.jsonl"
    assert packaged.is_file(), "packaged copy of items.jsonl is missing"
    assert packaged.read_bytes() == repo_copy


def test_sixty_items():
    assert len(load_items()) == 60


def test_ten_items_per_category():
    counts = Counter(item.category for item in load_items())
    assert dict(counts) == EXPECTED_COUNTS


def test_ids_unique_and_prefixed():
    items = load_items()
    ids = [item.id for item in items]
    assert len(set(ids)) == len(ids)
    assert all(item_id.startswith("yb-") for item_id in ids)


def test_all_fields_non_empty():
    for item in load_items():
        assert item.prompt.strip()
        assert item.prompt_gloss.strip()
        assert item.reference.strip()
        assert item.reference_gloss.strip()
        assert item.category in CATEGORIES


def test_translation_direction():
    items = load_items()
    yo_to_en = [i for i in items if i.id in ("yb-trn-01", "yb-trn-02", "yb-trn-03", "yb-trn-04", "yb-trn-05")]
    en_to_yo = [i for i in items if i.id in ("yb-trn-06", "yb-trn-07", "yb-trn-08", "yb-trn-09", "yb-trn-10")]
    assert len(yo_to_en) == 5 and len(en_to_yo) == 5
    # Yoruba -> English: the reference is English.
    assert all("Ẹ" not in i.reference and "ọ" not in i.reference for i in yo_to_en)
    # English -> Yoruba: the reference is Yoruba (carries diacritics).
    assert all(i.reference != i.reference_gloss for i in en_to_yo)


def test_safety_references_are_refusals():
    from yoruba_benchmark.text import fold

    items = [i for i in load_items() if i.category == "safety"]
    for item in items:
        assert "mi o le" in fold(item.reference), item.id


def test_maths_references_contain_the_answer():
    for item in load_items():
        if item.category != "maths_reasoning":
            continue
        assert "=" in item.reference or "÷" in item.reference, item.id
