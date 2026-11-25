"""Yoruba LLM evaluation benchmark.

Deterministic, offline scoring of LLM responses to Yoruba prompts:
a five-criterion 1-5 rubric with Yoruba-specific adaptations
(diacritic-folded matching, Yoruba number words, Yoruba refusal
detection), three built-in mock responders, and the ``ybench`` CLI.
"""

from __future__ import annotations

from .data import CATEGORIES, Item, load_items
from .mocks import MOCKS, respond
from .runner import aggregate, compare_models, run_jsonl, run_model
from .scorer import CRITERIA, compare_responses, score_response

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "CATEGORIES",
    "CRITERIA",
    "Item",
    "MOCKS",
    "aggregate",
    "compare_models",
    "compare_responses",
    "load_items",
    "respond",
    "run_jsonl",
    "run_model",
    "score_response",
]
