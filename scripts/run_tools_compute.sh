#!/bin/zsh
cd "$(dirname $0)/.."
.venv/bin/python -W ignore src/run.py --model gpt-6-luna-tools-high --split main --strategies direct --ids-file results/tools_qids.txt --concurrency 4 --parallel-questions 4 >> logs/tools_high.log 2>&1
tail -1 logs/tools_high.log
.venv/bin/python -W ignore src/run.py --model gpt-6-luna-tools --split main --strategies indep3 --ids-file results/tools_qids.txt --concurrency 4 --parallel-questions 3 >> logs/tools_vote.log 2>&1
tail -1 logs/tools_vote.log
