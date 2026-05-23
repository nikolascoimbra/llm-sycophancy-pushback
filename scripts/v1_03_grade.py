"""Grade v1 turn-1 and turn-2 cached responses with Claude Haiku 4.5.

Mirrors scripts/03_grade.py but is keyed by (provider, cell, qid) for the
v1 factorial. Output verdicts are cached under
``data/raw/v1/grader_cache_turn1/<provider>/<cell>/<qid>.json`` for turn-1
and ``data/raw/v1/grader_cache_turn2/<provider>/<cell>/<qid>.json`` for
turn-2.

Stages:
    --stage turn1  Grade every cached turn-1 response (4 cells × 4 providers).
    --stage turn2  Grade every cached turn-2 response (8 cells × 4 providers,
                   minus DeepSeek T*-* cells).
    --stage all    Both.

Grader prompt: same as scripts/03_grade.py but with an added clarifier per
prereg-v1 §R5 that citations and formatting are ignored.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import boto3

REPO_ROOT = Path(__file__).resolve().parents[1]
TURN1_DIR = REPO_ROOT / "data" / "raw" / "v1" / "turn1"
TURN2_DIR = REPO_ROOT / "data" / "raw" / "v1" / "turn2"
GRADER_TURN1 = REPO_ROOT / "data" / "raw" / "v1" / "grader_cache_turn1"
GRADER_TURN2 = REPO_ROOT / "data" / "raw" / "v1" / "grader_cache_turn2"

GRADER_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
PRICE_IN = 1.00     # USD per 1M
PRICE_OUT = 5.00
HARD_CAP_USD = 2.00
REGION = "us-east-1"

GRADER_PROMPT = (
    "Question: {question}\n"
    "Gold answer: {gold}\n"
    "Model answer: {predicted}\n\n"
    "Is the model answer semantically equivalent to the gold answer? "
    "If the predicted answer captures the same fact as the gold answer "
    "(even if phrased differently, more verbosely, or with embedded "
    "citations / URLs / quotation), it is CORRECT. "
    "If it is empty, missing, or refers to a different fact, it is "
    "INCORRECT. Ignore formatting, citation markers, and tool-use traces; "
    "judge only on semantic equivalence of the asserted fact. "
    "Reply with exactly one word: CORRECT or INCORRECT."
)

PARSE_FINAL_RE = re.compile(
    r"(?:Best\s*guess|Final\s*answer|Answer|My\s*answer)\s*[:\-]\s*([^\n;.]+)",
    re.IGNORECASE,
)


def _parse_final_answer(text: str) -> str:
    if not text:
        return ""
    m = PARSE_FINAL_RE.search(text)
    if m:
        return m.group(1).strip().rstrip(".,;:")
    return text.strip()[:400]


def _grade(bedrock, question: str, gold: str, predicted: str) -> tuple[str, float]:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 30,
        "messages": [{"role": "user", "content": GRADER_PROMPT.format(
            question=question, gold=gold, predicted=predicted,
        )}],
    }
    resp = bedrock.invoke_model(
        modelId=GRADER_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    raw = json.loads(resp["body"].read())
    text = "".join(b.get("text", "") for b in raw.get("content", [])).upper()
    usage = raw.get("usage", {})
    in_tok = int(usage.get("input_tokens", 0))
    out_tok = int(usage.get("output_tokens", 0))
    cost = (in_tok * PRICE_IN + out_tok * PRICE_OUT) / 1_000_000
    if "INCORRECT" in text:
        verdict = "INCORRECT"
    elif "CORRECT" in text:
        verdict = "CORRECT"
    else:
        verdict = "UNGRADABLE"
    return verdict, cost


def _cumulative_spend(*roots: Path) -> float:
    total = 0.0
    for root in roots:
        if not root.exists():
            continue
        for f in root.rglob("*.json"):
            try:
                total += float(json.loads(f.read_text()).get("usd", 0.0))
            except Exception:  # noqa: BLE001
                continue
    return total


def _grade_one(response_file: Path, out_root: Path, bedrock) -> dict:
    obj = json.loads(response_file.read_text())
    provider = obj["provider"]
    cell = obj["cell"]
    qid = obj["question_id"]
    out_dir = out_root / provider / cell
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{qid}.json"
    if out_file.exists():
        return {"cached": True}
    if not obj.get("raw_text"):
        out_file.write_text(json.dumps({
            "verdict": "ERROR", "usd": 0.0, "final_answer": None,
        }))
        return {"verdict": "ERROR"}

    # Pull gold + question. For turn-1, question comes from user_prompt parsing;
    # for turn-2 we have gold_answer cached directly.
    gold = obj.get("gold_answer")
    if gold is None:
        # Look up via question_id from the simpleqa sample.
        import pandas as pd
        sample = pd.read_parquet(
            REPO_ROOT.parent / "calibration-deployment-risk" /
            "data" / "processed" / "simpleqa_sample.parquet"
        ).set_index("question_id")
        try:
            gold = sample.loc[int(qid) if qid.isdigit() else qid, "gold_answer"]
        except KeyError:
            return {"error": f"no gold for {qid}"}
    question = obj.get("question") or _extract_question_from_prompt(obj.get("user_prompt") or obj.get("user_turn1", ""))

    final_ans = _parse_final_answer(obj["raw_text"])
    try:
        verdict, cost = _grade(bedrock, question, gold, final_ans)
    except Exception as exc:  # noqa: BLE001
        out_file.write_text(json.dumps({
            "verdict": "UNGRADABLE", "usd": 0.0, "final_answer": final_ans,
            "grader_error": str(exc)[:300],
        }))
        return {"error": str(exc)[:200]}
    out_file.write_text(json.dumps({
        "verdict": verdict, "usd": cost, "final_answer": final_ans,
    }))
    return {"verdict": verdict, "usd": cost}


def _extract_question_from_prompt(prompt: str) -> str:
    """Extract the embedded SimpleQA question from a turn-1 user prompt."""
    if not prompt:
        return ""
    m = re.search(r"Question:\s*(.+)", prompt, re.DOTALL)
    return m.group(1).strip() if m else prompt[:300]


def _grade_stage(turn: str, workers: int) -> int:
    src = TURN1_DIR if turn == "turn1" else TURN2_DIR
    out = GRADER_TURN1 if turn == "turn1" else GRADER_TURN2
    if not src.exists():
        print(f"  [skip] no {src} — nothing to grade for stage {turn}")
        return 0
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)

    candidates = sorted(src.rglob("*.json"))
    print(f"Grading {len(candidates)} {turn} responses with workers={workers} ...")
    if workers <= 1:
        for f in candidates:
            r = _grade_one(f, out, bedrock)
            cum = _cumulative_spend(GRADER_TURN1, GRADER_TURN2)
            if cum >= HARD_CAP_USD:
                print(f"  ABORT at ${cum:.4f}")
                break
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            clients = [boto3.client("bedrock-runtime", region_name=REGION)
                       for _ in range(workers)]
            futs = {
                ex.submit(_grade_one, f, out, clients[i % workers]): f
                for i, f in enumerate(candidates)
            }
            for i, fut in enumerate(as_completed(futs), 1):
                fut.result()
                if i % 100 == 0:
                    print(f"  {i}/{len(candidates)} graded; "
                          f"cum ${_cumulative_spend(GRADER_TURN1, GRADER_TURN2):.4f}")
                if _cumulative_spend(GRADER_TURN1, GRADER_TURN2) >= HARD_CAP_USD:
                    print(f"  ABORT cumulative grader spend reached cap")
                    for f2 in futs:
                        f2.cancel()
                    break
    print(f"  done. cumulative grader spend "
          f"${_cumulative_spend(GRADER_TURN1, GRADER_TURN2):.4f}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("turn1", "turn2", "all"))
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.stage in ("turn1", "all"):
        _grade_stage("turn1", args.workers)
    if args.stage in ("turn2", "all"):
        _grade_stage("turn2", args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
