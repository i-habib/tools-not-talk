# Tools, Not Talk: The Knowledge Ceiling of Biology Agents

Code, call logs, and analysis for the paper of the same name (NeurIPS 2026 AgenticLS workshop).

Many agent systems for biology add orchestration on top of a model: a critic that reviews the answer, two "scientists" who debate, or a longer reasoning budget. We tested whether that helps on biology questions that can be scored automatically, using 150 preregistered questions from LAB-Bench and LABBench2. Every strategy got the same budget of three model calls, so the baseline is three independent samples with a majority vote, not a single call.

- Solve → critique → revise never beat majority voting.
- Debate beat voting only for a model with its reasoning turned off.
- Raising reasoning effort produced up to 25× more tokens with no gain in accuracy.
- Which question was asked explains 56% of the variance in correctness. The choice of model, strategy, and reasoning effort together explain 0.6%.
- One call with web search and code execution solved 47% of the questions that all eight systems in the main study got wrong.

The paper is in [`paper/main.pdf`](paper/main.pdf). The protocol was frozen before any main-split call and is in [`PREREGISTRATION.md`](PREREGISTRATION.md), which also lists every deviation. The freeze is commit `Freeze protocol after pilot` in the history.

## Layout

```
src/
  data.py              builds the frozen question pool and splits from the public benchmark files
  strategies.py        the four strategies and their prompts
  llm.py               API clients (Cerebras, Gemini, Groq, Ollama, Codex CLI) with rate limiting and retries
  run.py               runs one model over a split; resumable
  scoring.py           answer parsing and deterministic scoring (no LLM judge)
  analyze.py           preregistered analysis: contrasts, bootstrap CIs, McNemar tests, figures 1-2
  think_vs_talk.py     one high-effort call vs. three low-effort calls; `ceiling` runs the variance decomposition
  tools_arm.py         the web search + code execution arm, with a check for searches that hit the benchmark
  paper_numbers.py     writes every number in the paper to paper/numbers.tex
  make_tables.py       writes the appendix category table
  export_public_logs.py  strips benchmark text from call logs (see below)
results/
  <model>/<split>/calls*.jsonl   one line per model call (sanitized)
  analysis/                      outputs of the scripts above
  figures/
data/task_ids.csv      the 150 main + pilot + reserve question IDs
tests/
```

## Reproducing the paper's numbers

This needs the public benchmark files but no API keys, because the call logs are included.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
git clone https://github.com/EdisonScientific/labbench2 vendor/labbench2
git -C vendor/labbench2 checkout c028ecdc && pip install --no-deps -e vendor/labbench2
```

Download the LAB-Bench parquet files for ProtocolQA, SeqQA, DbQA, and LitQA2 from the `futurehouse/lab-bench` Hugging Face dataset into `data/raw/labbench/`, and the LABBench2 SeqQA2 parquet into `data/raw/labbench2/seqqa2.parquet`. Then:

```bash
python src/fetch_seqqa2_files.py      # SeqQA2 input and validator files
python src/data.py                    # writes data/tasks.jsonl; IDs should match data/task_ids.csv
python -m pytest -q tests              # 98 tests; several need data/tasks.jsonl

python src/analyze.py --split main --models gpt-oss-120b gemma-4-31b flash-lite
python src/think_vs_talk.py
python src/think_vs_talk.py ceiling
python src/tools_arm.py
python src/paper_numbers.py
python src/make_tables.py --split main
```

The regenerated `results/analysis/` files and `paper/numbers.tex` should match the committed ones. `results/analysis/gemma_think.json` is the exception: it comes from an exploratory Gemma thinking-on/off run that was still in progress at submission and is not reported in the paper.

## Rerunning the model calls

Copy `.env.example` to `.env` and add keys. The primary models run on free tiers: GPT-OSS-120B on Cerebras (Groq as fallback) and Gemma 4 31B and Gemini 3.5 Flash-Lite on the Gemini API. The GPT-6 and GPT-5.6 runs go through the Codex CLI, and the high-effort GPT-OSS runs go through Ollama's cloud models, so those need the respective CLI logged in.

```bash
python src/smoke.py                                   # one mock call per strategy
python src/run.py --model gpt-oss-120b --split main
```

`run.py` caches every completed call in `results/<model>/<split>/calls.jsonl` and skips it on the next run, so an interrupted run can be restarted with the same command. The scripts in `scripts/` are the exact launch commands used for the supplementary arms.

## About the call logs

LAB-Bench asks that its questions not be posted where crawlers can pick them up. The raw logs contain the full prompt and the model's response, which often restates the question, so they are not in this repository. The committed logs were written by `src/export_public_logs.py`. Each record keeps the question ID, strategy, step, seed, token usage, latency, finish reason, and the model's parsed answer and confidence. The model's text is replaced by a two-line stand-in that the scoring code reads back to the same answer and confidence. For the tools arm, the search queries are replaced by a single flag recording whether any query touched the benchmark. Running the analysis on the raw and the sanitized logs gives byte-identical outputs.

If you need the raw logs for research, open an issue.

## Citation

```bibtex
@inproceedings{habib2026toolsnottalk,
  title     = {Tools, Not Talk: The Knowledge Ceiling of Biology Agents},
  author    = {Habib, Ivan},
  booktitle = {NeurIPS 2026 AgenticLS Workshop},
  year      = {2026}
}
```

## License

Code is MIT licensed. LAB-Bench and LABBench2 are distributed under their own terms.
