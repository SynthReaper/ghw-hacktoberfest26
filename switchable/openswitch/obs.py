"""Observability and Sentry integration: agent gen_ai tracing, telemetry scrubbing, and anomaly alerts."""

import os
import re
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import sentry_sdk

# Sensitive field name patterns to scrub (avoids matching metrics like tokens_in, tokens_out)
SENSITIVE_KEY_RE = re.compile(
    r"(^|_)(api_?key|secret|password|bearer|prompt|completion|output|messages|answer_[ab]|rubric|auth(_token)?|access_token|refresh_token)($|_)|authorization",
    re.IGNORECASE,
)


def scrub_dict(data: Any) -> Any:
    """Recursively scrub any sensitive keys, prompt text, or output text."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if SENSITIVE_KEY_RE.search(k):
                cleaned[k] = "[SCRUBBED]"
            else:
                cleaned[k] = scrub_dict(v)
        return cleaned
    elif isinstance(data, list):
        return [scrub_dict(item) for item in data]
    return data


def sentry_event_scrubber(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    """Sentry before_send hook ensuring zero secrets, prompts, or output text are transmitted."""
    # Scrub breadcrumbs
    if "breadcrumbs" in event and isinstance(event["breadcrumbs"], dict):
        for b in event["breadcrumbs"].get("values", []):
            if "data" in b and isinstance(b["data"], dict):
                b["data"] = scrub_dict(b["data"])

    # Scrub extra
    if "extra" in event and isinstance(event["extra"], dict):
        event["extra"] = scrub_dict(event["extra"])

    # Scrub contexts
    if "contexts" in event and isinstance(event["contexts"], dict):
        event["contexts"] = scrub_dict(event["contexts"])

    # Scrub request data if present
    if "request" in event and isinstance(event["request"], dict):
        if "data" in event["request"]:
            event["request"]["data"] = "[SCRUBBED]"
        if "headers" in event["request"] and isinstance(event["request"]["headers"], dict):
            event["request"]["headers"] = scrub_dict(event["request"]["headers"])

    return event


def init_sentry(
    dsn: str | None = None,
    release: str | None = None,
    environment: str = "production",
) -> bool:
    """Initialize Sentry with strict PII and prompt scrubbing.

    Returns True if Sentry was initialized, False otherwise.
    """
    effective_dsn = dsn or os.environ.get("SENTRY_DSN")
    if not effective_dsn:
        return False

    sentry_sdk.init(
        dsn=effective_dsn,
        release=release,
        environment=environment,
        send_default_pii=False,
        traces_sample_rate=1.0,
        before_send=sentry_event_scrubber,
    )
    return True


@contextmanager
def gen_ai_span(
    operation: str,
    description: str,
    model: str,
    provider: str,
    prompt_version: str | None = None,
    experiment_id: str | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Context manager for Sentry Gen AI spans (zero prompt/output text recorded).

    Yields a mutable dictionary where callers record token counts, latency, and cost.
    """
    meta: dict[str, Any] = {
        "tokens_in": 0,
        "tokens_out": 0,
        "latency_ms": 0.0,
        "ttft_ms": None,
        "cost_usd": 0.0,
        "usage_estimated": False,
    }

    # Start span if Sentry is active
    span = sentry_sdk.start_span(op=f"gen_ai.{operation}", name=description)
    span.set_data("gen_ai.system", provider)
    span.set_data("gen_ai.request.model", model)
    if prompt_version:
        span.set_data("gen_ai.prompt_version", prompt_version)
    if experiment_id:
        span.set_data("experiment_id", experiment_id)

    try:
        yield meta
    except Exception as exc:
        span.set_status("internal_error")
        span.set_data("error.message", str(exc))
        raise
    finally:
        # Record telemetry attributes
        span.set_data("gen_ai.usage.input_tokens", meta.get("tokens_in", 0))
        span.set_data("gen_ai.usage.output_tokens", meta.get("tokens_out", 0))
        span.set_data("gen_ai.usage.cost_usd", meta.get("cost_usd", 0.0))
        span.set_data("gen_ai.response.latency_ms", meta.get("latency_ms", 0.0))
        if meta.get("ttft_ms") is not None:
            span.set_data("gen_ai.response.ttft_ms", meta.get("ttft_ms"))
        span.set_data("gen_ai.usage.estimated", meta.get("usage_estimated", False))
        span.finish()


def check_and_report_experiment_anomalies(
    experiment_id: str,
    inconsistency_rate: float = 0.0,
    provider_error_rate: float = 0.0,
    empty_output_rate: float = 0.0,
    budget_cap_hit: bool = False,
    total_cost_usd: float = 0.0,
) -> list[str]:
    """Check anomaly thresholds per doc 03 §11 and capture Sentry issues.

    Thresholds:
    - Judge inconsistency rate > 20%
    - Provider error rate > 10%
    - Empty output rate > 5%
    - Budget cap hit
    """
    alerts: list[str] = []

    if inconsistency_rate > 0.20:
        msg = f"High judge inconsistency ({inconsistency_rate:.1%}) in experiment {experiment_id}"
        alerts.append(msg)
        sentry_sdk.capture_message(
            msg,
            level="warning",
            tags={"experiment_id": experiment_id, "anomaly": "high_judge_inconsistency"},
        )

    if provider_error_rate > 0.10:
        msg = f"High provider error rate ({provider_error_rate:.1%}) in experiment {experiment_id}"
        alerts.append(msg)
        sentry_sdk.capture_message(
            msg,
            level="error",
            tags={"experiment_id": experiment_id, "anomaly": "high_provider_errors"},
        )

    if empty_output_rate > 0.05:
        msg = f"High empty output rate ({empty_output_rate:.1%}) in experiment {experiment_id}"
        alerts.append(msg)
        sentry_sdk.capture_message(
            msg,
            level="warning",
            tags={"experiment_id": experiment_id, "anomaly": "high_empty_output"},
        )

    if budget_cap_hit:
        msg = f"Budget cap hit in experiment {experiment_id} (total spend: ${total_cost_usd:.4f})"
        alerts.append(msg)
        sentry_sdk.capture_message(
            msg,
            level="error",
            tags={"experiment_id": experiment_id, "anomaly": "budget_cap_hit"},
        )

    return alerts
