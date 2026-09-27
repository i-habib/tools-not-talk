"""Gemma 4 31B, thinking off (minimal) vs on (high): Direct, Vote, Debate on the same questions.

Tests within one model whether debate's gain over voting disappears once the model can reason.

  python src/gemma_think.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import analyze as A  # noqa: E402
import data  # noqa: E402
import scoring as S  # noqa: E402

STRATS = ["direct", "indep3", "multi3"]
TASKS = {t["qid"]: t for t in data.load("main")}


def correctness(model: str) -> dict[str, dict[str, bool]]:
    calls = A.load_calls(model, "main")
    out = {}
    for q, t in TASKS.items():
        row = {}
        for s in STRATS:
            recs = [calls.get((q, s, i)) for i in range(A.CALLS[s])]
            if any(r is None for r in recs):
                break
            if s == "indep3":
                ans = [S.parse_answer(r["text"], t) for r in recs]
                final = A.vote(ans, [S.parse_confidence(r["text"]) for r in recs], t)
            else:
                final = S.parse_answer(recs[-1]["text"], t)
            row[s] = S.is_correct(final, t)
        else:
            row["tokens"] = {s: sum(calls[(q, s, i)]["usage"]["output_tokens"] for i in range(A.CALLS[s]))
                             for s in STRATS}
            out[q] = row
    return out


def paired(a: np.ndarray, b: np.ndarray) -> dict:
    d = a.astype(float) - b.astype(float)
    idx = np.random.default_rng(A.BOOT_SEED).integers(0, len(d), (A.N_BOOT, len(d)))
    m = d[idx].mean(1)
    return {"delta": float(d.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))],
            **A.mcnemar(a, b)}


def main():
    off_name, on_name = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("gemma-4-31b-ollama-off", "gemma-4-31b-ollama-on")
    off, on = correctness(off_name), correctness(on_name)
    qs = [q for q in TASKS if q in off and q in on]
    if not qs:
        print("no overlapping complete questions yet")
        return
    arr = lambda d, s: np.array([d[q][s] for q in qs], bool)  # noqa: E731
    res = {"n": len(qs)}
    for tag, d in [("off", off), ("on", on)]:
        res[tag] = {s: float(arr(d, s).mean()) for s in STRATS}
        res[tag]["tokens"] = {s: float(np.mean([d[q]["tokens"][s] for q in qs])) for s in STRATS}
        res[tag]["debate_minus_vote"] = paired(arr(d, "multi3"), arr(d, "indep3"))
    res["direct_on_minus_off"] = paired(arr(on, "direct"), arr(off, "direct"))
    res["direct_on_minus_debate_off"] = paired(arr(on, "direct"), arr(off, "multi3"))
    (A.OUT / "gemma_think.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
