from __future__ import annotations

import unittest

from nyc_apartments.config import Criteria
from nyc_apartments.filters import filter_listings
from nyc_apartments.models import Listing


class FilterTests(unittest.TestCase):
    def test_strict_location_filters_facebook_drift(self) -> None:
        criteria = Criteria(
            min_bedrooms=2,
            max_price=4400,
            strict_location_sources=["facebook"],
            allowed_location_terms=["New York, New York"],
            excluded_location_terms=["Paterson"],
        )
        listings = [
            Listing(
                source="facebook",
                source_listing_id="1",
                source_url="https://example.com/1",
                title="Keep",
                raw_address="New York, New York",
                price=3000,
                bedrooms=2,
            ),
            Listing(
                source="facebook",
                source_listing_id="2",
                source_url="https://example.com/2",
                title="Drop",
                raw_address="Paterson, New Jersey",
                price=1900,
                bedrooms=3,
            ),
        ]

        self.assertEqual([listing.title for listing in filter_listings(listings, criteria)], ["Keep"])


if __name__ == "__main__":
    unittest.main()
