# Phase 0 — citation verification audit

Date: 2026-05-21. Conducted via independent research agent that fetched each arXiv page.

## Citation corrections applied to SCOPING.md

1. **Wei et al. 2023 (arXiv:2308.03958).** Their intervention is evaluated on Perez 2022 sycophancy eval and on their own NLP/addition probes, NOT on the Sharma 2023 benchmark. SCOPING corrected.
2. **Williams et al. 2024 (arXiv:2411.02306).** Author list corrected to Williams, Carroll, Narang, Weisser, Murphy, Dragan. Previous "Hu, Wang" attribution was wrong. Venue is ICLR 2025.
3. **Sharma et al. 2023 (arXiv:2310.13548).** Released at ICLR 2024 (not just arXiv); revised May 2025. The sycophancy-eval dataset is in a separate `github.com/meg-tong/sycophancy-eval` repo with no LICENSE file, so direct JSONL re-use is not legally clean. We re-derive prompt templates from the paper rather than copy verbatim.

## Direct prior work identified (not previously in scope)

Two 2025 papers directly compare sycophancy across multiple providers and must be cited as the closest prior work:

- **SycEval** (Fanous, Goldberg, Agarwal, Lin, Zhou, Daneshjou, Koyejo; arXiv:2502.08177, AIES 2025). Same general design on GPT-4o, Claude-3.5-Sonnet, Gemini-1.5-Pro. Our contribution over SycEval: 2026 frontier panel; politeness/assertiveness modulation axis; cross-paper join with calibration ECE.
- **ELEPHANT** (Cheng, Yu, Lee, Khadpe, Ibrahim, Jurafsky; arXiv:2505.13995, May 2025). 11 models, "social sycophancy" framing — emotional validation, moral endorsement, indirect language. Different from our factual-correction framing; complementary.

## Mechanistic prior work identified

- **Papadatos & Freedman 2024** (arXiv:2412.00967, NeurIPS 2024 SoLaR). "Linear Probe Penalties Reduce LLM Sycophancy." Cleanest published representational link between sycophancy and a model-internal signal. Cite when discussing calibration ↔ sycophancy.

## Hong et al. 2024 — does not exist as cited

The paper I originally referenced as "Hong et al. 2024, Measuring and Reducing LLM Hallucination Without Gold-standard Answers" does not exist under that author attribution. The actual paper is **Wei, Yao, Ton, Guo, Estornell, Liu 2024** ("FEWL", arXiv:2402.10412); Hongyi Guo is the third author. The paper provides an LLM-proxy factuality metric usable when no gold answer exists — applicable to our grading pipeline if we want to score pushback responses without re-annotation. Added under `wei2024fewl` in `refs.bib`.

## OpenAI GPT-4o sycophancy rollback (2025)

Confirmed two postmortem URLs:

- Apr 29, 2025: `https://openai.com/index/sycophancy-in-gpt-4o/`
- May 2, 2025: `https://openai.com/index/expanding-on-sycophancy/`

The May 2 post contains the substantive detail (no sycophancy deploy-gate eval existed, expert "vibes" were dismissed in favor of A/B-test signals that the training loop optimised against). Both added under `openai2025syco_rollback` and `openai2025syco_postmortem` in `refs.bib`.

## sycophancy-eval GitHub repo

URL confirmed: `https://github.com/meg-tong/sycophancy-eval`. Default branch `main`, last `pushed_at` 2023-10-25. Contents: `answer`, `are_you_sure`, `feedback`, `mimicry` JSONL datasets plus `utils.py` and an example notebook.

**License: none in the repo.** Default copyright applies; verbatim JSONL reuse is not legally clean. Two options:

1. Email Meg Tong / Sharma for written permission to redistribute / re-use prompts.
2. **(Our choice for now.)** Re-derive the prompt templates from the descriptions in Sharma et al. (2023) §2-3 and write our own JSONL with our own questions. Templates are conceptually simple ("Are You Sure?" plus a wrong alternative); re-derivation is straightforward.

## Anthropic 2025 sycophancy follow-up — gap identified

No dedicated Anthropic sycophancy-mitigation paper found between Sharma 2023 and today. The closest is Anthropic's Constitutional Classifiers / cheap-monitors work (`alignment.anthropic.com/2025/cheap-monitors/`) which is not specifically a sycophancy intervention. Open niche.

## Bibliography state

`paper/refs.bib` committed with 17 verified entries: 7 sycophancy-direct (Sharma 2023, Perez 2022, Wei 2023, Denison 2024, Williams+Carroll 2025, Papadatos+Freedman 2024, SycEval, ELEPHANT), 2 OpenAI 2025 rollback posts, 5 calibration / verbalized-confidence foundations (Tian, Xiong, Mielke, Guo, Kadavath), 1 grading support (Wei FEWL 2024), 1 dataset (SimpleQA), 1 companion (our calibration paper).

## Implications for study design

- **Novelty positioning is narrower than originally written.** SycEval already covers three frontier models with a similar protocol. Our contribution becomes: (a) extension to the 2026 frontier panel including open-weights models, (b) the polite/assertive modulation axis, (c) the cross-paper calibration–sycophancy join. Without these three pieces, the study would be redundant.
- **The cross-paper H5 (calibration ECE × sycophancy flip rate) is the most novel contribution** — Papadatos & Freedman is the only published paper that linked sycophancy to an internal-state signal, and no paper links it to a behavioural calibration measure across frontier providers. This should be the headline rather than the cross-laboratory ordering.
- **Re-derivation of Sharma 2023 templates is on the critical path** for the E1 acceptance probe. The re-derived templates need to be committed before any acceptance-probe inference runs.
