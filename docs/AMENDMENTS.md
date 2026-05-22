# Pre-tag amendments to PRE_REGISTRATION.md

This file logs every change to the pre-registration design between SCOPING and the `prereg-v0` Git tag. Amendments after `prereg-v0` is tagged require a separate file and a re-tag.

## A1 — Confidence threshold lowered from 0.50 to 0.30 (2026-05-21)

**Original (SCOPING.md §2.2 / PRE_REGISTRATION.md §2.2):** Eligibility = (CORRECT) AND (parsed_confidence ≥ 0.50).

**Amended to:** Eligibility = (CORRECT) AND (parsed_confidence ≥ 0.30).

**Reason.** The 0.50 threshold was set before observing the calibration study's empirical confidence distributions. Claude Opus 4.5 is systematically under-confident on SimpleQA (mean confidence 0.29, median correct-answer confidence 0.35), which the calibration paper documents as the headline finding. The 0.50 threshold would filter out the modal Claude correct answer and leave only 42 eligible questions for Claude versus 166 for GPT-5, biasing the cross-provider analysis toward over-confident providers.

The 0.30 threshold corresponds to "above one-in-three confidence" — interpretable as "the model has a position to defend, rather than flipping a coin." Per-provider eligible counts under the amended threshold:

| Provider | n_eligible | mean confidence on correct |
|---|---:|---:|
| Claude Opus 4.5 | 105 | 0.386 |
| GPT-5 | 173 | 0.794 |
| DeepSeek V3.2 | 89 | 0.757 |
| Llama 4 Maverick | 79 | 0.719 |

**Decision-rule impact.** None. The H1–H5 tests are defined as flip rates over the eligible set; the threshold change shifts the eligibility set but does not change the procedure on that set.

## A2 — Augmentation deferred for two below-100 providers (2026-05-21)

**Original (SCOPING.md §6 / PRE_REGISTRATION.md §2.2):** If a provider's eligible count falls below 100, augment by drawing fresh SimpleQA questions outside the calibration sample.

**Amended to:** Same rule with a documented exception for DeepSeek V3.2 (n=89) and Llama 4 Maverick (n=79). We proceed without augmentation and report per-provider sample sizes transparently. Reasons:

1. The bootstrap CI width at n=80 vs n=100 for a proportion near 0.5 is approximately ±0.11 vs ±0.10 — a marginal difference for the headline flip-rate estimate.
2. Augmentation would cost approximately $0.50–$1.00 of additional initial-turn inference per provider but introduces a measurement-protocol asymmetry: the augmented eligible questions came from a fresh second inference pass rather than from the original calibration sweep, so they are not exchangeable with the cached questions on response-text or grading provenance.
3. If a reviewer requests augmentation we can add it later; the cost and time are small.

**Decision-rule impact.** None. We report per-provider Holm-corrected results; underpowered providers are flagged in the limitations section.
