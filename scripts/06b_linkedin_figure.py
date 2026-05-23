"""LinkedIn-ready single-shot chart.

One bar per provider, sorted by TW flip rate, colored by severity zone.
Annotations call out the polite-right control floor and the headline number.
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

from _common import EXTENDED_PROVIDERS, REPO_ROOT, load_final  # noqa: E402

from sycophancy.stats import bootstrap_ci  # noqa: E402

FIG_DIR = REPO_ROOT / "figures"

DISPLAY = {
    "anthropic_opus":    "Claude Opus 4.5",
    "claude_sonnet_4_6": "Claude Sonnet 4.6",
    "openai_gpt5":       "GPT-5",
    "openai_gpt4o":      "GPT-4o",
    "deepseek_v3":       "DeepSeek V3.2",
    "llama4_maverick":   "Llama 4 Maverick",
    "mistral_large_3":   "Mistral Large 3",
    "amazon_nova_pro":   "Amazon Nova Pro",
}


def zone_color(rate: float) -> str:
    if rate >= 0.90: return "#C0392B"   # deep red
    if rate >= 0.70: return "#E67E22"   # orange
    if rate >= 0.50: return "#F1C40F"   # yellow
    return "#27AE60"                    # green


def main():
    df = load_final()
    df = df[df["is_final_correct"].notna()].copy()
    df["flipped"] = (~df["is_final_correct"].astype(bool)).astype(float)

    tw = df[df["template"] == "TW"]
    pr = df[df["template"] == "PR"]

    rows = []
    for p in EXTENDED_PROVIDERS:
        g = tw[tw["provider"] == p]
        gp = pr[pr["provider"] == p]
        if g.empty: continue
        boot = bootstrap_ci(g["flipped"].values, statistic=np.mean,
                            B=5000, seed=20260521)
        pr_rate = float(gp["flipped"].mean()) if len(gp) else float("nan")
        rows.append({
            "p": p, "label": DISPLAY[p],
            "n": int(len(g)),
            "rate": boot.point, "lo": boot.lo, "hi": boot.hi,
            "pr_rate": pr_rate,
        })
    rows.sort(key=lambda r: r["rate"])
    labels = [r["label"] for r in rows]
    rates = np.array([r["rate"] for r in rows])
    colors = [zone_color(r["rate"]) for r in rows]
    err = np.array([[r["rate"] - r["lo"], r["hi"] - r["rate"]] for r in rows]).T

    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.subplots_adjust(left=0.20, right=0.97, top=0.86, bottom=0.18)
    fig.patch.set_facecolor("white")

    y = np.arange(len(rows))
    bars = ax.barh(y, rates, xerr=err, color=colors, edgecolor="black",
                    linewidth=0.6, height=0.62, capsize=4,
                    error_kw={"ecolor": "#333", "linewidth": 1.0})

    # Polite-right control dots: how often does the model flip when the user politely
    # agrees with it? Anything above this is sycophancy proper.
    for i, r in enumerate(rows):
        ax.plot([r["pr_rate"]], [i], marker="o", markersize=8,
                markerfacecolor="white", markeredgecolor="black",
                markeredgewidth=1.4, zorder=5)

    # Big number labels on each bar
    for i, r in enumerate(rows):
        ax.text(r["rate"] + 0.012, i, f"{r['rate']*100:.0f}%",
                va="center", ha="left", fontsize=14, fontweight="bold",
                color="#222")

    # Headline
    ax.set_title(
        "Tell a frontier LLM it's wrong (when it isn't).\n"
        "How often does it abandon the correct answer?",
        fontsize=17, fontweight="bold", loc="left", pad=14, color="#111",
    )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=12)
    ax.set_xlim(0, 1.08)
    ax.set_xticks(np.arange(0, 1.01, 0.2))
    ax.set_xticklabels([f"{int(x*100)}%" for x in np.arange(0, 1.01, 0.2)])
    ax.set_xlabel(
        "Flip rate — % of confidently-correct answers the model recanted "
        "after a one-line user contradiction (\"No, it's X.\")",
        fontsize=10.5, labelpad=10, color="#333",
    )

    # Annotation for the white dots — placed in the empty zone above GPT-5's bar
    ax.annotate(
        "○  = control floor: how often the model flips\n"
        "     when the user politely AGREES with it",
        xy=(0.72, 0.04), xycoords=("axes fraction", "axes fraction"),
        fontsize=9, color="#444", ha="left", va="bottom",
        bbox=dict(facecolor="white", edgecolor="#bbb", boxstyle="round,pad=0.4"),
    )

    # Footer (figure coords, lives below the axes)
    total_n = sum(r["n"] for r in rows)
    fig.text(
        0.02, 0.04,
        f"n = {total_n} confidently-correct SimpleQA answers across 8 frontier LLMs  ·  "
        "graded by Claude Haiku 4.5 (κ = 0.98 vs. Claude Sonnet 4.6)  ·  "
        "pre-registered May 2026  ·  N. Janke",
        fontsize=8.5, color="#666",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888")
    ax.spines["bottom"].set_color("#888")
    ax.tick_params(colors="#444")
    ax.grid(True, axis="x", alpha=0.25, linestyle=":")
    ax.invert_yaxis()

    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"LI_flip_rate.{ext}", dpi=220, bbox_inches="tight",
                    facecolor="white")
    plt.close(fig)
    print(f"Wrote {FIG_DIR}/LI_flip_rate.png and .pdf")


if __name__ == "__main__":
    main()
