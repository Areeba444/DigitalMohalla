"""Generates the A3 state-machine diagrams and the transition table (Student 1).

    python generate_state_machines.py

Outputs (next to this file):
    borrowing_lifecycle_state_machine.drawio   UML state machine, BorrowingTransaction (14 states)
    escalation_case_state_machine.drawio       UML state machine, EscalationCase
    transition_table.csv                       leaf-level (state x event -> next state) table = test matrix

States, events and transitions come from ../_tools/lifecycle_model.py (single source of truth).
Edit that file, not the diagrams, when the lifecycle changes; then re-run this script.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))

from drawio import Diagram, EDGE_BASE  # noqa: E402
import lifecycle_model as lm  # noqa: E402

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
    d = Diagram("Borrowing lifecycle (A3)", 1840, 1350)
    d.text("<b>Digital Mohalla &#8212; Borrowing lifecycle state machine</b> (BorrowingTransaction, "
           "design step A3, v2.2)", 40, 12, 1100, 24, size=16, check=False)
    d.text("States and event types: Use Cases v1.3 &#167;2, FR-B-08; HELD_FOR_REVIEW exits ADR-0003; DISPUTED exits "
           "ADR-0004; overlap constraint ADR-0002. Transition IDs = rows of transition_table.csv.",
           40, 36, 1200, 20, size=11, color="#4A5560", check=False)

    # ---------------------------------------------------------------- PENDING composite
    P = d.node("PENDING&nbsp;&nbsp;<span style='font-weight:normal;font-size:11px'>(request not yet agreed; "
               "dates only marked as requested, ADR-0001)</span>", 40, 64, 1360, 496, COMPOSITE, id="PENDING")
    d.mark_container(P)
    d.node("", 225, 108, 20, 20, INIT, id="init", parent=P)
    state(d, "REQUEST_CREATED", 135, 170, parent=P)
    d.node("", 410, 178, 40, 40, CHOICE, id="c_loc", parent=P)
    state(d, "LOCALITY_CHECKED", 600, 170, parent=P)
    d.node("", 930, 178, 40, 40, CHOICE, id="c_assess", parent=P)
    state(d, "ASSESSED", 1150, 170, parent=P, body="lender sees assurance state + evidence")
    d.by_id["ASSESSED"]["h"] = 56
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
      style=tr_style("S"), exit=(1, 0.5), entry=(0, 0.5), label_dy=-20)
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
    E("DISPUTED", "COMPLETED", "dispute_resolved [moderator, reason]<br>/ resolved outcome &#8594; engine "
      "<b>T25</b>", style=tr_style("M"), exit=(0, 0.5), entry=(1, 0.5), label_dy=-18)
    E("DISPUTED", "H", "dispute_withdrawn [raising party]<br>/ restore previous_state <b>T26</b>",
      style=tr_style("P"), exit=(40 / 300, 0), entry=(0.5, 1), label_dx=-112, label_x=-0.15)

    # ---------------------------------------------------------------- legend
    lx, ly = 1180, 1085
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
    notes = ("<b>event [guard] / action</b>; transition IDs T01&#8211;T26 are rows of transition_table.csv.<br>"
             "Bold border = terminal state (no further transitions; record kept).<br>"
             "&#9671; choice pseudostate. <b>H</b> = shallow history of IN_PROGRESS: dispute_withdrawn restores the"
             " previous_state stored in dispute_opened (ADR-0004).<br>"
             "Border arrows apply to every substate of the composite (T23: except RETURNED, team decision D4).<br>"
             "<b>it.2</b> = drawn for completeness, built in iteration 2 (scheduler / extensions); faded.<br>"
             "Lifecycle state &#8800; assurance state: the assurance state is an attribute of the Assessment "
             "(e.g. HELD_FOR_REVIEW with REVIEW_RECOMMENDED, ES-04).")
    d.text(notes, lx + 10, ly + 136, 620, 110, size=9.5, check=False)
    return d


# =============================================================================== escalation case
def escalation_case() -> Diagram:
    d = Diagram("Escalation case (A3)", 1420, 820)
    d.text("<b>Digital Mohalla &#8212; Escalation case state machine</b> (EscalationCase, design step A3, v2.0)",
           40, 12, 1000, 24, size=16, check=False)
    d.text("Case types: dispute (booking DISPUTED) and non-dispute hold (request HELD_FOR_REVIEW). Sources: UC-D6, "
           "UC-I4, FR-T-10, FR-T-11, ADR-0003, ADR-0004.", 40, 36, 1100, 20, size=11, color="#4A5560", check=False)

    U = d.node("UNDECIDED", 60, 120, 420, 520, COMPOSITE, id="UNDECIDED")
    d.mark_container(U)
    d.node("", 260, 152, 20, 20, INIT, id="c_init", parent=U)
    state(d, "OPEN", 110, 240, w=320, h=130, parent=U,
          body="entry / assemble evidence trail from the event log;<br>set trigger type, priority, reason;<br>"
               "assign community moderator (Admin if none, D6 2a); notify<br>"
               "trigger_attached / no duplicate case (D6 1b)<br>"
               "escalated_to_admin [unresolvable | moderator<br>involved] / assignee := Admin (I4 3a, 3b)")
    state(d, "AWAITING_INFORMATION", 110, 520, w=320, h=80, parent=U,
          body="entry / notify parties; set response deadline<br>(I4 step 2; D6 1a missing evidence)")
    state(d, "DECIDED", 700, 244, w=250, h=90,
          body="entry / issue lifecycle command:<br>dispute_resolved | hold_cleared |<br>request_declined; "
               "notify parties")
    state(d, "WITHDRAWN", 700, 525, w=250, h=70, style=ST_TERM,
          body="entry / close without a decision")
    state(d, "APPEALED", 1110, 244, w=240, h=70, body="second moderator reviews (I4 4b)")
    state(d, "REVERSED", 1110, 515, w=240, h=90, style=ST_TERM,
          body="entry / keep both decisions; flag<br>affected outcomes for re-evaluation<br>(I4 4c, ES-11)")
    d.node("", 813, 650, 24, 24, FINAL, id="fin1")
    d.node("", 1218, 650, 24, 24, FINAL, id="fin2")

    E = d.edge
    E("c_init", "OPEN", "case_opened [no open case for this transaction] <b>C01</b><br>trigger &#8712; {dispute, manipulation_flag,"
      "<br>high_value_low_confidence, locality_hold, engine_failure}", style=tr_style("S"), exit=(0.5, 1),
      entry=(0.5, 0), label_dx=0, label_dy=-2, label_w=330)
    E("OPEN", "AWAITING_INFORMATION", "info_requested [assigned<br>moderator] / deadline &nbsp;<b>C02</b>",
      style=tr_style("M"), exit=(0.3, 1), entry=(0.3, 0), label_dx=-50)
    E("AWAITING_INFORMATION", "OPEN", "info_received [party]<br>| deadline_passed / note<br>non-response "
      "(I4 2a) <b>C03, C04</b>", style=tr_style("P"), exit=(0.75, 0), entry=(0.75, 1), label_dx=45)
    E("OPEN", "DECIDED", "decision_recorded [authorised,<br>not a party, reason, allowed<br>for hold reason (I4 3c),"
      "<br>case still undecided (I4 4a)] <b>C06</b>", style=tr_style("M"), exit=(1, 0.38), entry=(0, 0.5),
      label_dy=-48)
    E("UNDECIDED", "WITHDRAWN", "lifecycle left the trigger state<br>without a decision: dispute_withdrawn,"
      "<br>request_cancelled, request_declined<br>(dates taken) / case_withdrawn <b>C07</b>",
      style=tr_style("S"), exit=(1, (560 - 120) / 520), entry=(0, 0.5), label_dy=-44)
    E("DECIDED", "APPEALED", "appeal_filed [party, in window]<br><b>C08</b> it.2", style=tr_style("P", True),
      exit=(1, 0.3), entry=(0, 27 / 70), label_dy=-20)
    E("APPEALED", "DECIDED", "appeal_decided [upheld; second<br>moderator &#8800; first] <b>C09</b> it.2",
      style=tr_style("M", True), exit=(0, 0.75), entry=(1, 52.5 / 90), label_dy=20)
    E("APPEALED", "REVERSED", "appeal_decided<br>[overturned]<br><b>C10</b> it.2", style=tr_style("M", True),
      exit=(0.5, 1), entry=(0.5, 0), label_dx=50)
    E("DECIDED", "REVERSED", "decision_reversed<br>[authorised, reason]<br><b>C11</b> it.2",
      style=tr_style("M", True), exit=(0.6, 1), entry=(0, 0.5), points=[(850, 470), (1030, 470), (1030, 560)], label_x=-0.12, label_dy=-26)
    E("WITHDRAWN", "fin1", "", style=tr_style("S"), exit=(0.5, 1), entry=(0.5, 0))
    E("REVERSED", "fin2", "", style=tr_style("S"), exit=(0.5, 1), entry=(0.5, 0))

    d.text("Case actions are not lifecycle event types: each is written to the hash-chained audit_log (FR-M-05) and "
           "the case row keeps the current status. The decision itself becomes a lifecycle event (C06 &#8594; "
           "dispute_resolved T25, hold_cleared T09&#8211;T11 or request_declined T12). <b>it.2</b>: appeal and "
           "reversal are designed here but built in iteration 2 (Iteration 1 plan, Module 9).",
           60, 700, 1260, 40, size=10.5, color="#33404D", check=False)
    return d


# =============================================================================== transition table
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
    L = ["# Borrowing lifecycle: transition table (A3)", "",
         "Generated by `generate_state_machines.py` from `_tools/lifecycle_model.py`; do not edit by hand. "
         "Border transitions (from PENDING / IN_PROGRESS) and the history return (H) are listed once here and "
         "expanded to leaf rows in `transition_table.csv` and in `allowed_transition` (schema.sql).", "",
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
    lifecycle().save(os.path.join(HERE, "borrowing_lifecycle_state_machine.drawio"))
    escalation_case().save(os.path.join(HERE, "escalation_case_state_machine.drawio"))
    write_csv(os.path.join(HERE, "transition_table.csv"))
    write_md(os.path.join(HERE, "transition_table.md"))
