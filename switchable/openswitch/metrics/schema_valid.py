"""JSON schema validity checker for model generations."""

from typing import Any

from jsonschema import Draft202012Validator

from openswitch.metrics.json_valid import is_valid_json


def is_schema_valid(text: str | None, schema: dict[str, Any]) -> tuple[bool, Any | None, list[str]]:
    """Validate model output against a task's JSON schema.

    Returns:
        tuple[bool, Any | None, list[str]]: (is_valid, parsed_json, error_messages)
    """
    valid_json, parsed = is_valid_json(text)
    if not valid_json or parsed is None:
        return False, None, ["Invalid JSON payload"]

    validator = Draft202012Validator(schema)
    errors = [e.message for e in validator.iter_errors(parsed)]
    return len(errors) == 0, parsed, errors
