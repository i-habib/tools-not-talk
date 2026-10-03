"""Write a shareable copy of the call logs with all benchmark text removed.

The raw logs contain the prompt (question text) and the model's full response, which often restates the
question. LAB-Bench asks that its questions not be posted where they can be crawled, so the public logs keep only
what the analysis needs: the parsed answer, the self-reported confidence, token usage, and run metadata. The
model's text is replaced by "<answer>X</answer>\nCONFIDENCE: c", which scoring.parse_answer and
scoring.parse_confidence read back to the same values. Tool search queries are replaced by the leakage flag that
tools_arm.py computes from them.

  python src/export_public_logs.py --src ~/agenticls/results --dst results
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import data  # noqa: E402
import scoring as S  # noqa: E402
from tools_arm import LEAK  # noqa: E402

DROP = ("prompt", "reasoning", "tool_details")


def sanitize(rec: dict, task: dict) -> dict:
    out = {k: v for k, v in rec.items() if k not in DROP and k != "text"}
    ans = S.parse_answer(rec.get("text"), task)
    conf = S.parse_confidence(rec.get("text"))
    parts = [f"<answer>{ans}</answer>"] if ans is not None else []
    if conf:
        c = repr(conf)
        parts.append(f"CONFIDENCE: {c if 'e' not in c else f'{conf:.20f}'}")
    out["text"] = "\n".join(parts)
    if "tool_details" in rec:
        out["tool_leak"] = bool(LEAK.search(json.dumps(rec["tool_details"])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--dst", type=Path, required=True)
    args = ap.parse_args()
    tasks = {t["qid"]: t for t in data.load()}
    for p in sorted(args.src.glob("*/*/calls*.jsonl")):
        if p.parts[-3].startswith("_"):
            continue
        dst = args.dst / p.relative_to(args.src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        n = 0
        with p.open() as fin, dst.open("w") as fout:
            for line in fin:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                fout.write(json.dumps(sanitize(rec, tasks[rec["qid"]])) + "\n")
                n += 1
        print(f"{dst}: {n} calls")


if __name__ == "__main__":
    main()
