"""CaseService: information requests, party statements, deadlines and admin routing (Module 9, M2).

Follows sequence (g) "information request" and the escalation-case state machine DA-07:

    C02  OPEN --info_requested [moderator of the community, not a party] / deadline--> AWAITING_INFORMATION
    C03  AWAITING_INFORMATION --statement [addressed party, before the deadline] / append--> OPEN
    C04  AWAITING_INFORMATION --deadline passed [scheduler] / "no response" kept--> OPEN

The moderator then decides as before (sequence (c), ADR-0009). Case actions are not lifecycle
events: each is an audit_log entry, and the case row holds the status and the deadline. The
question itself is kept in the `info_requested` audit entry, the moderator-authored record, because
`case_statement` is for the parties only (sequence (g) open point; no schema change).

FR-B-17 (parties notified, a response with evidence, "no response" passes to a moderator), FR-T-10
(a case with no moderator in its community goes to an admin) and FR-T-11 (information requests).
The deadline is `scheduler_b13.party_response_deadline_hours` from the versioned config.
"""

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any, Literal, Protocol
from uuid import UUID

from app.domain.lifecycle.errors import InvalidTransition, NotAuthorised, StreamNotFound
from app.domain.notifications.notify import INotify, NullNotifier

Addressee = Literal["BORROWER", "LENDER", "BOTH"]


class InvalidCaseInput(ValueError):
    """Bad input for a case action, such as an empty question (422)."""


class CaseStore(Protocol):
    def case_for_update(self, case_id: UUID) -> dict[str, Any] | None:
        """The case with its loan's parties and community, locked for this transaction."""
        ...

    def is_moderator(self, user_id: UUID, community_id: UUID) -> bool: ...

    def set_awaiting(self, case_id: UUID, deadline: datetime) -> None: ...

    def reopen(self, case_id: UUID) -> None: ...

    def insert_statement(self, case_id: UUID, author_id: UUID, role: str, text: str) -> UUID: ...

    def overdue_information(self, now: datetime) -> list[dict[str, Any]]: ...

    def information_request(self, case_id: UUID) -> dict[str, Any] | None:
        """The latest info_requested audit entry's value: to, question, deadline."""
        ...

    def moderators_of(self, community_id: UUID) -> list[UUID]: ...

    def admins(self) -> list[UUID]: ...

    def audit(
        self,
        *,
        actor_id: UUID | None,
        authorisation: str,
        action: str,
        case_id: UUID,
        new_value: Mapping[str, Any],
    ) -> None: ...

    def audit_rejection(
        self, *, actor_id: UUID, action: str, case_id: UUID, reason: str
    ) -> None: ...


