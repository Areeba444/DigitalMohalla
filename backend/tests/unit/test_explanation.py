"""Explanation builder (TC-75; FR-T-08, NFR-U-01): it states facts, each number with its meaning.

Inputs follow the fixtures ES-01 (no history), ES-02 (strong history), ES-06 (high value, held) and
ES-13 (sparse history with community paths). Manipulation signals (ES-04) arrive with Slice C; until
then the text says the checks are not active. All names are synthetic.
"""

import re
from typing import Any

from app.domain.assurance.policy.explanation import NO_HISTORY, ExplainedPath, build_explanation

LIMITS: dict[str, Any] = {
    "n_min": 3.0,
    "rho_max": 0.6,
    "similarity_floor": 0.5,
    "lookback_months": 12,
}


def explain(**overrides: Any) -> str:
    args: dict[str, Any] = {
        "rule": "R7",
        "state": "SUFFICIENT_EVIDENCE",
        "mean": 0.913,
        "lower_90": 0.7518,
        "upper_90": 0.9951,
        "n_eff": 9.5,
        "direct_event_count": 10,
        "rho": 0.0,
        "paths": [],
        "resolved_disputes_12m": 0,
        "open_dispute": False,
        "is_high_value": False,
        "request_similarity": 1.0,
        "manipulation": None,
        **LIMITS,
    }
    args.update(overrides)
    return build_explanation(**args)


def test_no_history_is_not_a_negative_finding() -> None:  # ES-01
    text = explain(
        rule="R3",
        state="INSUFFICIENT_EVIDENCE",
        mean=0.5,
        lower_90=0.05,
        upper_90=0.95,
        n_eff=0.0,
        direct_event_count=0,
    )
    assert text.startswith(NO_HISTORY)
    assert "not a negative finding" in text
    assert "no verified loans yet" in text
    assert "0.50" not in text  # the prior mean is not shown as if it were evidence


def test_strong_history_states_the_interval_and_effective_evidence() -> None:  # ES-02
    text = explain()
    assert "Sufficient verified evidence" in text
    assert "10 verified loan(s)" in text
    assert "9.5 effective outcomes" in text
    assert "90% interval of 0.75 to 1.00" in text


def test_community_paths_are_listed_with_their_strengths() -> None:  # ES-13
    text = explain(
        rule="R9",
        state="REVIEW_RECOMMENDED",
        mean=0.7345,
        lower_90=0.3387,
        upper_90=0.9816,
        n_eff=1.7668,
        direct_event_count=2,
        rho=0.3942,
        paths=[ExplainedPath(["Neighbour A"], 0.369), ExplainedPath(["Neighbour B"], 0.3524)],
    )
    assert "via Neighbour A (path strength 0.37)" in text
    assert "via Neighbour B (path strength 0.35)" in text
    assert "indirect reliability 0.39 (at most 0.60)" in text
    assert "Without these paths the request would be INSUFFICIENT_EVIDENCE." in text


def test_a_one_hop_path_is_the_lenders_own_loans() -> None:
    text = explain(rho=0.13, paths=[ExplainedPath([], 0.75)])
    assert "earlier loans from this lender (path strength 0.75)" in text
    assert "via  " not in text


def test_high_value_hold_says_a_human_decides() -> None:  # ES-06
    text = explain(
        rule="R4",
        state="REVIEW_RECOMMENDED",
        mean=0.7143,
        lower_90=0.3017,
        upper_90=0.9797,
        n_eff=1.5,
        direct_event_count=2,
        is_high_value=True,
        request_similarity=0.25,
    )
    assert "similarity of earlier loans to this one 0.25 (threshold 0.50)" in text
    assert "nobody is restricted without a human decision" in text


def test_disputes_and_inactive_checks_are_stated() -> None:
    text = explain(rule="R1", state="ACTIVE_DISPUTE", open_dispute=True, resolved_disputes_12m=2)
    assert "An open dispute must be resolved first." in text
    assert "Resolved disputes in the last 12 months: 2." in text
    assert "Manipulation checks: not run." in text
    assert text.endswith("Decision support, not a guarantee.")


def test_thresholds_in_the_text_come_from_the_config() -> None:
    text = explain(
        rule="R9",
        state="REVIEW_RECOMMENDED",
        n_eff=3.5,
        rho=0.31,
        paths=[ExplainedPath(["Neighbour A"], 0.5)],
        is_high_value=True,
        resolved_disputes_12m=1,
        n_min=4.0,
        rho_max=0.5,
        similarity_floor=0.4,
        lookback_months=6,
    )
    assert "(at most 0.50)" in text and "(threshold 0.40)" in text
    assert "in the last 6 months" in text
    assert "Without these paths" in text  # n_eff 3.5 < n_min 4


def test_no_number_stands_alone_and_there_is_no_trust_score() -> None:
    """Every decimal is printed inside a labelled phrase (never a single trust number)."""
    texts = [
        explain(),
        explain(rho=0.4, paths=[ExplainedPath(["Neighbour A", "Neighbour B"], 0.3)]),
        explain(is_high_value=True, request_similarity=0.8),
    ]
    # the word just before each number: "interval of", "to", "return", "path strength", ...
    labels = {"of", "to", "return", "strength", "reliability", "most", "one", "threshold"}
    for text in texts:
        assert "score" not in text.lower()
        for m in re.finditer(r"\d+\.\d+", text):
            assert text[: m.start()].split()[-1].lstrip("(") in labels, (m.group(), text)
