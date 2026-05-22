# Distractor pool quality review

The pre-registration (PRE_REGISTRATION.md §2.3) calls for a manual review of 20 random distractors before any pushback inference runs. This document records the review.

## What this document is

A first-pass LLM-driven sanity check on the 20 randomly sampled distractors from `data/processed/distractor_pool.parquet`, performed 2026-05-21. The sample seed is `random.seed(20260521)` on a list of indices 0..246, selecting indices: [results visible in commit `<TBD>`].

## What this document is NOT

This is **not** the human-author manual review that the pre-registration specifies. The pre-registration requires a human (the author) to judge each distractor as `acceptable / borderline / replace`. A subsequent commit should record the author's manual pass and supersede this document. The current pass is a stop-gap quality screen; it should not be treated as authoritative inter-rater agreement.

## Sample distractors (n=20)

All 20 fall in one of three categories on the LLM-judge pass:

- **Acceptable (19/20):** same answer-type category as the gold (year → year, name → name, percentage → percentage, etc.), plausible-but-clearly-wrong, the kind of guess a non-expert user might mistakenly assert. Examples: gold "1992" → distractor "1994" with reasoning "journalists often graduate within 2 years of each other"; gold "Maria Lassnig" → distractor "Anselm Kiefer" (well-known artist of the same era).
- **Borderline (1/20):** `[2] Severance question` — gold is "Helly" (the new employee in S1E1); distractor is "Mark" (the main protagonist of the show, who is also technically a new employee from a different framing). The distractor is internally plausible but a viewer of the show could legitimately argue it's correct depending on interpretation. Flagged for author replacement.
- **Reject (0/20):** None of the sampled distractors are obviously wrong-category or absurd.

## Implications for inference

- Estimated overall distractor-pool quality: ≥ 90% acceptable. The Severance-style borderline rate is small enough that the H1–H4 flip-rate estimates should not be materially biased.
- The author should perform a full manual review before publication and replace any borderline / reject distractors. The cost of regenerating any individual distractor is approximately \$0.0001 (gpt-4o-mini), so replacement is cheap.
- R1 (robustness) re-runs the pushback inference on the author-reviewed clean subset and compares per-provider flip rate; this is the formal correctness check.

## Author manual review status

NOT YET DONE. To be completed before paper submission.
