"""Generates class_diagram.drawio: ONE class diagram of the whole system at iteration 2 (DA-11, v3.0).

    python generate_class_diagram.py   ->  class_diagram.drawio

Every design class of Students 1, 2 and 3 appears once, in the package of the module that owns it:

  Module 1 accounts, accounts.membership          Student 1   generate_class_model.class_diagram (+ iteration 2 section)
  Module 3 lifecycle, lifecycle.listings ...      Student 1
  Module 5 assurance.indirect                     Student 1
  Module 4 search.retrieval / .ranking / logging  Students 1 / 2 / 3
  Module 5 assurance, assurance.reviews ...       Student 2   generate_class_diagrams_s2_s3.class_diagram_s2 (+ section)
  Module 7 notifications                          Student 2
  Module 9 moderation, uploads; Module 10         Student 3   generate_class_diagram_s3.class_diagram_s3

The sections are built by the owners' generators and placed on one canvas here. The boundary copies each section
used to show other students' classes are left out, because the real class is now on the same diagram: a dependency
on another module is shown by the interface or class named in the attribute or operation (for example
"- notify: INotify"), and the module-level dependencies are drawn in the component diagram (03_architecture). Lines
are drawn between packages only where a class of one section uses a class of another directly.

Shared convention: colour = owner (blue S1, orange S2, purple S3); green text = added or changed in iteration 2; green
border = class new in iteration 2. The iteration 1 diagrams (one per student) are in archive_v1/.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
sys.path.insert(0, HERE)
from drawio import Diagram  # noqa: E402
import generate_class_model as cm  # noqa: E402
import generate_class_diagrams_s2_s3 as s23  # noqa: E402
import generate_class_diagram_s3 as s3mod  # noqa: E402

_spec = importlib.util.spec_from_file_location("cd_it2", os.path.join(HERE, "generate_class_diagrams_iteration2.py"))
it2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(it2)

GAP = 40


def embed(D: Diagram, src: Diagram, dx: float, dy: float, prefix: str, drop=(), rename=None):
    """Copy src's cells into D, shifted by (dx, dy), ids prefixed. Cells in drop (and their children, the edges that
    touch them and those edges' multiplicity labels) are left out, as are the section's title lines."""
    drop = set(drop)
    for c in src.cells:                                         # section titles: text above the packages
        if c["kind"] == "v" and c["style"].startswith("text;") and c["y"] < 62 and not c.get("parent"):
            drop.add(c["id"])
    changed = True
    while changed:                                              # children of dropped containers
        changed = False
        for c in src.cells:
            if c["id"] not in drop and c.get("parent") in drop:
                drop.add(c["id"])
                changed = True
    for c in src.cells:
        if c["kind"] == "e" and (c["src"] in drop or c["tgt"] in drop):
            drop.add(c["id"])
    for c in src.cells:                                         # multiplicities of dropped edges: m_<edge>_a / _b
        if c["kind"] == "v" and c["id"].startswith("m_") and c["id"][2:].rsplit("_", 1)[0] in drop:
            drop.add(c["id"])
    for c in src.cells:
        if c["id"] in drop:
            continue
        n = dict(c)
        n["id"] = prefix + c["id"]
        if c.get("parent"):
            n["parent"] = prefix + c["parent"]
        if c["kind"] == "v":
            n["x"], n["y"] = c["x"] + dx, c["y"] + dy
            if rename and c["id"] in rename:
                n["label"] = rename[c["id"]]
        else:
            n["src"] = prefix + c["src"] if c["src"] else None
            n["tgt"] = prefix + c["tgt"] if c["tgt"] else None
            n["points"] = [(x + dx, y + dy) for x, y in c["points"]]
            n["src_pt"] = (c["src_pt"][0] + dx, c["src_pt"][1] + dy) if c["src_pt"] else None
            n["tgt_pt"] = (c["tgt_pt"][0] + dx, c["tgt_pt"][1] + dy) if c["tgt_pt"] else None
        D.cells.append(n)
        D.by_id[n["id"]] = n


def bottom(D: Diagram, prefix: str) -> float:
    return max(c["y"] + c["h"] for c in D.cells if c["kind"] == "v" and c["id"].startswith(prefix))


def mid_y(D: Diagram, cid: str, f: float = 0.5) -> float:
    b = D.box(cid)
    return b[1] + f * (b[3] - b[1])


def build() -> Diagram:
    D = Diagram("Class diagram, whole system (DA-11)", 4640, 6000)
    D.text("<b>Digital Mohalla &#8212; Class diagram of the whole system</b> (design step A7 v1.0; iteration 2 v3.0, "
           "DA-11): Modules 1, 3, 4, 5, 7, 9 and 10, all three students", 40, 12, 3000, 24, size=18, check=False)
    D.text("Python design classes. Colour = owner: <span style='background:#E3EEF9'>&nbsp;S1 Fatima&nbsp;</span> "
           "<span style='background:#FDEBDD'>&nbsp;S2 Areeba&nbsp;</span> <span style='background:#EEE5F6'>&nbsp;S3 "
           "Minahil&nbsp;</span>. <font color='#0A7A36'><b>Green text</b> = added or changed in iteration 2; <b>green "
           "border</b> = class new in iteration 2.</font> Each class names the FRs it realises; a dependency on another "
           "module is the interface named in the attribute or operation (module dependencies: component diagram).",
           40, 40, 4400, 22, size=12, color="#4A5560", check=False)

    # ---------------- Student 1: iteration 1 classes with their iteration 2 members, then the iteration 2 packages
    s1a = cm.class_diagram()
    embed(D, s1a, 0, 30, "a_", drop={"p_s2", "c_Assess", "c_Result", "c_Sink"})
    s1b = it2.class_diagram_s1_page2(unified=True)
    y_s1b = bottom(D, "a_") + GAP - 70
    embed(D, s1b, 0, y_s1b, "b_")

    # ---------------- Student 2: engine section, then the iteration 2 packages
    X2 = 2310
    s2a = s23.class_diagram_s2()
    embed(D, s2a, X2, 30, "c_", drop={"p_s1", "IInd", "IndEv"})
    s2b = it2.class_diagram_s2_page2(unified=True)
    y_s2b = bottom(D, "c_") + GAP - 70
    embed(D, s2b, X2, y_s2b, "d_")

    # ---------------- Student 3: moderation, uploads, search logging, evaluation and the interfaces Module 9 uses
    s3 = s3mod.class_diagram_s3()
    y_s3 = max(bottom(D, "b_"), bottom(D, "d_")) + GAP + 20 - 70
    embed(D, s3, 0, y_s3, "e_", drop={"IJobs", "ISearch", "INotify", "IAssessB"},
          rename={"p_bnd": "<b>interfaces provided by Modules 3 and 5, used by Module 9</b>"})

    # the interfaces package kept from Student 3's section holds three interfaces now: fit it to them
    kids = [c for c in D.cells if c["kind"] == "v" and c.get("parent") is None and c["id"] in ("e_ILife", "e_IEvt", "e_IFlags")]
    pb = D.by_id["e_p_bnd"]
    pb["w"] = max(c["x"] + c["w"] for c in kids) + 30 - pb["x"]
    pb["h"] = max(c["y"] + c["h"] for c in kids) + 30 - pb["y"]

    # ---------------- lines between sections: a class of one section using a class of another directly
    E = cm.link
    # registration creates a User (Module 1)
    E(D, "b_Reg", "a_c_User", "", style=cm.DEPEND, exit=(0, 0.5), entry=(0, 0.5),
      points=[(12, mid_y(D, "b_Reg")), (12, mid_y(D, "a_c_User"))])
    # the invitation is checked by the iteration 1 verifier
    E(D, "b_Inv", "a_c_Verifier", "&#171;use&#187;", style=cm.DEPEND, exit=(0, 0.3), entry=(0, 0.7),
      points=[(22, mid_y(D, "b_Inv", 0.3)), (22, mid_y(D, "a_c_Verifier", 0.7))], label_x=0.0, label_dx=22, label_dy=0)
    # the open counter-offer belongs to the transaction (rebuilt from its events, ADR-0015)
    ct = D.box("b_Ctr")[1] - 18
    E(D, "a_c_Txn", "b_Ctr", "", "1", "0..1", style=cm.COMPOSE, exit=(0, 0.92), entry=(0.9, 0),
      points=[(1104, mid_y(D, "a_c_Txn", 0.92)), (1104, ct), (1053, ct)], ma_off=(0, -1), mb_off=(0, 1))
    # scheduled jobs act through BorrowingService, like any user command (ADR-0012)
    E(D, "b_Run", "a_c_Svc", "", style=cm.DEPEND, exit=(0, 0.5), entry=(1, 0.88),
      points=[(1116, mid_y(D, "b_Run")), (1116, mid_y(D, "a_c_Svc", 0.88))])

    # ---------------- legend and notes, beside Student 3's packages
    lx, ly = 2750, y_s3 + 70
    D.node("<b>How to read this diagram</b><br>&#8226; One diagram for the whole system: every class appears once, "
           "in the package of the module that owns it. Packages with a dot are parts of one module "
           "(accounts.membership is Module 1, search.retrieval, search.ranking and search logging are Module 4).<br>"
           "&#8226; A dependency on a class of another module is shown by its type in the attribute or operation "
           "(for example <i>- notify: INotify</i>, <i>- engine: AssuranceEngine</i>); the module dependencies are the "
           "component diagram. Lines cross package borders only where one class uses another directly: Registration "
           "creates a User, InvitationService uses the verifier, a BorrowingTransaction holds its open CounterOffer, "
           "JobRunner acts through BorrowingService.<br>"
           "&#8226; <font color='#0A7A36'>Green text</font> = added or changed in iteration 2; <font color='#0A7A36'>"
           "green border</font> = class new in iteration 2. Everything else is as built in iteration 1.<br>"
           "&#8226; Interfaces between students: IAssess, IOutcomeSink (Module 5, S2); ILifecycleCommands, "
           "IEventQuery, JobRunner, ISearch (Modules 3 and 4, S1); INotify (Module 7, S2); IOutcomeFlags (Module 5, "
           "S2); SearchLogger (Module 4, S3).<br>"
           "&#8226; Relationship ends: &#9670; composition, &#9671; aggregation, plain line = association, dashed "
           "open arrow = dependency, dashed hollow triangle = realisation. The iteration 1 diagrams, one per student, "
           "are in archive_v1/.", lx, ly, 1860, 250,
           "shape=note;size=14;whiteSpace=wrap;html=1;fontSize=12;align=left;verticalAlign=top;spacingLeft=10;"
           "spacingTop=6;fillColor=#F4F6F8;strokeColor=#8C99A6;", check=False)

    D.width = int(max(c["x"] + c["w"] for c in D.cells if c["kind"] == "v") + 40)
    D.height = int(max(c["y"] + c["h"] for c in D.cells if c["kind"] == "v") + 40)
    return D


if __name__ == "__main__":
    build().save(os.path.join(HERE, "class_diagram.drawio"))
