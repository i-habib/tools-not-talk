"""Pre-registered analysis. Reads results/<model>/<split>/calls.jsonl, derives final answers, writes
results/analysis/*.json|md and results/figures/*.png.

  python src/analyze.py --split main --models gpt-oss-120b gemma-4-31b flash-lite
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
import data  # noqa: E402
import scoring as S  # noqa: E402
from strategies import CALLS, STRATEGIES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "analysis"
FIG = ROOT / "results" / "figures"
N_BOOT = 10_000
BOOT_SEED = 20260925
LABEL = {"direct": "Direct (1 call)", "indep3": "Independent×3 (vote)",
         "critique3": "Solve→Critique→Revise", "multi3": "Two scientists + adjudicator"}


def vote(answers: list[str | None], confs: list[float], task: dict) -> str | None:
    """Majority over equivalent answers; if no majority, highest self-reported confidence (earliest on tie)."""
    keys = [S.canonical(a, task) for a in answers]
    clusters: list[list[int]] = []
    for i, k in enumerate(keys):
        if k is None:
            continue
        for c in clusters:
            if S.same(keys[c[0]], k):
                c.append(i)
                break
        else:
            clusters.append([i])
    if not clusters:
        return None
    best = max(clusters, key=len)
    if len(best) >= 2:
        return answers[best[0]]
    i = max((i for c in clusters for i in c), key=lambda i: (confs[i], -i))
    return answers[i]


def unanimous(answers, task) -> bool:
    keys = [S.canonical(a, task) for a in answers]
    return all(k is not None for k in keys) and all(S.same(keys[0], k) for k in keys[1:])


def load_calls(model: str, split: str):
    calls = {}
    for p in sorted((ROOT / "results" / model / split).glob("calls*.jsonl")):
        for line in p.open():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not r.get("error"):
                calls[(r["qid"], r["strategy"], r["step"])] = r
    return calls


def per_question(model: str, split: str, flash_only: bool = False):
    tasks = {t["qid"]: t for t in data.load(split, flash_only=flash_only)}
    calls = load_calls(model, split)
    rows = []
    for qid, t in tasks.items():
        if not all((qid, s, i) in calls for s in STRATEGIES for i in range(CALLS[s])):
            continue
        c = lambda s, i: calls[(qid, s, i)]  # noqa: E731
        ans = lambda s, i: S.parse_answer(c(s, i)["text"], t)  # noqa: E731
        ind = [ans("indep3", i) for i in range(3)]
        ind_conf = [S.parse_confidence(c("indep3", i)["text"]) for i in range(3)]
        final = {"direct": ans("direct", 0), "indep3": vote(ind, ind_conf, t),
                 "critique3": ans("critique3", 2), "multi3": ans("multi3", 2)}
        row = {"qid": qid, "category": t["category"], "subtask": t["subtask"],
               "provider": "groq" if c("direct", 0)["model"].startswith("openai/") else "primary",
               "unanimous": unanimous(ind, t),
               "indep_samples_correct": [S.is_correct(a, t) for a in ind],
               "critique_initial_correct": S.is_correct(ans("critique3", 0), t),
               "multi_s1_correct": S.is_correct(ans("multi3", 0), t),
               "multi_s2_correct": S.is_correct(ans("multi3", 1), t),
               "multi_scientists_agree": S.same(S.canonical(ans("multi3", 0), t), S.canonical(ans("multi3", 1), t))}
        for s in STRATEGIES:
            recs = [c(s, i) for i in range(CALLS[s])]
            row[f"{s}_answer"] = final[s]
            row[f"{s}_correct"] = S.is_correct(final[s], t)
            row[f"{s}_tokens"] = sum(r["usage"]["total_tokens"] for r in recs)
            row[f"{s}_in"] = sum(r["usage"]["input_tokens"] for r in recs)
            row[f"{s}_out"] = sum(r["usage"]["output_tokens"] for r in recs)
            row[f"{s}_latency"] = sum(r.get("latency_s", 0) for r in recs)
            row[f"{s}_truncated"] = sum(str(r.get("finish_reason")).lower() in ("length", "max_tokens") for r in recs)
            final_steps = range(3) if s == "indep3" else [CALLS[s] - 1]
            row[f"{s}_parse_fail"] = sum(S.parse_answer(recs[i]["text"], t) is None for i in final_steps)
        rows.append(row)
    return rows


def boot_idx(n: int):
    return np.random.default_rng(BOOT_SEED).integers(0, n, size=(N_BOOT, n))


def ci(x: np.ndarray, idx) -> list[float]:
    m = x[idx].mean(axis=1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def mcnemar(a: np.ndarray, b: np.ndarray) -> dict:
    b01, b10 = int((~a & b).sum()), int((a & ~b).sum())
    p = binomtest(b01, b01 + b10, 0.5).pvalue if b01 + b10 else 1.0
    return {"a_only": b10, "b_only": b01, "p_exact": float(p)}


def rate(num_mask, den_mask):
    d = int(den_mask.sum())
    return {"rate": float(num_mask[den_mask].mean()) if d else None, "n": d, "k": int(num_mask[den_mask].sum())}


def analyze(rows: list[dict]) -> dict:
    n = len(rows)
    idx = boot_idx(n)
    cor = {s: np.array([r[f"{s}_correct"] for r in rows]) for s in STRATEGIES}
    tok = {s: np.array([r[f"{s}_tokens"] for r in rows], float) for s in STRATEGIES}
    res = {"n": n, "strategies": {}, "contrasts": {}, "by_category": {}, "disagreement": {}, "transitions": {}}
    for s in STRATEGIES:
        res["strategies"][s] = {
            "accuracy": float(cor[s].mean()), "ci95": ci(cor[s].astype(float), idx),
            "tokens_per_q": float(tok[s].mean()),
            "input_per_q": float(np.mean([r[f"{s}_in"] for r in rows])),
            "output_per_q": float(np.mean([r[f"{s}_out"] for r in rows])),
            "latency_per_q": float(np.mean([r[f"{s}_latency"] for r in rows])),
            "correct_per_Mtok": float(cor[s].sum() / tok[s].sum() * 1e6) if tok[s].sum() else None,
            "truncated_calls": int(sum(r[f"{s}_truncated"] for r in rows)),
            "parse_failures": int(sum(r[f"{s}_parse_fail"] for r in rows)),
        }
    pairs = [("multi3", "indep3"), ("critique3", "indep3"), ("indep3", "direct"), ("multi3", "direct"),
             ("critique3", "direct"), ("multi3", "critique3")]
    for a, b in pairs:
        d = cor[a].astype(float) - cor[b].astype(float)
        res["contrasts"][f"{a}-{b}"] = {"delta": float(d.mean()), "ci95": ci(d, idx), **mcnemar(cor[a], cor[b])}
    cats = sorted({r["category"] for r in rows}, key=data.CATEGORIES.index)
    for cat in cats:
        m = np.array([r["category"] == cat for r in rows])
        res["by_category"][cat] = {"n": int(m.sum()), **{s: float(cor[s][m].mean()) for s in STRATEGIES},
                                   "disagreement_rate": float(np.mean([not r["unanimous"] for r in np.array(rows)[m]]))}
    D = np.array([not r["unanimous"] for r in rows])
    res["disagreement"] = {"n": int(D.sum()), "frac": float(D.mean()),
                           **{s: rate(cor[s], D) for s in STRATEGIES},
                           "unanimous_acc": {s: rate(cor[s], ~D) for s in STRATEGIES}}
    oracle = np.array([any(r["indep_samples_correct"]) for r in rows])
    res["indep_any_correct"] = float(oracle.mean())
    res["indep_single_sample_acc"] = float(np.mean([np.mean(r["indep_samples_correct"]) for r in rows]))
    for s in ["critique3", "multi3", "direct"]:
        res["transitions"][f"{s}_vs_indep3"] = {
            "rescue": rate(cor[s], ~cor["indep3"]), "corruption": rate(~cor[s], cor["indep3"])}
    ci0 = np.array([r["critique_initial_correct"] for r in rows])
    res["transitions"]["critique_revision"] = {"rescue": rate(cor["critique3"], ~ci0),
                                               "corruption": rate(~cor["critique3"], ci0),
                                               "initial_acc": float(ci0.mean())}
    agree = np.array([r["multi_scientists_agree"] for r in rows])
    s1 = np.array([r["multi_s1_correct"] for r in rows])
    s2 = np.array([r["multi_s2_correct"] for r in rows])
    res["transitions"]["multi_adjudication"] = {
        "scientists_disagree": int((~agree).sum()), "researcher_acc": float(s1.mean()), "skeptic_acc": float(s2.mean()),
        "adjudicator_acc_when_disagree": rate(cor["multi3"], ~agree),
        "either_scientist_correct_when_disagree": rate(s1 | s2, ~agree),
        "adjudicator_overrides_agreement": int(sum((agree[i] and r["multi3_correct"] != r["multi_s1_correct"])
                                                   for i, r in enumerate(rows)))}
    return res


def markdown(model: str, res: dict) -> str:
    L = [f"## {model}  (n = {res['n']} questions)", "",
         "| Strategy | Acc | 95% CI | tokens/q | out tok/q | correct/Mtok | trunc | parse-fail |", "|---|---|---|---|---|---|---|---|"]
    for s, v in res["strategies"].items():
        L.append(f"| {LABEL[s]} | {v['accuracy']:.3f} | [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] | {v['tokens_per_q']:.0f} | "
                 f"{v['output_per_q']:.0f} | {v['correct_per_Mtok'] or 0:.0f} | {v['truncated_calls']} | {v['parse_failures']} |")
    L += ["", "| Paired contrast | Δacc | 95% CI | A-only | B-only | McNemar p |", "|---|---|---|---|---|---|"]
    for k, v in res["contrasts"].items():
        L.append(f"| {k} | {v['delta']:+.3f} | [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}] | {v['a_only']} | {v['b_only']} | {v['p_exact']:.3f} |")
    d = res["disagreement"]
    L += ["", f"**Disagreement subset** (independent samples not unanimous): {d['n']} / {res['n']} ({d['frac']:.0%})", "",
          "| Strategy | acc on disagreement | acc on unanimous |", "|---|---|---|"]
    for s in STRATEGIES:
        a, u = d[s], d["unanimous_acc"][s]
        L.append(f"| {LABEL[s]} | {a['rate'] if a['rate'] is not None else float('nan'):.3f} ({a['k']}/{a['n']}) | "
                 f"{u['rate'] if u['rate'] is not None else float('nan'):.3f} ({u['k']}/{u['n']}) |")
    L += ["", "| vs Independent×3 vote | rescue P(correct | vote wrong) | corruption P(wrong | vote right) |", "|---|---|---|"]
    for k, v in res["transitions"].items():
        if k.endswith("_vs_indep3"):
            f = lambda x: f"{x['rate']:.3f} ({x['k']}/{x['n']})" if x["rate"] is not None else "–"  # noqa: E731
            L.append(f"| {k.replace('_vs_indep3', '')} | {f(v['rescue'])} | {f(v['corruption'])} |")
    L += ["", "| Category | n | " + " | ".join(STRATEGIES) + " | disagree |", "|---|---|" + "---|" * 5]
    for c, v in res["by_category"].items():
        L.append(f"| {c} | {v['n']} | " + " | ".join(f"{v[s]:.2f}" for s in STRATEGIES) + f" | {v['disagreement_rate']:.2f} |")
    L += ["", f"Single independent sample acc: {res['indep_single_sample_acc']:.3f}; any-of-3 correct (oracle): {res['indep_any_correct']:.3f}",
          f"Critique revision: {json.dumps(res['transitions']['critique_revision'])}",
          f"Multi-agent adjudication: {json.dumps(res['transitions']['multi_adjudication'])}", ""]
    return "\n".join(L)


def figures(all_res: dict, split: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    colors = {"direct": "#8c8c8c", "indep3": "#2a6fdb", "critique3": "#e3a21a", "multi3": "#c0392b"}
    models = list(all_res)
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    w = 0.2
    for j, s in enumerate(STRATEGIES):
        xs = np.arange(len(models)) + (j - 1.5) * w
        acc = [all_res[m]["strategies"][s]["accuracy"] for m in models]
        lo = [a - all_res[m]["strategies"][s]["ci95"][0] for a, m in zip(acc, models)]
        hi = [all_res[m]["strategies"][s]["ci95"][1] - a for a, m in zip(acc, models)]
        ax.bar(xs, acc, w, yerr=[lo, hi], capsize=2, color=colors[s], label=LABEL[s])
    ax.set_xticks(range(len(models)), [f"{m}\n(n={all_res[m]['n']})" for m in models])
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7, ncol=2, loc="upper right", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / f"fig1_accuracy_{split}.png", dpi=200)
    fig.savefig(FIG / f"fig1_accuracy_{split}.pdf")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    markers = ["o", "s", "^", "D"]
    for mi, m in enumerate(models):
        for s in STRATEGIES:
            v = all_res[m]["strategies"][s]
            axes[0].scatter(v["tokens_per_q"], v["accuracy"], color=colors[s], marker=markers[mi % 4], s=40)
        pts = sorted((all_res[m]["strategies"][s]["tokens_per_q"], all_res[m]["strategies"][s]["accuracy"]) for s in STRATEGIES)
        axes[0].plot(*zip(*pts), color="#cccccc", lw=0.8, zorder=0)
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Mean tokens / question (log)")
    axes[0].set_ylabel("Accuracy")
    for mi, m in enumerate(models):
        axes[0].scatter([], [], color="k", marker=markers[mi % 4], label=m)
    axes[0].legend(fontsize=7, frameon=False)
    for j, s in enumerate(STRATEGIES):
        xs = np.arange(len(models)) + (j - 1.5) * w
        axes[1].bar(xs, [all_res[m]["disagreement"][s]["rate"] or 0 for m in models], w, color=colors[s], label=LABEL[s])
    axes[1].set_xticks(range(len(models)), [f"{m}\n(n={all_res[m]['disagreement']['n']})" for m in models], fontsize=7)
    axes[1].set_ylabel("Accuracy on disagreement subset")
    axes[1].set_ylim(0, 1)
    for a in axes:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / f"fig2_efficiency_conflict_{split}.png", dpi=200)
    fig.savefig(FIG / f"fig2_efficiency_conflict_{split}.pdf")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="main")
    ap.add_argument("--models", nargs="+", default=["gpt-oss-120b", "gemma-4-31b", "flash-lite"])
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    all_res, md = {}, [f"# Results ({args.split})", ""]
    for m in args.models:
        rows = per_question(m, args.split)
        if len(rows) < 2:
            print(f"{m}: {len(rows)} complete questions, skipping")
            continue
        res = analyze(rows)
        all_res[m] = res
        (OUT / f"{m}_{args.split}_rows.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
        md.append(markdown(m, res))
    (OUT / f"summary_{args.split}.json").write_text(json.dumps(all_res, indent=1))
    (OUT / f"summary_{args.split}.md").write_text("\n".join(md))
    if all_res:
        figures(all_res, args.split)
    print("\n".join(md))
