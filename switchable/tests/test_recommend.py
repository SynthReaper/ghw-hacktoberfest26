from openswitch.recommend import (
    CandidateSummary,
    generate_recommendation,
)


def test_recommendation_single_eligible():
    c1 = CandidateSummary(
        model_key="digitalocean/gemma-2-9b",
        display_name="Gemma 2 9B (DO)",
        primary_metric_name="parity_rate",
        point_estimate=0.92,
        ci_lower=0.87,
        ci_upper=0.96,
        cost_per_1k=0.24,
        error_rate=0.01,
        is_local=False,
    )
    c2 = CandidateSummary(
        model_key="ollama/gemma2:2b",
        display_name="Gemma 2 2B (Local)",
        primary_metric_name="parity_rate",
        point_estimate=0.82,
        ci_lower=0.75,
        ci_upper=0.88,
        cost_per_1k=0.00,
        error_rate=0.03,
        is_local=True,
    )

    res = generate_recommendation(
        candidates=[c1, c2],
        baseline_cost_per_1k=15.00,
        threshold=0.85,
        test_size=100,
    )

    assert res.decision == "switch_recommended"
    assert res.recommended_candidate is not None
    assert res.recommended_candidate.model_key == "digitalocean/gemma-2-9b"
    assert len(res.eligible_candidates) == 1
    assert len(res.ineligible_candidates) == 1
    assert "Safe switch recommended" in res.headline


def test_recommendation_multiple_eligible_cheapest_wins():
    c_expensive = CandidateSummary(
        model_key="cloud/large-model",
        display_name="Large Model",
        primary_metric_name="parity_rate",
        point_estimate=0.95,
        ci_lower=0.90,
        ci_upper=0.98,
        cost_per_1k=1.50,
        error_rate=0.00,
    )
    c_cheap = CandidateSummary(
        model_key="digitalocean/gemma-2-9b",
        display_name="Gemma 2 9B",
        primary_metric_name="parity_rate",
        point_estimate=0.92,
        ci_lower=0.86,
        ci_upper=0.96,
        cost_per_1k=0.24,
        error_rate=0.01,
    )

    res = generate_recommendation(
        candidates=[c_expensive, c_cheap],
        baseline_cost_per_1k=15.00,
        threshold=0.85,
        test_size=100,
    )

    assert res.decision == "switch_recommended"
    # Cheapest wins
    assert res.recommended_candidate.model_key == "digitalocean/gemma-2-9b"
    assert len(res.runner_ups) == 1
    assert res.runner_ups[0].model_key == "cloud/large-model"
    # Overlapping CIs noted
    assert "not distinguishable" in res.details


def test_recommendation_disqualified_by_error_rate():
    # Good lower CI, but error rate exceeds 5%
    c = CandidateSummary(
        model_key="flaky-model",
        display_name="Flaky Model",
        primary_metric_name="parity_rate",
        point_estimate=0.95,
        ci_lower=0.89,
        ci_upper=0.99,
        cost_per_1k=0.10,
        error_rate=0.08,  # > 0.05
    )

    res = generate_recommendation(
        candidates=[c],
        baseline_cost_per_1k=15.00,
        threshold=0.85,
        max_error_rate=0.05,
        test_size=50,
        trainable_rows_count=0,
    )

    assert res.decision == "no_safe_switch"
    assert len(res.eligible_candidates) == 0


def test_recommendation_finetune_path():
    c_near = CandidateSummary(
        model_key="ollama/gemma2:2b",
        display_name="Gemma 2 2B",
        primary_metric_name="parity_rate",
        point_estimate=0.81,
        ci_lower=0.74,  # below 0.85
        ci_upper=0.87,
        cost_per_1k=0.00,
        error_rate=0.01,
    )

    res = generate_recommendation(
        candidates=[c_near],
        baseline_cost_per_1k=15.00,
        threshold=0.85,
        test_size=60,
        trainable_rows_count=120,  # >= 50
    )

    assert res.decision == "switch_after_finetune"
    assert res.recommended_candidate is not None
    assert res.recommended_candidate.model_key == "ollama/gemma2:2b"
    assert res.closest_gap is not None
    assert round(res.closest_gap, 2) == 0.11  # 0.85 - 0.74


def test_recommendation_no_safe_switch():
    c_low = CandidateSummary(
        model_key="weak-model",
        display_name="Weak Model",
        primary_metric_name="parity_rate",
        point_estimate=0.50,
        ci_lower=0.40,
        ci_upper=0.60,
        cost_per_1k=0.05,
        error_rate=0.02,
    )

    res = generate_recommendation(
        candidates=[c_low],
        baseline_cost_per_1k=15.00,
        threshold=0.85,
        test_size=50,
        trainable_rows_count=10,  # < 50
    )

    assert res.decision == "no_safe_switch"
    assert res.recommended_candidate is None
    assert "No safe switch found" in res.headline


def test_recommendation_insufficient_data_n_below_20():
    c = CandidateSummary(
        model_key="gemma-2-9b",
        display_name="Gemma 2 9B",
        primary_metric_name="parity_rate",
        point_estimate=0.95,
        ci_lower=0.90,
        ci_upper=0.99,
        cost_per_1k=0.24,
        error_rate=0.00,
    )

    res = generate_recommendation(
        candidates=[c],
        baseline_cost_per_1k=15.00,
        threshold=0.85,
        test_size=15,  # < 20 hard limit
    )

    assert res.decision == "insufficient_data"
    assert res.recommended_candidate is None
    assert "too small" in res.headline.lower()


def test_recommendation_warning_for_n_between_20_and_30():
    c = CandidateSummary(
        model_key="gemma-2-9b",
        display_name="Gemma 2 9B",
        primary_metric_name="parity_rate",
        point_estimate=0.95,
        ci_lower=0.88,
        ci_upper=0.99,
        cost_per_1k=0.24,
        error_rate=0.00,
    )

    res = generate_recommendation(
        candidates=[c],
        baseline_cost_per_1k=15.00,
        threshold=0.85,
        test_size=25,  # between 20 and 30
    )

    assert res.decision == "switch_recommended"
    assert len(res.warnings) == 1
    assert "below recommended threshold of 30" in res.warnings[0]
