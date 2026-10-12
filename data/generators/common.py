"""Shared constants and helpers for the synthetic-data generator.

Everything produced with these helpers is SYNTHETIC and deterministic: the same seed and the same
reference date give byte-identical files.

Plain-language note: a deterministic uuid ("uuid5") is an identifier computed from a fixed
namespace plus a name, so the same user always gets the same id on every run, on every machine.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
DERIVED = ROOT / "data" / "derived"
INTERIM = ROOT / "data" / "interim"

GENERATOR_VERSION = "1.0.0"
BASE_SEED = 20261001
# "Today" for generated data. Everything is dated before this; requests under test sit just before it.
REF_DATE = datetime(2026, 10, 1, 8, 0, 0, tzinfo=UTC)
# Earliest date any activity can have (the oldest accounts), so evidence can be 18 months old.
WINDOW_START = datetime(2025, 4, 1, 0, 0, 0, tzinfo=UTC)

# Fixed namespace: never change it, or every id in committed data changes.
NAMESPACE = uuid.UUID("5d1c7a0e-3b52-4f6e-9a47-0d4f2c9b8e11")

SYSTEM_AUTH = "system:borrowing-service"  # same string the lifecycle service uses

TRANSITIONS_CSV = BACKEND / "app" / "domain" / "lifecycle" / "transition_leaves.csv"
ENGINE_JSON = BACKEND / "config" / "engine.json"
PUBLIC_STATS_JSON = DERIVED / "public_graph_stats.json"


def uid(kind: str, key: str) -> str:
    """Deterministic uuid (as text) for a named thing, e.g. uid('user', 'U007')."""
    return str(uuid.uuid5(NAMESPACE, f"{kind}:{key}"))


def rng_for(seed: int, name: str) -> random.Random:
    """An independent random stream per purpose, so adding a feature does not shift other data."""
    return random.Random(f"{seed}:{name}")


# ----------------------------------------------------------------------------- time


def ts(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S+00:00").replace(tzinfo=UTC)


def days(n: float) -> timedelta:
    return timedelta(days=n)


def hours(n: float) -> timedelta:
    return timedelta(hours=n)


def local_hour_to_utc(day: datetime, hour: float) -> datetime:
    """A Pakistan-local clock time (UTC+5) on the given date, as UTC."""
    base = day.replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(hours=hour - 5)


def range_literal(start: datetime, end: datetime) -> str:
    return f"[{ts(start)},{ts(end)})"


# ----------------------------------------------------------------------------- config


@lru_cache(maxsize=1)
def engine_config() -> dict[str, Any]:
    return json.loads(ENGINE_JSON.read_text(encoding="utf-8"))


def value_band(value_pkr: float, cfg: dict[str, Any] | None = None) -> str:
    cfg = cfg or engine_config()
    b = cfg["decision_policy_alg4"]["value_bands_pkr"]
    if value_pkr <= b["low_value_max"]:
        return "LOW"
    if value_pkr <= b["medium_value_max"]:
        return "MEDIUM"
    return "HIGH"


def load_transitions() -> dict[tuple[str, str, str], set[str]]:
    """(from_state, event_type, to_state) -> allowed roles, from the backend's own table."""
    out: dict[tuple[str, str, str], set[str]] = {}
    with TRANSITIONS_CSV.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(r["from_state"], r["event_type"], r["to_state"])] = set(
                r["allowed_roles"].split("|")
            )
    return out


def iteration_of_transitions() -> dict[tuple[str, str, str], int]:
    out: dict[tuple[str, str, str], int] = {}
    with TRANSITIONS_CSV.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(r["from_state"], r["event_type"], r["to_state"])] = int(r["iteration"])
    return out


def auth_role(auth: str) -> str:
    """Mirror of the schema function auth_role()."""
    if auth == "party:borrower":
        return "BORROWER"
    if auth == "party:lender":
        return "LENDER"
    if auth.startswith("role:moderator@"):
        return "MODERATOR"
    if auth == "role:admin":
        return "ADMIN"
    if auth.startswith("system:"):
        return "SYSTEM"
    raise ValueError(f"bad authorisation {auth!r}")


# ----------------------------------------------------------------------------- public stats


def load_public_stats() -> dict[str, Any]:
    return json.loads(PUBLIC_STATS_JSON.read_text(encoding="utf-8"))


def draw_from_quantiles(
    rng: random.Random, table: dict[str, float], floor_ratio: float = 0.5, ceil_ratio: float = 1.5
) -> float:
    """Draw one value from a quantile table by linear interpolation of the inverse CDF.

    `table` maps '0.05' ... '0.99' to values. Below the first and above the last point the value
    is extended by `floor_ratio` / `ceil_ratio` of the end value, so tails are not cut off.
    """
    pts = sorted((float(q), v) for q, v in table.items())
    qs = [0.0] + [q for q, _ in pts] + [1.0]
    vs = [pts[0][1] * floor_ratio] + [v for _, v in pts] + [pts[-1][1] * ceil_ratio]
    u = rng.random()
    for i in range(1, len(qs)):
        if u <= qs[i]:
            span = qs[i] - qs[i - 1]
            frac = (u - qs[i - 1]) / span if span else 0.0
            return vs[i - 1] + frac * (vs[i] - vs[i - 1])
    return vs[-1]


# ----------------------------------------------------------------------------- csv output


def _cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (dict, list)):
        return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if isinstance(v, datetime):
        return ts(v)
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))
    return str(v)


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> int:
    """Write rows with a header. NULL is the empty string (PostgreSQL COPY ... CSV default)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(fields)
        for r in rows:
            extra = set(r) - set(fields)
            if extra:
                raise KeyError(f"{path.name}: unexpected columns {sorted(extra)}")
            w.writerow([_cell(r.get(c)) for c in fields])
            n += 1
    return n


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
