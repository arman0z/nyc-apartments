from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha1
from typing import Any
from urllib.parse import urlparse
import re

from nyc_apartments.config import Criteria
from nyc_apartments.enrich.policy import infer_policy_flags
from nyc_apartments.models import Listing


PRICE_RE = re.compile(r"\$?\s*([0-9][0-9,]*)")
UNIT_RE = re.compile(r"(?:#|apt\.?|unit)\s*([a-z0-9-]+)", re.I)


def normalize_items(source: str, items: list[dict[str, Any]], criteria: Criteria) -> list[Listing]:
    listings = [normalize_item(source, item) for item in items]
    for listing in listings:
        listing.dedupe_key = build_dedupe_key(listing)
        listing.history_key = build_history_key(listing)
        score_listing(listing, criteria)
    return listings


def normalize_item(source: str, item: dict[str, Any]) -> Listing:
    source_url = _first_string(
        item,
        "url",
        "sourceUrl",
        "source_url",
        "link",
        "listingUrl",
        "listing_url",
    )
    title = _first_string(
        item,
        "title",
        "name",
        "marketplace_listing_title",
        "heading",
        "descriptionTitle",
    )
    raw_address = _first_string(
        item,
        "address",
        "rawAddress",
        "location",
        "locationName",
        "formattedAddress",
    )
    if not raw_address:
        raw_address = _nested_string(item, ("location_text", "text"))
    if not raw_address:
        raw_address = _nested_string(item, ("location", "reverse_geocode", "city_page", "display_name"))
    if not raw_address:
        raw_address = ", ".join(
            part
            for part in [
                _nested_string(item, ("location", "reverse_geocode", "city")),
                _nested_string(item, ("location", "reverse_geocode", "state")),
            ]
            if part
        )

    description = _first_string(item, "description", "body", "postBody", "redacted_description")
    if not description:
        description = _nested_string(item, ("redacted_description", "text"))

    source_listing_id = _first_string(item, "id", "listingId", "postId", "pid")
    if not source_listing_id:
        source_listing_id = stable_id(source, source_url or title or repr(item))

    price = parse_price(_first_present(item, "price", "priceDisplay", "rent", "listing_price", "amount"))
    bedrooms = parse_number(_first_present(item, "bedrooms", "beds", "bedroomCount"))
    if bedrooms is None:
        bedrooms = parse_bedrooms_from_text(title)
    bathrooms = parse_number(_first_present(item, "bathrooms", "baths", "bathroomCount"))
    square_feet = parse_int(_first_present(item, "squareFeet", "sqft", "areaSqft", "area_sqft"))

    tags = _listish(_first_present(item, "tags", "labels", "amenities"))
    no_fee = _infer_no_fee(title, description, tags)

    scraped_at = (
        _first_string(item, "scrapedAt", "scraped_at", "postedAt", "posted_at")
        or datetime.now(UTC).isoformat()
    )
    normalized_address = normalize_address(raw_address)
    building_key = normalize_building_key(raw_address)
    unit = extract_unit(raw_address)

    policy_flags = infer_policy_flags(title, raw_address, description, " ".join(tags))
    quality_flags = infer_quality_flags(source, raw_address, price)

    return Listing(
        source=source,
        source_listing_id=source_listing_id,
        source_url=source_url,
        title=title
        or raw_address
        or _first_string(item, "neighborhood", "area", "subarea")
        or source_url
        or "(untitled listing)",
        raw_address=raw_address,
        normalized_address=normalized_address,
        building_key=building_key,
        unit=unit,
        neighborhood=_first_string(item, "neighborhood", "area", "subarea"),
        city=_first_string(item, "city"),
        state=_first_string(item, "state"),
        zip=_first_string(item, "zip", "postalCode", "postal_code"),
        latitude=parse_number(_first_present(item, "latitude", "lat")),
        longitude=parse_number(_first_present(item, "longitude", "lng", "lon")),
        price=price,
        gross_price=price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        square_feet=square_feet,
        no_fee=no_fee,
        broker_fee_known=no_fee is not None,
        available_at=_first_string(item, "availableAt", "available_at", "availability"),
        first_seen_at=scraped_at,
        last_seen_at=scraped_at,
        scraped_at=scraped_at,
        agent_name=_first_string(item, "agentName", "brokerName", "sellerName"),
        brokerage=_first_string(item, "agentBrokerage", "brokerage"),
        contact_url=source_url,
        policy_flags=policy_flags,
        quality_flags=quality_flags,
        raw=item,
    )


