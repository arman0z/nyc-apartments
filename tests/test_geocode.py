from __future__ import annotations

import unittest

from nyc_apartments.enrich.geocode import GeocodeResult, apply_geocode_result, looks_like_nyc_street_address
from nyc_apartments.models import Listing


class GeocodeTests(unittest.TestCase):
    def test_looks_like_nyc_street_address(self) -> None:
        self.assertTrue(looks_like_nyc_street_address("228a prospect park west"))
        self.assertFalse(looks_like_nyc_street_address("New York, New York"))

    def test_apply_geocode_result(self) -> None:
        listing = Listing(
            source="streeteasy",
            source_listing_id="1",
            source_url="https://example.com",
            title="Test",
        )
        apply_geocode_result(
            listing,
            GeocodeResult(
                query="228a prospect park west",
                bbl="3011130043",
                bin="3027197",
                borough="Brooklyn",
                neighborhood="South Slope",
                zip="11215",
                latitude=40.659787,
                longitude=-73.981221,
            ),
        )

        self.assertEqual(listing.bbl, "3011130043")
        self.assertEqual(listing.bin, "3027197")
        self.assertEqual(listing.borough, "Brooklyn")


if __name__ == "__main__":
    unittest.main()
