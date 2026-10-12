"""Design-wide consistency checks for the integrated Part-A baseline (all three students' artefacts).

    python 14_testing/verify_design.py        -> prints one line per check; exit code 1 if any check fails

What it checks (each check names the decision or requirement it protects):
  C01  every repository path cited in a Markdown file exists (folder reorganisation, D16)
  C02  every .drawio file is well-formed XML and no edge points to a missing cell
  C03  no superseded vocabulary or value survives outside change notes (D10-D15)
  C04  one config_version everywhere (D15, NFR-D-01)
  C05  the decision-table rules agree across config, schema check, schema tests and fixture oracle (ADR-0007/0008)
  C06  value bands agree between schema enum and config (D14)
  C07  the transition table CSV matches the lifecycle model and the suite-1 matrix (FR-B-08)
  C08  every FR / NFR / UC id cited in the test plan and traceability matrix exists in the requirements
  C09  every hand-written design document has a control block (plan step A0)
  C10  the fixtures pass the oracle (NFR-Q-01, A5 "done when")
  C11  ADR-0001 to ADR-0008 are all present and the sign-off table lists each
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "_tools"))
sys.path.insert(0, HERE)
SKIP_DIRS = {"archive_v1", "__pycache__", "_references"}
RESULTS = []


def check(cid, name):
    def deco(fn):
        try:
            problems = fn() or []
        except Exception as exc:                       # a crashing check is a failing check
            problems = [f"exception: {exc!r}"]
        RESULTS.append((cid, name, problems))
        return fn
    return deco


def files(ext):
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(ext):
                yield os.path.join(dp, f)


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def read(p):
    return open(p, encoding="utf-8").read()


# --------------------------------------------------------------------------- C01
@check("C01", "Cited repository paths exist")
def c01():
    pat = re.compile(r"`((?:\d\d_[a-z_]+|_tools)/[^`\s*]+?\.(?:md|py|sql|json|csv|drawio|txt))`")
    link = re.compile(r"\]\(((?!https?:|#|mailto:)[^)\s]+)\)")
    out = []
    for p in files(".md"):
        text = read(p)
        for m in pat.finditer(text):
            if not os.path.exists(os.path.join(ROOT, m.group(1))):
                out.append(f"{rel(p)}: `{m.group(1)}` does not exist")
        for m in link.finditer(text):
            target = m.group(1).split("#")[0]
            if target and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), target))):
                out.append(f"{rel(p)}: link ({m.group(1)}) does not resolve")
    return out


# --------------------------------------------------------------------------- C02
@check("C02", "Diagrams are well-formed, no dangling edges")
def c02():
    out = []
    for p in files(".drawio"):
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError as exc:
            out.append(f"{rel(p)}: {exc}")
            continue
        for diagram in root.iter("diagram"):
            ids = {c.get("id") for c in diagram.iter("mxCell")}
            for c in diagram.iter("mxCell"):
                for k in ("source", "target", "parent"):
                    if c.get(k) and c.get(k) not in ids:
                        out.append(f"{rel(p)} [{diagram.get('name')}]: {c.get('id')} has dangling {k}")
    return out


# --------------------------------------------------------------------------- C03
STALE = {   # term -> files (relative) where it may legitimately appear as history or explanation
    "VERY_HIGH": {"00_management/Integration_Decisions_2026-10-11.md", "00_management/Integration_Report_2026-10-11.md",
                  "06_data_model/Assurance_Data_Dictionary.md"},
    "1.0.0-draft": {"00_management/Integration_Report_2026-10-11.md"},
    "HIGH_ASSURANCE": {"00_management/Integration_Report_2026-10-11.md"},
    "STANDARD_FLOW": {"00_management/Integration_Report_2026-10-11.md"},
    "48h": {"00_management/Integration_Report_2026-10-11.md"},
    "clientGps": {"00_management/Integration_Report_2026-10-11.md"},
    "verifyLocality": {"00_management/Integration_Report_2026-10-11.md"},
    "assessment_risk_hold_ck": {"03_architecture/DigitalMohalla_ADRs_Ver1.md", "00_management/Integration_Report_2026-10-11.md"},
    "Acitvity": {"00_management/Integration_Report_2026-10-11.md"},
    "Accepted or Active booking": set(),
    "ACCEPTED/ACTIVE bookings": set(),
    "Transaction Service": {"00_management/Integration_Report_2026-10-11.md"},
}


@check("C03", "No superseded vocabulary or values")
def c03():
    out = []
    for ext in (".md", ".py", ".sql", ".json", ".csv", ".drawio"):
        for p in files(ext):
            if os.path.abspath(p) == os.path.abspath(__file__):
                continue
            text = read(p)
            for term, allowed in STALE.items():
                if term in text and rel(p) not in allowed:
                    out.append(f"{rel(p)}: contains superseded '{term}'")
    return out


# --------------------------------------------------------------------------- C04
@check("C04", "One config_version everywhere")
def c04():
    cfg = json.load(open(os.path.join(ROOT, "11_assurance_engine", "Assurance_Engine_Config_Draft.json"), encoding="utf-8"))
    cv = cfg["config_metadata"]["config_version"]
    out = []
    fx = json.load(open(os.path.join(HERE, "scenario_fixtures_iteration1.json"), encoding="utf-8"))
    if fx["metadata"]["config_version"] != cv:
        out.append(f"fixtures use {fx['metadata']['config_version']} not {cv}")
    for f in ("06_data_model/Data_Dictionary.md", "08_sequence_diagrams/Sequence_A_Request_To_Assessment.md",
              "10_dfd/Assurance_Pipeline_DFD_Level_0_Level_1.md", "08_sequence_diagrams/sequence_a_request_to_assessment.drawio",
              "13_wireframes/wireframes.drawio"):
        if cv not in read(os.path.join(ROOT, f)):
            out.append(f"{f} does not name config {cv}")
    return out


# --------------------------------------------------------------------------- C05
@check("C05", "Decision-table rules agree (config, schema, schema tests, oracle)")
def c05():
    import verify_fixtures as vf
    cfg = json.load(open(os.path.join(ROOT, "11_assurance_engine", "Assurance_Engine_Config_Draft.json"), encoding="utf-8"))
    order = cfg["decision_policy_alg4"]["rule_order"]
    sql = read(os.path.join(ROOT, "06_data_model", "schema.sql"))
    block = sql[sql.index("assessment_rule_ck"):]
    block = block[:block.index("ELSE false END")]
    in_sql = re.findall(r"WHEN '(R[0-9][A-Z_]*)'", block)
    tests = read(os.path.join(ROOT, "06_data_model", "test_schema.py"))
    in_tests = re.findall(r'"(R[0-9][A-Z_]*)": \(', tests)
    out = []
    for name, got in (("schema.sql", in_sql), ("test_schema.py", in_tests), ("verify_fixtures.py", list(vf.RULES))):
        if got != order:
            out.append(f"{name} rules {got} differ from config rule_order {order}")
    holds = {r: h for r, (_, _, h) in vf.RULES.items() if h}
    if holds != cfg["decision_policy_alg4"]["hold_rules"]:
        out.append(f"hold rules differ: oracle {holds} vs config {cfg['decision_policy_alg4']['hold_rules']}")
    algo = read(os.path.join(ROOT, "11_assurance_engine", "Algorithm_and_Data_Structure_Design.md"))
    for r in order:
        if f'rule="{r}"' not in algo:
            out.append(f"Algorithm doc pseudocode has no rule {r}")
    return out


# --------------------------------------------------------------------------- C06
@check("C06", "Value bands agree (schema enum, config)")
def c06():
    sql = read(os.path.join(ROOT, "06_data_model", "schema.sql"))
    enum = re.search(r"CREATE TYPE value_band\s+AS ENUM \(([^)]*)\)", sql).group(1)
    bands = [b.strip().strip("'") for b in enum.split(",")]
    cfg = json.load(open(os.path.join(ROOT, "11_assurance_engine", "Assurance_Engine_Config_Draft.json"), encoding="utf-8"))
    keys = {k for k in cfg["decision_policy_alg4"]["value_bands_pkr"] if k != "source"}
    expected = ["LOW", "MEDIUM", "HIGH"]
    out = []
    if bands != expected:
        out.append(f"schema value_band {bands} != {expected}")
    if set(keys) != {"low_value_max", "medium_value_max", "high_value_min"}:
        out.append(f"config value bands {sorted(keys)}")
    return out


# --------------------------------------------------------------------------- C07
@check("C07", "Transition table matches the lifecycle model and the suite-1 matrix")
def c07():
    import lifecycle_model as lm
    rows = list(csv.DictReader(open(os.path.join(ROOT, "07_state_machines", "transition_table.csv"), encoding="utf-8")))
    triples = {(r["from_state"], r["event_type"], r["to_state"]) for r in rows if r["from_state"] != "(initial)"}
    model = {(f, e, to) for f, e, to, *_ in lm.leaf_rows()}
    out = []
    if triples != model:
        out.append(f"CSV and lifecycle model differ: {sorted(triples ^ model)[:5]}")
    if len(model) != 34:
        out.append(f"{len(model)} leaf rows, expected 34 (allowed_transition)")
    matrix = list(csv.DictReader(open(os.path.join(HERE, "transition_test_matrix.csv"), encoding="utf-8")))
    if len(matrix) != len(lm.STATES) * len(lm.EVENTS):
        out.append(f"matrix has {len(matrix)} rows, expected {len(lm.STATES) * len(lm.EVENTS)}")
    m_valid = {(r["state"], r["event_type"]) for r in matrix if r["expected"] == "VALID"}
    if m_valid != {(f, e) for f, e, _ in model}:
        out.append("matrix valid pairs differ from the lifecycle model (regenerate the matrix)")
    return out


# --------------------------------------------------------------------------- C08
@check("C08", "Requirement ids cited in the test plan and traceability matrix exist")
def c08():
    req = read(os.path.join(ROOT, "01_requirements", "DigitalMohalla_FR_NFR_Ver1.md"))
    defined = set(re.findall(r"\| ((?:FR|NFR)-[A-Z]+-\d\d) \|", req))
    out = []
    for f in ("14_testing/Test_Plan.md", "01_requirements/Traceability_Matrix.md", "13_wireframes/Wireframes_Design.md"):
        text = read(os.path.join(ROOT, f))
        for rid in set(re.findall(r"\b((?:FR|NFR)-[A-Z]+-\d\d)\b", text)):
            if rid not in defined:
                out.append(f"{f}: {rid} is not defined in the FR/NFR baseline")
    return out


# --------------------------------------------------------------------------- C09
GENERATED = {"06_data_model/Data_Dictionary.md", "07_state_machines/transition_table.md",
             "11_assurance_engine/khop_example_results.md", "12_locality/locality_test_results.md",
             "14_testing/fixture_verification_results.md"}


@check("C09", "Hand-written design documents carry a control block")
def c09():
    out = []
    for p in files(".md"):
        r = rel(p)
        if r in GENERATED or r == "README.md":
            continue
        head = read(p)[:2500]
        if not re.search(r"\|\s*Version\s*\||\*\*Version:\*\*|Oct 1\d, 2026|\| Recorded by \|", head):
            out.append(f"{r}: no control block (version, date, author, status)")
    return out


# --------------------------------------------------------------------------- C10
@check("C10", "Fixtures pass the oracle")
def c10():
    import verify_fixtures as vf
    rows, problems, _ = vf.run()
    return problems if problems else ([] if len(rows) >= 13 else [f"only {len(rows)} fixtures"])


# --------------------------------------------------------------------------- C11
@check("C11", "ADR-0001 to ADR-0008 present and in the sign-off table")
def c11():
    text = read(os.path.join(ROOT, "03_architecture", "DigitalMohalla_ADRs_Ver1.md"))
    out = []
    for n in range(1, 9):
        a = f"ADR-{n:04d}"
        if f"## {a}:" not in text:
            out.append(f"{a} heading missing")
        if not re.search(rf"\| {a}[ (|]", text.split("## Sign-off")[1]):
            out.append(f"{a} not in the sign-off table")
    return out


# --------------------------------------------------------------------------- C12
def _pages(path):
    for diagram in ET.parse(os.path.join(ROOT, path)).getroot().iter("diagram"):
        cells = {c.get("id"): c for c in diagram.iter("mxCell")}
        yield diagram.get("name"), cells


@check("C12", "Standard notation rules hold (DFD, activity, use case, deployment, sequence)")
def c12():
    out = []
    # DFD (Gane & Sarson): every flow touches a process; level 0 has no data stores
    for name, cells in _pages("10_dfd/dfd_assurance_pipeline_level0_level1.drawio"):
        def is_proc(cid):
            return "rounded=1" in (cells.get(cid).get("style") or "") if cid in cells else False
        for c in cells.values():
            if c.get("edge") and c.get("source") and c.get("target"):
                if not (is_proc(c.get("source")) or is_proc(c.get("target"))):
                    out.append(f"DFD [{name}]: flow {c.get('value')!r} connects no process")
        if "level 0" in name and any("partialRectangle" in (c.get("style") or "") for c in cells.values()):
            out.append(f"DFD [{name}]: a context diagram must not show data stores")
    # activity: every decision with two or more outgoing flows guards each of them; no action with 2+ incoming flows
    for path in ("09_activity_diagrams/decision_policy_activity_diagram.drawio",):
        for name, cells in _pages(path):
            outgoing, incoming = {}, {}
            for c in cells.values():
                if c.get("edge"):
                    outgoing.setdefault(c.get("source"), []).append(c)
                    incoming.setdefault(c.get("target"), []).append(c)
            for cid, c in cells.items():
                style = c.get("style") or ""
                if "rhombus" in style and len(outgoing.get(cid, [])) > 1:
                    for e in outgoing[cid]:
                        if not (e.get("value") or "").startswith("["):
                            out.append(f"{path}: decision {cid} has an unguarded outgoing flow")
                if "rounded=1" in style and len(incoming.get(cid, [])) > 1:
                    out.append(f"{path}: action {c.get('value', '')[:40]!r} has {len(incoming[cid])} incoming flows "
                               "(implicit join; use a merge node)")
    # use case: no actor named like an internal component
    for name, cells in _pages("02_use_case_model/use_case_diagram.drawio"):
        for c in cells.values():
            if "umlActor" in (c.get("style") or "") and "Trust Engine" in (c.get("value") or ""):
                out.append("use case diagram: the Trust Engine is a system component, not an actor")
    # deployment: artifacts are not drawn with the comment (note) shape
    for name, cells in _pages("04_deployment/deployment_diagram.drawio"):
        for c in cells.values():
            if "shape=note" in (c.get("style") or "") and "artifact" in (c.get("value") or ""):
                out.append("deployment: an artifact is drawn as a UML comment (note shape)")
    # sequence diagrams: actors are stick figures, never boxes
    for path in ("08_sequence_diagrams/sequence_a_request_to_assessment.drawio",
                 "08_sequence_diagrams/sequence_b_handover_return.drawio",
                 "08_sequence_diagrams/sequence_c_dispute.drawio"):
        for name, cells in _pages(path):
            for c in cells.values():
                v = c.get("value") or ""
                if "(Actor)" in v and "umlActor" not in (c.get("style") or ""):
                    out.append(f"{path}: actor {v[:30]!r} drawn as a box")
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    failed = 0
    for cid, name, problems in RESULTS:
        status = "PASS" if not problems else "FAIL"
        failed += bool(problems)
        print(f"[{status}] {cid} {name}")
        for p in problems[:25]:
            print(f"        - {p}")
    print(f"\n{len(RESULTS) - failed}/{len(RESULTS)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
