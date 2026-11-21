"""User lookup for login (Module 1, minimal in iteration 1: seeded users, password login)."""

from sqlalchemy import Connection, text

from app.domain.accounts.auth import InvalidCredentials, verify_password
from app.domain.lifecycle.service import Actor


def authenticate(conn: Connection, email: str, password: str) -> Actor:
    """Return the Actor for valid credentials of an ACTIVE account, else InvalidCredentials."""
    row = (
        conn.execute(
            text(
                "SELECT id, password_hash, status::text AS status, platform_role::text AS platform_role "
                "FROM app_user WHERE lower(email) = lower(:e)"
            ),
            {"e": email},
        )
        .mappings()
        .first()
    )
    # verify even when the user is unknown, so response time does not reveal which emails exist
    ok = verify_password(row["password_hash"] if row else None, password)
    if not row or not ok or row["status"] != "ACTIVE":
        raise InvalidCredentials("invalid email or password")
    return Actor(row["id"], row["platform_role"])


def register(conn: Connection, display_name: str, email: str, password_hash: str) -> bool:
    """Create a PENDING_VERIFICATION account with the terms acceptance time (UC-A1 step 3).

    Returns False, and changes nothing, when the e-mail is already registered: the caller gives the
    same reply either way, so nothing reveals which identifier matched (FR-A-01).
    """
    created = conn.execute(
        text(
            "INSERT INTO app_user (display_name, email, password_hash, status, terms_accepted_at) "
            "VALUES (:n, :e, :h, 'PENDING_VERIFICATION', now()) "
            "ON CONFLICT (lower(email)) WHERE email IS NOT NULL DO NOTHING RETURNING id"
        ),
        {"n": display_name, "e": email, "h": password_hash},
    ).first()
    return created is not None
