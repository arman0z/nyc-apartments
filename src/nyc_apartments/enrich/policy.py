from __future__ import annotations

import re

from nyc_apartments.models import Listing


RENT_STABILIZED_RE = re.compile(r"\brent[-\s]?stabili[sz]ed\b|\bstabili[sz]ed\b", re.I)
FOUR_TWENTY_ONE_A_RE = re.compile(r"\b421[-\s]?a\b", re.I)
J51_RE = re.compile(r"\bj[-\s]?51\b", re.I)
GOOD_CAUSE_EXEMPTION_TEXT_RE = re.compile(
    r"\b(?:condo|co-op|cooperative|owner[-\s]?occupied|single[-\s]?family|two[-\s]?family)\b",
    re.I,
)
REGULATION_SIGNAL_FLAGS = {
    "verified_source_claim",
    "building_registered_rs",
    "tax_benefit_421a_local",
    "tax_benefit_421a_open_data",
    "tax_benefit_j51",
    "pre_1974_6plus_candidate",
}


def infer_policy_flags(*texts: str) -> list[str]:
    combined = " ".join(text for text in texts if text)
    flags: list[str] = []

    if RENT_STABILIZED_RE.search(combined):
        flags.append("verified_source_claim")
    if FOUR_TWENTY_ONE_A_RE.search(combined):
        flags.append("source_text_421a")
    if J51_RE.search(combined):
        flags.append("source_text_j51")
    if GOOD_CAUSE_EXEMPTION_TEXT_RE.search(combined):
        flags.append("source_text_good_cause_exemption")

    flags.append("unit_status_unknown")
    return flags


def apply_policy_classification(listings: list[Listing]) -> None:
    for listing in listings:
        classify_good_cause(listing)


def classify_good_cause(listing: Listing) -> None:
    if "good_cause_likely" in listing.policy_flags:
        return
    if "source_text_good_cause_exemption" in listing.policy_flags:
        _add_flag(listing.policy_flags, "good_cause_unlikely")
        return
    if REGULATION_SIGNAL_FLAGS.intersection(listing.policy_flags):
        _add_flag(listing.policy_flags, "good_cause_unclear")
        return
    if listing.bbl:
        _add_flag(listing.policy_flags, "good_cause_unclear")


def _add_flag(flags: list[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)
