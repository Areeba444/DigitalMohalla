"""Load a generated synthetic dataset (data/derived/<tier>) into PostgreSQL and verify it.

    cd backend
    uv run python ../scripts/load_dataset.py ../data/derived/standard --reset

By default it only touches a database whose name ends in `_test`, and `--reset` drops and rebuilds
schema `dm` from the Alembic migration first. The target URL is $TEST_DATABASE_URL or --url.

Why triggers are switched off while loading (plain language): the schema stamps every lifecycle event
with the current clock time and rejects a request whose dates are in the past, so history cannot be
replayed through the normal rules. This loader therefore turns off the schema's USER triggers for the
load (foreign keys, CHECK and exclusion constraints stay ON), computes the per-stream hash chain with
the schema's own `event_hash()` function, switches the triggers back on, and then verifies:
  * row counts equal the CSV files;
  * the hash chain of every stream passes the schema's `verify_event_chain()`;
  * the schema's `replay_state()` and the backend's own Python replay agree with the stored state;
  * the stored projections (state, version, last event time) equal the last event;
  * views work; no closing event is missing its outcomes.
All data is SYNTHETIC. Exit code 0 means everything loaded and verified.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from alembic.config import Config  # noqa: E402
from sqlalchemy import Engine, make_url, text  # noqa: E402

from alembic import command  # noqa: E402
from app.domain.lifecycle.aggregate import BorrowingTransaction  # noqa: E402
from app.domain.lifecycle.transition_table import TransitionTable  # noqa: E402
from app.infra.db.session import make_engine  # noqa: E402
from app.infra.eventstore.store import load_stream  # noqa: E402

# parents before children (foreign keys are enforced during the load)
LOAD_ORDER = [
    "app_user",
    "community",
    "membership",
    "locality_verification",
    "category",
    "item",
    "borrowing_transaction",
    "lifecycle_event",
    "booking",
    "condition_report",
    "escalation_case",
    "moderator_decision",
    "outcome",
    "trust_edge",
    "review",
]
HASH_CHAIN_SQL = """
DO $$
DECLARE s uuid; e lifecycle_event; prev bytea; h bytea;
BEGIN
  FOR s IN SELECT DISTINCT stream_id FROM lifecycle_event LOOP
    prev := NULL;
    FOR e IN SELECT * FROM lifecycle_event WHERE stream_id = s ORDER BY stream_seq LOOP
      h := event_hash(prev, e);
      UPDATE lifecycle_event SET prev_hash = prev, row_hash = h WHERE event_id = e.event_id;
      prev := h;
    END LOOP;
  END LOOP;
