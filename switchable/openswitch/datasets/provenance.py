"""Provenance tracking and training guard enforcement."""

from typing import Literal

ReferenceSource = Literal["human", "closed_api", "open_model", "unknown"]

PROVENANCE_DEFAULTS: dict[str, bool] = {
    "human": True,
    "open_model": True,
    "closed_api": False,
    "unknown": False,
}


class ProvenanceViolationError(ValueError):
    """Raised when closed_api or unknown rows attempt to be flagged train_allowed without attestation."""

    pass


def resolve_provenance(
    source: str | None,
    explicit_train_allowed: bool | None = None,
    attestation_granted: bool = False,
    line_number: int | None = None,
) -> tuple[str, bool]:
    """Resolve reference source and train_allowed status.

    Returns:
        tuple[str, bool]: (resolved_source, resolved_train_allowed)
    """
    src = (source or "unknown").strip().lower()
    if src not in PROVENANCE_DEFAULTS:
        line_prefix = f"Line {line_number}: " if line_number is not None else ""
        raise ValueError(
            f"{line_prefix}Invalid reference_source '{src}'. Must be one of: human, closed_api, open_model, unknown."
        )

    # If train_allowed was not explicitly provided, use the hard default
    if explicit_train_allowed is None:
        return src, PROVENANCE_DEFAULTS[src]

    # If user explicitly requests train_allowed=True for closed_api or unknown
    if explicit_train_allowed and not PROVENANCE_DEFAULTS[src]:
        if not attestation_granted:
            line_prefix = f"Line {line_number}: " if line_number is not None else ""
            raise ProvenanceViolationError(
                f"{line_prefix}Provenance Guard Block: reference_source is '{src}', but train_allowed=True was specified. "
                f"Training open models on closed API outputs or unknown data may violate terms of service. "
                f"To override, explicit legal attestation is required."
            )
        return src, True

    return src, explicit_train_allowed
