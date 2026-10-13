"""BorrowingService: the commands of the borrowing lifecycle (Module 3, IBorrowingCommands).

Follows sequence diagrams (a) request to assessment and (b) handover and return
(docs/design/08_sequence_diagrams) and the REST table in Architecture_Design.md section 4.
Every command appends at most the events its use case lists; the rules themselves (transition
table, who may act, the booking calendar, hash chain) are enforced by the database, and this class
adds a fast pre-check and an audit entry for every rejected command (suite 1).

Slice A scope: request -> locality -> assessment -> accept/decline/cancel -> handover -> return ->
completed. Disputes, holds' resolution and outcomes to the engine belong to Slices B and C.
"""

from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domain.lifecycle.actions import available_actions
from app.domain.lifecycle.errors import (
    DatesTaken,
    EventStoreError,
    InvalidTransition,
    NotAuthorised,
    StreamNotFound,
)
from app.domain.lifecycle.ports import (
    AssessmentRequest,
    AssessmentResult,
    AuditLog,
    EngineTimeout,
    IAssess,
    LifecycleStore,
    TransactionView,
)
from app.domain.lifecycle.transition_table import TransitionTable
from app.domain.moderation.decisions import Decision, InvalidDecision, plan

SYSTEM_AUTH = "system:borrowing-service"
_LOCALITY_HOLD = {"INCONCLUSIVE": "locality_inconclusive", "CONFLICTING": "locality_conflict"}
_engine_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="assess")


@dataclass(frozen=True)
class Actor:
    user_id: UUID
    platform_role: str = "MEMBER"


@dataclass(frozen=True)
class CommandResult:
    transaction_id: UUID
    state: str | None
    message: str | None = None
    hold_reason: str | None = None
    assessment_id: UUID | None = None


