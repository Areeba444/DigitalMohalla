"""Manipulation-risk scoring (Algorithm 3; suites 9 and 12; TC-30, TC-38, TC-43, TC-44; D18, D19).

The combination rule against the fixtures' signal values (ES-04, PU-01, PU-02) and the Algorithm
doc's worked examples; S1 and S4 on small hand-made review sets; the retaliation check's window,
loan-confirmation and rating conditions; and Hypothesis properties that mirror the schema's
assessment_level_ck. All people, reviews and texts are synthetic.
"""

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.config.engine_config import load_engine_config
from app.domain.assurance.detection.manipulation import (
    S1,
    S4,
    Complaint,
    ManipulationParams,
    ReviewSnapshot,
    Signal,
    assess_manipulation,
    combine,
    find_retaliation,
    max_cosine,
    partner_clustering,
    review_similarity,
)

P = ManipulationParams.from_config(load_engine_config().section("manipulation_detection_alg3"))
NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
FX = json.loads(
    (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "design"
        / "14_testing"
        / "scenario_fixtures_iteration1.json"
    ).read_text(encoding="utf-8")
)
WITH_SIGNALS = [
    f for f in FX["fixtures"] + FX["policy_unit_fixtures"] if "signals" in f["manipulation_risk"]
]


def sig(name: str, value: float) -> Signal:
    return Signal(name, True, value, P.weights[name])


def rv(
    rid: str, by: str, about: str, age: float = 5, text: str = "ok", low: int = 5, ok: bool = True
):
    return ReviewSnapshot(rid, by, about, low, text, NOW - timedelta(days=age), ok)


# ----------------------------------------------------------------------------- combination
@pytest.mark.parametrize("f", WITH_SIGNALS, ids=[f["scenario_id"] for f in WITH_SIGNALS])
def test_fixture_signals_give_the_fixture_score_level_and_corroboration(f: dict) -> None:
    want = f["manipulation_risk"]
    signals = [Signal(s["name"], s["available"], s["value"], s["weight"]) for s in want["signals"]]
    score, level, corroborated, _ = combine(signals, P)
    assert score == pytest.approx(want["score"], abs=0.05)
    assert (level, corroborated) == (want["level"], want["corroborated"])


def test_worked_examples_of_the_algorithm_doc() -> None:
    # single strong signal: 68, capped at level 3 (PU-01, TC-30)
    assert combine([sig(S1, 1.0), sig(S4, 0.2)], P) == (pytest.approx(68.0), 3, False, True)
    # friend group in iteration 1: 53.8, level 3, not capped (PU-02, TC-38)
    assert combine([sig(S1, 0.83), sig(S4, 0.10)], P)[:2] == (pytest.approx(53.8), 3)
    # colluding group: 96.8, corroborated, level 4 (ES-04, TC-43)
    assert combine([sig(S1, 1.0), sig(S4, 0.92)], P) == (pytest.approx(96.8), 4, True, False)


def test_no_available_signal_is_level_1_not_a_finding() -> None:
    unavailable = [Signal(S1, False, weight=0.3), Signal(S4, False, weight=0.2)]
    assert combine(unavailable, P) == (0.0, 1, False, False)


# ----------------------------------------------------------------------------- S1
def test_s1_needs_three_partners() -> None:
    s = partner_clustering("v", [rv("1", "v", "a"), rv("2", "b", "v")], P)
    assert not s.available and s.evidence == "2 review partners"


def test_s1_ordinary_two_sided_reviews_do_not_fire() -> None:
    """After each loan both sides review each other; the lenders never review one another."""
    reviews = [
        rv(f"{x}{d}", *pair) for x in "abc" for d, pair in (("1", ("v", x)), ("2", (x, "v")))
    ]
    s = partner_clustering("v", reviews, P)
    assert s.available and s.value == 0.0
    assert s.evidence == "mutual reviews in 0 of 3 pairs of 3 partners"


def test_s1_a_ring_reviewing_one_another_fires() -> None:
    ring = ["v", "a", "b", "c"]
    reviews = [rv(f"{x}>{y}", x, y) for x in ring for y in ring if x != y]
    assert partner_clustering("v", reviews, P).value == 1.0


