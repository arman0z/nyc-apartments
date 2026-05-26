from __future__ import annotations

import unittest

from nyc_apartments.enrich.building_signals import BuildingSignal, apply_building_signals
from nyc_apartments.models import Listing


class BuildingSignalTests(unittest.TestCase):
    def test_apply_building_signals_by_building_key(self) -> None:
        listing = Listing(
            source="streeteasy",
            source_listing_id="1",
            source_url="https://example.com",
            title="Test",
            building_key="456 demo avenue",
            policy_flags=["unit_status_unknown"],
        )

        apply_building_signals(
            [listing],
            [
                BuildingSignal(
                    building_key="456 demo avenue",
                    bbl="",
                    bin="",
                    flags=["building_registered_rs", "tax_benefit_active"],
                )
            ],
        )

        self.assertIn("building_registered_rs", listing.policy_flags)
        self.assertIn("tax_benefit_active", listing.policy_flags)
        self.assertIn("building policy signal", listing.score_reasons)

    def test_pre_1974_6plus_heuristic(self) -> None:
        listing = Listing(
            source="streeteasy",
            source_listing_id="1",
            source_url="https://example.com",
            title="Test",
            building_key="456 demo avenue",
            policy_flags=["unit_status_unknown"],
        )

        apply_building_signals(
            [listing],
            [
                BuildingSignal(
                    building_key="456 demo avenue",
                    bbl="",
                    bin="",
                    flags=[],
                    year_built=1931,
                    residential_units=24,
                )
            ],
        )

        self.assertIn("pre_1974_6plus_candidate", listing.policy_flags)
        self.assertIn("building policy signal", listing.score_reasons)


if __name__ == "__main__":
    unittest.main()
