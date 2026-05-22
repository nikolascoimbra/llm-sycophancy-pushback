"""H5 — Cross-paper Spearman between calibration ECE and sycophancy flip rate.

Per-provider TW flip rate from this study, joined with per-provider verbalized-
confidence ECE from the calibration study (constants in _common.py).

n = 4 providers; explicitly underpowered. We report the point estimate and a
bootstrap CI by resampling providers; no directional commitment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _common import CALIBRATION_ECE, PROVIDERS, load_final, write_results  # noqa: E402

from sycophancy.prereg import require_prereg_tag  # noqa: E402

B = 10_000
SEED = 20260521


def main() -> int:
    require_prereg_tag("prereg-v0")
    df = load_final()
    df = df[(df["template"] == "TW") & df["is_final_correct"].notna()].copy()
    df["flipped"] = ~df["is_final_correct"].astype(bool)

    per_provider = {}
    for p in PROVIDERS:
        g = df[df["provider"] == p]
        per_provider[p] = {
            "n": int(len(g)),
            "flip_rate_tw": float(g["flipped"].mean()) if len(g) else float("nan"),
            "calibration_ece": CALIBRATION_ECE[p],
        }

    flip_rates = np.array([per_provider[p]["flip_rate_tw"] for p in PROVIDERS])
    eces = np.array([per_provider[p]["calibration_ece"] for p in PROVIDERS])
    valid = ~np.isnan(flip_rates) & ~np.isnan(eces)
    n = int(valid.sum())
    if n < 3:
        payload = {"hypothesis": "H5", "decision": "underpowered",
                   "n_providers": n, "per_provider": per_provider}
        out = write_results("H5", payload)
        print(payload)
        print(f"Wrote {out}")
        return 0

    rho_obs = float(spearmanr(eces[valid], flip_rates[valid]).statistic)
    rng = np.random.default_rng(SEED)
    rhos = np.empty(B, dtype=float)
    for b in range(B):
        idx = rng.integers(0, n, n)
        rhos[b] = float(spearmanr(eces[valid][idx], flip_rates[valid][idx]).statistic) \
                  if n > 1 else float("nan")
    lo = float(np.nanquantile(rhos, 0.025))
    hi = float(np.nanquantile(rhos, 0.975))

    payload = {
        "hypothesis": "H5",
        "n_providers": n,
        "per_provider": per_provider,
        "spearman_rho_ece_vs_flip": rho_obs,
        "bootstrap_ci": {"lo": lo, "hi": hi, "B": B, "seed": SEED},
        "decision": "descriptive (n=4, no directional commitment)",
    }
    out = write_results("H5", payload)
    print("H5 — calibration ECE vs sycophancy flip rate (TW):")
    for p in PROVIDERS:
        v = per_provider[p]
        print(f"  {p:<22} n={v['n']:>3}  ECE={v['calibration_ece']:.3f}  "
              f"flip_rate={v['flip_rate_tw']:.3f}")
    print(f"Spearman rho = {rho_obs:.3f}  CI=({lo:.3f}, {hi:.3f})")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
