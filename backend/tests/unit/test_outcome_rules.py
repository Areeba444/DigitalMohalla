"""Outcome rules of team decision D11 (Test Plan TC-76, suite 16)."""

import pytest

from app.domain.assurance.estimation.outcomes import (
    ClosedLoan,
    OutcomeRecord,
    ResolvedDispute,
    outcomes_for_closed_loan,
    outcomes_for_resolved_dispute,
)


def as_dict(records: list[OutcomeRecord]) -> dict[tuple[str, str], bool]:
    out = {(r.subject_role, r.metric): r.success for r in records}
    assert len(out) == len(records), "one outcome per subject and metric"
    return out


def test_on_time_close_is_success_everywhere() -> None:
    assert as_dict(outcomes_for_closed_loan(ClosedLoan(returned_on_time=True))) == {
        ("BORROWER", "ON_TIME_RETURN"): True,
        ("BORROWER", "CONDITION_AGREED"): True,
        ("BORROWER", "DISPUTE_FREE"): True,
        ("LENDER", "CONDITION_AGREED"): True,
        ("LENDER", "DISPUTE_FREE"): True,
    }


def test_late_close_fails_only_on_time_return() -> None:
    got = as_dict(outcomes_for_closed_loan(ClosedLoan(returned_on_time=False)))
    assert got[("BORROWER", "ON_TIME_RETURN")] is False
    assert all(v for k, v in got.items() if k != ("BORROWER", "ON_TIME_RETURN"))


def test_lender_is_never_measured_on_returning() -> None:
    for d in (
        ClosedLoan(True),
        ResolvedDispute("RETURN_INITIATED", "DAMAGE", "lender", True),
        ResolvedDispute("ACTIVE", "NON_RETURN", "borrower"),
    ):
        records = (
            outcomes_for_closed_loan(d)
            if isinstance(d, ClosedLoan)
            else outcomes_for_resolved_dispute(d)
        )
        assert ("LENDER", "ON_TIME_RETURN") not in as_dict(records)


def test_damage_found_against_the_borrower() -> None:
    got = as_dict(
        outcomes_for_resolved_dispute(
            ResolvedDispute("RETURN_INITIATED", "DAMAGE", "borrower", True)
        )
    )
    assert got == {
        ("BORROWER", "ON_TIME_RETURN"): True,  # returned on time, but damaged
        ("BORROWER", "CONDITION_AGREED"): False,
        ("BORROWER", "DISPUTE_FREE"): False,
        ("LENDER", "CONDITION_AGREED"): True,
        ("LENDER", "DISPUTE_FREE"): True,
    }


def test_claim_rejected_counts_against_the_lender() -> None:
    got = as_dict(
        outcomes_for_resolved_dispute(
            ResolvedDispute("RETURN_INITIATED", "DAMAGE", "lender", False)
        )
    )
    assert got[("LENDER", "CONDITION_AGREED")] is False
    assert got[("LENDER", "DISPUTE_FREE")] is False
    assert got[("BORROWER", "CONDITION_AGREED")] is True
    assert got[("BORROWER", "ON_TIME_RETURN")] is False  # the late return still counts


def test_no_fault_is_success_for_both() -> None:
    got = as_dict(
        outcomes_for_resolved_dispute(ResolvedDispute("RETURN_INITIATED", "DAMAGE", "none", True))
    )
    assert all(got.values())


def test_non_return_fails_on_time_and_records_condition() -> None:
    got = as_dict(
        outcomes_for_resolved_dispute(ResolvedDispute("ACTIVE", "NON_RETURN", "borrower"))
    )
    assert got[("BORROWER", "ON_TIME_RETURN")] is False
    assert got[("BORROWER", "DISPUTE_FREE")] is False
    assert ("BORROWER", "CONDITION_AGREED") in got


