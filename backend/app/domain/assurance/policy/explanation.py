"""Explanation shown to the lender (FR-T-08, NFR-U-01): the factors, separately, never one trust number.

Every number is printed next to what it means ("from 6.2 effective outcomes", "90% interval 0.61 to
0.97"), the state is stated in words, and no-history is said to be "not a negative finding". Pure.
"""

from collections.abc import Sequence
from dataclasses import dataclass

NO_HISTORY = "Insufficient verified history; lender review required."

_STATE = {
    "SUFFICIENT_EVIDENCE": "Sufficient verified evidence for this request.",
    "REVIEW_RECOMMENDED": "Review recommended before lending.",
    "INSUFFICIENT_EVIDENCE": "Not enough verified evidence to judge this request.",
    "ACTIVE_DISPUTE": "A dispute involving a party is still open.",
}


@dataclass(frozen=True)
class ExplainedPath:
    via: Sequence[str]  # display names of the intermediaries; empty for the lender's own loans
    strength: float


def build_explanation(
    *,
    rule: str,
    state: str,
    mean: float,
    lower_90: float,
    upper_90: float,
    n_eff: float,
    direct_event_count: int,
    rho: float,
    paths: Sequence[ExplainedPath],
    resolved_disputes_12m: int,
    open_dispute: bool,
    is_high_value: bool,
    request_similarity: float,
    manipulation_active: bool,
    n_min: float,
    rho_max: float,
    similarity_floor: float,
    lookback_months: int,
) -> str:
    """Thresholds are passed in from the engine config, so the text never drifts from the policy."""
    parts: list[str] = []
    if rule == "R3":
        parts.append(NO_HISTORY)
        parts.append("This is not a negative finding about the borrower.")
    else:
        parts.append(_STATE[state])
    if direct_event_count == 0:
        parts.append("Direct evidence: no verified loans yet.")
    else:
        parts.append(
            f"Direct evidence: {direct_event_count} verified loan(s), weighted for recency and similarity to "
            f"{n_eff:.1f} effective outcomes; estimated on-time return {mean:.2f} with a 90% interval "
            f"of {lower_90:.2f} to {upper_90:.2f}."
        )
    if paths:
        listed = "; ".join(
            (f"via {' then '.join(p.via)}" if p.via else "earlier loans from this lender")
            + f" (path strength {p.strength:.2f})"
            for p in paths
        )
        parts.append(
            f"Community paths from the lender: {listed}; indirect reliability {rho:.2f} (at most {rho_max:.2f})."
        )
        if rule == "R9" and n_eff < n_min:
            parts.append("Without these paths the request would be INSUFFICIENT_EVIDENCE.")
    else:
        parts.append("Community paths from the lender: none found.")
    if open_dispute:
        parts.append("An open dispute must be resolved first.")
    if resolved_disputes_12m:
        parts.append(
            f"Resolved disputes in the last {lookback_months} months: {resolved_disputes_12m}."
        )
    if is_high_value:
        parts.append(
            f"High-value item: similarity of earlier loans to this one {request_similarity:.2f} (threshold {similarity_floor:.2f})."
        )
    if rule == "R4":
        parts.append(
            "Held for a moderator before it reaches the lender; nobody is restricted without a human decision."
        )
    if not manipulation_active:
        parts.append("Manipulation checks: not active yet (Slice C).")
    parts.append("Decision support, not a guarantee.")
    return " ".join(parts)
