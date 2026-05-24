"""V1 factorial figures.

F4  Per-provider grounding ablation: paired BV-TW vs TV-TW flip-rate bars
    with bootstrap CIs (the headline result for H6).
F5  Full 8-cell × 4-provider heatmap of TW flip rate (and PR controls below).
F6  Within-subject scatter: per-question flip outcome under BV-TW vs TV-TW,
    showing the "ground truth shifts the model" pattern.
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

from _common import (  # noqa: E402
    REPO_ROOT, V1_PROVIDERS_C, V1_PROVIDERS_G, load_final_v1, pair_flip,
)

from sycophancy.stats import bootstrap_ci  # noqa: E402

FIG_DIR = REPO_ROOT / "figures"

DISPLAY_V1 = {
    "anthropic_sonnet_46": ("Claude Sonnet 4.6", "#D97757"),
    "openai_gpt5":         ("GPT-5",              "#10A37F"),
    "google_gemini":       ("Gemini 2.5 Pro",     "#4285F4"),
    "deepseek_v3_2":       ("DeepSeek V3.2",      "#7C3AED"),
}

CELL_NAMES = {
    "BV-TW": "Bare + verbalized + terse-wrong",
    "BV-PR": "Bare + verbalized + polite-right (control)",
    "BF-TW": "Bare + free-form + terse-wrong",
    "BF-PR": "Bare + free-form + polite-right",
    "TV-TW": "Tools + verbalized + terse-wrong",
    "TV-PR": "Tools + verbalized + polite-right",
    "TF-TW": "Tools + free-form + terse-wrong",
    "TF-PR": "Tools + free-form + polite-right",
}


def _save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _flip_rate_ci(df, provider, cell):
    """Flip rate computed only over questions with BOTH turn-1 correct AND
    turn-2 graded (CORRECT or INCORRECT, not ungradable). Treats ungradable
    turn-2 responses as missing data, not as flips.
    """
    g = df[(df["provider"] == provider) & (df["cell"] == cell) &
            df["turn1_is_correct"].astype("boolean") &
            df["turn2_is_correct"].notna()]
    if len(g) < 5:
        return float("nan"), float("nan"), float("nan"), int(len(g))
    flips = (~g["turn2_is_correct"].astype(bool)).astype(float).values
    ci = bootstrap_ci(flips, statistic=np.mean, B=10_000, seed=20260523)
    return ci.point, ci.lo, ci.hi, int(len(g))


def fig_f4(df):
    """Paired BV-TW vs TV-TW flip rate per G-arm provider, matched within-subject.

    This is the figure that backs H6: flip rates are computed on the
    intersection of (turn-1 correct in BV-TW) AND (turn-1 correct in TV-TW),
    which is what the H6 paired bootstrap uses.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    providers = list(V1_PROVIDERS_G)
    x = np.arange(len(providers))
    bar_w = 0.36

    bv_vals, bv_lo, bv_hi, tv_vals, tv_lo, tv_hi, ns = [], [], [], [], [], [], []
    for p in providers:
        pairs = pair_flip(df, p, "BV-TW", "TV-TW")
        if len(pairs) < 3:
            bv_vals.append(float("nan")); bv_lo.append(0); bv_hi.append(0)
            tv_vals.append(float("nan")); tv_lo.append(0); tv_hi.append(0)
            ns.append(int(len(pairs)))
            continue
        bv = pairs["flip_a"].astype(float).values
        tv = pairs["flip_b"].astype(float).values
        bv_ci = bootstrap_ci(bv, statistic=np.mean, B=10_000, seed=20260523)
        tv_ci = bootstrap_ci(tv, statistic=np.mean, B=10_000, seed=20260523)
        bv_vals.append(bv_ci.point); bv_lo.append(bv_ci.point - bv_ci.lo); bv_hi.append(bv_ci.hi - bv_ci.point)
        tv_vals.append(tv_ci.point); tv_lo.append(tv_ci.point - tv_ci.lo); tv_hi.append(tv_ci.hi - tv_ci.point)
        ns.append(int(len(pairs)))
    ns_bv = ns_tv = ns  # n_pairs is the same for both bars (within-subject matched set)

    ax.bar(x - bar_w/2, bv_vals, bar_w, yerr=[bv_lo, bv_hi],
            color="#CD5C5C", edgecolor="black", linewidth=0.6,
            label="Bare API + verbalized confidence (no tools)", capsize=4)
    ax.bar(x + bar_w/2, tv_vals, bar_w, yerr=[tv_lo, tv_hi],
            color="#5BA17F", edgecolor="black", linewidth=0.6,
            label="Same provider + native web search enabled", capsize=4)

    ax.set_ylim(0, 1.05)
    ax.set_xticks(x)
    ax.set_xticklabels([DISPLAY_V1[p][0] for p in providers])
    ax.set_ylabel("Flip rate from correct answer\nunder terse-wrong pushback")
    ax.set_title("Native web search collapses sycophancy under user pushback",
                  fontsize=13, pad=12)
    ax.legend(loc="upper right", framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v*100)}%"))

    for i, (bv, tv) in enumerate(zip(bv_vals, tv_vals, strict=True)):
        if not (np.isnan(bv) or np.isnan(tv)):
            ax.text(i, max(bv, tv) + 0.10, f"Δ={bv-tv:+.2f}",
                    ha="center", fontsize=9, color="#444")
        ax.text(i - bar_w/2, -0.04, f"n={ns_bv[i]}", ha="center", fontsize=8, color="#888")
        ax.text(i + bar_w/2, -0.04, f"n={ns_tv[i]}", ha="center", fontsize=8, color="#888")

    fig.text(0.5, -0.02,
             "Each pair is the same model on the same questions, with vs. without web-search access.\n"
             "Within-subject paired bootstrap (B=10,000). H6 pre-registered at git tag prereg-v1.",
             ha="center", fontsize=8, color="#666")
    _save(fig, "F4_grounding_ablation")


