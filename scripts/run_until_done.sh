#!/bin/zsh
# Re-launch a run until every question is complete (survives quota exhaustion / transient errors).
# usage: scripts/run_until_done.sh <model> [extra run.py args...]
cd "$(dirname $0)/.."
model=$1; shift
while true; do
  out=$(.venv/bin/python -W ignore src/run.py --model $model --split main "$@" 2>&1 | tee -a logs/main_$model.log | tail -1)
  echo "$(date '+%F %T') $out" >> logs/main_$model.status
  n=$(echo "$out" | sed -nE 's/.*: ([0-9]+)\/([0-9]+) questions complete.*/\1 \2/p')
  set -- ${=n} "$@"; done_q=$1; total=$2; shift 2
  [[ -n "$done_q" && "$done_q" == "$total" ]] && break
  sleep 600
done
