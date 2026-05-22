"""Statistical helpers for the sycophancy study.

Reused from the calibration codebase (same author, same conventions) with one
addition: a permutation omnibus on per-question label arrays for the
cross-provider H1 test.

All public functions take a `seed` parameter so reported numbers are
reproducible. Default B = 10,000 matches the prereg.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

DEFAULT_B = 10_000


@dataclass(frozen=True)
class BootstrapCI:
    point: float
    lo: float
    hi: float
    n: int
    B: int
    samples: np.ndarray | None = None

    def __repr__(self) -> str:
        return (
            f"BootstrapCI(point={self.point:.4f}, lo={self.lo:.4f}, "
            f"hi={self.hi:.4f}, n={self.n}, B={self.B})"
        )


def bootstrap_ci(
    data: Sequence[float] | np.ndarray,
    statistic: Callable[[np.ndarray], float] = np.mean,
    B: int = DEFAULT_B,
    alpha: float = 0.05,
    seed: int = 20260521,
    return_samples: bool = False,
) -> BootstrapCI:
    """Percentile bootstrap CI on a 1-D array."""
    arr = np.asarray(data, dtype=float).ravel()
    if arr.size == 0:
        raise ValueError("empty input")
    rng = np.random.default_rng(seed)
    n = arr.size
    point = float(statistic(arr))
    samples = np.empty(B, dtype=float)
    for b in range(B):
        idx = rng.integers(0, n, n)
        samples[b] = float(statistic(arr[idx]))
    lo, hi = np.quantile(samples, [alpha / 2, 1 - alpha / 2])
    return BootstrapCI(
        point=point, lo=float(lo), hi=float(hi), n=n, B=B,
        samples=samples if return_samples else None,
    )


def paired_bootstrap_ci(
    a: Sequence[float] | np.ndarray,
    b: Sequence[float] | np.ndarray,
    statistic: Callable[[np.ndarray], float] = np.mean,
    B: int = DEFAULT_B,
    alpha: float = 0.05,
    seed: int = 20260521,
    return_samples: bool = False,
) -> BootstrapCI:
    """Percentile bootstrap CI on the paired difference (a - b)."""
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    if a.shape != b.shape or a.size == 0:
        raise ValueError("a and b must be non-empty and same shape")
    diffs = a - b
    return bootstrap_ci(diffs, statistic=statistic, B=B, alpha=alpha,
                         seed=seed, return_samples=return_samples)


def bootstrap_p_value(
    samples: np.ndarray,
    null_value: float = 0.0,
    alternative: str = "two-sided",
) -> float:
    """One- or two-sided bootstrap p-value from a sample distribution.

    +1 small-sample correction so a perfectly-supported test never reports 0.
    """
    s = np.asarray(samples, dtype=float).ravel()
    if s.size == 0:
        return float("nan")
    B = s.size
    if alternative == "greater":
        n_extreme = int(np.sum(s <= null_value))
    elif alternative == "less":
        n_extreme = int(np.sum(s >= null_value))
    elif alternative == "two-sided":
        p_g = (np.sum(s <= null_value) + 1) / (B + 1)
        p_l = (np.sum(s >= null_value) + 1) / (B + 1)
        return float(min(2 * min(p_g, p_l), 1.0))
    else:
        raise ValueError(f"unknown alternative {alternative!r}")
    return float((n_extreme + 1) / (B + 1))


def permutation_omnibus_variance(
    labels: np.ndarray,
    values: np.ndarray,
    B: int = DEFAULT_B,
    seed: int = 20260521,
) -> dict[str, float]:
    """Permutation omnibus for the cross-provider H1 test.

    `labels` are the provider strings (length n). `values` is a per-row 0/1
    indicator (typically the flip indicator for that (provider, question)).
    Returns the observed cross-provider variance of mean(value) per label,
    and the permutation p-value under shuffling provider labels.

    The variance is computed over the per-label means, treated as an unweighted
    sample (so a 4-provider design gives a 4-element variance).
    """
    labels = np.asarray(labels)
    values = np.asarray(values, dtype=float).ravel()
    if labels.size != values.size:
        raise ValueError("labels and values must be the same length")
    unique = np.unique(labels)
    if unique.size < 2:
        return {"observed_variance": float("nan"), "p_value": float("nan"),
                "n_perm": B}

    def _variance(perm_labels):
        means = np.array([values[perm_labels == u].mean() for u in unique])
        return float(np.var(means, ddof=0))

    observed = _variance(labels)
    rng = np.random.default_rng(seed)
    work = labels.copy()
    n_extreme = 0
    for _ in range(B):
        rng.shuffle(work)
        if _variance(work) >= observed - 1e-15:
            n_extreme += 1
    return {
        "observed_variance": observed,
        "p_value": float((n_extreme + 1) / (B + 1)),
        "n_perm": int(B),
    }


def holm_bonferroni(p_values: Sequence[float], alpha: float = 0.05) -> list[bool]:
    """Holm-Bonferroni step-down. Returns a list of booleans aligned with the
    input. True iff that hypothesis is rejected at family-wise alpha."""
    p = list(p_values)
    m = len(p)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p[i])
    reject = [False] * m
    for rank, i in enumerate(order):
        threshold = alpha / (m - rank)
        if p[i] <= threshold:
            reject[i] = True
        else:
            break
    return reject
