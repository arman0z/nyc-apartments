from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Listing:
    source: str
    source_listing_id: str
    source_url: str
    title: str
    raw_address: str = ""
    normalized_address: str = ""
    building_key: str = ""
    unit: str = ""
    borough: str = ""
    neighborhood: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    latitude: float | None = None
    longitude: float | None = None
    bbl: str = ""
    bin: str = ""
    price: int | None = None
    net_effective_price: int | None = None
    gross_price: int | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    square_feet: int | None = None
    no_fee: bool | None = None
    broker_fee_known: bool | None = None
    available_at: str = ""
    first_seen_at: str = ""
    last_seen_at: str = ""
    scraped_at: str = ""
    status: str = "active"
    agent_name: str = ""
    brokerage: str = ""
    contact_url: str = ""
    dedupe_key: str = ""
    policy_flags: list[str] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)
    score: int = 0
    score_reasons: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("raw", None)
        return payload

    @property
    def display_price(self) -> str:
        if self.price is None:
            return "n/a"
        return f"${self.price:,}"

    @property
    def display_beds(self) -> str:
        if self.bedrooms is None:
            return "n/a"
        if self.bedrooms == 0:
            return "Studio"
        if float(self.bedrooms).is_integer():
            return str(int(self.bedrooms))
        return str(self.bedrooms)
