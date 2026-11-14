"""MembershipService: joining a community and the moderator's membership decisions (Module 1).

Follows sequence (d) "join a community" (docs/design/08_sequence_diagrams), the membership state
machine DA-08 (M01, M02, M04, M05, M07, M08, M09) and the REST table of Architecture_Design_v2.md
section 4. FRs: A-06 (list), A-07 and A-08 (locality, via LocalityVerifier), A-09 (join request,
duplicates blocked), A-10 (queue with evidence, reason required, own community only), A-11
(concurrent decisions and reversal).

The database is the last word on every rule that matters: `membership_one_live_uq` blocks a second
live request, `locality_rule_ck` makes the stored outcome follow its signals, `locality_guard` keeps
an invitation single-use and same-community, and `membership_decision_guard` refuses a second
decision (40001) and anyone who is not a moderator of that community or an admin. This class adds
fast pre-checks with clear messages and records refused attempts in the audit log.
"""

import hashlib
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from app.domain.lifecycle.errors import InvalidTransition, NotAuthorised, StreamNotFound
from app.domain.membership.locality import (
    Fix,
    InvalidInvitation,
    Invitation,
    LocalityConfig,
    LocalityResult,
    boundary_from_geojson,
    evaluate,
)
from app.domain.notifications.notify import INotify, NullNotifier

DECISION_KINDS = ("APPROVED", "REJECTED", "INFO_REQUESTED")
_STATUS_AFTER = {
    "APPROVED": "APPROVED",
    "REJECTED": "REJECTED",
    "INFO_REQUESTED": "AWAITING_INFORMATION",
}
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I, read aloud between neighbours
_LEVELS = ("UNVERIFIED", "CONTACT_VERIFIED", "COMMUNITY_VERIFIED")


class AlreadyDecided(InvalidTransition):
    """UC-A4 4a / FR-A-11: another moderator decided first; nothing is applied twice (409)."""


class DuplicateRequest(InvalidTransition):
    """UC-A3 4b / FR-A-09: a live request or membership for this community already exists (409)."""


class InvalidMembershipInput(ValueError):
    """Bad input, such as a decision without a reason (422)."""


@dataclass(frozen=True)
class JoinInput:
    """What the app sends to join. The fix is used in memory and dropped (NFR-PR-01)."""

    fix: Fix | None
    permission_refused: bool
    invitation_code: str | None


@dataclass(frozen=True)
class JoinOutcome:
    membership_id: UUID
    status: str  # PENDING, or APPROVED in an OPEN community with a VERIFIED check (M09)
    locality: LocalityResult


class MembershipStore(Protocol):
    """Persistence for MembershipService; implemented by PostgresMembershipStore (infra)."""

    def communities(self, query: str | None) -> list[dict[str, Any]]: ...

    def community(self, community_id: UUID) -> dict[str, Any] | None: ...

    def account(self, user_id: UUID) -> dict[str, Any]: ...

    def live_membership(self, user_id: UUID, community_id: UUID) -> dict[str, Any] | None: ...

    def is_approved_member(self, user_id: UUID, community_id: UUID) -> bool: ...

    def is_moderator(self, user_id: UUID, community_id: UUID) -> bool: ...

    def open_invitations(self, inviter_id: UUID, community_id: UUID, now: datetime) -> int: ...

    def insert_invitation(
        self, community_id: UUID, inviter_id: UUID, code_hash: bytes, expires_at: datetime
    ) -> UUID: ...

    def invitation_by_hash(self, code_hash: bytes) -> dict[str, Any] | None: ...

    def insert_membership(self, user_id: UUID, community_id: UUID) -> UUID:
        """Raises DuplicateRequest if `membership_one_live_uq` refuses it (a concurrent request)."""
        ...

    def insert_locality(
        self,
        membership_id: UUID,
        result: LocalityResult,
        invitation_id: UUID | None,
        valid_until: datetime,
    ) -> UUID: ...

    def insert_moderator_approval(
        self, membership_id: UUID, approved_by: UUID, valid_until: datetime
    ) -> UUID: ...

    def membership(self, membership_id: UUID) -> dict[str, Any] | None: ...

    def latest_locality(self, membership_id: UUID) -> dict[str, Any] | None: ...

    def set_status(self, membership_id: UUID, status: str) -> None: ...

    def raise_verification(self, user_id: UUID, level: str) -> None: ...

    def insert_decision(
        self,
        membership_id: UUID,
        decided_by: UUID,
        kind: str,
        reason: str,
        reverses: UUID | None,
    ) -> UUID:
        """Raises AlreadyDecided or NotAuthorised when `membership_decision_guard` refuses."""
        ...

    def decision(self, decision_id: UUID) -> dict[str, Any] | None: ...

    def decisions(self, membership_id: UUID) -> list[dict[str, Any]]: ...

    def queue(self, moderator_id: UUID, every_community: bool) -> list[dict[str, Any]]: ...

    def moderators_of(self, community_id: UUID) -> list[UUID]: ...

    def audit(
        self,
        *,
        actor_id: UUID | None,
        authorisation: str,
        action: str,
        membership_id: UUID,
        new_value: Mapping[str, Any] | None = None,
    ) -> None:
        """A SUCCESS row in the command's own transaction (FR-M-05)."""
        ...

    def audit_rejection(
        self, *, actor_id: UUID, action: str, target_type: str, target_id: str, reason: str
    ) -> None:
        """A REJECTED row in its own transaction, so it survives the command's rollback."""
        ...


