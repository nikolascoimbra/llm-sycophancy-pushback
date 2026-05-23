"""Shared helpers for the H1-H5 / E1-E3 / R1-R3 analysis scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

SYCO_PARQUET = REPO_ROOT / "data" / "processed" / "sycophancy_final.parquet"
SYCO_PARQUET_V1 = REPO_ROOT / "data" / "processed" / "sycophancy_final_v1.parquet"
RESULTS_DIR = REPO_ROOT / "data" / "processed" / "results"

PROVIDERS = ("anthropic_opus", "openai_gpt5", "deepseek_v3", "llama4_maverick")
EXTENDED_PROVIDERS = (
    "anthropic_opus", "openai_gpt5", "deepseek_v3", "llama4_maverick",
    "openai_gpt4o", "claude_sonnet_4_6", "mistral_large_3", "amazon_nova_pro",
    # openai_gpt5_mini dropped due to OpenAI 429 rate-limit exhaustion (0 valid).
)
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


def load_final_v1() -> pd.DataFrame:
    """Load the v1 factorial dataset assembled by scripts/v1_04_assemble.py."""
    if not SYCO_PARQUET_V1.exists():
        sys.exit(f"Missing {SYCO_PARQUET_V1}. Run scripts/v1_04_assemble.py first.")
    df = pd.read_parquet(SYCO_PARQUET_V1)
    df["flipped"] = (df["turn1_is_correct"].astype("boolean") &
                      ~df["turn2_is_correct"].astype("boolean"))
    return df


V1_PROVIDERS_C = ("anthropic_sonnet_46", "openai_gpt5", "google_gemini", "deepseek_v3_2")
V1_PROVIDERS_G = ("anthropic_sonnet_46", "openai_gpt5", "google_gemini")


def pair_flip(df: pd.DataFrame, provider: str, cell_a: str, cell_b: str) -> pd.DataFrame:
    """Per-question matched pair for cells (a, b) on questions where turn-1
    was correct in BOTH cells. Returns columns flip_a, flip_b.
    """
    g = df[df["provider"] == provider]
    pivot_t1 = g.pivot_table(index="question_id", columns="cell",
                              values="turn1_is_correct", aggfunc="first")
    pivot_flip = g.pivot_table(index="question_id", columns="cell",
                                values="flipped", aggfunc="first")
    if cell_a not in pivot_flip.columns or cell_b not in pivot_flip.columns:
        return pd.DataFrame(columns=["flip_a", "flip_b"])
    mask = (pivot_t1.get(cell_a) == True) & (pivot_t1.get(cell_b) == True)  # noqa: E712
    pairs = pd.DataFrame({
        "flip_a": pivot_flip[cell_a].where(mask),
        "flip_b": pivot_flip[cell_b].where(mask),
    }).dropna()
    return pairs


def write_results(name: str, payload: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{name}.json"
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return out
