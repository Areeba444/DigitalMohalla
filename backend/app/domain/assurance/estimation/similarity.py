"""Similarity of a past loan to the request (FR-T-03, Overview §5.12, team decision D17).

Plain-language note: a history of small, short tool loans says less about a 30,000 PKR projector
than about another drill. Each past loan gets a similarity between 0 and 1:

    0.4 × value-band closeness (same band 1.0, next band 0.5, two bands apart 0.0)
  + 0.4 × same category (1 or 0)
  + 0.2 × duration closeness (the shorter loan length divided by the longer)

A past loan's weight is multiplied by max(0.5, similarity), so dissimilar history still counts at
least half. Rule R4 instead looks at the request similarity: the recency-weighted average of the
unfloored values, which is low when a high-value request follows only small, different loans.
All numbers come from engine.json (similarity_weighting, value_bands_pkr). Pure, no I/O.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

BANDS = ("LOW", "MEDIUM", "HIGH")


@dataclass(frozen=True)
class LoanProfile:
    category_id: int
    value_band: str
    duration_days: float


@dataclass(frozen=True)
class SimilarityParams:
    floor: float
    w_band: float
    w_category: float
    w_duration: float
    same: float
    adjacent: float
    two_apart: float

    @classmethod
    def from_config(cls, section: Mapping[str, Any]) -> "SimilarityParams":
        """`section` is trust_estimation_alg1.similarity_weighting of engine.json."""
        w, b = section["component_weights"], section["band_closeness"]
        return cls(
            floor=float(section["similarity_floor"]),
            w_band=float(w["value_band"]),
            w_category=float(w["category"]),
            w_duration=float(w["duration"]),
            same=float(b["same"]),
            adjacent=float(b["adjacent"]),
            two_apart=float(b["two_apart"]),
        )


def value_band(value_pkr: float, bands: Mapping[str, Any]) -> str:
    """`bands` is decision_policy_alg4.value_bands_pkr: LOW ≤ low_value_max < MEDIUM ≤ medium_value_max < HIGH."""
    if value_pkr < 0:
        raise ValueError("a value cannot be negative")
    if value_pkr <= bands["low_value_max"]:
        return "LOW"
    if value_pkr <= bands["medium_value_max"]:
        return "MEDIUM"
    return "HIGH"


def band_closeness(a: str, b: str, p: SimilarityParams) -> float:
    gap = abs(BANDS.index(a) - BANDS.index(b))
    return (p.same, p.adjacent, p.two_apart)[gap]


def similarity(past: LoanProfile, request: LoanProfile, p: SimilarityParams) -> float:
    """Unfloored similarity in [0, 1]."""
    if past.duration_days <= 0 or request.duration_days <= 0:
        raise ValueError("loan durations must be positive")
    duration = min(past.duration_days, request.duration_days) / max(
        past.duration_days, request.duration_days
    )
    category = 1.0 if past.category_id == request.category_id else 0.0
    return (
        p.w_band * band_closeness(past.value_band, request.value_band, p)
        + p.w_category * category
        + p.w_duration * duration
    )


def floored(raw: float, p: SimilarityParams) -> float:
    """The factor an outcome's weight is multiplied by: never below the floor, never above 1."""
    return min(1.0, max(p.floor, raw))


def request_similarity(history: Iterable[tuple[float, float]]) -> float:
    """Recency-weighted mean of unfloored similarities; `history` holds (recency weight, raw similarity).

    0.0 with no history: there is no similar evidence (rule R3 handles zero history before R4).
    """
    num = den = 0.0
    for w, s in history:
        num += w * s
        den += w
    return num / den if den > 0 else 0.0
