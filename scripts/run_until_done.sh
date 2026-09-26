#!/bin/zsh
# Re-launch a run until every question is complete (survives quota exhaustion / transient errors).
# usage: scripts/run_until_done.sh <model> [extra run.py args...]
cd "$(dirname $0)/.."
model=$1; shift
while true; do
  out=$(.venv/bin/python -W ignore src/run.py --model $model --split main "$@" 2>&1 | tee -a logs/main_$model.log | tail -1)
  echo "$(date '+%F %T') $out" >> logs/main_$model.status
  if echo "$out" | grep -qE ': ([0-9]+)/\1 questions complete'; then break; fi
  sleep 600
done
