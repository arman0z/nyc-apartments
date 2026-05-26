from __future__ import annotations

import re


RENT_STABILIZED_RE = re.compile(r"\brent[-\s]?stabili[sz]ed\b|\bstabili[sz]ed\b", re.I)
FOUR_TWENTY_ONE_A_RE = re.compile(r"\b421[-\s]?a\b", re.I)
J51_RE = re.compile(r"\bj[-\s]?51\b", re.I)


def infer_policy_flags(*texts: str) -> list[str]:
    combined = " ".join(text for text in texts if text)
    flags: list[str] = []

    if RENT_STABILIZED_RE.search(combined):
        flags.append("verified_source_claim")
    if FOUR_TWENTY_ONE_A_RE.search(combined):
        flags.append("source_text_421a")
    if J51_RE.search(combined):
        flags.append("source_text_j51")

    flags.append("unit_status_unknown")
    return flags
