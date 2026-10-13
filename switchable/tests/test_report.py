"""Tests for standalone HTML and JSON report generator (T-026)."""

import json
from pathlib import Path
import pytest

from openswitch.report import (
    escape,
    generate_pareto_svg,
    generate_report_files,
    generate_standalone_html,
)


def test_html_escape_security():
    """Verify that malicious script tags and XSS payloads are strictly escaped."""
    xss_payloads = [
        "<script>alert('xss')</script>",
        '"><img src=x onerror=alert(1)>',
        "<a href='javascript:alert(1)'>click</a>",
        "& < > \" '",
    ]
    for p in xss_payloads:
        escaped = escape(p)
        assert "<script>" not in escaped
        assert "<img" not in escaped
        assert "&lt;" in escaped or "&amp;" in escaped or "&gt;" in escaped or "&quot;" in escaped


def test_generate_standalone_html_no_external_resources():
    """Ensure report contains zero external CDN scripts or stylesheet links."""
    mock_data = {
        "experiment_id": "exp-12345",
        "git_commit": "abcdef12",
        "created_at": "2026-10-14T00:00:00Z",
        "dataset_name": "Test Dataset",
        "test_size": 50,
        "primary_metric": "composite",
        "recommendation": {
            "decision": "switch_immediately",
            "recommended_candidate": "gemma-9b-local",
            "headline": "Safe Switch: gemma-9b-local satisfies 85% threshold",
            "details": "Model achieves 91.2% point estimate.",
            "threshold": 0.85,
            "eligible_candidates": [
                {
                    "model_key": "gemma-9b-local",
                    "point_estimate": 0.912,
                    "ci_lower": 0.865,
                    "ci_upper": 0.954,
                    "cost_per_1k": 0.0,
                    "latency_p50_ms": 65.0,
                    "error_rate": 0.0,
                }
            ],
            "ineligible_candidates": [],
        },
        "worst_examples": [
            {
                "idx": 4,
                "input": "<b>urgent input</b>",
                "reference": "<script>alert(1)</script>",
                "candidate_output": "\"><img src=x>",
                "reason": "Failed extraction",
            }
        ],
        "calibration": {
            "tier": "reliable",
            "cohen_kappa": 0.848,
            "banner_message": "Judge is reliable (Cohen's kappa >= 0.60).",
        },
        "reproducibility": {
            "seed": 1337,
            "bootstrap_resamples": 10000,
        },
    }

    html_out = generate_standalone_html(mock_data)

    # Must contain critical sections
    assert "Open-Switch Evaluation Report" in html_out
    assert "Quality vs Cost Pareto Frontier" in html_out
    assert "Evaluated Candidates" in html_out
    assert "Interactive Monthly Savings Calculator" in html_out
    assert "Worst-10 Diagnostic Cases" in html_out
    assert "Reproducibility & Audit Trail" in html_out

    # Must escape XSS in worst examples
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_out
    assert "&lt;img src=x&gt;" in html_out or "&quot;&gt;&lt;img" in html_out

    # Zero external CDN links
    assert "https://cdn." not in html_out
    assert "http://" not in html_out or "http://www.w3.org" in html_out  # SVG namespace allowed
    assert "<script src=" not in html_out
    assert "<link rel=\"stylesheet\" href=\"http" not in html_out


def test_generate_report_files(tmp_path: Path):
    """Verify writing report files to disk."""
    mock_data = {
        "experiment_id": "exp-test",
        "dataset_name": "Bank77",
        "recommendation": {"decision": "no_safe_switch", "headline": "No Switch", "details": "Below threshold"},
    }
    html_file = tmp_path / "report.html"
    json_file = tmp_path / "report.json"

    h_path, j_path = generate_report_files(mock_data, html_file, json_file)
    assert h_path.exists()
    assert j_path.exists()
    assert "Open-Switch Evaluation Report" in h_path.read_text(encoding="utf-8")
    loaded = json.loads(j_path.read_text(encoding="utf-8"))
    assert loaded["experiment_id"] == "exp-test"
