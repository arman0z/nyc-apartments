# NYC Apartment Intelligence

Status: planning pass started on 2026-04-30.

This repo is intended to become a frequently refreshed intelligence feed for New York City apartment rentals. The near-term form factor is simple on purpose: a scheduled pipeline aggregates listings and related public housing data, analyzes them, and updates the repo's markdown so the GitHub page itself becomes the daily operating dashboard.

When generation begins, keep a clearly marked generated section in this README and put longer tables in `LISTINGS.md`. That gives the project a stable explanation while still making the README useful as a bookmark.

Working assumption: "Actify" in the initial notes means Apify, the hosted actor/scraper platform.

## Goal

Build one actionable place to answer:

- What promising NYC or nearby rentals appeared since the last run?
- Which listings match current criteria, such as 2 bedrooms under $4,500?
- Which listings have rent-stabilization or Good Cause Eviction signals?
- Which listings are likely duplicates, stale, scams, bait, or low-value?
- What changed: new listing, price drop, removed listing, relisted unit, new policy flag?

The system should preserve source links and evidence. It should avoid pretending that a building-level data signal proves a specific apartment's legal status.

## Current Recommendation

Start with a thin but serious pipeline:

1. Ingest listing data through source-specific adapters.
2. Normalize every result into one canonical listing schema.
3. Deduplicate across sources by URL, source ID, address, unit, price, and fuzzy title/address matching.
4. Enrich listings with NYC public data using address normalization, BBL, BIN, and coordinate joins.
5. Score and segment listings into a readable markdown dashboard.
6. Update markdown on a schedule, committing only when the rendered output changes.

For the first proof of concept, use Apify-backed adapters for StreetEasy and strict-filtered Facebook Marketplace so every enabled source lands in the same pipeline from the start. Keep Craigslist configured but disabled until a hard-capped ingestion path is proven.

## Documentation Map

- [Project plan](./docs/plan.md)

## Important Caveats

This project can flag likely rent-stabilized or Good Cause-relevant listings, but it cannot make a legal determination. The only reliable unit-level path is lease language, HCR/DHCR rent history, and legal review where needed.

For public GitHub output, the dashboard should link back to original listings and show compact facts. It should not republish full listing descriptions, full photo sets, or scraped personal contact data.

<!-- NYC_APARTMENT_FEED_START -->
## Current Listing Feed

Last updated: 2026-07-03T04:11:53+00:00
Active listings: 0 (no active listings)
Missing/removed tracked: 0

### High Priority

No listings.

### New Listings

No listings.

### Price Drops

No listings.

### Policy Signals

No listings.

### Manual Review

No listings.

### Missing Or Removed

No listings.


<!-- NYC_APARTMENT_FEED_END -->
