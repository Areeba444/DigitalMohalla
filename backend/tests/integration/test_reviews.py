"""Reviews (suite 23; plan item A3; UC-D1, FR-T-09, FR-B-15; sequence (f)).

Only parties to a completed loan, once each, inside the review window; editable for the edit window;
retaliation and near-identical text flagged at submission and never shown to the reviewer.
TC-230 to TC-236, input / expected / actual in each docstring. Synthetic loans and texts.
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.config.engine_config import load_engine_config
from app.domain.accounts.auth import hash_password
from app.domain.assurance.detection.manipulation import ManipulationParams
from app.domain.lifecycle.errors import InvalidTransition
from app.domain.reviews.service import ReviewConfig, ReviewService
from app.infra.db.reviews import PostgresReviewStore
from tests.integration.conftest import World
from tests.integration.test_api import TEST_PASSWORD, client, dates, login  # noqa: F401 - shared fixture

LENDER_RATINGS = {
    "condition_accuracy": 5,
    "fair_terms": 5,
    "responsiveness": 4,
    "dispute_fairness": 5,
}
BORROWER_RATINGS = {"punctuality": 5, "care_for_item": 5, "communication": 5, "follow_terms": 5}


def completed(api: TestClient, world: World, item: int, start: int, who: str = "borrower") -> str:
    b, lender = login(api, f"{who}@example.test"), login(api, "lender@example.test")
    txn = api.post(
        "/api/v1/requests", json={"item_id": str(world.items[item]), **dates(start, 1)}, headers=b
    ).json()["transaction_id"]
    api.post(f"/api/v1/requests/{txn}/accept", headers=lender)
    api.post(
        f"/api/v1/transactions/{txn}/handover/checklist", json={"checklist": {}}, headers=lender
    )
    api.post(f"/api/v1/transactions/{txn}/handover/confirm", json={}, headers=b)
    api.post(f"/api/v1/transactions/{txn}/return", headers=b)
    api.post(f"/api/v1/transactions/{txn}/return/confirm", json={}, headers=lender)
    done = api.post(f"/api/v1/transactions/{txn}/return/confirm", json={}, headers=b)
    assert done.json()["state"] == "COMPLETED", done.text
    return str(txn)


def review(api: TestClient, txn: str, who: str, ratings: dict, comment: str | None = None):  # type: ignore[no-untyped-def]
    return api.post(
        f"/api/v1/transactions/{txn}/review",
        json={"ratings": ratings, "comment": comment},
        headers=login(api, f"{who}@example.test"),
    )


def flags(engine: Engine, txn: str, reviewer: object) -> tuple[bool, bool]:
    with engine.connect() as c:
        r = c.execute(
            text(
                "SELECT retaliation_flag, similarity_flag FROM review "
                "WHERE transaction_id = :t AND reviewer_id = :r"
            ),
            {"t": txn, "r": reviewer},
        ).one()
    return bool(r[0]), bool(r[1])


def test_tc230_completion_unlocks_one_review_per_party(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: a review on an ASSESSED request; by a stranger; then the borrower reviews the lender
    of a completed loan. Expected: 409; 403; 201, the lender told, and the "review" action shown
    before and gone after (FR-B-15); no flag in the response."""
    pending = client.post(
        "/api/v1/requests",
        json={"item_id": str(world.items[19]), **dates(220, 1)},
        headers=login(client, "borrower@example.test"),
    ).json()["transaction_id"]
    assert review(client, pending, "borrower", LENDER_RATINGS).status_code == 409
    client.post(
        f"/api/v1/requests/{pending}/cancel", headers=login(client, "borrower@example.test")
    )

    txn = completed(client, world, item=19, start=222)
    assert review(client, txn, "borrower2", LENDER_RATINGS).status_code == 403
    b = login(client, "borrower@example.test")
    assert "review" in client.get(f"/api/v1/requests/{txn}", headers=b).json()["available_actions"]
    ok = review(client, txn, "borrower", LENDER_RATINGS, "Synthetic: drill was as described.")
    assert ok.status_code == 201, ok.text
    body = ok.json()
    assert body["reviewee_role"] == "LENDER" and "flag" not in str(body)
    assert (
        "review" not in client.get(f"/api/v1/requests/{txn}", headers=b).json()["available_actions"]
    )
    with engine.connect() as c:
        told = c.execute(
            text(
                "SELECT count(*) FROM notification WHERE user_id = :u AND type = 'review_received' "
                "AND payload->>'transaction_id' = :t"
            ),
            {"u": world.lender, "t": txn},
        ).scalar_one()
    assert told == 1


