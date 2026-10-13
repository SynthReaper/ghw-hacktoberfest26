"""Recommendation engine per PRD and Evaluation Methodology §7."""

from dataclasses import asdict, dataclass, field
from typing import Literal

from openswitch.stats import are_cis_overlapping

RecommendationDecision = Literal[
    "switch_recommended",
    "switch_after_finetune",
    "no_safe_switch",
    "insufficient_data",
]


@dataclass
class CandidateSummary:
    model_key: str
    display_name: str
    primary_metric_name: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    cost_per_1k: float
    error_rate: float
    latency_p50_ms: float = 0.0
    is_local: bool = False
    is_finetuned: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RecommendationResult:
    decision: RecommendationDecision
    recommended_candidate: CandidateSummary | None
    headline: str
    details: str
    threshold: float
    eligible_candidates: list[CandidateSummary] = field(default_factory=list)
    ineligible_candidates: list[CandidateSummary] = field(default_factory=list)
    runner_ups: list[CandidateSummary] = field(default_factory=list)
    savings_range_usd_per_1k: tuple[float, float] | None = None
    closest_candidate: CandidateSummary | None = None
    closest_gap: float | None = None
    finetune_feasible: bool = False
    trainable_rows_count: int = 0
    test_size: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def generate_recommendation(
    candidates: list[CandidateSummary],
    baseline_cost_per_1k: float,
    threshold: float = 0.85,
    max_error_rate: float = 0.05,
    test_size: int = 30,
    trainable_rows_count: int = 0,
    min_trainable_rows: int = 50,
) -> RecommendationResult:
    """Evaluate candidates and generate an honest recommendation based on CI lower bounds.

    Rules per doc 05 §7:
    1. Eligible = lower CI bound >= threshold AND error_rate <= max_error_rate.
    2. If eligible: lowest cost_per_1k wins.
    3. If none eligible, but trainable_rows >= min_trainable_rows: recommend switch_after_finetune.
    4. Otherwise: 'no_safe_switch'.
    """
    warnings: list[str] = []

    # Hard guard on sample size per doc 05 §2
    if test_size < 20:
        return RecommendationResult(
            decision="insufficient_data",
            recommended_candidate=None,
            headline=f"Sample size (n={test_size}) is too small (< 20).",
            details="Open-Switch refuses headline recommendations when test size is under 20 to avoid spurious claims.",
            threshold=threshold,
            test_size=test_size,
            warnings=[
                "Test split size < 20. Add more test rows before making a migration decision."
            ],
        )

    if test_size < 30:
        warnings.append(
            f"Warning: test size (n={test_size}) is below recommended threshold of 30. CIs are wide."
        )

    eligible: list[CandidateSummary] = []
    ineligible: list[CandidateSummary] = []

    for c in candidates:
        if c.ci_lower >= threshold and c.error_rate <= max_error_rate:
            eligible.append(c)
        else:
            ineligible.append(c)

    # Sort eligible by cost_per_1k ascending (cheapest first)
    eligible.sort(key=lambda x: x.cost_per_1k)

    if eligible:
        best = eligible[0]
        runner_ups = eligible[1:]

        # CI overlap notes
        indistinguishable: list[str] = []
        for ru in runner_ups:
            if are_cis_overlapping((best.ci_lower, best.ci_upper), (ru.ci_lower, ru.ci_upper)):
                indistinguishable.append(ru.display_name)

        overlap_note = ""
        if indistinguishable:
            overlap_note = (
                f" Note: {', '.join(indistinguishable)} quality is not distinguishable from "
                f"{best.display_name} at this sample size (overlapping 95% CIs)."
            )

        savings_per_1k = max(0.0, baseline_cost_per_1k - best.cost_per_1k)
        headline = f"Safe switch recommended: {best.display_name}"
        details = (
            f"{best.display_name} meets the {threshold:.0%} quality threshold with 95% CI "
            f"[{best.ci_lower:.2%}, {best.ci_upper:.2%}] and error rate {best.error_rate:.1%}. "
            f"Saves ${savings_per_1k:.4f} per 1,000 requests vs baseline (${baseline_cost_per_1k:.4f}/1k).{overlap_note}"
        )

        return RecommendationResult(
            decision="switch_recommended",
            recommended_candidate=best,
            headline=headline,
            details=details,
            threshold=threshold,
            eligible_candidates=eligible,
            ineligible_candidates=ineligible,
            runner_ups=runner_ups,
            savings_range_usd_per_1k=(
                max(0.0, baseline_cost_per_1k - best.cost_per_1k),
                max(0.0, baseline_cost_per_1k - best.cost_per_1k),
            ),
            test_size=test_size,
            warnings=warnings,
        )

    # No eligible candidates
    # Find closest candidate (highest lower CI bound)
    candidates_by_ci = sorted(candidates, key=lambda x: x.ci_lower, reverse=True)
    closest = candidates_by_ci[0] if candidates_by_ci else None
    gap = (threshold - closest.ci_lower) if closest else None

    finetune_feasible = trainable_rows_count >= min_trainable_rows

    if finetune_feasible and closest is not None:
        headline = f"Switch after fine-tune recommended (starting with {closest.display_name})"
        details = (
            f"No zero-shot candidate met the {threshold:.0%} threshold with 95% confidence. "
            f"Closest candidate is {closest.display_name} at [{closest.ci_lower:.2%}, {closest.ci_upper:.2%}] "
            f"(gap: {gap:.1%}). Fine-tuning is feasible with {trainable_rows_count} training rows."
        )
        return RecommendationResult(
            decision="switch_after_finetune",
            recommended_candidate=closest,
            headline=headline,
            details=details,
            threshold=threshold,
            eligible_candidates=[],
            ineligible_candidates=ineligible,
            closest_candidate=closest,
            closest_gap=round(gap, 4) if gap else None,
            finetune_feasible=True,
            trainable_rows_count=trainable_rows_count,
            test_size=test_size,
            warnings=warnings,
        )
    else:
        headline = f"No safe switch found at {threshold:.0%} threshold"
        details = (
            f"No candidate reliably satisfied the {threshold:.0%} lower CI bound requirement. "
            + (
                f"Closest was {closest.display_name} with lower bound {closest.ci_lower:.2%} "
                f"(gap: {gap:.1%}). "
                if closest
                else ""
            )
            + (
                f"Fine-tuning is not immediately feasible ({trainable_rows_count} trainable rows < {min_trainable_rows})."
                if not finetune_feasible
                else ""
            )
        )
        return RecommendationResult(
            decision="no_safe_switch",
            recommended_candidate=None,
            headline=headline,
            details=details,
            threshold=threshold,
            eligible_candidates=[],
            ineligible_candidates=ineligible,
            closest_candidate=closest,
            closest_gap=round(gap, 4) if gap else None,
            finetune_feasible=finetune_feasible,
            trainable_rows_count=trainable_rows_count,
            test_size=test_size,
            warnings=warnings,
        )