class BorrowingService:
    def __init__(
        self,
        store: LifecycleStore,
        engine: IAssess,
        audit: AuditLog,
        *,
        config_version: str,
        engine_timeout_ms: int = 2000,
        table: TransitionTable | None = None,
    ) -> None:
        self.store = store
        self.engine = engine
        self.audit = audit
        self.config_version = config_version
        self.engine_timeout_s = engine_timeout_ms / 1000
        self.table = table or TransitionTable.load()

    # ------------------------------------------------------------------ B5: send request
    def create_request(
        self, actor: Actor, item_id: UUID, period: str, message: str | None = None
    ) -> CommandResult:
        """UC-B5: create the request, check locality, run the assessment, and set the state.

        The request itself carries no location (decision D13); locality comes from the member's
        stored coarse result. Lands in ASSESSED, or HELD_FOR_REVIEW with a recorded reason.
        """
        item = self.store.item(item_id)
        txn_id = self.store.create_request(
            item_id=item_id,
            borrower_id=actor.user_id,
            lender_id=item["owner_id"],
            period=period,
            message=message,
        )
        return self._locality_and_assessment(txn_id)

    def _locality_and_assessment(self, txn_id: UUID) -> CommandResult:
        view = self.store.view(txn_id)
        outcome = self.store.locality_outcome(view.borrower_id, view.community_id)
        if outcome != "VERIFIED":
            return self._hold(txn_id, _LOCALITY_HOLD[outcome])
        self._system_event(
            txn_id, "locality_checked", "LOCALITY_CHECKED", {"locality_outcome": "VERIFIED"}
        )
        return self._assess(txn_id)

    def _assess(self, txn_id: UUID) -> CommandResult:
        """Run the engine on a request in LOCALITY_CHECKED: ASSESSED, or HELD_FOR_REVIEW."""
        view = self.store.view(txn_id)
        try:
            result = self._run_engine(view)
        except Exception as exc:  # timeout or fault: hold, assign no assurance state (FR-T-07)
            return self._hold(txn_id, "engine_failure", {"failure": type(exc).__name__})
        assessment_id = self.store.insert_assessment(txn_id, result)
        refs = {"assessment_id": str(assessment_id)}
        if result.hold_reason:
            self._system_event(
                txn_id,
                "held_for_review",
                "HELD_FOR_REVIEW",
                {"hold_reason": result.hold_reason},
                refs,
                result.config_version,
            )
            return CommandResult(txn_id, "HELD_FOR_REVIEW", None, result.hold_reason, assessment_id)
        self._system_event(
            txn_id, "assessment_generated", "ASSESSED", {}, refs, result.config_version
        )
        return CommandResult(txn_id, "ASSESSED", None, None, assessment_id)

    def _run_engine(self, view: TransactionView) -> AssessmentResult:
        request = AssessmentRequest(
            transaction_id=view.id,
            borrower_id=view.borrower_id,
            lender_id=view.lender_id,
            item_id=view.item_id,
            value_band=view.value_band,
            category_id=view.category_id,
            config_version=self.config_version,
            duration_days=view.duration_days,
        )
        future = _engine_pool.submit(self.engine.assess, request)
        try:
            return future.result(timeout=self.engine_timeout_s)
        except FutureTimeout as exc:
            future.cancel()
            raise EngineTimeout(f"no answer within {self.engine_timeout_s * 1000:.0f} ms") from exc

    def _hold(
        self, txn_id: UUID, reason: str, extra: Mapping[str, Any] | None = None
    ) -> CommandResult:
        payload = {"hold_reason": reason, **(extra or {})}
        self._system_event(txn_id, "held_for_review", "HELD_FOR_REVIEW", payload)
        return CommandResult(txn_id, "HELD_FOR_REVIEW", None, reason)

    def _system_event(
        self,
        txn_id: UUID,
        event_type: str,
        new_state: str,
        payload: Mapping[str, Any],
        evidence_refs: Mapping[str, Any] | None = None,
        config_version: str | None = None,
    ) -> int:
        return self.store.append(
            txn_id,
            event_type,
            new_state,
            actor_id=None,
            authorisation=SYSTEM_AUTH,
            payload=dict(payload),
            evidence_refs=dict(evidence_refs or {}),
            config_version=config_version,
        )

    # ------------------------------------------------------------------ B6: respond
    def accept(self, actor: Actor, txn_id: UUID) -> CommandResult:
        """T13. If the calendar refuses the dates, nothing is booked and the request ends DECLINED
        with reason dates_taken (ADR-0002). Call `decline_overlapping` after this commits."""
        view = self._precheck(actor, txn_id, "request_accepted", "LENDER")
        try:
            with self.store.savepoint():
                self._party_event(actor, view, "request_accepted", "LENDER")
        except DatesTaken:
            self._system_event(txn_id, "request_declined", "DECLINED", {"reason": "dates_taken"})
            return CommandResult(txn_id, "DECLINED", "dates taken")
        return CommandResult(txn_id, "ACCEPTED")

    def decline_overlapping(self, accepted_txn_id: UUID) -> list[UUID]:
        """T17: after an acceptance has committed, decline pending requests that overlap it.

        Run in a separate transaction from `accept`, so two simultaneous acceptances cannot wait
        on each other's rows.
        """
        declined: list[UUID] = []
        for other in self.store.overlapping_pending(accepted_txn_id):
            try:
                with self.store.savepoint():
                    self._system_event(
                        other, "request_declined", "DECLINED", {"reason": "dates_taken"}
                    )
                declined.append(other)
            except EventStoreError:
                continue  # no longer pending, or no longer overlapping
        return declined

    def decline(self, actor: Actor, txn_id: UUID, reason: str | None = None) -> CommandResult:
        view = self._precheck(actor, txn_id, "request_declined", "LENDER")
        payload = {"reason": reason} if reason else {}
        self._party_event(actor, view, "request_declined", "LENDER", payload)
        return CommandResult(txn_id, "DECLINED")

    def cancel(self, actor: Actor, txn_id: UUID) -> CommandResult:
        view = self._precheck(actor, txn_id, "request_cancelled", "BORROWER")
        self._party_event(actor, view, "request_cancelled", "BORROWER")
        return CommandResult(txn_id, "CANCELLED")

    # ------------------------------------------------------------------ B7: handover
    def record_handover_checklist(
        self,
        actor: Actor,
        txn_id: UUID,
        *,
        checklist: dict[str, Any] | None = None,
        deposit_received: bool | None = None,
        notes: str | None = None,
    ) -> CommandResult:
        """Lender's checklist (UC-B7 steps 1-2). Deposit is a record-only flag; no money moves."""
        view = self._require_party(actor, txn_id, "LENDER", "record_handover_checklist")
        self._require_state(actor, view, {"ACCEPTED"}, "record_handover_checklist")
        self.store.insert_condition_report(
            txn_id,
            phase="HANDOVER",
            reporter_id=actor.user_id,
            reporter_role="LENDER",
            condition_agreed=True,
            checklist=checklist or {},
            deposit_received=deposit_received,
            notes=notes,
        )
        return CommandResult(txn_id, "ACCEPTED", "lender checklist recorded")

    def confirm_handover(
        self,
        actor: Actor,
        txn_id: UUID,
        *,
        condition_agreed: bool = True,
        checklist: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> CommandResult:
        """Borrower's confirmation (UC-B7 steps 3-4). Moves to ACTIVE only when the pair is complete."""
        view = self._require_party(actor, txn_id, "BORROWER", "confirm_handover")
        self._require_state(actor, view, {"ACCEPTED"}, "confirm_handover")
        self.store.insert_condition_report(
            txn_id,
            phase="HANDOVER",
            reporter_id=actor.user_id,
            reporter_role="BORROWER",
            condition_agreed=condition_agreed,
            checklist=checklist or {},
            deposit_received=None,
            notes=notes,
        )
        if not condition_agreed:
            return CommandResult(
                txn_id, "ACCEPTED", "disagreement recorded; no handover (UC-B7 3a)"
            )
        try:
            with self.store.savepoint():
                self._party_event(actor, view, "handover_confirmed", "BORROWER")
        except InvalidTransition as exc:  # e.g. no lender checklist yet, or deposit not recorded
            return CommandResult(txn_id, "ACCEPTED", str(exc))
        return CommandResult(txn_id, "ACTIVE")

    # ------------------------------------------------------------------ B8: return
    def initiate_return(self, actor: Actor, txn_id: UUID) -> CommandResult:
        view = self._precheck(actor, txn_id, "return_initiated", "BORROWER")
        self._party_event(actor, view, "return_initiated", "BORROWER")
        return CommandResult(txn_id, "RETURN_INITIATED")

    def confirm_return(
        self,
        actor: Actor,
        txn_id: UUID,
        *,
        condition_agreed: bool = True,
        checklist: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> CommandResult:
        """Either party records their return report (UC-B8 steps 2-3). The lender goes first.

        When the borrower's agreeing report completes the pair, `return_confirmed` and
        `transaction_closed` are appended together (one DB transaction, T21 + T22).
        """
        view = self._store_view(txn_id)
        role = self._role_of(actor, view)
        if role is None:
            self._reject(actor, txn_id, "confirm_return", "not a party to this transaction")
            raise NotAuthorised("not a party to this transaction")
        self._require_state(actor, view, {"RETURN_INITIATED"}, "confirm_return")
        self.store.insert_condition_report(
            txn_id,
            phase="RETURN",
            reporter_id=actor.user_id,
            reporter_role=role,
            condition_agreed=condition_agreed,
            checklist=checklist or {},
            deposit_received=None,
            notes=notes,
        )
        if not condition_agreed:
            return CommandResult(
                txn_id, "RETURN_INITIATED", "disagreement recorded; a dispute is needed (UC-B8 3a)"
            )
        if role == "LENDER":
            return CommandResult(txn_id, "RETURN_INITIATED", "lender return checklist recorded")
        try:
            with self.store.savepoint():
                self._party_event(actor, view, "return_confirmed", "BORROWER")
        except InvalidTransition as exc:  # lender report missing, or made after the borrower's
            return CommandResult(txn_id, "RETURN_INITIATED", str(exc))
        returned = self.store.last_event(txn_id, "return_confirmed")
        due_at = self.store.view(txn_id).due_at
        outcome = "on_time" if returned and due_at and returned["occurred_at"] <= due_at else "late"
        closed = self._system_event(txn_id, "transaction_closed", "COMPLETED", {"outcome": outcome})
        # FR-B-15: the confirmed outcome becomes evidence in the same DB transaction as the close
        self.store.record_outcomes(closed)
        self.store.refresh_trust_edges(txn_id)  # ADR-0006: edges follow the new outcomes
        return CommandResult(txn_id, "COMPLETED", f"returned {outcome.replace('_', ' ')}")

    # ------------------------------------------------------------------ queries
    # ------------------------------------------------------------------ B12: disputes
    def raise_dispute(
        self, actor: Actor, txn_id: UUID, reason: str, description: str | None = None
    ) -> CommandResult:
        """UC-B12: either party, while ACCEPTED, ACTIVE or RETURN_INITIATED. The loan becomes
        DISPUTED (its previous state is kept in the event) and the database opens a case for a
        moderator (UC-D6). A second dispute on the same loan shows the open case (FR-B-16)."""
        view = self._store_view(txn_id)
        role = self._role_of(actor, view)
        if role is None:
            self._reject(actor, txn_id, "dispute_opened", "not a party to this transaction")
            raise NotAuthorised("only the borrower or the lender of this loan may raise a dispute")
        if view.state == "DISPUTED":
            return CommandResult(txn_id, "DISPUTED", "a dispute is already open for this loan")
        view = self._precheck(actor, txn_id, "dispute_opened", role)
        payload = {"reason": reason, **({"description": description} if description else {})}
        self._party_event(actor, view, "dispute_opened", role, payload)
        return CommandResult(txn_id, "DISPUTED", "dispute raised; a moderator will review it")

    def withdraw_dispute(self, actor: Actor, txn_id: UUID) -> CommandResult:
        """UC-B12 5b, FR-B-17: only the party who raised it; the loan returns to its previous
        state (ADR-0004) and the case closes as WITHDRAWN."""
        view = self._store_view(txn_id)
        role = self._role_of(actor, view)
        if role is None:
            self._reject(actor, txn_id, "dispute_withdrawn", "not a party to this transaction")
            raise NotAuthorised("only the party who raised the dispute may withdraw it")
        self._require_state(actor, view, {"DISPUTED"}, "dispute_withdrawn")
        case = self.store.open_case(txn_id)
        if case is None or case["raised_by"] != actor.user_id:
            self._reject(actor, txn_id, "dispute_withdrawn", "not the party who raised the dispute")
            raise NotAuthorised("only the party who raised the dispute may withdraw it")
        opened = self.store.last_event(txn_id, "dispute_opened")
        restore = opened["previous_state"] if opened else None
        if restore is None:
            raise InvalidTransition("no dispute_opened event to restore from")
        self._party_event(actor, view, "dispute_withdrawn", role, new_state=restore)
        return CommandResult(txn_id, restore, "dispute withdrawn")

    def dispute_case(self, actor: Actor, txn_id: UUID) -> dict[str, Any]:
        """UC-D6 evidence trail for the parties: the case, the loan, both sides' condition reports,
        the event history and the assessment. Moderators get the same trail in C2."""
        found = self.get_request(actor, txn_id)
        case = self.store.open_case(txn_id) or self.store.latest_case(txn_id)
        if case is None:
            raise StreamNotFound(f"no case for {txn_id}")
        view = found["view"]
        raiser = case["raised_by"]
        found["case"] = {
            **case,
            "raised_by_role": "BORROWER"
            if raiser == view.borrower_id
            else "LENDER"
            if raiser == view.lender_id
            else None,
        }
        found["events"] = self.store.events(txn_id)
        return found

    # ------------------------------------------------------------------ I4: moderator decisions
    def decide(self, actor: Actor, case_id: UUID, decision: Decision) -> CommandResult:
        """UC-I4: record the decision with its reason, then apply it as one lifecycle event that
        references it. A resolved dispute becomes trust evidence (FR-B-15); a cleared locality or
        engine-failure hold runs the assessment again (ADR-0003)."""
        case = self.store.case_by_id(case_id)
        if case is None:
            raise StreamNotFound(f"case {case_id}")
        txn_id = case["transaction_id"]
        view = self._store_view(txn_id)
        role, authorisation = self._moderator_role(actor, view, "decide_case")
        if case["status"] not in ("OPEN", "AWAITING_INFORMATION"):
            self._reject(actor, txn_id, "decide_case", f"case already {case['status']}")
            raise InvalidTransition(f"this case is already {case['status'].lower()}")
        try:
            p = plan(view.state, view.hold_reason, decision)
        except InvalidDecision as exc:
            self._reject(actor, txn_id, "decide_case", str(exc))
            raise
        decision_id = self.store.insert_decision(
            case_id,
            decided_by=actor.user_id,
            decider_role=role,
            kind=decision.kind,
            reason=decision.reason.strip(),
            safeguards=p.safeguards,
            resolved_outcome=p.resolved_outcome,
        )
        try:
            event_id = self.store.append(
                txn_id,
                p.event_type,
                p.new_state,
                actor_id=actor.user_id,
                authorisation=authorisation,
                payload={"decision": decision.kind},
                evidence_refs={"decision_id": str(decision_id)},
            )
        except EventStoreError as exc:
            self._reject(actor, txn_id, "decide_case", str(exc))
            raise
        if p.event_type == "dispute_resolved":
            self.store.record_outcomes(event_id)
            self.store.refresh_trust_edges(txn_id)
            return CommandResult(txn_id, "COMPLETED", "dispute resolved")
        if p.new_state == "LOCALITY_CHECKED":
            return self._assess(txn_id)
        return CommandResult(txn_id, p.new_state, f"decision recorded: {decision.kind.lower()}")

    def moderation_queue(self, actor: Actor) -> list[dict[str, Any]]:
        """Live cases this moderator may decide, most urgent first (admins see every community)."""
        return self.store.open_cases_for(actor.user_id, actor.platform_role == "ADMIN")

    def moderator_case(self, actor: Actor, case_id: UUID) -> dict[str, Any]:
        """UC-D6 step 3: the case and its evidence trail, for a moderator of the community."""
        case = self.store.case_by_id(case_id)
        if case is None:
            raise StreamNotFound(f"case {case_id}")
        txn_id = case["transaction_id"]
        view = self._store_view(txn_id)
        self._moderator_role(actor, view, "view_case")
        raiser = case["raised_by"]
        return {
            "case": {
                **case,
                "raised_by_role": "BORROWER"
                if raiser == view.borrower_id
                else "LENDER"
                if raiser == view.lender_id
                else None,
            },
            "view": view,
            "details": self.store.details(txn_id),
            "reports": self.store.latest_reports(txn_id),
            "events": self.store.events(txn_id),
            "assessment": self.store.latest_assessment(txn_id),
            "decisions": self.store.decisions(case_id),
        }

    def _moderator_role(self, actor: Actor, view: TransactionView, action: str) -> tuple[str, str]:
        """(role, authorisation) for a moderator of the item's community or an admin; a party to
        the loan can never act on its own case."""
        if actor.user_id in (view.borrower_id, view.lender_id):
            self._reject(actor, view.id, action, "a party cannot decide its own case")
            raise NotAuthorised("a party cannot decide its own case")
        if actor.platform_role == "ADMIN":
            return "ADMIN", "role:admin"
        if self.store.is_moderator(actor.user_id, view.community_id):
            return "MODERATOR", f"role:moderator@{view.community_id}"
        self._reject(actor, view.id, action, "not a moderator of this community")
        raise NotAuthorised("only a moderator of this community may do this")

    def get_request(self, actor: Actor, txn_id: UUID) -> dict[str, Any]:
        view = self._store_view(txn_id)
        role = self._role_of(actor, view)
        if role is None and actor.platform_role != "ADMIN":
            raise NotAuthorised("not a party to this transaction")
        reports = self.store.latest_reports(txn_id)
        case = self.store.open_case(txn_id) if view.state == "DISPUTED" else None
        raised_by = None
        if case is not None:
            raised_by = "BORROWER" if case["raised_by"] == view.borrower_id else "LENDER"
        return {
            "view": view,
            "role": role,
            "assessment": self.store.latest_assessment(txn_id),
            "details": self.store.details(txn_id),
            "reports": reports,
            "actions": available_actions(view.state, role, reports, raised_by),
            "moderator_safeguards": self.store.imposed_safeguards(txn_id),
        }

    def my_requests(self, actor: Actor) -> list[dict[str, Any]]:
        return self.store.list_for_member(actor.user_id)

    def browse_items(self, actor: Actor) -> list[dict[str, Any]]:
        return self.store.list_items_for(actor.user_id)

    # ------------------------------------------------------------------ helpers
    def _store_view(self, txn_id: UUID) -> TransactionView:
        return self.store.view(txn_id)

    @staticmethod
    def _role_of(actor: Actor, view: TransactionView) -> str | None:
        if actor.user_id == view.borrower_id:
            return "BORROWER"
        if actor.user_id == view.lender_id:
            return "LENDER"
        return None

    def _require_party(self, actor: Actor, txn_id: UUID, role: str, action: str) -> TransactionView:
        view = self._store_view(txn_id)
        if self._role_of(actor, view) != role:
            self._reject(actor, txn_id, action, f"only the {role.lower()} may do this")
            raise NotAuthorised(f"only the {role.lower()} of this request may do this")
        return view

    def _require_state(
        self, actor: Actor, view: TransactionView, allowed: set[str], action: str
    ) -> None:
        if view.state not in allowed:
            reason = f"not allowed in state {view.state}"
            self._reject(actor, view.id, action, reason)
            raise InvalidTransition(reason)

    def _precheck(self, actor: Actor, txn_id: UUID, event_type: str, role: str) -> TransactionView:
        """Fast rejection before touching the event log: right person, valid (state, event)."""
        view = self._require_party(actor, txn_id, role, event_type)
        allowed = self.table.lookup(view.state or "", event_type)
        if not allowed:
            reason = f"invalid transition: {view.state} --{event_type}--> ?"
            self._reject(actor, txn_id, event_type, reason)
            raise InvalidTransition(reason)
        if not any(role in t.allowed_roles for t in allowed):
            self._reject(actor, txn_id, event_type, f"role {role} may not do this")
            raise NotAuthorised(f"role {role} may not append {event_type} in {view.state}")
        return view

    def _party_event(
        self,
        actor: Actor,
        view: TransactionView,
        event_type: str,
        role: str,
        payload: Mapping[str, Any] | None = None,
        new_state: str | None = None,
    ) -> None:
        """`new_state` is needed only where the table has several targets (dispute_withdrawn)."""
        new_state = new_state or self.table.next_state(view.state or "", event_type)
        if new_state is None:
            raise InvalidTransition(f"no unique next state for {view.state} --{event_type}-->")
        try:
            self.store.append(
                view.id,
                event_type,
                new_state,
                actor_id=actor.user_id,
                authorisation=f"party:{role.lower()}",
                payload=dict(payload or {}),
            )
        except EventStoreError as exc:
            if not isinstance(exc, DatesTaken):
                self._reject(actor, view.id, event_type, str(exc))
            raise

    def _reject(self, actor: Actor, txn_id: UUID, action: str, reason: str) -> None:
        self.audit.record_rejection(
            actor_id=actor.user_id,
            authorisation="member",
            action=f"reject_{action}",
            transaction_id=txn_id,
            reason=reason,
        )
