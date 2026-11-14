"""Locality at runtime (suite 20, F3): the A11 cases through the backend's LocalityVerifier.

The same cases as the design oracle `docs/design/12_locality/test_locality_cases.py` (six required
cases L1 to L6, invitation errors E1 to E4, privacy P1, no automatic rejection P2), now run against
`app.domain.membership.locality` with the parameters from `backend/config/engine.json`. Every input
is SYNTHETIC: a made-up rectangular community about 600 m by 450 m. No outcome is ever a rejection
(NFR-Q-04, FR-A-08).
"""

import dataclasses
import math
from datetime import datetime, timedelta

import pytest

from app.config.engine_config import load_engine_config
from app.domain.membership.locality import (
    OUTCOMES,
    Fix,
    InvalidInvitation,
    Invitation,
    LocalityConfig,
    LocalityResult,
    boundary_from_geojson,
    evaluate,
)

CFG = LocalityConfig.from_section(load_engine_config().section("locality_a11"))
NOW = datetime(2026, 10, 11, 12, 0)
LAT0, LNG0 = 30.0000, 70.0000  # synthetic origin
M_LAT, M_LNG = 1 / 111_320, 1 / (111_320 * math.cos(math.radians(LAT0)))
RING = [
    [LNG0, LAT0],
    [LNG0 + 600 * M_LNG, LAT0],
    [LNG0 + 600 * M_LNG, LAT0 + 450 * M_LAT],
    [LNG0, LAT0 + 450 * M_LAT],
    [LNG0, LAT0],
]
GEOJSON = {"type": "Polygon", "coordinates": [RING]}  # how community.boundary_polygon stores it
BOUNDARY = boundary_from_geojson(GEOJSON)
GOOD_INV = Invitation("C1", "inviter", NOW + timedelta(days=5), False, True)


def at(east_m: float, north_m: float, acc: float = 20.0, mock: bool = False) -> Fix:
    return Fix(LAT0 + north_m * M_LAT, LNG0 + east_m * M_LNG, acc, mock)


def run(
    fix: Fix | None = None,
    refused: bool = False,
    inv: Invitation | None = None,
    dup: bool = False,
    boundary: object = BOUNDARY,
) -> LocalityResult:
    return evaluate(
        fix=fix,
        permission_refused=refused,
        boundary=boundary,  # type: ignore[arg-type]
        invitation=inv,
        community_id="C1",
        user_id="u1",
        duplicate_suspected=dup,
        now=NOW,
        cfg=CFG,
    )


# id, input, kwargs, expected (outcome, signal)
CASES = [
    (
        "L1a",
        "spoof: inside, mock provider, invitation",
        dict(fix=at(300, 200, mock=True), inv=GOOD_INV),
        ("CONFLICTING", "INSIDE"),
    ),
    (
        "L1b",
        "spoof undetected: inside, no invitation",
        dict(fix=at(300, 200)),
        ("INCONCLUSIVE", "INSIDE"),
    ),
    (
        "L1c",
        "spoof places user 2 km away",
        dict(fix=at(2600, 200), inv=GOOD_INV),
        ("CONFLICTING", "OUTSIDE"),
    ),
    (
        "L2a",
        "30 m inside the edge, invitation",
        dict(fix=at(30, 200), inv=GOOD_INV),
        ("INCONCLUSIVE", "NEAR_BOUNDARY"),
    ),
    (
        "L2b",
        "30 m outside the edge, invitation",
        dict(fix=at(-30, 200), inv=GOOD_INV),
        ("INCONCLUSIVE", "NEAR_BOUNDARY"),
    ),
    (
        "L2c",
        "150 m inside the edge, invitation",
        dict(fix=at(150, 200), inv=GOOD_INV),
        ("VERIFIED", "INSIDE"),
    ),
    ("L3", "visitor: inside, no invitation", dict(fix=at(300, 200)), ("INCONCLUSIVE", "INSIDE")),
    (
        "L4",
        "permission refused, invitation",
        dict(refused=True, inv=GOOD_INV),
        ("INCONCLUSIVE", "UNAVAILABLE"),
    ),
    (
        "L5",
        "duplicate-account signal",
        dict(fix=at(300, 200), inv=GOOD_INV, dup=True),
        ("CONFLICTING", "INSIDE"),
    ),
    (
        "L6a",
        "resident at home, invitation",
        dict(fix=at(300, 200), inv=GOOD_INV),
        ("VERIFIED", "INSIDE"),
    ),
    (
        "L6b",
        "resident indoors, accuracy 250 m",
        dict(fix=at(300, 200, acc=250), inv=GOOD_INV),
        ("INCONCLUSIVE", "UNAVAILABLE"),
    ),
    ("L6c", "new resident, knows no member", dict(fix=at(300, 200)), ("INCONCLUSIVE", "INSIDE")),
]


