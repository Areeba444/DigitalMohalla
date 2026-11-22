"""Probability-quality metrics and baselines for the evaluation harness (M7; Evaluation Protocol v0 §5, §6.1).

Pure functions, no I/O, no database. Plain-language notes:
- Brier score: the average of (p - y)^2 where y is 1 for an on-time return and 0 otherwise. Lower is
  better. Always answering the global average gives the reference level to beat.
- Log loss: the average of -ln(probability given to what happened); p is clipped away from 0 and 1.
- Calibration: of the loans given about 70%, about 70% should be returned on time. ECE is the
  bin-size-weighted average gap between what was said and what happened.
- Bootstrap: resample the test loans with replacement 1,000 times with a fixed seed; the 2.5% and
  97.5% points of the statistic give a 95% interval, so a difference is shown with its noise.
All inputs are synthetic.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

CLIP = 1e-6


def brier(p: Sequence[float], y: Sequence[int]) -> float:
    return sum((a - b) ** 2 for a, b in zip(p, y, strict=True)) / len(p)


def log_loss(p: Sequence[float], y: Sequence[int]) -> float:
    total = 0.0
    for a, b in zip(p, y, strict=True):
        a = min(1 - CLIP, max(CLIP, a))
        total -= math.log(a) if b else math.log(1 - a)
    return total / len(p)


@dataclass(frozen=True)
class Bin:
    low: float
    high: float
    n: int
    mean_p: float
    observed: float


def calibration(p: Sequence[float], y: Sequence[int], bins: int = 10) -> tuple[list[Bin], float]:
    """Reliability bins (equal width) and the expected calibration error."""
    cells: list[list[int]] = [[] for _ in range(bins)]
    for i, a in enumerate(p):
        cells[min(bins - 1, int(a * bins))].append(i)
    out: list[Bin] = []
    ece = 0.0
    for k, idx in enumerate(cells):
        if not idx:
            continue
        mean_p = sum(p[i] for i in idx) / len(idx)
        obs = sum(y[i] for i in idx) / len(idx)
        out.append(Bin(k / bins, (k + 1) / bins, len(idx), round(mean_p, 4), round(obs, 4)))
        ece += len(idx) / len(p) * abs(mean_p - obs)
    return out, ece


def bootstrap_ci(
    stat: Callable[[list[int]], float], n: int, resamples: int = 1000, seed: int = 20261001
) -> tuple[float, float]:
    """95% interval of `stat` (a function of the chosen loan indices) over resampled test loans."""
    rng = random.Random(seed)  # nosec B311 - seeded resampling for statistics, not security
    vals = sorted(stat([rng.randrange(n) for _ in range(n)]) for _ in range(resamples))
    return vals[int(0.025 * resamples)], vals[int(0.975 * resamples) - 1]


def coverage(intervals: Sequence[tuple[float, float]], truth: Sequence[float]) -> float:
    """Share of intervals that contain the hidden true probability."""
    return sum(lo <= t <= hi for (lo, hi), t in zip(intervals, truth, strict=True)) / len(truth)


# ----------------------------------------------------------------------------- baselines
Outcome = tuple[datetime, bool]  # (time of the outcome, on time?)


def b0_global(training: Sequence[bool]) -> float:
    """B0 (and B1 while only the borrower role is measured): the on-time rate of all training outcomes."""
    return sum(training) / len(training) if training else 0.5


def b2_recency(
    history: Sequence[Outcome], at: datetime, half_life: float, fallback: float
) -> float:
    """B2: the borrower's recency-weighted on-time rate; the global rate if there is no history."""
    total = good = 0.0
    for when, ok in history:
        w = 2.0 ** (-max(0.0, (at - when).total_seconds() / 86400.0) / half_life)
        total += w
        good += w if ok else 0.0
    return good / total if total > 0 else fallback


def b3_beta_mean(history: Sequence[Outcome], at: datetime, half_life: float) -> float:
    """B3: mean of the recency-weighted Beta(1, 1) posterior, without similarity weighting."""
    a = b = 1.0
    for when, ok in history:
        w = 2.0 ** (-max(0.0, (at - when).total_seconds() / 86400.0) / half_life)
        if ok:
            a += w
        else:
            b += w
    return a / (a + b)
