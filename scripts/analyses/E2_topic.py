"""E2 (exploratory) — per-topic flip rate stratified by SimpleQA's 10 topics."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from scipy.stats import kendalltau

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _common import PROVIDERS, load_final, write_results  # noqa: E402

from sycophancy.prereg import require_prereg_tag  # noqa: E402


def main() -> int:
    require_prereg_tag("prereg-v0")
    df = load_final()
    df = df[(df["template"] == "TW") & df["is_final_correct"].notna()].copy()
    df["flipped"] = (~df["is_final_correct"].astype(bool)).astype(int)

    pivot = (df.groupby(["topic", "provider"])["flipped"].mean()
                 .unstack().reindex(columns=list(PROVIDERS)))

    # Cross-topic rank consistency of providers
    topic_ranks = pivot.rank(axis=1)
    topics = list(pivot.index)
    pair_taus = []
    for i, t1 in enumerate(topics):
        for t2 in topics[i + 1:]:
            v1 = topic_ranks.loc[t1].dropna()
            v2 = topic_ranks.loc[t2].dropna()
            common = v1.index.intersection(v2.index)
            if len(common) >= 3:
                tau, _ = kendalltau(v1[common], v2[common])
                if tau == tau:  # not NaN
                    pair_taus.append(float(tau))
    mean_tau = float(sum(pair_taus) / len(pair_taus)) if pair_taus else float("nan")

    payload = {
        "hypothesis": "E2 (exploratory)",
        "pivot_flip_rate": pivot.to_dict(),
        "mean_pairwise_kendall_tau": mean_tau,
        "n_topics": int(len(topics)),
    }
    out = write_results("E2_topic", payload)
    print("E2 — per-topic TW flip rate (rows=topic, cols=provider):")
    print(pivot.round(3).to_string())
    print(f"\nMean pairwise Kendall tau across topics: {mean_tau:.3f}")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