END $$
"""


def reset_schema(engine: Engine) -> None:
    """Drop schema dm and rebuild it from the Alembic migration (same steps as the integration tests)."""
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA IF EXISTS dm CASCADE"))
        c.execute(text("DROP TABLE IF EXISTS public.alembic_version"))
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    with engine.begin() as c:
        cfg.attributes["connection"] = c
        command.upgrade(cfg, "head")


def csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def load(engine: Engine, folder: Path) -> dict[str, int]:
    """Copy every CSV in one transaction, with the schema's user triggers off."""
    counts: dict[str, int] = {}
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute("SET search_path = dm, public")
        cur.execute(
            "SELECT DISTINCT format('%I.%I', n.nspname, c.relname) FROM pg_trigger g "
            "JOIN pg_class c ON c.oid = g.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE NOT g.tgisinternal AND n.nspname = 'dm' ORDER BY 1"
        )
        guarded = [r[0] for r in cur.fetchall()]
        for t in guarded:
            cur.execute(f"ALTER TABLE {t} DISABLE TRIGGER USER")
        for table in LOAD_ORDER:
            path = folder / f"{table}.csv"
            with path.open(newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                cols = next(reader)
                extra = ["prev_hash", "row_hash"] if table == "lifecycle_event" else []
                n = 0
                with cur.copy(f"COPY {table} ({', '.join(cols + extra)}) FROM STDIN") as cp:
                    for row in reader:
                        vals: list[str | None] = [None if v == "" else v for v in row]
                        if extra:  # placeholder, replaced by the real chain below
                            vals += [None, "\\x00"]
                        cp.write_row(vals)
                        n += 1
            counts[table] = n
        cur.execute(HASH_CHAIN_SQL)
        for table, col in (("lifecycle_event", "event_id"), ("category", "id")):
            cur.execute(
                f"SELECT setval(pg_get_serial_sequence('dm.{table}', '{col}'), "
                f"(SELECT max({col}) FROM {table}))"
            )
        for t in guarded:
            cur.execute(f"ALTER TABLE {t} ENABLE TRIGGER USER")
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
    return counts


def verify(engine: Engine, folder: Path, counts: dict[str, int] | None = None) -> list[str]:
    """Return a list of problems; an empty list means the loaded data is consistent."""
    problems: list[str] = []
    table = TransitionTable.load()
    with engine.connect() as c:
        for t in LOAD_ORDER:
            n = c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one()
            want = csv_rows(folder / f"{t}.csv")
            if n != want:
                problems.append(f"{t}: {n} rows in the database, {want} in the CSV")
        bad_chain = c.execute(
            text(
                "SELECT count(*) FROM (SELECT DISTINCT stream_id FROM lifecycle_event) s, "
                "LATERAL verify_event_chain(s.stream_id)"
            )
        ).scalar_one()
        if bad_chain:
            problems.append(f"{bad_chain} hash-chain problems reported by verify_event_chain()")
        n = c.execute(
            text(
                "SELECT count(*) FROM borrowing_transaction "
                "WHERE replay_state(id) IS DISTINCT FROM current_state"
            )
        ).scalar_one()
        if n:
            problems.append(f"{n} transactions whose replay_state() differs from current_state")
        n = c.execute(
            text(
                "SELECT count(*) FROM borrowing_transaction t JOIN LATERAL ("
                "  SELECT * FROM lifecycle_event e WHERE e.stream_id = t.id "
                "  ORDER BY e.stream_seq DESC LIMIT 1) l ON true "
                "WHERE t.current_state <> l.new_state OR t.stream_version <> l.stream_seq "
                "   OR t.last_event_at <> l.occurred_at"
            )
        ).scalar_one()
        if n:
            problems.append(f"{n} transactions whose stored projection differs from the last event")
        for view, why in (("v_pending_outcomes", "closing events without outcomes"),):
            n = c.execute(text(f"SELECT count(*) FROM {view}")).scalar_one()
            if n:
                problems.append(f"{n} {why}")
        held = c.execute(text("SELECT count(*) FROM booking WHERE status = 'HELD'")).scalar_one()
        cal = c.execute(text("SELECT count(*) FROM v_item_calendar")).scalar_one()
        if held != cal:
            problems.append(f"v_item_calendar shows {cal} bookings, expected {held}")
        live = c.execute(
            text(
                "SELECT count(*) FROM escalation_case WHERE status IN ('OPEN','AWAITING_INFORMATION')"
            )
        ).scalar_one()
        queue = c.execute(text("SELECT count(*) FROM v_moderation_queue")).scalar_one()
        if live != queue:
            problems.append(f"v_moderation_queue shows {queue} cases, expected {live}")
        # the backend's own pure-Python replay of every stream must agree with what is stored
        for sid, state, version in c.execute(
            text("SELECT id, current_state::text, stream_version FROM borrowing_transaction")
        ).all():
            try:
                agg = BorrowingTransaction.replay(load_stream(c, sid), table)
            except Exception as exc:  # ReplayError and anything unexpected
                problems.append(f"Python replay failed for {sid}: {exc}")
                continue
            if (agg.state, agg.version) != (state, version):
                problems.append(
                    f"Python replay of {sid} gives {agg.state}/{agg.version}, stored {state}/{version}"
                )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("folder", type=Path, help="e.g. ../data/derived/standard")
    ap.add_argument(
        "--url",
        default=os.environ.get("TEST_DATABASE_URL"),
        help="database URL (default $TEST_DATABASE_URL)",
    )
    ap.add_argument(
        "--reset", action="store_true", help="drop and rebuild schema dm first (wipes the database)"
    )
    ap.add_argument(
        "--allow-non-test",
        action="store_true",
        help="allow a database whose name does not end in _test",
    )
    ap.add_argument(
        "--verify-only", action="store_true", help="do not load; only verify what is there"
    )
    a = ap.parse_args()
    if not a.url:
        print("set TEST_DATABASE_URL or pass --url", file=sys.stderr)
        return 2
    name = make_url(a.url).database or ""
    if not name.endswith("_test") and not a.allow_non_test:
        print(
            f"refusing to touch database {name!r}: its name does not end in _test (use --allow-non-test)",
            file=sys.stderr,
        )
        return 2
    engine = make_engine(a.url)
    if not a.verify_only:
        if a.reset:
            reset_schema(engine)
        counts = load(engine, a.folder)
        print("loaded:", ", ".join(f"{k} {v}" for k, v in counts.items()))
    problems = verify(engine, a.folder)
    for p in problems:
        print("PROBLEM:", p)
    print("verified" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
