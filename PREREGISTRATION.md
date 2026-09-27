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

## Deviations (logged after the freeze; they change no prompts, task IDs or analyses)
1. **Throttling and retry fixes.** On 2026-09-25 the Cerebras response headers showed a 150 requests/hour limit that
   is not listed in the docs. The runner was stalling on it, so the throttle now respects the hourly limit and
   rate-limit waits are capped at 300 s. These are runtime fixes only; no completed call was re-run.
2. **Second provider for GPT-OSS (2026-09-26, 10:55 PT).** The Cerebras free tier could not finish the run before
   the deadline. The last 13 questions in run order that had no calls yet (`results/gpt-oss-120b/main/groq_qids.txt`)
   (13 questions; 8 more at 11:20 PT and 15 more at 14:05 PT, of which Groq completed 1 before its quota ran out; the 14 unfinished were returned to Cerebras and their 18 partial Groq calls discarded, leaving 22 Groq questions) were assigned in full to Groq's `openai/gpt-oss-120b`, with identical prompts, decoding, seeds and cap.
   - Every call for a given question goes to one provider, so all strategy contrasts stay within-provider for
     each question.
   - The provider is recorded per question, and a sensitivity analysis excluding Groq questions is reported.
3. **Downtime.** The host machine slept from 00:40 to about 10:40 PT on 2026-09-26. The runs paused and then
   resumed; no data were lost.
4. **Exploratory frontier supplement (added 2026-09-26, after the freeze; not part of the primary analysis).**
   - Models: `gpt-6-luna`, `gpt-6-sol` and `gpt-5.6-terra`, run through the Codex CLI with a ChatGPT account.
   - Tasks: the first 30 main questions in run order (6 per category), selected by position and not by outcome.
   - Settings: all four strategies, identical prompts, reasoning effort low.
   - Caveats: the Codex agent harness adds its own system prompt; temperature and seed cannot be set; token counts
     include about 15K tokens of harness overhead per call, so they are excluded from efficiency analyses.
   - Reporting: accuracy and paired contrasts, clearly labelled as exploratory.
   - Tools: web search, shell/code execution, sub-agents, plugins and MCP are disabled via Codex config flags. Any
     call whose event stream still shows tool use is retried up to 3 times and flagged if it persists.
   - A first 25-call attempt ran with Codex's default web search on; it was discarded unanalysed
     (`results/_discarded/gpt-6-luna-websearch-enabled`).
   - **Reasoning effort (changed 2026-09-26, 11:35 PT):** at `low`, the Codex models used 0 reasoning tokens. The
     supplement therefore switched to `high` for `gpt-6-luna`, `gpt-6-sol` and `gpt-5.6-terra`.
     - The completed `gpt-6-luna` low run (30 questions) is kept as a reasoning-effort ablation.
     - A partial `gpt-6-sol` low run (67 calls) was discarded unanalysed.
     - Main-study settings are unchanged: GPT-OSS low, Gemma thinking minimal (its only accepted level), Flash-Lite
       low.
5. **Reasoning-effort arm (added 2026-09-26, 11:50 PT, exploratory).** The aim is to test whether one high-reasoning
   call matches or beats 3-call orchestration at low reasoning.
   - Runs: Direct only, on the same first 30 main questions, for GPT-OSS (`reasoning_effort=high`, Cerebras) and
     Flash-Lite (`thinkingLevel=high`), each with an 8,192-token cap. The Codex models run all four strategies at
     high effort.
   - Gemma is excluded because the API accepts no thinking level other than `minimal`.
   - Comparisons use generated tokens (output + reasoning), not input tokens.
   - The GPT-OSS high arm was stopped after 2 calls: both used the full 8,192-token cap on reasoning without
     producing an answer, and a larger cap would consume the Cerebras quota the main study needs. Both calls were
     discarded. The arm continues with Flash-Lite (high) and the Codex models (high).
6. **GPT-OSS via Ollama cloud (added 2026-09-26, 14:15 PT, exploratory).** This restores GPT-OSS to the
   reasoning-effort arm, which had been dropped for lack of Cerebras quota.
   - `gpt-oss:120b-cloud` runs at `think=high` (16,384-token cap), all four strategies, on the same first 30
     questions.
   - A `think=low` Direct run on the same questions checks for provider differences against the Cerebras low run.
7. **Tools arm (added 2026-09-26, 17:00 PT, exploratory; motivated by the "agents without tools" critique).**
   - Model: `gpt-6-luna` at low effort, with code execution (shell/Python) and live web search enabled. Sub-agents,
     plugins, apps and MCP stay disabled.
   - Prompt: a one-sentence harness note announcing the tools is prepended. It is the only prompt difference.
   - Runs: Direct only, on (a) the first 30 main questions, compared with the existing Luna low no-tools run, and (b)
     the 32 main questions that none of the 8 main systems solved (`results/unsolved_qids.txt`), where Luna is also
     run without tools.
   - Leakage check: all search queries and commands are logged. Any call whose search or command reaches the
     benchmark itself (LAB-Bench/LABBench2 pages or datasets) is flagged and excluded.
8. **Compute with tools (added 2026-09-26, 17:45 PT, exploratory).** Same 59 questions and tool setup as item 7.
   - (a) Luna at high effort with tools, Direct.
   - (b) Luna at low effort with tools, Vote over three calls (three new tools calls), run only
     if Codex quota allows.
   - Outcome: both runs completed, with 0 leakage flags.
9. **Gemma thinking on vs off (added 2026-09-26, 18:00 PT).** This tests within one model whether debate substitutes
   for reasoning.
   - Setup: Gemma 4 31B with `thinkingLevel=high` (its default and the only alternative to `minimal`) and a
     16,384-token cap, all four strategies, on the same 150 main questions.
   - Deadline rule: if the run does not finish in time, the largest complete prefix in run order is analysed.
   - Scope change at 20:05 PT: the run was slower than expected (~3.5 calls/min), so it was restricted to Direct,
     Vote and Debate. The largest complete run-order prefix available at about 01:00 PT is analysed.
   - Host change at 20:50 PT: Google's Gemma endpoint was congested (a trivial call took 30 s), so the comparison
     moved to Ollama Cloud (`gemma4:31b-cloud`) with thinking off vs on on the same host. The setup is Direct, Vote
     and Debate on all 150 questions. The thinking-off Ollama run also serves as a cross-host replication of the main
     Gemma result.
