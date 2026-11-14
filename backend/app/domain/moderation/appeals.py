"""AppealService: appeal, a second moderator's decision, and later reversal (Module 9, M3, ES-11).

Sequence (h) and the escalation-case state machine DA-07:

    C08  DECIDED  --appeal_filed [a party; within moderation_i4.appeal_window_days of the decision;
                                  one appeal per case] / assigned to a moderator other than the first
                                  decider (an admin if none)--> APPEALED
    C09  APPEALED --appeal_decided [upheld; a second moderator, not the first decider; reason]
                                  / APPEAL_UPHELD--> DECIDED
    C10  APPEALED --appeal_decided [overturned; same guards] / APPEAL_OVERTURNED--> REVERSED
    C11  DECIDED  --decision_reversed [a moderator of the community or an admin; reason]
                                  / REVERSAL--> REVERSED

Both decisions always stay in `moderator_decision` (append-only; `decision_reversal_ck` makes the
second reference the first). Overturning or reversing a decision does not rewind the loan: the
outcomes that decision produced are marked FLAGGED_FOR_REEVALUATION with the new decision as the
reason, and both parties' trust edges are recomputed. The estimator and the edges already count only
VALID outcomes, so the next assessment of either party changes without any engine change (ES-11).
Case actions are not lifecycle events; each is an audit entry.
"""

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from app.domain.lifecycle.errors import InvalidTransition, NotAuthorised, StreamNotFound
from app.domain.moderation.cases import InvalidCaseInput
from app.domain.notifications.notify import INotify, NullNotifier

FIRST_DECISIONS = ("CLEARED", "SAFEGUARDS_IMPOSED", "RESTRICTED", "DISPUTE_RESOLVED")


class AppealStore(Protocol):
    def case_for_update(self, case_id: UUID) -> dict[str, Any] | None: ...

    def decision(self, decision_id: UUID) -> dict[str, Any] | None: ...

    def appealed_decision(self, case_id: UUID) -> dict[str, Any] | None:
        """The case's latest first-instance decision (the one an appeal or reversal is about)."""
        ...

    def latest_decision(self, case_id: UUID) -> dict[str, Any] | None: ...

    def appeal_count(self, case_id: UUID) -> int: ...

    def is_moderator(self, user_id: UUID, community_id: UUID) -> bool: ...

    def moderators_of(self, community_id: UUID) -> list[UUID]: ...

    def admins(self) -> list[UUID]: ...

    def set_status(self, case_id: UUID, status: str, assigned_to: UUID | None = None) -> None: ...

    def insert_decision(
        self,
        case_id: UUID,
        decided_by: UUID,
        role: str,
        kind: str,
        reason: str,
        reverses: UUID | None,
    ) -> UUID: ...

    def flag_outcomes(self, decision_id: UUID, flagged_by: UUID) -> int: ...

    def refresh_trust_edges(self, transaction_id: UUID) -> int: ...

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


