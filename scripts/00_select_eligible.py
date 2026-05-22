"""Select eligible questions per provider from the calibration study cache.

Eligibility rule (pre-registered, amendment A1 lowered threshold from 0.5 to 0.3):
the provider's calibration-cached initial answer was graded CORRECT AND the
verbalized confidence was >= 0.30. The 0.30 threshold corresponds to "above
one-in-three" confidence — the model has a position to defend, not a coin
flip. It was lowered from the originally pre-registered 0.50 in response to
the empirical Claude confidence distribution (mean 0.29, median 0.35),
documented in docs/AMENDMENTS.md.

Reads:  ../calibration-deployment-risk/data/processed/simpleqa_verbalized.parquet
Writes: data/processed/eligible_questions.parquet
        data/processed/eligibility_report.txt
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CALIB_PARQUET = (
    REPO_ROOT.parent
    / "calibration-deployment-risk"
    / "data"
    / "processed"
    / "simpleqa_verbalized.parquet"
)
OUT_PARQUET = REPO_ROOT / "data" / "processed" / "eligible_questions.parquet"
OUT_REPORT = REPO_ROOT / "data" / "processed" / "eligibility_report.txt"

CONFIDENCE_THRESHOLD = 0.30
MIN_PER_PROVIDER = 100  # augmentation trigger; we report but do not augment


def main() -> int:
    if not CALIB_PARQUET.exists():
        sys.exit(f"Missing calibration cache: {CALIB_PARQUET}")
    df = pd.read_parquet(CALIB_PARQUET).dropna(
        subset=["parsed_confidence", "is_correct"]
    )

    rows = []
    report_lines = [
        f"Eligibility filter applied to {CALIB_PARQUET.name}",
        f"Rule: is_correct == True AND parsed_confidence >= {CONFIDENCE_THRESHOLD}",
        "",
        f"{'model':<22}  {'n_total':>8}  {'n_correct':>9}  {'eligible':>8}  {'mean_conf':>9}",
    ]
    for model, g in df.groupby("model"):
        correct = g[g["is_correct"] == True]  # noqa: E712 (pandas bool)
        eligible = correct[
            correct["parsed_confidence"].astype(float) >= CONFIDENCE_THRESHOLD
        ].copy()
        eligible["provider"] = model
        rows.append(eligible)
        report_lines.append(
            f"  {model:<20}  {len(g):>8}  {len(correct):>9}  "
            f"{len(eligible):>8}  {correct['parsed_confidence'].astype(float).mean():>9.3f}"
        )
        if len(eligible) < MIN_PER_PROVIDER:
            report_lines.append(
                f"    (below {MIN_PER_PROVIDER} threshold; augmentation rule "
                f"would apply per prereg §2.2; deferred — see docs/AMENDMENTS.md A2)"
            )

    out = pd.concat(rows, ignore_index=True)
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    cols = ["provider", "question_id", "topic", "question", "gold_answer",
            "parsed_answer", "parsed_confidence", "is_correct"]
    out[cols].to_parquet(OUT_PARQUET, index=False)
    report_lines.extend(["", f"Wrote {OUT_PARQUET}  rows={len(out)}"])
    OUT_REPORT.write_text("\n".join(report_lines) + "\n")
    print("\n".join(report_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
