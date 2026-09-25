"""Answer parsing, answer equivalence (for voting), and deterministic scoring. No LLM judge anywhere."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from labbench2.seqqa2.registry import VALIDATORS

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / "data" / "labbench2_files" / "validation"

ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.S | re.I)
CONF_RE = re.compile(r"CONFIDENCE\s*[:=]\s*\**\s*([01](?:\.\d+)?|\.\d+)", re.I)
NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def parse_answer(text: str | None, task: dict) -> str | None:
    """Last <answer>...</answer> in the visible output, normalized; None if absent/invalid."""
    if not text:
        return None
    found = ANSWER_RE.findall(text)
    if not found:
        return None
    raw = found[-1].strip()
    if task["kind"] == "mc":
        m = re.fullmatch(r"\(?\s*([A-J])\s*\)?\.?(?:\s.*)?", raw, re.S | re.I)
        if not m:
            return None
        letter = m.group(1).upper()
        return letter if ord(letter) - 65 < task["n_options"] else None
    return raw or None


def parse_confidence(text: str | None) -> float:
    m = CONF_RE.search(text or "")
    return min(max(float(m.group(1)), 0.0), 1.0) if m else 0.0


def canonical(ans: str | None, task: dict):
    """Key used to decide whether two answers are 'the same' for voting / disagreement."""
    if ans is None:
        return None
    if task["kind"] == "mc":
        return ans
    s = ans.strip().rstrip(".")
    if NUM_RE.match(s):
        return ("num", float(s))
    parts = [p.strip().upper() for p in s.split(",") if p.strip()]
    if len(parts) > 1 and all(NUM_RE.match(p) for p in parts):
        return ("nums", tuple(sorted(float(p) for p in parts)))
    return ("str", tuple(sorted(parts)) if len(parts) > 1 else s.upper())


def same(a, b) -> bool:
    if a is None or b is None:
        return False
    if isinstance(a, tuple) and a[0] == "num" and isinstance(b, tuple) and b[0] == "num":
        x, y = a[1], b[1]
        return abs(x - y) <= max(1e-9, 0.01 * max(abs(x), abs(y)))  # within 1% = same vote
    return a == b


def is_correct(ans: str | None, task: dict) -> bool:
    if ans is None:
        return False
    if task["kind"] == "mc":
        return ans == task["correct"]
    return seqqa2_validate(ans, task)


def seqqa2_validate(ans: str, task: dict) -> bool:
    """Mirrors vendor/labbench2/evals/evaluators.py (seqqa2 branch) exactly."""
    m = re.search(f"<answer>{task['answer_regex']}</answer>", f"<answer>{ans}</answer>", re.I)
    if not m:
        return False
    extracted = m.groupdict()
    validator = VALIDATORS[task["subtask"]]
    if "answer" in extracted and validator.answer_param != "answer":
        extracted[validator.answer_param] = extracted.pop("answer")
    vp = task["validator_params"]
    try:
        params = json.loads(vp) if vp else {}
    except json.JSONDecodeError:
        params = ast.literal_eval(vp)
    kwargs = {**params, **extracted}
    qdir = ROOT / task["files_dir"]
    for k, v in list(kwargs.items()):
        if k.endswith("_path") and isinstance(v, str):
            p = qdir / v if (qdir / v).exists() else VALIDATION_DIR / v
            if not p.exists():
                raise FileNotFoundError(p)
            kwargs[k] = p
    try:
        return validator.func(**kwargs) == 1.0
    except Exception:
        return False
