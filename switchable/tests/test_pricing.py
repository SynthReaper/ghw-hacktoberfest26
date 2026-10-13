import pytest

from openswitch.pricing import (
    BaselinePricing,
    ModelPrice,
    is_price_stale,
    load_pricing,
)


def test_load_default_pricing():
    catalog = load_pricing()
    assert catalog.version == 1
    assert "gemma-2b-local" in catalog.models
    assert "do-llama-8b" in catalog.models
    assert catalog.baseline.label == "GPT-4o (Incumbent Baseline)"

    # Local model cost is 0.0
    local_m = catalog.get_model_price("gemma-2b-local")
    assert local_m.price_in_per_mtok == 0.0
    assert local_m.calculate_cost(1000, 500) == 0.0

    # DO Llama 8B cost: $0.15 / 1M tokens in, $0.15 / 1M out
    do_m = catalog.get_model_price("do-llama-8b")
    # 1,000,000 in + 1,000,000 out = $0.30
    assert pytest.approx(do_m.calculate_cost(1_000_000, 1_000_000), 0.0001) == 0.30


def test_staleness_detection():
    # Fresh date within 30 days of 2026-10-14
    assert is_price_stale("2026-10-14") is False
    # Stale date from past year
    assert is_price_stale("2025-01-01") is True
    # Unverified / missing
    assert is_price_stale("UNVERIFIED") is True
    assert is_price_stale(None) is True
    assert is_price_stale("invalid-date") is True


def test_custom_pricing_yaml_with_warnings(tmp_path):
    yaml_content = """
version: 1
baseline:
  label: "Custom Baseline"
  flat_cost_per_request: 0.05
models:
  fresh-model:
    price_in_per_mtok: 0.20
    price_out_per_mtok: 0.20
    verified_on: "2026-10-14"
  stale-model:
    price_in_per_mtok: 1.00
    price_out_per_mtok: 2.00
    verified_on: "2024-05-01"
"""
    p = tmp_path / "custom_pricing.yaml"
    p.write_text(yaml_content, encoding="utf-8")

    catalog = load_pricing(p)
    assert catalog.models["fresh-model"].is_stale is False
    assert catalog.models["stale-model"].is_stale is True
    assert len(catalog.warnings) == 1
    assert "stale-model" in catalog.warnings[0]

    # Baseline flat cost
    assert catalog.baseline.calculate_cost(500, 200) == 0.05
