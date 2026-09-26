#!/bin/zsh
cd "$(dirname $0)/.."
.venv/bin/python -W ignore src/run.py --model gpt-oss-120b-ollama-high --split main --limit 30 --concurrency 6 --parallel-questions 4 >> logs/ollama_high.log 2>&1; tail -1 logs/ollama_high.log
.venv/bin/python -W ignore src/run.py --model gpt-oss-120b-ollama-low --split main --limit 30 --strategies direct --concurrency 6 --parallel-questions 6 >> logs/ollama_low.log 2>&1; tail -1 logs/ollama_low.log
