from __future__ import annotations

import unittest

from nyc_apartments.models import Listing
from nyc_apartments.render.markdown import END_MARKER, START_MARKER, render_feed


class RenderTests(unittest.TestCase):
    def test_render_feed_has_markers_and_listing_link(self) -> None:
        feed = render_feed(
            [
                Listing(
                    source="streeteasy",
                    source_listing_id="1",
                    source_url="https://example.com/listing",
                    title="Test Listing",
                    price=4000,
                    bedrooms=2,
                    raw_address="1 Test Street",
                    score=50,
                )
            ]
        )

        self.assertIn(START_MARKER, feed)
        self.assertIn(END_MARKER, feed)
        self.assertIn("### High Priority", feed)
        self.assertIn("[Test Listing](https://example.com/listing)", feed)

    def test_render_feed_splits_new_and_price_drops(self) -> None:
        feed = render_feed(
            [
                Listing(
                    source="streeteasy",
                    source_listing_id="1",
                    source_url="https://example.com/new",
                    title="New Listing",
                    price=4400,
                    bedrooms=2,
                    raw_address="1 Test Street",
                    score=55,
                    change_flags=["new_listing"],
                ),
                Listing(
                    source="streeteasy",
                    source_listing_id="2",
                    source_url="https://example.com/drop",
                    title="Price Drop",
                    price=4300,
                    previous_price=4500,
                    price_delta=-200,
                    bedrooms=2,
                    raw_address="2 Test Street",
                    score=60,
                    change_flags=["price_drop"],
                    bbl="3011130043",
                    bin="3027197",
                ),
            ]
        )

        self.assertIn("### New Listings", feed)
        self.assertIn("### Price Drops", feed)
        self.assertIn("-$200 from $4,500", feed)
        self.assertIn("BBL 3011130043, BIN 3027197", feed)


if __name__ == "__main__":
    unittest.main()
