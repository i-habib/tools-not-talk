#!/bin/zsh
cd "$(dirname $0)/.."
.venv/bin/python -W ignore src/run.py --model gpt-6-luna --split main --strategies direct --ids-file results/unsolved_qids.txt --concurrency 4 --parallel-questions 4 >> logs/tools_nolook.log 2>&1 &
.venv/bin/python -W ignore src/run.py --model gpt-6-luna-tools --split main --strategies direct --ids-file results/tools_qids.txt --concurrency 4 --parallel-questions 4 >> logs/tools.log 2>&1
wait
tail -1 logs/tools_nolook.log; tail -1 logs/tools.log
