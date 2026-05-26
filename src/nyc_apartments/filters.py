from __future__ import annotations

from nyc_apartments.config import Criteria
from nyc_apartments.models import Listing


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
        return any(term.lower() in haystack for term in criteria.allowed_location_terms)

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
