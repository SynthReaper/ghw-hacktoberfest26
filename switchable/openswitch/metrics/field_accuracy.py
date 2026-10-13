"""Field accuracy and composite critical fields metric for structured extraction tasks."""

from typing import Any

from openswitch.metrics.json_valid import is_valid_json


def normalize_value(val: Any) -> Any:
    """Normalize values for robust case-insensitive comparison."""
    if isinstance(val, str):
        return val.strip().lower()
    return val


def evaluate_field_accuracy(
    candidate_text: str | None,
    reference_text: str,
    critical_fields: list[str] | None = None,
) -> dict[str, float]:
    """Compute per-field accuracy and critical fields composite.

    Returns:
        dict[str, float]: mapping of 'field_<name>' -> 0.0/1.0 and
                          'composite_critical_fields_correct' -> 0.0/1.0
    """
    results: dict[str, float] = {}

    ref_valid, ref_json = is_valid_json(reference_text)
    if not ref_valid or not isinstance(ref_json, dict):
        raise ValueError(f"Reference output is not a valid JSON object: {reference_text}")

    cand_valid, cand_json = is_valid_json(candidate_text)
    cand_dict: dict[str, Any] | None = (
        cand_json if (cand_valid and isinstance(cand_json, dict)) else None
    )
    all_critical_match = cand_dict is not None

    for field, ref_val in ref_json.items():
        norm_ref = normalize_value(ref_val)
        if cand_dict is not None and field in cand_dict:
            cand_val = normalize_value(cand_dict[field])
            is_match = norm_ref == cand_val
        else:
            is_match = False

        results[f"field_{field}"] = 1.0 if is_match else 0.0

        if critical_fields and field in critical_fields:
            if not is_match:
                all_critical_match = False

    if critical_fields:
        results["composite_critical_fields_correct"] = 1.0 if all_critical_match else 0.0

    return results
