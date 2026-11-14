"""Manipulation-risk scoring (Algorithm 3; FR-T-05, FR-T-09; ADR-0007; decisions D18 and D19).

A risk detector, not proof of fraud: it never changes records and never restricts anyone. Only
level 4 (with two corroborating signals) holds a request, for a moderator (rule R2).

Plain-language note.
- S1, partners reviewing one another (D18): take everyone the subject reviewed or was reviewed by
  in the window (at least `s1_min_partners`). Count how many pairs of those partners reviewed each
  other both ways. A ring of accounts all rating one another fills almost every pair; an ordinary
  borrower's lenders rarely review each other. Pairwise "A rated B, B rated A" is NOT used: after
  every loan both sides review each other, so it would flag ordinary members.
- S4, similar review texts: the reviews the subject received in the window, as character 3-grams
  weighted by TF-IDF over those reviews; the highest cosine similarity between any two of them.
- S2 rating velocity, S3 new-account activity and S5 invitation linkage (iteration 2, DA-15
  section 4): a burst of ratings, many ratings for a very new account, and raters who joined
  through the same invitations as the subject. A quiet signal counts as evidence of normal
  behaviour, which is why the family group of iteration 1 falls from level 3 to level 2.
- Each signal is scaled to 0..1, combined as a weighted mean over the signals that are available,
  and banded into levels 1 to 4. Level 4 needs two signals at 0.5 or more; otherwise it is level 3.
- Retaliation check (D19): a low review posted within `retaliation_window_days` after the subject
  complained about the reviewer (a dispute they opened, or a low review of their own), about a loan
  whose return was confirmed, is set aside: it is left out of S1 and S4 and reported. Reviews never
  enter the trust estimate (that uses verified loan outcomes), so it cannot lower anyone's trust.
Pure, no I/O.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import combinations
from typing import Any

S1, S4 = "s1_reciprocal_clustering", "s4_review_similarity"
S2, S3, S5 = "s2_rating_velocity", "s3_new_account_activity", "s5_account_linkage"


@dataclass(frozen=True)
class ReviewSnapshot:
    id: str
    reviewer: str
    reviewee: str
    lowest_rating: int | None  # the lowest of its rating dimensions; None if it has none
    comment: str | None
    created_at: datetime
    loan_confirmed: bool  # the reviewed loan's return was confirmed by both parties


@dataclass(frozen=True)
class Complaint:
    by: str  # who opened the dispute
    against: str  # the other party of that loan
    at: datetime


@dataclass(frozen=True)
class ManipulationParams:
    window_days: float
    retaliation_window_days: float
    weights: Mapping[str, float]
    active: tuple[str, ...]
    s1_min_ratio: float
    s1_range: float
    s1_min_partners: int
    s4_min_cosine: float
    s4_range: float
    s4_char_ngram: int
    s4_min_reviews: int
    band_max: tuple[float, float, float]  # upper bounds of levels 1, 2 and 3
    corroboration_min: float
    corroboration_count: int
    negative_rating_max: int
    # iteration 2 (DA-15 section 4); defaults keep an iteration 1 config loadable
    velocity_recent_days: float = 7.0
    velocity_baseline_days: float = 83.0
    new_account_age_days: float = 30.0
    new_account_recent_days: float = 14.0
    s2_base_ratio: float = 2.0
    s2_range: float = 3.0
    s2_min_recent: int = 3
    s3_base_count: float = 3.0
    s3_range: float = 7.0
    s5_base_links: float = 2.0
    s5_range: float = 8.0
    s5_window_days: float = 90.0

    @classmethod
    def from_config(cls, section: Mapping[str, Any]) -> ManipulationParams:
        win, sw = section["observation_windows"], section["signal_weights"]
        b, bands = section["signal_scaling_bounds"], section["risk_bands"]
        guard = section["corroboration_guard"]
        return cls(
            window_days=float(win["evaluation_window_days_W"]),
            retaliation_window_days=float(win["retaliation_window_days"]),
            weights={k: float(v) for k, v in sw["weights"].items()},
            active=tuple(sw.get("iteration_2_active", sw["iteration_1_active"])),
            s1_min_ratio=float(b["s1_min_ratio"]),
            s1_range=float(b["s1_range"]),
            s1_min_partners=int(b["s1_min_partners"]),
            s4_min_cosine=float(b["s4_min_cosine"]),
            s4_range=float(b["s4_range"]),
            s4_char_ngram=int(b["s4_char_ngram"]),
            s4_min_reviews=int(b["s4_min_reviews"]),
            band_max=(
                float(bands["level_1_proceed_max"]),
                float(bands["level_2_monitor_max"]),
                float(bands["level_3_verify_max"]),
            ),
            corroboration_min=float(guard["min_signal_threshold"]),
            corroboration_count=int(guard["required_corroborating_signals"]),
            negative_rating_max=int(section["retaliation_check"]["negative_rating_max"]),
            **_iteration_2_params(section),
        )


def _iteration_2_params(section: Mapping[str, Any]) -> dict[str, Any]:
    """S2, S3 and S5 parameters, present from config 1.3.3 (copied from design config 1.4.0)."""
    win, b = section["observation_windows"], section["signal_scaling_bounds"]
    if "s2_base_ratio" not in b:
        return {}
    return {
        "velocity_recent_days": float(win["velocity_recent_window_days"]),
        "velocity_baseline_days": float(win["velocity_baseline_window_days"]),
        "new_account_age_days": float(win["new_account_age_threshold_days"]),
        "new_account_recent_days": float(win["new_account_recent_window_days"]),
        "s2_base_ratio": float(b["s2_base_ratio"]),
        "s2_range": float(b["s2_range"]),
        "s2_min_recent": int(b["s2_min_recent"]),
        "s3_base_count": float(b["s3_base_count"]),
        "s3_range": float(b["s3_range"]),
        "s5_base_links": float(b["s5_base_links"]),
        "s5_range": float(b["s5_range"]),
        "s5_window_days": float(section["s5_linkage"]["window_days"]),
    }


@dataclass(frozen=True)
class Signal:
    name: str
    available: bool
    value: float = 0.0
    weight: float = 0.0
    evidence: str = ""


@dataclass(frozen=True)
class RetaliationFlag:
    review_id: str
    reviewer: str
    days_after_complaint: float


@dataclass(frozen=True)
class ManipulationRisk:
    score: float  # 0..100
    level: int  # 1..4
    corroborated: bool
    signals: list[Signal]
    retaliation: list[RetaliationFlag] = field(default_factory=list)
    capped: bool = False  # level 4 by score, held at 3 because only one signal is strong

    @property
    def stored_score(self) -> int:
        """The integer kept in assessment.manipulation_risk. Rounded down, so it falls in the same
        band as the exact score (band edges are whole numbers) and the schema's level check holds."""
        return math.floor(self.score)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


