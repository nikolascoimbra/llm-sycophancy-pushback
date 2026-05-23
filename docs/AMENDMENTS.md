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

## A3 — Extended-panel descriptive addition (post-tag, 2026-05-21)

**Original (PRE_REGISTRATION.md §2.1):** Four-provider panel (Claude Opus 4.5, GPT-5, Llama 4 Maverick, DeepSeek V3.2).

**Amended to:** The pre-registered four-provider panel is unchanged for H1–H5 confirmatory analyses. Five additional providers are added as a descriptive exploratory extension only:

| Added model | API | Why |
|---|---|---|
| GPT-4o (`gpt-4o`) | OpenAI direct | Central to the April–May 2025 OpenAI sycophancy rollback episode; any sycophancy paper that doesn't include GPT-4o will be asked about it by reviewers. |
| GPT-5-mini (`gpt-5-mini`) | OpenAI direct | Within-OpenAI capability-scaling comparison. |
| Claude Sonnet 4.6 (`us.anthropic.claude-sonnet-4-6`) | Bedrock | Within-Anthropic comparison vs Opus 4.5; tests whether the Claude calibration / sycophancy advantage is a family trait. |
| Mistral Large 3 (`mistral.mistral-large-3-675b-instruct`) | Bedrock | French lab; new vendor in the panel. |
| Amazon Nova Pro (`us.amazon.nova-pro-v1:0`) | Bedrock | Amazon lab; new vendor in the panel. |

**Reason.** The four-provider panel is sufficient for the pre-registered H1–H5 tests but covers only three labs (Anthropic, OpenAI, Meta, DeepSeek). The descriptive cross-laboratory contribution of the paper is significantly strengthened by including GPT-4o (for direct connection to the 2025 rollback literature) and two additional labs (Mistral, Amazon). The within-vendor comparisons (Sonnet vs Opus; GPT-5-mini vs GPT-5) probe whether the per-provider sycophancy rate is a model-family property or a model-size property.

**Decision-rule impact.** H1–H5 confirmatory tests are unchanged and still defined on the original four providers; the new providers do not participate in those tests. H5 cross-paper Spearman remains at n = 4 because the calibration paper did not measure these five additional models.

A new exploratory section (E4) will report per-provider flip rates for the extended nine-provider panel descriptively, with the explicit caveat that the new providers were added post-tag and do not enter the confirmatory family.

**Budget.** Estimated additional cost ~$5; total study budget remains under the $20 ceiling.

**Eligibility for new providers.** The same eligibility rule (correct AND parsed_confidence ≥ 0.30) is applied to each new provider after running calibration-style initial-turn verbalized inference on the same 500 SimpleQA questions. Per-provider eligible counts will be reported transparently in the paper; providers with fewer than 40 eligible questions are dropped from the descriptive panel.

## A4 — OpenAI API quota exhaustion mid-inference (2026-05-21)

**Original (SCOPING.md / A3):** Five additional providers (GPT-4o, GPT-5-mini, Claude Sonnet 4.6, Mistral Large 3, Amazon Nova Pro) for descriptive E4 panel.

**Amended to:** Four additional providers. GPT-5-mini is dropped from all analyses due to complete OpenAI API quota exhaustion (HTTP 429 on every call; 0 valid pushback responses out of 104 attempted). GPT-4o is retained with partial data: 338 valid pushback responses out of 472 attempted, with 134 quota-failure error placeholders excluded from analysis.

**Reason.** OpenAI's tier-1 quota was exhausted before either model completed inference. Re-funding and waiting for tier recovery was outside the project timeline and budget. The GPT-4o partial run captures 85 of 118 eligible questions per template (n_TW = 85), which is above the descriptive-panel cutoff of 40.

**Decision-rule impact.** None on H1–H5 (these use only the original four providers). GPT-5-mini removed from E4. GPT-4o retained in E4 with explicit "partial sample" caveat.

## A6 — Pre-registration v1 supplement, factorial extension (2026-05-23)

**Original (PRE_REGISTRATION.md, all sections):** Four-provider bare-API panel under verbalized-confidence prompts and four pushback templates. Hypotheses H1–H5 confirmatory.

**Amended to:** `prereg-v0` is unchanged and frozen. A supplementary pre-registration `prereg/PRE_REGISTRATION_v1.md` introduces a new confirmatory hypothesis family (H6, H7, H8) over a **factorial design**: G (grounding: tools-off / native-web-search-on) × C (format: verbalized-confidence / free-form) × P (pushback: TW / PR-control). The new family is corrected separately with Holm-Bonferroni at family-wise α = 0.05.

**Providers (v1 factorial):**

