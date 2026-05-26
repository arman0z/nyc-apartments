from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from nyc_apartments.models import Listing, listing_from_dict
from nyc_apartments.normalize import build_history_key


def apply_listing_history(
    active_listings: list[Listing],
    previous_payloads: list[dict[str, Any]],
    generated_at: datetime | None = None,
    *,
    missing_before_removed_runs: int = 2,
) -> list[Listing]:
    generated_at = generated_at or datetime.now(UTC)
    seen_at = generated_at.isoformat(timespec="seconds")
    previous_by_key = {
        _history_key_for_payload(payload): payload
        for payload in previous_payloads
        if _history_key_for_payload(payload)
    }

    merged: list[Listing] = []
    active_keys: set[str] = set()

    for listing in active_listings:
        if not listing.history_key:
            listing.history_key = build_history_key(listing)
        previous = previous_by_key.pop(listing.history_key, None)
        apply_active_history(listing, previous, seen_at)
        active_keys.add(listing.history_key)
        merged.append(listing)

    for payload in previous_by_key.values():
        if str(payload.get("status") or "active") == "removed":
            continue
        missing = listing_from_dict(payload)
        if not missing.history_key:
            missing.history_key = build_history_key(missing)
        if missing.history_key in active_keys:
            continue
        apply_missing_history(missing, seen_at, missing_before_removed_runs)
        merged.append(missing)

    return sorted(
        merged,
        key=lambda listing: (
            listing.status != "active",
            listing.status == "removed",
            -listing.score,
            listing.price or 0,
        ),
    )


def apply_active_history(listing: Listing, previous: dict[str, Any] | None, seen_at: str) -> None:
    listing.status = "active"
    listing.last_seen_at = seen_at
    listing.missing_runs = 0
    listing.removed_at = ""
    listing.change_flags = []

    if previous is None:
        listing.first_seen_at = listing.first_seen_at or seen_at
        _add_flag(listing.change_flags, "new_listing")
        listing.score += 5
        _add_flag(listing.score_reasons, "new listing")
        return

    listing.first_seen_at = str(previous.get("first_seen_at") or listing.first_seen_at or seen_at)
    previous_status = str(previous.get("status") or "active")
    if previous_status in {"missing", "removed"}:
        listing.relisted_at = seen_at
        _add_flag(listing.change_flags, "relisted_listing")
        _add_flag(listing.score_reasons, "relisted")
    else:
        listing.relisted_at = str(previous.get("relisted_at") or "")

    previous_price = _optional_int(previous.get("price"))
    if previous_price is not None and listing.price is not None and previous_price != listing.price:
        listing.previous_price = previous_price
        listing.price_delta = listing.price - previous_price
        listing.price_changed_at = seen_at
        listing.price_history = _price_history(previous)
        listing.price_history.append(
            {
                "seen_at": seen_at,
                "previous_price": previous_price,
                "price": listing.price,
                "delta": listing.price - previous_price,
            }
        )
        if listing.price < previous_price:
            _add_flag(listing.change_flags, "price_drop")
            listing.score += 10
            _add_flag(listing.score_reasons, "price drop")
        else:
            _add_flag(listing.change_flags, "price_increase")
    else:
        listing.previous_price = _optional_int(previous.get("previous_price"))
        listing.price_delta = _optional_int(previous.get("price_delta"))
        listing.price_changed_at = str(previous.get("price_changed_at") or "")
        listing.price_history = _price_history(previous)


def apply_missing_history(
    listing: Listing,
    seen_at: str,
    missing_before_removed_runs: int,
) -> None:
    listing.missing_runs += 1
    listing.status = "removed" if listing.missing_runs >= missing_before_removed_runs else "missing"
    if listing.status == "removed" and not listing.removed_at:
        listing.removed_at = seen_at
    listing.change_flags = ["removed_listing" if listing.status == "removed" else "missing_listing"]
    _add_flag(listing.quality_flags, "missing_from_latest_run")


def _history_key_for_payload(payload: dict[str, Any]) -> str:
    key = str(payload.get("history_key") or "")
    if key:
        return key
    return build_history_key(listing_from_dict(payload))


def _price_history(previous: dict[str, Any]) -> list[dict[str, Any]]:
    raw = previous.get("price_history")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _add_flag(flags: list[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)
