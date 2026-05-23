"""Assemble v1 turn-1 + turn-2 caches and grader verdicts into a tidy parquet.

Output columns:
    provider, cell, question_id, topic, question, gold_answer, wrong_alt,
    grounding (bool), format_arm (verbalized|freeform), pushback_template (TW|PR),
    turn1_raw_text, turn1_final_answer, turn1_verdict, turn1_is_correct,
    turn2_raw_text, turn2_final_answer, turn2_verdict, turn2_is_correct,
    turn1_tool_invocations, turn2_tool_invocations,
    input_tokens_total, output_tokens_total, usd_total.

Reads:
    data/raw/v1/turn1/<provider>/<gc_cell>/<qid>.json
    data/raw/v1/turn2/<provider>/<cell>/<qid>.json
    data/raw/v1/grader_cache_turn1/<provider>/<gc_cell>/<qid>.json
    data/raw/v1/grader_cache_turn2/<provider>/<cell>/<qid>.json
Writes:
    data/processed/sycophancy_final_v1.parquet
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
TURN1_DIR = REPO_ROOT / "data" / "raw" / "v1" / "turn1"
TURN2_DIR = REPO_ROOT / "data" / "raw" / "v1" / "turn2"
GRADER_TURN1 = REPO_ROOT / "data" / "raw" / "v1" / "grader_cache_turn1"
GRADER_TURN2 = REPO_ROOT / "data" / "raw" / "v1" / "grader_cache_turn2"
OUT = REPO_ROOT / "data" / "processed" / "sycophancy_final_v1.parquet"
SIMPLEQA_SAMPLE = (
    REPO_ROOT.parent
    / "calibration-deployment-risk"
    / "data" / "processed" / "simpleqa_sample.parquet"
)


def _read_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    if not TURN2_DIR.exists():
        sys.exit(f"Missing {TURN2_DIR}. Nothing to assemble.")
    sample = pd.read_parquet(SIMPLEQA_SAMPLE).set_index("question_id")

    rows = []
    for turn2_cache in sorted(TURN2_DIR.rglob("*.json")):
        t2 = _read_json(turn2_cache)
        if t2 is None:
            continue
        provider = t2["provider"]
        cell = t2["cell"]
        qid = t2["question_id"]
        gc_cell, p_template = cell.split("-")

        t1 = _read_json(TURN1_DIR / provider / gc_cell / f"{qid}.json")
        g1 = _read_json(GRADER_TURN1 / provider / gc_cell / f"{qid}.json")
        g2 = _read_json(GRADER_TURN2 / provider / cell / f"{qid}.json")

        try:
            topic = sample.loc[int(qid) if qid.isdigit() else qid, "topic"]
        except KeyError:
            topic = None

        def _is_correct(v: str | None) -> bool | None:
            if v == "CORRECT":
                return True
            if v == "INCORRECT":
                return False
            return None

        rows.append({
            "provider": provider,
            "cell": cell,
            "gc_cell": gc_cell,
            "question_id": qid,
            "topic": topic,
            "question": sample.loc[int(qid) if qid.isdigit() else qid, "question"] if str(qid) in [str(x) for x in sample.index] else None,
            "gold_answer": t2.get("gold_answer"),
            "wrong_alt": t2.get("wrong_alt"),
            "grounding": t2.get("grounding"),
            "format_arm": t2.get("format_arm"),
            "pushback_template": p_template,
            "turn1_raw_text": (t1 or {}).get("raw_text"),
            "turn1_final_answer": (g1 or {}).get("final_answer"),
            "turn1_verdict": (g1 or {}).get("verdict"),
            "turn1_is_correct": _is_correct((g1 or {}).get("verdict")),
            "turn1_tool_invocations": (t1 or {}).get("tool_invocations", 0),
            "turn2_raw_text": t2.get("raw_text"),
            "turn2_final_answer": (g2 or {}).get("final_answer"),
            "turn2_verdict": (g2 or {}).get("verdict"),
            "turn2_is_correct": _is_correct((g2 or {}).get("verdict")),
            "turn2_tool_invocations": t2.get("tool_invocations", 0),
            "input_tokens_total": ((t1 or {}).get("input_tokens", 0) +
                                    t2.get("input_tokens", 0)),
            "output_tokens_total": ((t1 or {}).get("output_tokens", 0) +
                                     t2.get("output_tokens", 0)),
            "usd_total": ((t1 or {}).get("usd", 0.0) + t2.get("usd", 0.0)),
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}  rows={len(df)}")
    if df.empty:
        return 0
    print("\nPer (provider, cell) coverage:")
    for (p, c), g in df.groupby(["provider", "cell"]):
        n = len(g)
        n_t1_correct = int(g["turn1_is_correct"].sum())
        n_t2_correct = int((g["turn1_is_correct"] & g["turn2_is_correct"].fillna(False)).sum())
        n_flip = int((g["turn1_is_correct"] & (g["turn2_is_correct"] == False)).sum())  # noqa: E712
        print(f"  {p:<22} {c:<5}  n={n:>3}  t1_correct={n_t1_correct:>3}  "
              f"t2_correct={n_t2_correct:>3}  flips={n_flip:>3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
