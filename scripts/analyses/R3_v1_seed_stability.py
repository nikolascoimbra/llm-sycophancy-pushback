"""R3 v1 — Bootstrap-seed stability for the v1 H6/H7/H8 tests.

Pre-registered as robustness check R3 in prereg-v0; extended to v1.
Re-runs the H6/H7/H8 paired bootstraps at three seeds and verifies CI
widths agree to within ±0.02.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _common import V1_PROVIDERS_C, V1_PROVIDERS_G, load_final_v1, pair_flip, write_results  # noqa: E402

from sycophancy.stats import bootstrap_p_value, paired_bootstrap_ci  # noqa: E402

B = 10_000
SEEDS = (20260523, 20260524, 20260525)


def seed_replication(df, providers, cell_a, cell_b, alt):
    """Return per-(provider × seed) CI widths and means."""
    rows = []
    for p in providers:
        pairs = pair_flip(df, p, cell_a, cell_b)
        if len(pairs) < 5:
            continue
        a = pairs["flip_a"].astype(float).values
        b = pairs["flip_b"].astype(float).values
        for s in SEEDS:
            boot = paired_bootstrap_ci(a, b, statistic=np.mean,
                                        B=B, seed=s, return_samples=True)
            pval = bootstrap_p_value(boot.samples, null_value=0.0, alternative=alt)
            rows.append({
                "provider": p, "seed": s,
                "n_pairs": int(len(pairs)),
                "point": float(boot.point),
                "ci_lo": float(boot.lo),
                "ci_hi": float(boot.hi),
                "ci_width": float(boot.hi - boot.lo),
                "p_value": pval,
            })
    return rows


def summarize_stability(rows, label):
    """For each provider, check that CI widths and points agree across seeds."""
    summary = []
    if not rows:
        return summary
    for p in {r["provider"] for r in rows}:
        sub = [r for r in rows if r["provider"] == p]
        widths = [r["ci_width"] for r in sub]
        points = [r["point"] for r in sub]
        max_width_diff = max(widths) - min(widths)
        max_point_diff = max(points) - min(points)
        flag = max_width_diff > 0.02
        summary.append({
            "test": label,
            "provider": p,
            "n_seeds": len(sub),
            "ci_width_range": [round(min(widths), 4), round(max(widths), 4)],
            "max_ci_width_diff": round(max_width_diff, 4),
            "max_point_diff": round(max_point_diff, 4),
            "stable_within_0.02": not flag,
        })
    return summary


def main() -> int:
    df = load_final_v1()

    h6_rows = seed_replication(df, V1_PROVIDERS_G, "BV-TW", "TV-TW", "greater")
    h7_rows = seed_replication(df, V1_PROVIDERS_C, "BV-TW", "BF-TW", "greater")
    h8_rows = seed_replication(df, V1_PROVIDERS_G, "BF-TW", "TV-TW", "two-sided")

    h6_sum = summarize_stability(h6_rows, "H6")
    h7_sum = summarize_stability(h7_rows, "H7")
    h8_sum = summarize_stability(h8_rows, "H8")

    all_stable = all(
        s["stable_within_0.02"]
        for s in (*h6_sum, *h7_sum, *h8_sum)
    )

    print("R3 v1 bootstrap-seed stability:")
    print(f"  seeds: {SEEDS}")
    for sub in (h6_sum, h7_sum, h8_sum):
        for s in sub:
            flag = "OK" if s["stable_within_0.02"] else "DRIFT"
            print(f"  {s['test']} {s['provider']:<22} CI-widths {s['ci_width_range']}  "
                  f"max-diff={s['max_ci_width_diff']:.4f}  {flag}")
    print(f"\nAll stable within ±0.02? {all_stable}")

    payload = {
        "robustness_check": "R3_v1",
        "claim": "Bootstrap CI widths for H6/H7/H8 stable across seeds "
                 f"{SEEDS} to within ±0.02 absolute.",
        "seeds": list(SEEDS),
        "h6_per_provider_per_seed": h6_rows,
        "h7_per_provider_per_seed": h7_rows,
        "h8_per_provider_per_seed": h8_rows,
        "h6_summary": h6_sum,
        "h7_summary": h7_sum,
        "h8_summary": h8_sum,
        "all_stable": all_stable,
    }
    out_path = write_results("R3_v1", payload)
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
