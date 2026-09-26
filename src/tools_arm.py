"""Tools arm: GPT-6 Luna (low effort, Direct) with vs without code execution + web search.

Sets: the first 30 main questions, and the questions no main system (GPT-OSS, Gemma x 4 strategies) solved.
Calls whose searches/commands touch the benchmark itself are flagged and excluded (both conditions, paired).

  python src/tools_arm.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import analyze as A  # noqa: E402
import data  # noqa: E402
import scoring as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LEAK = re.compile(r"lab-?bench|labbench|futurehouse|edisonscientific|huggingface\.co/datasets|canary", re.I)
TASKS = {t["qid"]: t for t in data.load("main")}
Q30 = [t["qid"] for t in data.load("main")[:30]]
UNSOLVED = (ROOT / "results" / "unsolved_qids.txt").read_text().split()


def direct(model: str):
    calls = A.load_calls(model, "main")
    return {q: r for (q, s, i), r in calls.items() if s == "direct" and i == 0}


def leaked(rec) -> bool:
    return bool(LEAK.search(json.dumps(rec.get("tool_details", []))))


def compare(qids, base, tools):
    qs = [q for q in qids if q in base and q in tools and not leaked(tools[q])]
    b = np.array([S.is_correct(S.parse_answer(base[q]["text"], TASKS[q]), TASKS[q]) for q in qs])
    t = np.array([S.is_correct(S.parse_answer(tools[q]["text"], TASKS[q]), TASKS[q]) for q in qs])
    d = t.astype(float) - b.astype(float)
    idx = np.random.default_rng(A.BOOT_SEED).integers(0, len(d), (A.N_BOOT, len(d)))
    m = d[idx].mean(1)
    by = {}
    for c in data.CATEGORIES:
        ii = [k for k, q in enumerate(qs) if TASKS[q]["category"] == c]
        if ii:
            by[c] = {"n": len(ii), "no_tools": float(b[ii].mean()), "tools": float(t[ii].mean())}
    used = [bool(tools[q].get("tool_items")) for q in qs]
    return {"n": len(qs), "no_tools": float(b.mean()), "tools": float(t.mean()), "delta": float(d.mean()),
            "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))],
            "mcnemar": A.mcnemar(t, b), "by_category": by, "tool_use_rate": float(np.mean(used)),
            "tokens_no_tools": float(np.mean([base[q]["usage"]["output_tokens"] for q in qs])),
            "tokens_tools": float(np.mean([tools[q]["usage"]["output_tokens"] for q in qs]))}


def main():
    base, tools = direct("gpt-6-luna"), direct("gpt-6-luna-tools")
    leaks = [q for q, r in tools.items() if leaked(r)]
    kinds = Counter(k for r in tools.values() for k in r.get("tool_items", []))
    out = {"first30": compare(Q30, base, tools), "unsolved": compare(UNSOLVED, base, tools),
           "n_leak_flagged": len(leaks), "tool_calls": dict(kinds)}
    (A.OUT / "tools_arm.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
