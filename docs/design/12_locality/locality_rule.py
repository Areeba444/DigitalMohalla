"""Reference implementation of the A11 locality rule (Student 1): coarse geofence + invitation.

Pure Python, no dependencies. It is the specification that Module 1's LocalityVerifier implements; the same
decision table is enforced in the database by `locality_rule_ck` (06_data_model/schema.sql).

Privacy (NFR-PR-01, NFR-PR-02): the device fix is an argument of evaluate() and is never returned or stored.
The result carries only the coarse signal, the outcome and flags.
All parameters are INITIAL, UNVALIDATED values for the versioned config (NFR-D-01); NFR-Q-04 measures them.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from datetime import datetime

# ---------------------------------------------------------------- config (initial, to be validated)
MAX_ACCURACY_M = 100.0      # a fix less accurate than this is treated as UNAVAILABLE
MIN_MARGIN_M = 50.0         # boundary band; the band is max(MIN_MARGIN_M, reported accuracy)
INVITE_TTL_DAYS = 7         # invitation lifetime
MAX_OPEN_INVITES = 3        # open invitations per member (limits invitation chains of fake accounts)
VALIDITY_DAYS = 365         # re-verification period ("verified once or periodically", Overview section 1)


class InvalidInvitation(Exception):
    """UC-A3 ext 3d: invalid, expired or used invitation code: show an error and let the member retry."""


@dataclass(frozen=True)
class Fix:
    """One-time device location fix. Lives only in memory during evaluate()."""
    lat: float
    lon: float
    accuracy_m: float
    mock_provider: bool = False          # device reports a mock-location provider


@dataclass(frozen=True)
class Invitation:
    community_id: str
    inviter_id: str
    expires_at: datetime
    used: bool
    inviter_is_approved_member: bool


@dataclass(frozen=True)
class LocalityResult:
    outcome: str                         # VERIFIED | INCONCLUSIVE | CONFLICTING  (never negative, FR-A-08)
    geofence_signal: str                 # INSIDE | NEAR_BOUNDARY | OUTSIDE | UNAVAILABLE
    invitation_used: bool
    permission_refused: bool
    mock_provider_detected: bool
    duplicate_suspected: bool


def _to_metres(lat0, lat, lon):
    k = 111_320.0
    return (lon * k * math.cos(math.radians(lat0)), lat * k)


def _inside(pt, poly):
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _dist_to_edges(pt, poly):
    px, py = pt
    best = math.inf
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)))
    return best


def geofence_signal(fix: Fix | None, boundary: list[tuple[float, float]]) -> str:
    """Coarse signal from a one-time fix and the community's coarse boundary [(lat, lon), ...]."""
    if fix is None or fix.accuracy_m > MAX_ACCURACY_M:
        return "UNAVAILABLE"
    lat0 = fix.lat
    poly = [_to_metres(lat0, la, lo) for la, lo in boundary]
    pt = _to_metres(lat0, fix.lat, fix.lon)
    if _dist_to_edges(pt, poly) <= max(MIN_MARGIN_M, fix.accuracy_m):
        return "NEAR_BOUNDARY"
    return "INSIDE" if _inside(pt, poly) else "OUTSIDE"


def check_invitation(inv: Invitation | None, community_id: str, user_id: str, now: datetime) -> bool:
    """True if a valid invitation is presented; raises InvalidInvitation for a bad code; False if none."""
    if inv is None:
        return False
    if inv.used or inv.expires_at <= now or inv.community_id != community_id or inv.inviter_id == user_id \
            or not inv.inviter_is_approved_member:
        raise InvalidInvitation("invitation is invalid, expired, used or not from a member of this community")
    return True


def decide(signal: str, invitation_ok: bool, mock: bool, duplicate: bool) -> str:
    """A11 decision table (identical to locality_rule_ck in schema.sql)."""
    if mock or duplicate or signal == "OUTSIDE":
        return "CONFLICTING"             # evidence contradicts the claim: moderator review, never auto-reject
    if signal == "INSIDE" and invitation_ok:
        return "VERIFIED"                # two independent signals agree
    return "INCONCLUSIVE"                # one signal missing or weak: moderator review


def evaluate(*, fix: Fix | None, permission_refused: bool, boundary, invitation: Invitation | None,
             community_id: str, user_id: str, duplicate_suspected: bool, now: datetime) -> LocalityResult:
    inv_ok = check_invitation(invitation, community_id, user_id, now)
    signal = "UNAVAILABLE" if permission_refused else geofence_signal(fix, boundary)
    mock = bool(fix and fix.mock_provider and not permission_refused)
    return LocalityResult(outcome=decide(signal, inv_ok, mock, duplicate_suspected), geofence_signal=signal,
                          invitation_used=inv_ok, permission_refused=permission_refused,
                          mock_provider_detected=mock, duplicate_suspected=duplicate_suspected)


def stored_fields(result: LocalityResult) -> dict:
    """Exactly what is persisted to locality_verification: no coordinates, no accuracy, no address."""
    return asdict(result)
