from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nyc_apartments.enrich.tax_benefits import TaxBenefitResult, enrich_tax_benefits
from nyc_apartments.models import Listing


class TaxBenefitTests(unittest.TestCase):
    def test_local_421a_bbl_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            local_421a = tmp_path / "421a.csv"
            local_421a.write_text("bbl,source,notes\n3011130043,test,example\n")
            tax_cache = tmp_path / "tax-cache.json"
            tax_cache.write_text(
                '{"3011130043": {"bbl": "3011130043", "flags": [], "evidence": []}}\n'
            )
            listing = Listing(
                source="streeteasy",
                source_listing_id="1",
                source_url="https://example.com",
                title="Test",
                bbl="3011130043",
            )

            enrich_tax_benefits(
                [listing],
                cache_path=tax_cache,
                local_421a_bbls_path=local_421a,
            )

            self.assertIn("tax_benefit_421a_local", listing.policy_flags)

    def test_open_data_421a_signal_from_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            listing = Listing(
                source="streeteasy",
                source_listing_id="1",
                source_url="https://example.com",
                title="Test",
                bbl="3011130043",
            )

            with patch(
                "nyc_apartments.enrich.tax_benefits.lookup_tax_benefits",
                return_value=TaxBenefitResult(
                    bbl="3011130043",
                    flags=["tax_benefit_421a_open_data"],
                    evidence=["421-a exemption record year=2026"],
                ),
            ):
                enrich_tax_benefits(
                    [listing],
                    cache_path=tmp_path / "tax-cache.json",
                    local_421a_bbls_path=tmp_path / "missing.csv",
                )

            self.assertIn("tax_benefit_421a_open_data", listing.policy_flags)


if __name__ == "__main__":
    unittest.main()
