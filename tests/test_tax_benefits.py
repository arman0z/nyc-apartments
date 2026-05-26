from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nyc_apartments.enrich.tax_benefits import enrich_tax_benefits
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


if __name__ == "__main__":
    unittest.main()
