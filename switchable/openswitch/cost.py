"""Cost, latency, and savings projection models with fine-tune break-even calculations."""

import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Literal


@dataclass
class CostAssumptions:
    pricing_source: str
    verified_on: str
    is_stale: bool
    baseline_method: Literal["per_request_flat", "tokens_and_price"]
    baseline_cost_per_request: float
    candidate_cost_per_request: float
    candidate_is_local: bool
    training_cost_usd: float = 0.0
    serving_cost_notes: str | None = None
    hardware_amortization_monthly_usd: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ModelCostSummary:
    model_key: str
    mean_tokens_in: float
    mean_tokens_out: float
    cost_per_request: float
    cost_per_1k: float
    assumptions: CostAssumptions

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MonthlyProjection:
    monthly_volume: int
    baseline_monthly_cost: float
    candidate_monthly_cost: float
    monthly_savings: float
    savings_pct: float
    assumptions: CostAssumptions

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FinetuneBreakEven:
    one_time_training_cost: float
    per_request_savings: float
    breakeven_requests: int | None
    breakeven_months_at_volume: dict[int, float | None]
    assumptions: CostAssumptions

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_request_cost(
    tokens_in: int | float,
    tokens_out: int | float,
    price_in_per_m: float,
    price_out_per_m: float,
) -> float:
    """Calculate single request dollar cost based on per-million token pricing."""
    cost = (tokens_in * price_in_per_m / 1_000_000.0) + (tokens_out * price_out_per_m / 1_000_000.0)
    return round(cost, 8)


def calculate_model_cost_summary(
    model_key: str,
    requests_tokens: Sequence[tuple[int | float, int | float]],
    price_in_per_m: float,
    price_out_per_m: float,
    pricing_source: str,
    verified_on: str,
    is_stale: bool,
    is_local: bool = False,
    baseline_cost_per_request: float = 0.0,
) -> ModelCostSummary:
    """Calculate average cost per request and per 1k requests over test rows."""
    if not requests_tokens:
        assumptions = CostAssumptions(
            pricing_source=pricing_source,
            verified_on=verified_on,
            is_stale=is_stale,
            baseline_method="per_request_flat",
            baseline_cost_per_request=baseline_cost_per_request,
            candidate_cost_per_request=0.0,
            candidate_is_local=is_local,
        )
        return ModelCostSummary(
            model_key=model_key,
            mean_tokens_in=0.0,
            mean_tokens_out=0.0,
            cost_per_request=0.0,
            cost_per_1k=0.0,
            assumptions=assumptions,
        )

    n = len(requests_tokens)
    total_tokens_in = sum(t[0] for t in requests_tokens)
    total_tokens_out = sum(t[1] for t in requests_tokens)
    mean_in = total_tokens_in / n
    mean_out = total_tokens_out / n

    if is_local:
        cost_per_req = 0.0
    else:
        costs = [
            calculate_request_cost(t[0], t[1], price_in_per_m, price_out_per_m)
            for t in requests_tokens
        ]
        cost_per_req = sum(costs) / n

    cost_per_1k = cost_per_req * 1000.0

    assumptions = CostAssumptions(
        pricing_source=pricing_source,
        verified_on=verified_on,
        is_stale=is_stale,
        baseline_method="tokens_and_price" if baseline_cost_per_request > 0 else "per_request_flat",
        baseline_cost_per_request=baseline_cost_per_request,
        candidate_cost_per_request=round(cost_per_req, 8),
        candidate_is_local=is_local,
    )

    return ModelCostSummary(
        model_key=model_key,
        mean_tokens_in=round(mean_in, 2),
        mean_tokens_out=round(mean_out, 2),
        cost_per_request=round(cost_per_req, 8),
        cost_per_1k=round(cost_per_1k, 6),
        assumptions=assumptions,
    )


def calculate_monthly_projection(
    baseline_cost_per_request: float,
    candidate_cost_per_request: float,
    monthly_volume: int,
    assumptions: CostAssumptions,
) -> MonthlyProjection:
    """Calculate monthly cost projection and savings.

    Formula:
        monthly_cost = volume * mean_cost
        savings = (baseline_cost - candidate_cost) * volume
    """
    baseline_monthly = baseline_cost_per_request * monthly_volume
    candidate_monthly = (
        candidate_cost_per_request * monthly_volume
    ) + assumptions.hardware_amortization_monthly_usd
    savings = baseline_monthly - candidate_monthly

    savings_pct = (savings / baseline_monthly * 100.0) if baseline_monthly > 0 else 0.0

    return MonthlyProjection(
        monthly_volume=monthly_volume,
        baseline_monthly_cost=round(baseline_monthly, 2),
        candidate_monthly_cost=round(candidate_monthly, 2),
        monthly_savings=round(savings, 2),
        savings_pct=round(savings_pct, 2),
        assumptions=assumptions,
    )


def calculate_finetune_breakeven(
    one_time_training_cost_usd: float,
    baseline_cost_per_request: float,
    candidate_cost_per_request: float,
    assumptions: CostAssumptions,
    reference_volumes: tuple[int, ...] = (10_000, 50_000, 100_000),
) -> FinetuneBreakEven:
    """Calculate requests and months to break even on one-time fine-tuning cost.

    Per doc 05 §6:
        breakeven_requests = one_time_cost / per_request_savings
    """
    per_req_savings = baseline_cost_per_request - candidate_cost_per_request

    months_at_vol: dict[int, float | None]
    if per_req_savings <= 0 or one_time_training_cost_usd <= 0:
        breakeven_reqs = None
        months_at_vol = {vol: None for vol in reference_volumes}
    else:
        breakeven_reqs = int(math.ceil(one_time_training_cost_usd / per_req_savings))
        months_at_vol = {
            vol: (round(breakeven_reqs / vol, 2) if vol > 0 else None) for vol in reference_volumes
        }

    # Record training cost in assumptions
    assumptions.training_cost_usd = round(one_time_training_cost_usd, 4)

    return FinetuneBreakEven(
        one_time_training_cost=round(one_time_training_cost_usd, 4),
        per_request_savings=round(per_req_savings, 8),
        breakeven_requests=breakeven_reqs,
        breakeven_months_at_volume=months_at_vol,
        assumptions=assumptions,
    )
