# sycophancy-study

Cross-laboratory measurement of LLM sycophancy under user-correction pressure.

## What this is

A pre-registered study measuring how often four 2026 frontier APIs abandon a correct answer when a user pushes back with an incorrect alternative. The primary outcome is the per-provider flip rate from correct to incorrect on a controlled ground-truth question set. The study extends Sharma et al. (2023) "Towards Understanding Sycophancy in Language Models" to the current frontier panel (Claude Opus 4.5, GPT-5, Llama 4 Maverick, DeepSeek V3.2) under a single matched protocol, and tests whether per-provider sycophancy correlates with per-provider calibration measured in our companion study.

See `SCOPING.md` for the full design rationale, literature review, and budget plan.

## Status

| Phase | Description | Status |
|---|---|---|
| 0 | Citation verification + design review | pending |
| 1 | Project skeleton + metrics + pre-registration draft | pending |
| 2 | Eligible-question filter + distractor pool | pending |
| 3 | Pushback inference (≤ $18 hard cap) | pending |
| 4 | Confirmatory analyses H1–H5 | pending (gated on `prereg-v0`) |
| 5 | Exploratory + robustness | pending |
| 6 | Figures | pending |
| 7 | Paper draft | pending |

## Companion repo

This study reuses cached responses from the calibration-deployment-risk study (`../calibration-deployment-risk/data/raw/simpleqa_cache/`). The eligible-question filter restricts to questions on which each provider was confident (≥ 0.5) AND correct in the calibration run, since pushback against an already-wrong or uncertain initial answer is not a clean sycophancy probe.

## License

Code: MIT.
