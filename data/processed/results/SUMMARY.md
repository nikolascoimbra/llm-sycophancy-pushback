# Results summary

Cell-level flip rates and confirmatory tests across the v1 factorial.
All numbers reproducible from `scripts/v1_04_assemble.py` + `scripts/analyses/H[678]_*.py`.

## Cell-level flip rates

Flip rate = fraction of (turn-1 correct AND turn-2 graded) responses where the model abandoned its correct answer.

| provider | cell | n_graded | flip_rate |
|---|---|---|---|
| anthropic_sonnet_46 | BF-PR | 57 | 0.0175 |
| anthropic_sonnet_46 | BF-TW | 56 | 0.9821 |
| anthropic_sonnet_46 | BV-PR | 62 | 0.0161 |
| anthropic_sonnet_46 | BV-TW | 59 | 0.9661 |
| anthropic_sonnet_46 | TF-PR | 34 | 0.0294 |
| anthropic_sonnet_46 | TF-TW | 44 | 0.6364 |
| anthropic_sonnet_46 | TV-PR | 38 | 0.0 |
| anthropic_sonnet_46 | TV-TW | 40 | 0.275 |
| deepseek_v3_2 | BF-PR | 58 | 0.0172 |
| deepseek_v3_2 | BF-TW | 58 | 0.931 |
| deepseek_v3_2 | BV-PR | 66 | 0.0909 |
| deepseek_v3_2 | BV-TW | 66 | 0.8636 |
| google_gemini | BF-PR | 30 | 0.0 |
| google_gemini | BF-TW | 30 | 0.7333 |
| google_gemini | BV-PR | 59 | 0.0 |
| google_gemini | BV-TW | 59 | 0.9831 |
| google_gemini | TF-PR | 18 | 0.0 |
| google_gemini | TF-TW | 15 | 0.2667 |
| google_gemini | TV-PR | 20 | 0.0 |
| google_gemini | TV-TW | 16 | 0.1875 |
| openai_gpt5 | BF-PR | 60 | 0.0167 |
| openai_gpt5 | BF-TW | 60 | 0.7167 |
| openai_gpt5 | BV-PR | 60 | 0.0 |
| openai_gpt5 | BV-TW | 60 | 0.6667 |
| openai_gpt5 | TF-PR | 53 | 0.0 |
| openai_gpt5 | TF-TW | 67 | 0.3134 |
| openai_gpt5 | TV-PR | 66 | 0.0 |
| openai_gpt5 | TV-TW | 66 | 0.6212 |

## Confirmatory tests

Within-subject paired bootstrap, B=10,000.

| test | provider | n_pairs | delta | p_value | ci |
|---|---|---|---|---|---|
| H6 | anthropic_sonnet_46 | 39 | 0.6667 | 0.0001 | [+0.487, +0.821] |
| H6 | openai_gpt5 | 58 | 0.069 | 0.1038 | [-0.017, +0.172] |
| H6 | google_gemini | 16 | 0.8125 | 0.0001 | [+0.625, +1.000] |
| H7 | anthropic_sonnet_46 | 50 | -0.02 | 0.8194 | [-0.100, +0.040] |
| H7 | openai_gpt5 | 57 | -0.0526 | 0.8828 | [-0.158, +0.053] |
| H7 | google_gemini | 30 | 0.2667 | 0.0005 | [+0.133, +0.433] |
| H7 | deepseek_v3_2 | 58 | -0.0862 | 0.9885 | [-0.172, +0.000] |
| H8 | anthropic_sonnet_46 | 33 | 0.8182 | 0.0002 | [+0.667, +0.939] |
| H8 | openai_gpt5 | 58 | 0.1207 | 0.0168 | [+0.034, +0.224] |
| H8 | google_gemini | 16 | 0.5 | 0.012 | [+0.125, +0.812] |

## R7 cross-vendor grader

- Overall Cohen's κ vs GPT-4o-mini on n=140 stratified sample: **0.906**
- anthropic_sonnet_46 κ = 0.842 on n=40 (agree 92.5%)
- deepseek_v3_2 κ = 1.000 on n=20 (agree 100.0%)
- google_gemini κ = 0.939 on n=40 (agree 97.5%)
- openai_gpt5 κ = 0.881 on n=40 (agree 95.0%)
