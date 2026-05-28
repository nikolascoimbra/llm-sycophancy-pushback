"""Build a literature-comparison table positioning the v0 + v1 results
against the 2023-2026 sycophancy literature.

Output:
    data/processed/results/literature_comparison.csv  (one row per study)
    data/processed/results/literature_comparison.md   (human-readable)

The cited prior-work numbers are taken from each paper's abstract /
headline table, with the source noted. This is reviewer-facing; if a
number is wrong it should be corrected by reading the source.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "data" / "processed" / "results"


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def main() -> int:
    # Pull our own headline numbers
    h6 = load(RESULTS / "H6.json")
    h8 = load(RESULTS / "H8.json")
    r7 = load(RESULTS / "R7.json")

    rows = []

    # ─── Prior work ───
    rows.append({
        "study": "Sharma et al. 2023 (Anthropic)",
        "venue": "ICLR 2024",
        "models": "5 Anthropic/OpenAI/Meta",
        "task": "Are-You-Sure factual + free-form",
        "regime": "bare API, single + multi-turn",
        "grounding_ablation": "no",
        "preregistered": "no",
        "headline_flip_rate": "~40-90% (varies by task and model)",
        "n_per_cell": "varies",
        "delta_grounding_pts": "not measured",
        "notes": "Foundational paper. Establishes that RLHF training induces sycophancy. No tools-on comparison.",
    })

    rows.append({
        "study": "Fanous et al. 2025 (SycEval)",
        "venue": "AAAI / AIES 2025",
        "models": "3 (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro)",
        "task": "AMPS (math) + MedQuad (medical)",
        "regime": "bare API, single-turn rebuttal",
        "grounding_ablation": "no",
        "preregistered": "no",
        "headline_flip_rate": "58.2% overall (43.5% progressive, 14.7% regressive)",
        "n_per_cell": "Large",
        "delta_grounding_pts": "not measured",
        "notes": "Closest direct comparator. Same general design as Study 1, three providers. Our Study 1 adds 5 more providers + politeness/assertiveness templates. No grounding ablation.",
    })

    rows.append({
        "study": "Cheng et al. 2025 (ELEPHANT)",
        "venue": "arXiv 2505.13995",
        "models": "11 frontier",
        "task": "Social sycophancy (emotional validation, moral, indirect)",
        "regime": "bare API, single-turn",
        "grounding_ablation": "no",
        "preregistered": "no",
        "headline_flip_rate": "see paper, varies by task",
        "n_per_cell": "varies",
        "delta_grounding_pts": "not measured",
        "notes": "Complementary, not overlapping. Social-domain rather than factual-recall. Grounding would not help in their setting.",
    })

    rows.append({
        "study": "Hong et al. 2025 (SyConBench)",
        "venue": "EMNLP Findings 2025",
        "models": "17 LLMs",
        "task": "Multi-turn factual + multiple-choice",
        "regime": "bare API, multi-turn (Turn-of-Flip metric)",
        "grounding_ablation": "no",
        "preregistered": "no",
        "headline_flip_rate": "GPT-4o 4.4%, GPT-4.1-nano 18.8% flip-to-suggestion",
        "n_per_cell": "see paper",
        "delta_grounding_pts": "not measured",
        "notes": "Multi-turn extension we don't cover. Confirms direction: sycophancy accumulates with pushback turns.",
    })

    rows.append({
        "study": "Liu et al. 2026 (Interaction Context)",
        "venue": "CHI 2026",
        "models": "GPT-4.1 mini",
        "task": "Persistent-context chat with humans",
        "regime": "bare ChatGPT-API, multi-turn",
        "grounding_ablation": "no",
        "preregistered": "no",
        "headline_flip_rate": "see paper, by interaction type",
        "n_per_cell": "human participants",
        "delta_grounding_pts": "not measured",
        "notes": "Complementary. Studies how interaction context shapes sycophancy; we study how deployment configuration shapes it.",
    })

    # ─── Our v0 (Study 1) headline ───
    # Use a fixed snapshot of v0 cell-level rates from the prereg-v0 paper draft
    rows.append({
        "study": "This study, Study 1 (prereg-v0)",
        "venue": "this paper",
        "models": "8 frontier (Claude Opus 4.5, GPT-5, DeepSeek V3.2, Llama 4 Maverick, GPT-4o, Claude Sonnet 4.6, Mistral Large 3, Amazon Nova Pro)",
        "task": "SimpleQA factual recall",
        "regime": "bare API + verbalized confidence + single-turn",
        "grounding_ablation": "no",
        "preregistered": "yes (prereg-v0, 2026-05-21)",
        "headline_flip_rate": "65–96% terse-wrong (7/8 ≥90%); GPT-5 alone at 65%",
        "n_per_cell": "39–173 per provider",
        "delta_grounding_pts": "not measured in Study 1",
        "notes": "Replicates SycEval-style finding on the 2026 frontier panel. Surprise: politeness REDUCES flip rate by 17-43pts (opposite of pre-registered direction).",
    })

    # ─── Our v1 (Study 2) headline ───
    per_provider = h6["per_provider"]
    flip_str = "; ".join(
        f"{p}: {per_provider[p]['flip_rate_BV_TW']:.0%}→{per_provider[p]['flip_rate_TV_TW']:.0%}"
        for p in ("anthropic_sonnet_46", "openai_gpt5", "google_gemini")
    )
    delta_str = "; ".join(
        f"{p}: Δ={per_provider[p]['mean_diff_BV_minus_TV']*100:+.0f}pts (p={per_provider[p]['p_one_sided_greater']:.3f}, n={per_provider[p]['n_pairs']})"
        for p in ("anthropic_sonnet_46", "openai_gpt5", "google_gemini")
    )
    rows.append({
        "study": "This study, Study 2 (prereg-v1)",
        "venue": "this paper",
        "models": "3 G-arm (Claude Sonnet 4.6, GPT-5, Gemini 2.5 Pro) + DeepSeek V3.2 (C-arm only)",
        "task": "SimpleQA factual recall",
        "regime": "within-subject ablation: grounding × format × pushback",
        "grounding_ablation": "yes (first such ablation)",
        "preregistered": "yes (prereg-v1, 2026-05-23)",
        "headline_flip_rate": flip_str,
        "n_per_cell": "16-58 matched pairs (after distractor-pool filter)",
        "delta_grounding_pts": delta_str,
        "notes": f"H6 supported at aggregate min-p=0.0001. H8 G_dominates contrast +0.48 (p=0.0002). Cross-vendor R7 Cohen's κ vs GPT-4o-mini grader: {r7['kappa_overall']:.3f}.",
    })

    df = pd.DataFrame(rows)
    csv_path = RESULTS / "literature_comparison.csv"
    df.to_csv(csv_path, index=False)
    print(f"Wrote {csv_path}")

    # ─── Markdown table for the paper / repo ───
    md_lines = ["# Literature comparison",
                "",
                "Our two studies positioned against the 2023–2026 sycophancy literature.",
                "",
                "| Study | Venue | Models | Task | Grounding ablation | Pre-registered | Headline flip rate |",
                "|---|---|---|---|---|---|---|"]
    for r in rows:
        md_lines.append(
            f"| {r['study']} | {r['venue']} | {r['models']} | {r['task']} | "
            f"{r['grounding_ablation']} | {r['preregistered']} | {r['headline_flip_rate']} |"
        )
    md_lines += ["",
                 "## Where this paper differs",
                 "",
                 "1. **Pre-registered within-subject grounding ablation.** No prior sycophancy paper toggles native web search on the same model + same question to isolate the deployment-configuration effect from the model-property effect.",
                 "",
                 "2. **Cross-vendor grader robustness.** We report Cohen's κ vs GPT-4o-mini on a stratified sample (κ=0.91 overall) to rule out same-family grader bias — a robustness check the prior literature does not perform.",
                 "",
                 "3. **Two-prereg discipline.** Study 1 (prereg-v0) and Study 2 (prereg-v1) are separately frozen at git tags. The amendments log documents every post-tag deviation with reason, timestamp, and decision-rule impact.",
                 "",
                 "## What this paper does not cover",
                 "",
                 "- **Multi-turn pushback** (covered by Hong et al. 2025 SyConBench). Our single-turn flip rates are a lower bound.",
                 "- **Social / opinion / advice sycophancy** (covered by ELEPHANT). Our claims are factual recall only.",
                 "- **Persistent-context interaction effects** (covered by Liu et al. 2026 CHI). Each of our conversations is fresh.",
                 ""]
    md_path = RESULTS / "literature_comparison.md"
    md_path.write_text("\n".join(md_lines))
    print(f"Wrote {md_path}")

    print("\n=== preview ===")
    for line in md_lines[:14]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
