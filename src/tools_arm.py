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


def voted(model: str):
    """Majority vote over the three indep3 tool calls, as a pseudo-record {text, usage, tool_details}."""
    calls = A.load_calls(model, "main")
    out = {}
    for q, t in TASKS.items():
        recs = [calls.get((q, "indep3", i)) for i in range(3)]
        if any(r is None for r in recs):
            continue
        ans = [S.parse_answer(r["text"], t) for r in recs]
        final = A.vote(ans, [S.parse_confidence(r["text"]) for r in recs], t)
        out[q] = {"text": f"<answer>{final}</answer>" if final is not None else "",
                  "usage": {"output_tokens": sum(r["usage"]["output_tokens"] for r in recs)},
                  "tool_items": [x for r in recs for x in r.get("tool_items", [])],
                  "tool_details": [x for r in recs for x in r.get("tool_details", [])],
                  "tool_leak": any(r.get("tool_leak", False) for r in recs)}
    return out


def leaked(rec) -> bool:
    # public logs carry the precomputed flag instead of the search queries (see export_public_logs.py)
    return rec.get("tool_leak", False) or bool(LEAK.search(json.dumps(rec.get("tool_details", []))))


def compare(qids, base, tools):
    qs = [q for q in qids if q in base and q in tools and not leaked(tools[q]) and not leaked(base[q])]
    if not qs:
        return None
    b = np.array([S.is_correct(S.parse_answer(base[q]["text"], TASKS[q]), TASKS[q]) for q in qs], bool)
    t = np.array([S.is_correct(S.parse_answer(tools[q]["text"], TASKS[q]), TASKS[q]) for q in qs], bool)
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
    # compute on top of tools: each vs tools@low Direct (paired, same questions)
    for name, arm in [("tools_high", direct("gpt-6-luna-tools-high")), ("tools_vote", voted("gpt-6-luna-tools"))]:
        if arm:
            out[name] = {"first30": compare(Q30, tools, arm), "unsolved": compare(UNSOLVED, tools, arm),
                         "n_leak_flagged": sum(leaked(r) for r in arm.values())}
    (A.OUT / "tools_arm.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
