from __future__ import annotations

import unittest

from nyc_apartments.config import Criteria
from nyc_apartments.normalize import (
    build_history_key,
    normalize_building_key,
    normalize_items,
    parse_bedrooms_from_text,
    parse_price,
)


class NormalizeTests(unittest.TestCase):
    def test_parse_price_handles_strings_and_facebook_objects(self) -> None:
        self.assertEqual(parse_price("$4,400"), 4400)
        self.assertEqual(
            parse_price({"formatted_amount_zeros_stripped": "$3,800"}),
            3800,
        )

    def test_parse_bedrooms_from_text(self) -> None:
        self.assertEqual(parse_bedrooms_from_text("2 bedroom apartment"), 2.0)
        self.assertEqual(parse_bedrooms_from_text("studio in Astoria"), 0.0)

    def test_normalize_building_key_removes_unit(self) -> None:
        self.assertEqual(normalize_building_key("456 Demo Avenue #2B"), "456 demo avenue")
        self.assertEqual(normalize_building_key("21-43 29th Street #2D"), "21-43 29th street")

    def test_rent_stabilized_source_claim_gets_policy_flag(self) -> None:
        listings = normalize_items(
            "streeteasy",
            [
                {
                    "id": "1",
                    "url": "https://example.com/1",
                    "title": "Rent stabilized 2 bed",
                    "address": "1 Test Street #2A",
                    "price": 4000,
                    "bedrooms": 2,
                }
            ],
            Criteria(min_bedrooms=2, max_price=4400),
        )

        self.assertEqual(len(listings), 1)
        self.assertIn("verified_source_claim", listings[0].policy_flags)
        self.assertGreater(listings[0].score, 0)

    def test_facebook_reverse_geocode_location(self) -> None:
        listings = normalize_items(
            "facebook",
            [
                {
                    "id": "1",
                    "listingUrl": "https://example.com/1",
                    "marketplace_listing_title": "2 bedroom apartment",
                    "listing_price": {"amount": "3800.00"},
                    "location": {
                        "reverse_geocode": {
                            "city": "Queens",
                            "state": "NY",
                        }
                    },
                }
            ],
            Criteria(min_bedrooms=2, max_price=4400),
        )

        self.assertEqual(listings[0].raw_address, "Queens, NY")
        self.assertIn("facebook_manual_review", listings[0].quality_flags)

    def test_history_key_ignores_price_for_specific_unit(self) -> None:
        listings = normalize_items(
            "streeteasy",
            [
                {
                    "id": "1",
                    "url": "https://example.com/1",
                    "title": "2 bed",
                    "address": "1 Test Street #2A",
                    "price": 4500,
                    "bedrooms": 2,
                },
                {
                    "id": "2",
                    "url": "https://example.com/2",
                    "title": "2 bed",
                    "address": "1 Test Street #2A",
                    "price": 4300,
                    "bedrooms": 2,
                },
            ],
            Criteria(min_bedrooms=2, max_price=4500),
        )

        self.assertEqual(build_history_key(listings[0]), build_history_key(listings[1]))
        self.assertNotEqual(listings[0].dedupe_key, listings[1].dedupe_key)

    def test_good_cause_exemption_text_gets_conservative_label(self) -> None:
        listings = normalize_items(
            "facebook",
            [
                {
                    "id": "1",
                    "listingUrl": "https://example.com/1",
                    "marketplace_listing_title": "2 bedroom condo rental",
                    "listing_price": {"amount": "3800.00"},
                    "location": "New York, New York",
                }
            ],
            Criteria(min_bedrooms=2, max_price=4500),
        )

        self.assertIn("source_text_good_cause_exemption", listings[0].policy_flags)


if __name__ == "__main__":
    unittest.main()
