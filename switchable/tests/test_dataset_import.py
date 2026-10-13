import json

import pytest

from openswitch.datasets.importer import DatasetImporter
from openswitch.datasets.pii import scan_pii
from openswitch.datasets.provenance import (
    ProvenanceViolationError,
    resolve_provenance,
)
from openswitch.datasets.splits import compute_split


def test_splits_determinism():
    """Verify compute_split produces exact same assignments across runs with same seed."""
    seed = 42
    results_a = [compute_split(f"row_{i}", seed) for i in range(100)]
    results_b = [compute_split(f"row_{i}", seed) for i in range(100)]
    assert results_a == results_b

    # Different seed should change distribution
    diff_seed_results = [compute_split(f"row_{i}", 9999) for i in range(100)]
    assert results_a != diff_seed_results


def test_provenance_defaults():
    """Verify default train_allowed mappings per source."""
    assert resolve_provenance("human")[1] is True
    assert resolve_provenance("open_model")[1] is True
    assert resolve_provenance("closed_api")[1] is False
    assert resolve_provenance("unknown")[1] is False
    assert resolve_provenance(None)[1] is False


def test_provenance_guard_blocks_closed_api_training_without_attestation():
    """Verify Provenance Guard blocks train_allowed=True for closed_api unless attested."""
    with pytest.raises(ProvenanceViolationError) as exc_info:
        resolve_provenance("closed_api", explicit_train_allowed=True, attestation_granted=False)
    assert "Provenance Guard Block" in str(exc_info.value)
    assert "closed_api" in str(exc_info.value)

    # With explicit attestation granted, it is allowed
    src, allowed = resolve_provenance(
        "closed_api", explicit_train_allowed=True, attestation_granted=True
    )
    assert src == "closed_api"
    assert allowed is True


def test_pii_detection():
    """Verify PII scanner identifies emails, phones, SSNs, and credit cards."""
    rows = [
        {
            "id": "1",
            "input": "Contact me at alice.smith@enterprise.com or call +1 (555) 234-5678.",
            "reference": "Processed query.",
        },
        {
            "id": "2",
            "input": "My social security number is 123-45-6789.",
            "reference": "Do not charge 4111-2222-3333-4444.",
        },
    ]
    warnings = scan_pii(rows)
    types_found = {w.pii_type for w in warnings}
    assert "email" in types_found
    assert "phone" in types_found
    assert "ssn" in types_found
    assert "card" in types_found


def test_importer_valid_jsonl():
    importer = DatasetImporter(seed=1337)
    sample_jsonl = (
        json.dumps(
            {
                "id": "ex_1",
                "input": "Cancel subscription",
                "reference": "cancel_sub",
                "reference_source": "human",
            }
        )
        + "\n"
        + json.dumps(
            {
                "id": "ex_2",
                "input": "Billing inquiry",
                "reference": "billing",
                "reference_source": "closed_api",
            }
        )
        + "\n"
        + json.dumps(
            {
                "id": "ex_3",
                "input": "Track order #9921",
                "reference": "order_tracking",
                "reference_source": "open_model",
            }
        )
        + "\n"
    )
    imported = importer.import_from_bytes(sample_jsonl.encode("utf-8"), filename="test.jsonl")

    assert imported.name == "test"
    assert len(imported.rows) == 3
    assert len(imported.sha256) == 64
    assert imported.rows[0]["train_allowed"] is True  # human
    assert imported.rows[1]["train_allowed"] is False  # closed_api
    assert imported.rows[2]["train_allowed"] is True  # open_model


def test_importer_schema_validation_line_numbered_errors():
    importer = DatasetImporter()
    # Missing required 'reference' field on Line 2
    bad_jsonl = (
        json.dumps({"id": "ex_1", "input": "Hello", "reference": "World"})
        + "\n"
        + json.dumps({"id": "ex_2", "input": "Missing reference"})
        + "\n"
    )
    with pytest.raises(ValueError) as exc_info:
        importer.import_from_bytes(bad_jsonl.encode("utf-8"), filename="bad.jsonl")
    assert "Line 2" in str(exc_info.value)
    assert "'reference' is a required property" in str(exc_info.value)


def test_importer_csv_parsing():
    importer = DatasetImporter()
    csv_content = (
        "id,input,reference,reference_source\n"
        "1,What is your return policy?,30 days return,human\n"
        "2,How to reset password?,Go to settings,closed_api\n"
    )
    imported = importer.import_from_bytes(csv_content.encode("utf-8"), filename="support.csv")
    assert imported.name == "support"
    assert len(imported.rows) == 2
    assert imported.rows[0]["reference_source"] == "human"
    assert imported.rows[0]["train_allowed"] is True
    assert imported.rows[1]["reference_source"] == "closed_api"
    assert imported.rows[1]["train_allowed"] is False
