"""Interfaces between Module 3 (lifecycle) and its neighbours (Architecture_Design.md section 3).

Slice A runs with stubs behind these interfaces; later slices replace them without touching the
lifecycle service (class model, design reasoning).
"""

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID


class EngineTimeout(Exception):
    """The assurance engine did not answer within `engine_timeout_ms` (FR-T-07)."""


@dataclass(frozen=True)
class AssessmentRequest:
    transaction_id: UUID
    borrower_id: UUID
    lender_id: UUID
    item_id: UUID
    value_band: str
    category_id: int
    config_version: str


@dataclass(frozen=True)
class AssessmentResult:
    """Output of IAssess. Trust evidence and manipulation risk are separate fields, never merged."""

    assurance_state: str
    policy_decision: str
    rule_fired: str
    hold_reason: str | None
    explanation: str
    config_version: str
    manipulation_risk: int = 0
    manipulation_level: int = 1
    manipulation_corroborated: bool = False
    posterior_mean: float | None = None
    ci90_low: float | None = None
    ci90_high: float | None = None
    effective_evidence: float | None = None
    direct_evidence: dict[str, Any] = field(default_factory=dict)
    indirect_evidence: dict[str, Any] = field(default_factory=dict)
    manipulation_signals: list[Any] = field(default_factory=list)
    safeguards: list[Any] = field(default_factory=list)


class IAssess(Protocol):
    """Module 5 boundary: raises EngineTimeout (or any exception) on failure."""

    def assess(self, request: AssessmentRequest) -> AssessmentResult: ...


@dataclass(frozen=True)
class TransactionView:
    """What the service needs to know about one transaction (read model)."""

    id: UUID
    item_id: UUID
    borrower_id: UUID
    lender_id: UUID
    community_id: UUID
    value_band: str
    category_id: int
    state: str | None
    version: int
    hold_reason: str | None
    due_at: Any


class LifecycleStore(Protocol):
    """Persistence used by BorrowingService. Implemented by PostgresLifecycleStore (infra)."""

    def create_request(
        self, *, item_id: UUID, borrower_id: UUID, lender_id: UUID, period: str, message: str | None
    ) -> UUID: ...

    def append(
        self,
        stream_id: UUID,
        event_type: str,
        new_state: str,
        *,
        actor_id: UUID | None,
        authorisation: str,
        payload: dict[str, Any] | None = None,
        evidence_refs: dict[str, Any] | None = None,
        config_version: str | None = None,
    ) -> int: ...

    def view(self, transaction_id: UUID) -> TransactionView: ...

    def locality_outcome(self, user_id: UUID, community_id: UUID) -> str: ...

    def insert_assessment(self, transaction_id: UUID, result: AssessmentResult) -> UUID: ...

    def insert_condition_report(
        self,
        transaction_id: UUID,
        *,
        phase: str,
        reporter_id: UUID,
        reporter_role: str,
        condition_agreed: bool,
        checklist: dict[str, Any],
        deposit_received: bool | None,
        notes: str | None,
    ) -> UUID: ...

    def last_event(self, transaction_id: UUID, event_type: str) -> dict[str, Any] | None: ...

    def overlapping_pending(self, transaction_id: UUID) -> list[UUID]: ...

    def item(self, item_id: UUID) -> dict[str, Any]: ...

    def latest_assessment(self, transaction_id: UUID) -> dict[str, Any] | None: ...

    def savepoint(self) -> AbstractContextManager[Any]: ...

    def list_for_lender(self, lender_id: UUID, state: str | None) -> list[dict[str, Any]]: ...

    def booked_periods(self, item_id: UUID) -> list[str]: ...

    def events(self, transaction_id: UUID) -> list[dict[str, Any]]: ...

    def list_items_for(self, user_id: UUID) -> list[dict[str, Any]]: ...

    def list_for_member(self, user_id: UUID) -> list[dict[str, Any]]: ...

    def details(self, transaction_id: UUID) -> dict[str, Any]: ...

    def latest_reports(self, transaction_id: UUID) -> dict[tuple[str, str], dict[str, Any]]: ...

    def record_outcomes(self, event_id: int) -> int:
        """Write the verified outcomes of a closing event (FR-B-15); returns rows added."""
        ...


class AuditLog(Protocol):
    """Records rejected commands outside the command's own transaction (suite 1, FR-M-05)."""

    def record_rejection(
        self,
        *,
        actor_id: UUID | None,
        authorisation: str,
        action: str,
        transaction_id: UUID,
        reason: str,
    ) -> None: ...
