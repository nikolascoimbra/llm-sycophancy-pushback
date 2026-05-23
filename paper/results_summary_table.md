| Hypothesis | Estimate | 95% CI | Aggregate p | Decision |
|---|---|---|---|---|
| H1 cross-provider variance | omnibus | per-provider TW: anthro=0.90, openai=0.65, deepse=0.96, llama4=0.95 | 0.0001 | supported |
| H2 TW vs PR | min over providers | anthro=+0.857; openai=+0.568; deepse=+0.562; llama4=+0.937 | 0.0001 | supported |
| H3 PW vs TW | min over providers | anthro=-0.400; openai=-0.429; deepse=-0.180; llama4=-0.165 | 1.0000 | refuted |
| H4 AW vs TW | min over providers | anthro=-0.486; openai=-0.457; deepse=-0.056; llama4=-0.127 | 0.9569 | refuted |
| H5 calibration ↔ sycophancy (n=4) | ρ = 0.800 | (-1.000, 1.000) | — | descriptive (n=4, no directional commitment) |

**Holm-Bonferroni at family-wise α = 0.05 across confirmatory hypotheses:**

| Hypothesis | p | Reject H₀? |
|---|---|---|
| H1 | 0.0001 | yes |
| H2 | 0.0001 | yes |
| H3 | 1.0000 | no |
| H4 | 0.9569 | no |
