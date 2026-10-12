"""Integration-test setup: a real PostgreSQL 16 with btree_gist, rebuilt from migration 0001.

Set TEST_DATABASE_URL to a database that may be wiped (schema `dm` is dropped and recreated), e.g.
    postgresql+psycopg://postgres:<password>@localhost:5433/digitalmohalla_test
Without it these tests are skipped. All users, items and communities below are synthetic.
"""

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from alembic.config import Config
from sqlalchemy import Connection, Engine, text

from alembic import command
from app.infra.db.session import make_engine

BACKEND = Path(__file__).resolve().parents[2]


@dataclass
class World:
    community: UUID
    borrower: UUID
    lender: UUID
    borrower2: UUID
    moderator: UUID
    admin: UUID
    items: list[UUID]


def period(start_day: int, end_day: int) -> str:
    """Bounded range literal, days counted from today (in the future for start_day >= 1)."""
    base = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = (base + timedelta(days=start_day)).isoformat()
    end = (base + timedelta(days=end_day)).isoformat()
    return f"[{start},{end})"


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    eng = make_engine(url)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS dm CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS public.alembic_version"))
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    with eng.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def world(engine: Engine) -> World:
    with engine.begin() as c:

        def one(sql: str, **kw: object) -> UUID:
            return c.execute(text(sql), kw).scalar_one()

        def user(name: str, role: str = "MEMBER") -> UUID:
            return one(
                "INSERT INTO app_user (display_name, email, verification_level, platform_role, "
                "status, is_synthetic) "
                "VALUES (:n, :e, 'COMMUNITY_VERIFIED', :r, 'ACTIVE', true) RETURNING id",
                n=name,
                e=f"{name.lower()}@example.test",
                r=role,
            )

        community = one(
            "INSERT INTO community (name, join_code) VALUES ('Synthetic Block C', 'SBC') "
            "RETURNING id"
        )
        borrower, lender, borrower2 = user("Borrower"), user("Lender"), user("Borrower2")
        moderator, admin = user("Moderator"), user("Admin", "ADMIN")
        members = (
            (borrower, "MEMBER"),
            (lender, "MEMBER"),
            (borrower2, "MEMBER"),
            (moderator, "MODERATOR"),
        )
        for uid, role in members:
            m = one(
                "INSERT INTO membership (user_id, community_id, role, status, decided_at) "
                "VALUES (:u, :c, :r, 'APPROVED', now()) RETURNING id",
                u=uid,
                c=community,
                r=role,
            )
            c.execute(
                text(
                    "INSERT INTO locality_verification "
                    "(membership_id, method, outcome, approved_by, valid_until) "
                    "VALUES (:m, 'MODERATOR_APPROVAL', 'VERIFIED', :a, now() + interval '180 days')"
                ),
                {"m": m, "a": admin},
            )
        cat = one("INSERT INTO category (name) VALUES ('Tools') RETURNING id")
        items = [
            one(
                "INSERT INTO item (owner_id, community_id, category_id, title, value_band, "
                "deposit_amount, status) "
                "VALUES (:o, :c, :cat, :t, 'LOW', 0, 'PUBLISHED') RETURNING id",
                o=lender,
                c=community,
                cat=cat,
                t=f"Synthetic item {k}",
            )
            for k in range(20)
        ]
    return World(community, borrower, lender, borrower2, moderator, admin, items)


@pytest.fixture
def conn(engine: Engine) -> Iterator[Connection]:
    """A connection whose work is rolled back after each test, so tests do not see each other."""
    connection = engine.connect()
    outer = connection.begin()
    try:
        yield connection
    finally:
        outer.rollback()
        connection.close()
