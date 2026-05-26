from __future__ import annotations

from nyc_apartments.config import Criteria
from nyc_apartments.models import Listing


AREA_ALIASES = {
    "manhattan": ["manhattan", "new york, new york", "new york, ny"],
    "brooklyn": ["brooklyn", "kings county"],
    "queens": ["queens", "long island city", "lic", "astoria", "sunnyside", "woodside"],
    "long island city": ["long island city", "lic"],
}


def filter_listings(listings: list[Listing], criteria: Criteria) -> list[Listing]:
    return [listing for listing in listings if matches_criteria(listing, criteria)]


def matches_criteria(listing: Listing, criteria: Criteria) -> bool:
    if criteria.max_price is not None and listing.price is not None:
        if listing.price > criteria.max_price:
            return False

    if criteria.min_bedrooms is not None and listing.bedrooms is not None:
        if listing.bedrooms < criteria.min_bedrooms:
            return False

    haystack = location_text(listing).lower()
    if any(term.lower() in haystack for term in criteria.excluded_location_terms):
        return False

    if listing.source in criteria.strict_location_sources and criteria.allowed_location_terms:
        if not any(term.lower() in haystack for term in criteria.allowed_location_terms):
            return False

    if criteria.neighborhoods:
        return any(term.lower() in haystack for term in criteria.neighborhoods)

    if criteria.areas and has_known_area(listing):
        return any(term in haystack for term in expanded_area_terms(criteria.areas))

    return True


def location_text(listing: Listing) -> str:
    return " ".join(
        part
        for part in [
            listing.raw_address,
            listing.normalized_address,
            listing.neighborhood,
            listing.borough,
            listing.city,
            listing.state,
            listing.zip,
        ]
        if part
    )


def has_known_area(listing: Listing) -> bool:
    return bool(listing.borough or listing.neighborhood or listing.city or "," in listing.raw_address)


def expanded_area_terms(areas: list[str]) -> set[str]:
    terms: set[str] = set()
    for area in areas:
        lowered = area.lower()
        terms.add(lowered)
        terms.update(AREA_ALIASES.get(lowered, []))
    return terms
