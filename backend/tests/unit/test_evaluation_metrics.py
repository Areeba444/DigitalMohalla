"""Evaluation metrics and baselines (M7; Evaluation Protocol v0 §5, §6.1). Hand-checked, synthetic."""

import math
from datetime import UTC, datetime, timedelta

import pytest

from app.evaluation.metrics import (
    b0_global,
    b2_recency,
    b3_beta_mean,
    bootstrap_ci,
    brier,
    calibration,
    coverage,
    log_loss,
)

T = datetime(2026, 6, 1, tzinfo=UTC)


def test_brier_by_hand() -> None:
    # (0.9-1)^2 = 0.01, (0.2-0)^2 = 0.04, (0.5-1)^2 = 0.25: mean 0.1
    assert brier([0.9, 0.2, 0.5], [1, 0, 1]) == pytest.approx(0.1)


def test_log_loss_by_hand_and_clipping() -> None:
    assert log_loss([0.8, 0.8], [1, 0]) == pytest.approx((-math.log(0.8) - math.log(0.2)) / 2)
    assert math.isfinite(log_loss([0.0, 1.0], [1, 0]))  # clipped, not infinite


def test_calibration_bins_and_ece() -> None:
    p = [0.15, 0.15, 0.85, 0.85]
    bins, ece = calibration(p, [0, 1, 1, 1])
    assert [(b.n, b.observed) for b in bins] == [(2, 0.5), (2, 1.0)]
    # |0.15-0.5| = 0.35 and |0.85-1.0| = 0.15, each over half the loans: 0.25
    assert ece == pytest.approx(0.25)


def test_bootstrap_is_deterministic_and_brackets_the_estimate() -> None:
    p, y = [0.9] * 20 + [0.3] * 20, [1] * 18 + [0] * 2 + [0] * 14 + [1] * 6

    def stat(i: list[int]) -> float:
        return brier([p[k] for k in i], [y[k] for k in i])

    low, high = bootstrap_ci(stat, len(p))
    assert (low, high) == bootstrap_ci(stat, len(p))
    assert low <= stat(list(range(len(p)))) <= high


def test_coverage_counts_intervals_containing_the_truth() -> None:
    assert coverage([(0.5, 0.9), (0.1, 0.3)], [0.7, 0.4]) == 0.5


def test_baselines() -> None:
    assert b0_global([True, True, False, True]) == 0.75 and b0_global([]) == 0.5
    hist = [(T - timedelta(days=180), False), (T, True)]  # weights 0.5 and 1
    assert b2_recency(hist, T, 180.0, 0.9) == pytest.approx(1 / 1.5)
    assert b2_recency([], T, 180.0, 0.9) == 0.9  # no history: the global rate
    # Beta(1 + 1, 1 + 0.5) has mean 2 / 3.5
    assert b3_beta_mean(hist, T, 180.0) == pytest.approx(2 / 3.5)
    assert b3_beta_mean([], T, 180.0) == 0.5
