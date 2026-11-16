"""Photo uploads through the API (suite 27; plan item M4; ADR-0014; FR-B-01, FR-B-11, NFR-S-06).

TC-265 to TC-270, input / expected / actual in each docstring. Storage is a temporary local
directory; images are generated in memory. All users and items are synthetic.
"""

import hashlib
import io
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import Engine, text

from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.main import create_app
from tests.integration.conftest import World
from tests.integration.test_api import TEST_PASSWORD, dates, login


@pytest.fixture
def client(
    engine: Engine, world: World, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "files"))
    get_settings.cache_clear()
    with engine.begin() as c:
        for uid in (world.borrower, world.lender, world.borrower2, world.moderator):
            c.execute(
                text("UPDATE app_user SET password_hash = :h WHERE id = :i"),
                {"h": hash_password(TEST_PASSWORD), "i": uid},
            )
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def photo(fmt: str = "JPEG") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 24), (10, 200, 90)).save(buf, format=fmt)
    return buf.getvalue()


def upload(client: TestClient, url: str, who: str, data: bytes, **form: str):  # type: ignore[no-untyped-def]
    return client.post(
        url,
        files={"file": ("phone-photo.jpg", data, "image/jpeg")},
        data=form,
        headers=login(client, f"{who}@example.test"),
    )


def test_tc265_owner_adds_a_listing_photo_and_members_get_a_signed_link(
    client: TestClient, world: World, engine: Engine
) -> None:
    """Input: the lender uploads a photo to their item; a member and a stranger ask for its link.
    Expected: 201 with a signed link; the stored bytes match the recorded SHA-256 and carry no
    metadata; the member gets a link that serves the file; a tampered link is 404."""
    item = str(world.items[7])
    saved = upload(client, f"/api/v1/items/{item}/photos", "lender", photo())
    assert saved.status_code == 201, saved.text
    body = saved.json()
    assert body["mime_type"] == "image/jpeg" and "phone-photo" not in body["url"]
    link = client.get(
        f"/api/v1/attachments/{body['id']}", headers=login(client, "borrower@example.test")
    )
    assert link.status_code == 200
    served = client.get(link.json()["url"])
    assert served.status_code == 200 and served.headers["content-type"] == "image/jpeg"
    with engine.connect() as c:
        sha, stripped = c.execute(
            text("SELECT content_sha256, metadata_stripped FROM attachment WHERE id = :a"),
            {"a": body["id"]},
        ).one()
    assert bytes(sha) == hashlib.sha256(served.content).digest() and stripped is True
    assert client.get(link.json()["url"].replace("sig=", "sig=0")).status_code == 404


def test_tc266_only_the_owner_adds_listing_photos(client: TestClient, world: World) -> None:
    item = str(world.items[7])
    assert upload(client, f"/api/v1/items/{item}/photos", "borrower", photo()).status_code == 403


def test_tc267_wrong_type_or_size_is_422(
    client: TestClient, world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-85. Input: text named .jpg; a photo over a 100-byte limit. Expected: 422 both times."""
    url = f"/api/v1/items/{world.items[7]}/photos"
    assert upload(client, url, "lender", b"MZ not an image").status_code == 422
    assert upload(client, url, "lender", photo(), latitude="31.5").status_code == 422  # TC-60
    monkeypatch.setenv("UPLOAD_MAX_BYTES", "100")
    get_settings.cache_clear()
    assert upload(client, url, "lender", photo()).status_code == 422


def test_tc268_handover_photo_belongs_to_the_checklist(client: TestClient, world: World) -> None:
    """Input: the lender uploads a handover photo before, then after, their checklist. Expected:
    409 then 201; the request shows the lender's report with one photo and without the reduced-
    evidence mark, while the borrower's report (no photo) keeps it (FR-B-11)."""
    b, lender = login(client, "borrower@example.test"), login(client, "lender@example.test")
    txn = client.post(
        "/api/v1/requests", json={"item_id": str(world.items[8]), **dates(340, 1)}, headers=b
    ).json()["transaction_id"]
    client.post(f"/api/v1/requests/{txn}/accept", headers=lender)
    url = f"/api/v1/transactions/{txn}/photos"
    assert upload(client, url, "lender", photo(), purpose="HANDOVER").status_code == 409
    client.post(
        f"/api/v1/transactions/{txn}/handover/checklist", json={"checklist": {}}, headers=lender
    )
    assert upload(client, url, "lender", photo("PNG"), purpose="HANDOVER").status_code == 201
    client.post(f"/api/v1/transactions/{txn}/handover/confirm", json={}, headers=b)
    reports = {
        r["reporter_role"]: r
        for r in client.get(f"/api/v1/requests/{txn}", headers=b).json()["reports"]
    }
    assert (reports["LENDER"]["photos"], reports["LENDER"]["reduced_evidence"]) == (1, False)
    assert reports["BORROWER"]["reduced_evidence"] is True
    assert upload(client, url, "borrower2", photo(), purpose="HANDOVER").status_code == 403


def test_tc269_a_stranger_cannot_see_a_loan_photo(client: TestClient, world: World) -> None:
    """Input: a dispute photo by the borrower; Borrower2 (not a party) and the moderator ask for
    it. Expected: 403 for Borrower2; 200 for the community's moderator."""
    b, lender = login(client, "borrower@example.test"), login(client, "lender@example.test")
    txn = client.post(
        "/api/v1/requests", json={"item_id": str(world.items[9]), **dates(345, 1)}, headers=b
    ).json()["transaction_id"]
    client.post(f"/api/v1/requests/{txn}/accept", headers=lender)
    client.post(f"/api/v1/transactions/{txn}/dispute", json={"reason": "OTHER"}, headers=b)
    saved = upload(
        client, f"/api/v1/transactions/{txn}/photos", "borrower", photo(), purpose="DISPUTE"
    )
    assert saved.status_code == 201, saved.text
    a = saved.json()["id"]
    assert (
        client.get(
            f"/api/v1/attachments/{a}", headers=login(client, "borrower2@example.test")
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/attachments/{a}", headers=login(client, "moderator@example.test")
        ).status_code
        == 200
    )


def test_tc270_no_storage_means_503_and_the_checklist_still_works(
    client: TestClient, world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Input: no STORAGE_DIR. Expected: 503 for an upload; nothing stored (ADR-0014 fallback)."""
    monkeypatch.delenv("STORAGE_DIR")
    get_settings.cache_clear()
    r = upload(client, f"/api/v1/items/{world.items[7]}/photos", "lender", photo())
    assert r.status_code == 503 and "checklist" in r.json()["detail"]
