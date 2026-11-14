"""Detection and trivial-exchange rules of iteration 2 (suite 24; DA-15 sections 2 and 4; A4).

Oracles are DA-15's worked examples: the new-account burst is level 4 and held; the iteration 1
family group falls to level 2 when all five signals are available; S5 is unavailable without an
invitation; five loans with one neighbour in 20 days weigh 1.9375, with five neighbours 5.
TC-240 to TC-247. All inputs are synthetic.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.config.engine_config import load_engine_config
from app.domain.assurance.detection.manipulation import (
    S2,
    S3,
    S5,
    ManipulationParams,
    ReviewSnapshot,
    Signal,
    account_linkage,
    assess_manipulation,
    combine,
    new_account_activity,
    rating_velocity,
)
from app.domain.assurance.estimation.repeat import RepeatParams, repeat_multipliers

CFG = load_engine_config()
P = ManipulationParams.from_config(CFG.section("manipulation_detection_alg3"))
REPEAT = RepeatParams.from_config(CFG.section("trust_estimation_alg1")["pair_repeat_discount"])
NOW = datetime(2026, 11, 15, 12, tzinfo=UTC)
W = {"s1_reciprocal_clustering": 0.3, S2: 0.2, S3: 0.2, "s4_review_similarity": 0.2, S5: 0.1}


def rated(by: str, days_ago: float, about: str = "v", text: str = "ok") -> ReviewSnapshot:
    return ReviewSnapshot(
        f"{by}-{days_ago}", by, about, 5, text, NOW - timedelta(days=days_ago), True
    )


def signals(values: dict[str, float]) -> list[Signal]:
    return [Signal(k, True, v, W[k]) for k, v in values.items()]


def test_tc240_config_activates_all_five_signals() -> None:
    assert set(P.active) >= set(W)
    assert (P.s2_min_recent, P.new_account_age_days, P.s5_window_days) == (3, 30.0, 90.0)


def test_tc241_burst_case_is_level_4_and_corroborated() -> None:
    """DA-15 table row 1: s = 0.20, 1.00, 0.71, 0.90, 0.25 -> 60.8, level 4, held (R2)."""
    s = signals(
        {"s1_reciprocal_clustering": 0.2, S2: 1.0, S3: 0.71, "s4_review_similarity": 0.9, S5: 0.25}
    )
    score, level, corroborated, capped = combine(s, P)
    assert score == pytest.approx(60.7, abs=0.15) and (level, corroborated, capped) == (
        4,
        True,
        False,
    )


def test_tc242_family_group_with_all_signals_is_level_2() -> None:
    """DA-15 table row 2 (fixture PU-02): s1 0.83, s4 0.10, the rest 0 -> 26.9, level 2, not held."""
    s = signals(
        {"s1_reciprocal_clustering": 0.83, S2: 0.0, S3: 0.0, "s4_review_similarity": 0.10, S5: 0.0}
    )
    score, level, corroborated, _ = combine(s, P)
    assert score == pytest.approx(26.9, abs=0.05) and (level, corroborated) == (2, False)


def test_tc243_s2_rating_velocity() -> None:
    """Input: 4 ratings in the last week, 4 in the 83 days before -> ratio 11.9 -> 1.0; 4 in a week
    and 40 before -> ratio 1.19 -> 0; 2 in a week -> unavailable; 4 in a week, none before -> 1."""
    burst = [rated(f"r{i}", 1 + i) for i in range(4)] + [
        rated(f"o{i}", 20 + 10 * i) for i in range(4)
    ]
    assert rating_velocity("v", burst, NOW, P).value == 1.0
    steady = [rated(f"r{i}", 1 + i) for i in range(4)] + [
        rated(f"o{i}", 8 + 2 * i) for i in range(40)
    ]
    assert rating_velocity("v", steady, NOW, P).value == 0.0
    assert rating_velocity("v", burst[:2], NOW, P).available is False
    assert rating_velocity("v", burst[:4], NOW, P).value == 1.0


def test_tc244_s3_new_account_activity() -> None:
    """Input: a 10-day-old account with 8 ratings in 14 days -> (8 - 3) / 7 = 0.714; a 200-day-old
    account -> 0, still available; unknown age -> unavailable."""
    eight = [rated(f"r{i}", i) for i in range(8)]
    young = new_account_activity("v", eight, NOW - timedelta(days=10), NOW, P)
    assert young.value == pytest.approx(5 / 7) and young.available
    old = new_account_activity("v", eight, NOW - timedelta(days=200), NOW, P)
    assert (old.available, old.value) == (True, 0.0)
    assert new_account_activity("v", eight, None, NOW, P).available is False


def test_tc245_s5_uses_only_the_invitation_tree() -> None:
    """Input: 4 raters, all invited by the subject's inviter -> (4 - 2) / 8 = 0.25; the subject did
    not join through an invitation -> unavailable (no device or network data is collected)."""
    raters = [rated(f"r{i}", 1) for i in range(4)]
    linked = frozenset({"r0-1", "r1-1", "r2-1", "r3-1"} | {"r0", "r1", "r2", "r3"})
    assert account_linkage("v", raters, linked, P).value == pytest.approx(0.25)
    assert account_linkage("v", raters, None, P).available is False


def test_tc246_whole_assessment_holds_the_burst_but_not_a_quiet_old_account() -> None:
    """Input: 8 near-identical 5-star reviews in 6 days for a 10-day-old account whose 4 raters are
    invitation siblings, plus mutual reviews among partners. Expected: level 4, corroborated. The
    same reviews spread over 80 days for a 400-day-old account without an invitation: below 4."""
    text = "Synthetic: great neighbour, very trustworthy, highly recommended"
    ring = [f"x{i}" for i in range(4)]
    burst = [rated(ring[i % 4], 0.5 + 0.7 * i, text=text + f" {i}") for i in range(8)]
    mutual = [
        ReviewSnapshot(f"m{a}{b}", a, b, 5, None, NOW - timedelta(days=2), True)
        for a in ring
        for b in ring
        if a != b
    ]
    held = assess_manipulation(
        "v",
        burst + mutual,
        [],
        NOW,
        P,
        account_created=NOW - timedelta(days=10),
        linked_accounts=frozenset(ring),
    )
    assert (held.level, held.corroborated) == (4, True)
    spread = [
        rated(f"p{i}", 10 * i + 1, text=f"Synthetic review number {i} about a drill")
        for i in range(8)
    ]
    quiet = assess_manipulation("v", spread, [], NOW, P, account_created=NOW - timedelta(days=400))
    assert quiet.level < 4


def test_tc247_pair_repeat_discount_bounds_trivial_exchanges() -> None:
    """DA-15 section 2: five outcomes with one observer within 20 days weigh 1.9375; with five
    observers 5; an unknown observer is never discounted; outside the 30-day window the count resets."""
    days = [0, 5, 10, 15, 20]
    one = [(NOW + timedelta(days=d), "n1") for d in days]
    assert sum(repeat_multipliers(one, REPEAT)) == pytest.approx(1.9375)
    five = [(NOW + timedelta(days=d), f"n{d}") for d in days]
    assert sum(repeat_multipliers(five, REPEAT)) == 5.0
    assert repeat_multipliers([(NOW, None), (NOW, None)], REPEAT) == [1.0, 1.0]
    apart = [(NOW, "n1"), (NOW + timedelta(days=40), "n1")]
    assert repeat_multipliers(apart, REPEAT) == [1.0, 1.0]
    assert repeat_multipliers(list(reversed(one)), REPEAT)[0] == 0.0625  # order of input kept
