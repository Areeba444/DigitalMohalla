"""Decision policy and assurance-state mapping (Algorithm 4; FR-T-01, FR-T-06; ADR-0007, ADR-0008, D12).

Plain-language note: the first rule whose condition holds decides. An open dispute always wins
(R1); a corroborated manipulation finding holds the request for a moderator (R2); a newcomer with no
community support is INSUFFICIENT_EVIDENCE, never a negative finding (R3); a high-value request on
weak or dissimilar evidence is held for a moderator (R4, nobody is restricted without a human);
strong evidence proceeds (R7, R8); anything else reaches the lender as REVIEW_RECOMMENDED (R9).
Indirect evidence on its own can never give SUFFICIENT_EVIDENCE: R7 and R8 need n_eff >= n_min from
the borrower's own outcomes. Thresholds come from engine.json; the rule table and its outputs are the
design (Algorithm doc §6, the schema's assessment_rule_ck). Pure, no I/O.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

# rule -> (policy decision, assurance state, hold reason); same table as schema.sql assessment_rule_ck
RULES: dict[str, tuple[str, str, str | None]] = {
    "R1": ("ESCALATE", "ACTIVE_DISPUTE", None),
    "R2": ("ESCALATE", "REVIEW_RECOMMENDED", "manipulation_risk"),
    "R3": ("REQUEST_VERIFICATION", "INSUFFICIENT_EVIDENCE", None),
    "R4": ("RESTRICT_HIGH_VALUE", "REVIEW_RECOMMENDED", "high_value_low_confidence"),
    "R5": ("REQUEST_VERIFICATION", "REVIEW_RECOMMENDED", None),
    "R6_DISPUTE": ("PROCEED_WITH_SAFEGUARDS", "REVIEW_RECOMMENDED", None),
    "R6_SPARSE": ("REQUEST_VERIFICATION", "INSUFFICIENT_EVIDENCE", None),
    "R7": ("PROCEED", "SUFFICIENT_EVIDENCE", None),
    "R8": ("PROCEED_WITH_SAFEGUARDS", "SUFFICIENT_EVIDENCE", None),
    "R9": ("PROCEED_WITH_SAFEGUARDS", "REVIEW_RECOMMENDED", None),
}

_LABELS = {
    "standard_return_reminder": "Send the standard return reminder",
    "condition_photos_checklist": "Photograph the item and complete the condition checklist",
    "deposit_record": "Record the deposit before handover",
    "explicit_return_reminder": "Agree the return date explicitly and send a reminder",
    "medium_value_deposit_record": "Record a deposit suited to a medium-value item",
    "high_value_deposit_record": "Record a deposit suited to a high-value item",
    "handover_photos": "Take item photos at handover",
    "handover_checklist": "Complete the handover checklist together",
    "fixed_return_date": "Agree a fixed return date",
}


def _sg(*codes: str) -> list[dict[str, str]]:
    return [{"code": c.upper(), "label": _LABELS[c]} for c in codes]


def safeguards_for(rule: str, value_band: str) -> list[dict[str, str]]:
    """Safeguards attached to a decision. Sources: the fixtures' expected safeguards (ES-02 R7,
    ES-03 R6_DISPUTE, ES-05 and ES-13 for medium value), Overview §5.8 for newcomers (R3), and the
    Algorithm doc's example for strong high-value evidence (R8: deposit record, handover checklist).
    Rules the design does not specify get none; holds (R2, R4) get them from the moderator."""
    if rule == "R3":
        return _sg("deposit_record", "handover_photos", "fixed_return_date")
    if rule == "R7":
        return _sg("standard_return_reminder")
    if rule == "R6_DISPUTE":
        return _sg("condition_photos_checklist", "deposit_record", "explicit_return_reminder")
    if rule in ("R8", "R9") and value_band == "MEDIUM":
        return _sg("medium_value_deposit_record", "handover_photos")
    if rule == "R8" and value_band == "HIGH":
        return _sg("high_value_deposit_record", "handover_checklist")
    return []


@dataclass(frozen=True)
class PolicyThresholds:
    tau_mu: float
    tau_l: float
    n_min: float
    rho_sup: float
    similarity_floor: float

    @classmethod
    def from_config(cls, cfg_data: Mapping[str, Any]) -> "PolicyThresholds":
        """`cfg_data` is the whole engine.json."""
        t = cfg_data["decision_policy_alg4"]["thresholds"]
        return cls(
            tau_mu=float(t["tau_mu_mean_threshold"]),
            tau_l=float(t["tau_L_lower_bound_threshold"]),
            n_min=float(t["n_min_effective_observations"]),
            rho_sup=float(t["rho_sup_indirect_support_threshold"]),
            similarity_floor=float(
                cfg_data["trust_estimation_alg1"]["similarity_weighting"]["similarity_floor"]
            ),
        )


@dataclass(frozen=True)
class PolicyInputs:
    mean: float
    lower_90: float
    n_eff: float
    direct_event_count: int
    rho: float
    risk_level: int  # 1..4 (ADR-0007)
    value_band: str
    open_dispute: bool
    resolved_disputes_12m: int
    verification_ok: bool
    request_similarity: float


@dataclass(frozen=True)
class PolicyDecision:
    rule: str
    decision: str
    state: str
    hold_reason: str | None
    escalate: bool
    safeguards: list[dict[str, str]]


def decide(x: PolicyInputs, th: PolicyThresholds) -> PolicyDecision:
    if x.risk_level not in (1, 2, 3, 4):
        raise ValueError("risk level must be 1 to 4")
    high = x.value_band == "HIGH"
    medium = x.value_band == "MEDIUM"
    if x.open_dispute:
        rule = "R1"
    elif x.risk_level == 4:
        rule = "R2"
    elif x.direct_event_count == 0 and x.rho < th.rho_sup:
        rule = "R3"
    elif high and (x.request_similarity < th.similarity_floor or x.lower_90 < th.tau_l):
        rule = "R4"
    elif x.risk_level == 3:
        rule = "R5"
    elif x.resolved_disputes_12m > 0:
        rule = "R6_DISPUTE"
    elif x.n_eff < th.n_min and x.rho < th.rho_sup:
        rule = "R6_SPARSE"
    else:
        strong = x.mean >= th.tau_mu and x.lower_90 >= th.tau_l and x.n_eff >= th.n_min
        if strong and x.risk_level == 1 and x.verification_ok and not medium and not high:
            rule = "R7"
        elif strong and x.risk_level <= 2 and x.verification_ok:
            rule = "R8"
        else:
            rule = "R9"
    decision, state, hold = RULES[rule]
    return PolicyDecision(
        rule, decision, state, hold, hold is not None, safeguards_for(rule, x.value_band)
    )
