"""ReviewService: reviews from the parties of a completed loan (Module 5, UC-D1, FR-T-09, B-15; A3).

Sequence (f): a review is checked and flagged when it is submitted, and reaches the decision engine
only through the manipulation signals, never the trust estimate (decision D19).

Rules (FR-T-09, FR/NFR v1.4 timer table, config section `reviews_d1`):
- only the borrower or the lender of a COMPLETED loan, one review each (`review_once_uq`), about
  the other party (`review_guard`);
- within `review_window_days` of completion; editable by its author for `edit_window_hours`;
- one rating from `rating_min` to `rating_max` for every dimension of the reviewee's role;
- flags, written at submission and recomputed on an edit, never shown to the reviewer:
  * retaliation_flag: a low review (lowest rating <= negative_rating_max) of someone who, within
    `retaliation_window_days` before it, complained about the reviewer (opened a dispute against
    them, or gave them a low review), about a loan whose return both parties confirmed. The same
    rule as Algorithm 3's retaliation check (`find_retaliation`);
  * similarity_flag: the comment's TF-IDF cosine with a review the reviewee already received in
    the evaluation window is at least `s4_min_cosine` (the S4 measure, one text against the rest).
Flagged reviews are kept for a moderator and down-weighted by the detector (set aside, D19).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from app.domain.assurance.detection.manipulation import (
    Complaint,
    ManipulationParams,
    ReviewSnapshot,
    find_retaliation,
    max_cosine_to,
)
from app.domain.lifecycle.errors import InvalidTransition, NotAuthorised, StreamNotFound
from app.domain.notifications.notify import INotify, NullNotifier

NEW_REVIEW = "new-review"


class InvalidReview(ValueError):
    """Ratings or comment do not fit the rules (422)."""


@dataclass(frozen=True)
class ReviewConfig:
    review_window_days: float
    edit_window_hours: float
    rating_min: int
    rating_max: int
    dimensions: Mapping[str, tuple[str, ...]]

    @classmethod
    def from_section(cls, s: Mapping[str, Any]) -> "ReviewConfig":
        return cls(
            float(s["review_window_days"]),
            float(s["edit_window_hours"]),
            int(s["rating_min"]),
            int(s["rating_max"]),
            {role: tuple(dims) for role, dims in s["dimensions"].items()},
        )


@dataclass(frozen=True)
class ReviewResult:
    id: UUID
    reviewee_role: str
    editable_until: datetime


class ReviewStore(Protocol):
    def loan(self, txn_id: UUID) -> dict[str, Any] | None:
        """state, borrower_id, lender_id, completed_at, return_confirmed."""
        ...

    def review_by(self, txn_id: UUID, reviewer_id: UUID) -> dict[str, Any] | None: ...

    def reviews_received(self, user_id: UUID, since: datetime) -> list[dict[str, Any]]: ...

    def reviews_given(self, user_id: UUID, since: datetime) -> list[ReviewSnapshot]: ...

    def disputes_raised(self, by: UUID, against: UUID, since: datetime) -> list[datetime]: ...

    def insert(
        self,
        txn_id: UUID,
        reviewer: UUID,
        reviewee: UUID,
        role: str,
        ratings: Mapping[str, int],
        comment: str | None,
        retaliation: bool,
        similar: bool,
    ) -> UUID: ...

    def update(
        self,
        review_id: UUID,
        ratings: Mapping[str, int],
        comment: str | None,
        retaliation: bool,
        similar: bool,
    ) -> None: ...


class ReviewService:
    def __init__(
        self,
        store: ReviewStore,
        cfg: ReviewConfig,
        detection: ManipulationParams,
        *,
        now: datetime,
        notifier: INotify | None = None,
    ) -> None:
        self.store = store
        self.cfg = cfg
        self.p = detection
        self.now = now
        self.notifier: INotify = notifier or NullNotifier()

    def submit(
        self, actor_id: UUID, txn_id: UUID, ratings: Mapping[str, int], comment: str | None
    ) -> ReviewResult:
        """A new review, or an edit of the actor's own review inside the edit window."""
        loan = self.store.loan(txn_id)
        if loan is None:
            raise StreamNotFound(f"transaction {txn_id}")
        if actor_id == loan["borrower_id"]:
            reviewee, role = loan["lender_id"], "LENDER"
        elif actor_id == loan["lender_id"]:
            reviewee, role = loan["borrower_id"], "BORROWER"
        else:
            raise NotAuthorised("only the borrower or the lender of this loan can review it")
        if loan["state"] != "COMPLETED" or loan["completed_at"] is None:
            raise InvalidTransition("reviews open when the loan is completed")
        comment = (comment or "").strip() or None
        clean = self._check(role, ratings, comment)
        retaliation, similar = self._flags(actor_id, reviewee, clean, comment, loan)

        existing = self.store.review_by(txn_id, actor_id)
        if existing is not None:
            until = existing["created_at"] + timedelta(hours=self.cfg.edit_window_hours)
            if self.now > until:
                raise InvalidTransition("your review can no longer be changed")
            self.store.update(existing["id"], clean, comment, retaliation, similar)
            return ReviewResult(existing["id"], role, until)

        if self.now > loan["completed_at"] + timedelta(days=self.cfg.review_window_days):
            raise InvalidTransition("the review window for this loan has closed")
        review_id = self.store.insert(
            txn_id, actor_id, reviewee, role, clean, comment, retaliation, similar
        )
        self.notifier.notify(
            reviewee,
            "review_received",
            {"transaction_id": str(txn_id)},
            f"{txn_id}:review_received:{actor_id}",
        )
        return ReviewResult(review_id, role, self.now + timedelta(hours=self.cfg.edit_window_hours))

    # ------------------------------------------------------------------ checks and flags
    def _check(self, role: str, ratings: Mapping[str, int], comment: str | None) -> dict[str, int]:
        dims = self.cfg.dimensions[role]
        if set(ratings) != set(dims):
            raise InvalidReview(f"rate exactly these: {', '.join(dims)}")
        for k, v in ratings.items():
            if not isinstance(v, int) or isinstance(v, bool):
                raise InvalidReview(f"{k} must be a whole number")
            if not self.cfg.rating_min <= v <= self.cfg.rating_max:
                raise InvalidReview(
                    f"{k} must be from {self.cfg.rating_min} to {self.cfg.rating_max}"
                )
        if comment is not None and len(comment) > 1000:
            raise InvalidReview("the comment is longer than 1000 characters")
        return {d: int(ratings[d]) for d in dims}

    def _flags(
        self,
        reviewer: UUID,
        reviewee: UUID,
        ratings: Mapping[str, int],
        comment: str | None,
        loan: Mapping[str, Any],
    ) -> tuple[bool, bool]:
        """(retaliation_flag, similarity_flag) for this review, by Algorithm 3's own rules."""
        reach = self.now - timedelta(days=self.p.retaliation_window_days)
        this = ReviewSnapshot(
            NEW_REVIEW,
            str(reviewer),
            str(reviewee),
            min(ratings.values()),
            comment,
            self.now,
            bool(loan["return_confirmed"]),
        )
        given_by_reviewee = [
            r for r in self.store.reviews_given(reviewee, reach) if r.reviewee == str(reviewer)
        ]
        complaints = [
            Complaint(str(reviewee), str(reviewer), at)
            for at in self.store.disputes_raised(reviewee, reviewer, reach)
        ]
        flags = find_retaliation(str(reviewee), [this, *given_by_reviewee], complaints, self.p)
        retaliation = any(f.review_id == NEW_REVIEW for f in flags)

        similar = False
        if comment:
            since = self.now - timedelta(days=self.p.window_days)
            others = [
                r["comment"]
                for r in self.store.reviews_received(reviewee, since)
                if r["comment"] and r["reviewer_id"] != reviewer
            ]
            similar = bool(others) and (
                max_cosine_to(comment, others, self.p.s4_char_ngram) >= self.p.s4_min_cosine
            )
        return retaliation, similar
