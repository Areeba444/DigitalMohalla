"""Joining a community and membership decisions (suites 20 and 21; plan items F2, F3).

Through the REST API on PostgreSQL: the locality check runs live (geofence plus invitation) and only
the coarse result is stored; a duplicate request is refused; a moderator sees and decides only
their own community's requests, with a reason; a second decision is refused without applying
anything; a reversal keeps both decisions; an OPEN community approves a VERIFIED request by itself
(M09). Test ids TC-160 to TC-172, input / expected / actual in each docstring.

Everything here is SYNTHETIC: the communities, people and the 600 m x 450 m boundary are made up.
"""

import json
import math
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import count
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.main import create_app

PASSWORD = "synthetic-test-password"  # noqa: S105 - throwaway value for this test database
LAT0, LNG0 = 31.0000, 71.0000
M_LAT, M_LNG = 1 / 111_320, 1 / (111_320 * math.cos(math.radians(LAT0)))
RING = [
    [LNG0, LAT0],
    [LNG0 + 600 * M_LNG, LAT0],
    [LNG0 + 600 * M_LNG, LAT0 + 450 * M_LAT],
    [LNG0, LAT0 + 450 * M_LAT],
    [LNG0, LAT0],
]
BOUNDARY = json.dumps({"type": "Polygon", "coordinates": [RING]})
_n = count()


def fix(east_m: float = 300, north_m: float = 200, acc: float = 20, mock: bool = False) -> dict:
    return {
        "lat": LAT0 + north_m * M_LAT,
        "lng": LNG0 + east_m * M_LNG,
        "accuracy_m": acc,
        "mock_provider": mock,
    }


@dataclass
class M:
    moderated: UUID
    open_: UUID
    other: UUID
    mod1: str
    mod2: str
    mod_other: str
    inviter: str


@pytest.fixture(scope="module")
def m(engine: Engine) -> M:
    with engine.begin() as c:

        def one(sql: str, **kw: object) -> UUID:
            return c.execute(text(sql), kw).scalar_one()

        def community(name: str, policy: str) -> UUID:
            return one(
                "INSERT INTO community (name, join_code, rules, boundary_polygon, join_policy) "
                "VALUES (:n, :j, 'Synthetic rules: return on time.', CAST(:b AS jsonb), "
                "CAST(:p AS join_policy)) RETURNING id",
                n=name,
                j="SYN-" + name.split()[-1].upper(),
                b=BOUNDARY,
                p=policy,
            )

        def person(email: str, community_roles: list[tuple[UUID, str]]) -> str:
            uid = one(
                "INSERT INTO app_user (display_name, email, password_hash, verification_level, "
                "status, is_synthetic) VALUES (:n, :e, :h, 'COMMUNITY_VERIFIED', 'ACTIVE', true) "
                "RETURNING id",
                n=email.split("@")[0],
                e=email,
                h=hash_password(PASSWORD),
            )
            for cid, role in community_roles:
                c.execute(
                    text(
                        "INSERT INTO membership (user_id, community_id, role, status, decided_at) "
                        "VALUES (:u, :c, CAST(:r AS membership_role), 'APPROVED', now())"
                    ),
                    {"u": uid, "c": cid, "r": role},
                )
            return email

        moderated = community("Synthetic Join Moderated", "MODERATED")
        open_ = community("Synthetic Join Open", "OPEN")
        other = community("Synthetic Join Other", "MODERATED")
        return M(
            moderated,
            open_,
            other,
            person("jmod1@example.test", [(moderated, "MODERATOR")]),
            person("jmod2@example.test", [(moderated, "MODERATOR")]),
            person("jmodother@example.test", [(other, "MODERATOR")]),
            person("jinviter@example.test", [(moderated, "MEMBER"), (open_, "MEMBER")]),
        )


