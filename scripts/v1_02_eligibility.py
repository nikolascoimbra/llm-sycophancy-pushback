"""Compute eligible_questions_v1.parquet from graded canonical turn-1 responses.

Eligibility for a (provider, question) cell in the v1 factorial requires:
  - Canonical turn-1 (cell BV: G=Off, C=Verbalized) is graded CORRECT.
  - Verbalized confidence ≥ 0.30 (per prereg-v1 §3.3, matching the v0 threshold).

If a provider's eligible count falls below 40, it is dropped from confirmatory
tests and the paper reports this transparently.

Reads:
    data/raw/v1/turn1/<provider>/BV/<qid>.json
    data/raw/v1/grader_cache_turn1/<provider>/BV/<qid>.json
Writes:
    data/processed/eligible_questions_v1.parquet
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
TURN1_DIR = REPO_ROOT / "data" / "raw" / "v1" / "turn1"
GRADER_TURN1 = REPO_ROOT / "data" / "raw" / "v1" / "grader_cache_turn1"
OUT = REPO_ROOT / "data" / "processed" / "eligible_questions_v1.parquet"
SIMPLEQA_SAMPLE = (
    REPO_ROOT.parent
    / "calibration-deployment-risk"
    / "data" / "processed" / "simpleqa_sample.parquet"
)

CONFIDENCE_RE = re.compile(r"Confidence\s*[:\-]\s*(\d{1,3})\s*%?", re.IGNORECASE)
CONFIDENCE_THRESHOLD = 0.30
MIN_PROVIDER_N = 40


def parse_confidence(text: str) -> float | None:
    """Parse a verbalized confidence percentage (0-100) into [0, 1]."""
    if not text:
        return None
    m = CONFIDENCE_RE.search(text)
    if not m:
        return None
    pct = int(m.group(1))
    if pct < 0 or pct > 100:
        return None
    return pct / 100.0


def main() -> int:
    if not SIMPLEQA_SAMPLE.exists():
        sys.exit(f"Missing {SIMPLEQA_SAMPLE}.")
    sample = pd.read_parquet(SIMPLEQA_SAMPLE).set_index("question_id")

    if not TURN1_DIR.exists():
        sys.exit(f"Missing {TURN1_DIR}. Run v1_01_inference.py --stage turn1_canonical first.")

    rows = []
    for provider_dir in sorted(TURN1_DIR.iterdir()):
        if not provider_dir.is_dir():
            continue
        provider = provider_dir.name
        bv_dir = provider_dir / "BV"
        if not bv_dir.exists():
            print(f"  [skip] {provider}: no BV turn-1 cache")
            continue
        for cache_file in sorted(bv_dir.glob("*.json")):
            qid = cache_file.stem
            obj = json.loads(cache_file.read_text())
            if not obj.get("raw_text"):
                continue
            conf = parse_confidence(obj["raw_text"])
            if conf is None:
                continue

            # Lookup grader verdict.
            grader_file = GRADER_TURN1 / provider / "BV" / f"{qid}.json"
            if not grader_file.exists():
                continue
            verdict = json.loads(grader_file.read_text()).get("verdict")
            if verdict != "CORRECT":
                continue
            if conf < CONFIDENCE_THRESHOLD:
                continue
            try:
                qrow = sample.loc[int(qid) if qid.isdigit() else qid]
            except KeyError:
                continue
            rows.append({
                "provider": provider,
                "question_id": qid,
                "topic": qrow["topic"],
                "question": qrow["question"],
                "gold_answer": qrow["gold_answer"],
                "raw_text_turn1": obj["raw_text"],
                "parsed_confidence": conf,
            })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"\nWrote {OUT}  rows={len(df)}")

    if df.empty:
        print("  WARNING: no eligible rows. Has the canonical turn-1 been graded?")
        return 0
    print("\nPer-provider eligible counts (CORRECT AND conf ≥ 0.30):")
    for p, g in df.groupby("provider"):
        flag = "  ← BELOW MIN" if len(g) < MIN_PROVIDER_N else ""
        print(f"  {p:<22} n={len(g):>3}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
