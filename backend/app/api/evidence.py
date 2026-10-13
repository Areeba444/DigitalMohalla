"""Evidence summary for the lender's screen (W1, TC-100; FR-T-01, FR-T-08, NFR-U-01).

Turns a stored assessment row into the API's AssessmentOut. The stored indirect evidence names the
people on each community path by user id; the response carries their display names instead, so no
user id of a third person leaves the API. Rows written by the Slice A stub have no evidence detail,
so `verified_loans` and `community` stay empty for them. Pure: names are looked up by the caller.
"""

from collections.abc import Mapping
from typing import Any

from app.api import schemas

_PLAIN = [f for f in schemas.AssessmentOut.model_fields if f not in ("verified_loans", "community")]


def _paths(assessment: Mapping[str, Any]) -> list[dict[str, Any]]:
    paths: list[dict[str, Any]] = (assessment.get("indirect_evidence") or {}).get("paths") or []
    return paths


def intermediaries(assessment: Mapping[str, Any]) -> list[str]:
    """User ids between the lender and the borrower on the stored paths."""
    return sorted({n for p in _paths(assessment) for n in p["nodes"][1:-1]})


def assessment_out(
    assessment: Mapping[str, Any], names: Mapping[str, str]
) -> schemas.AssessmentOut:
    direct = assessment.get("direct_evidence") or {}
    indirect = assessment.get("indirect_evidence") or {}
    community = (
        schemas.CommunityOut(
            reliability=round(indirect["reliability_rho"], 4),
            paths=[
                schemas.PathOut(
                    via=[names.get(n, "a member") for n in p["nodes"][1:-1]],
                    strength=round(p["path_weight"], 4),
                )
                for p in _paths(assessment)
            ],
        )
        if "reliability_rho" in indirect
        else None
    )
    return schemas.AssessmentOut(
        **{k: assessment[k] for k in _PLAIN},
        verified_loans=direct.get("direct_event_count"),
        community=community,
    )
