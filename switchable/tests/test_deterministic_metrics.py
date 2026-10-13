import pytest

from openswitch.metrics.field_accuracy import evaluate_field_accuracy
from openswitch.metrics.json_valid import is_valid_json
from openswitch.metrics.labels import calculate_classification_metrics
from openswitch.metrics.schema_valid import is_schema_valid


@pytest.mark.parametrize(
    "raw_input,expected_valid,expected_parsed",
    [
        ('{"status": "ok"}', True, {"status": "ok"}),
        ('```json\n{"status": "ok"}\n```', True, {"status": "ok"}),
        ('```\n{"count": 42}\n```', True, {"count": 42}),
        ('  ```JSON\n{"key": "val"}\n```  ', True, {"key": "val"}),
        ('{"bad": json,}', False, None),
        ("", False, None),
        (None, False, None),
    ],
)
def test_json_valid_table_driven(raw_input, expected_valid, expected_parsed):
    valid, parsed = is_valid_json(raw_input)
    assert valid == expected_valid
    assert parsed == expected_parsed


def test_schema_valid_rules():
    schema = {
        "type": "object",
        "required": ["category", "priority"],
        "additionalProperties": False,
        "properties": {
            "category": {"enum": ["billing", "bug", "feature"]},
            "priority": {"enum": ["low", "high"]},
        },
    }

    # Valid matching
    valid, _, errors = is_schema_valid('{"category": "billing", "priority": "high"}', schema)
    assert valid is True
    assert len(errors) == 0

    # Missing required field
    valid, _, errors = is_schema_valid('{"category": "billing"}', schema)
    assert valid is False
    assert any("priority" in e for e in errors)

    # Extra keys rejected by additionalProperties=False
    valid, _, errors = is_schema_valid(
        '{"category": "bug", "priority": "low", "extra": 123}', schema
    )
    assert valid is False
    assert any("extra" in e for e in errors)

    # Wrong enum value
    valid, _, errors = is_schema_valid('{"category": "unsupported_cat", "priority": "low"}', schema)
    assert valid is False


@pytest.mark.parametrize(
    "cand,ref,critical,expected_critical_composite",
    [
        # Exact match
        (
            '{"category": "billing", "priority": "low"}',
            '{"category": "billing", "priority": "low"}',
            ["category", "priority"],
            1.0,
        ),
        # Case insensitive match: "Low" vs "low"
        (
            '{"category": "Billing", "priority": "LOW"}',
            '{"category": "billing", "priority": "low"}',
            ["category", "priority"],
            1.0,
        ),
        # One critical field mismatch
        (
            '{"category": "billing", "priority": "high"}',
            '{"category": "billing", "priority": "low"}',
            ["category", "priority"],
            0.0,
        ),
        # Markdown fenced input
        (
            '```json\n{"category": "billing", "priority": "low"}\n```',
            '{"category": "billing", "priority": "low"}',
            ["category"],
            1.0,
        ),
        # Invalid JSON candidate
        ("Invalid string", '{"category": "billing", "priority": "low"}', ["category"], 0.0),
    ],
)
def test_field_accuracy_table_driven(cand, ref, critical, expected_critical_composite):
    res = evaluate_field_accuracy(cand, ref, critical_fields=critical)
    assert res["composite_critical_fields_correct"] == expected_critical_composite


def test_classification_labels_and_macro_f1():
    references = ["billing", "bug", "account", "billing"]
    predictions = ['"billing"', "Bug", "other", "BILLING"]

    # 3 out of 4 correct ('billing', 'bug', 'billing' correct; 'account' vs 'other' wrong)
    metrics = calculate_classification_metrics(predictions, references)
    assert metrics["label_accuracy"] == 0.75
    assert 0.0 < metrics["macro_f1"] < 1.0

    # Perfect match test
    perf_metrics = calculate_classification_metrics(["A", "B", "C"], ["A", "B", "C"])
    assert perf_metrics["label_accuracy"] == 1.0
    assert perf_metrics["macro_f1"] == 1.0
