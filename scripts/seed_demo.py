"""Seed a development database with SYNTHETIC users, one community and a few items.

Every user is flagged `is_synthetic` and has an `@example.test` address. Run from the repo root after
`alembic upgrade head`:

    cd backend && uv run python ../scripts/seed_demo.py            # uses DATABASE_URL from .env
    cd backend && uv run python ../scripts/seed_demo.py --reset    # wipes schema dm first, re-migrates

The demo password below is a throwaway value for local demos only (never use it anywhere real).
Locality is recorded as a moderator-approved coarse result (A11); no coordinates exist anywhere.
"""

import argparse
import sys
from pathlib import Path

from alembic.config import Config
from sqlalchemy import Connection, text

from alembic import command

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from app.domain.accounts.auth import hash_password  # noqa: E402
from app.infra.db.session import make_engine  # noqa: E402

DEMO_PASSWORD = "demo-password-synthetic"  # noqa: S105 - local demo value
USERS = [
    ("Ayesha (lender)", "lender@example.test", "MEMBER", "MEMBER"),
    ("Bilal (borrower)", "borrower@example.test", "MEMBER", "MEMBER"),
    ("Chand (borrower)", "borrower2@example.test", "MEMBER", "MEMBER"),
    ("Dua (moderator)", "moderator@example.test", "MEMBER", "MODERATOR"),
    ("Admin", "admin@example.test", "ADMIN", "MEMBER"),
]
ITEMS = [("Power drill", "LOW", 0), ("Folding ladder", "MEDIUM", 500), ("Camping tent", "LOW", 0)]


def seed(conn: Connection) -> None:
    password_hash = hash_password(DEMO_PASSWORD)
    community = conn.execute(
        text(
            "INSERT INTO community (name, join_code) VALUES ('Synthetic Block C', 'DEMO1') RETURNING id"
        )
    ).scalar_one()
    ids: dict[str, object] = {}
    for name, email, platform_role, _ in USERS:
        ids[email] = conn.execute(
            text(
                "INSERT INTO app_user (display_name, email, password_hash, verification_level, "
                "platform_role, status, is_synthetic) VALUES (:n, :e, :h, 'COMMUNITY_VERIFIED', "
                "CAST(:r AS platform_role), 'ACTIVE', true) RETURNING id"
            ),
            {"n": name, "e": email, "h": password_hash, "r": platform_role},
        ).scalar_one()
    admin = ids["admin@example.test"]
    for _, email, _, community_role in USERS:
        if email == "admin@example.test":
            continue
        membership = conn.execute(
            text(
                "INSERT INTO membership (user_id, community_id, role, status, decided_at) "
                "VALUES (:u, :c, CAST(:r AS membership_role), 'APPROVED', now()) RETURNING id"
            ),
            {"u": ids[email], "c": community, "r": community_role},
        ).scalar_one()
        conn.execute(
            text(
                "INSERT INTO locality_verification (membership_id, method, outcome, approved_by, "
                "valid_until) VALUES (:m, 'MODERATOR_APPROVAL', 'VERIFIED', :a, "
                "now() + interval '180 days')"
            ),
            {"m": membership, "a": admin},
        )
    category = conn.execute(
        text("INSERT INTO category (name) VALUES ('Tools') RETURNING id")
    ).scalar_one()
    for title, band, deposit in ITEMS:
        conn.execute(
            text(
                "INSERT INTO item (owner_id, community_id, category_id, title, value_band, "
                "deposit_amount, status) VALUES (:o, :c, :cat, :t, CAST(:b AS value_band), :d, "
                "'PUBLISHED')"
            ),
            {
                "o": ids["lender@example.test"],
                "c": community,
                "cat": category,
                "t": title,
                "b": band,
                "d": deposit,
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reset", action="store_true", help="drop schema dm and re-migrate first")
    args = parser.parse_args()
    engine = make_engine()
    if args.reset:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS dm CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS public.alembic_version"))
        config = Config(str(BACKEND / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND / "alembic"))
        with engine.begin() as conn:
            config.attributes["connection"] = conn
            command.upgrade(config, "head")
    with engine.begin() as conn:
        seed(conn)
    print(
        f"Seeded {len(USERS)} synthetic users and {len(ITEMS)} items. Password: see DEMO_PASSWORD."
    )


if __name__ == "__main__":
    main()
