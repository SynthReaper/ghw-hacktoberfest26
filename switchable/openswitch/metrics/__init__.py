"""Deterministic evaluation metrics package."""

from openswitch.metrics.field_accuracy import evaluate_field_accuracy
from openswitch.metrics.json_valid import is_valid_json, strip_code_fences
from openswitch.metrics.labels import calculate_classification_metrics, normalize_label
from openswitch.metrics.schema_valid import is_schema_valid

__all__ = [
    "strip_code_fences",
    "is_valid_json",
    "is_schema_valid",
    "evaluate_field_accuracy",
    "normalize_label",
    "calculate_classification_metrics",
]
