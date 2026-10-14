"""Tests for security hardening, CSV formula sanitization, rate limits, and demo cleanup."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from openswitch.config import settings
from openswitch.db import session_context
from openswitch.models import Dataset, Experiment, init_db
from openswitch.security import (
    check_kill_switch,
    check_visitor_rate_limit,
    cleanup_old_demo_data,
    escape_html_text,
    generate_experiment_csv,
    sanitize_csv_cell,
)


@pytest.fixture(autouse=True)
async def ensure_db():
    await init_db()


def test_sanitize_csv_cell_neutralizes_formula_injection():
    """Verify dangerous formula prefixes are escaped with a leading single quote (CWE-1236)."""
    # Formula payloads
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("=cmd|'/C calc'!A0") == "'=cmd|'/C calc'!A0"
    assert sanitize_csv_cell("+100") == "'+100"
    assert sanitize_csv_cell("-200") == "'-200"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("\t=SUM(1,2)") == "'\t=SUM(1,2)"
    assert (
        sanitize_csv_cell('  =HYPERLINK("http://evil.com")') == '\'  =HYPERLINK("http://evil.com")'
    )

    # Benign inputs
    assert sanitize_csv_cell("Normal text") == "Normal text"
    assert sanitize_csv_cell("gemma-2b-local") == "gemma-2b-local"
    assert sanitize_csv_cell("95.4%") == "95.4%"
    assert sanitize_csv_cell(123) == "123"
    assert sanitize_csv_cell(None) == ""
    assert sanitize_csv_cell("") == ""


def test_escape_html_text():
    """Verify HTML special characters are properly escaped to prevent XSS."""
    assert (
        escape_html_text("<script>alert('xss')</script>")
        == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    )
    assert escape_html_text("Hello & Goodbye") == "Hello &amp; Goodbye"
    assert escape_html_text('"Quoted"') == "&quot;Quoted&quot;"
    assert escape_html_text(None) == ""


def test_check_kill_switch_behavior(monkeypatch):
    """Verify kill switch raises 503 when enabled and passes when disabled."""
    monkeypatch.setattr(settings, "kill_switch", False)
    check_kill_switch()  # Should not raise

    monkeypatch.setattr(settings, "kill_switch", True)
    with pytest.raises(HTTPException) as exc_info:
        check_kill_switch()
    assert exc_info.value.status_code == 503
    assert "paused via kill switch" in exc_info.value.detail


@pytest.mark.asyncio
async def test_visitor_rate_limiting(monkeypatch):
    """Verify rate limit check blocks visitor exceeding max_experiments_per_visitor_day in demo mode."""
    monkeypatch.setattr(settings, "demo_mode", True)
    monkeypatch.setattr(settings, "max_experiments_per_visitor_day", 2)

    session_hash = f"test_session_{uuid.uuid4().hex[:8]}"

    # With 0 experiments, passes
    await check_visitor_rate_limit(session_hash)

    # Seed 2 experiments under this session hash
    ds_id = f"ds_{uuid.uuid4().hex[:8]}"
    async with session_context() as session:
        ds = Dataset(
            id=ds_id,
            name="Rate Limit DS",
            task_json="{}",
            n_rows=5,
            sha256="dummy",
        )
        session.add(ds)
        for i in range(2):
            session.add(
                Experiment(
                    id=f"exp_{uuid.uuid4().hex[:8]}",
                    dataset_id=ds_id,
                    session_hash=session_hash,
                    name=f"Exp {i}",
                    config_json="{}",
                    config_hash="h",
                    status="completed",
                )
            )
        await session.commit()

    # With 2 experiments, limit reached -> raises 429
    with pytest.raises(HTTPException) as exc_info:
        await check_visitor_rate_limit(session_hash)
    assert exc_info.value.status_code == 429
    assert "rate limit exceeded" in exc_info.value.detail


@pytest.mark.asyncio
async def test_cleanup_old_demo_data(monkeypatch):
    """Verify demo data cleanup deletes datasets and experiments older than cutoff."""
    monkeypatch.setattr(settings, "demo_mode", True)

    old_date = datetime.now(UTC) - timedelta(hours=30)
    old_ds_id = f"old_ds_{uuid.uuid4().hex[:8]}"
    old_exp_id = f"old_exp_{uuid.uuid4().hex[:8]}"

    async with session_context() as session:
        ds = Dataset(
            id=old_ds_id,
            name="Old Dataset",
            task_json="{}",
            n_rows=1,
            sha256="dummy",
            created_at=old_date,
        )
        exp = Experiment(
            id=old_exp_id,
            dataset_id=old_ds_id,
            name="Old Experiment",
            config_json="{}",
            config_hash="h",
            status="completed",
            created_at=old_date,
        )
        session.add(ds)
        session.add(exp)
        await session.commit()

    deleted = await cleanup_old_demo_data(max_age_hours=24)
    assert deleted >= 1


def test_generate_experiment_csv_export():
    """Verify CSV report generation includes headers, values, and sanitized cells."""
    sample_data = {
        "recommendation": {"recommended_candidate": "gemma-2b-local"},
        "models": [
            {
                "model_key": "gemma-2b-local",
                "model_name": "Gemma 2 2B (Local)",
                "family": "Gemma 2",
                "primary_metric": 0.8824,
                "ci_95": [0.7843, 0.9608],
                "cost_per_1k": 0.0,
                "latency_ms": 42.1,
                "status": "PASS",
            },
            {
                "model_key": "=evil_calc",
                "model_name": "Formula Model",
                "family": "Test",
                "primary_metric": 0.5000,
                "ci_95": [0.3, 0.7],
                "cost_per_1k": 0.05,
                "latency_ms": 100.0,
                "status": "FAIL",
            },
        ],
    }

    csv_text = generate_experiment_csv(sample_data)
    lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")

    assert "model_key,model_name,family,primary_metric" in lines[0]
    assert "gemma-2b-local,Gemma 2 2B (Local)" in lines[1]
    assert "RECOMMENDED" in lines[1]

    # Formula cell must be sanitized with leading quote
    assert "'=evil_calc" in lines[2]
