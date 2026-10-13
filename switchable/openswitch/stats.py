"""Statistical routines: 10,000 resample bootstrap 95% CIs, percentiles, and length bias guards."""

from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np
from scipy import stats as sp_stats


@dataclass
class MetricWithCI:
    metric_name: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    ci_level: float = 0.95
    n_samples: int = 0
    bootstrap_resamples: int = 10000
    seed: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LengthBiasResult:
    spearman_rho: float
    p_value: float
    flagged: bool
    warning: str | None


def bootstrap_ci(
    data: list[float] | np.ndarray,
    stat_func: Callable[[np.ndarray], float] = np.mean,
    ci_level: float = 0.95,
    n_resamples: int = 10000,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Calculate percentile bootstrap confidence interval with a fixed seed.

    Returns:
        tuple[float, float, float]: (point_estimate, ci_lower, ci_upper)
    """
    arr = np.asarray(data, dtype=float)
    n = len(arr)
    if n == 0:
        return 0.0, 0.0, 0.0

    point_estimate = float(stat_func(arr))
    if n == 1:
        return point_estimate, point_estimate, point_estimate

    # Handle edge case where all values are identical (zero variance)
    if np.all(arr == arr[0]):
        return point_estimate, point_estimate, point_estimate

    rng = np.random.default_rng(seed)
    # Resample with replacement: shape (n_resamples, n)
    indices = rng.integers(0, n, size=(n_resamples, n))
    resampled_data = arr[indices]

    # Compute statistic along rows
    boot_stats = np.apply_along_axis(stat_func, 1, resampled_data)

    alpha = 1.0 - ci_level
    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    ci_lower = float(np.percentile(boot_stats, lower_pct))
    ci_upper = float(np.percentile(boot_stats, upper_pct))

    return round(point_estimate, 6), round(ci_lower, 6), round(ci_upper, 6)


def paired_difference_ci(
    values_a: list[float] | np.ndarray,
    values_b: list[float] | np.ndarray,
    stat_func: Callable[[np.ndarray], float] = np.mean,
    ci_level: float = 0.95,
    n_resamples: int = 10000,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Calculate bootstrap CI for paired difference (values_a - values_b)."""
    arr_a = np.asarray(values_a, dtype=float)
    arr_b = np.asarray(values_b, dtype=float)
    if len(arr_a) != len(arr_b):
        raise ValueError("Paired samples must have equal length")

    diffs = arr_a - arr_b
    return bootstrap_ci(
        diffs, stat_func=stat_func, ci_level=ci_level, n_resamples=n_resamples, seed=seed
    )


def calculate_metric_ci(
    scores: list[float] | list[int] | list[bool],
    metric_name: str,
    ci_level: float = 0.95,
    n_resamples: int = 10000,
    seed: int = 42,
) -> MetricWithCI:
    """Calculate point estimate and 95% CI for any numeric or boolean metric list."""
    float_scores = [float(s) for s in scores]
    n = len(float_scores)
    point, lower, upper = bootstrap_ci(
        float_scores,
        stat_func=np.mean,
        ci_level=ci_level,
        n_resamples=n_resamples,
        seed=seed,
    )
    return MetricWithCI(
        metric_name=metric_name,
        point_estimate=point,
        ci_lower=lower,
        ci_upper=upper,
        ci_level=ci_level,
        n_samples=n,
        bootstrap_resamples=n_resamples,
        seed=seed,
    )


def calculate_judge_stats(
    verdicts: list[str],
    ci_level: float = 0.95,
    n_resamples: int = 10000,
    seed: int = 42,
) -> dict[str, MetricWithCI]:
    """Calculate rates and bootstrap CIs for judge pairwise verdicts per PRD §3.

    Valid verdicts: win, loss, tie.
    - parity_rate = (win + tie) / valid_count
    - win_rate = win / valid_count
    - loss_rate = loss / valid_count
    - inconsistent_rate = inconsistent / total_count
    - invalid_rate = invalid / total_count
    """
    total = len(verdicts)
    if total == 0:
        empty = MetricWithCI("empty", 0.0, 0.0, 0.0, n_samples=0)
        return {
            "parity_rate": empty,
            "win_rate": empty,
            "loss_rate": empty,
            "inconsistent_rate": empty,
            "invalid_rate": empty,
        }

    norm = [v.strip().lower() for v in verdicts]
    valid_verdicts = [v for v in norm if v in ("win", "loss", "tie")]
    n_valid = len(valid_verdicts)

    if n_valid > 0:
        parity_binary = [1.0 if v in ("win", "tie") else 0.0 for v in valid_verdicts]
        win_binary = [1.0 if v == "win" else 0.0 for v in valid_verdicts]
        loss_binary = [1.0 if v == "loss" else 0.0 for v in valid_verdicts]

        parity_ci = calculate_metric_ci(
            parity_binary, "parity_rate", ci_level=ci_level, n_resamples=n_resamples, seed=seed
        )
        win_ci = calculate_metric_ci(
            win_binary, "win_rate", ci_level=ci_level, n_resamples=n_resamples, seed=seed
        )
        loss_ci = calculate_metric_ci(
            loss_binary, "loss_rate", ci_level=ci_level, n_resamples=n_resamples, seed=seed
        )
    else:
        parity_ci = MetricWithCI("parity_rate", 0.0, 0.0, 0.0, n_samples=0)
        win_ci = MetricWithCI("win_rate", 0.0, 0.0, 0.0, n_samples=0)
        loss_ci = MetricWithCI("loss_rate", 0.0, 0.0, 0.0, n_samples=0)

    # Inconsistent and Invalid rates across ALL judgments
    inconsistent_binary = [1.0 if v == "inconsistent" else 0.0 for v in norm]
    invalid_binary = [1.0 if v == "invalid" else 0.0 for v in norm]

    inconsistent_ci = calculate_metric_ci(
        inconsistent_binary,
        "inconsistent_rate",
        ci_level=ci_level,
        n_resamples=n_resamples,
        seed=seed,
    )
    invalid_ci = calculate_metric_ci(
        invalid_binary, "invalid_rate", ci_level=ci_level, n_resamples=n_resamples, seed=seed
    )

    return {
        "parity_rate": parity_ci,
        "win_rate": win_ci,
        "loss_rate": loss_ci,
        "inconsistent_rate": inconsistent_ci,
        "invalid_rate": invalid_ci,
    }


def calculate_percentiles(
    values: list[float] | np.ndarray,
    pcts: tuple[int, ...] = (50, 95),
) -> dict[str, float]:
    """Calculate distribution percentiles (e.g. p50, p95 for latency)."""
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return {f"p{p}": 0.0 for p in pcts}
    return {f"p{p}": round(float(np.percentile(arr, p)), 2) for p in pcts}


def check_length_bias(
    output_lengths: list[int] | list[float],
    scores: list[float] | list[int],
    threshold: float = 0.5,
) -> LengthBiasResult:
    """Check if model success correlates strongly with output character/token length.

    Per doc 05 §3: Flag if Spearman rho > 0.5.
    """
    if len(output_lengths) < 3 or len(output_lengths) != len(scores):
        return LengthBiasResult(spearman_rho=0.0, p_value=1.0, flagged=False, warning=None)

    # Check for constant arrays
    if len(set(output_lengths)) <= 1 or len(set(scores)) <= 1:
        return LengthBiasResult(spearman_rho=0.0, p_value=1.0, flagged=False, warning=None)

    res = sp_stats.spearmanr(output_lengths, scores)
    rho = float(res.statistic) if hasattr(res, "statistic") else float(res.correlation)  # type: ignore
    p_val = float(res.pvalue)

    if np.isnan(rho):
        return LengthBiasResult(spearman_rho=0.0, p_value=1.0, flagged=False, warning=None)

    flagged = rho > threshold
    warning = (
        f"Length bias warning: Spearman rho = {rho:.3f} > {threshold}. "
        "The judge shows strong preference for longer responses."
        if flagged
        else None
    )

    return LengthBiasResult(
        spearman_rho=round(rho, 4),
        p_value=round(p_val, 4),
        flagged=flagged,
        warning=warning,
    )


def are_cis_overlapping(ci_a: tuple[float, float], ci_b: tuple[float, float]) -> bool:
    """Check if two confidence intervals overlap."""
    lower_a, upper_a = ci_a
    lower_b, upper_b = ci_b
    return max(lower_a, lower_b) <= min(upper_a, upper_b)
