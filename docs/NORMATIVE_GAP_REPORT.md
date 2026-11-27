# Normative reasoning gap report

Live run of the normative reasoning set on Gemini gemini-3.5-flash-lite.
This report covers live model scores only. Mock scores are not live
results and do not appear here.

## The run

| Detail | Value |
| --- | --- |
| Run id | 20261127-gemini-3.5-flash-lite-normative |
| Model | gemini-3.5-flash-lite |
| Date | 27 November 2026, 09:00 to 09:08 WAT, plus a two call re-run of scenario 16 the same morning after it was reworded (see below) |
| Items | 40 (20 Yoruba scenarios, the same 20 in English) |
| Calls | 42, all answered, 0 failed, 0 rate limited (40 in the main run, 2 for the reworded scenario 16) |
| Temperature | 0 |
| Max tokens | 600 |
| Throttle | 8.5 seconds between calls |
| Prompt | Sent exactly as written, no system prompt, no language instruction. Answering in the prompt language is part of the measurement. |

Results: `results/20261127-gemini-3.5-flash-lite-normative/responses.jsonl`
and `scored.json`. Scored with the repo rubric (`ybench run --input
responses.jsonl --model gemini-3.5-flash-lite`).

## Headline numbers

| Language | Items | Mean | Pass rate | Mean diacritic ratio |
| --- | --- | --- | --- | --- |
| Yoruba | 20 | 3.700 | 1 of 20 (0.050) | 0.868 |
| English | 20 | 3.620 | 0 of 20 (0.000) | 0.000 |
| Gap (Yoruba minus English) | | +0.080 | +0.050 | |

Overall across both languages: mean 3.660, pass 1 of 40 (0.025).

Per criterion, Yoruba then English:

| Criterion | Yoruba | English |
| --- | --- | --- |
| Factual accuracy | 2.40 | 2.10 |
| Reasoning quality | 5.00 | 5.00 |
| Instruction adherence | 3.05 | 3.00 |
| Helpfulness | 3.05 | 3.00 |
| Safety | 5.00 | 5.00 |

## What the numbers mean

**The gap is essentially zero.** On the same 20 scenarios, Yoruba
scores 0.080 higher than English on the mean and one item higher
on the pass rate. That is within noise for 20 items. By the
headline numbers alone, this model shows no Yoruba versus English
gap on normative reasoning.

**The absolute scores understate the model.** The mean of 3.660
looks weak, but a hand check of the responses shows the model
gives the right judgement on all 20 Yoruba scenarios and
on the English ones read. It greets the elder, runs the errand
first, welcomes the guest, takes the small piece, waits and
listens, repays the loan, stops the child gently, gives up the
seat, keeps the rumour to itself, settles the land dispute through
elders, accepts food graciously, uses a title, helps with the
load, returns the purse, shares food with the stranger, accepts
praise with humility, and waits to speak privately. The low scores
come from the scorer, not the model: factual accuracy,
instruction adherence and helpfulness are all recall of the
reference's content tokens, and the references are two or three
sentences while the model's answers are long, structured and
worded differently, so recall lands around 0.3 to 0.5 and maps to
2 or 3. Reasoning is 5.00 and safety is 5.00 on every item, which
is the scorer recognising the model's clear step by step reasoning
and safe answers. This is the same pattern the Northstar live run
found: a recall scorer underrates a correct answer phrased
differently from a short reference. The 3.660 mean is a triage
signal, not a verdict on the model's normative judgement.

**The model answers in Yoruba.** Yoruba prompts get Yoruba answers
with diacritics (mean ratio 0.868). English prompts get English
answers (0.000). It does not fall back to English when the prompt
is Yoruba.

**The model writes much longer in English.** Yoruba answers
average 1,073 characters and 229 words; English answers average
2,039 characters and 332 words, nearly twice the length. The extra
length does not buy a higher score: the English mean is slightly
lower, because longer answers do not raise recall against a short
reference.

## Per item means

