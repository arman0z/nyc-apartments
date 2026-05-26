from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from nyc_apartments.models import Listing


START_MARKER = "<!-- NYC_APARTMENT_FEED_START -->"
END_MARKER = "<!-- NYC_APARTMENT_FEED_END -->"


def render_feed(listings: list[Listing], generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.now(UTC)
    source_counts = Counter(listing.source for listing in listings)
    source_summary = ", ".join(f"{source}: {count}" for source, count in sorted(source_counts.items()))
    source_summary = source_summary or "no listings"

    lines = [
        START_MARKER,
        "## Current Listing Feed",
        "",
        f"Last updated: {generated_at.isoformat(timespec='seconds')}",
        f"Listings: {len(listings)} ({source_summary})",
        "",
        "| Score | Price | Beds | Area/address | Source | Signals | Link |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]

    for listing in listings[:50]:
        area = listing.raw_address or listing.neighborhood or listing.city or "n/a"
        signals = ", ".join(_interesting_flags(listing)) or "none"
        title = _escape(listing.title[:80])
        link = f"[{title}]({listing.source_url})" if listing.source_url else title
        lines.append(
            " | ".join(
                [
                    str(listing.score),
                    listing.display_price,
                    listing.display_beds,
                    _escape(area),
                    listing.source,
                    _escape(signals),
                    link,
                ]
            ).join(["| ", " |"])
        )

    lines.extend(["", END_MARKER, ""])
    return "\n".join(lines)


def render_listings_page(listings: list[Listing], generated_at: datetime | None = None) -> str:
    return "# Listings\n\n" + render_feed(listings, generated_at)


def replace_generated_section(readme: str, feed: str) -> str:
    if START_MARKER not in readme or END_MARKER not in readme:
        return readme.rstrip() + "\n\n" + feed

    before = readme.split(START_MARKER, 1)[0].rstrip()
    after = readme.split(END_MARKER, 1)[1].lstrip()
    return before + "\n\n" + feed.rstrip() + "\n\n" + after


def _interesting_flags(listing: Listing) -> list[str]:
    return [
        flag
        for flag in listing.policy_flags + listing.quality_flags
        if flag != "unit_status_unknown"
    ]


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
