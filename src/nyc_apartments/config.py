from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import tomllib


@dataclass(slots=True)
class Criteria:
    min_bedrooms: float | None = None
    max_price: int | None = None
    areas: list[str] = field(default_factory=list)
    neighborhoods: list[str] = field(default_factory=list)
    strict_location_sources: list[str] = field(default_factory=list)
    allowed_location_terms: list[str] = field(default_factory=list)
    excluded_location_terms: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SourceConfig:
    name: str
    type: str
    enabled: bool
    actor_id: str | None = None
    input: dict[str, Any] = field(default_factory=dict)
    max_items: int | None = None
    timeout_seconds: int = 600


@dataclass(slots=True)
class PolicyConfig:
    building_signals_path: str = "data/policy/building-signals.csv"
    local_421a_bbls_path: str = "data/policy/421a-bbls.csv"


@dataclass(slots=True)
class EnrichmentConfig:
    geocode_nyc_addresses: bool = False
    tax_benefit_lookup: bool = False
    geocode_cache_path: str = "data/geocode-cache.json"
    tax_benefit_cache_path: str = "data/tax-benefit-cache.json"


@dataclass(slots=True)
class HistoryConfig:
    missing_before_removed_runs: int = 2


@dataclass(slots=True)
class AppConfig:
    criteria: Criteria
    sources: list[SourceConfig]
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    enrichment: EnrichmentConfig = field(default_factory=EnrichmentConfig)
    history: HistoryConfig = field(default_factory=HistoryConfig)


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    raw = tomllib.loads(config_path.read_text())

    criteria_raw = raw.get("criteria", {})
    criteria = Criteria(
        min_bedrooms=_optional_float(criteria_raw.get("min_bedrooms")),
        max_price=_optional_int(criteria_raw.get("max_price")),
        areas=list(criteria_raw.get("areas", [])),
        neighborhoods=list(criteria_raw.get("neighborhoods", [])),
        strict_location_sources=list(criteria_raw.get("strict_location_sources", [])),
        allowed_location_terms=list(criteria_raw.get("allowed_location_terms", [])),
        excluded_location_terms=list(criteria_raw.get("excluded_location_terms", [])),
    )

    sources = [
        SourceConfig(
            name=str(source["name"]),
            type=str(source.get("type", "apify")),
            enabled=bool(source.get("enabled", True)),
            actor_id=source.get("actor_id"),
            input=dict(source.get("input", {})),
            max_items=_optional_int(source.get("max_items")),
            timeout_seconds=int(source.get("timeout_seconds", 600)),
        )
        for source in raw.get("sources", [])
    ]

    policy_raw = raw.get("policy", {})
    policy = PolicyConfig(
        building_signals_path=str(
            policy_raw.get("building_signals_path", "data/policy/building-signals.csv")
        ),
        local_421a_bbls_path=str(policy_raw.get("local_421a_bbls_path", "data/policy/421a-bbls.csv")),
    )

    enrichment_raw = raw.get("enrichment", {})
    enrichment = EnrichmentConfig(
        geocode_nyc_addresses=bool(enrichment_raw.get("geocode_nyc_addresses", False)),
        tax_benefit_lookup=bool(enrichment_raw.get("tax_benefit_lookup", False)),
        geocode_cache_path=str(enrichment_raw.get("geocode_cache_path", "data/geocode-cache.json")),
        tax_benefit_cache_path=str(
            enrichment_raw.get("tax_benefit_cache_path", "data/tax-benefit-cache.json")
        ),
    )

    history_raw = raw.get("history", {})
    history = HistoryConfig(
        missing_before_removed_runs=int(history_raw.get("missing_before_removed_runs", 2)),
    )

    return AppConfig(
        criteria=criteria,
        sources=sources,
        policy=policy,
        enrichment=enrichment,
        history=history,
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
