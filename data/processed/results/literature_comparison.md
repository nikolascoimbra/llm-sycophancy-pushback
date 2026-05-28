# Literature comparison

Our two studies positioned against the 2023–2026 sycophancy literature.

| Study | Venue | Models | Task | Grounding ablation | Pre-registered | Headline flip rate |
|---|---|---|---|---|---|---|
| Sharma et al. 2023 (Anthropic) | ICLR 2024 | 5 Anthropic/OpenAI/Meta | Are-You-Sure factual + free-form | no | no | ~40-90% (varies by task and model) |
| Fanous et al. 2025 (SycEval) | AAAI / AIES 2025 | 3 (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro) | AMPS (math) + MedQuad (medical) | no | no | 58.2% overall (43.5% progressive, 14.7% regressive) |
| Cheng et al. 2025 (ELEPHANT) | arXiv 2505.13995 | 11 frontier | Social sycophancy (emotional validation, moral, indirect) | no | no | see paper, varies by task |
| Hong et al. 2025 (SyConBench) | EMNLP Findings 2025 | 17 LLMs | Multi-turn factual + multiple-choice | no | no | GPT-4o 4.4%, GPT-4.1-nano 18.8% flip-to-suggestion |
| Liu et al. 2026 (Interaction Context) | CHI 2026 | GPT-4.1 mini | Persistent-context chat with humans | no | no | see paper, by interaction type |
| This study, Study 1 (prereg-v0) | this paper | 8 frontier (Claude Opus 4.5, GPT-5, DeepSeek V3.2, Llama 4 Maverick, GPT-4o, Claude Sonnet 4.6, Mistral Large 3, Amazon Nova Pro) | SimpleQA factual recall | no | yes (prereg-v0, 2026-05-21) | 65–96% terse-wrong (7/8 ≥90%); GPT-5 alone at 65% |
| This study, Study 2 (prereg-v1) | this paper | 3 G-arm (Claude Sonnet 4.6, GPT-5, Gemini 2.5 Pro) + DeepSeek V3.2 (C-arm only) | SimpleQA factual recall | yes (first such ablation) | yes (prereg-v1, 2026-05-23) | anthropic_sonnet_46: 95%→28%; openai_gpt5: 67%→60%; google_gemini: 100%→19% |

## Where this paper differs

1. **Pre-registered within-subject grounding ablation.** No prior sycophancy paper toggles native web search on the same model + same question to isolate the deployment-configuration effect from the model-property effect.

2. **Cross-vendor grader robustness.** We report Cohen's κ vs GPT-4o-mini on a stratified sample (κ=0.91 overall) to rule out same-family grader bias — a robustness check the prior literature does not perform.

3. **Two-prereg discipline.** Study 1 (prereg-v0) and Study 2 (prereg-v1) are separately frozen at git tags. The amendments log documents every post-tag deviation with reason, timestamp, and decision-rule impact.

## What this paper does not cover

- **Multi-turn pushback** (covered by Hong et al. 2025 SyConBench). Our single-turn flip rates are a lower bound.
- **Social / opinion / advice sycophancy** (covered by ELEPHANT). Our claims are factual recall only.
- **Persistent-context interaction effects** (covered by Liu et al. 2026 CHI). Each of our conversations is fresh.