| Provider | Direct-API ID | Native web search | In H6/H8 (G) | In H7 (C) |
|---|---|---|---|---|
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | yes | ✓ | ✓ |
| GPT-5 (Responses API) | `gpt-5` | yes | ✓ | ✓ |
| Gemini 2.5 Pro | `gemini-2.5-pro` | yes | ✓ | ✓ |
| DeepSeek V3.2 | `deepseek-v3-2` | no | — | ✓ |

The v0 four-provider bare-API panel (via Bedrock and direct OpenAI Chat Completions) remains the **Study 1** dataset for descriptive cross-laboratory reporting. **Study 2** is the new factorial with direct-API snapshots and is within-subject per provider.

**Reason.** After v0 results were computed, the author ran an independent replication of the headline Donaldson / Fields Medal example on the consumer-facing `claude.ai` product. Claude with web-search enabled cited Britannica and MacTutor and held its correct answer when contradicted by the user — the opposite of the 90% flip rate reported by `prereg-v0` for Claude Opus 4.5. Three plausible explanations (snapshot, grounding, prompt format) all confound in the consumer-vs-experiment comparison. `prereg-v1` isolates G and C as testable factors and holds snapshot constant by re-running all v1 conditions on the same direct-API snapshot per provider.

The contribution is novel against 2025–2026 sycophancy literature: SycEval, SyConBench, ELEPHANT, BrokenMath, CHI 2026 Interaction-Context, AAAI 2026 internal-origins, and "Challenging the Evaluator" do not perform a within-subject black-box ablation of native tool access on a shared question set under matched user-correction pressure.

**Decision-rule impact on v0.** None. H1–H5 are unchanged and remain frozen. The v0 Study 1 results stand and are reported in the paper with their existing framing (a cross-laboratory measurement under bare-API conditions).

**Anthropic model choice — Sonnet 4.6 not Opus 4.7.** Smoke testing confirmed that Opus 4.7 tools-on calls cost ~$0.05 each (3000+ tokens of tool-spec input × $15/M), which extrapolates to ~$30 for the Anthropic v1 arm alone — over the $25 v1 cap. Sonnet 4.6 input is 5× cheaper ($3/M vs $15/M) and is the model `claude.ai` serves to free-tier users by default, which makes it the more deployment-relevant choice for a study of consumer-vs-API sycophancy. Anthropic prompt caching on the tool spec further reduces per-call cost on repeat invocations. The v0 Bedrock Sonnet 4.6 data (109 graded TW rows in the v0 descriptive panel) is **not** the same snapshot as direct-API Sonnet 4.6 and is not reused for v1 confirmatory cells; v1 is fully within-subject on its own direct-API snapshot.

**Per-provider sample cap N=80.** Sonnet 4.6 tools-on calls that fire a web search cost ~$0.066 each. To fit the budget, each v1 confirmatory cell is capped at the first 80 eligible questions per provider (sorted by `question_id`, deterministic; symmetric across cells). The cap is set before inference. Providers with fewer than 80 eligible use all available.

**Budget.** New cap +$25 (cumulative study budget $40, was $20). Abort at $22 v1 cumulative spend.

**Cleanliness of the v1 pre-registration.** v1 differs from v0 in that **every confirmatory analysis script** for H6/H7/H8 will be committed and tagged BEFORE any v1 inference data is observed. The inference scripts (`04_turn1_directapi.py`, `05_pushback_with_tools.py`, `06_pushback_freeform.py`) are also committed at the v1 tag. The author additionally discloses (in `prereg-v1` §9.6) that the v1 design was motivated by the post-v0 replication; the pre-registration commitment is over the **statistical tests on the new conditions**, not over the existence of those conditions prior to any observation.

## A5 — R2 secondary grader substituted from GPT-4o-mini to Claude Sonnet 4.6 (2026-05-21)

**Original (PRE_REGISTRATION.md §3.3):** R2 cross-validation grades a stratified random sample of n=100 pushback responses with a secondary grader (GPT-4o-mini) and reports Cohen's κ vs the primary Claude Haiku 4.5 grader.

**Amended to:** Same protocol, but the secondary grader is Claude Sonnet 4.6 (via Bedrock) rather than GPT-4o-mini. Achieved n=96 (4 short of target due to grouping arithmetic on the 8 providers).

**Reason.** OpenAI quota exhaustion (see A4) prevented running GPT-4o-mini. Sonnet 4.6 is a different model family from Haiku 4.5 (sibling within Claude 4 family but trained with separate optimization, different post-training, and different parameter count), so it provides meaningful cross-model agreement evidence even if not cross-vendor. This is documented as a limitation in the paper's robustness section.

**Decision-rule impact.** None on confirmatory tests. R2 is robustness-only; the threshold for "concerning grader disagreement" was κ < 0.70 (achieved κ = 0.978).

