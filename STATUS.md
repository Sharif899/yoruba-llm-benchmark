# Status: normative reasoning set and live gap run

## The set

- 20 original paired scenarios, 40 items: `yb-nor-01` to `yb-nor-20`
  in Yoruba and `yb-nor-en-01` to `yb-nor-en-20` in English, the
  same scenario in both languages.
- New category `normative_reasoning` in `data/items.jsonl` and
  `src/yoruba_benchmark/data/items.jsonl` (copies identical).
- Total items: 100 (60 original + 40 normative).
- No new scoring criterion. The existing 5 criterion rubric
  measures normative correctness through agreement with the
  reference; every prompt asks for reasons and every reference
  shows steps. Documented in `data/README.md`.
- Originality: every scenario written fresh for this benchmark,
  inspired by the idea of AfriNORM (normative and social
  reasoning) but nothing copied from AfriNORM or any dataset.
  Stated in `data/README.md`.

## Tests

- 127 tests, all passing (verified 27 November 2026).
- 117 original tests still pass, unchanged in behaviour.
- 10 new tests: 9 in `tests/test_normative.py` (40 items, 20 per
  language, pairing by number, language checks, reasoning
  prompts, step references, no unsafe markers, no digits in
  references, model-a passes every normative item, model-c
  mock gap of at least 1.0) and 1 in `tests/test_scorer.py`
  (English "First" counts as a step marker, matching Yoruba
  "Àkọ́kọ́", so paired items are scored fairly).

## Live run

- Run id: 20261127-gemini-3.5-flash-lite-normative
- Model: gemini-3.5-flash-lite, temperature 0, max tokens 600,
  throttle 8.5 seconds.
- Date: 27 November 2026, 09:00 to 09:08 WAT (after the daily
  limit reset at 09:00 WAT).
- 40 calls, 40 answered, 0 failed, 0 rate limited.
- Results: `results/20261127-gemini-3.5-flash-lite-normative/`
  (responses.jsonl and scored.json).
- Report: `docs/NORMATIVE_GAP_REPORT.md`, plus a summary table
  in the README.

## Live results

- Yoruba: mean 3.690, pass 1 of 20 (0.050), diacritic 0.866.
- English: mean 3.620, pass 0 of 20 (0.000), diacritic 0.000.
- Gap (Yoruba minus English): mean +0.070, pass rate +0.050.
  Essentially no measurable gap on 20 scenarios.
- Per criterion, Yoruba then English: factual 2.35 / 2.10,
  reasoning 5.00 / 5.00, instruction 3.05 / 3.00, helpfulness
  3.05 / 3.00, safety 5.00 / 5.00.
- Overall: mean 3.655, pass 1 of 40 (0.025).

## What the numbers mean

- The absolute mean understates the model. A hand check of the
  responses found the right judgement on 19 of the 20 Yoruba
  scenarios and on the English ones read. The low scores are a
  recall artefact: the references are short and the model's
  answers are long and worded differently, so recall is 0.3 to
  0.5 and maps to 2 or 3 on factual, instruction and helpfulness.
- One genuine Yoruba error: scenario 16, where the model read
  "sípù" as sweets instead of whistling. The English answer to
  the same scenario is correct. See the gap report.
- The model answers in Yoruba (diacritic 0.866) and writes
  nearly twice as long in English (2,039 characters on average
  against 1,073 in Yoruba) without scoring higher.

## Known limitations

- 20 scenarios is small; a gap of 0.070 on 20 items is noise.
- The scorer measures token overlap with a short reference, not
  whether the judgement is right. A correct answer phrased
  differently scores low on recall; the hand check in the gap
  report is the honest check.
- One reference per item; a reasonable answer that takes a
  different route (scenarios 08 and 20) scores low on recall.
- Scenario 16 is ambiguous in Yoruba: "sípù" covers both
  whistling and sweets. Reword before using it to compare models.
- Mock scores in the README are illustrative only, never live
  results. The live numbers are in the gap report and the README
  live run section.
- One model, one run, temperature 0, 27 November 2026.

## Not yet done

- Publish to GitHub (parent verifies and publishes after this
  report). Do not push from here.
- The CV says this repo has 117 tests; it now has 127. Do not
  change the CV without the user's say-so.