# ----------------------------------------------------------------------------- S1
def partner_clustering(
    subject: str, reviews: Iterable[ReviewSnapshot], p: ManipulationParams
) -> Signal:
    rs = list(reviews)
    partners = {r.reviewee for r in rs if r.reviewer == subject} | {
        r.reviewer for r in rs if r.reviewee == subject
    }
    partners.discard(subject)
    weight = p.weights[S1]
    if len(partners) < p.s1_min_partners:
        return Signal(S1, False, weight=weight, evidence=f"{len(partners)} review partners")
    wrote = {(r.reviewer, r.reviewee) for r in rs}
    pairs = list(combinations(sorted(partners), 2))
    mutual = sum(1 for a, b in pairs if (a, b) in wrote and (b, a) in wrote)
    value = _clamp((mutual / len(pairs) - p.s1_min_ratio) / p.s1_range)
    evidence = f"mutual reviews in {mutual} of {len(pairs)} pairs of {len(partners)} partners"
    return Signal(S1, True, value, weight, evidence)


# ----------------------------------------------------------------------------- S4
def _grams(text: str, n: int) -> Counter[str]:
    t = " " + re.sub(r"\s+", " ", text.lower()).strip() + " "
    return Counter(t[i : i + n] for i in range(len(t) - n + 1))


