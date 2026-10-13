"""Value bands and similarity weighting (Test Plan TC-77; team decision D17)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.config.engine_config import load_engine_config
from app.domain.assurance.estimation.similarity import (
    BANDS,
    LoanProfile,
    SimilarityParams,
    floored,
    request_similarity,
    similarity,
    value_band,
)

CFG = load_engine_config()
P = SimilarityParams.from_config(CFG.section("trust_estimation_alg1")["similarity_weighting"])
VB = CFG.section("decision_policy_alg4")["value_bands_pkr"]


@pytest.mark.parametrize(
    ("value", "band"),
    [(0, "LOW"), (5000, "LOW"), (5001, "MEDIUM"), (15000, "MEDIUM"), (15001, "HIGH")],
)
def test_tc77_band_boundaries(value: int, band: str) -> None:
    assert value_band(value, VB) == band


def test_weights_from_the_config_add_up_to_one() -> None:
    assert (P.w_band, P.w_category, P.w_duration, P.floor) == (0.4, 0.4, 0.2, 0.5)
    assert P.w_band + P.w_category + P.w_duration == pytest.approx(1.0)


def test_identical_loan_is_fully_similar() -> None:
    a = LoanProfile(3, "MEDIUM", 4)
    assert similarity(a, a, P) == pytest.approx(1.0)


def test_small_short_tool_loans_say_little_about_a_high_value_projector() -> None:
    past = LoanProfile(category_id=1, value_band="LOW", duration_days=3)
    request = LoanProfile(category_id=3, value_band="HIGH", duration_days=2)
    raw = similarity(past, request, P)
    assert raw == pytest.approx(0.2 * 2 / 3)  # only the duration part matches
    assert floored(raw, P) == 0.5  # still counts half as evidence


def test_adjacent_band_same_category_same_length() -> None:
    assert similarity(LoanProfile(1, "LOW", 2), LoanProfile(1, "MEDIUM", 2), P) == pytest.approx(
        0.8
    )


def test_request_similarity_is_the_recency_weighted_mean_of_raw_values() -> None:
    assert request_similarity([(1.0, 0.2), (0.25, 1.0)]) == pytest.approx((0.2 + 0.25) / 1.25)
    assert request_similarity([]) == 0.0


@given(
    st.sampled_from(BANDS),
    st.sampled_from(BANDS),
    st.integers(1, 7),
    st.integers(1, 7),
    st.floats(0.5, 30),
    st.floats(0.5, 30),
)
def test_similarity_is_bounded_and_the_floored_weight_is_in_range(
    b1: str, b2: str, c1: int, c2: int, d1: float, d2: float
) -> None:
    raw = similarity(LoanProfile(c1, b1, d1), LoanProfile(c2, b2, d2), P)
    assert 0.0 <= raw <= 1.0 + 1e-12
    assert P.floor <= floored(raw, P) <= 1.0
    assert raw == pytest.approx(
        similarity(LoanProfile(c2, b2, d2), LoanProfile(c1, b1, d1), P)
    )  # symmetric


def test_invalid_inputs_are_refused() -> None:
    with pytest.raises(ValueError):
        similarity(LoanProfile(1, "LOW", 0), LoanProfile(1, "LOW", 2), P)
    with pytest.raises(ValueError):
        value_band(-1, VB)
