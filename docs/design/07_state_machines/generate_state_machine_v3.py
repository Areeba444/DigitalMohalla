"""Generates the iteration 2 lifecycle state machine (v3) and its transition table (DA-06, Student 1).

    python generate_state_machine_v3.py

Outputs (next to this file):
    borrowing_lifecycle_state_machine_v3.drawio   UML state machine, BorrowingTransaction (14 states), v3
    transition_table_v3.csv                       leaf-level (state x event -> next state) table = test matrix
    transition_table_v3.md                        the same table for reading

Changes from iteration 1 (v2.2): ADR-0009 dispute exits by item possession (T25a, T25b, T25c) and ADR-0015
counter-offer (T29, I07, I08). The escalation-case state machine is Minahil's artefact DA-07 and is not drawn here.

States, events and transitions come from ../_tools/lifecycle_model_v3.py (single source of truth).
Edit that file, not the diagrams, when the lifecycle changes; then re-run this script.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))

from drawio import Diagram, EDGE_BASE  # noqa: E402
import lifecycle_model_v3 as lm  # noqa: E402

# actor colours (legend)
C_B, C_L, C_P, C_M, C_S = "#1F5FA8", "#2E7D32", "#00796B", "#7B3FA0", "#5F6B76"
ACTOR_COLOUR = {"B": C_B, "L": C_L, "P": C_P, "M": C_M, "S": C_S}

ST = ("rounded=1;arcSize=24;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2B3A4A;"
      "fontSize=12;fontColor=#1D1D1D;verticalAlign=middle;")
ST_TERM = ST + "strokeWidth=3;fillColor=#F4F6F8;"
ST_SIDE = ST + "fillColor=#FFF4E5;strokeColor=#B26A00;strokeWidth=2;"
ST_HOLD = ST + "fillColor=#F3ECF8;strokeColor=#7B3FA0;strokeWidth=2;"
COMPOSITE = ("rounded=1;arcSize=2;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=10;"
             "spacingTop=3;fontStyle=1;fontSize=13;fillColor=#F7F9FC;strokeColor=#7A8A9A;container=1;"
             "collapsible=0;recursiveResize=0;")
INIT = "ellipse;html=1;fillColor=#000000;strokeColor=#000000;"
FINAL = "ellipse;html=1;shape=endState;fillColor=#000000;strokeColor=#000000;"
CHOICE = "rhombus;html=1;fillColor=#FFFFFF;strokeColor=#2B3A4A;"
HIST = "ellipse;html=1;fillColor=#FFFFFF;strokeColor=#2B3A4A;fontStyle=1;fontSize=13;"


def tr_style(actor: str, it2: bool = False) -> str:
    c = ACTOR_COLOUR[actor]
    s = EDGE_BASE + f"strokeColor={c};fontColor={c};endArrow=open;endFill=0;strokeWidth=1.6;"
    if actor == "S":
        s += "dashed=1;dashPattern=6 3;"
    if it2:
        s += "opacity=70;textOpacity=85;"
    return s


def state(d, name, x, y, w=200, h=56, style=ST, body="", parent=None):
    label = f"<b>{name}</b>"
    if body:
        label += f"<hr style='margin:3px 0'><span style='font-size:10px'>{body}</span>"
    return d.node(label, x, y, w, h, style, id=name, parent=parent)


# =============================================================================== lifecycle
def lifecycle() -> Diagram:
    d = Diagram("Borrowing lifecycle v3 (DA-06)", 1840, 1530)
    d.text("<b>Digital Mohalla &#8212; Borrowing lifecycle state machine</b> (BorrowingTransaction, "
           "iteration 2, DA-06, v3.0)", 40, 12, 1100, 24, size=16, check=False)
    d.text("States and event types: Use Cases v1.4 &#167;2, FR-B-08; HELD_FOR_REVIEW exits ADR-0003; DISPUTED exits "
           "ADR-0004 and ADR-0009 (by item possession); counter-offer ADR-0015; overlap constraint ADR-0002. "
           "Transition IDs = rows of transition_table_v3.csv. <b>New or changed in v3: T25a, T25b, T25c, T29, I07, I08 (bold red IDs).</b>",
           40, 36, 1780, 20, size=11, color="#4A5560", check=False)

    # ---------------------------------------------------------------- PENDING composite
    P = d.node("PENDING&nbsp;&nbsp;<span style='font-weight:normal;font-size:11px'>(request not yet agreed; "
               "dates only marked as requested, ADR-0001)</span>", 40, 64, 1360, 496, COMPOSITE, id="PENDING")
    d.mark_container(P)
    d.node("", 225, 108, 20, 20, INIT, id="init", parent=P)
    state(d, "REQUEST_CREATED", 135, 170, parent=P)
    d.node("", 410, 178, 40, 40, CHOICE, id="c_loc", parent=P)
    state(d, "LOCALITY_CHECKED", 600, 170, parent=P)
    d.node("", 930, 178, 40, 40, CHOICE, id="c_assess", parent=P)
    state(d, "ASSESSED", 1150, 170, h=82, parent=P, body="lender sees assurance state + evidence<br>"
          "counter_offered (lender) / counter_declined<br>(borrower): internal, I07, I08, it.2")
    state(d, "HELD_FOR_REVIEW", 360, 400, w=640, h=64, style=ST_HOLD, parent=P,
          body="entry / record hold_reason; open escalation case (D6). Never an automatic rejection.")

    # ---------------------------------------------------------------- terminal states (pending side)
    state(d, "DECLINED", 240, 610, w=200, h=50, style=ST_TERM)
    state(d, "EXPIRED", 1570, 95, w=190, h=50, style=ST_TERM)
    state(d, "CANCELLED", 1570, 280, w=190, h=50, style=ST_TERM)

    # ---------------------------------------------------------------- IN_PROGRESS composite
    IP = d.node("IN_PROGRESS&nbsp;&nbsp;<span style='font-weight:normal;font-size:11px'>(booking HELD: dates "
                "blocked by the overlap constraint until release, ADR-0002)</span>", 40, 740, 1360, 300,
                COMPOSITE, id="IN_PROGRESS")
    d.mark_container(IP)
    state(d, "ACCEPTED", 1170, 840, w=200, h=70, parent=IP, body="reminder_sent (internal, it.2)")
    state(d, "ACTIVE", 800, 840, w=240, h=70, parent=IP,
          body="reminder_sent; extension_requested /<br>_approved / _declined (internal, it.2)")
    state(d, "RETURN_INITIATED", 470, 840, w=220, h=70, parent=IP, body="reminder_sent (internal, it.2)")
    state(d, "RETURNED", 120, 840, w=200, h=70, parent=IP)
    d.node("H", 785, 985, 30, 30, HIST, id="H", parent=IP)

    state(d, "COMPLETED", 120, 1130, w=200, h=80, style=ST_TERM,
          body="entry / outcome &#8594; engine; release booking;<br>record deposit release; unlock reviews")
    state(d, "DISPUTED", 760, 1130, w=300, h=80, style=ST_SIDE,
          body="entry / store previous_state; freeze deposit record<br>and transitions; open or attach case (D6)")
    state(d, "NO_SHOW", 1570, 850, w=190, h=50, style=ST_TERM)

    E = d.edge
    # ---- pending
    E("init", "REQUEST_CREATED", "request_created [G1] / mark dates as requested &nbsp;<b>T01</b>",
      style=tr_style("B"), exit=(0.5, 1), entry=(0.5, 0), label_dx=165, label_dy=-6)
    E("REQUEST_CREATED", "c_loc", "", style=tr_style("S"), exit=(1, 0.5), entry=(0, 0.5))
    E("c_loc", "LOCALITY_CHECKED", "[verified]<br>/ locality_checked &nbsp;<b>T02</b>",
      style=tr_style("S"), exit=(1, 0.5), entry=(0, 0.5), label_dy=-20)
    E("c_loc", "HELD_FOR_REVIEW", "[inconclusive | conflicting]<br>/ held_for_review<br>reason = locality_inconclusive"
      "<br>| locality_conflict &nbsp;<b>T03, T04</b>",
      style=tr_style("S"), exit=(0.5, 1), entry=((430 - 360) / 640, 0), label_dx=-118)
    E("LOCALITY_CHECKED", "c_assess", "/ assess(request)", style=tr_style("S"), exit=(1, 0.5), entry=(0, 0.5),
      label_dy=-12)
    E("c_assess", "ASSESSED", "[no hold reason]<br>/ assessment_generated &nbsp;<b>T05</b>",
      style=tr_style("S"), exit=(1, 0.5), entry=(0, 28 / 82), label_dy=-20)
    E("c_assess", "HELD_FOR_REVIEW", "[R2: risk level 4 | R4: high<br>value, weak evidence |<br>engine failure"
      " / timeout]<br>/ held_for_review<br>(reason recorded) <b>T06&#8211;T08</b>",
      style=tr_style("S"), exit=(0.5, 1), entry=((950 - 360) / 640, 0), label_dx=-112)
    E("HELD_FOR_REVIEW", "LOCALITY_CHECKED", "hold_cleared [reason = locality_*<br>| engine_failure] / safeguards"
      "<br>attached (none for engine_failure);<br>assessment runs again &nbsp;<b>T09, T10</b>",
      style=tr_style("M"), exit=((700 - 360) / 640, 0), entry=(0.5, 1), label_dx=-128)
    E("HELD_FOR_REVIEW", "ASSESSED", "hold_cleared [reason = manipulation_risk<br>| high_value_low_confidence]"
      "<br>/ moderator note + safeguards &nbsp;<b>T11</b>",
      style=tr_style("M"), exit=(1, 0.5), entry=(0.1, 1), points=[(1165, 432)], label_x=-0.32, label_dy=34)
    E("HELD_FOR_REVIEW", "DECLINED", "request_declined [moderator<br>restricts, reason] &nbsp;<b>T12</b>",
      style=tr_style("M"), exit=(40 / 640, 1), entry=(0.8, 0), label_dx=88, label_x=-0.3)
    E("ASSESSED", "ACCEPTED", "request_accepted [owner; overlap constraint holds]<br>/ write booking + event in one"
      " DB transaction; decline overlapping pending &nbsp;<b>T13</b>",
      style=tr_style("L"), exit=(0.75, 1), entry=(0.65, 0), label_x=0.52, label_dx=-158)
    E("ASSESSED", "DECLINED", "request_declined [lender] &nbsp;<b>T14</b>",
      style=tr_style("L"), exit=(0.4, 1), entry=(1, 0.5), points=[(1230, 635)], label_x=0.55, label_dy=-11)
    E("ASSESSED", "EXPIRED", "request_expired<br>[window elapsed] <b>T15</b> it.2",
      style=tr_style("S", True), exit=(0.75, 0), entry=(0, 0.5), points=[(1300, 120)], label_x=0.4, label_dy=-17)
    E("PENDING", "CANCELLED", "request_cancelled<br>[borrower] &nbsp;<b>T16</b>",
      style=tr_style("B"), exit=(1, (305 - 64) / 496), entry=(0, 0.5), label_dy=-17)
    E("PENDING", "DECLINED", "request_declined [dates taken] <b>T17</b>",
      style=tr_style("S"), exit=((300 - 40) / 1360, 1), entry=(0.3, 0), label_dx=-103)
    # ---- in progress
    E("ACCEPTED", "ACTIVE", "handover_confirmed<br>[checklist + receipt +<br>deposit recorded] <b>T18</b>",
      style=tr_style("P"), exit=(0, 0.5), entry=(1, 0.5), label_dy=-50)
    E("ACCEPTED", "NO_SHOW", "no_show [handover +<br>grace passed] <b>T19</b> it.2",
      style=tr_style("S", True), exit=(1, 0.5), entry=(0, 0.5), label_dx=12, label_dy=-20)
    E("ACTIVE", "RETURN_INITIATED", "return_initiated<br>[borrower] <b>T20</b>",
      style=tr_style("B"), exit=(0, 0.5), entry=(1, 0.5), label_dy=-50)
    E("RETURN_INITIATED", "RETURNED", "return_confirmed<br>[both confirm; agree]<br><b>T21</b>",
      style=tr_style("P"), exit=(0, 0.5), entry=(1, 0.5), label_dy=-50)
    E("RETURNED", "COMPLETED", "transaction_closed<br>/ outcome = on_time | late &nbsp;<b>T22</b>",
      style=tr_style("S"), exit=(0.5, 1), entry=(0.5, 0), label_x=0.35, label_dx=112)
    E("IN_PROGRESS", "DISPUTED", "dispute_opened<br>[party; not<br>RETURNED] <b>T23</b>",
      style=tr_style("P"), exit=((880 - 40) / 1360, 1), entry=(120 / 300, 0), label_dx=52)
    E("ACTIVE", "DISPUTED", "dispute_opened [overdue<br>limit] <b>T24</b> it.2",
      style=tr_style("S", True), exit=(200 / 240, 1), entry=(240 / 300, 0), label_x=0.62, label_dx=78)
    NEW = "<b><font color='#B00020'>"
    E("DISPUTED", "COMPLETED", f"dispute_resolved [moderator, reason;<br>possession = RETURNED | LOST]<br>"
      f"/ resolved outcome &#8594; engine {NEW}T25c</font></b>", style=tr_style("M"), exit=(0, 0.5), entry=(1, 0.5),
      label_dy=-28)
    E("DISPUTED", "NO_SHOW", f"dispute_resolved [raised from ACCEPTED;<br>possession = NOT_HANDED_OVER]<br>/ release "
      f"booking {NEW}T25a</font></b> it.2", style=tr_style("M", True), exit=(1, 0.25), entry=(0.5, 1),
      points=[(1665, 1150)], label_x=-0.35, label_dy=-30)
    E("DISPUTED", "ACTIVE", f"dispute_resolved [possession =<br>WITH_BORROWER] / the loan continues,<br>"
      f"booking stays held {NEW}T25b</font></b> it.2", style=tr_style("M", True), exit=(10 / 300, 0),
      entry=(0, 55 / 70), points=[(770, 895)], label_x=0.3, label_dx=-125)
    E("ASSESSED", "LOCALITY_CHECKED", f"counter_accepted [borrower; open counter-offer; dates free]<br>/ new dates; "
      f"assessment runs again {NEW}T29</font></b> it.2", style=tr_style("B", True), exit=(0.25, 0), entry=(0.5, 0),
      points=[(1200, 140), (700, 140)], label_dy=-16)
    E("DISPUTED", "H", "dispute_withdrawn [raising party]<br>/ restore previous_state <b>T26</b>",
      style=tr_style("P"), exit=(40 / 300, 0), entry=(0.5, 1), label_dx=-150, label_x=-0.15)

    # ---------------------------------------------------------------- legend
    lx, ly = 1180, 1260
    d.node("", lx, ly, 640, 250, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#B0BAC4;", id="legend_box",
           check=False)
    d.text("<b>Legend</b>", lx + 10, ly + 6, 200, 18, check=False)
    rows = [("B", "Borrower"), ("L", "Lender"), ("P", "Either party (the one completing the pair)"),
            ("M", "Moderator / Admin (authorised for the community)"), ("S", "System (lifecycle service, engine, "
                                                                            "scheduler)")]
    for i, (k, txt) in enumerate(rows):
        y = ly + 34 + i * 20
        d.edge(None, None, "", style=tr_style(k), src_pt=(lx + 12, y), tgt_pt=(lx + 62, y), check=False)
        d.text(txt, lx + 70, y - 9, 300, 18, size=10.5, check=False)
    notes = ("<b>event [guard] / action</b>; transition IDs T01&#8211;T29, I01&#8211;I08 are rows of transition_table_v3.csv.<br>"
             "Bold border = terminal state (no further transitions; record kept).<br>"
             "&#9671; choice pseudostate. <b>H</b> = shallow history of IN_PROGRESS: dispute_withdrawn restores the"
             " previous_state stored in dispute_opened (ADR-0004).<br>"
             "Border arrows apply to every substate of the composite (T23: except RETURNED, team decision D4).<br>"
             "<b>it.2</b> = built in iteration 2 (scheduler, extensions, counter-offer, possession exits); faded.<br>"
             "Lifecycle state &#8800; assurance state: the assurance state is an attribute of the Assessment "
             "(e.g. HELD_FOR_REVIEW with REVIEW_RECOMMENDED, ES-04).")
    d.text(notes, lx + 10, ly + 136, 620, 110, size=9.5, check=False)
    return d


def write_csv(path):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "from_state", "event_type", "to_state", "guard", "action", "allowed_actors", "source",
                    "frs", "scenarios", "iteration"])
        for tr in lm.T:
            frm = tr["frm"] or "(initial)"
            for f in (lm.froms(tr) if tr["frm"] else [frm]):
                for to in lm.tos(tr):
                    guard = tr["guard"]
                    if tr["to"] == "H":
                        guard += f"; dispute_opened.previous_state = {to}"
                    w.writerow([tr["id"], f, tr["event"], to, guard, tr["action"], "|".join(tr["actors"]),
                                tr["source"], tr["frs"], tr["es"], tr["it"]])
        for it in lm.INTERNAL:
            w.writerow([it["id"], it["state"], it["event"], it["state"], it["guard"], "(internal; state unchanged)",
                        "|".join(it["actors"]), it["source"], it["frs"], "", it["it"]])
    print(f"{path}: written")


def write_md(path):
    """Human-readable transition table (same rows as the CSV), included by State_Machine_Design.md."""
    L = ["# Borrowing lifecycle: transition table, v3 (iteration 2, DA-06)", "",
         "Generated by `generate_state_machine_v3.py` from `_tools/lifecycle_model_v3.py`; do not edit by hand. "
         "Border transitions (from PENDING / IN_PROGRESS) and the history return (H) are listed once here and "
         "expanded to leaf rows in `transition_table_v3.csv` and in `allowed_transition` (schema.sql).", "",
         "| ID | From | Event type | To | Guard | Action | Actor | Source | FRs | ES | It. |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for tr in lm.T:
        frm = tr["frm"] or "(initial)"
        to = "previous_state (H)" if tr["to"] == "H" else tr["to"]
        L.append(f"| {tr['id']} | {frm} | `{tr['event']}` | {to} | {tr['guard']} | {tr['action']} | "
                 f"{', '.join(a.title() for a in tr['actors'])} | {tr['source']} | {tr['frs']} | {tr['es']} | {tr['it']} |")
    L += ["", "**Internal transitions** (state unchanged; the event is still appended with previous_state = new_state)", "",
          "| ID | State | Event type | Guard | Actor | Source | FRs | It. |", "|---|---|---|---|---|---|---|---|"]
    for it in lm.INTERNAL:
        L.append(f"| {it['id']} | {it['state']} | `{it['event']}` | {it['guard']} | "
                 f"{', '.join(a.title() for a in it['actors'])} | {it['source']} | {it['frs']} | {it['it']} |")
    rows = lm.leaf_rows()
    L += ["", f"**Leaf rows:** {len(rows)} valid (state, event type, next state) triples. Every other combination of the "
          f"{len(lm.STATES)} states and {len(lm.EVENTS)} event types ({len(lm.STATES) * len(lm.EVENTS)} pairs) is "
          "invalid and must be rejected and logged (test suite 1, NFR-R-02)."]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"{path}: written")


if __name__ == "__main__":
    lifecycle().save(os.path.join(HERE, "borrowing_lifecycle_state_machine_v3.drawio"))
    write_csv(os.path.join(HERE, "transition_table_v3.csv"))
    write_md(os.path.join(HERE, "transition_table_v3.md"))
