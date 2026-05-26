from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


PUBLIC_OMIT_FIELDS = {
    "raw",
    "agent_name",
    "brokerage",
    "contact_url",
    "score",
    "score_reasons",
}


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
    missing_runs: int = 0
    removed_at: str = ""
    relisted_at: str = ""
    agent_name: str = ""
    brokerage: str = ""
    contact_url: str = ""
    dedupe_key: str = ""
    history_key: str = ""
    previous_price: int | None = None
    price_delta: int | None = None
    price_changed_at: str = ""
    price_history: list[dict[str, Any]] = field(default_factory=list)
    change_flags: list[str] = field(default_factory=list)
    policy_flags: list[str] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)
    score: int = 0
    score_reasons: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for field_name in PUBLIC_OMIT_FIELDS:
            payload.pop(field_name, None)
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


def listing_from_dict(payload: dict[str, Any]) -> Listing:
    listing = Listing(
        source=str(payload.get("source") or ""),
        source_listing_id=str(payload.get("source_listing_id") or ""),
        source_url=str(payload.get("source_url") or ""),
        title=str(payload.get("title") or "(untitled listing)"),
    )
    field_names = {field.name for field in fields(Listing)}
    for key, value in payload.items():
        if key in field_names and key not in {"source", "source_listing_id", "source_url", "title", "raw"}:
            setattr(listing, key, value)
    return listing
