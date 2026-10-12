"""Password hashing and login tokens (FR-A-04 part, NFR-S-01).

Passwords are stored only as argon2 hashes. A login returns a signed JWT carrying the user id and
platform role. The role in the token is a convenience only: every lifecycle transition is checked
again by the database against the real parties of the transaction (NFR-S-02).
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.domain.lifecycle.service import Actor

_hasher = PasswordHasher()


class InvalidCredentials(Exception):
    """Generic on purpose: never say whether the account or the password was wrong."""


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    if not password_hash:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_token(actor: Actor, secret: str, minutes: int = 60) -> str:
    payload = {
        "sub": str(actor.user_id),
        "role": actor.platform_role,
        "exp": datetime.now(UTC) + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> Actor:
    try:
        data = jwt.decode(token, secret, algorithms=["HS256"])
        return Actor(UUID(data["sub"]), data.get("role", "MEMBER"))
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise InvalidCredentials("invalid or expired token") from exc
