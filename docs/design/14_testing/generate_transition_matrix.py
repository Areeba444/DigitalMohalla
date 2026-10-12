"""Generates transition_test_matrix.csv: the oracle of test suite 1 (state-transition testing, FR-B-08, NFR-R-02).

One row for every (state, event type) pair of the borrowing lifecycle: 14 states x 21 event types = 294 pairs.
A pair is VALID when the A3 transition table (07_state_machines/transition_table.csv, generated from
_tools/lifecycle_model.py) has at least one leaf row for it; the row then lists the allowed next state(s), the
transition IDs and the actors. Every other pair must be REJECTED and logged (403 / 409, audit_log REJECTED).

Run: python 14_testing/generate_transition_matrix.py
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
import lifecycle_model as lm  # noqa: E402

TABLE = os.path.join(HERE, "..", "07_state_machines", "transition_table.csv")


def main():
    rows = list(csv.DictReader(open(TABLE, encoding="utf-8")))
    valid = {}
    for r in rows:
        if r["from_state"] == "(initial)":
            continue
        valid.setdefault((r["from_state"], r["event_type"]), []).append(r)
    out = []
    n = 0
    for s in lm.STATES:
        for e in [ev[0] if isinstance(ev, tuple) else ev for ev in lm.EVENTS]:
            n += 1
            hits = valid.get((s, e), [])
            if hits:
                out.append(dict(case=f"TM-{n:03d}", state=s, event_type=e, expected="VALID",
                                next_states="|".join(sorted({h["to_state"] for h in hits})),
                                transitions="|".join(sorted({h["id"] for h in hits})),
                                actors="|".join(sorted({a for h in hits for a in h["allowed_actors"].split("|")})),
                                iteration=min(h["iteration"] for h in hits)))
            else:
                out.append(dict(case=f"TM-{n:03d}", state=s, event_type=e, expected="REJECT (409, logged)",
                                next_states="", transitions="", actors="", iteration="1"))
    path = os.path.join(HERE, "transition_test_matrix.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    v = sum(1 for o in out if o["expected"] == "VALID")
    triples = {(r["from_state"], r["event_type"], r["to_state"]) for x in valid.values() for r in x}
    print(f"{path}: {len(out)} pairs, {v} valid pairs ({len(triples)} distinct valid triples), "
          f"{len(out) - v} must be rejected")


if __name__ == "__main__":
    main()
