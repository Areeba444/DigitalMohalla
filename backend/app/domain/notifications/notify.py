"""NotificationService boundary (Module 7, FR-C-02 in-app channel, ADR-0013).

`notify(user, type, payload, dedupe_key)` records that someone was told something. It is not a
lifecycle event: nothing changes state. The in-app channel is a `notification` row that the app
polls; email and push (iteration 3) will be further channels behind the same call, so callers do
not change.

Two rules hold here and again in the database:
- Duplicate suppression: `(user, dedupe_key)` is unique, so a retried job or a repeated command
  tells nobody twice (FR-B-18, NFR-R-05). `notify` returns False when the row already existed.
- No location in the payload (R7, NFR-PR-01): the app builds the text from ids and titles only.
"""

import re
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

# Location-like keys refused in a payload; the same list as the schema's has_location_keys().
LOCATION_KEYS = frozenset(
    {"lat", "lng", "lon", "latitude", "longitude", "coordinates", "address", "location", "accuracy"}
)
_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class InvalidNotification(ValueError):
    """A notification the system must not send: bad type, location keys, or a bad dedupe key."""


def check(type_: str, payload: Mapping[str, Any], dedupe_key: str) -> None:
    """Refuse a notification before it reaches the database (the schema checks the same)."""
    if not _TYPE_RE.match(type_):
        raise InvalidNotification(f"notification type {type_!r} is not snake_case")
    leaked = LOCATION_KEYS.intersection(k.lower() for k in payload)
    if leaked:
        raise InvalidNotification(f"payload may not carry location keys: {sorted(leaked)}")
    if not 1 <= len(dedupe_key) <= 200:
        raise InvalidNotification("dedupe_key must be 1 to 200 characters")


class INotify(Protocol):
    """M7 -> M1, M3, M9 (Architecture_Design_v2.md section 3)."""

    def notify(
        self, user_id: UUID, type_: str, payload: Mapping[str, Any], dedupe_key: str
    ) -> bool:
        """Record one notification; False if this user was already told (same dedupe_key)."""
        ...


class NullNotifier:
    """Tells nobody. Used where no channel is wired, for example unit tests of other services."""

    def notify(
        self, user_id: UUID, type_: str, payload: Mapping[str, Any], dedupe_key: str
    ) -> bool:
        check(type_, payload, dedupe_key)
        return False
