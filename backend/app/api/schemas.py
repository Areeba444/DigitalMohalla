"""Request and response models of the REST API (Architecture_Design.md section 4).

Responses carry ids, states and evidence only. No address, coordinates or CNIC field exists in any
model (NFR-PR-01, NFR-S-07), and an assurance state is always returned with its evidence and
explanation, never as a single trust number (NFR-U-01).
"""

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictIn(BaseModel):
    """Request bodies refuse unknown fields (422), so no client can send a location, an address or
    an identity number that would be silently ignored (TC-60, NFR-PR-01)."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _no_nul_characters(cls, data: Any) -> Any:
        """PostgreSQL text cannot hold NUL; refuse it as bad input (422) instead of failing (500)."""

        def has_nul(v: Any) -> bool:
            if isinstance(v, str):
                return "\x00" in v
            if isinstance(v, dict):
                return any(has_nul(k) or has_nul(x) for k, x in v.items())
            if isinstance(v, list):
                return any(has_nul(x) for x in v)
            return False

        if has_nul(data):
            raise ValueError("text may not contain NUL characters")
        return data


class LoginIn(StrictIn):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RequestIn(StrictIn):
    item_id: UUID
    start_date: date
    end_date: date = Field(description="Exclusive end: the item is returned by this date")
    message: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _dates_in_order(self) -> "RequestIn":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    def period(self) -> str:
        return f"[{self.start_date}T00:00:00+00,{self.end_date}T00:00:00+00)"


class DeclineIn(StrictIn):
    reason: str | None = Field(default=None, max_length=200)


class ChecklistIn(StrictIn):
    checklist: dict[str, Any] = Field(default_factory=dict)
    deposit_received: bool | None = None
    notes: str | None = Field(default=None, max_length=500)


class ConfirmIn(StrictIn):
    condition_agreed: bool = True
    checklist: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=500)


class CommandOut(BaseModel):
    transaction_id: UUID
    state: str | None
    message: str | None = None
    hold_reason: str | None = None


class PathOut(BaseModel):
    """One community path from the lender to the borrower, by display name only (no user ids)."""

    via: list[str]  # the intermediaries; empty when the lender lent to the borrower before
    strength: float


class CommunityOut(BaseModel):
    """Indirect evidence (FR-T-04): it can support a request but never makes it SUFFICIENT."""

    reliability: float  # rho, capped by the config
    paths: list[PathOut]


class AssessmentOut(BaseModel):
    assurance_state: str
    policy_decision: str
    rule_fired: str
    config_version: str
    explanation: str
    safeguards: list[Any]
    posterior_mean: float | None = None
    ci90_low: float | None = None
    ci90_high: float | None = None
    effective_evidence: float | None = None
    verified_loans: int | None = None  # the borrower's verified outcomes behind the interval
    community: CommunityOut | None = None
    # risk is a separate dimension and is never averaged with reliability (FR-T-05, NFR-U-01)
    manipulation_risk: int = 0
    manipulation_level: int = 1


class ReportOut(BaseModel):
    phase: str
    reporter_role: str
    condition_agreed: bool
    checklist: Any
    deposit_received: bool | None = None
    notes: str | None = None
    created_at: datetime
    photos: int = 0
    reduced_evidence: bool = True  # FR-B-11: a checklist without photos is marked as such

    @model_validator(mode="after")
    def _mark(self) -> "ReportOut":
        self.reduced_evidence = self.photos == 0
        return self


class RequestOut(BaseModel):
    transaction_id: UUID
    item_id: UUID
    item_title: str
    state: str | None
    hold_reason: str | None
    your_role: str | None
    borrower_name: str
    lender_name: str
    requested_period: str
    message: str | None
    deposit_required: bool
    assessment: AssessmentOut | None
    reports: list[ReportOut]
    available_actions: list[str]
    moderator_safeguards: list[Any] = []  # imposed when a moderator cleared a hold


class MyRequestOut(BaseModel):
    id: UUID
    item_id: UUID
    title: str
    state: str | None
    hold_reason: str | None
    requested_period: str
    your_role: str
    counterpart_name: str
    assurance_state: str | None


class BrowseItemOut(BaseModel):
    id: UUID
    title: str
    value_band: str
    deposit_amount: float
    owner_name: str


class EventOut(BaseModel):
    stream_seq: int
    event_type: str
    previous_state: str | None
    new_state: str
    occurred_at: datetime
    authorisation: str
    config_version: str | None = None


class DisputeIn(StrictIn):
    """UC-B12 step 2: a reason from the fixed list and a description (photos come with C2 uploads)."""

    reason: Literal["DAMAGE", "NON_RETURN", "CONDITION_MISMATCH", "NO_SHOW", "OTHER"]
    description: str | None = Field(default=None, max_length=1000)


class CaseOut(BaseModel):
    """An escalation case. The raiser is given by role only, never by user id."""

    id: UUID
    trigger_type: str
    dispute_reason: str | None = None
    hold_reason: str | None = None
    raised_by_role: str | None = None
    status: str
    priority: int
    reason: str
    opened_at: datetime
    closed_at: datetime | None = None
    info_deadline: datetime | None = None  # set while AWAITING_INFORMATION; kept after (C04)


class InformationRequestOut(BaseModel):
    """The moderator's latest question (sequence (g)); `to` is BORROWER, LENDER or BOTH."""

    to: str
    question: str
    deadline: datetime


