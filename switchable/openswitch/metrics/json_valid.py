"""JSON validity metric with strict markdown fence stripping."""

import json
import re
from typing import Any

FENCE_REGEX = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL | re.IGNORECASE)


def strip_code_fences(text: str) -> str:
    """Strip outermost markdown ```json ... ``` code blocks without repair."""
    cleaned = text.strip()
    match = FENCE_REGEX.match(cleaned)
    if match:
        return match.group(1).strip()
    return cleaned


def is_valid_json(text: str | None) -> tuple[bool, Any | None]:
    """Check if output parses as strict JSON after stripping fences.

    Returns:
        tuple[bool, Any | None]: (is_valid, parsed_object_or_none)
    """
    if not text or not str(text).strip():
        return False, None

    stripped = strip_code_fences(text)
    try:
        parsed = json.loads(stripped)
        return True, parsed
    except (json.JSONDecodeError, TypeError):
        return False, None