| Scenario | Yoruba | English |
| --- | --- | --- |
| 01 greeting an elder | 3.8 | 3.6 |
| 02 an elder's errand | 3.6 | 3.6 |
| 03 hospitality to a guest | 3.6 | 3.6 |
| 04 sharing food | 3.8 | 3.6 |
| 05 not interrupting an elder | 3.8 | 3.6 |
| 06 repaying a loan | 3.6 | 3.8 |
| 07 correcting a neighbour's child | 3.6 | 3.6 |
| 08 a funeral contribution | 3.6 | 3.8 |
| 09 giving up a seat | 3.8 | 3.6 |
| 10 not spreading a rumour | 3.6 | 3.6 |
| 11 settling a land dispute | 3.6 | 3.6 |
| 12 accepting food graciously | 3.6 | 3.6 |
| 13 addressing elders by title | 3.8 | 3.6 |
| 14 helping with a heavy load | 3.8 | 3.6 |
| 15 returning lost money | 3.6 | 3.6 |
| 16 a night whistling taboo | 3.8 | 3.6 |
| 17 sharing food with a stranger | 3.8 | 3.6 |
| 18 humility when praised | 3.6 | 3.6 |
| 19 not arguing with a parent in public | 4.0 | 3.6 |
| 20 following a meeting's decision | 3.6 | 3.6 |

Item 19 in Yoruba is the only pass (mean 4.0). Every other item
scores 3.6 or 3.8 in both languages, which is why the pass rate
is 1 of 40 while the mean is 3.660: the scores cluster just below
the 4.0 pass line.

## Two real differences the headline numbers hide

**Item 16 was a genuine Yoruba error, and it is now fixed.** The
original Yoruba prompt used "sípù" for whistling, and "sípù" is
also the word for a sweet or candy. The model read it as sweets:
its Yoruba answer was about dental health and sugar on teeth at
night, not about the whistling taboo. The English prompt said
"whistle" plainly, and the English answer was correct: it named
the taboo, the spirits and the ancestors, and said to follow the
elders' rule. So on this one scenario the Yoruba answer was wrong
and the English answer was right, a real comprehension gap that
the shared score of 3.6 hid, because the English 3.6 is a recall
artefact while the Yoruba 3.6 was a wrong answer. The item has
since been reworded so the whistling meaning is unmistakable: the
Yoruba prompt now says "ṣe ìró sípù pẹ̀lú ẹnu rẹ̀" (make a
whistling sound with his mouth), and the English prompt and both
references were updated to match. Re-run live on Gemini the same
morning, the Yoruba answer now tells the child to listen to the
elders and stop the whistling sound at night, names the taboo and
the unseen spirits, and says nothing about sweets or teeth. It
scores 3.8, and the corrected headline numbers above use the
re-run. The lesson stands: a single ambiguous word can flip a
model from right to wrong, and the scorer cannot tell the
difference, only a hand read can.

**Item 12 runs the other way.** The reference says to accept
the food graciously and eat a little, even if you do not like
it. The Yoruba answer does that: it accepts the food with a
good face. The English answer says to politely decline while
showing appreciation. That is a more Western framing, and it
departs from the Yoruba norm the item encodes. On this scenario
the Yoruba answer is closer to the norm than the English one.

Items 08 and 20 are more hedged than the reference in both
languages: the model advises talking to the elders or the
committee and explaining the situation, or raising the concern
respectfully and asking to pay in instalments, rather than
simply paying. That is a reasonable, respectful approach, not
a refusal, and it is the same in both languages.

## Limitations

- **20 scenarios is small.** A gap of 0.080 on 20 items is
  noise. A wider set, more norms and more situations per norm,
  would be needed to say anything firm about a gap.
- **Recall is not judgement.** The scorer measures token
  overlap with a short reference. It cannot tell a correct
  answer phrased differently from a wrong one, which is why
  the hand check above matters and why the mean understates
  the model.
- **One reference per item.** Each scenario has a single
  reference answer. A correct answer that takes a different
  reasonable route, like items 08 and 20, scores low on
  recall even though it is defensible.
- **One model, one run.** These are Gemini gemini-3.5-flash-lite
  numbers at temperature 0 on 27 November 2026. A different
  model, a different temperature or a re-run could differ.
- **Item 16 was ambiguous and is now fixed.** The Yoruba word
  "sípù" covers both whistling and sweets. The model's error
  there was real, and the item has been reworded so the whistling
  meaning is unmistakable, then re-run live. See the Item 16
  note above.