def parse_price(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, dict):
        for key in (
            "amount",
            "amount_zeros_stripped",
            "formatted_amount",
            "formatted_amount_zeros_stripped",
            "value",
        ):
            parsed = parse_price(value.get(key))
            if parsed is not None:
                return parsed
        return None
    match = PRICE_RE.search(str(value))
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def parse_int(value: Any) -> int | None:
    parsed = parse_number(value)
    if parsed is None:
        return None
    return int(parsed)


def parse_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, int | float):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    if not match:
        return None
    return float(match.group(0))


def parse_bedrooms_from_text(value: str) -> float | None:
    if not value:
        return None
    lowered = value.lower()
    if "studio" in lowered:
        return 0.0
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:br|bed|beds|bedroom|bedrooms)\b", lowered)
    if not match:
        return None
    return float(match.group(1))


def normalize_address(address: str) -> str:
    return re.sub(r"\s+", " ", address).strip().lower()


def normalize_building_key(address: str) -> str:
    without_unit = re.sub(r"\s+(?:#|apt\.?|unit)\s*[a-z0-9-]+", "", address, flags=re.I)
    without_trailing_hash = re.sub(r"\s*#[a-z0-9-]+$", "", without_unit, flags=re.I)
    return normalize_address(without_trailing_hash)


def extract_unit(address: str) -> str:
    match = UNIT_RE.search(address)
    if not match:
        return ""
    return match.group(1).upper()


def build_dedupe_key(listing: Listing) -> str:
    if listing.normalized_address:
        parts = [
            listing.normalized_address,
            listing.unit,
            str(listing.price or ""),
            str(listing.bedrooms or ""),
        ]
        return stable_id("address", "|".join(parts))
    if listing.source_url:
        parsed = urlparse(listing.source_url)
        return stable_id("url", f"{parsed.netloc}{parsed.path}")
    return stable_id(listing.source, listing.source_listing_id)


def build_history_key(listing: Listing) -> str:
    if looks_specific_building_key(listing.building_key):
        return stable_id(
            "building-unit",
            "|".join(
                [
                    listing.building_key,
                    listing.unit,
                    str(listing.bedrooms or ""),
                ]
            ),
        )
    if listing.source_url:
        parsed = urlparse(listing.source_url)
        return stable_id("url", f"{parsed.netloc}{parsed.path}")
    return stable_id(listing.source, listing.source_listing_id)


def looks_specific_building_key(value: str) -> bool:
    return bool(value and "," not in value and re.search(r"^\s*\d+(?:-\d+)?[a-z]?\s+\S+", value, re.I))


def stable_id(namespace: str, value: str) -> str:
    return f"{namespace}_{sha1(value.encode('utf-8')).hexdigest()[:16]}"


def score_listing(listing: Listing, criteria: Criteria) -> None:
    score = 0
    reasons: list[str] = []

    if criteria.max_price is not None and listing.price is not None:
        if listing.price <= criteria.max_price:
            score += 30
            reasons.append("within price target")
        else:
            score -= 20
            reasons.append("over price target")

    if criteria.min_bedrooms is not None and listing.bedrooms is not None:
        if listing.bedrooms >= criteria.min_bedrooms:
            score += 20
            reasons.append("bedroom target")

    if listing.no_fee:
        score += 5
        reasons.append("no-fee signal")

    meaningful_policy_flags = [flag for flag in listing.policy_flags if flag != "unit_status_unknown"]
    if meaningful_policy_flags:
        score += 20
        reasons.append("policy signal")

    if "missing_price" in listing.quality_flags:
        score -= 15
    if "missing_address" in listing.quality_flags:
        score -= 10
    if "facebook_manual_review" in listing.quality_flags:
        score -= 5

    listing.score = score
    listing.score_reasons = reasons


def infer_quality_flags(source: str, address: str, price: int | None) -> list[str]:
    flags: list[str] = []
    if price is None:
        flags.append("missing_price")
    if not address:
        flags.append("missing_address")
    if source == "facebook":
        flags.append("facebook_manual_review")
    if source == "craigslist":
        flags.append("craigslist_manual_review")
    if price is not None and price < 1200:
        flags.append("suspicious_low_price")
    return flags


def _infer_no_fee(title: str, description: str, tags: list[str]) -> bool | None:
    combined = " ".join([title, description, *tags]).lower()
    if "no fee" in combined or "no-fee" in combined:
        return True
    if "broker fee" in combined:
        return False
    return None


def _first_string(item: dict[str, Any], *keys: str) -> str:
    value = _first_present(item, *keys)
    if value is None:
        return ""
    if isinstance(value, dict | list):
        return ""
    return str(value).strip()


def _first_present(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return None


def _nested_string(item: dict[str, Any], path: tuple[str, ...]) -> str:
    value: Any = item
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return ""
        value = value[key]
    if value is None:
        return ""
    return str(value).strip()


def _listish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
