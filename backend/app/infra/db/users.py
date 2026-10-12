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
