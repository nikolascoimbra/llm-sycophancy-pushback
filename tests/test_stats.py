"""Unit tests for src/sycophancy/stats.py."""

from __future__ import annotations

import math

import numpy as np
import pytest

from sycophancy.stats import (
    bootstrap_ci,
    bootstrap_p_value,
    holm_bonferroni,
    paired_bootstrap_ci,
    permutation_omnibus_variance,
)


def test_bootstrap_ci_mean_covers_truth():
    rng = np.random.default_rng(0)
    x = rng.normal(loc=2.5, scale=1.0, size=1000)
    out = bootstrap_ci(x, statistic=np.mean, B=2000, seed=42)
    assert out.lo <= 2.5 <= out.hi
    assert out.point == pytest.approx(x.mean())


def test_bootstrap_ci_constant_input():
    out = bootstrap_ci(np.ones(50), statistic=np.mean, B=200)
    assert out.point == pytest.approx(1.0)
    assert out.lo == pytest.approx(1.0)
    assert out.hi == pytest.approx(1.0)


def test_bootstrap_ci_empty_raises():
    with pytest.raises(ValueError):
        bootstrap_ci(np.array([]))


def test_bootstrap_ci_return_samples():
    out = bootstrap_ci(np.arange(100, dtype=float), B=500, return_samples=True)
    assert out.samples is not None
    assert out.samples.shape == (500,)


def test_paired_bootstrap_ci():
    rng = np.random.default_rng(1)
    a = rng.normal(1.0, 0.3, 200)
    b = rng.normal(0.0, 0.3, 200)
    out = paired_bootstrap_ci(a, b, B=500)
    assert out.point > 0.5
    assert out.lo > 0


def test_bootstrap_p_value_greater_clear_signal():
    samples = np.full(1000, 0.5)
    p = bootstrap_p_value(samples, null_value=0.0, alternative="greater")
    assert p < 0.005


def test_bootstrap_p_value_two_sided():
    rng = np.random.default_rng(2)
    samples = rng.normal(0, 1, 1000)
    p = bootstrap_p_value(samples, null_value=0.0, alternative="two-sided")
    assert 0 < p <= 1.0


def test_holm_bonferroni_orders_correctly():
    rej = holm_bonferroni([0.001, 0.04, 0.30], alpha=0.05)
    assert rej == [True, False, False]


def test_holm_bonferroni_all_significant():
    rej = holm_bonferroni([0.001, 0.005, 0.010], alpha=0.05)
    assert rej == [True, True, True]


def test_holm_bonferroni_empty():
    assert holm_bonferroni([]) == []


def test_permutation_omnibus_no_signal_high_p():
    rng = np.random.default_rng(3)
    n_per = 200
    labels = np.repeat(["A", "B", "C", "D"], n_per)
    values = rng.binomial(1, 0.3, size=4 * n_per).astype(float)  # same rate
    out = permutation_omnibus_variance(labels, values, B=500, seed=0)
    assert out["p_value"] > 0.1


def test_permutation_omnibus_strong_signal_low_p():
    n_per = 200
    labels = np.repeat(["A", "B", "C", "D"], n_per)
    rates = [0.10, 0.30, 0.50, 0.70]
    rng = np.random.default_rng(4)
    values = np.concatenate([
        rng.binomial(1, r, size=n_per).astype(float) for r in rates
    ])
    out = permutation_omnibus_variance(labels, values, B=1000, seed=0)
    assert out["p_value"] < 0.01


def test_permutation_omnibus_single_label_nan():
    labels = np.repeat(["A"], 50)
    values = np.zeros(50)
    out = permutation_omnibus_variance(labels, values, B=200)
    assert math.isnan(out["p_value"])