class StatementOut(BaseModel):
    """A party's response on a case. The author is named and given by role, never by id."""

    id: UUID
    author_role: str
    author_name: str
    statement: str
    created_at: datetime


class InformationRequestIn(StrictIn):
    to: Literal["BORROWER", "LENDER", "BOTH"]
    question: str = Field(max_length=1000)


class InformationRequestedOut(BaseModel):
    case_id: UUID
    status: str
    deadline: datetime


class StatementIn(StrictIn):
    statement: str = Field(max_length=2000)


class StatementCreatedOut(BaseModel):
    id: UUID
    case_status: str


class DisputeTrailOut(BaseModel):
    """UC-D6 evidence trail: the case, the loan, both sides' reports, the history, the assessment."""

    case: CaseOut
    transaction_id: UUID
    item_title: str
    state: str | None
    your_role: str | None
    borrower_name: str
    lender_name: str
    requested_period: str
    reports: list[ReportOut]
    events: list[EventOut]
    assessment: AssessmentOut | None
    available_actions: list[str]
    information_request: InformationRequestOut | None = None
    statements: list[StatementOut] = []


class DecisionIn(StrictIn):
    """UC-I4: the decision, its mandatory reason (FR-T-11), and what it needs."""

    kind: Literal["CLEARED", "SAFEGUARDS_IMPOSED", "RESTRICTED", "DISPUTE_RESOLVED"]
    reason: str = Field(min_length=1, max_length=1000)
    safeguards: list[str] = Field(default_factory=list, max_length=10)
    at_fault: Literal["borrower", "lender", "none"] | None = None
    # disputes only: where the item is now (ADR-0009); it decides how the loan ends
    possession: Literal["NOT_HANDED_OVER", "WITH_BORROWER", "RETURNED", "LOST"] | None = None


class DecisionOut(BaseModel):
    id: UUID  # needed to reverse it (POST /moderation/decisions/{id}/reversal)
    decider_role: str
    kind: str
    reason: str
    safeguards: list[Any]
    resolved_outcome: Any = None
    decided_at: datetime


class CaseQueueOut(BaseModel):
    """One row of the moderator queue (W6): no names or ids of the people involved."""

    id: UUID
    transaction_id: UUID
    trigger_type: str
    dispute_reason: str | None = None
    hold_reason: str | None = None
    status: str
    priority: int
    reason: str
    opened_at: datetime
    item_title: str
    state: str | None


class ModeratorCaseOut(BaseModel):
    """UC-D6 evidence trail for the moderator (W7)."""

    case: CaseOut
    transaction_id: UUID
    item_title: str
    state: str | None
    hold_reason: str | None
    borrower_name: str
    lender_name: str
    requested_period: str
    reports: list[ReportOut]
    events: list[EventOut]
    assessment: AssessmentOut | None
    decisions: list[DecisionOut]
    information_request: InformationRequestOut | None = None
    statements: list[StatementOut] = []


