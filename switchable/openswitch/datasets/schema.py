"""JSON Schema validation for dataset rows."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "specs" / "dataset.schema.json"


def load_dataset_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


_SCHEMA = load_dataset_schema()
_VALIDATOR = Draft202012Validator(_SCHEMA)


class DatasetValidationError(Exception):
    """Raised when one or more rows fail schema validation."""

    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def validate_row_schema(row: dict[str, Any], line_number: int) -> None:
    """Validate a single row dictionary against the dataset schema.

    Raises:
        ValidationError: If schema conformance fails, formatted with line number.
    """
    errors = list(_VALIDATOR.iter_errors(row))
    if errors:
        msg_parts = []
        for err in errors:
            path = ".".join(str(p) for p in err.path) if err.path else "root"
            msg_parts.append(f"Line {line_number} [{path}]: {err.message}")
        raise DatasetValidationError(msg_parts)