@pytest.mark.parametrize(
    ("ratings", "start"),
    [
        (BORROWER_RATINGS, 232),  # the borrower's dimensions, for a lender
        ({**LENDER_RATINGS, "fair_terms": 6}, 235),
        ({**LENDER_RATINGS, "fair_terms": 0}, 238),
        ({k: v for k, v in LENDER_RATINGS.items() if k != "fair_terms"}, 241),
    ],
)
def test_tc231_ratings_must_fit_the_role(
    client: TestClient,  # noqa: F811
    world: World,
    ratings: dict,
    start: int,
) -> None:
    """Expected 422: wrong dimensions, out of range, missing one."""
    txn = completed(client, world, item=0, start=start)
    assert review(client, txn, "borrower", ratings).status_code == 422


def test_tc232_edit_inside_the_window_keeps_one_review(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: submit, then submit again with other ratings. Expected: still one review, now with the
    new ratings (an edit inside the 24 h window)."""
    txn = completed(client, world, item=1, start=250)
    review(client, txn, "borrower", LENDER_RATINGS, "first")
    again = review(client, txn, "borrower", {**LENDER_RATINGS, "responsiveness": 2}, "second")
    assert again.status_code == 201
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT ratings->>'responsiveness', comment FROM review WHERE transaction_id = :t"
            ),
            {"t": txn},
        ).all()
    assert [tuple(r) for r in rows] == [("2", "second")]


def test_tc233_review_and_edit_windows_close(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: the lender reviews 15 days after completion; the borrower edits 25 hours after their
    review. Expected: both refused (review window 14 d, edit window 24 h)."""
    txn = completed(client, world, item=2, start=255)
    review(client, txn, "borrower", LENDER_RATINGS)
    config = load_engine_config()

    def svc(now: datetime, conn) -> ReviewService:  # type: ignore[no-untyped-def]
        return ReviewService(
            PostgresReviewStore(conn),
            ReviewConfig.from_section(config.section("reviews_d1")),
            ManipulationParams.from_config(config.section("manipulation_detection_alg3")),
            now=now,
        )

    with engine.connect() as conn:
        late = datetime.now(UTC) + timedelta(days=15)
        with pytest.raises(InvalidTransition, match="window"):
            svc(late, conn).submit(world.lender, txn, BORROWER_RATINGS, None)  # type: ignore[arg-type]
        later = datetime.now(UTC) + timedelta(hours=25)
        with pytest.raises(InvalidTransition, match="no longer"):
            svc(later, conn).submit(world.borrower, txn, LENDER_RATINGS, "x")  # type: ignore[arg-type]
        conn.rollback()


def fresh_pair(engine: Engine, world: World, tag: str) -> tuple[str, str, str]:
    """Two new synthetic members of the test community with no history, and one item of the
    second: (borrower email, lender email, item id). Keeps a test free of other tests' disputes."""
    with engine.begin() as c:
        ids = []
        for role in ("b", "l"):
            uid = c.execute(
                text(
                    "INSERT INTO app_user (display_name, email, password_hash, verification_level, "
                    "status, is_synthetic) VALUES (:n, :e, :h, 'COMMUNITY_VERIFIED', 'ACTIVE', true) "
                    "RETURNING id"
                ),
                {
                    "n": f"Fresh {role}{tag}",
                    "e": f"fresh-{role}{tag}@example.test",
                    "h": hash_password(TEST_PASSWORD),
                },
            ).scalar_one()
            m = c.execute(
                text(
                    "INSERT INTO membership (user_id, community_id, status, decided_at) "
                    "VALUES (:u, :c, 'APPROVED', now()) RETURNING id"
                ),
                {"u": uid, "c": world.community},
            ).scalar_one()
            c.execute(
                text(
                    "INSERT INTO locality_verification (membership_id, method, outcome, approved_by, "
                    "valid_until) VALUES (:m, 'MODERATOR_APPROVAL', 'VERIFIED', :a, now() + interval '90 days')"
                ),
                {"m": m, "a": world.admin},
            )
            ids.append(uid)
        item = c.execute(
            text(
                "INSERT INTO item (owner_id, community_id, category_id, title, description, condition, "
                "value_band, status) SELECT :o, :c, id, 'Synthetic fresh item', 'Synthetic.', 'GOOD', "
                "'LOW', 'PUBLISHED' FROM category WHERE name = 'Tools' RETURNING id"
            ),
            {"o": ids[1], "c": world.community},
        ).scalar_one()
    return f"fresh-b{tag}@example.test", f"fresh-l{tag}@example.test", str(item)


def test_tc234_low_review_right_after_a_complaint_is_flagged_as_retaliation(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: two members with no history; on a loan whose return both confirmed, the lender rates
    the borrower 1, then the borrower rates the lender 1. Expected: the borrower's review has
    retaliation_flag (D19); the lender's, made first, does not."""
    b_email, l_email, item = fresh_pair(engine, world, "234")
    b, lender = login(client, b_email), login(client, l_email)
    txn = client.post(
        "/api/v1/requests", json={"item_id": item, **dates(260, 1)}, headers=b
    ).json()["transaction_id"]
    client.post(f"/api/v1/requests/{txn}/accept", headers=lender)
    client.post(
        f"/api/v1/transactions/{txn}/handover/checklist", json={"checklist": {}}, headers=lender
    )
    client.post(f"/api/v1/transactions/{txn}/handover/confirm", json={}, headers=b)
    client.post(f"/api/v1/transactions/{txn}/return", headers=b)
    client.post(f"/api/v1/transactions/{txn}/return/confirm", json={}, headers=lender)
    assert (
        client.post(f"/api/v1/transactions/{txn}/return/confirm", json={}, headers=b).json()[
            "state"
        ]
        == "COMPLETED"
    )
    low_b = {**BORROWER_RATINGS, "punctuality": 1}
    low_l = {**LENDER_RATINGS, "fair_terms": 1}
    client.post(
        f"/api/v1/transactions/{txn}/review",
        json={"ratings": low_b, "comment": "late"},
        headers=lender,
    )
    client.post(
        f"/api/v1/transactions/{txn}/review",
        json={"ratings": low_l, "comment": "unfair"},
        headers=b,
    )
    with engine.connect() as c:
        rows = dict(
            c.execute(
                text(
                    "SELECT r.reviewee_role::text, r.retaliation_flag FROM review r "
                    "WHERE r.transaction_id = :t"
                ),
                {"t": txn},
            ).all()
        )
    assert rows == {"LENDER": True, "BORROWER": False}  # the borrower's review of the lender


def test_tc235_near_identical_text_is_flagged(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: Borrower2 reviews the lender; then Borrower posts almost the same text about the same
    lender. Expected: the second review has similarity_flag (S4 measure >= s4_min_cosine)."""
    text_ = "Synthetic: very good lender, item was clean and on time, highly recommended to all."
    first = completed(client, world, item=4, start=265, who="borrower2")
    review(client, first, "borrower2", LENDER_RATINGS, text_)
    second = completed(client, world, item=5, start=268)
    review(client, second, "borrower", LENDER_RATINGS, text_.replace("all", "everyone"))
    assert flags(engine, second, world.borrower) == (False, True)
    third = completed(client, world, item=6, start=271)
    review(client, third, "borrower", LENDER_RATINGS, "Synthetic: the ladder had a loose step.")
    assert flags(engine, third, world.borrower)[1] is False