class LenderRequestOut(BaseModel):
    id: UUID
    item_id: UUID
    title: str
    state: str | None
    assurance_state: str | None
    requested_period: str


class ListingFields(StrictIn):
    """Fields a lender sets on a listing (UC-B1, W22). Omitted fields are left unchanged on an edit."""

    title: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    category_id: int | None = None
    condition: Literal["NEW", "GOOD", "FAIR", "WORN"] | None = None
    value_band: Literal["LOW", "MEDIUM", "HIGH"] | None = None
    deposit_amount: float | None = Field(default=None, ge=0, le=10_000_000)
    usage_terms: str | None = Field(default=None, max_length=2000)
    handover_method: str | None = Field(default=None, max_length=200)
    search_terms: str | None = Field(default=None, max_length=300)
    expires_at: datetime | None = None


class ListingCreateIn(ListingFields):
    community_id: UUID
    publish: bool = False  # false saves a draft


class ListingUpdateIn(ListingFields):
    status: Literal["DRAFT", "PUBLISHED", "PAUSED"] | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    is_restricted: bool
    min_verification: str


class ListingOut(BaseModel):
    """A listing as its owner or a member sees it. The owner is named, never identified by id."""

    id: UUID
    title: str
    description: str | None
    category_id: int
    category_name: str
    community_name: str
    condition: str | None
    value_band: str
    deposit_amount: float
    usage_terms: str | None
    handover_method: str | None
    search_terms: str | None
    required_verification: str
    status: str
    expires_at: datetime | None
    owner_name: str
    is_yours: bool


class MyListingOut(BaseModel):
    id: UUID
    title: str
    value_band: str
    deposit_amount: float
    status: str
    condition: str | None
    updated_at: datetime


class ItemOut(ListingOut):
    """GET /items/{id}: the listing plus the dates already booked (B4, B5 step 1)."""

    booked_periods: list[str]


# ----------------------------------------------------------------------------- notifications (G3)
class NotificationOut(BaseModel):
    """One in-app notification. The app writes the sentence from `type` and `payload`."""

    id: UUID
    type: str
    payload: dict[str, Any]
    created_at: datetime
    read_at: datetime | None


class InboxOut(BaseModel):
    unread_count: int
    notifications: list[NotificationOut]


class MarkReadIn(StrictIn):
    """`ids` omitted means "mark everything read"."""

    ids: list[UUID] | None = Field(default=None, max_length=200)


class MarkReadOut(BaseModel):
    marked: int


# ----------------------------------------------------------------------------- membership (A3, A4)
class CommunityListOut(BaseModel):
    id: UUID
    name: str
    join_code: str
    rules: str | None
    join_policy: str
    member_count: int
    methods: list[str]
    has_boundary: bool


class FixIn(StrictIn):
    """One-time device fix. Evaluated in memory by the LocalityVerifier and then dropped: it is
    never stored, logged or returned (NFR-PR-01, sequence (d))."""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy_m: float = Field(ge=0, le=100_000)
    mock_provider: bool = False


class JoinIn(StrictIn):
    fix: FixIn | None = None
    permission_refused: bool = False
    invitation_code: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def _fix_or_refusal(self) -> "JoinIn":
        if self.permission_refused and self.fix is not None:
            raise ValueError("send either a fix or permission_refused, not both")
        return self


class LocalityOut(BaseModel):
    """The outcome in neutral words; never a rejection (FR-A-08)."""

    outcome: Literal["VERIFIED", "INCONCLUSIVE", "CONFLICTING"]
    message: str
    invitation_used: bool


class JoinOut(BaseModel):
    membership_id: UUID
    status: str
    locality: LocalityOut


class InvitationOut(BaseModel):
    """The code is shown once; only its hash is stored."""

    code: str
    expires_at: datetime