class AppealService:
    def __init__(
        self,
        store: AppealStore,
        *,
        now: datetime,
        appeal_window_days: float,
        notifier: INotify | None = None,
    ) -> None:
        self.store = store
        self.now = now
        self.window = timedelta(days=appeal_window_days)
        self.notifier: INotify = notifier or NullNotifier()

    # ------------------------------------------------------------------ C08
    def file_appeal(self, actor_id: UUID, case_id: UUID, reason: str) -> UUID:
        """A party appeals; returns who will decide it (a second moderator, or an admin)."""
        reason = (reason or "").strip()
        case = self._case(case_id)
        if actor_id not in (case["borrower_id"], case["lender_id"]):
            self._refuse(actor_id, case_id, "file_appeal", "not a party to this loan")
            raise NotAuthorised("only the borrower or the lender of this loan can appeal")
        if not reason:
            raise InvalidCaseInput("say why you are appealing")
        first = self.store.appealed_decision(case_id)
        if case["status"] != "DECIDED" or first is None:
            raise InvalidTransition("only a decided case can be appealed")
        if self.store.appeal_count(case_id) > 0:
            self._refuse(actor_id, case_id, "file_appeal", "already appealed")
            raise InvalidTransition("this case has already been appealed once")
        if self.now > first["decided_at"] + self.window:
            raise InvalidTransition("the appeal window for this decision has closed")
        second = self._second_decider(case, first["decided_by"])
        self.store.set_status(case_id, "APPEALED", assigned_to=second)
        self.store.audit(
            actor_id=actor_id,
            authorisation=f"party:{self._role(actor_id, case).lower()}",
            action="appeal_filed",
            case_id=case_id,
            new_value={"reason": reason, "decision_id": str(first["id"]), "assigned_to": "second"},
        )
        payload = {"case_id": str(case_id), "transaction_id": str(case["transaction_id"])}
        self.notifier.notify(second, "appeal_to_decide", payload, f"{case_id}:appeal")
        other = case["lender_id"] if actor_id == case["borrower_id"] else case["borrower_id"]
        self.notifier.notify(other, "appeal_filed", payload, f"{case_id}:appeal")
        return second

    # ------------------------------------------------------------------ C09, C10
    def decide_appeal(
        self, actor_id: UUID, platform_role: str, case_id: UUID, upheld: bool, reason: str
    ) -> dict[str, Any]:
        reason = (reason or "").strip()
        case = self._case(case_id)
        role, authorisation = self._moderator(actor_id, platform_role, case, "decide_appeal")
        if case["status"] != "APPEALED":
            raise InvalidTransition(f"this case is {case['status'].lower()}, not under appeal")
        first = self.store.appealed_decision(case_id)
        if first is None:  # cannot happen for an APPEALED case; refuse rather than guess
            raise InvalidTransition("this case has no decision to appeal")
        if first["decided_by"] == actor_id:
            self._refuse(actor_id, case_id, "decide_appeal", "same moderator as the first decision")
            raise NotAuthorised("a second moderator must decide the appeal, not the first decider")
        if not reason:
            raise InvalidCaseInput("a reason is required for every appeal decision")
        if upheld:
            decision = self.store.insert_decision(
                case_id, actor_id, role, "APPEAL_UPHELD", reason, None
            )
            self.store.set_status(case_id, "DECIDED")
            flagged = 0
        else:
            decision = self.store.insert_decision(
                case_id, actor_id, role, "APPEAL_OVERTURNED", reason, first["id"]
            )
            self.store.set_status(case_id, "REVERSED")
            flagged = self._reevaluate(first["id"], decision, case["transaction_id"])
        kind = "upheld" if upheld else "overturned"
        self.store.audit(
            actor_id=actor_id,
            authorisation=authorisation,
            action="appeal_decided",
            case_id=case_id,
            new_value={"result": kind, "reason": reason, "flagged_outcomes": flagged},
        )
        self._tell_parties(case, f"appeal_{kind}", {"reason": reason}, f"{case_id}:appeal_decided")
        return {
            "decision_id": decision,
            "status": "DECIDED" if upheld else "REVERSED",
            "flagged_outcomes": flagged,
        }

    # ------------------------------------------------------------------ C11
    def reverse(
        self, actor_id: UUID, platform_role: str, decision_id: UUID, reason: str
    ) -> dict[str, Any]:
        reason = (reason or "").strip()
        old = self.store.decision(decision_id)
        if old is None:
            raise StreamNotFound(f"decision {decision_id}")
        case = self._case(old["case_id"])
        role, authorisation = self._moderator(actor_id, platform_role, case, "reverse_decision")
        if not reason:
            raise InvalidCaseInput("a reason is required to reverse a decision")
        latest = self.store.latest_decision(case["id"])
        if case["status"] != "DECIDED" or latest is None or latest["id"] != decision_id:
            raise InvalidTransition("only the latest decision of a decided case can be reversed")
        new = self.store.insert_decision(
            case["id"], actor_id, role, "REVERSAL", reason, decision_id
        )
        self.store.set_status(case["id"], "REVERSED")
        flagged = self._reevaluate(decision_id, new, case["transaction_id"])
        self.store.audit(
            actor_id=actor_id,
            authorisation=authorisation,
            action="decision_reversed",
            case_id=case["id"],
            new_value={"reverses": str(decision_id), "reason": reason, "flagged_outcomes": flagged},
        )
        self._tell_parties(case, "decision_reversed", {"reason": reason}, f"{case['id']}:reversed")
        return {"decision_id": new, "status": "REVERSED", "flagged_outcomes": flagged}

    # ------------------------------------------------------------------ helpers
    def _reevaluate(self, old_decision: UUID, new_decision: UUID, txn_id: UUID) -> int:
        """Outcomes the old decision produced stop counting; trust edges follow (ADR-0006)."""
        flagged = self.store.flag_outcomes(old_decision, new_decision)
        if flagged:
            self.store.refresh_trust_edges(txn_id)
        return flagged

    def _second_decider(self, case: Mapping[str, Any], first: UUID) -> UUID:
        parties = (case["borrower_id"], case["lender_id"])
        for m in self.store.moderators_of(case["community_id"]):
            if m != first and m not in parties:
                return m
        for a in self.store.admins():
            if a != first and a not in parties:
                return a
        raise InvalidTransition("no second moderator or admin is available to hear this appeal")

    def _tell_parties(
        self, case: Mapping[str, Any], type_: str, extra: Mapping[str, Any], key: str
    ) -> None:
        payload = {
            "case_id": str(case["id"]),
            "transaction_id": str(case["transaction_id"]),
            **extra,
        }
        for party in (case["borrower_id"], case["lender_id"]):
            self.notifier.notify(party, type_, payload, key)

    def _case(self, case_id: UUID) -> dict[str, Any]:
        case = self.store.case_for_update(case_id)
        if case is None:
            raise StreamNotFound(f"case {case_id}")
        return case

    @staticmethod
    def _role(actor_id: UUID, case: Mapping[str, Any]) -> str:
        return "BORROWER" if actor_id == case["borrower_id"] else "LENDER"

    def _moderator(
        self, actor_id: UUID, platform_role: str, case: Mapping[str, Any], action: str
    ) -> tuple[str, str]:
        if actor_id in (case["borrower_id"], case["lender_id"]):
            reason = "a party cannot decide its own case"
        elif platform_role == "ADMIN":
            return "ADMIN", "role:admin"
        elif self.store.is_moderator(actor_id, case["community_id"]):
            return "MODERATOR", f"role:moderator@{case['community_id']}"
        else:
            reason = "not a moderator of this community"
        self._refuse(actor_id, case["id"], action, reason)
        raise NotAuthorised(reason)

    def _refuse(self, actor_id: UUID, case_id: UUID, action: str, reason: str) -> None:
        self.store.audit_rejection(
            actor_id=actor_id, action=f"reject_{action}", case_id=case_id, reason=reason
        )
