from __future__ import annotations

import unittest

from nyc_apartments.models import Listing


class ModelTests(unittest.TestCase):
    def test_public_dict_omits_raw_and_contact_fields(self) -> None:
        payload = Listing(
            source="facebook",
            source_listing_id="1",
            source_url="https://example.com/listing",
            title="Listing",
            agent_name="Seller Name",
            brokerage="Brokerage",
            contact_url="https://example.com/contact",
            raw={"description": "full copied text"},
        ).to_dict()

        self.assertNotIn("raw", payload)
        self.assertNotIn("agent_name", payload)
        self.assertNotIn("brokerage", payload)
        self.assertNotIn("contact_url", payload)
        self.assertNotIn("score", payload)
        self.assertNotIn("score_reasons", payload)


if __name__ == "__main__":
    unittest.main()
