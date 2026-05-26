from __future__ import annotations

import unittest

from nyc_apartments.enrich.policy import apply_policy_classification
from nyc_apartments.models import Listing


class PolicyTests(unittest.TestCase):
    def test_good_cause_unlikely_for_text_exemption_signal(self) -> None:
        listing = Listing(
            source="facebook",
            source_listing_id="1",
            source_url="https://example.com",
            title="Condo",
            policy_flags=["source_text_good_cause_exemption", "unit_status_unknown"],
        )

        apply_policy_classification([listing])

        self.assertIn("good_cause_unlikely", listing.policy_flags)

    def test_good_cause_unclear_when_only_bbl_is_known(self) -> None:
        listing = Listing(
            source="streeteasy",
            source_listing_id="1",
            source_url="https://example.com",
            title="Apartment",
            bbl="3011130043",
            policy_flags=["unit_status_unknown"],
        )

        apply_policy_classification([listing])

        self.assertIn("good_cause_unclear", listing.policy_flags)


if __name__ == "__main__":
    unittest.main()
