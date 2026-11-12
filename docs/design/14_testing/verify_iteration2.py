"""Consistency checks for Student 1's iteration 2 design artefacts (the iteration 1 checks stay in verify_design.py).

    python 14_testing/verify_iteration2.py          (from docs/design)

C01 lifecycle model v3: every event used, every state reachable, 39 leaf rows
C02 transition_table_v3.csv lists exactly the model's transitions
C03 migration 0002 seeds exactly the leaf rows the model adds to schema v2.3
C04 transition_test_matrix_v3.csv: 14 x 24 pairs, valid pairs match the model
C05 every iteration 2 .drawio file of Student 1 is well-formed and has no dangling edge
C06 config 1.4.0 keeps every key of the backend's 1.3.0 config and is cited with its version
C07 Student 1's iteration 2 documents carry a control block (owner or authors, version, status)
C08 relative paths cited in the documents exist
C09 the ranking worked example is reproducible from the config
"""
import csv
import io
import json
import os
import re
import runpy
import sys
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(ROOT, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_tools"))
import lifecycle_model_v3 as lm  # noqa: E402

results = []

# Student 1's iteration 2 artefacts; the other files in docs/design are checked by verify_design.py or their owners
DIAGRAMS = ["03_architecture/component_diagram_v2.drawio", "03_architecture/layer_diagram_v2.drawio",
            "05_class_model/class_diagram_s1_iteration2.drawio", "05_class_model/class_diagram_s2_iteration2.drawio",
            "06_data_model/er_diagram_v2_4.drawio", "07_state_machines/borrowing_lifecycle_state_machine_v3.drawio",
            "08_sequence_diagrams/sequence_d_join_community.drawio",
            "08_sequence_diagrams/sequence_e_overdue_escalation.drawio",
            "08_sequence_diagrams/sequence_f_review_to_signals.drawio"]
DOCUMENTS = ["00_management/Scope_Baseline_and_Change_Record.md", "03_architecture/Architecture_Design_v2.md",
             "05_class_model/Class_Model_Design_Iteration2.md", "06_data_model/ER_Schema_Design_v2_4.md",
             "06_data_model/Data_Dictionary_v2_4.md", "07_state_machines/State_Machine_Design_v3.md",
             "07_state_machines/transition_table_v3.md", "08_sequence_diagrams/Sequence_D_E_F_Design.md",
             "11_assurance_engine/Algorithm_Design_Iteration2.md", "11_assurance_engine/ranking_example_results.md"]


def check(cid, name):
    def wrap(fn):
        try:
            problems = fn() or []
        except Exception as exc:  # noqa: BLE001
            problems = [f"exception: {exc!r}"]
        results.append((cid, name, problems))
        return fn
    return wrap


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def seed_rows(sql):
    return set(re.findall(r"\('([A-Z_]+)'\s*,\s*'([a-z_]+)'\s*,\s*'([A-Z_]+)'\s*,\s*'\{[A-Z,]+\}'\s*,\s*'([TI][0-9a-cTI/]+)'", sql))


@check("C01", "Lifecycle model v3 is complete")
def c01():
    out = io.StringIO()
    with redirect_stdout(out):
        runpy.run_path(os.path.join(ROOT, "_tools", "lifecycle_model_v3.py"), run_name="__main__")
    rows = lm.leaf_rows()
    return [] if len(rows) == 39 and len(lm.STATES) == 14 and len(lm.EVENTS) == 24 else \
        [f"{len(lm.STATES)} states, {len(lm.EVENTS)} events, {len(rows)} leaf rows (expected 14, 24, 39)"]


@check("C02", "transition_table_v3.csv matches the model")
def c02():
    with open(os.path.join(ROOT, "07_state_machines", "transition_table_v3.csv"), encoding="utf-8") as fh:
        ids = {r["id"] for r in csv.DictReader(fh)}
    want = {t["id"] for t in lm.T} | {i["id"] for i in lm.INTERNAL}
    return [] if ids == want else [f"differs: {sorted(ids ^ want)}"]


@check("C03", "Migration 0002 seeds exactly the new leaf rows")
def c03():
    old = {(f, e, t) for f, e, t, _ in seed_rows(read(os.path.join(ROOT, "06_data_model", "schema.sql")))}
    new = {(f, e, t) for f, e, t, _ in seed_rows(read(os.path.join(ROOT, "06_data_model", "migration_0002_schema_v2_4.sql")))}
    model = {(f, e, t) for f, e, t, *_ in lm.leaf_rows()}
    problems = []
    if old | new != model:
        problems.append(f"v2.3 + 0002 rows differ from the model: {sorted((old | new) ^ model)}")
    if old & new:
        problems.append(f"rows seeded twice: {sorted(old & new)}")
    return problems


@check("C04", "Transition test matrix matches the model")
def c04():
    with open(os.path.join(HERE, "transition_test_matrix_v3.csv"), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    valid = {(r["state"], r["event_type"]) for r in rows if r["expected"].startswith("VALID")}
    model = {(f, e) for f, e, *_ in lm.leaf_rows()}
    problems = []
    if len(rows) != len(lm.STATES) * len(lm.EVENTS):
        problems.append(f"{len(rows)} pairs, expected {len(lm.STATES) * len(lm.EVENTS)}")
    if valid != model:
        problems.append(f"valid pairs differ: {sorted(valid ^ model)}")
    return problems


@check("C05", "Diagrams are well-formed, no dangling edges")
def c05():
    problems, n = [], 0
    for rel in DIAGRAMS:
        f = os.path.basename(rel)
        n += 1
        tree = ET.parse(os.path.join(ROOT, rel))
        for diagram in tree.getroot().iter("diagram"):
            ids = {c.get("id") for c in diagram.iter("mxCell")}
            for c in diagram.iter("mxCell"):
                for k in ("source", "target", "parent"):
                    if c.get(k) and c.get(k) not in ids:
                        problems.append(f"{f}: {c.get('id')} dangling {k}")
    return problems if n else ["no diagrams found"]


@check("C06", "Config 1.4.0 is a superset of the backend config and is cited")
def c06():
    new = json.loads(read(os.path.join(ROOT, "11_assurance_engine", "Assurance_Engine_Config_v1.4.0.json")))
    old = json.loads(read(os.path.join(REPO, "backend", "config", "engine.json")))
    problems = []

    def walk(a, b, path):
        for k, v in a.items():
            if k not in b:
                problems.append(f"missing key {path}{k}")
            elif isinstance(v, dict) and isinstance(b[k], dict):
                walk(v, b[k], f"{path}{k}.")
            elif k not in ("config_version", "updated_at", "changelog", "author", "rule_order", "iteration_2_scheduled",
                           "source") and v != b[k] and not isinstance(v, dict):
                problems.append(f"value changed {path}{k}: {v!r} -> {b[k]!r}")
    walk(old, new, "")
    version = new["config_metadata"]["config_version"]
    for f in ("06_data_model/Data_Dictionary_v2_4.md", "11_assurance_engine/Algorithm_Design_Iteration2.md",
              "11_assurance_engine/ranking_example_results.md"):
        if version not in read(os.path.join(ROOT, f)):
            problems.append(f"{f} does not cite {version}")
    return problems


GENERATED = {"transition_table_v3.md", "Data_Dictionary_v2_4.md", "ranking_example_results.md"}


def documents():
    for rel in DOCUMENTS:
        yield os.path.join(ROOT, rel)


@check("C07", "Hand-written documents carry a control block")
def c07():
    problems = []
    for p in documents():
        if os.path.basename(p) in GENERATED:
            continue
        head = read(p)[:1500]
        if not (re.search(r"\|\s*(Owner|Owners|Authors)\s*\|", head) and re.search(r"\|\s*Version\s*\|", head)
                and re.search(r"\|\s*Status\s*\|", head)):
            problems.append(f"{os.path.relpath(p, ROOT)}: no control block (owner, version, status)")
    return problems


@check("C08", "Cited relative paths exist")
def c08():
    problems = []
    for p in documents():
        for m in re.finditer(r"`((?:\.\./)+[^`\s]+?\.(?:md|py|sql|drawio|json|csv))`", read(p)):
            target = os.path.normpath(os.path.join(os.path.dirname(p), m.group(1)))
            if not os.path.exists(target):
                problems.append(f"{os.path.relpath(p, ROOT)}: {m.group(1)} does not exist")
    return problems


@check("C09", "Ranking worked example is reproducible")
def c09():
    path = os.path.join(ROOT, "11_assurance_engine", "ranking_example_results.md")
    before = read(path)
    out = io.StringIO()
    with redirect_stdout(out):
        runpy.run_path(os.path.join(ROOT, "11_assurance_engine", "generate_ranking_example.py"), run_name="__main__")
    return [] if read(path) == before else ["ranking_example_results.md changed when regenerated: commit the new output"]


if __name__ == "__main__":
    passed = 0
    for cid, name, problems in results:
        print(f"[{'PASS' if not problems else 'FAIL'}] {cid} {name}")
        for p in problems[:20]:
            print(f"        - {p}")
        passed += not problems
    print(f"\n{passed}/{len(results)} checks passed")
    sys.exit(0 if passed == len(results) else 1)
