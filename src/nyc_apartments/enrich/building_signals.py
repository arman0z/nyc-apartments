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
    year_built: int | None = None
    residential_units: int | None = None
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
                year_built=_optional_int(row.get("year_built")),
                residential_units=_optional_int(
                    row.get("residential_units") or row.get("units") or row.get("unit_count")
                ),
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
        heuristic_signal = is_pre_1974_6plus(signal)
        if heuristic_signal:
            _add_flag(listing.policy_flags, "pre_1974_6plus_candidate")
        if signal.flags or heuristic_signal:
            listing.score += 20
            if "building policy signal" not in listing.score_reasons:
                listing.score_reasons.append("building policy signal")


def _parse_flags(raw: str) -> list[str]:
    return [part.strip() for part in raw.replace(",", ";").split(";") if part.strip()]


def is_pre_1974_6plus(signal: BuildingSignal) -> bool:
    if signal.year_built is None or signal.residential_units is None:
        return False
    return signal.year_built < 1974 and signal.residential_units >= 6


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(str(value).strip())


def _add_flag(flags: list[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)
