"""Running the benchmark: score models, aggregate, compare."""

from __future__ import annotations

import json
from pathlib import Path

from .data import CATEGORIES, Item
from .mocks import MOCKS, respond
from .scorer import (
    PASS_THRESHOLD,
    TIE_THRESHOLD,
    compare_results,
    score_response,
)

# A scored record: one model response to one item, with its rubric result.
Record = dict


def run_model(model_name: str, items: list[Item]) -> list[Record]:
    """Score one mock model over the item set."""
    if model_name not in MOCKS:
        raise ValueError(
            f"Unknown model '{model_name}'. Choose from: {', '.join(MOCKS)}"
        )
    records: list[Record] = []
    for item in items:
        response = respond(model_name, item)
        result = score_response(item.prompt, response, item.reference, item.category)
        records.append(_record(model_name, item, response, result))
    return records


def run_jsonl(path: str | Path, items: list[Item]) -> list[Record]:
    """Score a JSONL file of real model responses.

    Each line must be a JSON object with ``prompt_id`` (an item id
    from the benchmark), ``model`` (a name for the model) and
    ``response`` (the model's response, a non-empty string).
    Validation is strict and fails loudly: a malformed line, an
    unknown prompt id or a missing field raises ValueError naming
    the line, because silently skipping bad rows would make the
    results unreproducible.
    """
    by_id = {item.id: item for item in items}
    records: list[Record] = []
    jsonl_path = Path(path)
    with open(jsonl_path, encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{jsonl_path}:{line_no}: not valid JSON: {exc}"
                ) from exc
            if not isinstance(row, dict):
                raise ValueError(
                    f"{jsonl_path}:{line_no}: each row must be a JSON object "
                    f"with 'prompt_id', 'model' and 'response'"
                )
            for field_name in ("prompt_id", "model", "response"):
                if field_name not in row:
                    raise ValueError(
                        f"{jsonl_path}:{line_no}: missing field '{field_name}'"
                    )
            prompt_id = row["prompt_id"]
            if prompt_id not in by_id:
                raise ValueError(
                    f"{jsonl_path}:{line_no}: unknown prompt_id '{prompt_id}'"
                )
            response = row["response"]
            if not isinstance(response, str) or not response.strip():
                raise ValueError(
                    f"{jsonl_path}:{line_no}: 'response' must be a non-empty string"
                )
            item = by_id[prompt_id]
            result = score_response(item.prompt, response, item.reference, item.category)
            records.append(_record(str(row["model"]), item, response, result))
    return records


def _record(model: str, item: Item, response: str, result) -> Record:
    return {
        "item_id": item.id,
        "category": item.category,
        "model": model,
        "prompt": item.prompt,
        "response": response,
        "reference": item.reference,
        "mean": result.mean,
        "total": result.total,
        "passed": result.passed,
        "diacritic_ratio": result.diacritic_ratio,
        "criteria": {c.criterion: c.score for c in result.criteria},
        "rationales": {c.criterion: c.rationale for c in result.criteria},
    }


def aggregate(records: list[Record]) -> dict:
    """Per-category and overall means and pass rates for one model."""
    if not records:
        raise ValueError("No records to aggregate.")
    model = records[0]["model"]
    by_category: dict[str, dict] = {}
    for category in CATEGORIES:
        group = [r for r in records if r["category"] == category]
        if not group:
            continue
        means = [r["mean"] for r in group]
        by_category[category] = {
            "n": len(group),
            "mean": round(sum(means) / len(means), 3),
            "pass_rate": round(sum(1 for r in group if r["passed"]) / len(group), 3),
        }
    means = [r["mean"] for r in records]
    ratios = [r["diacritic_ratio"] for r in records]
    return {
        "model": model,
        "n": len(records),
        "overall_mean": round(sum(means) / len(means), 3),
        "overall_pass_rate": round(
            sum(1 for r in records if r["passed"]) / len(records), 3
        ),
        "mean_diacritic_ratio": round(sum(ratios) / len(ratios), 3),
        "by_category": by_category,
    }


def compare_records(records_a: list[Record], records_b: list[Record]) -> dict:
    """Head-to-head between two models' records, aligned by item id.

    A model wins an item when its mean is higher by at least 0.3;
    anything closer is a tie."""
    if not records_a or not records_b:
        raise ValueError("Both models need records to compare.")
    by_id_b = {r["item_id"]: r for r in records_b}
    model_a, model_b = records_a[0]["model"], records_b[0]["model"]
    wins_a = wins_b = ties = 0
    per_category: dict[str, dict] = {}
    for record_a in records_a:
        record_b = by_id_b.get(record_a["item_id"])
        if record_b is None:
            continue
        gap = record_a["mean"] - record_b["mean"]
        if gap >= TIE_THRESHOLD:
            winner = "A"
            wins_a += 1
        elif -gap >= TIE_THRESHOLD:
            winner = "B"
            wins_b += 1
        else:
            winner = "tie"
            ties += 1
        bucket = per_category.setdefault(
            record_a["category"], {"a": 0, "b": 0, "tie": 0, "n": 0}
        )
        bucket["n"] += 1
        bucket[{"A": "a", "B": "b", "tie": "tie"}[winner]] += 1
    return {
        "model_a": model_a,
        "model_b": model_b,
        "n": wins_a + wins_b + ties,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "ties": ties,
        "mean_a": round(
            sum(r["mean"] for r in records_a) / len(records_a), 3
        ),
        "mean_b": round(
            sum(r["mean"] for r in records_b) / len(records_b), 3
        ),
        "per_category": per_category,
    }


def compare_models(model_a: str, model_b: str, items: list[Item]) -> dict:
    """Run two mock models and compare them head to head."""
    return compare_records(run_model(model_a, items), run_model(model_b, items))


def save_results(path: str | Path, records: list[Record], summary: dict) -> Path:
    """Save scored records and their aggregate summary as JSON."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "records": records}, handle, ensure_ascii=False, indent=2)
    return out_path


def load_results(path: str | Path) -> tuple[list[Record], dict]:
    """Load a results file written by :func:`save_results`."""
    with open(Path(path), encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or "records" not in data or "summary" not in data:
        raise ValueError(f"{path}: not a results file (expected 'summary' and 'records')")
    return data["records"], data["summary"]
