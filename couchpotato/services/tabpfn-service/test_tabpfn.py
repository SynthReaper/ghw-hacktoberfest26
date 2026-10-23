"""
Unit and integration tests for TabPFN-3.5 Financial Intelligence Server
Validates few-shot IRS Schedule C classification, quantile anomaly detection,
and Schedule C audit tools.
"""

import os
import pytest
from server import (
    classify_expense,
    detect_bill_spike,
    audit_schedule_c,
    load_history
)

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "data", "sample_expenses.csv")

def test_load_history():
    """Verify sample dataset loads with expected columns and non-empty rows."""
    df = load_history(SAMPLE_CSV)
    assert not df.empty
    assert "vendor" in df.columns
    assert "amount" in df.columns
    assert "tax_category" in df.columns
    assert len(df) >= 20

def test_classify_utility_expense():
    """Verify electric & gas bills are classified into Schedule C: Line 25 Utilities."""
    res = classify_expense(
        vendor="Pacific Gas & Electric",
        amount=155.00,
        description="Commercial electric and gas monthly statement",
        history_csv_path=SAMPLE_CSV
    )
    assert res["predicted_category"] == "Schedule C: Line 25 Utilities"
    assert res["is_deductible"] is True
    assert res["confidence"] > 0.4
    assert "Schedule C: Line 25 Utilities" in res["class_probabilities"]

def test_classify_office_expense():
    """Verify cloud and SaaS infrastructure are classified into Schedule C: Line 18 Office Expense."""
    res = classify_expense(
        vendor="AWS Cloud Infrastructure",
        amount=340.00,
        description="Compute EC2 instances and cloud storage backup",
        history_csv_path=SAMPLE_CSV
    )
    assert res["predicted_category"] == "Schedule C: Line 18 Office Expense"
    assert res["is_deductible"] is True
    assert res["confidence"] > 0.4

def test_classify_advertising_expense():
    """Verify digital ads are classified into Schedule C: Line 8 Advertising."""
    res = classify_expense(
        vendor="Google Ads",
        amount=420.00,
        description="Pay-per-click search marketing campaign",
        history_csv_path=SAMPLE_CSV
    )
    assert res["predicted_category"] == "Schedule C: Line 8 Advertising"
    assert res["is_deductible"] is True

def test_classify_coworking_rent():
    """Verify coworking and lease payments are classified into Schedule C: Line 20 Rent or Lease."""
    res = classify_expense(
        vendor="WeWork Coworking",
        amount=550.00,
        description="Dedicated office workspace monthly fee",
        history_csv_path=SAMPLE_CSV
    )
    assert res["predicted_category"] == "Schedule C: Line 20 Rent or Lease"
    assert res["is_deductible"] is True

def test_detect_bill_spike_normal():
    """Verify standard utility bill is NOT flagged as an anomaly/spike."""
    res = detect_bill_spike(
        vendor="Pacific Gas & Electric",
        current_amount=146.50,
        history_csv_path=SAMPLE_CSV
    )
    assert res["is_spike"] is False
    assert res["anomaly_score"] < 0.5
    assert res["current_amount"] == 146.50
    assert res["expected_range"][0] <= res["current_amount"] <= res["expected_range"][1]

def test_detect_bill_spike_abnormal_surge():
    """Verify an 80% surge in PG&E bill triggers a high anomaly score and spike alert."""
    res = detect_bill_spike(
        vendor="Pacific Gas & Electric",
        current_amount=285.00,  # ~90% above median ~148
        history_csv_path=SAMPLE_CSV
    )
    assert res["is_spike"] is True
    assert res["anomaly_score"] >= 0.5
    assert res["percent_change_vs_median"] > 50.0
    assert "anomalous surge" in res["explanation"].lower()

def test_audit_schedule_c():
    """Verify aggregate Schedule C write-off report and sloth hours saved."""
    res = audit_schedule_c(history_csv_path=SAMPLE_CSV)
    assert res["grand_total_usd"] > 1000.0
    assert res["total_receipts"] >= 20
    assert res["hours_saved_from_chores"] > 15.0
    assert "Schedule C: Line 25 Utilities" in res["category_breakdown"]
    assert "Schedule C: Line 18 Office Expense" in res["category_breakdown"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
