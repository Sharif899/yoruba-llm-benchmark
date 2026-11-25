"""Command line interface: ``ybench``.

    ybench run --mock model-a            score a built-in mock over all items
    ybench run --input responses.jsonl --model my-model
                                         score real model responses from JSONL
    ybench compare --a model-a --b model-b
                                         head-to-head between two models
    ybench report --input results.json  print the results table again
    ybench list [--category safety]     show the benchmark items

Each of ``run`` and ``compare`` takes ``--json`` for machine-readable
output, and ``run`` takes ``--out`` to save the full results file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .data import CATEGORIES, default_items_path, items_by_category, load_items
from .mocks import MOCK_INFO, MOCKS
from .runner import (
    aggregate,
    compare_models,
    compare_records,
    load_results,
    run_jsonl,
    run_model,
    save_results,
)


def _table(headers: list[str], rows: list[list[str]]) -> str:
    """A plain fixed-width text table (standard library only)."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    rule = "-+-".join("-" * w for w in widths)
    body = "\n".join(
        " | ".join(cell.ljust(w) for cell, w in zip(row, widths)) for row in rows
    )
    return line + "\n" + rule + ("\n" + body if body else "")


def _summary_table(summary: dict) -> str:
    rows = [
        [CATEGORIES[cat], str(stats["n"]), f"{stats['mean']:.3f}", f"{stats['pass_rate']:.3f}"]
        for cat, stats in summary["by_category"].items()
    ]
    rows.append([
        "Overall", str(summary["n"]),
        f"{summary['overall_mean']:.3f}", f"{summary['overall_pass_rate']:.3f}",
    ])
    return _table(["Category", "n", "Mean", "Pass rate"], rows)


def _load_source(value: str, items: list) -> tuple[list, str]:
    """A compare/run source: a mock name, or a path to a results file."""
    path = Path(value)
    if path.is_file():
        records, _ = load_results(path)
        return records, records[0]["model"] if records else value
    if value in MOCKS:
        return run_model(value, items), value
    raise ValueError(
        f"'{value}' is neither a mock model ({', '.join(MOCKS)}) "
        f"nor a results file"
    )


def _cmd_run(args: argparse.Namespace) -> int:
    items = load_items(args.items)
    if args.category:
        items = [item for item in items if item.category == args.category]
        if not items:
            print(f"No items in category '{args.category}'.", file=sys.stderr)
            return 2
    if args.mock:
        records = run_model(args.mock, items)
        model = args.mock
    else:
        if not args.input or not args.model:
            print("run needs --mock or both --input and --model.", file=sys.stderr)
            return 2
        records = run_jsonl(args.input, items)
        model = args.model
    summary = aggregate(records)
    if args.out:
        save_results(args.out, records, summary)
        print(f"Saved {len(records)} scored records to {args.out}")
    if args.json:
        print(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2))
    else:
        print(f"Model: {model} ({summary['n']} items)")
        print(_summary_table(summary))
        print(f"Mean diacritic ratio: {summary['mean_diacritic_ratio']:.3f}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    items = load_items(args.items)
    records_a, name_a = _load_source(args.a, items)
    records_b, name_b = _load_source(args.b, items)
    result = compare_records(records_a, records_b)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"Head-to-head: {name_a} vs {name_b} ({result['n']} items)")
    rows = [
        [CATEGORIES[cat], str(stats["n"]), str(stats["a"]), str(stats["b"]), str(stats["tie"])]
        for cat, stats in result["per_category"].items()
    ]
    rows.append([
        "Overall", str(result["n"]),
        str(result["wins_a"]), str(result["wins_b"]), str(result["ties"]),
    ])
    print(_table(["Category", "n", f"{name_a} wins", f"{name_b} wins", "Ties"], rows))
    print(f"Mean: {name_a} {result['mean_a']:.3f} vs {name_b} {result['mean_b']:.3f}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    records, summary = load_results(args.input)
    if args.json:
        print(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2))
        return 0
    print(f"Model: {summary['model']} ({summary['n']} items)")
    print(_summary_table(summary))
    print(f"Mean diacritic ratio: {summary['mean_diacritic_ratio']:.3f}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    items = load_items(args.items)
    if args.category:
        items = [item for item in items if item.category == args.category]
        if not items:
            print(f"No items in category '{args.category}'.", file=sys.stderr)
            return 2
    grouped = items_by_category(items)
    for category, group in grouped.items():
        if not group:
            continue
        print(f"\n## {CATEGORIES[category]} ({len(group)} items)")
        for item in group:
            print(f"\n{item.id}: {item.prompt}")
            print(f"  Gloss: {item.prompt_gloss}")
            print(f"  Reference: {item.reference}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ybench",
        description="Yoruba LLM evaluation benchmark: score model responses to Yoruba prompts.",
    )
    parser.add_argument("--items", default=None, help="path to items.jsonl (default: shipped file)")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="score a model over the items")
    run.add_argument("--mock", choices=list(MOCKS), help="run a built-in mock model")
    run.add_argument("--input", help="JSONL file of model responses to score")
    run.add_argument("--model", help="model name for --input responses")
    run.add_argument("--category", choices=list(CATEGORIES), help="score one category only")
    run.add_argument("--out", help="save the full results JSON here")
    run.add_argument("--json", action="store_true", help="print machine-readable JSON")
    run.set_defaults(func=_cmd_run)

    compare = sub.add_parser("compare", help="head-to-head between two models")
    compare.add_argument("--a", required=True, help="mock name or results file for model A")
    compare.add_argument("--b", required=True, help="mock name or results file for model B")
    compare.add_argument("--json", action="store_true", help="print machine-readable JSON")
    compare.set_defaults(func=_cmd_compare)

    report = sub.add_parser("report", help="print the results table from a saved results file")
    report.add_argument("--input", required=True, help="results JSON file from 'ybench run --out'")
    report.add_argument("--json", action="store_true", help="print machine-readable JSON")
    report.set_defaults(func=_cmd_report)

    listing = sub.add_parser("list", help="show the benchmark items")
    listing.add_argument("--category", choices=list(CATEGORIES), help="show one category only")
    listing.set_defaults(func=_cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
