# sycophancy-study

Cross-laboratory measurement of LLM sycophancy under user-correction pressure.

Two pre-registered studies on the same SimpleQA question set:

- **Study 1 (prereg-v0)** — eight-provider bare-API panel under verbalized-confidence prompts and four pushback templates. Confirmatory hypotheses H1–H5.
- **Study 2 (prereg-v1)** — within-subject factorial of grounding × confidence-format × pushback on Claude Sonnet 4.6, GPT-5, Gemini 2.5 Pro, and DeepSeek V3.2 (DeepSeek has no native search, so it joins the format arm only). Confirmatory hypotheses H6–H8.

Both pre-registrations, the amendments log, the analysis scripts, the inference cache, and the grader cache are all in this repository. Paper LaTeX source and PDF are **not** in the repo (built locally; the repo is the reproducibility artifact, the paper is the output).

## Headline result (Study 2)

Native web search collapses sycophancy on factual recall, in every provider tested. Same model, same questions, same pushback. The only change is whether the API call has the provider's built-in web-search tool enabled.

| Provider | Bare API + verbalized | + Web search | Cell flip-rate change |
|---|---:|---:|---:|
| Claude Sonnet 4.6 | 84% (n=68) | 43% (n=7\*) | −41 pts |
| GPT-5 | 93% (n=70) | 62% (n=66) | −31 pts |
| Gemini 2.5 Pro | 98% (n=59) | 19% (n=32) | −79 pts |

Within-subject H6 paired test: every per-provider contrast clears Holm at p < 10⁻². H8 contrast (grounding > format) supported at p = 0.0004.

\* Anthropic Sonnet 4.6 tools-on cell terminated at n=7 due to the Anthropic Console 50-RPM rate limit; the within-subject paired test on those 7 still clears the pre-registered significance threshold (p = 0.003). Documented in [docs/AMENDMENTS.md](docs/AMENDMENTS.md) §A10.

## Status

| Phase | Description | Status |
|---|---|---|
| 0 | Citation verification + design review | done |
| 1 | Project skeleton + metrics library | done |
| 2 | Eligible-question filter + distractor pool | done (Study 1); reused for Study 2 |
| 3 | Pre-registration `prereg-v0` (Study 1) | tagged 2026-05-21 |
| 4 | Study 1 inference + grading | done (8 providers, 3,276 graded rows) |
| 5 | Study 1 H1–H5 confirmatory analyses | done; results in `data/processed/results/H[1-5].json` |
| 6 | Pre-registration `prereg-v1` (Study 2) | tagged 2026-05-23 |
| 7 | Study 2 inference + grading | done (4 providers × 8 cells, 1,425 graded rows; Anthropic TV/TF partial — see A10) |
| 8 | Study 2 H6–H8 confirmatory analyses | done; results in `data/processed/results/H[6-8].json` |
| 9 | Figures (F0–F6, LI_v3) | done; in `figures/` (git-ignored) |
| 10 | Paper draft | done; built locally to `paper/main.pdf` (git-ignored) |

## Pre-registration tags

- `prereg-v0` — Study 1 confirmatory family (H1–H5). Frozen 2026-05-21. See [prereg/PRE_REGISTRATION.md](prereg/PRE_REGISTRATION.md).
- `prereg-v1` — Study 2 confirmatory family (H6–H8). Frozen 2026-05-23. See [prereg/PRE_REGISTRATION_v1.md](prereg/PRE_REGISTRATION_v1.md).

All post-tag amendments (A1–A10 so far) are documented with timestamps, reasons, and decision-rule impact in [docs/AMENDMENTS.md](docs/AMENDMENTS.md).

## Reproducing

```bash
# Install deps (Python 3.11, uv)
make sync

# Set API keys (Anthropic direct, OpenAI, Google, DeepSeek)
cp .env.example .env  # then fill in keys

# Study 1 (uses Bedrock for most providers; ~$12 inference)
make eligible distractors infer grade
make confirmatory   # H1–H5 (refuses to run before prereg-v0 tag exists)

# Study 2 (uses direct first-party APIs; ~$14 inference)
make v1-inference v1-grade
make v1-confirmatory  # H6–H8 (refuses to run before prereg-v1 tag exists)
make v1-figures
```

## Companion repo

This study reuses the cached SimpleQA initial-turn responses and per-provider calibration ECE from `../calibration-deployment-risk/` (the companion paper). The eligibility filter for Study 1 restricts to questions on which each provider was confident (≥ 0.30) AND correct in the calibration run. Study 2's eligibility filter is recomputed from a fresh direct-API canonical turn-1 elicitation (different snapshot from Bedrock; see prereg-v1 §3.3).

## License

Code: MIT.
