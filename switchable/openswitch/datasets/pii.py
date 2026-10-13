"""PII detection and masking for dataset inputs and references."""

import re
from dataclasses import dataclass

# Compiled regex patterns for common sensitive entities
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")


@dataclass
class PIIWarning:
    row_idx: int
    example_id: str
    pii_type: str
    preview: str


def scan_pii_in_text(text: str, row_idx: int, example_id: str) -> list[PIIWarning]:
    """Scan a single text string for potential PII matches."""
    warnings: list[PIIWarning] = []

    for match in EMAIL_REGEX.finditer(text):
        warnings.append(PIIWarning(row_idx, example_id, "email", match.group(0)[:12] + "..."))

    for match in PHONE_REGEX.finditer(text):
        warnings.append(PIIWarning(row_idx, example_id, "phone", match.group(0)[:10] + "..."))

    for match in SSN_REGEX.finditer(text):
        warnings.append(PIIWarning(row_idx, example_id, "ssn", "***-**-****"))

    for match in CARD_REGEX.finditer(text):
        warnings.append(PIIWarning(row_idx, example_id, "card", "****-****-****-****"))

    return warnings


def scan_pii(rows: list[dict]) -> list[PIIWarning]:
    """Scan all rows for PII across system_prompt, input, and reference fields."""
    all_warnings: list[PIIWarning] = []
    for idx, row in enumerate(rows):
        ex_id = str(row.get("id", f"idx_{idx}"))
        for field in ("system_prompt", "input", "reference"):
            val = row.get(field)
            if isinstance(val, str) and val:
                all_warnings.extend(scan_pii_in_text(val, idx, ex_id))
            elif isinstance(val, list):  # Chat message list
                for msg in val:
                    content = msg.get("content", "")
                    if content:
                        all_warnings.extend(scan_pii_in_text(content, idx, ex_id))
    return all_warnings


def mask_pii(text: str) -> str:
    """Mask detected PII tokens in text with generic placeholders."""
    masked = EMAIL_REGEX.sub("[EMAIL]", text)
    masked = PHONE_REGEX.sub("[PHONE]", masked)
    masked = SSN_REGEX.sub("[SSN]", masked)
    masked = CARD_REGEX.sub("[CARD]", masked)
    return masked
