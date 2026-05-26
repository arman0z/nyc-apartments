from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv

from nyc_apartments.models import Listing


@dataclass(slots=True)
class BuildingSignal:
    building_key: str
    bbl: str
    bin: str
    flags: list[str]
    notes: str = ""


def load_building_signals(path: str | Path) -> list[BuildingSignal]:
    signal_path = Path(path)
    if not signal_path.exists():
        return []

    with signal_path.open(newline="") as file:
        rows = csv.DictReader(file)
        return [
            BuildingSignal(
                building_key=(row.get("building_key") or "").strip().lower(),
                bbl=(row.get("bbl") or "").strip(),
                bin=(row.get("bin") or "").strip(),
                flags=_parse_flags(row.get("flags") or ""),
                notes=(row.get("notes") or "").strip(),
            )
            for row in rows
        ]


def apply_building_signals(listings: list[Listing], signals: list[BuildingSignal]) -> None:
    by_building_key = {
        signal.building_key: signal for signal in signals if signal.building_key
    }
    by_bbl = {signal.bbl: signal for signal in signals if signal.bbl}

    for listing in listings:
        signal = None
        if listing.bbl:
            signal = by_bbl.get(listing.bbl)
        if signal is None and listing.building_key:
            signal = by_building_key.get(listing.building_key)
        if signal is None:
            continue

        for flag in signal.flags:
            if flag not in listing.policy_flags:
                listing.policy_flags.append(flag)
        if signal.bbl and not listing.bbl:
            listing.bbl = signal.bbl
        if signal.bin and not listing.bin:
            listing.bin = signal.bin
        if signal.flags:
            listing.score += 20
            if "building policy signal" not in listing.score_reasons:
                listing.score_reasons.append("building policy signal")


def _parse_flags(raw: str) -> list[str]:
    return [part.strip() for part in raw.replace(",", ";").split(";") if part.strip()]
