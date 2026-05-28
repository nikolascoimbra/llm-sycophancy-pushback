"""E7 — Tool-invocation rate per (provider, cell).

Pure analysis on the existing v1 turn-2 cache. Each cached turn-2 response
has a `tool_invocations` field counting how many search calls the model
actually issued. Under tools-on cells, this is the model's own epistemic
policy — does it use the tool when it could?

Two questions:
  (1) Per provider, in cells where tools are AVAILABLE (T*-*), what
      fraction of responses invoke the tool at least once?
  (2) Does the rate differ between adversarial pushback (TW) and
      polite-agreement pushback (PR)? If models search under contradiction
      but not under agreement, that's a healthy epistemic policy.

Pre-registered as exploratory in prereg-v1 §5 E7.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _common import load_final_v1, V1_PROVIDERS_G, write_results  # noqa: E402


def main() -> int:
    df = load_final_v1()
    # E7 only meaningful for cells where tools are available
    tools_cells = ("TV-TW", "TV-PR", "TF-TW", "TF-PR")

    rows = []
    for p in V1_PROVIDERS_G:
        for c in tools_cells:
            g = df[(df["provider"] == p) & (df["cell"] == c)]
            if len(g) == 0:
                continue
            invocations = g["turn2_tool_invocations"].fillna(0).astype(int).values
            n = len(invocations)
            any_invoked = int((invocations >= 1).sum())
            mean_invocations = float(invocations.mean())
            invocation_rate = float((invocations >= 1).mean())
            rows.append({
                "provider": p,
                "cell": c,
                "n": int(n),
                "any_invoked": any_invoked,
                "invocation_rate": invocation_rate,
                "mean_invocations": mean_invocations,
            })

    out = pd.DataFrame(rows)
    print("E7 — tool-invocation rate per (provider, cell):")
    print(out.to_string(index=False))

    # Aggregate: TW vs PR comparison per provider
    print("\nE7 contrast — TW (contradiction) vs PR (agreement):")
    contrast_rows = []
    for p in V1_PROVIDERS_G:
        for gc in ("TV", "TF"):
            tw = out[(out["provider"] == p) & (out["cell"] == f"{gc}-TW")]
            pr = out[(out["provider"] == p) & (out["cell"] == f"{gc}-PR")]
            if tw.empty or pr.empty:
                continue
            tw_rate = tw["invocation_rate"].iloc[0]
            pr_rate = pr["invocation_rate"].iloc[0]
            tw_n = int(tw["n"].iloc[0])
            pr_n = int(pr["n"].iloc[0])
            contrast_rows.append({
                "provider": p,
                "gc_cell": gc,
                f"{gc}_TW_invocation_rate": tw_rate,
                f"{gc}_TW_n": tw_n,
                f"{gc}_PR_invocation_rate": pr_rate,
                f"{gc}_PR_n": pr_n,
                "delta_TW_minus_PR": tw_rate - pr_rate,
            })
            print(f"  {p:<22} {gc}: TW={tw_rate:.2f} (n={tw_n})  "
                  f"PR={pr_rate:.2f} (n={pr_n})  Δ={tw_rate-pr_rate:+.2f}")

    payload = {
        "hypothesis": "E7",
        "claim": "tools-available cells: invocation rate per (provider, cell), "
                 "and contrast between adversarial (TW) and agreement (PR) pushback",
        "per_cell": rows,
        "tw_vs_pr_contrast": contrast_rows,
    }
    out_path = write_results("E7", payload)
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
