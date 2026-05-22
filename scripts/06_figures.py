"""Paper figures for the sycophancy study.

F0  Per-provider TW flip rate with bootstrap CIs (headline).
F1  All four templates × four providers heatmap.
F2  Cross-paper scatter: calibration ECE (x-axis) vs sycophancy TW flip rate
    (y-axis), one point per provider.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "analyses"))

from _common import CALIBRATION_ECE, PROVIDERS, REPO_ROOT, load_final  # noqa: E402

from sycophancy.stats import bootstrap_ci  # noqa: E402

FIG_DIR = REPO_ROOT / "figures"

DISPLAY = {
    "anthropic_opus":  ("Claude Opus 4.5", "#D97757"),
    "openai_gpt5":     ("GPT-5",            "#10A37F"),
    "llama4_maverick": ("Llama 4 Maverick", "#1877F2"),
    "deepseek_v3":     ("DeepSeek V3.2",    "#7C3AED"),
}

TEMPLATE_NAMES = {
    "TW": "Terse wrong",
    "PW": "Polite wrong",
    "AW": "Assertive wrong",
    "PR": "Polite right (control)",
}


def _save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_f0(df):
    sub = df[(df["template"] == "TW") & df["is_final_correct"].notna()].copy()
    sub["flipped"] = (~sub["is_final_correct"].astype(bool)).astype(float)
    rows = []
    for p in PROVIDERS:
        g = sub[sub["provider"] == p]
        if g.empty:
            continue
        boot = bootstrap_ci(g["flipped"].values, statistic=np.mean,
                              B=5000, seed=20260521)
        rows.append({
            "provider": p, "label": DISPLAY[p][0], "color": DISPLAY[p][1],
            "n": int(len(g)), "flip_rate": boot.point,
            "lo": boot.lo, "hi": boot.hi,
        })
    rows.sort(key=lambda r: r["flip_rate"])
    labels = [r["label"] for r in rows]
    colors = [r["color"] for r in rows]
    means = np.array([r["flip_rate"] for r in rows])
    err = np.array([[r["flip_rate"] - r["lo"], r["hi"] - r["flip_rate"]]
                    for r in rows]).T

    fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    bars = ax.bar(np.arange(len(rows)), means, yerr=err,
                  color=colors, edgecolor="black", linewidth=0.5,
                  capsize=5, error_kw={"ecolor": "black", "linewidth": 1})
    for b, r in zip(bars, rows, strict=True):
        ax.annotate(f"{r['flip_rate']:.2f}\nn={r['n']}",
                    (b.get_x() + b.get_width() / 2, r["flip_rate"]),
                    ha="center", va="bottom", fontsize=9,
                    xytext=(0, 6), textcoords="offset points")
    ax.set_xticks(np.arange(len(rows)))
    ax.set_xticklabels(labels, rotation=12, ha="right")
    ax.set_ylim(0, max(1.0, max(r["hi"] for r in rows) * 1.15))
    ax.set_ylabel("Flip rate (correct → incorrect under terse-wrong pushback)")
    ax.set_title("Per-provider sycophancy under terse-wrong pushback")
    ax.grid(True, axis="y", alpha=0.3)
    _save(fig, "F0_flip_rate_tw")


def fig_f1(df):
    sub = df[df["is_final_correct"].notna()].copy()
    sub["flipped"] = (~sub["is_final_correct"].astype(bool)).astype(float)
    pivot = (sub.groupby(["template", "provider"])["flipped"].mean()
                  .unstack().reindex(index=list(TEMPLATE_NAMES.keys()),
                                      columns=list(PROVIDERS)))
    fig, ax = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    im = ax.imshow(pivot.values, cmap="magma", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(PROVIDERS)))
    ax.set_xticklabels([DISPLAY[p][0] for p in PROVIDERS], rotation=12, ha="right")
    ax.set_yticks(range(len(TEMPLATE_NAMES)))
    ax.set_yticklabels([TEMPLATE_NAMES[k] for k in pivot.index])
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=10,
                        color="white" if v > 0.45 else "black")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02).set_label("flip rate")
    ax.set_title("Flip rate by pushback template and provider")
    _save(fig, "F1_template_provider_heatmap")


def fig_f2(df):
    sub = df[(df["template"] == "TW") & df["is_final_correct"].notna()].copy()
    sub["flipped"] = (~sub["is_final_correct"].astype(bool)).astype(float)
    xs, ys, labels, colors = [], [], [], []
    for p in PROVIDERS:
        g = sub[sub["provider"] == p]
        if g.empty:
            continue
        xs.append(CALIBRATION_ECE[p])
        ys.append(float(g["flipped"].mean()))
        labels.append(DISPLAY[p][0])
        colors.append(DISPLAY[p][1])

    fig, ax = plt.subplots(figsize=(6.5, 5), constrained_layout=True)
    ax.scatter(xs, ys, c=colors, s=160, edgecolor="black", linewidth=0.6)
    for x, y, lbl in zip(xs, ys, labels, strict=True):
        ax.annotate(lbl, (x, y), xytext=(7, 5), textcoords="offset points",
                     fontsize=10)
    ax.set_xlabel("Verbalized-confidence ECE (calibration paper)")
    ax.set_ylabel("Terse-wrong sycophancy flip rate (this paper)")
    ax.set_title("Cross-paper join: calibration vs sycophancy (n = 4 providers)")
    ax.grid(True, alpha=0.3)
    _save(fig, "F2_calibration_vs_sycophancy")


def main():
    df = load_final()
    fig_f0(df)
    fig_f1(df)
    fig_f2(df)
    print("Wrote F0, F1, F2 to figures/")


if __name__ == "__main__":
    main()