def fig_f5(df):
    """8-cell × 4-provider heatmap of flip rate. NaN where cell not run."""
    cells = ["BV-TW", "BV-PR", "BF-TW", "BF-PR", "TV-TW", "TV-PR", "TF-TW", "TF-PR"]
    providers = list(V1_PROVIDERS_C)
    M = np.full((len(providers), len(cells)), np.nan)
    N = np.zeros_like(M, dtype=int)
    for i, p in enumerate(providers):
        for j, c in enumerate(cells):
            v, _, _, n = _flip_rate_ci(df, p, c)
            M[i, j] = v
            N[i, j] = n

    fig, ax = plt.subplots(figsize=(9, 4))
    cmap = plt.get_cmap("RdYlGn_r")
    im = ax.imshow(M, vmin=0, vmax=1, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels(cells, rotation=0, fontsize=9)
    ax.set_yticks(range(len(providers)))
    ax.set_yticklabels([DISPLAY_V1[p][0] for p in providers])
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isnan(M[i, j]):
                ax.text(j, i, "—", ha="center", va="center", fontsize=9, color="#666")
            else:
                ax.text(j, i, f"{M[i,j]:.2f}\nn={N[i,j]}",
                        ha="center", va="center", fontsize=7.5,
                        color="white" if M[i, j] > 0.55 else "black")
    cb = plt.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("Flip rate", fontsize=9)
    ax.set_title("Flip rate by (grounding × format × pushback) × provider", fontsize=11)
    fig.text(0.5, -0.04, "B = bare API; T = tools-on. V = verbalized confidence; F = free-form. "
             "TW = terse-wrong; PR = polite-right (within-subject control).",
             ha="center", fontsize=8, color="#666")
    _save(fig, "F5_cells_heatmap")


def fig_f6(df):
    """Within-subject question-level scatter for Claude Sonnet:
    BV-TW outcome (x) vs TV-TW outcome (y) per question."""
    providers = list(V1_PROVIDERS_G)
    fig, axes = plt.subplots(1, len(providers), figsize=(4.2 * len(providers), 4),
                              sharey=True)
    for ax, p in zip(axes, providers, strict=True):
        pairs = pair_flip(df, p, "BV-TW", "TV-TW")
        if pairs.empty:
            ax.set_title(f"{DISPLAY_V1[p][0]}\n(no pairs)")
            continue
        # 4 cells of the 2×2 contingency
        held_both = ((~pairs["flip_a"].astype(bool)) & (~pairs["flip_b"].astype(bool))).sum()
        flip_bare = (pairs["flip_a"].astype(bool) & (~pairs["flip_b"].astype(bool))).sum()
        flip_tools = ((~pairs["flip_a"].astype(bool)) & pairs["flip_b"].astype(bool)).sum()
        flip_both = (pairs["flip_a"].astype(bool) & pairs["flip_b"].astype(bool)).sum()
        n = len(pairs)

        sizes = np.array([[held_both, flip_tools], [flip_bare, flip_both]]) / max(n, 1)
        ax.imshow(sizes, vmin=0, vmax=1, cmap="Reds", aspect="equal")
        for (i, j), val in np.ndenumerate(sizes):
            count = int(sizes[i, j] * n + 0.5)
            ax.text(j, i, f"{count}\n({val*100:.0f}%)",
                    ha="center", va="center", fontsize=10,
                    color="white" if val > 0.5 else "black")
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(["held under\ntools", "flipped under\ntools"], fontsize=9)
        ax.set_yticklabels(["held bare", "flipped bare"], fontsize=9)
        ax.set_title(f"{DISPLAY_V1[p][0]}  (n={n})", fontsize=10)
    fig.suptitle("Per-question outcomes: bare API vs same provider with web search",
                  y=1.02, fontsize=12)
    _save(fig, "F6_within_subject_outcomes")


def main() -> int:
    df = load_final_v1()
    fig_f4(df)
    fig_f5(df)
    fig_f6(df)
    print(f"Wrote v1 figures to {FIG_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
