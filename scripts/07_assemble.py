"""Assemble per-hypothesis JSON bundles into a single paper-ready summary table."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from sycophancy.stats import holm_bonferroni  # noqa: E402

RESULTS = REPO_ROOT / "data" / "processed" / "results"
TABLE_OUT = REPO_ROOT / "paper" / "results_summary_table.md"


def _load(name: str) -> dict | None:
    p = RESULTS / f"{name}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def main():
    h = {n: _load(n) for n in ("H1", "H2", "H3", "H4", "H5")}

    lines = ["| Hypothesis | Estimate | 95% CI | Aggregate p | Decision |",
             "|---|---|---|---|---|"]

    # H1
    if h["H1"]:
        v = h["H1"]
        per_p_summary = ", ".join(
            f"{p.split('_')[0][:6]}={v['per_provider'][p]['flip_rate']:.2f}"
            for p in v["per_provider"]
        )
        lines.append(
            f"| H1 cross-provider variance | omnibus | per-provider TW: {per_p_summary} | "
            f"{v['omnibus_p_value']:.4f} | {v['decision']} |"
        )

    # H2, H3, H4
    family_p = []
    family_labels = []
    if h["H1"]:
        family_p.append(h["H1"]["omnibus_p_value"])
        family_labels.append("H1")
    for hkey, label in (("H2", "TW vs PR"), ("H3", "PW vs TW"), ("H4", "AW vs TW")):
        if h[hkey]:
            v = h[hkey]
            agg_p = v.get("aggregate_p_value", float("nan"))
            family_p.append(agg_p)
            family_labels.append(hkey)
            per = v.get("per_provider", {})
            diffs = []
            for p, vv in per.items():
                if "p_one_sided_greater" in vv:
                    diff_key = next((k for k in vv if k.startswith("mean_diff")), None)
                    if diff_key:
                        diffs.append(f"{p.split('_')[0][:6]}={vv[diff_key]:+.3f}")
            lines.append(
                f"| {hkey} {label} | min over providers | "
                f"{'; '.join(diffs)} | {agg_p:.4f} | {v['decision']} |"
            )

    # H5
    if h["H5"]:
        v = h["H5"]
        rho = v.get("spearman_rho_ece_vs_flip", float("nan"))
        ci = v.get("bootstrap_ci", {})
        lines.append(
            f"| H5 calibration ↔ sycophancy (n=4) | ρ = {rho:.3f} | "
            f"({ci.get('lo', float('nan')):.3f}, {ci.get('hi', float('nan')):.3f}) | "
            f"— | {v['decision']} |"
        )

    # Holm-Bonferroni
    if family_p:
        rej = holm_bonferroni(family_p, alpha=0.05)
        lines.append("")
        lines.append("**Holm-Bonferroni at family-wise α = 0.05 across confirmatory hypotheses:**")
        lines.append("")
        lines.append("| Hypothesis | p | Reject H₀? |")
        lines.append("|---|---|---|")
        for lab, p_, r in zip(family_labels, family_p, rej, strict=True):
            lines.append(f"| {lab} | {p_:.4f} | {'yes' if r else 'no'} |")

    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    TABLE_OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {TABLE_OUT}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
