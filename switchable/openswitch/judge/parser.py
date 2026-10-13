"""Strict JSON parser for judge verdicts."""

from dataclasses import dataclass
from typing import Literal

from openswitch.metrics.json_valid import is_valid_json

RawVerdict = Literal["A", "B", "tie"]


@dataclass
class JudgeVerdict:
    verdict: RawVerdict | None
    reason: str
    is_valid: bool


def parse_judge_output(raw_output: str | None) -> JudgeVerdict:
    """Parse judge response into validated verdict."""
    if not raw_output or not raw_output.strip():
        return JudgeVerdict(verdict=None, reason="Empty output from judge", is_valid=False)

    valid_json, data = is_valid_json(raw_output)
    if not valid_json or not isinstance(data, dict):
        return JudgeVerdict(
            verdict=None, reason=f"Invalid JSON: {raw_output[:100]}", is_valid=False
        )

    verdict_raw = str(data.get("verdict", "")).strip().upper()
    reason = str(data.get("reason", "")).strip()

    if verdict_raw == "TIE":
        return JudgeVerdict(verdict="tie", reason=reason, is_valid=True)
    elif verdict_raw in ("A", "B"):
        return JudgeVerdict(verdict=verdict_raw, reason=reason, is_valid=True)  # type: ignore[arg-type]

    return JudgeVerdict(
        verdict=None,
        reason=f"Invalid verdict value '{verdict_raw}'. Must be 'A', 'B', or 'tie'.",
        is_valid=False,
    )
