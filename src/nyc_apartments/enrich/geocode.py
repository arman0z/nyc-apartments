from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
import json
import re

from nyc_apartments.models import Listing


GEOSearch_URL = "https://geosearch.planninglabs.nyc/v2/search"
STREET_ADDRESS_RE = re.compile(r"^\s*\d+(?:-\d+)?[a-z]?\s+\S+", re.I)


@dataclass(slots=True)
class GeocodeResult:
    query: str
    label: str = ""
    bbl: str = ""
    bin: str = ""
    borough: str = ""
    neighborhood: str = ""
    zip: str = ""
    latitude: float | None = None
    longitude: float | None = None
    confidence: float | None = None


def enrich_geocodes(listings: list[Listing], cache_path: str | Path) -> None:
    cache = load_geocode_cache(cache_path)
    changed = False

    for listing in listings:
        if listing.bbl or not looks_like_nyc_street_address(listing.building_key):
            continue
        result = cache.get(listing.building_key)
        if result is None:
            result = geocode_address(listing.building_key)
            cache[listing.building_key] = result
            changed = True
        apply_geocode_result(listing, result)

    if changed:
        save_geocode_cache(cache_path, cache)


def looks_like_nyc_street_address(value: str) -> bool:
    if not value:
        return False
    if "," in value:
        return False
    return bool(STREET_ADDRESS_RE.search(value))


def geocode_address(query: str) -> GeocodeResult:
    params = urlencode({"text": query, "size": 1})
    with urlopen(f"{GEOSearch_URL}?{params}", timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    features = payload.get("features") or []
    if not features:
        return GeocodeResult(query=query)

    feature = features[0]
    properties = feature.get("properties") or {}
    pad = (properties.get("addendum") or {}).get("pad") or {}
    coordinates = (feature.get("geometry") or {}).get("coordinates") or []

    longitude = coordinates[0] if len(coordinates) >= 1 else None
    latitude = coordinates[1] if len(coordinates) >= 2 else None

    return GeocodeResult(
        query=query,
        label=properties.get("label") or "",
        bbl=str(pad.get("bbl") or ""),
        bin=str(pad.get("bin") or ""),
        borough=properties.get("borough") or "",
        neighborhood=properties.get("neighbourhood") or "",
        zip=properties.get("postalcode") or "",
        latitude=latitude,
        longitude=longitude,
        confidence=_optional_float(properties.get("confidence")),
    )


def apply_geocode_result(listing: Listing, result: GeocodeResult) -> None:
    if result.bbl and not listing.bbl:
        listing.bbl = result.bbl
    if result.bin and not listing.bin:
        listing.bin = result.bin
    if result.borough and not listing.borough:
        listing.borough = result.borough
    if result.neighborhood and not listing.neighborhood:
        listing.neighborhood = result.neighborhood
    if result.zip and not listing.zip:
        listing.zip = result.zip
    if result.latitude is not None and listing.latitude is None:
        listing.latitude = result.latitude
    if result.longitude is not None and listing.longitude is None:
        listing.longitude = result.longitude


def load_geocode_cache(path: str | Path) -> dict[str, GeocodeResult]:
    cache_path = Path(path)
    if not cache_path.exists():
        return {}
    raw = json.loads(cache_path.read_text())
    return {
        key: GeocodeResult(**value)
        for key, value in raw.items()
        if isinstance(value, dict)
    }


def save_geocode_cache(path: str | Path, cache: dict[str, GeocodeResult]) -> None:
    cache_path = Path(path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({key: asdict(value) for key, value in cache.items()}, indent=2, sort_keys=True)
        + "\n"
    )


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
