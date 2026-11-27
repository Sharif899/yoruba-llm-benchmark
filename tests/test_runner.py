"""Tests for the runner: JSONL scoring, aggregation, comparison."""

import json

import pytest

from yoruba_benchmark.data import load_items
from yoruba_benchmark.runner import (
    aggregate,
    compare_records,
    load_results,
    run_jsonl,
    run_model,
    save_results,
)


@pytest.fixture(scope="module")
def items():
    return load_items()


def _write_jsonl(tmp_path, lines):
    path = tmp_path / "responses.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_run_model_scores_all_items(items):
    records = run_model("model-a", items)
    assert len(records) == 100
    assert all(r["model"] == "model-a" for r in records)
    assert all("mean" in r and "criteria" in r for r in records)


def test_run_jsonl_happy_path(items, tmp_path):
    path = _write_jsonl(tmp_path, [
        json.dumps({"prompt_id": "yb-faq-01", "model": "my-model",
                    "response": "Olú ìlú Nàìjíríà ni Abùjá."}, ensure_ascii=False),
        json.dumps({"prompt_id": "yb-mat-01", "model": "my-model",
                    "response": "Adé ní ọ̀sàn mẹ́fà báyìí, nítorí 3 + 3 = 6."}, ensure_ascii=False),
    ])
    records = run_jsonl(path, items)
    assert len(records) == 2
    assert records[0]["model"] == "my-model"
    assert records[0]["mean"] == 4.6


def test_run_jsonl_malformed_json(items, tmp_path):
    path = _write_jsonl(tmp_path, ['{"prompt_id": "yb-faq-01",'])
    with pytest.raises(ValueError, match=":1: not valid JSON"):
        run_jsonl(path, items)


def test_run_jsonl_unknown_prompt_id(items, tmp_path):
    path = _write_jsonl(tmp_path, [
        json.dumps({"prompt_id": "yb-nope-99", "model": "m", "response": "x"}),
    ])
    with pytest.raises(ValueError, match="unknown prompt_id 'yb-nope-99'"):
        run_jsonl(path, items)


def test_run_jsonl_missing_field(items, tmp_path):
    path = _write_jsonl(tmp_path, [
        json.dumps({"prompt_id": "yb-faq-01", "model": "m"}),
    ])
    with pytest.raises(ValueError, match="missing field 'response'"):
        run_jsonl(path, items)


def test_run_jsonl_empty_response(items, tmp_path):
    path = _write_jsonl(tmp_path, [
        json.dumps({"prompt_id": "yb-faq-01", "model": "m", "response": "   "}),
    ])
    with pytest.raises(ValueError, match="'response' must be a non-empty string"):
        run_jsonl(path, items)


def test_run_jsonl_non_object_row(items, tmp_path):
    path = _write_jsonl(tmp_path, ['["yb-faq-01"]'])
    with pytest.raises(ValueError, match="must be a JSON object"):
        run_jsonl(path, items)


def test_aggregate_math(items):
    records = run_model("model-a", items)
    summary = aggregate(records)
    assert summary["model"] == "model-a"
    assert summary["n"] == 100
    assert summary["overall_mean"] == round(sum(r["mean"] for r in records) / 100, 3)
    assert summary["overall_pass_rate"] == 1.0
    assert set(summary["by_category"]) == {
        "factual_qa", "maths_reasoning", "instruction_following",
        "safety", "translation", "reasoning", "normative_reasoning",
    }
    expected_counts = {
        "factual_qa": 10, "maths_reasoning": 10,
        "instruction_following": 10, "safety": 10, "translation": 10,
        "reasoning": 10, "normative_reasoning": 40,
    }
    assert {cat: stats["n"] for cat, stats in summary["by_category"].items()} == expected_counts


def test_aggregate_empty_raises():
    with pytest.raises(ValueError, match="No records"):
        aggregate([])


def test_compare_model_a_beats_model_b(items):
    result = compare_records(run_model("model-a", items), run_model("model-b", items))
    assert result["model_a"] == "model-a"
    assert result["model_b"] == "model-b"
    assert result["n"] == 100
    assert result["wins_a"] > result["wins_b"]
    assert result["mean_a"] > result["mean_b"]
    assert result["wins_a"] + result["wins_b"] + result["ties"] == 100


def test_compare_identical_records_all_tie(items):
    records = run_model("model-a", items)
    result = compare_records(records, list(records))
    assert result["ties"] == 100
    assert result["wins_a"] == 0 and result["wins_b"] == 0


def test_compare_tie_threshold(items):
    # Two records 0.2 apart on the mean are a tie, not a win.
    records_a = run_model("model-a", items)
    records_b = [dict(r, mean=round(r["mean"] - 0.2, 2)) for r in records_a]
    result = compare_records(records_a, records_b)
    assert result["ties"] == 100


def test_save_and_load_results_round_trip(items, tmp_path):
    records = run_model("model-c", items)
    summary = aggregate(records)
    path = save_results(tmp_path / "out" / "results.json", records, summary)
    assert path.is_file()
    loaded_records, loaded_summary = load_results(path)
    assert loaded_summary == summary
    assert len(loaded_records) == 100
    assert loaded_records[0]["item_id"] == records[0]["item_id"]


def test_load_results_rejects_bad_file(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"hello": "world"}', encoding="utf-8")
    with pytest.raises(ValueError, match="not a results file"):
        load_results(path)
