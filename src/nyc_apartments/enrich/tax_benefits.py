from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import csv
import json

from nyc_apartments.models import Listing


J51_ABATEMENT_URL = "https://data.cityofnewyork.us/resource/rgyu-ii48.json"


@dataclass(slots=True)
class TaxBenefitResult:
    bbl: str
    flags: list[str]
    evidence: list[str]


def enrich_tax_benefits(
    listings: list[Listing],
    *,
    cache_path: str | Path,
    local_421a_bbls_path: str | Path,
) -> None:
    cache = load_tax_cache(cache_path)
    local_421a_bbls = load_local_421a_bbls(local_421a_bbls_path)
    changed = False

    for listing in listings:
        if not listing.bbl:
            continue

        result = cache.get(listing.bbl)
        if result is None:
            try:
                result = lookup_tax_benefits(listing.bbl)
            except Exception as exc:
                result = TaxBenefitResult(
                    bbl=listing.bbl,
                    flags=[],
                    evidence=[f"tax benefit lookup failed: {type(exc).__name__}"],
                )
            cache[listing.bbl] = result
            changed = True

        flags = list(result.flags)
        if listing.bbl in local_421a_bbls:
            flags.append("tax_benefit_421a_local")

        for flag in sorted(set(flags)):
            if flag not in listing.policy_flags:
                listing.policy_flags.append(flag)
        if flags:
            listing.score += 20
            if "tax benefit signal" not in listing.score_reasons:
                listing.score_reasons.append("tax benefit signal")

    if changed:
        save_tax_cache(cache_path, cache)


def lookup_tax_benefits(bbl: str) -> TaxBenefitResult:
    params = urlencode(
        {
            "$limit": 1,
            "$select": "parid,taxyr,tccode,yrbegdt,yrenddt",
            "$where": f"parid='{bbl}' AND (tccode='J51' OR tccode='J51   ')",
            "$order": "taxyr DESC",
        }
    )
    with urlopen(f"{J51_ABATEMENT_URL}?{params}", timeout=20) as response:
        rows = json.loads(response.read().decode("utf-8"))

    flags: list[str] = []
    evidence: list[str] = []
    if rows:
        flags.append("tax_benefit_j51")
        latest = rows[0]
        evidence.append(
            "J-51 abatement record"
            + (f" taxyr={latest.get('taxyr')}" if latest.get("taxyr") else "")
        )

    return TaxBenefitResult(bbl=bbl, flags=flags, evidence=evidence)


def load_local_421a_bbls(path: str | Path) -> set[str]:
    bbl_path = Path(path)
    if not bbl_path.exists():
        return set()

    with bbl_path.open(newline="") as file:
        reader = csv.DictReader(file)
        return {
            (row.get("bbl") or "").strip()
            for row in reader
            if (row.get("bbl") or "").strip()
        }


def load_tax_cache(path: str | Path) -> dict[str, TaxBenefitResult]:
    cache_path = Path(path)
    if not cache_path.exists():
        return {}
    raw = json.loads(cache_path.read_text())
    return {
        key: TaxBenefitResult(**value)
        for key, value in raw.items()
        if isinstance(value, dict)
    }


def save_tax_cache(path: str | Path, cache: dict[str, TaxBenefitResult]) -> None:
    cache_path = Path(path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({key: asdict(value) for key, value in cache.items()}, indent=2, sort_keys=True)
        + "\n"
    )
