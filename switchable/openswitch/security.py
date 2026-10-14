"""Security hardening, CSV formula sanitization, rate limiting, and demo cleanup."""

from datetime import UTC, datetime, timedelta
import html
import io
import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select

from openswitch.config import settings
from openswitch.db import session_context
from openswitch.models import Dataset, Experiment, Generation, HumanLabel, Judgment, Report, Run, Score

logger = logging.getLogger(__name__)

# Dangerous formula trigger prefixes in spreadsheets (Excel, Google Sheets, LibreOffice Calc)
DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "%")


def sanitize_csv_cell(value: Any) -> str:
    """Sanitize a cell value to prevent CSV formula injection (CWE-1236).

    If the string representation begins with =, +, -, @, \\t, \\r, or %, prepend a single quote
    so spreadsheet software treats it as plain text instead of executing it.
    """
    if value is None:
        return ""

    text = str(value)
    if not text:
        return ""

    # Check for leading dangerous characters or whitespace followed by formula character
    stripped = text.lstrip()
    if stripped.startswith(DANGEROUS_FORMULA_PREFIXES):
        return "'" + text

    return text


def escape_html_text(value: str | None) -> str:
    """Safely HTML-escape text for rendering in web pages and reports."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def check_kill_switch() -> None:
    """Enforce the global kill switch if active."""
    if settings.kill_switch:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Open-Switch is currently paused via kill switch. Evaluation runs are suspended.",
        )


async def check_visitor_rate_limit(session_hash: str | None) -> None:
    """Verify visitor has not exceeded maximum experiments per day in demo mode."""
    if not settings.demo_mode or not session_hash:
        return

    cutoff = datetime.now(UTC) - timedelta(days=1)
    async with session_context() as session:
        query = (
            select(func.count(Experiment.id))
            .where(Experiment.session_hash == session_hash)
            .where(Experiment.created_at >= cutoff)
        )
        res = await session.execute(query)
        count = res.scalar() or 0

        if count >= settings.max_experiments_per_visitor_day:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Demo mode rate limit exceeded: maximum {settings.max_experiments_per_visitor_day} "
                    f"experiments per visitor per 24 hours (used {count})."
                ),
            )


async def cleanup_old_demo_data(max_age_hours: int = 24) -> int:
    """Delete demo-mode datasets and experiments older than max_age_hours."""
    if not settings.demo_mode:
        return 0

    cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
    deleted_count = 0

    try:
        async with session_context() as session:
            # Find old experiments
            exp_res = await session.execute(
                select(Experiment.id).where(Experiment.created_at < cutoff)
            )
            old_exp_ids = exp_res.scalars().all()

            if old_exp_ids:
                # Delete cascaded experiments
                await session.execute(delete(Experiment).where(Experiment.id.in_(old_exp_ids)))
                deleted_count += len(old_exp_ids)

            # Find old demo datasets
            ds_res = await session.execute(
                select(Dataset.id).where(Dataset.created_at < cutoff)
            )
            old_ds_ids = ds_res.scalars().all()
            if old_ds_ids:
                await session.execute(delete(Dataset).where(Dataset.id.in_(old_ds_ids)))
                deleted_count += len(old_ds_ids)

            await session.commit()
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired demo records older than {max_age_hours}h.")
    except Exception as e:
        logger.error(f"Error during demo data cleanup: {e}")

    return deleted_count


def generate_experiment_csv(data: dict[str, Any]) -> str:
    """Generate formula-sanitized CSV export for model evaluation comparisons."""
    import csv

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        "model_key",
        "model_name",
        "family",
        "primary_metric",
        "ci_lower",
        "ci_upper",
        "cost_per_1k_usd",
        "latency_ms",
        "status",
        "recommendation",
    ])

    rec = data.get("recommendation", {})
    recommended_model = rec.get("recommended_candidate")

    for m in data.get("models", []):
        ci = m.get("ci_95", [None, None])
        ci_lower = f"{ci[0]:.4f}" if ci and ci[0] is not None else ""
        ci_upper = f"{ci[1]:.4f}" if ci and len(ci) > 1 and ci[1] is not None else ""
        is_rec = "RECOMMENDED" if m.get("model_key") == recommended_model else ""

        row = [
            sanitize_csv_cell(m.get("model_key", "")),
            sanitize_csv_cell(m.get("model_name", "")),
            sanitize_csv_cell(m.get("family", "")),
            sanitize_csv_cell(f"{m.get('primary_metric', 0.0):.4f}"),
            sanitize_csv_cell(ci_lower),
            sanitize_csv_cell(ci_upper),
            sanitize_csv_cell(f"{m.get('cost_per_1k', 0.0):.4f}"),
            sanitize_csv_cell(f"{m.get('latency_ms', 0.0):.1f}"),
            sanitize_csv_cell(m.get("status", "")),
            sanitize_csv_cell(is_rec),
        ]
        writer.writerow(row)

    return output.getvalue()
