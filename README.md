# agenticls — controlled inference budgets for biological reasoning

Direct vs Independent×3 (vote) vs Solve→Critique→Revise vs two-scientist+adjudicator, all at 3 calls, on LAB-Bench + LABBench2 SeqQA2, deterministic scoring. See `PREREGISTRATION.md`.

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python httpx pandas pyarrow numpy scipy matplotlib biopython primer3-py pyahocorasick rapidfuzz python-dotenv pydantic
git clone https://github.com/EdisonScientific/labbench2 vendor/labbench2 && git -C vendor/labbench2 checkout c028ecdc && uv pip install --python .venv/bin/python --no-deps -e vendor/labbench2
# data: LAB-Bench parquet -> data/raw/labbench/, LABBench2 seqqa2 parquet -> data/raw/labbench2/
.venv/bin/python src/fetch_seqqa2_files.py && .venv/bin/python src/data.py
cp .env.example .env   # add keys
.venv/bin/python src/smoke.py
.venv/bin/python src/run.py --model gpt-oss-120b --split pilot
.venv/bin/python src/analyze.py --split pilot --models gpt-oss-120b gemma-4-31b
```
