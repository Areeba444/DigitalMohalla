"""Evidence summary for the lender's screen (TC-100): stored assessment row -> AssessmentOut.

People on community paths are shown by display name; their user ids never reach the response.
Rows from the Slice A stub carry no evidence detail. All ids and names are synthetic.
"""

from typing import Any

from app.api.evidence import assessment_out, intermediaries

LENDER, A, B, BORROWER = "u-lender", "u-a", "u-b", "u-borrower"


def row(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "assurance_state": "REVIEW_RECOMMENDED",
        "policy_decision": "PROCEED_WITH_SAFEGUARDS",
        "rule_fired": "R9",
        "config_version": "1.2.0-iteration1-draft",
        "explanation": "Synthetic.",
        "safeguards": [],
        "posterior_mean": 0.7345,
        "ci90_low": 0.3387,
        "ci90_high": 0.9816,
        "effective_evidence": 1.767,
        "manipulation_risk": 0,
        "manipulation_level": 1,
        "direct_evidence": {"direct_event_count": 2},
        "indirect_evidence": {
            "reliability_rho": 0.394213,
            "paths": [
                {"nodes": [LENDER, A, BORROWER], "path_weight": 0.36901},
                {"nodes": [LENDER, B, BORROWER], "path_weight": 0.35243},
                {"nodes": [LENDER, BORROWER], "path_weight": 0.5},
            ],
        },
    }
    base.update(overrides)
    return base


def test_intermediaries_are_the_inner_nodes_only() -> None:
    assert intermediaries(row()) == [A, B]


def test_paths_use_display_names_and_no_user_ids() -> None:
    out = assessment_out(row(), {A: "Neighbour A"})
    assert out.verified_loans == 2
    assert out.community is not None and out.community.reliability == 0.3942
    assert [(p.via, p.strength) for p in out.community.paths] == [
        (["Neighbour A"], 0.369),
        (["a member"], 0.3524),  # a name that could not be looked up
        ([], 0.5),  # the lender's own earlier loans
    ]
    dumped = out.model_dump_json()
    assert all(uid not in dumped for uid in (LENDER, A, B, BORROWER))


def test_stub_rows_have_no_evidence_detail() -> None:
    out = assessment_out(row(direct_evidence={}, indirect_evidence={}), {})
    assert out.verified_loans is None and out.community is None
    assert intermediaries(row(indirect_evidence=None)) == []
