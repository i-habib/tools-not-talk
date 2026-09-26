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
    "GPT-OSS-120B": ("gpt-oss-120b", "gpt-oss-120b-ollama-high"),
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
        if fam == "GPT-6 Luna":
            t = arm("gpt-6-luna-tools", "direct")
            if t:
                r["direct@tools"] = t
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
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    order = ["GPT-6 Sol", "GPT-5.6 Terra", "GPT-6 Luna", "Flash-Lite", "Gemma 4 31B", "GPT-OSS-120B"]
    fams = [f for f in order if f in table and any("@" in k and "-" not in k for k in table[f])]
    colors = {"direct": "#2a6fdb", "indep3": "#1b9e77", "critique3": "#e3a21a", "multi3": "#c0392b"}
    names = {"direct": "Direct (1 call)", "indep3": "Vote (3)", "critique3": "Critique (3)", "multi3": "Debate (3)"}
    fig, axes = plt.subplots(1, len(fams), figsize=(1.35 * len(fams) + 0.4, 2.3), sharey=True, sharex=True,
                             squeeze=False)
    for ax, fam in zip(axes[0], fams):
        for k, v in table[fam].items():
            if "@" not in k or "-" in k:
                continue
            s, eff = k.split("@")
            if eff == "tools":
                ax.scatter(max(v["gen_tokens"], 1), 100 * v["acc"], color="#111111", marker="D", s=42, zorder=4)
                ax.annotate("+tools", (v["gen_tokens"], 100 * v["acc"]), textcoords="offset points", xytext=(4, 3),
                            fontsize=6)
                continue
            ax.scatter(max(v["gen_tokens"], 1), 100 * v["acc"], color=colors[s], zorder=3,
                       marker="o" if eff == "low" else "*", s=28 if eff == "low" else 110,
                       edgecolor="k" if eff == "high" else "none", linewidth=0.6)
        ax.set_xscale("log")
        ax.set_xlim(80, 40000)
        ax.xaxis.set_major_locator(FixedLocator([100, 1000, 10000]))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: {100: "100", 1000: "1k", 10000: "10k"}.get(int(x), "")))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_title(fam, fontsize=7.5)
        ax.tick_params(labelsize=6.5)
        ax.grid(axis="y", lw=0.3, alpha=0.5)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0][0].set_ylabel("accuracy (%)", fontsize=7.5)
    fig.supxlabel("generated tokens per question (log)", fontsize=7.5, y=0.13)
    handles = [plt.Line2D([], [], color=c, marker="s", ls="", ms=5, label=names[s]) for s, c in colors.items()]
    handles += [plt.Line2D([], [], color="k", marker="o", ls="", ms=4, mfc="w", label="low reasoning"),
                plt.Line2D([], [], color="k", marker="*", ms=8, ls="", mfc="w", label="high reasoning"),
                plt.Line2D([], [], color="#111111", marker="D", ms=5, ls="", label="1 call + tools")]
    fig.legend(handles=handles, fontsize=6.5, ncol=7, loc="lower center", frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.12, 1, 1), w_pad=0.4)
    A.FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(A.FIG / "fig_think_vs_talk.png", dpi=220)
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
    """Rows grouped by model (colour), columns sorted by fraction of systems correct; category strip on top."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb
    fam_col = {"gpt-oss-120b": "#6a3d9a", "gemma-4-31b": "#1f78b4", "flash-lite": "#33a02c", "GPT-6 Sol": "#e31a1c",
               "GPT-5.6 Terra": "#ff7f00", "GPT-6 Luna": "#b15928", "Flash-Lite": "#33a02c", "Gemma 4 31B": "#1f78b4",
               "GPT-OSS-120B": "#6a3d9a"}
    cat_col = {"ProtocolQA": "#8dd3c7", "SeqQA": "#fdb462", "DbQA": "#bebada", "LitQA2": "#fb8072", "SeqQA2": "#80b1d3"}
    nice = {"direct": "Direct", "indep3": "Vote", "critique3": "Critique", "multi3": "Debate"}
    fam = [l.split(" · ")[0] for l in labels]
    order_q = np.argsort(-M.mean(0), kind="stable")
    order_a = sorted(range(len(labels)), key=lambda i: (-M[[j for j in range(len(labels)) if fam[j] == fam[i]]].mean(),
                                                       fam[i], -M[i].mean()))
    X = M[order_a][:, order_q]
    img = np.ones((X.shape[0] + 2, X.shape[1], 3))
    for c, q in enumerate(order_q):
        img[0, c] = to_rgb(cat_col.get(qcats[q], "#cccccc"))
    for r, i in enumerate(order_a):
        col = np.array(to_rgb(fam_col.get(fam[i], "#444444")))
        for c in range(X.shape[1]):
            img[r + 2, c] = col if X[r, c] else np.array([0.96, 0.96, 0.96])
    fig, ax = plt.subplots(figsize=(6.8, 0.13 * len(labels) + 1.0))
    ax.imshow(img, aspect="auto", interpolation="nearest")
    ylab = ["category", ""] + [f"{fam[i]} · {nice.get(labels[i].split(' · ')[1].split('@')[0], labels[i].split(' · ')[1])}"
                               + (" (high)" if labels[i].endswith("@high") else "") for i in order_a]
    ax.set_yticks(range(len(ylab)), ylab, fontsize=5)
    ax.set_xticks([])
    ax.set_xlabel("questions, sorted by fraction of systems correct  (coloured = correct)", fontsize=6.5)
    for sp in ax.spines.values():
        sp.set_visible(False)
    handles = [plt.Line2D([], [], color=c, marker="s", ls="", ms=5, label=k) for k, c in cat_col.items()
               if k in set(qcats)]
    ax.legend(handles=handles, fontsize=5, ncol=5, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
    fig.tight_layout()
    fig.savefig(A.FIG / f"{path_stem}.png", dpi=220)
    fig.savefig(A.FIG / f"{path_stem}.pdf")



def ceiling_analysis():
    out = {}
    # (a) all arms on the shared first-30 questions
    res = summarize()
    arms = [(f"{f} · {k}", v) for f, a in res.items() for k, v in a.items() if not k.endswith("@tools")]
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
                labels.append(f"{ {'gpt-oss-120b': 'GPT-OSS-120B', 'gemma-4-31b': 'Gemma 4 31B'}.get(m, m)} · {s}")
                mat.append([rr[q][f"{s}_correct"] for q in common])
        M = np.array(mat, float)
        import collections
        cats = [TASKS[q]["category"] for q in common]
        unsolved = collections.Counter(c for c, col in zip(cats, M.T) if col.sum() == 0)
        out["main_models"] = {**variance_decomposition(M), "models": list(rows),
                              "n_unsolved": int(sum(unsolved.values())), "unsolved_by_category": dict(unsolved),
                              "n_all_solved": int((M.min(0) == 1).sum())}
        ceiling_figure(labels, M, [TASKS[q]["category"] for q in common], "fig_ceiling_main")
    (A.OUT / "ceiling.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "ceiling":
    ceiling_analysis()
