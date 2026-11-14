"""LocalityVerifier: the A11 locality rule at runtime (Module 1, FR-A-07, FR-A-08, DM02).

Port of the design's reference implementation `docs/design/12_locality/locality_rule.py`. The same
decision table is enforced again by the database (`locality_rule_ck`), so this code and the schema
cannot disagree without an insert failing.

Privacy (NFR-PR-01): the device fix is an argument of `evaluate` and is never returned or stored.
`LocalityResult` carries only the coarse signal, the outcome and the flags; nothing else crosses to
the database (sequence (d)).

The boundary is the community's `boundary_polygon`, a GeoJSON Polygon (`{"type": "Polygon",
"coordinates": [[[lng, lat], ...]]}`). A community without one cannot be checked, so the signal is
UNAVAILABLE and the request goes to a moderator: missing evidence is never a negative finding.

Parameters come from config section `locality_a11` (initial, unvalidated values; NFR-Q-04).
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

Point = tuple[float, float]  # (lat, lng)

OUTCOMES = ("VERIFIED", "INCONCLUSIVE", "CONFLICTING")  # three-valued, never a rejection (FR-A-08)


class InvalidInvitation(Exception):
    """UC-A3 3d: the code is invalid, expired, used, self-issued or for another community.

    The member can retry with another code or continue without one (the outcome is then
    INCONCLUSIVE and a moderator decides)."""


@dataclass(frozen=True)
class LocalityConfig:
    max_accuracy_m: float = 100.0  # a fix less accurate than this is UNAVAILABLE
    min_margin_m: float = 50.0  # boundary band is max(min_margin_m, reported accuracy)
    invite_ttl_days: int = 7
    max_open_invites: int = 3
    validity_days: int = 365  # re-verification period

    @classmethod
    def from_section(cls, section: dict[str, Any]) -> "LocalityConfig":
        return cls(
            max_accuracy_m=float(section["max_accuracy_m"]),
            min_margin_m=float(section["min_margin_m"]),
            invite_ttl_days=int(section["invite_ttl_days"]),
            max_open_invites=int(section["max_open_invites"]),
            validity_days=int(section["validity_days"]),
        )


@dataclass(frozen=True)
class Fix:
    """One-time device location fix. Lives only in memory during `evaluate`."""

    lat: float
    lng: float
    accuracy_m: float
    mock_provider: bool = False  # the device reports a mock-location provider


@dataclass(frozen=True)
class Invitation:
    community_id: str
    inviter_id: str
    expires_at: datetime
    used: bool
    inviter_is_approved_member: bool


@dataclass(frozen=True)
class LocalityResult:
    """What may be stored: the coarse signal, the outcome and flags. No coordinates, no accuracy."""

    outcome: str  # VERIFIED | INCONCLUSIVE | CONFLICTING
    geofence_signal: str  # INSIDE | NEAR_BOUNDARY | OUTSIDE | UNAVAILABLE
    invitation_used: bool
    permission_refused: bool
    mock_provider_detected: bool
    duplicate_suspected: bool


def boundary_from_geojson(polygon: dict[str, Any] | None) -> list[Point] | None:
    """The outer ring of a GeoJSON Polygon as [(lat, lng)], or None if absent or malformed."""
    if not polygon or polygon.get("type") != "Polygon":
        return None
    try:
        ring = polygon["coordinates"][0]
        points = [(float(lat), float(lng)) for lng, lat, *_ in ring]
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]  # GeoJSON repeats the first point; the maths below closes the ring
    return points if len(points) >= 3 else None


def _to_metres(lat0: float, lat: float, lng: float) -> Point:
    """Local equirectangular projection; accurate to well under a metre at community scale."""
    k = 111_320.0
    return (lng * k * math.cos(math.radians(lat0)), lat * k)


def _inside(pt: Point, poly: list[Point]) -> bool:
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1], strict=True):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _dist_to_edges(pt: Point, poly: list[Point]) -> float:
    px, py = pt
    best = math.inf
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1], strict=True):
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)))
    return best


def geofence_signal(fix: Fix | None, boundary: list[Point] | None, cfg: LocalityConfig) -> str:
    """Coarse signal from a one-time fix and the community's coarse boundary [(lat, lng), ...]."""
    if fix is None or boundary is None or fix.accuracy_m > cfg.max_accuracy_m:
        return "UNAVAILABLE"
    lat0 = fix.lat
    poly = [_to_metres(lat0, la, lo) for la, lo in boundary]
    pt = _to_metres(lat0, fix.lat, fix.lng)
    if _dist_to_edges(pt, poly) <= max(cfg.min_margin_m, fix.accuracy_m):
        return "NEAR_BOUNDARY"
    return "INSIDE" if _inside(pt, poly) else "OUTSIDE"


def check_invitation(
    inv: Invitation | None, community_id: str, user_id: str, now: datetime
) -> bool:
    """True for a valid invitation, False if none was given; InvalidInvitation for a bad code."""
    if inv is None:
        return False
    if (
        inv.used
        or inv.expires_at <= now
        or inv.community_id != community_id
        or inv.inviter_id == user_id
        or not inv.inviter_is_approved_member
    ):
        raise InvalidInvitation(
            "invitation is invalid, expired, used or not from a member of this community"
        )
    return True


def decide(signal: str, invitation_ok: bool, mock: bool, duplicate: bool) -> str:
    """A11 decision table, identical to `locality_rule_ck` in the schema."""
    if mock or duplicate or signal == "OUTSIDE":
        return (
            "CONFLICTING"  # evidence contradicts the claim: a moderator decides, never auto-reject
        )
    if signal == "INSIDE" and invitation_ok:
        return "VERIFIED"  # two independent signals agree
    return "INCONCLUSIVE"  # one signal missing or weak: a moderator decides


def evaluate(
    *,
    fix: Fix | None,
    permission_refused: bool,
    boundary: list[Point] | None,
    invitation: Invitation | None,
    community_id: str,
    user_id: str,
    duplicate_suspected: bool,
    now: datetime,
    cfg: LocalityConfig,
) -> LocalityResult:
    """Evaluate one join attempt. The fix is used here and dropped; only the result is returned."""
    inv_ok = check_invitation(invitation, community_id, user_id, now)
    signal = "UNAVAILABLE" if permission_refused else geofence_signal(fix, boundary, cfg)
    mock = bool(fix and fix.mock_provider and not permission_refused)
    return LocalityResult(
        outcome=decide(signal, inv_ok, mock, duplicate_suspected),
        geofence_signal=signal,
        invitation_used=inv_ok,
        permission_refused=permission_refused,
        mock_provider_detected=mock,
        duplicate_suspected=duplicate_suspected,
    )
