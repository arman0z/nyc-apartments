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

Last updated: 2026-05-26T03:24:33+00:00
Active listings: 2 (streeteasy: 2)
Missing/removed tracked: 4

### High Priority

| Score | Price | Beds | Area/address | Source | BBL/BIN | Signals | Change | Link |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 95 | $3,900 | 2 | 456 Demo Avenue #2B | streeteasy | BBL 3041800058, BIN 3414892 | verified_source_claim, building_registered_rs, tax_benefit_active, pre_1974_6plus_candidate, good_cause_unclear | new | [Rent stabilized 2 bed in elevator building](https://streeteasy.com/building/stabilized-demo/2b) |
| 60 | $4,200 | 2 | 123 Demo Street #4A | streeteasy | BBL 1019087504, BIN 1087830 | good_cause_unclear | new | [No Fee 2 Bed Near Prospect Park](https://streeteasy.com/building/demo-building/4a) |

### New Listings

| Score | Price | Beds | Area/address | Source | BBL/BIN | Signals | Change | Link |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 95 | $3,900 | 2 | 456 Demo Avenue #2B | streeteasy | BBL 3041800058, BIN 3414892 | verified_source_claim, building_registered_rs, tax_benefit_active, pre_1974_6plus_candidate, good_cause_unclear | new | [Rent stabilized 2 bed in elevator building](https://streeteasy.com/building/stabilized-demo/2b) |
| 60 | $4,200 | 2 | 123 Demo Street #4A | streeteasy | BBL 1019087504, BIN 1087830 | good_cause_unclear | new | [No Fee 2 Bed Near Prospect Park](https://streeteasy.com/building/demo-building/4a) |

### Price Drops

No listings.

### Policy Signals

| Score | Price | Beds | Area/address | Source | BBL/BIN | Signals | Change | Link |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 95 | $3,900 | 2 | 456 Demo Avenue #2B | streeteasy | BBL 3041800058, BIN 3414892 | verified_source_claim, building_registered_rs, tax_benefit_active, pre_1974_6plus_candidate, good_cause_unclear | new | [Rent stabilized 2 bed in elevator building](https://streeteasy.com/building/stabilized-demo/2b) |

### Manual Review

No listings.

### Missing Or Removed

| Score | Price | Beds | Area/address | Source | BBL/BIN | Signals | Change | Link |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | $2,895 | 2 | 224 East 135th Street #1212S | streeteasy | BBL 2023197501, BIN 2129362 | missing_from_latest_run | missing 1 run | [224 East 135th Street #1212S](https://streeteasy.com/building/the-arches-nyc/1212s) |
| 50 | $4,275 | 2 | 532 Neptune Avenue #307H | streeteasy | BBL 3072737501, BIN 3426198 | missing_from_latest_run | missing 1 run | [532 Neptune Avenue #307H](https://streeteasy.com/building/sky-three-residences-club/307h?featured=1) |
| 50 | $4,300 | 2 | 228a Prospect Park West #2A | streeteasy | BBL 3011130043, BIN 3027197 | missing_from_latest_run | missing 1 run | [228a Prospect Park West #2A](https://streeteasy.com/building/228a-prospect-park-west-brooklyn/2a?featured=1) |
| 45 | $2,350 | 2 | New York, New York | facebook | n/a | facebook_manual_review, missing_from_latest_run | missing 1 run | [2 Beds 1 Bath - House](https://www.facebook.com/marketplace/item/1940915213055279) |


<!-- NYC_APARTMENT_FEED_END -->
