#!/bin/zsh
# Exploratory supplement: first 30 main questions for each Codex-served model, one model at a time.
cd "$(dirname $0)/.."
for m in gpt-6-luna gpt-6-sol gpt-5.6-terra; do
  .venv/bin/python -W ignore src/run.py --model $m --split main --limit 30 --concurrency 4 --parallel-questions 3 >> logs/codex_$m.log 2>&1
  tail -1 logs/codex_$m.log
done
