from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import os

from nyc_apartments.config import AppConfig, SourceConfig, load_config
from nyc_apartments.dedupe import dedupe_listings
from nyc_apartments.enrich.building_signals import apply_building_signals, load_building_signals
from nyc_apartments.enrich.geocode import enrich_geocodes
from nyc_apartments.enrich.tax_benefits import enrich_tax_benefits
from nyc_apartments.env import load_dotenv
from nyc_apartments.filters import filter_listings
from nyc_apartments.normalize import normalize_items
from nyc_apartments.render.markdown import render_feed, render_listings_page, replace_generated_section
from nyc_apartments.sources.apify import ApifySource


def run_pipeline(
    config_path: str | Path,
    *,
    dry_run: bool,
    fixtures_dir: str | Path = "data/fixtures",
    readme_path: str | Path = "README.md",
    listings_path: str | Path = "LISTINGS.md",
    json_path: str | Path = "data/current-listings.json",
    cache_dir: str | Path = "data/source-cache",
) -> list[str]:
    load_dotenv()
    config = load_config(config_path)
    raw_by_source, source_errors = load_raw_items(
        config,
        dry_run=dry_run,
        fixtures_dir=Path(fixtures_dir),
        cache_dir=Path(cache_dir),
    )

    all_listings = []
    for source_name, raw_items in raw_by_source.items():
        all_listings.extend(normalize_items(source_name, raw_items, config.criteria))

    if config.enrichment.geocode_nyc_addresses:
        enrich_geocodes(all_listings, config.enrichment.geocode_cache_path)

    if config.enrichment.tax_benefit_lookup:
        enrich_tax_benefits(
            all_listings,
            cache_path=config.enrichment.tax_benefit_cache_path,
            local_421a_bbls_path=config.policy.local_421a_bbls_path,
        )

    apply_building_signals(
        all_listings,
        load_building_signals(config.policy.building_signals_path),
    )
    filtered_listings = filter_listings(all_listings, config.criteria)
    listings = dedupe_listings(filtered_listings)
    generated_at = datetime.now(UTC)

    json_output = Path(json_path)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps([listing.to_dict() for listing in listings], indent=2, sort_keys=True)
        + "\n"
    )

    feed = render_feed(listings, generated_at)
    listings_output = Path(listings_path)
    listings_output.write_text(render_listings_page(listings, generated_at))

    readme_output = Path(readme_path)
    readme = readme_output.read_text() if readme_output.exists() else "# NYC Apartment Intelligence\n"
    readme_output.write_text(replace_generated_section(readme, feed))

    messages = [
        f"loaded {sum(len(items) for items in raw_by_source.values())} raw items",
        f"rendered {len(listings)} deduped listings",
        f"updated {readme_output}",
        f"updated {listings_output}",
        f"updated {json_output}",
    ]
    messages.extend(f"source failed: {name}: {error}" for name, error in source_errors.items())
    return messages


def load_raw_items(
    config: AppConfig,
    *,
    dry_run: bool,
    fixtures_dir: Path,
    cache_dir: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    result: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, str] = {}
    for source in config.sources:
        if not source.enabled:
            continue
        try:
            if dry_run:
                result[source.name] = load_fixture(fixtures_dir / f"{source.name}.json")
            else:
                result[source.name] = fetch_live_source(source)
                save_source_cache(cache_dir / f"{source.name}.json", result[source.name])
        except Exception as exc:
            cached_items = load_fixture(cache_dir / f"{source.name}.json")
            result[source.name] = cached_items
            cache_note = f"; using {len(cached_items)} cached items" if cached_items else ""
            errors[source.name] = f"{type(exc).__name__}: {exc}{cache_note}"
    return result, errors


def load_fixture(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError(f"Fixture must be a list: {path}")
    return [item for item in raw if isinstance(item, dict)]


def save_source_cache(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2, sort_keys=True) + "\n")


def fetch_live_source(source: SourceConfig) -> list[dict[str, Any]]:
    if source.type != "apify":
        raise ValueError(f"Unsupported source type: {source.type}")
    token = os.environ.get("APIFY_API_TOKEN", "")
    return ApifySource(source, token).fetch()
