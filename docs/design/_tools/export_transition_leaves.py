"""Writes backend/app/domain/lifecycle/transition_leaves.csv from the lifecycle model (F1).

    python docs/design/_tools/export_transition_leaves.py          # lifecycle v3 (iteration 2)

The backend's transition table is a copy of the design model's leaf rows; the database copy is
`allowed_transition` (migrations 0001 and 0003). test_domain_table_equals_database_table checks that the
two copies agree, so regenerate this file whenever lifecycle_model_v3.py changes, never edit it by hand.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle_model_v3 as model  # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "backend", "app", "domain", "lifecycle",
                                    "transition_leaves.csv"))

if __name__ == "__main__":
    rows = sorted(model.leaf_rows(), key=lambda r: (r[0], r[1], r[2]))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["from_state", "event_type", "to_state", "allowed_roles", "ref", "iteration"])
        for frm, event, to, actors, ref, it in rows:
            w.writerow([frm, event, to, "|".join(sorted(actors)), ref, it])
    print(f"{len(rows)} rows -> {OUT}")
