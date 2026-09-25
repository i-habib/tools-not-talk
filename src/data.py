"""Build the frozen task pool and the pilot / main / flash-lite splits.

Selection rules (fixed before any model output is seen):
  * LAB-Bench (v1, public HF release): ProtocolQA, SeqQA, DbQA, LitQA2 -- multiple choice.
    Options = ideal + distractors, shuffled with a per-question seed. No "insufficient info" option.
  * LABBench2 SeqQA2: only items with a unique ground-truth answer (ground_truth == True), scored by
    the official LABBench2 validators; input files injected into the prompt ("inject" mode, as in the
    official harness). `restriction_counts` is excluded because its input is a 1.5 MB genome;
    items whose gold answer fails the official validator (unanswerable, ideal == "undefined") are dropped.
  * Any item whose rendered prompt exceeds MAX_PROMPT_CHARS is excluded (token budget).
  * Per category: shuffle with SEED; first N_PILOT -> pilot, next N_MAIN -> main, rest -> reserve.
    Flash-Lite subset = first N_FLASH main items per category.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FILES = ROOT / "data" / "labbench2_files"
OUT = ROOT / "data" / "tasks.jsonl"

SEED = 20260925
MAX_PROMPT_CHARS = 6000
N_PILOT, N_MAIN, N_FLASH = 2, 30, 15
LB1 = ["ProtocolQA", "SeqQA", "DbQA", "LitQA2"]
CATEGORIES = LB1 + ["SeqQA2"]
TEXT_EXT = {".gbff", ".gbk", ".gb", ".fasta", ".fa", ".fna", ".ffn", ".faa", ".txt", ".json", ".xml", ".csv"}
SEQQA2_EXCLUDED_TYPES = {"restriction_counts"}
LETTERS = "ABCDEFGHIJ"


def _rng(*parts) -> random.Random:
    h = hashlib.sha256("|".join(map(str, (SEED, *parts))).encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def lb1_items(cat: str) -> list[dict]:
    df = pd.read_parquet(RAW / "labbench" / f"{cat}.parquet")
    items = []
    for r in df.itertuples():
        opts = [r.ideal, *list(r.distractors)]
        _rng("options", r.id).shuffle(opts)
        body = ""
        if cat == "ProtocolQA":
            body = f"Protocol:\n{r.protocol.strip()}\n\n"
        body += f"Question: {r.question.strip()}\n\nOptions:\n"
        body += "\n".join(f"{LETTERS[i]}) {o}" for i, o in enumerate(opts))
        items.append({
            "qid": r.id, "category": cat, "subtask": r.subtask, "kind": "mc",
            "question": body,
            "answer_instruction": "Inside <answer></answer> put only the single letter of the option you choose.",
            "correct": LETTERS[opts.index(r.ideal)], "n_options": len(opts),
        })
    return items


def seqqa2_items() -> list[dict]:
    df = pd.read_parquet(RAW / "labbench2" / "seqqa2.parquet")
    df = df[df.ground_truth & ~df.type.isin(SEQQA2_EXCLUDED_TYPES)]
    items = []
    for r in df.itertuples():
        fdir = FILES / r.files.strip("/")
        blobs = [f"## {f.name}\n\n{f.read_text()}" for f in sorted(fdir.iterdir())
                 if f.is_file() and f.suffix.lower() in TEXT_EXT]
        body = f"Question: {r.question.strip()}"
        if blobs:
            body += "\n\nFiles:\n\n" + "\n\n".join(blobs)
        items.append({
            "qid": r.id, "category": "SeqQA2", "subtask": r.type, "kind": "seqqa2",
            "question": body, "answer_instruction": r.prompt_suffix.strip(),
            "correct": r.ideal, "answer_regex": r.answer_regex,
            "validator_params": r.validator_params, "files_dir": str(fdir.relative_to(ROOT)),
        })
    # Drop items whose own gold answer fails the official validator (e.g. ideal == "undefined").
    from scoring import seqqa2_validate
    return [it for it in items if seqqa2_validate(it["correct"], it)]


def build() -> list[dict]:
    out = []
    for cat in CATEGORIES:
        items = seqqa2_items() if cat == "SeqQA2" else lb1_items(cat)
        items = [it for it in items if len(it["question"]) + len(it["answer_instruction"]) <= MAX_PROMPT_CHARS]
        items.sort(key=lambda it: it["qid"])
        _rng("split", cat).shuffle(items)
        for i, it in enumerate(items):
            it["rank"] = i
            if i < N_PILOT:
                it["split"] = "pilot"
            elif i < N_PILOT + N_MAIN:
                it["split"] = "main"
                it["flash_subset"] = (i - N_PILOT) < N_FLASH
            else:
                it["split"] = "reserve"
            it.setdefault("flash_subset", False)
        out += items
    return out


def load(split: str | None = None, flash_only: bool = False) -> list[dict]:
    """Tasks in run order: round-robin over categories, so any prefix is category-balanced."""
    tasks = [json.loads(l) for l in OUT.open()]
    if split:
        tasks = [t for t in tasks if t["split"] == split]
    if flash_only:
        tasks = [t for t in tasks if t["flash_subset"]]
    return sorted(tasks, key=lambda t: (t["rank"], CATEGORIES.index(t["category"])))


if __name__ == "__main__":
    tasks = build()
    with OUT.open("w") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")
    df = pd.DataFrame(tasks)
    df[["qid", "category", "subtask", "split", "rank", "flash_subset"]].to_csv(ROOT / "data" / "task_ids.csv", index=False)
    print(df.groupby(["category", "split"]).size().unstack(fill_value=0))
    print("flash subset:", df.flash_subset.sum())
