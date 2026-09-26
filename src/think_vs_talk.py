"""'Think longer, not together': one high-reasoning call vs 3-call orchestration at low reasoning.

Same first-30 main questions for every arm. Tokens = generated tokens (output incl. reasoning), since Codex input
counts include harness overhead.

  python src/think_vs_talk.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
import analyze as A  # noqa: E402
import data  # noqa: E402
import scoring as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# family -> (low-effort run with all strategies, high-effort run, high run has all strategies?)
FAMILIES = {
    "Flash-Lite": ("flash-lite", "flash-lite-high"),
    "GPT-6 Luna": ("gpt-6-luna", "gpt-6-luna-high"),
    "GPT-6 Sol": (None, "gpt-6-sol-high"),
    "GPT-5.6 Terra": (None, "gpt-5.6-terra-high"),
    "GPT-OSS-120B": ("gpt-oss-120b", None),
    "Gemma 4 31B": ("gemma-4-31b", None),
}
Q30 = [t["qid"] for t in data.load("main")[:30]]
TASKS = {t["qid"]: t for t in data.load("main")}


def arm(model: str | None, strategy: str):
    """Per-question (correct, generated_tokens) for the 30 questions, or None if incomplete."""
    if not model:
        return None
    calls = A.load_calls(model, "main")
    out = {}
    for q in Q30:
        recs = [calls.get((q, strategy, i)) for i in range(A.CALLS[strategy])]
        if any(r is None for r in recs):
            return None
        t = TASKS[q]
        if strategy == "indep3":
            ans = [S.parse_answer(r["text"], t) for r in recs]
            final = A.vote(ans, [S.parse_confidence(r["text"]) for r in recs], t)
        else:
            final = S.parse_answer(recs[-1]["text"], t)
        out[q] = (S.is_correct(final, t), sum(r["usage"]["output_tokens"] for r in recs))
    return out


def summarize():
    res = {}
    for fam, (low, high) in FAMILIES.items():
        r = {}
        for s in A.STRATEGIES:
            a = arm(low, s)
            if a:
                r[f"{s}@low"] = a
            b = arm(high, s)
            if b:
                r[f"{s}@high"] = b
        if r:
            res[fam] = r
    return res


def paired(a: dict, b: dict):
    x = np.array([a[q][0] for q in Q30], float) - np.array([b[q][0] for q in Q30], float)
    idx = np.random.default_rng(A.BOOT_SEED).integers(0, len(x), (A.N_BOOT, len(x)))
    m = x[idx].mean(1)
    ca, cb = np.array([a[q][0] for q in Q30]), np.array([b[q][0] for q in Q30])
    return float(x.mean()), [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], A.mcnemar(ca, cb)["p_exact"]


def main():
    res = summarize()
    lines = ["# Think longer, not together (first 30 main questions)", ""]
    table = {}
    for fam, arms in res.items():
        lines.append(f"## {fam}")
        lines.append("| arm | acc | generated tok/q |")
        lines.append("|---|---|---|")
        table[fam] = {}
        for k, v in arms.items():
            acc = np.mean([v[q][0] for q in Q30])
            tok = np.mean([v[q][1] for q in Q30])
            table[fam][k] = {"acc": float(acc), "gen_tokens": float(tok)}
            lines.append(f"| {k} | {acc:.3f} | {tok:.0f} |")
        if "direct@high" in arms:
            for other in ["indep3@low", "critique3@low", "multi3@low"]:
                if other in arms:
                    d, ci, p = paired(arms["direct@high"], arms[other])
                    table[fam][f"direct@high-{other}"] = {"delta": d, "ci95": ci, "p": p}
                    lines.append(f"- Direct@high − {other}: {d:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}], McNemar p={p:.3f}")
        for s in ["indep3", "critique3", "multi3"]:
            if f"{s}@high" in arms and "direct@high" in arms:
                d, ci, p = paired(arms[f"{s}@high"], arms["direct@high"])
                table[fam][f"{s}@high-direct@high"] = {"delta": d, "ci95": ci, "p": p}
                lines.append(f"- {s}@high − Direct@high: {d:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}], p={p:.3f}")
        lines.append("")
    A.OUT.mkdir(parents=True, exist_ok=True)
    (A.OUT / "think_vs_talk.json").write_text(json.dumps(table, indent=1))
    (A.OUT / "think_vs_talk.md").write_text("\n".join(lines))
    print("\n".join(lines))
    figure(table)


def figure(table):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fams = [f for f in table if any(k.endswith("@high") for k in table[f]) or len(table[f]) > 1]
    colors = {"direct": "#2a6fdb", "indep3": "#7f8c8d", "critique3": "#e3a21a", "multi3": "#c0392b"}
    fig, axes = plt.subplots(1, len(fams), figsize=(2.3 * len(fams), 2.6), sharey=True, squeeze=False)
    for ax, fam in zip(axes[0], fams):
        for k, v in table[fam].items():
            if "@" not in k or "-" in k:
                continue
            s, eff = k.split("@")
            ax.scatter(max(v["gen_tokens"], 1), v["acc"], color=colors[s], marker="o" if eff == "low" else "*",
                       s=40 if eff == "low" else 140, edgecolor="k" if eff == "high" else "none", zorder=3)
        ax.set_xscale("log")
        ax.set_title(fam, fontsize=8)
        ax.set_xlabel("generated tokens / q", fontsize=7)
        ax.tick_params(labelsize=7)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0][0].set_ylabel("accuracy (30 q)", fontsize=8)
    handles = [plt.Line2D([], [], color=c, marker="o", ls="", label=s) for s, c in colors.items()]
    handles += [plt.Line2D([], [], color="gray", marker="o", ls="", label="low reasoning"),
                plt.Line2D([], [], color="gray", marker="*", ms=10, ls="", mec="k", label="high reasoning")]
    fig.legend(handles=handles, fontsize=6, ncol=6, loc="lower center", frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    A.FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(A.FIG / "fig_think_vs_talk.png", dpi=200)
    fig.savefig(A.FIG / "fig_think_vs_talk.pdf")


if __name__ == "__main__" and len(sys.argv) == 1:
    main()


def variance_decomposition(M: np.ndarray) -> dict:
    """Two-way (arm x item) decomposition of the 0/1 correctness matrix, no interaction term.
    Bootstrap over items for CIs of the item and arm shares."""
    def shares(X):
        g = X.mean()
        ss_tot = ((X - g) ** 2).sum()
        ss_item = X.shape[0] * ((X.mean(0) - g) ** 2).sum()
        ss_arm = X.shape[1] * ((X.mean(1) - g) ** 2).sum()
        return ss_item / ss_tot, ss_arm / ss_tot
    item, arm = shares(M)
    rng = np.random.default_rng(A.BOOT_SEED)
    bs = np.array([shares(M[:, rng.integers(0, M.shape[1], M.shape[1])]) for _ in range(2000)])
    return {"item_share": float(item), "arm_share": float(arm),
            "item_ci95": np.percentile(bs[:, 0], [2.5, 97.5]).tolist(),
            "arm_ci95": np.percentile(bs[:, 1], [2.5, 97.5]).tolist(),
            "n_arms": int(M.shape[0]), "n_items": int(M.shape[1])}


def ceiling_figure(labels: list[str], M: np.ndarray, qcats: list[str], path_stem: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    order_q = np.argsort(-M.mean(0), kind="stable")
    order_a = np.argsort(-M.mean(1), kind="stable")
    X = M[order_a][:, order_q]
    fig, ax = plt.subplots(figsize=(6.8, 0.16 * len(labels) + 0.9))
    ax.imshow(X, aspect="auto", cmap="Greys", vmin=0, vmax=1.4, interpolation="nearest")
    ax.set_yticks(range(len(labels)), [labels[i] for i in order_a], fontsize=5)
    ax.set_xticks([])
    ax.set_xlabel("questions (sorted by fraction of systems correct)", fontsize=7)
    fig.tight_layout()
    fig.savefig(A.FIG / f"{path_stem}.png", dpi=200)
    fig.savefig(A.FIG / f"{path_stem}.pdf")


def ceiling_analysis():
    out = {}
    # (a) all arms on the shared first-30 questions
    res = summarize()
    arms = [(f"{f} · {k}", v) for f, a in res.items() for k, v in a.items()]
    M30 = np.array([[v[q][0] for q in Q30] for _, v in arms], float)
    out["first30_all_arms"] = variance_decomposition(M30)
    ceiling_figure([l for l, _ in arms], M30, [TASKS[q]["category"] for q in Q30], "fig_ceiling_first30")
    # (b) main models x 4 strategies on all questions complete for every main model
    rows = {m: {r["qid"]: r for r in A.per_question(m, "main")} for m in ["gpt-oss-120b", "gemma-4-31b"]}
    common = sorted(set.intersection(*(set(v) for v in rows.values())))
    if len(common) >= 20:
        labels, mat = [], []
        for m, rr in rows.items():
            for s in A.STRATEGIES:
                labels.append(f"{m} · {s}")
                mat.append([rr[q][f"{s}_correct"] for q in common])
        M = np.array(mat, float)
        out["main_models"] = {**variance_decomposition(M), "models": list(rows)}
        ceiling_figure(labels, M, [TASKS[q]["category"] for q in common], "fig_ceiling_main")
    (A.OUT / "ceiling.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "ceiling":
    ceiling_analysis()