def max_cosine(texts: Sequence[str], n: int) -> float:
    """Highest cosine similarity between two texts, as character n-grams weighted by TF-IDF over
    these texts (smoothed: idf = ln((1 + N) / (1 + df)) + 1, so no gram gets weight zero)."""
    docs = [_grams(t, n) for t in texts]
    df = Counter(g for d in docs for g in d)
    big_n = len(docs)
    vecs = [{g: c * (math.log((1 + big_n) / (1 + df[g])) + 1) for g, c in d.items()} for d in docs]
    norms = [math.sqrt(sum(v * v for v in vec.values())) for vec in vecs]
    best = 0.0
    for i, j in combinations(range(big_n), 2):
        if norms[i] and norms[j]:
            dot = sum(v * vecs[j].get(g, 0.0) for g, v in vecs[i].items())
            best = max(best, dot / (norms[i] * norms[j]))
    return best


def max_cosine_to(text: str, others: Sequence[str], n: int) -> float:
    """Highest cosine similarity between `text` and any of `others`, with the same TF-IDF weighting
    as `max_cosine` computed over all the texts together (used when a review is submitted, A3)."""
    docs = [_grams(t, n) for t in (text, *others)]
    df = Counter(g for d in docs for g in d)
    big_n = len(docs)
    vecs = [{g: c * (math.log((1 + big_n) / (1 + df[g])) + 1) for g, c in d.items()} for d in docs]
    norms = [math.sqrt(sum(v * v for v in vec.values())) for vec in vecs]
    best = 0.0
    for j in range(1, big_n):
        if norms[0] and norms[j]:
            dot = sum(v * vecs[j].get(g, 0.0) for g, v in vecs[0].items())
            best = max(best, dot / (norms[0] * norms[j]))
    return best


def review_similarity(texts: Sequence[str], p: ManipulationParams) -> Signal:
    weight = p.weights[S4]
    texts = [t for t in texts if t and t.strip()]
    if len(texts) < p.s4_min_reviews:
        return Signal(S4, False, weight=weight, evidence=f"{len(texts)} reviews with text")
    c = max_cosine(texts, p.s4_char_ngram)
    value = _clamp((c - p.s4_min_cosine) / p.s4_range)
    return Signal(S4, True, value, weight, f"closest two of {len(texts)} reviews {c:.2f} alike")


# ----------------------------------------------------------------------------- S2, S3, S5
def rating_velocity(
    subject: str, reviews: Sequence[ReviewSnapshot], now: datetime, p: ManipulationParams
) -> Signal:
    """S2: ratings received per day in the last 7 days against the 83 days before. A sudden burst
    of ratings is how a ring inflates a new reputation. Available with at least s2_min_recent."""
    weight = p.weights[S2]
    recent_from = now - timedelta(days=p.velocity_recent_days)
    base_from = recent_from - timedelta(days=p.velocity_baseline_days)
    received = [r.created_at for r in reviews if r.reviewee == subject]
    recent = sum(recent_from <= t <= now for t in received)
    base = sum(base_from <= t < recent_from for t in received)
    if recent < p.s2_min_recent:
        return Signal(S2, False, weight=weight, evidence=f"{recent} ratings in the last week")
    recent_rate = recent / p.velocity_recent_days
    base_rate = base / p.velocity_baseline_days
    if base_rate == 0:
        return Signal(S2, True, 1.0, weight, f"{recent} ratings in a week and none before")
    ratio = recent_rate / base_rate
    value = _clamp((ratio - p.s2_base_ratio) / p.s2_range)
    return Signal(S2, True, value, weight, f"{recent} ratings in a week, {ratio:.1f}x the usual")


def new_account_activity(
    subject: str,
    reviews: Sequence[ReviewSnapshot],
    account_created: datetime | None,
    now: datetime,
    p: ManipulationParams,
) -> Signal:
    """S3: many ratings for a very new account. An account older than new_account_age_days scores
    0 (a quiet signal is evidence of normal behaviour, DA-15 section 4)."""
    weight = p.weights[S3]
    if account_created is None:
        return Signal(S3, False, weight=weight, evidence="account age unknown")
    age = (now - account_created).total_seconds() / 86400
    if age > p.new_account_age_days:
        return Signal(S3, True, 0.0, weight, f"account {age:.0f} days old")
    since = now - timedelta(days=p.new_account_recent_days)
    n = sum(r.reviewee == subject and since <= r.created_at <= now for r in reviews)
    value = _clamp((n - p.s3_base_count) / p.s3_range)
    return Signal(S3, True, value, weight, f"account {age:.0f} days old with {n} recent ratings")


