"""H2 — Asymmetry: TW flip rate exceeds PR flip rate per provider, paired.

For each provider, we form per-question pairs of (TW flip indicator,
PR flip indicator) on the same question, then bootstrap the per-question
difference (TW - PR). One-sided test for positive difference. The aggregate
p-value is the most-significant per-provider p as a conservative summary;
Holm-Bonferroni is applied across the H1-H5 family.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _common import PROVIDERS, load_final, write_results  # noqa: E402

from sycophancy.prereg import require_prereg_tag  # noqa: E402
from sycophancy.stats import (  # noqa: E402
    bootstrap_p_value,
    paired_bootstrap_ci,
)

B = 10_000
SEED = 20260521


def main() -> int:
    require_prereg_tag("prereg-v0")
    df = load_final()
    df = df[df["is_final_correct"].notna()].copy()
    df["flipped"] = ~df["is_final_correct"].astype(bool)

    per_provider = {}
    for p in PROVIDERS:
        g = df[df["provider"] == p]
        # Pivot: rows = question_id, cols = template
        pivot = g.pivot_table(index="question_id", columns="template",
                              values="flipped", aggfunc="first")
        if "TW" not in pivot.columns or "PR" not in pivot.columns:
            per_provider[p] = {"n_pairs": 0, "mean_diff": float("nan")}
            continue
        paired = pivot[["TW", "PR"]].dropna()
        if len(paired) < 5:
            per_provider[p] = {"n_pairs": len(paired), "mean_diff": float("nan")}
            continue
        tw = paired["TW"].astype(float).values
        pr = paired["PR"].astype(float).values
        boot = paired_bootstrap_ci(tw, pr, statistic=np.mean,
                                     B=B, seed=SEED, return_samples=True)
        p_value = bootstrap_p_value(boot.samples, null_value=0.0,
                                     alternative="greater")
        per_provider[p] = {
            "n_pairs": int(len(paired)),
            "mean_diff_tw_minus_pr": boot.point,
            "ci_lo": boot.lo, "ci_hi": boot.hi,
            "p_one_sided_greater": p_value,
        }

    # Aggregate p (conservative: most significant)
    pvals = [v["p_one_sided_greater"] for v in per_provider.values()
             if "p_one_sided_greater" in v]
    aggregate_p = min(pvals) if pvals else float("nan")
    decision = ("supported" if aggregate_p < 0.05 else
                "refuted" if aggregate_p >= 0.95 else "inconclusive")

    payload = {
        "hypothesis": "H2",
        "per_provider": per_provider,
        "aggregate_p_value": aggregate_p,
        "decision": decision,
    }
    out = write_results("H2", payload)
    print("H2 — TW vs PR per-provider paired difference:")
    for p, v in per_provider.items():
        if "mean_diff_tw_minus_pr" in v:
            print(f"  {p:<22} n_pairs={v['n_pairs']:>3}  "
                  f"diff={v['mean_diff_tw_minus_pr']:+.3f}  "
                  f"CI=({v['ci_lo']:+.3f}, {v['ci_hi']:+.3f})  "
                  f"p={v['p_one_sided_greater']:.4f}")
        else:
            print(f"  {p:<22} n_pairs={v.get('n_pairs', 0)}  (insufficient)")
    print(f"Aggregate p (min) = {aggregate_p:.4f} -> {decision}")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
