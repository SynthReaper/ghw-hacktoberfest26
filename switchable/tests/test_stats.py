import numpy as np
import pytest

from openswitch.stats import (
    are_cis_overlapping,
    bootstrap_ci,
    calculate_judge_stats,
    calculate_metric_ci,
    calculate_percentiles,
    check_length_bias,
    paired_difference_ci,
)


def test_bootstrap_ci_determinism():
    data = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0]
    p1, low1, up1 = bootstrap_ci(data, seed=42, n_resamples=1000)
    p2, low2, up2 = bootstrap_ci(data, seed=42, n_resamples=1000)

    assert p1 == p2
    assert low1 == low2
    assert up1 == up2


def test_bootstrap_ci_coverage_normal_distribution():
    # Known distribution: N(10.0, 1.0)
    rng = np.random.default_rng(12345)
    sample = rng.normal(loc=10.0, scale=1.0, size=500)

    point, lower, upper = bootstrap_ci(sample, ci_level=0.95, n_resamples=5000, seed=999)

    assert lower < 10.0 < upper
    assert lower <= point <= upper
    assert pytest.approx(point, abs=0.15) == 10.0


def test_bootstrap_ci_bernoulli_distribution():
    # 80% ones, 20% zeros
    data = [1] * 80 + [0] * 20
    point, lower, upper = bootstrap_ci(data, ci_level=0.95, n_resamples=5000, seed=42)

    assert point == 0.8
    assert lower < 0.8 < upper
    assert 0.70 <= lower <= 0.75
    assert 0.85 <= upper <= 0.90


def test_bootstrap_ci_edge_cases():
    # Empty
    assert bootstrap_ci([]) == (0.0, 0.0, 0.0)

    # Single sample
    assert bootstrap_ci([42.0]) == (42.0, 42.0, 42.0)

    # All identical
    assert bootstrap_ci([1.0, 1.0, 1.0, 1.0]) == (1.0, 1.0, 1.0)


def test_paired_difference_ci():
    model_a = [1.0, 1.0, 1.0, 1.0, 0.0]
    model_b = [0.0, 1.0, 0.0, 1.0, 0.0]

    # Differences: [1.0, 0.0, 1.0, 0.0, 0.0] -> mean diff = +0.4
    point, lower, upper = paired_difference_ci(model_a, model_b, seed=42)
    assert point == 0.4
    assert lower <= 0.4 <= upper


def test_calculate_judge_stats():
    # 10 wins, 5 ties, 5 losses (20 valid) + 2 inconsistent + 1 invalid (23 total)
    verdicts = ["win"] * 10 + ["tie"] * 5 + ["loss"] * 5 + ["inconsistent"] * 2 + ["invalid"] * 1

    stats = calculate_judge_stats(verdicts, seed=42)

    # Parity = (10 + 5) / 20 = 0.75
    assert stats["parity_rate"].point_estimate == 0.75
    assert stats["parity_rate"].n_samples == 20
    assert stats["parity_rate"].ci_lower < 0.75 < stats["parity_rate"].ci_upper

    # Win rate = 10 / 20 = 0.50
    assert stats["win_rate"].point_estimate == 0.50
    assert stats["win_rate"].n_samples == 20

    # Inconsistent = 2 / 23
    assert pytest.approx(stats["inconsistent_rate"].point_estimate, abs=0.01) == 2 / 23

    # Invalid = 1 / 23
    assert pytest.approx(stats["invalid_rate"].point_estimate, abs=0.01) == 1 / 23


def test_calculate_metric_ci():
    scores = [1, 1, 1, 0, 1]
    metric = calculate_metric_ci(scores, metric_name="schema_valid_rate", seed=42)
    assert metric.metric_name == "schema_valid_rate"
    assert metric.point_estimate == 0.8
    assert metric.n_samples == 5
    assert metric.ci_lower <= 0.8 <= metric.ci_upper


def test_calculate_percentiles():
    data = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    pcts = calculate_percentiles(data, pcts=(50, 95))
    assert pcts["p50"] == 55.0
    assert pcts["p95"] == 95.5

    assert calculate_percentiles([]) == {"p50": 0.0, "p95": 0.0}


def test_check_length_bias():
    # Strong correlation: length perfectly predicts positive score
    lengths = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    bias = check_length_bias(lengths, scores, threshold=0.5)
    assert bias.flagged
    assert bias.spearman_rho == 1.0
    assert bias.warning is not None
    assert "Length bias warning" in bias.warning

    # Uncorrelated / random
    scores_uncorr = [0.5, 0.1, 0.9, 0.2, 0.8, 0.3, 0.7, 0.4, 0.6, 0.5]
    bias_low = check_length_bias(lengths, scores_uncorr, threshold=0.5)
    assert not bias_low.flagged


def test_are_cis_overlapping():
    # Overlapping: [0.70, 0.85] and [0.80, 0.95]
    assert are_cis_overlapping((0.70, 0.85), (0.80, 0.95))

    # Disjoint: [0.60, 0.75] and [0.80, 0.90]
    assert not are_cis_overlapping((0.60, 0.75), (0.80, 0.90))

    # Touching boundary: [0.70, 0.80] and [0.80, 0.90]
    assert are_cis_overlapping((0.70, 0.80), (0.80, 0.90))