@pytest.mark.parametrize(("cid", "desc", "kwargs", "expected"), CASES, ids=[c[0] for c in CASES])
def test_a11_case(cid: str, desc: str, kwargs: dict, expected: tuple[str, str]) -> None:
    r = run(**kwargs)
    assert (r.outcome, r.geofence_signal) == expected, f"{cid}: {desc}"


ERRORS = [
    ("E1", Invitation("C1", "inviter", NOW - timedelta(days=1), False, True)),  # expired
    ("E2", Invitation("C1", "inviter", NOW + timedelta(days=5), True, True)),  # used
    ("E3", Invitation("C2", "inviter", NOW + timedelta(days=5), False, True)),  # other community
    ("E4", Invitation("C1", "u1", NOW + timedelta(days=5), False, True)),  # self-invitation
    (
        "E5",
        Invitation("C1", "inviter", NOW + timedelta(days=5), False, False),
    ),  # inviter not approved
]


@pytest.mark.parametrize(("cid", "inv"), ERRORS, ids=[e[0] for e in ERRORS])
def test_bad_invitation_is_an_error_the_member_can_retry(cid: str, inv: Invitation) -> None:
    with pytest.raises(InvalidInvitation):
        run(fix=at(300, 200), inv=inv)


def test_p1_result_has_no_coordinates_or_accuracy() -> None:
    stored = dataclasses.asdict(run(fix=at(300, 200), inv=GOOD_INV))
    assert not [
        k
        for k in stored
        if any(t in k for t in ("lat", "lng", "lon", "accuracy", "coord", "address"))
    ]
    assert not any(isinstance(v, float) for v in stored.values())


def test_p2_no_combination_is_a_rejection() -> None:
    outs = {
        run(fix=at(e, 200, a, m), inv=i, dup=d).outcome
        for e in (-500, -30, 30, 300)
        for a in (20, 250)
        for m in (False, True)
        for i in (None, GOOD_INV)
        for d in (False, True)
    }
    assert outs <= set(OUTCOMES)


def test_community_without_a_boundary_is_inconclusive_not_negative() -> None:
    r = run(fix=at(300, 200), inv=GOOD_INV, boundary=None)
    assert (r.outcome, r.geofence_signal) == ("INCONCLUSIVE", "UNAVAILABLE")


def test_mock_flag_is_ignored_when_permission_was_refused() -> None:
    r = run(fix=at(300, 200, mock=True), refused=True, inv=GOOD_INV)
    assert (r.outcome, r.mock_provider_detected) == ("INCONCLUSIVE", False)


@pytest.mark.parametrize(
    "polygon",
    [
        None,
        {},
        {"type": "Point", "coordinates": [70, 30]},
        {"type": "Polygon", "coordinates": [[[70, 30], [71, 30]]]},
    ],
)
def test_malformed_boundary_reads_as_none(polygon: dict | None) -> None:
    assert boundary_from_geojson(polygon) is None


def test_geojson_ring_is_read_as_lat_lng_without_the_closing_point() -> None:
    assert BOUNDARY is not None and len(BOUNDARY) == 4
    assert BOUNDARY[0] == (LAT0, LNG0)
