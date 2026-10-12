"""A11 locality test cases (Overview section 1): the six required cases plus invitation errors and privacy.

    python test_locality_cases.py   ->  prints the table and writes locality_test_results.md

Input / expected / actual format (FYP-1 Final, Form 5). All coordinates are SYNTHETIC: a made-up
rectangular "community" about 600 m x 450 m; they are test inputs, never stored by the system.
"""
import math
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from locality_rule import Fix, Invitation, InvalidInvitation, evaluate, stored_fields  # noqa: E402

NOW = datetime(2026, 10, 11, 12, 0)
LAT0, LON0 = 30.0000, 70.0000                      # synthetic origin
M_LAT, M_LON = 1 / 111_320, 1 / (111_320 * math.cos(math.radians(LAT0)))
BOUNDARY = [(LAT0, LON0), (LAT0, LON0 + 600 * M_LON), (LAT0 + 450 * M_LAT, LON0 + 600 * M_LON),
            (LAT0 + 450 * M_LAT, LON0)]            # 600 m (east) x 450 m (north)


def at(east_m, north_m, acc=20.0, mock=False):
    return Fix(LAT0 + north_m * M_LAT, LON0 + east_m * M_LON, acc, mock)


GOOD_INV = Invitation("C1", "inviter", NOW + timedelta(days=5), used=False, inviter_is_approved_member=True)


def run(fix=None, refused=False, inv=None, dup=False, user="u1"):
    return evaluate(fix=fix, permission_refused=refused, boundary=BOUNDARY, invitation=inv, community_id="C1",
                    user_id=user, duplicate_suspected=dup, now=NOW)


CASES = [
    # id, test case (Overview 1), input description, kwargs, expected outcome, expected signal
    ("L1a", "GPS spoofing", "fix inside, device reports a mock-location provider, valid invitation",
     dict(fix=at(300, 200, mock=True), inv=GOOD_INV), "CONFLICTING", "INSIDE"),
    ("L1b", "GPS spoofing", "undetected spoofed fix inside, no invitation",
     dict(fix=at(300, 200)), "INCONCLUSIVE", "INSIDE"),
    ("L1c", "GPS spoofing", "spoofed fix places the user 2 km away from the claimed community",
     dict(fix=at(2600, 200), inv=GOOD_INV), "CONFLICTING", "OUTSIDE"),
    ("L2a", "Boundary users", "30 m inside the edge, accuracy 20 m, valid invitation",
     dict(fix=at(30, 200), inv=GOOD_INV), "INCONCLUSIVE", "NEAR_BOUNDARY"),
    ("L2b", "Boundary users", "30 m outside the edge, accuracy 20 m, valid invitation",
     dict(fix=at(-30, 200), inv=GOOD_INV), "INCONCLUSIVE", "NEAR_BOUNDARY"),
    ("L2c", "Boundary users", "150 m inside the edge, accuracy 20 m, valid invitation",
     dict(fix=at(150, 200), inv=GOOD_INV), "VERIFIED", "INSIDE"),
    ("L3", "Visitors", "inside the community, no invitation from a member",
     dict(fix=at(300, 200)), "INCONCLUSIVE", "INSIDE"),
    ("L4", "Location-permission refusal", "permission refused, valid invitation",
     dict(refused=True, inv=GOOD_INV), "INCONCLUSIVE", "UNAVAILABLE"),
    ("L5", "Duplicate accounts", "inside, valid invitation, duplicate-account signal raised",
     dict(fix=at(300, 200), inv=GOOD_INV, dup=True), "CONFLICTING", "INSIDE"),
    ("L6a", "False rejection of genuine residents", "resident at home: inside, accuracy 20 m, valid invitation",
     dict(fix=at(300, 200), inv=GOOD_INV), "VERIFIED", "INSIDE"),
    ("L6b", "False rejection of genuine residents", "resident indoors, poor accuracy 250 m, valid invitation",
     dict(fix=at(300, 200, acc=250), inv=GOOD_INV), "INCONCLUSIVE", "UNAVAILABLE"),
    ("L6c", "False rejection of genuine residents", "new resident, inside, knows no member (no invitation)",
     dict(fix=at(300, 200)), "INCONCLUSIVE", "INSIDE"),
]
ERRORS = [
    ("E1", "Invitation code expired (UC-A3 3d)", Invitation("C1", "inviter", NOW - timedelta(days=1), False, True)),
    ("E2", "Invitation code already used (UC-A3 3d)", Invitation("C1", "inviter", NOW + timedelta(days=5), True, True)),
    ("E3", "Invitation for another community (UC-A3 3d)", Invitation("C2", "inviter", NOW + timedelta(days=5), False, True)),
    ("E4", "Self-invitation (UC-A3 3d)", Invitation("C1", "u1", NOW + timedelta(days=5), False, True)),
]


def main():
    rows, ok = [], True
    for cid, tc, desc, kw, exp_out, exp_sig in CASES:
        r = run(**kw)
        passed = (r.outcome, r.geofence_signal) == (exp_out, exp_sig)
        ok &= passed
        rows.append((cid, tc, desc, f"{exp_out} ({exp_sig})", f"{r.outcome} ({r.geofence_signal})", passed))
    for cid, tc, inv in ERRORS:
        try:
            run(fix=at(300, 200), inv=inv)
            actual, passed = "accepted", False
        except InvalidInvitation:
            actual, passed = "error: retry", True
        ok &= passed
        rows.append((cid, "Invitation errors", tc, "error: retry", actual, passed))
    # privacy: what would be stored has no coordinates or accuracy
    stored = stored_fields(run(fix=at(300, 200), inv=GOOD_INV))
    leak = [k for k in stored if any(t in k for t in ("lat", "lon", "accuracy", "coord", "address"))]
    passed = not leak and not any(isinstance(v, float) for v in stored.values())
    ok &= passed
    rows.append(("P1", "Privacy", "fields that would be stored after a check", "no coordinates or accuracy",
                 "none" if passed else f"leaks {leak}", passed))
    # no negative outcome exists: every combination stays within the three values
    outs = {run(fix=at(e, n, a, m), inv=i, dup=d).outcome for e in (-500, -30, 30, 300) for n in (200,)
            for a in (20, 250) for m in (False, True) for i in (None, GOOD_INV) for d in (False, True)}
    passed = outs <= {"VERIFIED", "INCONCLUSIVE", "CONFLICTING"}
    ok &= passed
    rows.append(("P2", "No automatic rejection", "64 combinations of position, accuracy, mock, invitation, duplicate",
                 "only VERIFIED / INCONCLUSIVE / CONFLICTING", ", ".join(sorted(outs)), passed))

    lines = ["# A11 locality test cases: results", "",
             "Generated by `test_locality_cases.py` (synthetic inputs). Expected values come from the A11 decision table.",
             "", "| ID | Test case | Input | Expected | Actual | Result |", "|---|---|---|---|---|---|"]
    for cid, tc, desc, exp, act, passed in rows:
        lines.append(f"| {cid} | {tc} | {desc} | {exp} | {act} | {'PASS' if passed else 'FAIL'} |")
    lines += ["", f"**{sum(r[5] for r in rows)}/{len(rows)} passed**"]
    text = "\n".join(lines) + "\n"
    print(text)
    with open(os.path.join(HERE, "locality_test_results.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
