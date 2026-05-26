from __future__ import annotations

from datetime import UTC, datetime
import unittest

from nyc_apartments.history import apply_listing_history
from nyc_apartments.models import Listing


class HistoryTests(unittest.TestCase):
    def test_new_listing_gets_change_flag(self) -> None:
        listing = Listing(
            source="streeteasy",
            source_listing_id="1",
            source_url="https://example.com/1",
            title="New",
            price=4400,
            bedrooms=2,
            history_key="listing-1",
        )

        tracked = apply_listing_history(
            [listing],
            [],
            datetime(2026, 5, 26, tzinfo=UTC),
        )

        self.assertEqual(tracked[0].change_flags, ["new_listing"])
        self.assertEqual(tracked[0].last_seen_at, "2026-05-26T00:00:00+00:00")

    def test_price_drop_is_tracked_against_previous_price(self) -> None:
        listing = Listing(
            source="streeteasy",
            source_listing_id="1",
            source_url="https://example.com/1",
            title="Drop",
            price=4300,
            bedrooms=2,
            history_key="listing-1",
        )
        previous = [
            {
                "source": "streeteasy",
                "source_listing_id": "1",
                "source_url": "https://example.com/1",
                "title": "Drop",
                "price": 4500,
                "first_seen_at": "2026-05-20T00:00:00+00:00",
                "history_key": "listing-1",
                "status": "active",
            }
        ]

        tracked = apply_listing_history(
            [listing],
            previous,
            datetime(2026, 5, 26, tzinfo=UTC),
        )

        self.assertIn("price_drop", tracked[0].change_flags)
        self.assertEqual(tracked[0].previous_price, 4500)
        self.assertEqual(tracked[0].price_delta, -200)
        self.assertEqual(tracked[0].price_history[-1]["delta"], -200)

    def test_missing_listing_becomes_removed_after_threshold(self) -> None:
        previous = [
            {
                "source": "streeteasy",
                "source_listing_id": "1",
                "source_url": "https://example.com/1",
                "title": "Gone",
                "price": 4200,
                "history_key": "listing-1",
                "missing_runs": 1,
                "status": "missing",
            }
        ]

        tracked = apply_listing_history(
            [],
            previous,
            datetime(2026, 5, 26, tzinfo=UTC),
            missing_before_removed_runs=2,
        )

        self.assertEqual(tracked[0].status, "removed")
        self.assertEqual(tracked[0].change_flags, ["removed_listing"])
        self.assertEqual(tracked[0].removed_at, "2026-05-26T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
