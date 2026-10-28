"""
Unit tests for NecroGit TabPFN Bitrot Forensics Service.
Hacktoberfest 2026 Week 4 ("Ghost in the Machine")
"""

import os
import pytest
from server import BitrotForensicsModel, load_benchmark_data, DEFAULT_BENCHMARK_PATH

def test_load_benchmark_data():
    """Verify historical cemetery benchmark dataset loads with expected shape."""
    df = load_benchmark_data(DEFAULT_BENCHMARK_PATH)
    assert not df.empty
    assert len(df) >= 30
    assert "bitrot_risk_class" in df.columns
    assert "cve_vulnerability_risk" in df.columns
    assert "days_inactive" in df.columns

def test_audit_critical_bitrot():
    """Verify ancient, unmaintained repository (>10 years inactive) is flagged as Critical or High bitrot."""
    model = BitrotForensicsModel()
    res = model.audit_repo(
        repo_name="dead_urlfetch_vintage",
        language="python",
        days_inactive=5100,  # ~14 years
        dependency_count=6,
        unpinned_ratio=0.85,
        cyclomatic_entropy=42.0,
    )
    assert res["repo_name"] == "dead_urlfetch_vintage"
    assert res["bitrot_risk_class"] in ["Critical", "High"]
    assert res["cve_vulnerability_risk"] > 0.6
    assert res["zombie_dependencies_detected"] >= 4
    assert "confidence_probabilities" in res

def test_audit_healthy_modern_repo():
    """Verify freshly maintained repository is classified as Low bitrot."""
    model = BitrotForensicsModel()
    res = model.audit_repo(
        repo_name="modern_active_microservice",
        language="python",
        days_inactive=12,
        dependency_count=5,
        unpinned_ratio=0.0,
        cyclomatic_entropy=10.0,
    )
    assert res["bitrot_risk_class"] == "Low"
    assert res["cve_vulnerability_risk"] < 0.25
    assert res["zombie_dependencies_detected"] == 0

def test_forecast_time_of_death_ancient():
    """Verify time-of-death calculation for a vintage 2012 codebase."""
    model = BitrotForensicsModel()
    res = model.forecast_time_of_death(days_inactive=5110)
    assert res["estimated_death_year"] <= 2013
    assert res["years_in_crypt"] >= 13.0
    assert "Ancient Spectral Codebase" in res["ghost_status"]
    assert res["resurrection_urgency"] == "High"

def test_forecast_time_of_death_recent():
    """Verify time-of-death calculation for a recently dormant codebase."""
    model = BitrotForensicsModel()
    res = model.forecast_time_of_death(days_inactive=400)
    assert res["estimated_death_year"] >= 2024
    assert res["years_in_crypt"] < 2.0
    assert "Dormant" in res["ghost_status"]

def test_bitrot_index_scale():
    """Verify bitrot index is bounded in [0.0, 1.0]."""
    model = BitrotForensicsModel()
    res = model.audit_repo("test", "python", 2000, 4, 0.5, 20.0)
    assert 0.0 <= res["bitrot_index"] <= 1.0
