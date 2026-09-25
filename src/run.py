"""Run all four strategies for one model over a split. Resumable: completed calls are cached in
results/<model>/<split>/calls.jsonl and never re-requested.

  python src/run.py --model gpt-oss-120b --split pilot
  python src/run.py --model gpt-oss-120b --split main --token-budget 900000
  python src/run.py --model flash-lite --split main --flash-only --max-requests 480
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data  # noqa: E402
from llm import LLM, MODELS, QuotaExhausted  # noqa: E402
from strategies import CALLS, STRATEGIES, run_strategy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


class Stop(Exception):
    pass


async def main(args):
    cfg = MODELS[args.model]
    if args.max_tokens:
        cfg.max_tokens = args.max_tokens
    tasks = data.load(args.split, flash_only=args.flash_only)
    if args.limit:
        tasks = tasks[: args.limit]
    out_dir = ROOT / "results" / cfg.name / args.split
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "calls.jsonl"
    cache = {}
    if log_path.exists():
        for line in log_path.open():
            r = json.loads(line)
            if not r.get("error"):
                cache[(r["qid"], r["strategy"], r["step"])] = r
    (out_dir / "config.json").write_text(json.dumps(cfg.__dict__, indent=1))

    llm = LLM(cfg, concurrency=args.concurrency)
    log = log_path.open("a")
    spent = {"tokens": 0, "requests": 0}
    stop = asyncio.Event()

    async def do_task(task):
        async def call(step, prompt, seed):
            key = (task["qid"], strategy, step)
            if key in cache:
                return cache[key]["text"]
            if stop.is_set():
                raise Stop()
            try:
                res = await llm.complete(prompt, seed)
                err = None
            except QuotaExhausted as e:
                stop.set()
                print(f"[quota] daily quota exhausted: {e}", flush=True)
                raise Stop()
            except Exception as e:  # logged; rerun retries it
                res, err = {"text": "", "usage": {"total_tokens": 0}}, repr(e)[:800]
            rec = {"qid": task["qid"], "category": task["category"], "strategy": strategy, "step": step,
                   "seed": seed, "model": cfg.model, "prompt": prompt, **res, "error": err,
                   "ts": datetime.now(timezone.utc).isoformat()}
            log.write(json.dumps(rec) + "\n")
            log.flush()
            spent["tokens"] += res["usage"]["total_tokens"]
            spent["requests"] += 1
            if err:
                print(f"[error] {task['qid'][:8]} {strategy}:{step} {err[:200]}", flush=True)
                raise Stop()
            cache[key] = rec
            if (args.token_budget and spent["tokens"] >= args.token_budget) or \
               (args.max_requests and spent["requests"] >= args.max_requests):
                stop.set()
            return res["text"]

        results = []
        for strategy in STRATEGIES if not args.strategies else args.strategies.split(","):
            try:
                await run_strategy(strategy, task, call)
                results.append(True)
            except Stop:
                results.append(False)
        return all(results)

    t0 = time.time()
    sem = asyncio.Semaphore(args.parallel_questions)
    done = 0

    async def guarded(task):
        nonlocal done
        async with sem:
            if stop.is_set() and not all((task["qid"], s, i) in cache for s in STRATEGIES for i in range(CALLS[s])):
                return False
            ok = await do_task(task)
            done += ok
            if done % 10 == 0 and ok:
                print(f"[{time.time()-t0:6.0f}s] {done}/{len(tasks)} questions complete; "
                      f"this run: {spent['requests']} req, {spent['tokens']:,} tok", flush=True)
            return ok

    oks = await asyncio.gather(*(guarded(t) for t in tasks))
    await llm.aclose()
    log.close()
    n_ok = sum(oks)
    print(f"DONE model={cfg.name} split={args.split}: {n_ok}/{len(tasks)} questions complete; "
          f"this run {spent['requests']} requests, {spent['tokens']:,} tokens, {time.time()-t0:.0f}s"
          + (" (stopped early: budget/quota)" if stop.is_set() else ""), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--split", default="pilot", choices=["pilot", "main", "reserve"])
    ap.add_argument("--flash-only", action="store_true", help="restrict to the 75-question Flash-Lite subset")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--strategies", help="comma-separated subset (default: all four)")
    ap.add_argument("--token-budget", type=int, help="stop starting new calls after this many tokens this run")
    ap.add_argument("--max-requests", type=int, help="stop after this many requests this run")
    ap.add_argument("--max-tokens", type=int, help="override per-call completion cap")
    ap.add_argument("--concurrency", type=int, default=8, help="max in-flight requests")
    ap.add_argument("--parallel-questions", type=int, default=4)
    asyncio.run(main(ap.parse_args()))
