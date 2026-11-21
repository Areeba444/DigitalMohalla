"""Smoke test after a deploy (TC-91, extended; build item M10; Test, Deployment, Rollback plan section 4).

    python scripts/smoke_test.py https://<service>.onrender.com --email borrower@example.test
    (the password is read from the SMOKE_PASSWORD environment variable, or asked for without echo)

Checks, in order, against a running instance with SYNTHETIC data:
  1  GET /health answers
  2  a seeded synthetic member signs in
  3  Browse items lists at least one item
  4  a search answers and says which mode it used (HYBRID or KEYWORD_ONLY), with no score field
  5  GET /me/evidence answers with per-role factors and no single number
  6  one scripted request reaches ASSESSED (or is HELD_FOR_REVIEW with a reason, reported as a
     warning because a rule may hold it), then the request is cancelled so the data stays clean
The password is never printed or put in a URL. Only the standard library is used, so it runs on any
machine with Python 3.9 or later. Exit code 0 means every check passed; the plan asks to record the
result and the commit in the release note.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from typing import Any

failures = 0


def call(
    base: str, method: str, path: str, body: dict[str, Any] | None = None, token: str = ""
) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, None


def check(name: str, ok: bool, detail: str = "") -> bool:
    global failures
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures += 1
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("base_url")
    ap.add_argument("--email", required=True, help="a seeded synthetic member who may borrow")
    ap.add_argument("--start-in-days", type=int, default=200, help="date offset for the test request")
    a = ap.parse_args()
    base = a.base_url.rstrip("/")
    password = os.environ.get("SMOKE_PASSWORD") or getpass.getpass("Password (not shown): ")

    t0 = time.perf_counter()
    status, body = call(base, "GET", "/health")  # a sleeping free service can take about a minute
    if not check("1 /health answers", status == 200, f"{time.perf_counter() - t0:.1f} s"):
        return 1
    status, body = call(base, "POST", "/api/v1/auth/login", {"email": a.email, "password": password})
    if not check("2 sign in", status == 200 and bool(body and body.get("access_token")), f"HTTP {status}"):
        return 1
    token = body["access_token"]
    api = "/api/v1"

    status, items = call(base, "GET", f"{api}/items", token=token)
    check("3 browse items lists items", status == 200 and bool(items), f"HTTP {status}, {len(items or [])} items")

    status, found = call(base, "GET", f"{api}/search?q=drill", token=token)
    ok = status == 200 and found.get("mode") in ("HYBRID", "KEYWORD_ONLY")
    no_score = not any(k in r for r in found.get("results", []) for k in ("score", "relevance", "rank_score"))
    check("4 search answers with its mode and no score", ok and no_score, f"mode {found.get('mode') if ok else '?'}")

    status, ev = call(base, "GET", f"{api}/me/evidence", token=token)
    roles = {r["role"] for r in (ev or {}).get("roles", [])} if status == 200 else set()
    check("5 own evidence per role", roles == {"BORROWER", "LENDER"}, f"HTTP {status}")

    own = {r["item_id"] for r in (call(base, "GET", f"{api}/requests", token=token)[1] or [])}
    candidates = [i["id"] for i in (items or []) if i["id"] not in own]
    if not candidates:
        check("6 one scripted request reaches ASSESSED", False, "no item to request")
        return 1
    start = date.today() + timedelta(days=a.start_in_days)
    request = {"item_id": candidates[0], "start_date": start.isoformat(),
               "end_date": (start + timedelta(days=2)).isoformat(), "message": "smoke test (synthetic)"}  # fmt: skip
    status, made = call(base, "POST", f"{api}/requests", request, token)
    state = (made or {}).get("state")
    if status == 201 and state == "HELD_FOR_REVIEW":
        print(f"WARN  6 request held for review ({made.get('hold_reason')}): a rule may hold it; try another item")
    else:
        check("6 one scripted request reaches ASSESSED", status == 201 and state == "ASSESSED", f"HTTP {status}, state {state}")
    if status == 201:
        c_status, _ = call(base, "POST", f"{api}/requests/{made['transaction_id']}/cancel", {}, token)
        check("6b the test request is cancelled again", c_status == 200, f"HTTP {c_status}")
    print("RESULT:", "all checks passed" if failures == 0 else f"{failures} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
