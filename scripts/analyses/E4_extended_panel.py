"""E4 — Descriptive flip-rate panel for the post-tag 8-provider extended panel.

The four confirmatory providers (anthropic_opus, openai_gpt5, deepseek_v3,
llama4_maverick) are the only ones that enter H1-H5. The four post-tag
additions (openai_gpt4o, claude_sonnet_4_6, mistral_large_3, amazon_nova_pro)
are reported here descriptively only — see docs/AMENDMENTS.md A3 and
PRE_REGISTRATION.md.

openai_gpt5_mini was added but is excluded due to OpenAI 429 quota exhaustion
(0 valid pushback responses).

Per provider and per template: bootstrap flip-rate point estimate and 95% CI.
No hypothesis tests; no Holm correction.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from _common import EXTENDED_PROVIDERS, TEMPLATES, load_final, write_results  # noqa: E402

from sycophancy.stats import bootstrap_ci  # noqa: E402

B = 10_000
SEED = 20260521


def main() -> int:
    df = load_final()
    df = df[df["is_final_correct"].notna()].copy()

    per_provider = {}
    for prov in EXTENDED_PROVIDERS:
        gp = df[df["provider"] == prov]
        per_template = {}
        for t in TEMPLATES:
            g = gp[gp["template"] == t]
            n = len(g)
            if n == 0:
                per_template[t] = {"n": 0, "flip_rate": float("nan"),
                                    "ci_lo": float("nan"), "ci_hi": float("nan")}
                continue
            flips = (~g["is_final_correct"].astype(bool)).astype(float).values
            boot = bootstrap_ci(flips, statistic=np.mean, B=B, seed=SEED)
            per_template[t] = {"n": int(n), "flip_rate": boot.point,
                                "ci_lo": boot.lo, "ci_hi": boot.hi}
        per_provider[prov] = {"n_total": int(len(gp)),
                              "per_template": per_template}

    payload = {
        "hypothesis": "E4 (descriptive extended panel; non-confirmatory)",
        "panel": list(EXTENDED_PROVIDERS),
        "per_provider": per_provider,
    }
    out = write_results("E4_extended_panel", payload)

    print("E4 — extended-panel descriptive flip rates (post-tag, non-confirmatory):")
    for prov, v in per_provider.items():
        print(f"  {prov:<22} n_total={v['n_total']:>3}")
        for t in TEMPLATES:
            r = v["per_template"][t]
            print(f"    {t}  n={r['n']:>3}  flip={r['flip_rate']:.3f}  "
                  f"CI=({r['ci_lo']:.3f}, {r['ci_hi']:.3f})")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
