"""PostgreSQL adapter for MembershipService (Module 1, plan items F2 and F3).

Works on the caller's open connection, so a join or a decision is one DB transaction. Only the
coarse locality result is written (`locality_verification`); no coordinate or accuracy column
exists anywhere in the schema (R5, NFR-PR-01).
"""

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import errors as pg
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.domain.lifecycle.errors import NotAuthorised
from app.domain.membership.locality import InvalidInvitation, LocalityResult
from app.domain.membership.service import AlreadyDecided, DuplicateRequest


class PostgresMembershipStore:
    def __init__(self, conn: Connection, audit_engine: Engine | None = None) -> None:
        self.conn = conn
        self.audit_engine = audit_engine

    def _one(self, sql: str, **params: Any) -> dict[str, Any] | None:
        row = self.conn.execute(text(sql), params).mappings().first()
        return dict(row) if row else None

    # communities --------------------------------------------------------------------------------
    def communities(self, query: str | None) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            text(
                "SELECT id, name, join_code, rules, join_policy::text AS join_policy, "
                "boundary_polygon, (SELECT count(*) FROM membership m WHERE m.community_id = c.id "
                " AND m.status = 'APPROVED') AS member_count "
                "FROM community c WHERE c.is_active AND (CAST(:q AS text) IS NULL "
                " OR c.name ILIKE '%' || :q || '%' OR lower(c.join_code) = lower(:q)) "
                "ORDER BY c.name LIMIT 50"
            ),
            {"q": query},
        ).mappings()
        return [dict(r) for r in rows]

    def community(self, community_id: UUID) -> dict[str, Any] | None:
        return self._one(
            "SELECT id, name, is_active, join_policy::text AS join_policy, boundary_polygon "
            "FROM community WHERE id = :c",
            c=community_id,
        )

    def account(self, user_id: UUID) -> dict[str, Any]:
        row = self._one(
            "SELECT status::text AS status, verification_level::text AS verification_level "
            "FROM app_user WHERE id = :u",
            u=user_id,
        )
        if row is None:  # a token for a deleted account
            raise NotAuthorised("this account no longer exists")
        return row

    def live_membership(self, user_id: UUID, community_id: UUID) -> dict[str, Any] | None:
        return self._one(
            "SELECT id, status::text AS status FROM membership WHERE user_id = :u "
            "AND community_id = :c AND status IN ('PENDING', 'AWAITING_INFORMATION', 'APPROVED')",
            u=user_id,
            c=community_id,
        )

    def is_approved_member(self, user_id: UUID, community_id: UUID) -> bool:
        return bool(
            self._one(
                "SELECT 1 AS ok FROM membership WHERE user_id = :u AND community_id = :c "
                "AND status = 'APPROVED'",
                u=user_id,
                c=community_id,
            )
        )

    def is_moderator(self, user_id: UUID, community_id: UUID) -> bool:
        return bool(
            self._one(
                "SELECT 1 AS ok FROM membership WHERE user_id = :u AND community_id = :c "
                "AND role = 'MODERATOR' AND status = 'APPROVED'",
                u=user_id,
                c=community_id,
            )
        )

    def moderators_of(self, community_id: UUID) -> list[UUID]:
        return list(
            self.conn.execute(
                text(
                    "SELECT user_id FROM membership WHERE community_id = :c AND role = 'MODERATOR' "
                    "AND status = 'APPROVED' ORDER BY user_id"
                ),
                {"c": community_id},
            ).scalars()
        )

    # invitations ------------------------------------------------------------------------------
    def open_invitations(self, inviter_id: UUID, community_id: UUID, now: datetime) -> int:
        return int(
            self.conn.execute(
                text(
                    "SELECT count(*) FROM invitation i WHERE i.inviter_id = :u "
                    "AND i.community_id = :c AND i.expires_at > :now AND NOT EXISTS ("
                    " SELECT 1 FROM locality_verification lv WHERE lv.invitation_id = i.id)"
                ),
                {"u": inviter_id, "c": community_id, "now": now},
            ).scalar_one()
        )

    def insert_invitation(
        self, community_id: UUID, inviter_id: UUID, code_hash: bytes, expires_at: datetime
    ) -> UUID:
        return UUID(
            str(
                self.conn.execute(
                    text(
                        "INSERT INTO invitation (community_id, inviter_id, code_hash, expires_at) "
                        "VALUES (:c, :u, :h, :e) RETURNING id"
                    ),
                    {"c": community_id, "u": inviter_id, "h": code_hash, "e": expires_at},
                ).scalar_one()
            )
        )

    def invitation_by_hash(self, code_hash: bytes) -> dict[str, Any] | None:
        return self._one(
            "SELECT i.id, i.community_id, i.inviter_id, i.expires_at, "
            "EXISTS (SELECT 1 FROM locality_verification lv WHERE lv.invitation_id = i.id) AS used, "
            "EXISTS (SELECT 1 FROM membership im WHERE im.user_id = i.inviter_id "
            " AND im.community_id = i.community_id AND im.status = 'APPROVED') "
            " AS inviter_is_approved_member "
            "FROM invitation i WHERE i.code_hash = :h",
            h=code_hash,
        )

    # membership rows --------------------------------------------------------------------------
    def insert_membership(self, user_id: UUID, community_id: UUID) -> UUID:
        try:
            with self.conn.begin_nested():
                value = self.conn.execute(
                    text(
                        "INSERT INTO membership (user_id, community_id) VALUES (:u, :c) RETURNING id"
                    ),
                    {"u": user_id, "c": community_id},
                ).scalar_one()
        except IntegrityError as exc:  # membership_one_live_uq: a request raced this one
            raise DuplicateRequest("you already have a live request for this community") from exc
        return UUID(str(value))

    def insert_locality(
        self,
        membership_id: UUID,
        result: LocalityResult,
        invitation_id: UUID | None,
        valid_until: datetime,
    ) -> UUID:
        try:
            with self.conn.begin_nested():
                value = self.conn.execute(
                    text(
                        "INSERT INTO locality_verification (membership_id, method, outcome, "
                        "geofence_signal, invitation_id, permission_refused, "
                        "mock_provider_detected, duplicate_suspected, valid_until) VALUES "
                        "(:m, 'GEOFENCE_INVITATION', CAST(:o AS locality_outcome), "
                        "CAST(:s AS geofence_signal), :i, :pr, :mock, :dup, :until) RETURNING id"
                    ),
                    {
                        "m": membership_id,
                        "o": result.outcome,
                        "s": result.geofence_signal,
                        "i": invitation_id,
                        "pr": result.permission_refused,
                        "mock": result.mock_provider_detected,
                        "dup": result.duplicate_suspected,
                        "until": valid_until,
                    },
                ).scalar_one()
        except (IntegrityError, DBAPIError) as exc:
            if isinstance(exc.orig, pg.UniqueViolation | pg.CheckViolation):  # used meanwhile
                raise InvalidInvitation(
                    "this invitation code is not valid: retry or continue without"
                ) from exc
            raise
        return UUID(str(value))

    def insert_moderator_approval(
        self, membership_id: UUID, approved_by: UUID, valid_until: datetime
    ) -> UUID:
        return UUID(
            str(
                self.conn.execute(
                    text(
                        "INSERT INTO locality_verification (membership_id, method, outcome, "
                        "approved_by, valid_until) VALUES (:m, 'MODERATOR_APPROVAL', 'VERIFIED', "
                        ":a, :until) RETURNING id"
                    ),
                    {"m": membership_id, "a": approved_by, "until": valid_until},
                ).scalar_one()
            )
        )

    def membership(self, membership_id: UUID) -> dict[str, Any] | None:
        return self._one(
            "SELECT id, user_id, community_id, role::text AS role, status::text AS status, "
            "requested_at, decided_at FROM membership WHERE id = :m FOR UPDATE",
            m=membership_id,
        )

    def latest_locality(self, membership_id: UUID) -> dict[str, Any] | None:
        return self._one(
            "SELECT outcome::text AS outcome, geofence_signal::text AS geofence_signal "
            "FROM locality_verification WHERE membership_id = :m "
            "ORDER BY checked_at DESC, id LIMIT 1",
            m=membership_id,
        )

    def set_status(self, membership_id: UUID, status: str) -> None:
        self.conn.execute(
            text(
                "UPDATE membership SET status = CAST(:s AS membership_status), decided_at = "
                "CASE WHEN :s IN ('PENDING', 'AWAITING_INFORMATION') THEN NULL "
                "ELSE coalesce(decided_at, now()) END WHERE id = :m"
            ),
            {"s": status, "m": membership_id},
        )

    def raise_verification(self, user_id: UUID, level: str) -> None:
        self.conn.execute(
            text(
                "UPDATE app_user SET verification_level = CAST(:l AS verification_level) "
                "WHERE id = :u AND verification_level < CAST(:l AS verification_level)"
            ),
            {"u": user_id, "l": level},
        )

    # decisions --------------------------------------------------------------------------------
    def insert_decision(
        self,
        membership_id: UUID,
        decided_by: UUID,
        kind: str,
        reason: str,
        reverses: UUID | None,
    ) -> UUID:
        try:
            with self.conn.begin_nested():
                value = self.conn.execute(
                    text(
                        "INSERT INTO membership_decision (membership_id, decided_by, kind, "
                        "reason, reverses_decision_id) VALUES (:m, :d, "
                        "CAST(:k AS membership_decision_kind), :r, :rev) RETURNING id"
                    ),
                    {"m": membership_id, "d": decided_by, "k": kind, "r": reason, "rev": reverses},
                ).scalar_one()
        except DBAPIError as exc:  # membership_decision_guard (UC-A4 4a, 4b)
            if isinstance(exc.orig, pg.SerializationFailure):
                raise AlreadyDecided("another moderator decided first; nothing applied") from exc
            if isinstance(exc.orig, pg.InsufficientPrivilege):
                raise NotAuthorised(str(exc.orig).split("\n")[0]) from exc
            raise
        return UUID(str(value))

    def decision(self, decision_id: UUID) -> dict[str, Any] | None:
        return self._one(
            "SELECT id, membership_id, decided_by, kind::text AS kind, reason, decided_at "
            "FROM membership_decision WHERE id = :d",
            d=decision_id,
        )

    def decisions(self, membership_id: UUID) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            text(
                "SELECT d.id, d.kind::text AS kind, d.reason, d.reverses_decision_id, d.decided_at, "
                "u.display_name AS decided_by_name FROM membership_decision d "
                "JOIN app_user u ON u.id = d.decided_by WHERE d.membership_id = :m "
                "ORDER BY d.decided_at, d.id"
            ),
            {"m": membership_id},
        ).mappings()
        return [dict(r) for r in rows]

    def queue(self, moderator_id: UUID, every_community: bool) -> list[dict[str, Any]]:
        """Undecided requests with the latest coarse check; CONFLICTING first, then oldest."""
        rows = self.conn.execute(
            text(
                "SELECT m.id AS membership_id, m.status::text AS status, m.requested_at, "
                "c.id AS community_id, c.name AS community_name, u.display_name AS applicant_name, "
                "lv.outcome::text AS locality_outcome, lv.geofence_signal::text AS boundary_signal, "
                "(lv.invitation_id IS NOT NULL) AS invitation_used, "
                "coalesce(lv.permission_refused, false) AS permission_refused, "
                "coalesce(lv.mock_provider_detected, false) AS mock_provider_detected, "
                "coalesce(lv.duplicate_suspected, false) AS duplicate_suspected "
                "FROM membership m JOIN community c ON c.id = m.community_id "
                "JOIN app_user u ON u.id = m.user_id "
                "LEFT JOIN LATERAL (SELECT * FROM locality_verification v "
                " WHERE v.membership_id = m.id ORDER BY v.checked_at DESC, v.id LIMIT 1) lv ON true "
                "WHERE m.status IN ('PENDING', 'AWAITING_INFORMATION') AND m.user_id <> :u "
                "AND (:all OR EXISTS (SELECT 1 FROM membership mm WHERE mm.user_id = :u "
                " AND mm.community_id = m.community_id AND mm.role = 'MODERATOR' "
                " AND mm.status = 'APPROVED')) "
                "ORDER BY (lv.outcome = 'CONFLICTING') DESC NULLS LAST, m.requested_at, m.id"
            ),
            {"u": moderator_id, "all": every_community},
        ).mappings()
        return [dict(r) for r in rows]

    # audit --------------------------------------------------------------------------------------
    def audit(
        self,
        *,
        actor_id: UUID | None,
        authorisation: str,
        action: str,
        membership_id: UUID,
        new_value: Mapping[str, Any] | None = None,
    ) -> None:
        self.conn.execute(
            text(
                "INSERT INTO audit_log (actor_id, authorisation, action, target_type, target_id, "
                "new_value, outcome) VALUES (:a, :auth, :act, 'membership', :t, "
                "CAST(:v AS jsonb), 'SUCCESS')"
            ),
            {
                "a": actor_id,
                "auth": authorisation,
                "act": action,
                "t": str(membership_id),
                "v": json.dumps(dict(new_value or {})),
            },
        )

    def audit_rejection(
        self, *, actor_id: UUID, action: str, target_type: str, target_id: str, reason: str
    ) -> None:
        if self.audit_engine is None:
            return
        with self.audit_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO audit_log (actor_id, authorisation, action, target_type, "
                    "target_id, outcome, reason) VALUES (:a, 'member', :act, :tt, :t, "
                    "'REJECTED', :r)"
                ),
                {
                    "a": actor_id,
                    "act": action,
                    "tt": target_type,
                    "t": target_id,
                    "r": reason[:500],
                },
            )
