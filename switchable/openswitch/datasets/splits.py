"""Deterministic dataset splitting with cryptographic hashing and duplicate detection."""

import hashlib
from typing import Any


def compute_split(example_id: str, seed: int, train_pct: float = 0.6, dev_pct: float = 0.1) -> str:
    """Deterministically assign an example to train, dev, or test split.

    Uses sha256(f"{seed}:{example_id}") to ensure reproducible assignment.
    """
    key = f"{seed}:{example_id}".encode()
    digest = hashlib.sha256(key).hexdigest()
    # Use first 16 hex characters (64 bits) for uniform float in [0, 1)
    ratio = int(digest[:16], 16) / float(0xFFFFFFFFFFFFFFFF)

    if ratio < train_pct:
        return "train"
    elif ratio < (train_pct + dev_pct):
        return "dev"
    else:
        return "test"


def assign_splits(
    rows: list[dict[str, Any]],
    seed: int = 1337,
    train_pct: float = 0.6,
    dev_pct: float = 0.1,
) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    """Assign splits to a list of rows and check for cross-split duplicates.

    Returns:
        tuple[list[dict], dict[str, int], list[str]]:
            - Rows with 'split' assigned
            - Split counts dictionary {"train": count, "dev": count, "test": count}
            - List of warnings (e.g. small sample warnings, cross-split input leakage)
    """
    warnings: list[str] = []
    split_counts: dict[str, int] = {"train": 0, "dev": 0, "test": 0}

    # Tracking inputs to detect duplicates across splits
    seen_inputs: dict[str, tuple[str, str]] = {}  # normalized_input -> (split, example_id)

    for row in rows:
        ex_id = str(row["id"])
        split = compute_split(ex_id, seed, train_pct, dev_pct)
        row["split"] = split
        split_counts[split] += 1

        # Check for normalized duplicate inputs across splits
        raw_input = row.get("input", "")
        norm_input = " ".join(str(raw_input).strip().lower().split())
        if norm_input in seen_inputs:
            prev_split, prev_id = seen_inputs[norm_input]
            if prev_split != split:
                warnings.append(
                    f"Data Leakage Warning: Exact duplicate input detected between {prev_split} "
                    f"(id={prev_id}) and {split} (id={ex_id})."
                )
        else:
            seen_inputs[norm_input] = (split, ex_id)

    # Statistical validity warnings
    test_n = split_counts["test"]
    if test_n < 20:
        warnings.append(
            f"Critical Statistical Limitation: Test split has only {test_n} examples. "
            f"Confidence intervals will be extremely wide; headline parity claims are unreliable below n=20."
        )
    elif test_n < 30:
        warnings.append(
            f"Statistical Notice: Test split has {test_n} examples (recommended minimum is 30). "
            f"Interpret bootstrap confidence intervals with caution."
        )

    return rows, split_counts, warnings
