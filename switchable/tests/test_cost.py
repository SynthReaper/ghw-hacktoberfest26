import pytest

from openswitch.cost import (
    CostAssumptions,
    calculate_finetune_breakeven,
    calculate_model_cost_summary,
    calculate_monthly_projection,
    calculate_request_cost,
)


def test_calculate_request_cost_worked_example():
    # 1,000 prompt tokens at $2.50/M = 0.002500
    # 200 completion tokens at $10.00/M = 0.002000
    # Total = 0.004500
    cost = calculate_request_cost(1000, 200, price_in_per_m=2.50, price_out_per_m=10.00)
    assert pytest.approx(cost, abs=1e-6) == 0.0045


def test_calculate_model_cost_summary():
    # 2 requests:
    # req 1: 500 in, 100 out
    # req 2: 1500 in, 300 out
    # Average: 1000 in, 200 out
    tokens = [(500, 100), (1500, 300)]
    summary = calculate_model_cost_summary(
        model_key="digitalocean/gemma-2-9b",
        requests_tokens=tokens,
        price_in_per_m=0.20,
        price_out_per_m=0.20,
        pricing_source="https://www.digitalocean.com/pricing",
        verified_on="2026-10-14",
        is_stale=False,
        is_local=False,
        baseline_cost_per_request=0.015,
    )

    assert summary.mean_tokens_in == 1000.0
    assert summary.mean_tokens_out == 200.0
    # cost = (1000 * 0.20 / 1e6) + (200 * 0.20 / 1e6) = 0.000200 + 0.000040 = 0.000240
    assert pytest.approx(summary.cost_per_request, abs=1e-6) == 0.00024
    # cost per 1k = 0.240
    assert pytest.approx(summary.cost_per_1k, abs=1e-4) == 0.24
    assert not summary.assumptions.is_stale


def test_calculate_monthly_projection():
    assumptions = CostAssumptions(
        pricing_source="specs/pricing.yaml",
        verified_on="2026-10-14",
        is_stale=False,
        baseline_method="per_request_flat",
        baseline_cost_per_request=0.015,
        candidate_cost_per_request=0.0003,
        candidate_is_local=False,
    )

    proj = calculate_monthly_projection(
        baseline_cost_per_request=0.015,
        candidate_cost_per_request=0.0003,
        monthly_volume=50_000,
        assumptions=assumptions,
    )

    assert proj.baseline_monthly_cost == 750.0  # 50,000 * $0.015
    assert proj.candidate_monthly_cost == 15.0  # 50,000 * $0.0003
    assert proj.monthly_savings == 735.0
    assert proj.savings_pct == 98.0


def test_calculate_monthly_projection_local_with_amortization():
    assumptions = CostAssumptions(
        pricing_source="local",
        verified_on="2026-10-14",
        is_stale=False,
        baseline_method="per_request_flat",
        baseline_cost_per_request=0.015,
        candidate_cost_per_request=0.0,
        candidate_is_local=True,
        hardware_amortization_monthly_usd=25.0,
    )

    proj = calculate_monthly_projection(
        baseline_cost_per_request=0.015,
        candidate_cost_per_request=0.0,
        monthly_volume=50_000,
        assumptions=assumptions,
    )

    assert proj.baseline_monthly_cost == 750.0
    assert proj.candidate_monthly_cost == 25.0  # amortized hardware line
    assert proj.monthly_savings == 725.0
    assert pytest.approx(proj.savings_pct, abs=0.1) == 96.67


def test_calculate_finetune_breakeven_worked_example():
    assumptions = CostAssumptions(
        pricing_source="tinker-pricing",
        verified_on="2026-10-14",
        is_stale=False,
        baseline_method="per_request_flat",
        baseline_cost_per_request=0.015,
        candidate_cost_per_request=0.0003,
        candidate_is_local=False,
    )

    # One-time training: $3.50, per request savings: 0.0147
    # Breakeven requests = ceil(3.50 / 0.0147) = 239
    be = calculate_finetune_breakeven(
        one_time_training_cost_usd=3.50,
        baseline_cost_per_request=0.015,
        candidate_cost_per_request=0.0003,
        assumptions=assumptions,
        reference_volumes=(10_000, 50_000),
    )

    assert be.breakeven_requests == 239
    assert be.breakeven_months_at_volume[10_000] == 0.02  # 239 / 10000 = ~0.024 -> 0.02
    assert be.breakeven_months_at_volume[50_000] == 0.00  # < 0.01 mo


def test_calculate_finetune_breakeven_negative_savings():
    assumptions = CostAssumptions(
        pricing_source="test",
        verified_on="2026-10-14",
        is_stale=False,
        baseline_method="per_request_flat",
        baseline_cost_per_request=0.001,
        candidate_cost_per_request=0.005,  # Candidate is more expensive!
        candidate_is_local=False,
    )

    be = calculate_finetune_breakeven(
        one_time_training_cost_usd=10.0,
        baseline_cost_per_request=0.001,
        candidate_cost_per_request=0.005,
        assumptions=assumptions,
    )

    assert be.breakeven_requests is None
    assert be.breakeven_months_at_volume[10_000] is None
