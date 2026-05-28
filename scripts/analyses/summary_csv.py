"""Generate a human-readable SUMMARY.csv with all the v1 cell rates,
H6/H7/H8 deltas, and R7 κ. Designed for a casual repo visitor who wants
the numbers without parsing JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "data" / "processed" / "results"

sys.path.insert(0, str(REPO_ROOT / "scripts" / "analyses"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from _common import load_final_v1  # noqa: E402


def main() -> int:
    df = load_final_v1()
    df = df[df["turn1_is_correct"].astype("boolean") & df["turn2_is_correct"].notna()]
    df["flipped"] = (~df["turn2_is_correct"].astype(bool)).astype(float)

    # Cell-level flip rates
    rows = []
    for (p, c), g in df.groupby(["provider", "cell"]):
        rows.append({
            "provider": p,
            "cell": c,
            "n_graded": int(len(g)),
            "flip_rate": round(float(g["flipped"].mean()), 4),
        })
    cell_df = pd.DataFrame(rows).sort_values(["provider", "cell"])

    # Append H6/H7/H8 stats from results JSON
    h6 = json.loads((RESULTS / "H6.json").read_text())
    h7 = json.loads((RESULTS / "H7.json").read_text())
    h8 = json.loads((RESULTS / "H8.json").read_text())
    r7 = json.loads((RESULTS / "R7.json").read_text())

    stats_rows = []
    for p, v in h6["per_provider"].items():
        if "mean_diff_BV_minus_TV" in v:
            stats_rows.append({
                "test": "H6", "provider": p, "n_pairs": v["n_pairs"],
                "delta": round(v["mean_diff_BV_minus_TV"], 4),
                "p_value": round(v["p_one_sided_greater"], 4),
                "ci": f"[{v['ci_lo']:+.3f}, {v['ci_hi']:+.3f}]",
            })
    for p, v in h7["per_provider"].items():
        if "mean_diff_BV_minus_BF" in v:
            stats_rows.append({
                "test": "H7", "provider": p, "n_pairs": v["n_pairs"],
                "delta": round(v["mean_diff_BV_minus_BF"], 4),
                "p_value": round(v["p_one_sided_greater"], 4),
                "ci": f"[{v['ci_lo']:+.3f}, {v['ci_hi']:+.3f}]",
            })
    for p, v in h8["per_provider"].items():
        if "contrast_BF_minus_TV" in v:
            stats_rows.append({
                "test": "H8", "provider": p, "n_pairs": v["n_pairs"],
                "delta": round(v["contrast_BF_minus_TV"], 4),
                "p_value": round(v["p_two_sided"], 4),
                "ci": f"[{v['ci_lo']:+.3f}, {v['ci_hi']:+.3f}]",
            })
    stats_df = pd.DataFrame(stats_rows)

    # R7 grader agreement
    r7_rows = [{"check": "R7 grader κ (overall)",
                 "value": f"κ={r7['kappa_overall']:.3f} on n={r7['n_dual_graded']}"}]
    for p, v in r7["per_provider"].items():
        r7_rows.append({"check": f"R7 grader κ ({p})",
                         "value": f"κ={v['kappa']:.3f} on n={v['n']}"})
    r7_df = pd.DataFrame(r7_rows)

    out_csv = RESULTS / "SUMMARY.csv"
    out_md  = RESULTS / "SUMMARY.md"

    # Single CSV with sections
    sections = []
    sections.append("# Cell-level flip rates")
    sections.append(cell_df.to_csv(index=False).rstrip())
    sections.append("")
    sections.append("# Confirmatory tests (H6, H7, H8)")
    sections.append(stats_df.to_csv(index=False).rstrip())
    sections.append("")
    sections.append("# R7 cross-vendor grader robustness")
    sections.append(r7_df.to_csv(index=False).rstrip())
    out_csv.write_text("\n".join(sections) + "\n")
    print(f"Wrote {out_csv}")

    def df_to_md(df):
        """Tiny pure-python markdown table renderer; avoids the tabulate dep."""
        if df.empty:
            return "(empty)"
        cols = list(df.columns)
        lines = ["| " + " | ".join(cols) + " |",
                 "|" + "|".join(["---"] * len(cols)) + "|"]
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        return "\n".join(lines)

    md_lines = [
        "# Results summary",
        "",
        "Cell-level flip rates and confirmatory tests across the v1 factorial.",
        "All numbers reproducible from `scripts/v1_04_assemble.py` + "
        "`scripts/analyses/H[678]_*.py`.",
        "",
        "## Cell-level flip rates",
        "",
        "Flip rate = fraction of (turn-1 correct AND turn-2 graded) responses "
        "where the model abandoned its correct answer.",
        "",
        df_to_md(cell_df),
        "",
        "## Confirmatory tests",
        "",
        "Within-subject paired bootstrap, B=10,000.",
        "",
        df_to_md(stats_df),
        "",
        "## R7 cross-vendor grader",
        "",
        f"- Overall Cohen's κ vs GPT-4o-mini on n={r7['n_dual_graded']} stratified "
        f"sample: **{r7['kappa_overall']:.3f}**",
    ]
    for p, v in r7["per_provider"].items():
        md_lines.append(f"- {p} κ = {v['kappa']:.3f} on n={v['n']} "
                        f"(agree {v['agree_pct']:.1%})")
    out_md.write_text("\n".join(md_lines) + "\n")
    print(f"Wrote {out_md}")

    # Stdout preview
    print("\n=== preview ===")
    print(cell_df.to_string(index=False))
    print()
    print(stats_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
