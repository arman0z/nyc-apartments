from __future__ import annotations

from nyc_apartments.models import Listing


def dedupe_listings(listings: list[Listing]) -> list[Listing]:
    by_key: dict[str, Listing] = {}

    for listing in sorted(listings, key=lambda item: item.score, reverse=True):
        existing = by_key.get(listing.dedupe_key)
        if existing is None:
            by_key[listing.dedupe_key] = listing
            continue
        existing.quality_flags = sorted(set(existing.quality_flags + ["duplicate_sources"]))
        existing.score = max(existing.score, listing.score)

    return sorted(by_key.values(), key=lambda item: item.score, reverse=True)
