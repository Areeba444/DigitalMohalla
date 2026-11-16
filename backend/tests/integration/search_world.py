"""Synthetic community for the search tests (suites 29 and 30): a searcher, two lenders, a lender
who blocked the searcher, and items in another community, so eligibility can be checked exactly.
Shared by test_search.py and test_search_log.py through conftest.py (one instance per session)."""

from dataclasses import dataclass
from uuid import UUID

import pytest
from sqlalchemy import Engine, text

from app.domain.accounts.auth import hash_password

PASSWORD = "synthetic-test-password"  # noqa: S105 - throwaway value for this test database


@dataclass
class S:
    community: UUID
    other: UUID
    items: dict[str, UUID]


@pytest.fixture(scope="session")
def s(engine: Engine) -> S:
    with engine.begin() as c:

        def one(sql: str, **kw: object) -> UUID:
            return c.execute(text(sql), kw).scalar_one()

        community = one(
            "INSERT INTO community (name, join_code) VALUES ('Synthetic Search', 'SYN-SRCH') RETURNING id"
        )
        other = one(
            "INSERT INTO community (name, join_code) VALUES ('Synthetic Elsewhere', 'SYN-ELSE') RETURNING id"
        )
        tools = one("INSERT INTO category (name) VALUES ('Search tools') RETURNING id")
        kitchen = one("INSERT INTO category (name) VALUES ('Search kitchen') RETURNING id")

        def person(email: str, communities: list[UUID]) -> UUID:
            uid = one(
                "INSERT INTO app_user (display_name, email, password_hash, verification_level, status, "
                "is_synthetic) VALUES (:n, :e, :h, 'COMMUNITY_VERIFIED', 'ACTIVE', true) RETURNING id",
                n=email.split("@")[0],
                e=email,
                h=hash_password(PASSWORD),
            )
            for cid in communities:
                c.execute(
                    text(
                        "INSERT INTO membership (user_id, community_id, status, decided_at) VALUES (:u, :c, 'APPROVED', now())"
                    ),
                    {"u": uid, "c": cid},
                )
            return uid

        admin = one(
            "INSERT INTO app_user (display_name, email, platform_role, verification_level, status, "
            "is_synthetic) VALUES ('Search admin', 'sadmin@example.test', 'ADMIN', "
            "'COMMUNITY_VERIFIED', 'ACTIVE', true) RETURNING id"
        )
        searcher = person("searcher@example.test", [community])
        c.execute(
            text(
                "INSERT INTO locality_verification (membership_id, method, outcome, approved_by, "
                "valid_until) SELECT m.id, 'MODERATOR_APPROVAL', 'VERIFIED', :a, "
                "now() + interval '90 days' FROM membership m WHERE m.user_id = :s"
            ),
            {"s": searcher, "a": admin},
        )
        l1 = person("slender1@example.test", [community])
        l2 = person("slender2@example.test", [community, other])
        blocker = person("sblocker@example.test", [community])
        c.execute(
            text("INSERT INTO user_block (blocker_id, blocked_id) VALUES (:b, :s)"),
            {"b": blocker, "s": searcher},
        )

        def item(
            key: str,
            owner: UUID,
            cid: UUID,
            cat: UUID,
            title: str,
            desc: str,
            cond: str,
            deposit: int,
            status: str = "PUBLISHED",
            terms: str | None = None,
        ) -> tuple[str, UUID]:
            return key, one(
                "INSERT INTO item (owner_id, community_id, category_id, title, description, condition, "
                "value_band, deposit_amount, status, search_terms, created_at) VALUES (:o, :c, :k, :t, "
                ":d, CAST(:cond AS item_condition), 'MEDIUM', :dep, CAST(:st AS item_status), :terms, "
                "clock_timestamp()) RETURNING id",
                o=owner,
                c=cid,
                k=cat,
                t=title,
                d=desc,
                cond=cond,
                dep=deposit,
                st=status,
                terms=terms,
            )

        items = dict(
            [
                item(
                    "drill",
                    l1,
                    community,
                    tools,
                    "Bosch hammer drill",
                    "Corded drill for brick walls.",
                    "GOOD",
                    1000,
                ),
                item(
                    "ladder",
                    l1,
                    community,
                    tools,
                    "Aluminium step ladder",
                    "Folds flat, 3 m.",
                    "FAIR",
                    0,
                    terms="seedhi",
                ),
                item(
                    "mixer",
                    l2,
                    community,
                    kitchen,
                    "Hand mixer",
                    "Two speeds, for cakes and dough.",
                    "NEW",
                    500,
                ),
                item(
                    "screw",
                    l2,
                    community,
                    tools,
                    "Screwdriver set",
                    "Twelve bits, also for a drill.",
                    "WORN",
                    200,
                ),
                item(
                    "elsewhere",
                    l2,
                    other,
                    tools,
                    "Cordless drill",
                    "Other community only.",
                    "GOOD",
                    0,
                ),
                item(
                    "draft",
                    l1,
                    community,
                    tools,
                    "Draft drill",
                    "Not published.",
                    "GOOD",
                    0,
                    status="DRAFT",
                ),
                item(
                    "mine", searcher, community, tools, "My own drill", "Searcher's own.", "GOOD", 0
                ),
                item(
                    "blocked",
                    blocker,
                    community,
                    tools,
                    "Blocker's drill",
                    "From a lender who blocked the searcher.",
                    "GOOD",
                    0,
                ),
            ]
        )
    return S(community, other, items)