# ----------------------------------------------------------------------------- S4
def test_s4_identical_texts_are_fully_similar_and_distinct_ones_are_not() -> None:
    same = "Very reliable person, quick and smooth deal, thanks"
    assert max_cosine([same, same], 3) == pytest.approx(1.0)
    distinct = [
        "Returned the drill on time and cleaned it too.",
        "Bohat acha banda hai, sab kuch waqt pe wapas kiya.",
        "Friendly neighbour; the ladder came back in perfect shape.",
    ]
    s = review_similarity(distinct, P)
    assert s.available and s.value == 0.0


def test_s4_needs_two_reviews_with_text() -> None:
    assert not review_similarity(["only one", "  ", ""], P).available


# ----------------------------------------------------------------------------- retaliation
def complaint(days_ago: float) -> Complaint:
    return Complaint("v", "lender", NOW - timedelta(days=days_ago))


def test_low_review_after_a_complaint_on_a_confirmed_loan_is_flagged() -> None:
    flags = find_retaliation("v", [rv("r", "lender", "v", age=17, low=1)], [complaint(20)], P)
    assert [(f.review_id, f.days_after_complaint) for f in flags] == [("r", pytest.approx(3.0))]


@pytest.mark.parametrize(
    ("review", "complaints"),
    [
        (rv("r", "lender", "v", age=5, low=1), [complaint(20)]),  # 15 days after: outside 14
        (rv("r", "lender", "v", age=25, low=1), [complaint(20)]),  # before the complaint
        (rv("r", "lender", "v", age=17, low=3), [complaint(20)]),  # not negative
        (rv("r", "lender", "v", age=17, low=1, ok=False), [complaint(20)]),  # return not confirmed
        (
            rv("r", "someone", "v", age=17, low=1),
            [complaint(20)],
        ),  # not the complained-about person
    ],
    ids=[
        "outside-window",
        "before-complaint",
        "not-negative",
        "unconfirmed-loan",
        "other-reviewer",
    ],
)
def test_retaliation_needs_every_condition(review: ReviewSnapshot, complaints: list) -> None:
    assert find_retaliation("v", [review], complaints, P) == []


def test_a_low_review_by_the_subject_also_counts_as_a_complaint() -> None:
    reviews = [rv("mine", "v", "lender", age=20, low=1), rv("r", "lender", "v", age=18, low=1)]
    assert [f.review_id for f in find_retaliation("v", reviews, [], P)] == ["r"]


def test_set_aside_reviews_are_left_out_of_s1_and_s4() -> None:
    """Only the retaliatory review is near-identical to another one; once set aside, S4 is quiet."""
    text = "Terrible lender, the kit was not as described and they were rude."
    reviews = [
        rv("r1", "lender", "v", age=17, text=text, low=1),
        rv("r2", "x", "v", age=10, text=text),
    ]
    risk = assess_manipulation("v", reviews, [complaint(20)], NOW, P)
    assert [f.review_id for f in risk.retaliation] == ["r1"]
    s4 = next(s for s in risk.signals if s.name == S4)
    assert not s4.available  # one review with text left


# ----------------------------------------------------------------------------- properties
values = st.floats(0.0, 1.0, allow_nan=False)


@settings(max_examples=500, deadline=None)
@given(values, values, st.booleans(), st.booleans())
def test_level_matches_the_schema_check(s1: float, s4: float, has1: bool, has4: bool) -> None:
    """assessment_level_ck: level = 1 below 20, 2 below 40, 3 below 60 or when not corroborated,
    else 4, on the stored (rounded-down) score."""
    signals = [Signal(S1, has1, s1, P.weights[S1]), Signal(S4, has4, s4, P.weights[S4])]
    score, level, corroborated, _ = combine(signals, P)
    stored = math.floor(score)
    assert 0 <= score <= 100
    expected = (
        1 if stored < 20 else 2 if stored < 40 else 3 if stored < 60 or not corroborated else 4
    )
    assert level == expected


@settings(max_examples=300, deadline=None)
@given(values)
def test_one_strong_signal_never_reaches_level_4(v: float) -> None:  # TC-38, ADR-0007
    for strong, other in ((S1, S4), (S4, S1)):
        _, level, _, _ = combine([sig(strong, v), sig(other, 0.49)], P)
        assert level <= 3