class MembershipQueueOut(BaseModel):
    membership_id: UUID
    status: str
    requested_at: datetime
    community_id: UUID
    community_name: str
    applicant_name: str
    locality_outcome: str | None
    boundary_signal: str | None  # coarse INSIDE / NEAR_BOUNDARY / OUTSIDE / UNAVAILABLE only
    invitation_used: bool
    permission_refused: bool
    mock_provider_detected: bool
    duplicate_suspected: bool


class MembershipDecisionIn(StrictIn):
    kind: Literal["APPROVED", "REJECTED", "INFO_REQUESTED", "REVERSED"]
    reason: str = Field(max_length=1000)
    reverses_decision_id: UUID | None = None


class MembershipDecisionOut(BaseModel):
    membership_id: UUID
    status: str


# ----------------------------------------------------------------------------- scheduler (B13)
class JobRunIn(StrictIn):
    """`as_of` is honoured only when the API runs with DEMO_CLOCK on (ADR-0012 point 5)."""

    as_of: datetime | None = None


class JobCountsOut(BaseModel):
    job: str
    ran: int
    skipped: int
    failed: int
    errors: list[str]


class JobReportOut(BaseModel):
    now: datetime
    lock_acquired: bool
    jobs: list[JobCountsOut]


# ----------------------------------------------------------------------------- extensions (B8 1a)
class ExtensionIn(StrictIn):
    """The borrower asks to return later: the new last day, exclusive like `end_date` of a request."""

    new_due_date: date
    reason: str | None = Field(default=None, max_length=500)


# ----------------------------------------------------------------------------- counter-offer (B6 3b)
class CounterOfferIn(StrictIn):
    """Other dates the lender offers (ADR-0015); same date rules as a request."""

    start_date: date
    end_date: date
    message: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _dates_in_order(self) -> "CounterOfferIn":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    def period(self) -> str:
        return f"[{self.start_date}T00:00:00+00,{self.end_date}T00:00:00+00)"


# ----------------------------------------------------------------------------- reviews (D1)
class ReviewIn(StrictIn):
    """One rating per dimension of the other party's role (config `reviews_d1.dimensions`)."""

    ratings: dict[str, int]
    comment: str | None = Field(default=None, max_length=1000)


class ReviewOut(BaseModel):
    """The review was stored. Flags are not returned to the reviewer (sequence (f))."""

    id: UUID
    reviewee_role: str
    editable_until: datetime


# ----------------------------------------------------------------------------- appeals (I4 4b, 4c)
class AppealIn(StrictIn):
    reason: str = Field(max_length=1000)


class AppealFiledOut(BaseModel):
    case_id: UUID
    status: str


class AppealDecisionIn(StrictIn):
    result: Literal["UPHELD", "OVERTURNED"]
    reason: str = Field(max_length=1000)


class AppealDecidedOut(BaseModel):
    """The new decision; `flagged_outcomes` counts the loan outcomes now under re-evaluation."""

    decision_id: UUID
    status: str
    flagged_outcomes: int


# ----------------------------------------------------------------------------- photos (ADR-0014)
class AttachmentOut(BaseModel):
    """A stored photo. `url` is a short-lived signed link, never a public address."""

    id: UUID
    url: str
    expires_at: int
    mime_type: str


class AttachmentUrlOut(BaseModel):
    url: str
    expires_at: int


# ----------------------------------------------------------------------------- search (B3)
class SearchResultOut(BaseModel):
    """One result: the listing, whether it is in the member's community, and a reason line in
    plain words. Scores are kept for evaluation and never returned (FR-S-01, NFR-U-01)."""

    item_id: UUID
    title: str
    condition: str | None
    value_band: str
    deposit_amount: float
    category_name: str
    community_name: str
    owner_name: str
    same_community: bool
    available: bool | None  # true when dates were given (booked items are filtered out)
    reason: str


class SearchOut(BaseModel):
    query_id: UUID | None  # set when the search is logged (FR-S-05)
    mode: Literal["HYBRID", "KEYWORD_ONLY"]
    total: int
    results: list[SearchResultOut]