def test_dispute_at_handover_does_not_measure_the_borrower_on_items_they_never_had() -> None:
    got = as_dict(
        outcomes_for_resolved_dispute(ResolvedDispute("ACCEPTED", "CONDITION_MISMATCH", "lender"))
    )
    assert ("BORROWER", "ON_TIME_RETURN") not in got
    assert ("BORROWER", "CONDITION_AGREED") not in got
    assert got[("BORROWER", "DISPUTE_FREE")] is True
    assert got[("LENDER", "CONDITION_AGREED")] is False


def test_active_dispute_not_about_returning_records_no_on_time_outcome() -> None:
    got = as_dict(outcomes_for_resolved_dispute(ResolvedDispute("ACTIVE", "OTHER", "none")))
    assert ("BORROWER", "ON_TIME_RETURN") not in got


@pytest.mark.parametrize(
    "bad",
    [
        ResolvedDispute(
            "RETURNED", "DAMAGE", "none", True
        ),  # decision D4: no dispute from RETURNED
        ResolvedDispute("RETURN_INITIATED", "DAMAGE", "nobody", True),  # type: ignore[arg-type]
        ResolvedDispute("RETURN_INITIATED", "DAMAGE", "none", None),  # return time unknown
    ],
)
def test_impossible_inputs_are_refused_not_guessed(bad: ResolvedDispute) -> None:
    with pytest.raises(ValueError):
        outcomes_for_resolved_dispute(bad)


# ----------------------------------------------------------------------------- item possession (ADR-0009)
def test_lost_item_fails_the_borrower_on_return_and_condition() -> None:  # TC-143
    out = as_dict(
        outcomes_for_resolved_dispute(
            ResolvedDispute("ACTIVE", "NON_RETURN", "borrower", possession="LOST")
        )
    )
    assert out == {
        ("BORROWER", "ON_TIME_RETURN"): False,
        ("BORROWER", "CONDITION_AGREED"): False,
        ("BORROWER", "DISPUTE_FREE"): False,
        ("LENDER", "CONDITION_AGREED"): True,
        ("LENDER", "DISPUTE_FREE"): True,
    }


def test_lost_after_return_initiated_ignores_the_return_time() -> None:
    out = as_dict(
        outcomes_for_resolved_dispute(
            ResolvedDispute(
                "RETURN_INITIATED", "DAMAGE", "none", returned_on_time=True, possession="LOST"
            )
        )
    )
    assert out[("BORROWER", "ON_TIME_RETURN")] is False
    assert out[("BORROWER", "CONDITION_AGREED")] is False


def test_item_still_with_the_borrower_records_only_the_finding() -> None:  # TC-141
    out = as_dict(
        outcomes_for_resolved_dispute(
            ResolvedDispute(
                "RETURN_INITIATED",
                "CONDITION_MISMATCH",
                "lender",
                returned_on_time=True,
                possession="WITH_BORROWER",
            )
        )
    )
    assert ("BORROWER", "ON_TIME_RETURN") not in out  # judged when the return happens
    assert out[("LENDER", "DISPUTE_FREE")] is False


def test_close_after_a_dispute_records_only_the_return() -> None:
    out = as_dict(outcomes_for_closed_loan(ClosedLoan(returned_on_time=False, after_dispute=True)))
    assert out == {("BORROWER", "ON_TIME_RETURN"): False}


@pytest.mark.parametrize("possession", ["RETURNED", "NOT_HANDED_OVER", None])
def test_returned_and_not_handed_over_keep_the_d11_rules(possession: str | None) -> None:
    stage = "ACCEPTED" if possession == "NOT_HANDED_OVER" else "ACTIVE"
    with_possession = outcomes_for_resolved_dispute(
        ResolvedDispute(stage, "DAMAGE", "borrower", possession=possession)  # type: ignore[arg-type]
    )
    without = outcomes_for_resolved_dispute(ResolvedDispute(stage, "DAMAGE", "borrower"))
    assert as_dict(with_possession) == as_dict(without)
