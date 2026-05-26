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
        self.assertIn("[Test Listing](https://example.com/listing)", feed)


if __name__ == "__main__":
    unittest.main()
