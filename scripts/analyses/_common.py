"""Shared helpers for the H1-H5 / E1-E3 / R1-R3 analysis scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

SYCO_PARQUET = REPO_ROOT / "data" / "processed" / "sycophancy_final.parquet"
RESULTS_DIR = REPO_ROOT / "data" / "processed" / "results"

PROVIDERS = ("anthropic_opus", "openai_gpt5", "deepseek_v3", "llama4_maverick")
TEMPLATES = ("TW", "PW", "AW", "PR")

# Calibration ECE per provider (from calibration paper, for H5 cross-paper join)
CALIBRATION_ECE = {
    "anthropic_opus":  0.119,
    "openai_gpt5":     0.258,
    "llama4_maverick": 0.437,
    "deepseek_v3":     0.539,
}


def load_final() -> pd.DataFrame:
    if not SYCO_PARQUET.exists():
        sys.exit(f"Missing {SYCO_PARQUET}. Run scripts/03_grade.py first.")
    return pd.read_parquet(SYCO_PARQUET)


def write_results(name: str, payload: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{name}.json"
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return out
