from sycophancy.metrics import (
    contingency_table,
    flip_rate,
    paired_template_difference,
    persistence_rate,
    refusal_rate,
)
from sycophancy.stats import (
    bootstrap_ci,
    bootstrap_p_value,
    holm_bonferroni,
    paired_bootstrap_ci,
    permutation_omnibus_variance,
)

__all__ = [
    "bootstrap_ci",
    "bootstrap_p_value",
    "contingency_table",
    "flip_rate",
    "holm_bonferroni",
    "paired_bootstrap_ci",
    "paired_template_difference",
    "permutation_omnibus_variance",
    "persistence_rate",
    "refusal_rate",
]
__version__ = "0.1.0"
