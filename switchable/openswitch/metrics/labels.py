"""Classification metrics: exact label accuracy and macro-averaged F1 score."""

import re

from sklearn.metrics import accuracy_score, f1_score


def normalize_label(label: str | None) -> str:
    """Normalize label string by trimming whitespace, quotes, and punctuation."""
    if not label:
        return ""
    cleaned = str(label).strip().lower()
    # Strip wrapping quotes if model returned '"billing"'
    cleaned = re.sub(r"^['\"]|['\"]$", "", cleaned)
    return cleaned.strip()


def calculate_classification_metrics(
    predictions: list[str | None],
    references: list[str],
) -> dict[str, float]:
    """Calculate accuracy and macro-F1 score across prediction and reference lists.

    Returns:
        dict[str, float]: {"label_accuracy": float, "macro_f1": float}
    """
    if not references:
        return {"label_accuracy": 0.0, "macro_f1": 0.0}

    norm_preds = [normalize_label(p) for p in predictions]
    norm_refs = [normalize_label(r) for r in references]

    acc = float(accuracy_score(norm_refs, norm_preds))
    f1 = float(f1_score(norm_refs, norm_preds, average="macro", zero_division=0))

    return {
        "label_accuracy": round(acc, 6),
        "macro_f1": round(f1, 6),
    }