class CaseService:
    def __init__(
        self,
        store: CaseStore,
        *,
        now: datetime,
        response_hours: float,
        notifier: INotify | None = None,
    ) -> None:
        self.store = store
        self.now = now
        self.response_hours = response_hours
        self.notifier: INotify = notifier or NullNotifier()

    # ------------------------------------------------------------------ C02 (sequence (g) part 1)
    def request_information(
        self, actor_id: UUID, platform_role: str, case_id: UUID, to: Addressee, question: str
    ) -> datetime:
        question = (question or "").strip()
        case = self._case(case_id)
        authorisation = self._moderator(actor_id, platform_role, case, "request_information")
        if not question:
            raise InvalidCaseInput("write the question the party should answer")
        if case["status"] != "OPEN":
            self.store.audit_rejection(
                actor_id=actor_id,
                action="reject_request_information",
                case_id=case_id,
                reason=f"case is {case['status']}",
            )
            raise InvalidTransition(f"this case is {case['status'].lower().replace('_', ' ')}")
        deadline = self.now + timedelta(hours=self.response_hours)
        self.store.set_awaiting(case_id, deadline)
        self.store.audit(
            actor_id=actor_id,
            authorisation=authorisation,
            action="info_requested",
            case_id=case_id,
            new_value={"to": to, "question": question, "deadline": deadline.isoformat()},
        )
        payload = {
            "case_id": str(case_id),
            "transaction_id": str(case["transaction_id"]),
            "question": question,
            "deadline": deadline.isoformat(),
        }
        for party in self._addressed(case, to):
            self.notifier.notify(
                party, "information_requested", payload, f"{case_id}:info:{deadline.isoformat()}"
            )
        return deadline

    # ------------------------------------------------------------------ C03 (sequence (g) part 2)
    def add_statement(self, actor_id: UUID, case_id: UUID, statement: str) -> UUID:
        statement = (statement or "").strip()
        case = self._case(case_id)
        role = self._party_role(actor_id, case)
        if role is None:
            self.store.audit_rejection(
                actor_id=actor_id,
                action="reject_case_statement",
                case_id=case_id,
                reason="not a party to this loan",
            )
            raise NotAuthorised("only the borrower or the lender of this loan can respond")
        if not statement:
            raise InvalidCaseInput("the response cannot be empty")
        asked = self.store.information_request(case_id)
        addressed = asked is not None and asked.get("to") in (role, "BOTH")
        if case["status"] != "AWAITING_INFORMATION" or not addressed:
            raise InvalidTransition("no information has been requested from you on this case")
        if case["info_deadline"] is not None and case["info_deadline"] <= self.now:
            raise InvalidTransition("the deadline for this response has passed")
        statement_id = self.store.insert_statement(case_id, actor_id, role, statement)
        self.store.reopen(case_id)
        self.store.audit(
            actor_id=actor_id,
            authorisation=f"party:{role.lower()}",
            action="info_received",
            case_id=case_id,
            new_value={"statement_id": str(statement_id)},
        )
        for m in self._deciders(case):
            self.notifier.notify(
                m,
                "information_received",
                {"case_id": str(case_id), "transaction_id": str(case["transaction_id"])},
                f"{case_id}:received:{statement_id}",
            )
        return statement_id

    # ------------------------------------------------------------------ C04 (scheduler, F4)
    def expire_information(self) -> int:
        """Cases whose deadline passed go back to OPEN; the deadline stays as evidence of
        non-response. A rerun finds none (idempotent, NFR-R-05); notices are deduplicated."""
        expired = self.store.overdue_information(self.now)
        for case in expired:
            self.store.reopen(case["id"])
            deadline = case["info_deadline"].isoformat()
            self.store.audit(
                actor_id=None,
                authorisation="system:scheduler",
                action="info_deadline_passed",
                case_id=case["id"],
                new_value={"deadline": deadline, "response": "none"},
            )
            for m in self._deciders(case):
                self.notifier.notify(
                    m,
                    "information_deadline_passed",
                    {"case_id": str(case["id"]), "transaction_id": str(case["transaction_id"])},
                    f"{case['id']}:deadline:{deadline}",
                )
        return len(expired)

    # ------------------------------------------------------------------ FR-T-10 routing
    def route_new_case(self, case_id: UUID) -> list[UUID]:
        """Tell who must act on a new case: the community's moderators, or the admins when the
        community has none (UC-D6 2a). Returns who was told."""
        case = self._case(case_id)
        deciders = self._deciders(case)
        payload = {
            "case_id": str(case_id),
            "transaction_id": str(case["transaction_id"]),
            "trigger": case["trigger_type"],
        }
        for m in deciders:
            self.notifier.notify(m, "case_opened", payload, f"{case_id}:opened")
        for party in (case["borrower_id"], case["lender_id"]):
            if case["trigger_type"] == "DISPUTE" and party != case["raised_by"]:
                self.notifier.notify(party, "dispute_opened", payload, f"{case_id}:dispute")
        return deciders

    # ------------------------------------------------------------------ helpers
    def _deciders(self, case: Mapping[str, Any]) -> list[UUID]:
        mods = [
            m
            for m in self.store.moderators_of(case["community_id"])
            if m not in (case["borrower_id"], case["lender_id"])
        ]
        return mods or self.store.admins()

    def _case(self, case_id: UUID) -> dict[str, Any]:
        case = self.store.case_for_update(case_id)
        if case is None:
            raise StreamNotFound(f"case {case_id}")
        return case

    @staticmethod
    def _party_role(actor_id: UUID, case: Mapping[str, Any]) -> str | None:
        if actor_id == case["borrower_id"]:
            return "BORROWER"
        if actor_id == case["lender_id"]:
            return "LENDER"
        return None

    @staticmethod
    def _addressed(case: Mapping[str, Any], to: Addressee) -> list[UUID]:
        return [
            case[f"{role.lower()}_id"] for role in ("BORROWER", "LENDER") if to in (role, "BOTH")
        ]

    def _moderator(
        self, actor_id: UUID, platform_role: str, case: Mapping[str, Any], action: str
    ) -> str:
        if actor_id in (case["borrower_id"], case["lender_id"]):
            reason = "a party cannot moderate its own case"
        elif platform_role == "ADMIN":
            return "role:admin"
        elif self.store.is_moderator(actor_id, case["community_id"]):
            return f"role:moderator@{case['community_id']}"
        else:
            reason = "not a moderator of this community"
        self.store.audit_rejection(
            actor_id=actor_id, action=f"reject_{action}", case_id=case["id"], reason=reason
        )
        raise NotAuthorised(reason)