def hash_code(code: str) -> bytes:
    """SHA-256 of the normalised code (upper case, no spaces or dashes). Only this is stored."""
    normalised = "".join(ch for ch in code.upper() if ch.isalnum())
    return hashlib.sha256(normalised.encode("ascii", "ignore")).digest()


def new_code() -> str:
    raw = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


class MembershipService:
    def __init__(
        self,
        store: MembershipStore,
        cfg: LocalityConfig,
        *,
        now: datetime,
        notifier: INotify | None = None,
    ) -> None:
        self.store = store
        self.cfg = cfg
        self.now = now
        self.notifier: INotify = notifier or NullNotifier()

    # ------------------------------------------------------------------ A3 steps 1-2 (FR-A-06)
    def communities(self, query: str | None) -> list[dict[str, Any]]:
        """Active communities by name or join code, with rules and verification methods."""
        rows = self.store.communities((query or "").strip() or None)
        for r in rows:
            r["methods"] = ["GEOFENCE_INVITATION", "MODERATOR_APPROVAL"]
            r["has_boundary"] = r.pop("boundary_polygon", None) is not None
        return rows

    # ------------------------------------------------------------------ A11 invitations (FR-A-07)
    def issue_invitation(self, inviter_id: UUID, community_id: UUID) -> tuple[str, datetime]:
        """A single-use code from an approved member; returned once, only its hash is stored."""
        self._active_community(community_id)
        if not self.store.is_approved_member(inviter_id, community_id):
            self.store.audit_rejection(
                actor_id=inviter_id,
                action="reject_issue_invitation",
                target_type="community",
                target_id=str(community_id),
                reason="not an approved member of this community",
            )
            raise NotAuthorised("only an approved member of this community can invite")
        if (
            self.store.open_invitations(inviter_id, community_id, self.now)
            >= self.cfg.max_open_invites
        ):
            raise InvalidMembershipInput(
                f"you already have {self.cfg.max_open_invites} unused invitations for this community"
            )
        code = new_code()
        expires = self.now + timedelta(days=self.cfg.invite_ttl_days)
        self.store.insert_invitation(community_id, inviter_id, hash_code(code), expires)
        return code, expires

    # ------------------------------------------------------------------ A3 steps 3-4 (FR-A-07 to A-09)
    def request_join(self, user_id: UUID, community_id: UUID, join: JoinInput) -> JoinOutcome:
        community = self._active_community(community_id)
        account = self.store.account(user_id)
        if account["status"] != "ACTIVE" or _level(account["verification_level"]) < _level(
            "CONTACT_VERIFIED"
        ):
            raise NotAuthorised("verify your contact details before joining a community (M01)")
        live = self.store.live_membership(user_id, community_id)
        if live is not None:
            raise DuplicateRequest(f"you already have a {live['status'].lower()} membership here")

        invitation_id, invitation = None, None
        if join.invitation_code:
            row = self.store.invitation_by_hash(hash_code(join.invitation_code))
            if row is None:
                raise InvalidInvitation(
                    "this invitation code is not valid: retry or continue without"
                )
            invitation_id = row["id"]
            invitation = Invitation(
                community_id=str(row["community_id"]),
                inviter_id=str(row["inviter_id"]),
                expires_at=row["expires_at"],
                used=row["used"],
                inviter_is_approved_member=row["inviter_is_approved_member"],
            )
        result = evaluate(
            fix=None if join.permission_refused else join.fix,
            permission_refused=join.permission_refused,
            boundary=boundary_from_geojson(community.get("boundary_polygon")),
            invitation=invitation,
            community_id=str(community_id),
            user_id=str(user_id),
            # FR-A-03's device signal is not built yet (iteration 3), so nothing raises it here
            duplicate_suspected=False,
            now=self.now,
            cfg=self.cfg,
        )
        membership_id = self.store.insert_membership(user_id, community_id)
        self.store.insert_locality(
            membership_id,
            result,
            invitation_id if result.invitation_used else None,
            self.now + timedelta(days=self.cfg.validity_days),
        )
        self.store.audit(
            actor_id=user_id,
            authorisation="member",
            action="membership_requested",
            membership_id=membership_id,
            new_value={"status": "PENDING", "locality_outcome": result.outcome},
        )
        moderators = self.store.moderators_of(community_id)
        payload = {"membership_id": str(membership_id), "community_name": community["name"]}
        if community["join_policy"] == "OPEN" and result.outcome == "VERIFIED":  # M09
            self._approve_effects(membership_id, user_id, None)
            self.store.audit(
                actor_id=None,
                authorisation="system:membership-service",
                action="membership_auto_approved",
                membership_id=membership_id,
                new_value={"status": "APPROVED"},
            )
            for m in moderators:
                self.notifier.notify(m, "member_joined", payload, f"{membership_id}:joined")
            return JoinOutcome(membership_id, "APPROVED", result)
        for m in moderators:
            self.notifier.notify(m, "membership_request", payload, f"{membership_id}:request")
        return JoinOutcome(membership_id, "PENDING", result)

    # ------------------------------------------------------------------ A4 (FR-A-10, A-11)
    def queue(self, moderator_id: UUID, platform_role: str) -> list[dict[str, Any]]:
        """Undecided requests of the moderator's own communities, with the coarse evidence."""
        return self.store.queue(moderator_id, platform_role == "ADMIN")

    def decide(
        self,
        actor_id: UUID,
        platform_role: str,
        membership_id: UUID,
        kind: str,
        reason: str,
        reverses_decision_id: UUID | None = None,
    ) -> str:
        """Record a decision with its reason and apply it; returns the new membership status."""
        reason = (reason or "").strip()
        m = self.store.membership(membership_id)
        if m is None:
            raise StreamNotFound(f"membership {membership_id}")
        authorisation = self._moderator_of(actor_id, platform_role, m, "decide_membership")
        if not reason:
            raise InvalidMembershipInput("a reason is required for every membership decision")
        if kind == "REVERSED":
            return self._reverse(actor_id, authorisation, m, reason, reverses_decision_id)
        if kind not in DECISION_KINDS:
            raise InvalidMembershipInput(
                f"kind must be one of {', '.join(DECISION_KINDS)}, REVERSED"
            )
        if m["status"] not in ("PENDING", "AWAITING_INFORMATION"):  # fast path; the guard is final
            raise AlreadyDecided(f"this request is already {m['status'].lower()}")
        decision_id = self.store.insert_decision(membership_id, actor_id, kind, reason, None)
        status = _STATUS_AFTER[kind]
        if kind == "APPROVED":
            self._approve_effects(membership_id, m["user_id"], actor_id)
        else:
            self.store.set_status(membership_id, status)
        self.store.audit(
            actor_id=actor_id,
            authorisation=authorisation,
            action=f"membership_{kind.lower()}",
            membership_id=membership_id,
            new_value={"status": status, "decision_id": str(decision_id), "reason": reason},
        )
        self.notifier.notify(
            m["user_id"],
            "membership_decided",
            {"membership_id": str(membership_id), "status": status, "reason": reason},
            f"{membership_id}:decision:{decision_id}",
        )
        return status

    def _reverse(
        self,
        actor_id: UUID,
        authorisation: str,
        m: Mapping[str, Any],
        reason: str,
        reverses_decision_id: UUID | None,
    ) -> str:
        """FR-A-11, M07 and M08: a new REVERSED row; the reversed decision stays in the log.

        Reversing a rejection approves (M08); reversing an approval revokes (M07). The reversal
        must come from someone other than the moderator who made the decision."""
        if reverses_decision_id is None:
            raise InvalidMembershipInput("a reversal names the decision it reverses")
        old = self.store.decision(reverses_decision_id)
        if old is None or old["membership_id"] != m["id"]:
            raise InvalidMembershipInput("that decision is not about this membership")
        if old["decided_by"] == actor_id:
            raise NotAuthorised("another moderator or an admin must reverse a decision")
        target = {("REJECTED", "REJECTED"): "APPROVED", ("APPROVED", "APPROVED"): "REVOKED"}.get(
            (old["kind"], m["status"])
        )
        if target is None:
            raise AlreadyDecided(
                f"a {old['kind'].lower()} decision cannot be reversed while the membership is "
                f"{m['status'].lower()}"
            )
        decision_id = self.store.insert_decision(
            m["id"], actor_id, "REVERSED", reason, reverses_decision_id
        )
        if target == "APPROVED":
            self._approve_effects(m["id"], m["user_id"], actor_id)
        else:
            self.store.set_status(m["id"], "REVOKED")
        self.store.audit(
            actor_id=actor_id,
            authorisation=authorisation,
            action="membership_reversed",
            membership_id=m["id"],
            new_value={"status": target, "decision_id": str(decision_id), "reason": reason},
        )
        self.notifier.notify(
            m["user_id"],
            "membership_decided",
            {"membership_id": str(m["id"]), "status": target, "reason": reason},
            f"{m['id']}:decision:{decision_id}",
        )
        return target

    # ------------------------------------------------------------------ helpers
    def _approve_effects(self, membership_id: UUID, user_id: UUID, approver: UUID | None) -> None:
        """M04 / M09 effects: APPROVED, and the member counts as community verified.

        If the stored check was not VERIFIED, the moderator's approval is recorded as a
        MODERATOR_APPROVAL locality result (A11), so `locality_outcome_for` reads VERIFIED for
        borrowing (FR-B-07). A system approval (M09) only ever follows a VERIFIED check.
        """
        self.store.set_status(membership_id, "APPROVED")
        latest = self.store.latest_locality(membership_id)
        if approver is not None and (latest is None or latest["outcome"] != "VERIFIED"):
            self.store.insert_moderator_approval(
                membership_id, approver, self.now + timedelta(days=self.cfg.validity_days)
            )
        # basic_community = COMMUNITY_VERIFIED (Assurance_Data_Dictionary.md); never lowered here
        self.store.raise_verification(user_id, "COMMUNITY_VERIFIED")

    def _active_community(self, community_id: UUID) -> dict[str, Any]:
        community = self.store.community(community_id)
        if community is None or not community["is_active"]:
            raise StreamNotFound(f"community {community_id}")
        return community

    def _moderator_of(
        self, actor_id: UUID, platform_role: str, m: Mapping[str, Any], action: str
    ) -> str:
        """Authorisation string for a moderator of the membership's community or an admin."""
        if actor_id == m["user_id"]:
            refusal = "an applicant cannot decide their own membership"
        elif platform_role == "ADMIN":
            return "role:admin"
        elif self.store.is_moderator(actor_id, m["community_id"]):
            return f"role:moderator@{m['community_id']}"
        else:
            refusal = "not a moderator of this community"
        self.store.audit_rejection(
            actor_id=actor_id,
            action=f"reject_{action}",
            target_type="membership",
            target_id=str(m["id"]),
            reason=refusal,
        )
        raise NotAuthorised(refusal)


def _level(level: str) -> int:
    return _LEVELS.index(level)
