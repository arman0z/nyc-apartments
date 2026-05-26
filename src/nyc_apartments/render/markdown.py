from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from nyc_apartments.models import Listing


START_MARKER = "<!-- NYC_APARTMENT_FEED_START -->"
END_MARKER = "<!-- NYC_APARTMENT_FEED_END -->"


def render_feed(listings: list[Listing], generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.now(UTC)
    active_listings = [listing for listing in listings if listing.status == "active"]
    inactive_listings = [listing for listing in listings if listing.status != "active"]
    source_counts = Counter(listing.source for listing in active_listings)
    source_summary = ", ".join(f"{source}: {count}" for source, count in sorted(source_counts.items()))
    source_summary = source_summary or "no active listings"

    lines = [
        START_MARKER,
        "## Current Listing Feed",
        "",
        f"Last updated: {generated_at.isoformat(timespec='seconds')}",
        f"Active listings: {len(active_listings)} ({source_summary})",
        f"Missing/removed tracked: {len(inactive_listings)}",
        "",
    ]

    sections = [
        ("High Priority", high_priority_listings(active_listings), 15),
        ("New Listings", changed_listings(active_listings, "new_listing"), 15),
        ("Price Drops", changed_listings(active_listings, "price_drop"), 15),
        ("Policy Signals", policy_signal_listings(active_listings), 15),
        ("Manual Review", manual_review_listings(active_listings), 15),
        ("Missing Or Removed", inactive_listings, 15),
    ]

    for title, section_listings, limit in sections:
        lines.extend(render_section(title, section_listings, limit))

    lines.extend(["", END_MARKER, ""])
    return "\n".join(lines)


def render_listings_page(listings: list[Listing], generated_at: datetime | None = None) -> str:
    return "# Listings\n\n" + render_feed(listings, generated_at)


def replace_generated_section(readme: str, feed: str) -> str:
    if START_MARKER not in readme or END_MARKER not in readme:
        return readme.rstrip() + "\n\n" + feed

    before = readme.split(START_MARKER, 1)[0].rstrip()
    after = readme.split(END_MARKER, 1)[1].lstrip()
    if not after:
        return before + "\n\n" + feed.rstrip() + "\n"
    return before + "\n\n" + feed.rstrip() + "\n\n" + after


def _interesting_flags(listing: Listing) -> list[str]:
    return [
        flag
        for flag in listing.policy_flags + listing.quality_flags
        if flag != "unit_status_unknown"
    ]


def high_priority_listings(listings: list[Listing]) -> list[Listing]:
    return [
        listing
        for listing in sorted(listings, key=lambda item: item.score, reverse=True)
        if listing.score >= 50 and not is_manual_review(listing)
    ]


def changed_listings(listings: list[Listing], flag: str) -> list[Listing]:
    return [
        listing
        for listing in sorted(listings, key=lambda item: item.score, reverse=True)
        if flag in listing.change_flags
    ]


def policy_signal_listings(listings: list[Listing]) -> list[Listing]:
    return [
        listing
        for listing in sorted(listings, key=lambda item: item.score, reverse=True)
        if strong_policy_flags(listing)
    ]


def manual_review_listings(listings: list[Listing]) -> list[Listing]:
    return [
        listing
        for listing in sorted(listings, key=lambda item: item.score, reverse=True)
        if is_manual_review(listing)
    ]


def render_section(title: str, listings: list[Listing], limit: int) -> list[str]:
    lines = [f"### {title}", ""]
    if not listings:
        lines.extend(["No listings.", ""])
        return lines

    lines.extend(
        [
            "| Score | Price | Beds | Area/address | Source | BBL/BIN | Signals | Change | Link |",
            "| ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for listing in listings[:limit]:
        lines.append(render_listing_row(listing))
    lines.append("")
    return lines


def render_listing_row(listing: Listing) -> str:
    area = listing.raw_address or listing.neighborhood or listing.city or "n/a"
    signals = ", ".join(_interesting_flags(listing)) or "none"
    title = _escape(listing.title[:80])
    link = f"[{title}]({listing.source_url})" if listing.source_url else title
    return " | ".join(
        [
            "| " + str(listing.score),
            listing.display_price,
            listing.display_beds,
            _escape(area),
            listing.source,
            _escape(parcel_summary(listing)),
            _escape(signals),
            _escape(change_summary(listing)),
            link + " |",
        ]
    )


def parcel_summary(listing: Listing) -> str:
    parts = []
    if listing.bbl:
        parts.append(f"BBL {listing.bbl}")
    if listing.bin:
        parts.append(f"BIN {listing.bin}")
    return ", ".join(parts) or "n/a"


def change_summary(listing: Listing) -> str:
    if "new_listing" in listing.change_flags:
        return "new"
    if listing.price_delta:
        previous = f"${listing.previous_price:,}" if listing.previous_price else "previous price"
        amount = f"${abs(listing.price_delta):,}"
        if listing.price_delta < 0:
            return f"-{amount} from {previous}"
        return f"+{amount} from {previous}"
    if listing.status == "removed":
        return "removed"
    if listing.status == "missing":
        return f"missing {listing.missing_runs} run" + ("" if listing.missing_runs == 1 else "s")
    if "relisted_listing" in listing.change_flags:
        return "relisted"
    return ""


def strong_policy_flags(listing: Listing) -> list[str]:
    return [
        flag
        for flag in listing.policy_flags
        if flag not in {"unit_status_unknown", "good_cause_unclear"}
    ]


def is_manual_review(listing: Listing) -> bool:
    return any(flag.endswith("_manual_review") for flag in listing.quality_flags)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
