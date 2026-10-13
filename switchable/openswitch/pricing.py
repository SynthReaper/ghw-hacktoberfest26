"""Pricing loader and staleness auditor for model tokens."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml

DEFAULT_PRICING_PATH = Path(__file__).resolve().parent.parent / "specs" / "pricing.yaml"


@dataclass
class ModelPrice:
    key: str
    price_in_per_mtok: float
    price_out_per_mtok: float
    source_url: str | None = None
    verified_on: str | None = None
    is_stale: bool = False
    warning: str | None = None
    note: str | None = None

    def calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Calculate USD cost for a given token count."""
        cost_in = (tokens_in * self.price_in_per_mtok) / 1_000_000.0
        cost_out = (tokens_out * self.price_out_per_mtok) / 1_000_000.0
        return cost_in + cost_out


@dataclass
class BaselinePricing:
    label: str
    price_in_per_mtok: float | None = None
    price_out_per_mtok: float | None = None
    flat_cost_per_request: float | None = None
    source_url: str | None = None
    verified_on: str | None = None

    def calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        if self.flat_cost_per_request is not None:
            return self.flat_cost_per_request
        p_in = self.price_in_per_mtok or 0.0
        p_out = self.price_out_per_mtok or 0.0
        return (tokens_in * p_in + tokens_out * p_out) / 1_000_000.0


@dataclass
class PricingCatalog:
    version: int
    baseline: BaselinePricing
    models: dict[str, ModelPrice] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def get_model_price(self, key: str) -> ModelPrice:
        if key not in self.models:
            raise KeyError(f"Model key '{key}' not found in pricing catalog.")
        return self.models[key]


def is_price_stale(verified_on_str: str | None, max_age_days: int = 30) -> bool:
    """Check if verified date is missing or older than max_age_days."""
    if not verified_on_str or verified_on_str == "UNVERIFIED":
        return True
    try:
        verified_date = datetime.strptime(verified_on_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - verified_date).days
        return age_days > max_age_days
    except ValueError:
        return True


def load_pricing(pricing_path: Path | str = DEFAULT_PRICING_PATH) -> PricingCatalog:
    """Load pricing YAML and check for stale or unverified prices."""
    p = Path(pricing_path)
    if not p.exists():
        raise FileNotFoundError(f"Pricing file not found at: {p}")

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    version = data.get("version", 1)
    base_dict = data.get("baseline", {})
    baseline = BaselinePricing(
        label=base_dict.get("label", "Incumbent Baseline"),
        price_in_per_mtok=base_dict.get("price_in_per_mtok"),
        price_out_per_mtok=base_dict.get("price_out_per_mtok"),
        flat_cost_per_request=base_dict.get("flat_cost_per_request"),
        source_url=base_dict.get("source_url"),
        verified_on=base_dict.get("verified_on"),
    )

    models: dict[str, ModelPrice] = {}
    warnings: list[str] = []

    for key, m_data in data.get("models", {}).items():
        v_on = m_data.get("verified_on")
        p_in = float(m_data.get("price_in_per_mtok", 0.0) or 0.0)
        p_out = float(m_data.get("price_out_per_mtok", 0.0) or 0.0)
        source = m_data.get("source_url")
        note = m_data.get("note")

        stale = is_price_stale(v_on)
        warn_msg = None
        if stale:
            warn_msg = (
                f"Pricing Warning: Model '{key}' price is unverified or older than 30 days (verified_on='{v_on}'). "
                f"Please verify against provider documentation."
            )
            warnings.append(warn_msg)

        models[key] = ModelPrice(
            key=key,
            price_in_per_mtok=p_in,
            price_out_per_mtok=p_out,
            source_url=source,
            verified_on=v_on,
            is_stale=stale,
            warning=warn_msg,
            note=note,
        )

    return PricingCatalog(
        version=version,
        baseline=baseline,
        models=models,
        warnings=warnings,
    )
