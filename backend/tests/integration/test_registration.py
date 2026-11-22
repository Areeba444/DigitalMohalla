"""Registration through the API (UC-A1; FR-A-01; NFR-S-01), and the proofs the plan lists for F7:
a restricted item is refused with a neutral message (FR-B-02) and an identical pending request is
refused as a duplicate (FR-B-06, TC-70). All data is synthetic; the passwords are throwaway values for
this test database only.
"""

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.api import routes as api_routes
from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.domain.accounts.registration import GENERIC_REPLY
from app.domain.lifecycle.service import RESTRICTED_ITEM_MESSAGE
from app.main import create_app
from tests.integration.conftest import World
from tests.integration.test_api import TEST_PASSWORD, dates, login


def login_as(client: TestClient, email: str, password: str) -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


FORM = {
    "display_name": "Registration Synthetic",
    "email": "reg-synthetic@example.test",
    "password": "a-long-synthetic-pass",
    "accepted_terms": True,
}


@pytest.fixture
def api_client(
    engine: Engine, world: World, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    with engine.begin() as c:
        c.execute(
            text("UPDATE app_user SET password_hash = :h WHERE id = :i"),
            {"h": hash_password(TEST_PASSWORD), "i": world.borrower},
        )
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


@pytest.fixture
def reg_client(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def rows(engine: Engine, email: str) -> list[dict]:
    with engine.connect() as c:
        return [
            dict(r)
            for r in c.execute(
                text(
                    "SELECT status::text AS status, verification_level::text AS level, "
                    "terms_accepted_at, password_hash, display_name FROM app_user "
                    "WHERE lower(email) = :e"
                ),
                {"e": email},
            ).mappings()
        ]


def test_tc174_registering_creates_a_pending_account_with_the_terms_time(
    reg_client: TestClient, engine: Engine
) -> None:
    email = "reg-tc174@example.test"
    r = reg_client.post("/api/v1/auth/register", json={**FORM, "email": email})
    assert r.status_code == 202 and r.json() == {"message": GENERIC_REPLY}
    [row] = rows(engine, email)
    assert (row["status"], row["level"]) == ("PENDING_VERIFICATION", "UNVERIFIED")
    assert row["terms_accepted_at"] is not None
    assert row["password_hash"] and FORM["password"] not in row["password_hash"]  # hashed
    assert row["password_hash"].startswith("$argon2")


def test_tc175_a_registered_email_gets_the_same_reply_and_no_second_account(
    reg_client: TestClient, engine: Engine
) -> None:
    email = "reg-tc175@example.test"
    first = reg_client.post("/api/v1/auth/register", json={**FORM, "email": email})
    again = reg_client.post(
        "/api/v1/auth/register",
        json={**FORM, "email": email.upper(), "display_name": "Someone Else"},  # case differs
    )
    assert (first.status_code, first.json()) == (again.status_code, again.json())
    [row] = rows(engine, email)  # exactly one, and the first registration's name
    assert row["display_name"] == "Registration Synthetic"


@pytest.mark.parametrize(
    ("change", "text_in"),
    [
        ({"accepted_terms": False}, "terms"),
        ({"password": "short"}, "password"),
        ({"email": "not-an-email"}, "e-mail"),
        ({"display_name": "  "}, "display name"),
    ],
)
def test_tc176_an_invalid_form_creates_nothing_and_says_what_to_fix(
    reg_client: TestClient, engine: Engine, change: dict, text_in: str
) -> None:
    email = "reg-tc176@example.test"
    r = reg_client.post("/api/v1/auth/register", json={**FORM, "email": email, **change})
    if "email" in change:
        email = change["email"]
    assert r.status_code == 422 and text_in in r.json()["detail"]
    assert rows(engine, email) == []
    assert FORM["password"] not in r.text


def test_tc176_the_form_rejects_unknown_fields(reg_client: TestClient) -> None:
    extra = reg_client.post("/api/v1/auth/register", json={**FORM, "platform_role": "ADMIN"})
    assert extra.status_code == 422  # a guest cannot ask for a role


def test_tc178_while_otp_is_not_built_a_pending_account_can_sign_in(
    reg_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Documented interim (config registration_a1.otp_built false): registered accounts may sign
    in. When OTP exists the switch is set to true and a pending account is refused again."""
    email = "reg-tc178@example.test"
    reg_client.post("/api/v1/auth/register", json={**FORM, "email": email})
    creds = {"email": email, "password": FORM["password"]}
    assert reg_client.post("/api/v1/auth/login", json=creds).status_code == 200
    real = api_routes.load_engine_config

    class Switch:
        def section(self, name: str) -> dict:
            section = dict(real().section(name))
            if name == "registration_a1":
                section["otp_built"] = True
            return section

    monkeypatch.setattr(api_routes, "load_engine_config", lambda: Switch())
    assert reg_client.post("/api/v1/auth/login", json=creds).status_code == 401


def test_tc179_a_registered_member_joins_and_approval_activates_the_account(
    reg_client: TestClient, engine: Engine, world: World
) -> None:
    email = "reg-tc179@example.test"
    reg_client.post("/api/v1/auth/register", json={**FORM, "email": email})
    member = login_as(reg_client, email, FORM["password"])
    joined = reg_client.post(
        f"/api/v1/communities/{world.community}/join",
        json={"permission_refused": True},
        headers=member,
    )
    assert joined.status_code == 201, joined.text
    assert rows(engine, email)[0]["status"] == "PENDING_VERIFICATION"  # waiting for a moderator
    with engine.begin() as c:
        c.execute(
            text("UPDATE app_user SET password_hash = :h WHERE id = :i"),
            {"h": hash_password(TEST_PASSWORD), "i": world.moderator},
        )
        mod_email = c.execute(
            text("SELECT email FROM app_user WHERE id = :i"), {"i": world.moderator}
        ).scalar_one()
    mod = login_as(reg_client, mod_email, TEST_PASSWORD)
    decided = reg_client.post(
        f"/api/v1/moderation/memberships/{joined.json()['membership_id']}/decision",
        json={"kind": "APPROVED", "reason": "Synthetic: known neighbour."},
        headers=mod,
    )
    assert decided.status_code == 200, decided.text
    row = rows(engine, email)[0]
    assert (row["status"], row["level"]) == ("ACTIVE", "COMMUNITY_VERIFIED")


# ----------------------------------------------------------------------------- B-02 and B-06 proofs
def set_item_level(engine: Engine, item: UUID, level: str) -> None:
    with engine.begin() as c:
        c.execute(
            text(
                "UPDATE item SET required_verification = CAST(:l AS verification_level) "
                "WHERE id = :i"
            ),
            {"l": level, "i": item},
        )


def set_borrower_level(engine: Engine, user: UUID, level: str) -> None:
    with engine.begin() as c:
        c.execute(
            text(
                "UPDATE app_user SET verification_level = CAST(:l AS verification_level) WHERE id = :u"
            ),
            {"l": level, "u": user},
        )


def borrower_email(engine: Engine, world: World) -> str:
    with engine.connect() as c:
        return str(
            c.execute(
                text("SELECT email FROM app_user WHERE id = :i"), {"i": world.borrower}
            ).scalar()
        )


def test_tc177_a_restricted_item_is_refused_neutrally_and_nothing_is_created(
    api_client: TestClient,
    engine: Engine,
    world: World,
) -> None:
    item = world.items[17]
    count = "SELECT count(*) FROM borrowing_transaction WHERE item_id = :i"
    with engine.connect() as c:  # other tests share this item, so compare before and after
        before = c.execute(text(count), {"i": item}).scalar_one()
    set_item_level(engine, item, "COMMUNITY_VERIFIED")
    set_borrower_level(engine, world.borrower, "CONTACT_VERIFIED")
    headers = login(api_client, borrower_email(engine, world))
    r = api_client.post(
        "/api/v1/requests", json={"item_id": str(item), **dates(6, 2)}, headers=headers
    )
    assert r.status_code == 403 and r.json()["detail"] == RESTRICTED_ITEM_MESSAGE
    detail = r.json()["detail"].lower()
    assert "g1" not in detail and not any(w in detail for w in ("suspicious", "risk", "fraud"))
    with engine.connect() as c:
        assert c.execute(text(count), {"i": item}).scalar_one() == before  # nothing created
    # the same item is open to a borrower at the required level
    set_borrower_level(engine, world.borrower, "COMMUNITY_VERIFIED")
    ok = api_client.post(
        "/api/v1/requests", json={"item_id": str(item), **dates(6, 2)}, headers=headers
    )
    assert ok.status_code == 201, ok.text


def test_tc70_an_identical_pending_request_is_refused_as_a_duplicate(
    api_client: TestClient,
    engine: Engine,
    world: World,
) -> None:
    set_borrower_level(engine, world.borrower, "COMMUNITY_VERIFIED")
    headers = login(api_client, borrower_email(engine, world))
    count = "SELECT count(*) FROM borrowing_transaction WHERE item_id = :i AND borrower_id = :b"
    args = {"i": world.items[16], "b": world.borrower}
    with engine.connect() as c:  # the test database keeps rows from earlier runs: count the change
        before = c.execute(text(count), args).scalar_one()
    body = {"item_id": str(world.items[16]), **dates(9, 2)}
    first = api_client.post("/api/v1/requests", json=body, headers=headers)
    assert first.status_code == 201, first.text
    second = api_client.post("/api/v1/requests", json=body, headers=headers)
    assert second.status_code == 409 and "identical pending request" in second.json()["detail"]
    with engine.connect() as c:
        assert c.execute(text(count), args).scalar_one() == before + 1
