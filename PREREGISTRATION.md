# Pre-registration: Where does the agentic gain come from?

Status: **FROZEN** (2026-09-25, after pilot; before any main-split call).
After that commit, prompts, task IDs, model configs and the analysis script do not change.

## Question
At a matched budget of three model calls per question, does structured agent interaction beat simply
spending those calls on independent samples plus a majority vote?

## Tasks (frozen by `src/data.py`, seed 20260925; IDs in `data/task_ids.csv`)
- LAB-Bench (futurehouse/lab-bench, public HF release): ProtocolQA, SeqQA, DbQA, LitQA2. These are multiple choice,
  and options are shuffled per question with a fixed seed. There is no "insufficient information" option.
- LABBench2 SeqQA2 (EdisonScientific/labbench2 at commit c028ecdc; data from the public mirror of the HF release).
  Only items with a unique ground-truth answer are used, excluding `restriction_counts` (its input is a 1.5 MB
  genome) and 2 items whose gold answer fails the official validator. Input files are injected into the prompt
  (official "inject" mode) and scored with the **official LABBench2 validators**.
- Items whose prompt is longer than 6,000 characters are excluded.
- Per category, 2 pilot items (excluded from all reported results), 30 main items and 15 Flash-Lite subset items
  (a subset of main).
- FigQA/TableQA are excluded (the models are text-only). CloningScenarios is excluded (prompt length).
- There is **no LLM judge anywhere**.

## Strategies (`src/strategies.py`)
| | Calls | Final answer |
|---|---|---|
| A. Direct | 1 | parsed answer |
| B. Independent×3 | 3 independent solves | majority over equivalent answers; with no majority, highest self-reported confidence (earliest wins a tie) |
| C. Solve → Critique → Revise | 3 sequential | answer from the revise call |
| D. Researcher + skeptic (independent) → adjudicator | 3 | answer from the adjudicator |

- Only visible output is passed between calls, never hidden reasoning.
- Every call is a single user message with identical decoding parameters: temperature 0.6, a fixed per-(strategy,
  step) seed, and a completion cap of `max_tokens` (frozen after the pilot).
- GPT-OSS runs with `reasoning_effort=low`.
- Answer equivalence for voting: MC answers match on the letter. Numeric answers match within 1% relative
  difference. Lists match as order-insensitive sets.
- A missing or unparseable answer counts as incorrect and does not vote.

## Models
- **Primary:** `gpt-oss-120b` (Cerebras free tier) and `gemma-4-31b-it` (Gemini API free tier), each on all 150
  main items.
- **Auxiliary:** `gemini-3.5-flash-lite` on the 75-item subset.
- There is no per-model prompt tuning.

## Hypotheses and primary analysis (`src/analyze.py`)
- **Primary contrast:** accuracy(D, multi-agent) − accuracy(B, independent×3), per model. Reported as a paired
  bootstrap 95% CI (10,000 resamples over questions, seed 20260925) plus an exact McNemar test.
- **Secondary contrasts:** C − B, B − A, D − A, C − A, D − C.
- **Mechanism analyses:**
  - accuracy on the disagreement subset (the 3 independent samples are not unanimous);
  - rescue rate P(correct | vote wrong) and corruption rate P(wrong | vote right) for C and D relative to B;
  - self-revision flips within C;
  - adjudicator accuracy when the two scientists disagree.
- **Efficiency:** mean total tokens per question (input + output + reasoning) and correct answers per million
  tokens.
- **Emphasis:** effect sizes and CIs, not p < 0.05. No multiple-comparison correction on secondary contrasts; they
  are labelled exploratory.

## Decision rules (applied on pilot items only, before freezing)
- **Saturation:** if pilot Direct accuracy is > 90% on a category, replace that category's items with harder ones.
- **Floor:** if Direct is < 25–30% and all methods are near chance, drop the category.
- **Token overrun:** if GPT-OSS averages more than ~1,100–1,200 tokens per call, reduce N from 150 to 120. Do not
  drop conditions.
- **Truncation:** if more than 5% of pilot calls hit the completion cap, raise `max_tokens` once before freezing.
- **Flash-Lite:** if it is dramatically worse than both primary models, report it in the appendix only.
- **Failures:** API errors are retried. Calls that still fail are re-run later with the same seed. A question counts
  only if all 10 of its calls completed.

## Pilot outcome (10 pilot items × 10 calls × 3 models, plus a Direct-only calibration on 20 reserve items/category)
- **Tokens:** GPT-OSS averaged 632 tokens/call (pilot, all strategies) and 979 (reserve, Direct). Below the reduction
  threshold, so **N = 150**.
- **Truncation:** at a 1,024-token cap, Gemma and Flash-Lite each hit the cap on 5/100 calls, all in solve calls, where
  a hit means no answer. `max_tokens` was **raised once to 2,048** for all models.
  - Residual Gemma truncation at 2,048 is due to long visible working on SeqQA items. It is reported, not tuned.
- **Gemma thinking:** by default, Gemma 4 spent the entire cap on hidden thinking in every call and produced no
  answers. `thinkingConfig.thinkingLevel` is set to `minimal` (thinking off). This is the only accepted value; `low`
  and `thinkingBudget` return HTTP 400. Those 100 discarded calls are not analysed.
- **Flash-Lite:** `thinkingLevel = low`.
- **Saturation/floor:** Direct accuracy on 20 reserve items per category was:

  | Model | ProtocolQA | SeqQA | DbQA | LitQA2 | SeqQA2 |
  |---|---|---|---|---|---|
  | GPT-OSS | 0.60 | 0.60 | 0.30 | 0.55 | 0.50 |
  | Gemma (~13/cat) | 0.69 | 0.38 | 0.71 | 0.31 | 0.46 |

  No category is > 90%, and none is at chance for both models, so **no categories were replaced or dropped**.
- **Stopping rule (quota):** questions run in a fixed round-robin order over categories. If a model's run is not
  complete by 2026-09-26 20:00 PT, the analysis uses the largest complete prefix in that order (category-balanced), and
  that prefix is reported.
