"""Judge calibration against human ground-truth labels using Cohen's kappa."""

from collections import Counter
from typing import Literal

ReliabilityTier = Literal["reliable", "moderate", "unreliable"]


def calculate_agreement(human_labels: list[str], judge_labels: list[str]) -> float:
    """Calculate raw observed agreement rate between human and judge."""
    if not human_labels or not judge_labels:
        return 0.0
    if len(human_labels) != len(judge_labels):
        raise ValueError("human_labels and judge_labels must have the same length")

    matches = sum(1 for h, j in zip(human_labels, judge_labels) if h.lower() == j.lower())
    return matches / len(human_labels)


def calculate_cohen_kappa(human_labels: list[str], judge_labels: list[str]) -> float:
    """Calculate Cohen's kappa coefficient measuring inter-annotator agreement.

    Formula:
        kappa = (P_o - P_e) / (1 - P_e)
    Where:
        P_o = observed agreement
        P_e = hypothetical probability of chance agreement
    """
    if not human_labels or not judge_labels:
        return 0.0
    if len(human_labels) != len(judge_labels):
        raise ValueError("human_labels and judge_labels must have the same length")

    n = len(human_labels)
    if n == 0:
        return 0.0

    # Normalise labels
    h_norm = [h.strip().lower() for h in human_labels]
    j_norm = [j.strip().lower() for j in judge_labels]

    # Categories union
    categories = sorted(set(h_norm).union(set(j_norm)))
    if not categories:
        return 1.0

    # Observed agreement
    observed_matches = sum(1 for h, j in zip(h_norm, j_norm) if h == j)
    p_o = observed_matches / n

    # Marginal totals
    h_counts = Counter(h_norm)
    j_counts = Counter(j_norm)

    # Expected agreement by chance
    p_e = sum((h_counts[c] / n) * (j_counts[c] / n) for c in categories)

    if abs(1.0 - p_e) < 1e-12:
        return 1.0 if abs(p_o - 1.0) < 1e-12 else 0.0

    kappa = (p_o - p_e) / (1.0 - p_e)
    return float(kappa)


def compute_confusion_matrix(
    human_labels: list[str],
    judge_labels: list[str],
) -> dict[str, dict[str, int]]:
    """Compute confusion matrix mapping human label -> judge label -> count."""
    h_norm = [h.strip().lower() for h in human_labels]
    j_norm = [j.strip().lower() for j in judge_labels]
    categories = sorted(set(h_norm).union(set(j_norm)))

    matrix: dict[str, dict[str, int]] = {c1: {c2: 0 for c2 in categories} for c1 in categories}
    for h, j in zip(h_norm, j_norm):
        matrix[h][j] += 1

    return matrix


def judge_reliability_tier(kappa: float) -> tuple[ReliabilityTier, str]:
    """Return the tier and guideline banner per PRD / Eval Methodology §5.

    - kappa >= 0.6: reliable
    - 0.4 <= kappa < 0.6: moderate, interpret with caution
    - kappa < 0.4: unreliable (fallback to deterministic ranking)
    """
    if kappa >= 0.6:
        return "reliable", "Judge is reliable (Cohen's kappa >= 0.60)."
    elif kappa >= 0.4:
        return (
            "moderate",
            "Moderate judge agreement (0.40 <= kappa < 0.60). Interpret judge results with caution.",
        )
    else:
        return (
            "unreliable",
            "Judge agreement is low (kappa < 0.40). Rankings will prioritize deterministic metrics.",
        )
