"""H1 — cross-provider variance in flip rate under wrong pushback (TW template).

Permutation omnibus on the per-question flip indicator under the terse-wrong
template. Test statistic is the variance of per-provider mean flip rate.
Provider labels are shuffled within question 10,000 times to build the null.

Refuses to run before Git tag prereg-v0.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _common import PROVIDERS, load_final, write_results  # noqa: E402

from sycophancy.prereg import require_prereg_tag  # noqa: E402
from sycophancy.stats import bootstrap_ci, permutation_omnibus_variance  # noqa: E402

B = 10_000
SEED = 20260521


def main() -> int:
    require_prereg_tag("prereg-v0")
    df = load_final()

    sub = df[(df["template"] == "TW") & (df["is_final_correct"].notna())].copy()
    # Per-provider flip rate (initial-correct AND final-incorrect; in this
    # study every cached eligible row is initial-correct by construction).
    per_provider = {}
    for p in PROVIDERS:
        g = sub[sub["provider"] == p]
        n = len(g)
        if n == 0:
            per_provider[p] = {"n": 0, "flip_rate": float("nan"),
                                "ci_lo": float("nan"), "ci_hi": float("nan")}
            continue
        flips = (~g["is_final_correct"].astype(bool)).astype(float).values
        boot = bootstrap_ci(flips, statistic=np.mean, B=B, seed=SEED)
        per_provider[p] = {"n": int(n), "flip_rate": boot.point,
                            "ci_lo": boot.lo, "ci_hi": boot.hi}

    # Build long arrays for the omnibus (every per-(provider, question) row)
    labels = sub["provider"].astype(str).values
    flips = (~sub["is_final_correct"].astype(bool)).astype(float).values
    omnibus = permutation_omnibus_variance(labels, flips, B=B, seed=SEED)

    decision = ("supported" if omnibus["p_value"] < 0.05 else
                "refuted" if omnibus["p_value"] >= 0.05 else "inconclusive")

    payload = {
        "hypothesis": "H1",
        "template": "TW (terse-wrong)",
        "per_provider": per_provider,
        "omnibus_p_value": omnibus["p_value"],
        "omnibus_observed_variance": omnibus["observed_variance"],
        "n_perm": omnibus["n_perm"],
        "decision": decision,
    }
    out = write_results("H1", payload)
    print(f"H1 — per-provider flip rate under TW:")
    for p, v in per_provider.items():
        print(f"  {p:<22} n={v['n']:>3}  flip_rate={v['flip_rate']:.3f}  "
              f"CI=({v['ci_lo']:.3f}, {v['ci_hi']:.3f})")
    print(f"Omnibus permutation p = {omnibus['p_value']:.4f}  -> {decision}")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