@pytest.fixture
def client(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def login(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def applicant(engine: Engine, level: str = "CONTACT_VERIFIED") -> tuple[str, UUID]:
    email = f"japplicant{next(_n)}@example.test"
    with engine.begin() as c:
        uid = c.execute(
            text(
                "INSERT INTO app_user (display_name, email, password_hash, verification_level, "
                "status, is_synthetic) VALUES ('Applicant', :e, :h, "
                "CAST(:l AS verification_level), 'ACTIVE', true) RETURNING id"
            ),
            {"e": email, "h": hash_password(PASSWORD), "l": level},
        ).scalar_one()
    return email, uid


def invitation(client: TestClient, m: M, community: UUID) -> str:
    r = client.post(
        f"/api/v1/communities/{community}/invitations", headers=login(client, m.inviter)
    )
    assert r.status_code == 201, r.text
    return str(r.json()["code"])


def join(client: TestClient, email: str, community: UUID, **body: object):  # type: ignore[no-untyped-def]
    return client.post(
        f"/api/v1/communities/{community}/join", json=body, headers=login(client, email)
    )


def test_tc160_communities_by_name_or_code_with_rules_and_methods(
    client: TestClient, m: M, engine: Engine
) -> None:
    """Input: search "join moderated", then the join code. Expected: the community, its rules and
    both verification methods; no boundary coordinates in the response."""
    h = login(client, m.inviter)
    by_name = client.get("/api/v1/communities?query=join moderated", headers=h).json()
    assert [c["name"] for c in by_name] == ["Synthetic Join Moderated"]
    c0 = by_name[0]
    assert c0["rules"] and c0["methods"] == ["GEOFENCE_INVITATION", "MODERATOR_APPROVAL"]
    assert c0["has_boundary"] is True and "boundary_polygon" not in c0
    by_code = client.get(f"/api/v1/communities?query={c0['join_code']}", headers=h).json()
    assert [c["id"] for c in by_code] == [c0["id"]]


def test_tc161_inside_with_invitation_is_verified_and_waits_for_a_moderator(
    client: TestClient, m: M, engine: Engine
) -> None:
    """Input: fix 150 m inside, accuracy 20 m, valid code, MODERATED community. Expected: 201,
    PENDING, VERIFIED; only the coarse signal stored; moderators notified; invitation now used."""
    email, uid = applicant(engine)
    code = invitation(client, m, m.moderated)
    r = join(client, email, m.moderated, fix=fix(), invitation_code=code)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "PENDING" and body["locality"]["outcome"] == "VERIFIED"
    assert "lat" not in json.dumps(body)
    with engine.connect() as c:
        lv = (
            c.execute(
                text(
                    "SELECT lv.* FROM locality_verification lv JOIN membership mm "
                    "ON mm.id = lv.membership_id WHERE mm.user_id = :u"
                ),
                {"u": uid},
            )
            .mappings()
            .one()
        )
        cols = set(lv.keys())
        assert not {k for k in cols if any(t in k for t in ("lat", "lng", "lon", "accura"))}
        assert (lv["outcome"], lv["geofence_signal"]) == ("VERIFIED", "INSIDE")
        assert lv["invitation_id"] is not None
        told = c.execute(
            text("SELECT count(*) FROM notification WHERE dedupe_key = :k"),
            {"k": f"{body['membership_id']}:request"},
        ).scalar_one()
        assert told == 2  # both moderators of the community
        audit = (
            c.execute(
                text("SELECT new_value::text FROM audit_log WHERE target_id = :t"),
                {"t": body["membership_id"]},
            )
            .scalars()
            .all()
        )
        assert audit and not any("lat" in a or "lng" in a for a in audit)
    again = join(client, applicant(engine)[0], m.moderated, fix=fix(), invitation_code=code)
    assert again.status_code == 422  # TC-165: the code is single-use


def test_tc162_a_second_request_is_refused_and_shows_the_status(
    client: TestClient, m: M, engine: Engine
) -> None:
    """Input: the same member joins twice. Expected: 409 naming the pending request."""
    email, _ = applicant(engine)
    assert join(client, email, m.moderated, permission_refused=True).status_code == 201
    second = join(client, email, m.moderated, permission_refused=True)
    assert second.status_code == 409 and "pending" in second.json()["detail"]


@pytest.mark.parametrize(
    ("body", "outcome"),
    [
        ({"permission_refused": True}, "INCONCLUSIVE"),  # ES-10 / L4
        ({"fix": fix(mock=True)}, "CONFLICTING"),  # L1a
        ({"fix": fix(east_m=2600)}, "CONFLICTING"),  # L1c, OUTSIDE
        ({"fix": fix(east_m=30)}, "INCONCLUSIVE"),  # L2a, NEAR_BOUNDARY
        ({"fix": fix(acc=250)}, "INCONCLUSIVE"),  # L6b
    ],
)
def test_tc163_no_check_is_a_rejection(
    client: TestClient, m: M, engine: Engine, body: dict, outcome: str
) -> None:
    """Input: weak or contradicting evidence. Expected: PENDING with INCONCLUSIVE or CONFLICTING,
    in the moderator's queue; never REJECTED (FR-A-08, NFR-Q-04)."""
    email, _ = applicant(engine)
    r = join(client, email, m.moderated, **body)
    assert r.status_code == 201, r.text
    assert (r.json()["status"], r.json()["locality"]["outcome"]) == ("PENDING", outcome)


def test_tc164_unknown_or_unverified_applicant(client: TestClient, m: M, engine: Engine) -> None:
    """Input: a bad code; an UNVERIFIED account. Expected: 422 retryable; 403 verify contact."""
    email, _ = applicant(engine)
    bad = join(client, email, m.moderated, fix=fix(), invitation_code="ZZZZ-ZZZZ")
    assert bad.status_code == 422 and "retry" in bad.json()["detail"]
    unverified, _ = applicant(engine, "UNVERIFIED")
    assert join(client, unverified, m.moderated, permission_refused=True).status_code == 403
    both = join(client, email, m.moderated, fix=fix(), permission_refused=True)
    assert both.status_code == 422


def test_tc166_moderator_sees_and_decides_only_their_own_community(
    client: TestClient, m: M, engine: Engine
) -> None:
    """Input: a request in Moderated; the moderator of Other tries to decide. Expected: absent from
    their queue; 403; a REJECTED audit row."""
    email, _ = applicant(engine)
    mid = join(client, email, m.moderated, permission_refused=True).json()["membership_id"]
    own = client.get("/api/v1/moderation/memberships", headers=login(client, m.mod1)).json()
    entry = next(q for q in own if q["membership_id"] == mid)
    assert entry["locality_outcome"] == "INCONCLUSIVE" and entry["permission_refused"] is True
    other_h = login(client, m.mod_other)
    other = client.get("/api/v1/moderation/memberships", headers=other_h).json()
    assert mid not in {q["membership_id"] for q in other}
    refused = client.post(
        f"/api/v1/moderation/memberships/{mid}/decision",
        json={"kind": "APPROVED", "reason": "looks fine"},
        headers=other_h,
    )
    assert refused.status_code == 403
    with engine.connect() as c:
        logged = c.execute(
            text(
                "SELECT count(*) FROM audit_log WHERE target_type = 'membership' "
                "AND target_id = :t AND outcome = 'REJECTED'"
            ),
            {"t": mid},
        ).scalar_one()
    assert logged == 1


def test_tc167_approval_needs_a_reason_and_records_moderator_approval(
    client: TestClient, m: M, engine: Engine
) -> None:
    """Input: approve an INCONCLUSIVE request, first with an empty reason. Expected: 422, then
    APPROVED; MODERATOR_APPROVAL stored; locality now VERIFIED for borrowing; applicant told."""
    email, uid = applicant(engine)
    mid = join(client, email, m.moderated, permission_refused=True).json()["membership_id"]
    h = login(client, m.mod1)
    url = f"/api/v1/moderation/memberships/{mid}/decision"
    assert client.post(url, json={"kind": "APPROVED", "reason": "  "}, headers=h).status_code == 422
    ok = client.post(url, json={"kind": "APPROVED", "reason": "Known to two members"}, headers=h)
    assert ok.status_code == 200 and ok.json()["status"] == "APPROVED"
    with engine.connect() as c:
        assert (
            c.execute(
                text("SELECT locality_outcome_for(:u, :c)::text"), {"u": uid, "c": m.moderated}
            ).scalar_one()
            == "VERIFIED"
        )
        assert (
            c.execute(
                text("SELECT verification_level::text FROM app_user WHERE id = :u"), {"u": uid}
            ).scalar_one()
            == "COMMUNITY_VERIFIED"
        )
        methods = (
            c.execute(
                text(
                    "SELECT method::text FROM locality_verification WHERE membership_id = :m "
                    "ORDER BY checked_at"
                ),
                {"m": mid},
            )
            .scalars()
            .all()
        )
        assert methods == ["GEOFENCE_INVITATION", "MODERATOR_APPROVAL"]
    inbox = client.get("/api/v1/notifications", headers=login(client, email)).json()
    assert [n["payload"]["status"] for n in inbox["notifications"]] == ["APPROVED"]


def test_tc168_second_decision_is_refused_and_nothing_applies_twice(
    client: TestClient, m: M, engine: Engine
) -> None:
    """Input: moderator 1 rejects, then moderator 2 approves the same request. Expected: the second
    gets 409; the membership stays REJECTED; one decision row (FR-A-11)."""
    email, _ = applicant(engine)
    mid = join(client, email, m.moderated, fix=fix(east_m=2600)).json()["membership_id"]
    url = f"/api/v1/moderation/memberships/{mid}/decision"
    first = client.post(
        url, json={"kind": "REJECTED", "reason": "Outside"}, headers=login(client, m.mod1)
    )
    assert first.status_code == 200
    second = client.post(
        url, json={"kind": "APPROVED", "reason": "Fine"}, headers=login(client, m.mod2)
    )
    assert second.status_code == 409
    with engine.connect() as c:
        rows = (
            c.execute(
                text("SELECT kind::text FROM membership_decision WHERE membership_id = :m"),
                {"m": mid},
            )
            .scalars()
            .all()
        )
    assert rows == ["REJECTED"]


def test_tc169_reversal_keeps_both_decisions(client: TestClient, m: M, engine: Engine) -> None:
    """Input: moderator 1 rejects; moderator 1 then tries to reverse; moderator 2 reverses.
    Expected: 403 for the same moderator; APPROVED after moderator 2; both rows kept."""
    email, _ = applicant(engine)
    mid = join(client, email, m.moderated, fix=fix(mock=True)).json()["membership_id"]
    url = f"/api/v1/moderation/memberships/{mid}/decision"
    client.post(url, json={"kind": "REJECTED", "reason": "Mock"}, headers=login(client, m.mod1))
    with engine.connect() as c:
        rejected = c.execute(
            text("SELECT id FROM membership_decision WHERE membership_id = :m"), {"m": mid}
        ).scalar_one()
    body = {"kind": "REVERSED", "reason": "Device fault", "reverses_decision_id": str(rejected)}
    assert client.post(url, json=body, headers=login(client, m.mod1)).status_code == 403
    ok = client.post(url, json=body, headers=login(client, m.mod2))
    assert ok.status_code == 200 and ok.json()["status"] == "APPROVED"
    with engine.connect() as c:
        kinds = (
            c.execute(
                text(
                    "SELECT kind::text FROM membership_decision WHERE membership_id = :m "
                    "ORDER BY decided_at"
                ),
                {"m": mid},
            )
            .scalars()
            .all()
        )
    assert kinds == ["REJECTED", "REVERSED"]


def test_tc170_open_community_approves_only_a_verified_check(
    client: TestClient, m: M, engine: Engine
) -> None:
    """Input: OPEN community; VERIFIED join, then an INCONCLUSIVE one. Expected: the first APPROVED
    by the system (M09), the second PENDING for a moderator."""
    email, uid = applicant(engine)
    code = invitation(client, m, m.open_)
    auto = join(client, email, m.open_, fix=fix(), invitation_code=code)
    assert auto.json()["status"] == "APPROVED", auto.text
    with engine.connect() as c:
        assert (
            c.execute(
                text("SELECT locality_outcome_for(:u, :c)::text"), {"u": uid, "c": m.open_}
            ).scalar_one()
            == "VERIFIED"
        )
    weak = join(client, applicant(engine)[0], m.open_, permission_refused=True)
    assert weak.json()["status"] == "PENDING"


def test_tc171_invitations_only_from_members_and_only_hashes_stored(
    client: TestClient, m: M, engine: Engine
) -> None:
    """Input: a non-member asks for a code; a member asks until the limit. Expected: 403; codes
    until max_open_invites, then 422; the plain code is nowhere in the database."""
    outsider, _ = applicant(engine)
    url = f"/api/v1/communities/{m.other}/invitations"
    assert client.post(url, headers=login(client, outsider)).status_code == 403
    with engine.begin() as c:
        c.execute(
            text(
                "INSERT INTO membership (user_id, community_id, status, decided_at) "
                "SELECT id, :c, 'APPROVED', now() FROM app_user WHERE email = :e"
            ),
            {"c": m.other, "e": outsider},
        )
    h = login(client, outsider)
    codes = [client.post(url, headers=h) for _ in range(4)]
    assert [r.status_code for r in codes] == [201, 201, 201, 422]
    with engine.connect() as c:
        dump = c.execute(text("SELECT string_agg(encode(code_hash, 'escape'), '') FROM invitation"))
        stored = dump.scalar_one() or ""
    assert not any(r.json()["code"] in stored for r in codes[:3])


def test_tc172_unknown_community_and_not_logged_in(client: TestClient, m: M) -> None:
    """Expected: 404 for an unknown community; 401 without a login; 422 for a stray field."""
    assert client.get("/api/v1/communities").status_code == 401
    h = login(client, m.inviter)
    unknown = "00000000-0000-0000-0000-000000000000"
    r = client.post(
        f"/api/v1/communities/{unknown}/join", json={"permission_refused": True}, headers=h
    )
    assert r.status_code == 404
    stray = client.post(f"/api/v1/communities/{m.moderated}/join", json={"address": "x"}, headers=h)
    assert stray.status_code == 422
