#!/usr/bin/env bash
# Orchestrate the v1 pipeline from canonical turn-1 grading through analyses.
# Assumes canonical turn-1 inference has already been run (data/raw/v1/turn1/<provider>/BV/*).
# Each stage is idempotent and resumable; re-running re-grades / re-infers any
# entries that are missing or errored on a prior pass.
set -euo pipefail

PY=.venv/bin/python

echo "=========================="
echo "v1 pipeline orchestrator"
echo "=========================="

echo
echo "[1/8] Grade canonical turn-1 (BV cells)"
$PY scripts/v1_03_grade.py --stage turn1 --workers 8

echo
echo "[2/8] Compute eligibility v1"
$PY scripts/v1_02_eligibility.py

echo
echo "[3/8] Run non-canonical turn-1 (BF, TV, TF) — eligible questions only"
# Sequential per-provider with conservative workers to respect rate limits.
for prov in anthropic_sonnet_46 openai_gpt5 google_gemini deepseek_v3_2; do
    case "$prov" in
        anthropic_sonnet_46|google_gemini) WORKERS=2 ;;
        *) WORKERS=6 ;;
    esac
    $PY scripts/v1_01_inference.py --stage turn1_other --provider "$prov" --workers $WORKERS
done

echo
echo "[4/8] Grade non-canonical turn-1"
$PY scripts/v1_03_grade.py --stage turn1 --workers 8

echo
echo "[5/8] Run turn-2 pushback (8 cells, ex. T*-* DeepSeek)"
for prov in anthropic_sonnet_46 openai_gpt5 google_gemini deepseek_v3_2; do
    case "$prov" in
        anthropic_sonnet_46|google_gemini) WORKERS=2 ;;
        *) WORKERS=6 ;;
    esac
    $PY scripts/v1_01_inference.py --stage turn2 --provider "$prov" --workers $WORKERS
done

echo
echo "[6/8] Grade turn-2 responses"
$PY scripts/v1_03_grade.py --stage turn2 --workers 8

echo
echo "[7/8] Assemble v1 parquet"
$PY scripts/v1_04_assemble.py

echo
echo "[8/8] Run confirmatory analyses H6/H7/H8"
$PY scripts/analyses/H6_grounding_main.py
$PY scripts/analyses/H7_format_main.py
$PY scripts/analyses/H8_grounding_format_interaction.py

echo
echo "=========================="
echo "v1 pipeline complete"
echo "=========================="