def account_linkage(
    subject: str,
    reviews: Sequence[ReviewSnapshot],
    linked: frozenset[str] | None,
    p: ManipulationParams,
) -> Signal:
    """S5: raters linked to the subject through the invitation tree (invited by the same member,
    or invited by the subject). Device and network data are not collected (FR-A-03 is iteration 3),
    so S5 is available only when the subject joined through an invitation."""
    weight = p.weights[S5]
    if linked is None:
        return Signal(S5, False, weight=weight, evidence="did not join through an invitation")
    raters = {r.reviewer for r in reviews if r.reviewee == subject}
    m = len(raters & linked)
    value = _clamp((m - p.s5_base_links) / p.s5_range)
    return Signal(S5, True, value, weight, f"{m} raters joined through the same invitations")


# ----------------------------------------------------------------------------- retaliation
def _negative(r: ReviewSnapshot, p: ManipulationParams) -> bool:
    return r.lowest_rating is not None and r.lowest_rating <= p.negative_rating_max


def find_retaliation(
    subject: str,
    reviews: Iterable[ReviewSnapshot],
    complaints: Iterable[Complaint],
    p: ManipulationParams,
) -> list[RetaliationFlag]:
    rs = list(reviews)
    window = timedelta(days=p.retaliation_window_days)
    adverse = [(c.against, c.at) for c in complaints if c.by == subject] + [
        (r.reviewee, r.created_at) for r in rs if r.reviewer == subject and _negative(r, p)
    ]
    flags = []
    for r in rs:
        if r.reviewee != subject or not _negative(r, p) or not r.loan_confirmed:
            continue
        after = [r.created_at - at for who, at in adverse if who == r.reviewer]
        after = [d for d in after if timedelta(0) <= d <= window]
        if after:
            flags.append(RetaliationFlag(r.id, r.reviewer, min(after).total_seconds() / 86400))
    return flags


# ----------------------------------------------------------------------------- combination
def combine(signals: Sequence[Signal], p: ManipulationParams) -> tuple[float, int, bool, bool]:
    """Weighted mean over available signals (renormalised), band, and the corroboration cap.
    Returns (score, level, corroborated, capped)."""
    available = [s for s in signals if s.available]
    if not available:
        return 0.0, 1, False, False
    score = min(
        100.0, 100 * sum(s.weight * s.value for s in available) / sum(s.weight for s in available)
    )
    stored = math.floor(score)
    level = 1 + sum(stored > edge for edge in p.band_max)
    corroborated = sum(s.value >= p.corroboration_min for s in available) >= p.corroboration_count
    capped = level == 4 and not corroborated
    return score, 3 if capped else level, corroborated, capped


def assess_manipulation(
    subject: str,
    reviews: Iterable[ReviewSnapshot],
    complaints: Iterable[Complaint],
    now: datetime,
    p: ManipulationParams,
    *,
    account_created: datetime | None = None,
    linked_accounts: frozenset[str] | None = None,
) -> ManipulationRisk:
    """`reviews` should reach back window_days + retaliation_window_days, so that a complaint made
    by low review just before the window still counts for the retaliation check. Signals not listed
    as active in the config, or without the data they need, are left out and the weights
    renormalised (Algorithm 3)."""
    rs = list(reviews)
    flags = find_retaliation(subject, rs, complaints, p)
    set_aside = {f.review_id for f in flags}
    since = now - timedelta(days=p.window_days)
    window = [r for r in rs if since <= r.created_at <= now and r.id not in set_aside]
    computed = {
        S1: partner_clustering(subject, window, p),
        S2: rating_velocity(subject, window, now, p),
        S3: new_account_activity(subject, window, account_created, now, p),
        S4: review_similarity([r.comment or "" for r in window if r.reviewee == subject], p),
        S5: account_linkage(subject, window, linked_accounts, p),
    }
    signals = [
        computed[name]
        if name in computed and name in p.active
        else Signal(name, False, weight=w, evidence="not active in this config")
        for name, w in p.weights.items()
    ]
    score, level, corroborated, capped = combine(signals, p)
    return ManipulationRisk(score, level, corroborated, signals, flags, capped)
