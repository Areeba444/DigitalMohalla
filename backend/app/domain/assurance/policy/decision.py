"""Decision policy and assurance-state mapping (Algorithm 4; FR-T-01, FR-T-06; ADR-0007, ADR-0008, D12).

Plain-language note: the first rule whose condition holds decides, in the order the config gives
(`decision_policy_alg4.rule_order`). An open dispute always wins (R1); a corroborated manipulation
finding holds the request for a moderator (R2); a high-value request on weak or dissimilar evidence
is held for a moderator (R4, nobody is restricted without a human), and since config 1.3.1 this is
checked before R3, so a high-value newcomer is held too (ADR-0010 proposed, review DM09, FR-B-07);
a newcomer with no community support is INSUFFICIENT_EVIDENCE, never a negative finding (R3);
strong evidence proceeds (R7, R8); anything else reaches the lender as REVIEW_RECOMMENDED (R9).
Indirect evidence on its own can never give SUFFICIENT_EVIDENCE: R7 and R8 need n_eff >= n_min from
the borrower's own outcomes. Thresholds come from engine.json; the rule table and its outputs are the
design (Algorithm doc §6, the schema's assessment_rule_ck). Pure, no I/O.
"""

from collections.abc import Callable, Mapping
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


# Iteration 1 order (config 1.3.0). Config 1.3.1 moves R4 before R3.
DEFAULT_RULE_ORDER = ("R1", "R2", "R3", "R4", "R5", "R6_DISPUTE", "R6_SPARSE", "R7", "R8", "R9")


@dataclass(frozen=True)
class PolicyThresholds:
    tau_mu: float
    tau_l: float
    n_min: float
    rho_sup: float
    similarity_floor: float
    rule_order: tuple[str, ...] = DEFAULT_RULE_ORDER

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
            rule_order=check_rule_order(cfg_data["decision_policy_alg4"]["rule_order"]),
        )


def check_rule_order(order: Any) -> tuple[str, ...]:
    """Every rule exactly once, R1 first (an open dispute always wins), R9 last (the fallback)."""
    rules = tuple(str(r) for r in order)
    if sorted(rules) != sorted(RULES) or rules[0] != "R1" or rules[-1] != "R9":
        raise ValueError(f"rule_order must list every rule once, R1 first and R9 last: {rules}")
    return rules


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
    strong = x.mean >= th.tau_mu and x.lower_90 >= th.tau_l and x.n_eff >= th.n_min
    conditions: dict[str, Callable[[], bool]] = {
        "R1": lambda: x.open_dispute,
        "R2": lambda: x.risk_level == 4,
        "R3": lambda: x.direct_event_count == 0 and x.rho < th.rho_sup,
        "R4": lambda: (
            high and (x.request_similarity < th.similarity_floor or x.lower_90 < th.tau_l)
        ),
        "R5": lambda: x.risk_level == 3,
        "R6_DISPUTE": lambda: x.resolved_disputes_12m > 0,
        "R6_SPARSE": lambda: x.n_eff < th.n_min and x.rho < th.rho_sup,
        "R7": lambda: (
            strong and x.risk_level == 1 and x.verification_ok and not medium and not high
        ),
        "R8": lambda: strong and x.risk_level <= 2 and x.verification_ok,
        "R9": lambda: True,
    }
    rule = next(r for r in th.rule_order if conditions[r]())
    decision, state, hold = RULES[rule]
    return PolicyDecision(
        rule, decision, state, hold, hold is not None, safeguards_for(rule, x.value_band)
    )
