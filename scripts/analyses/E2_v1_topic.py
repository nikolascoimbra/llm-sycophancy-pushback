"""E2 v1 — Per-topic stratification of the v1 grounding contrast.

Pre-registered as exploratory in prereg-v1 §5 (extension of the prereg-v0
E2 analysis to the v1 factorial). For each (provider, topic), compute the
flip rate under BV-TW (bare API) and TV-TW (tools-on). Report the
per-topic Δ to see if the grounding effect varies across SimpleQA topic
categories.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _common import load_final_v1, V1_PROVIDERS_G, write_results  # noqa: E402


def main() -> int:
    df = load_final_v1()
    # Restrict to G-arm providers + matched within-subject set
    df = df[df["provider"].isin(V1_PROVIDERS_G) & df["topic"].notna()]
    df = df[df["cell"].isin({"BV-TW", "TV-TW"})]
    df = df[df["turn1_is_correct"].astype("boolean") &
            df["turn2_is_correct"].notna()]
    df["flipped"] = (~df["turn2_is_correct"].astype(bool)).astype(float)

    rows = []
    for (p, t), g in df.groupby(["provider", "topic"]):
        bv = g[g["cell"] == "BV-TW"]["flipped"]
        tv = g[g["cell"] == "TV-TW"]["flipped"]
        if len(bv) < 2 and len(tv) < 2:
            continue
        rows.append({
            "provider": p, "topic": t,
            "n_BV_TW": int(len(bv)),
            "flip_BV_TW": float(bv.mean()) if len(bv) else float("nan"),
            "n_TV_TW": int(len(tv)),
            "flip_TV_TW": float(tv.mean()) if len(tv) else float("nan"),
            "delta": (float(bv.mean()) - float(tv.mean()))
                       if len(bv) and len(tv) else float("nan"),
        })

    out_df = pd.DataFrame(rows)
    print("E2 v1 — per-topic flip rates under BV-TW vs TV-TW (G-arm only):")
    print(out_df.to_string(index=False))

    # Aggregate: median Δ per provider across topics
    summary = []
    for p in V1_PROVIDERS_G:
        sub = out_df[out_df["provider"] == p]
        valid = sub["delta"].dropna()
        if len(valid):
            summary.append({
                "provider": p,
                "n_topics": int(len(valid)),
                "median_delta": float(valid.median()),
                "min_delta": float(valid.min()),
                "max_delta": float(valid.max()),
            })

    print("\nPer-provider topic summary:")
    print(pd.DataFrame(summary).to_string(index=False))

    payload = {
        "hypothesis": "E2_v1",
        "claim": "Per-topic flip rates under bare-API vs tools-on, "
                 "showing whether the grounding effect varies by topic.",
        "per_provider_topic": rows,
        "per_provider_summary": summary,
    }
    out_path = write_results("E2_v1", payload)
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
