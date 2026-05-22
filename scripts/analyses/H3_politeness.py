"""H3 — Politeness modulation: PW flip rate exceeds TW flip rate per provider, paired."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

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
        pivot = g.pivot_table(index="question_id", columns="template",
                              values="flipped", aggfunc="first")
        if "PW" not in pivot.columns or "TW" not in pivot.columns:
            per_provider[p] = {"n_pairs": 0, "mean_diff": float("nan")}
            continue
        paired = pivot[["PW", "TW"]].dropna()
        if len(paired) < 5:
            per_provider[p] = {"n_pairs": len(paired), "mean_diff": float("nan")}
            continue
        pw = paired["PW"].astype(float).values
        tw = paired["TW"].astype(float).values
        boot = paired_bootstrap_ci(pw, tw, statistic=np.mean,
                                     B=B, seed=SEED, return_samples=True)
        p_value = bootstrap_p_value(boot.samples, null_value=0.0,
                                     alternative="greater")
        per_provider[p] = {
            "n_pairs": int(len(paired)),
            "mean_diff_pw_minus_tw": boot.point,
            "ci_lo": boot.lo, "ci_hi": boot.hi,
            "p_one_sided_greater": p_value,
        }

    pvals = [v["p_one_sided_greater"] for v in per_provider.values()
             if "p_one_sided_greater" in v]
    aggregate_p = min(pvals) if pvals else float("nan")
    decision = ("supported" if aggregate_p < 0.05 else
                "refuted" if aggregate_p >= 0.95 else "inconclusive")

    payload = {
        "hypothesis": "H3",
        "per_provider": per_provider,
        "aggregate_p_value": aggregate_p,
        "decision": decision,
    }
    out = write_results("H3", payload)
    print("H3 — PW (polite-wrong) vs TW (terse-wrong) per-provider paired difference:")
    for p, v in per_provider.items():
        if "mean_diff_pw_minus_tw" in v:
            print(f"  {p:<22} n_pairs={v['n_pairs']:>3}  "
                  f"diff={v['mean_diff_pw_minus_tw']:+.3f}  "
                  f"CI=({v['ci_lo']:+.3f}, {v['ci_hi']:+.3f})  "
                  f"p={v['p_one_sided_greater']:.4f}")
        else:
            print(f"  {p:<22} insufficient")
    print(f"Aggregate p = {aggregate_p:.4f} -> {decision}")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
