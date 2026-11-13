"""Generates the escalation-case state machine, v3.0 (DA-07, Student 3, iteration 2).

    python generate_escalation_case_state_machine.py   ->  escalation_case_state_machine.drawio

v3.0 adds the build detail for information requests (C02 to C05) and for appeal and reversal (C08 to C11), and
records the item's possession when a dispute is decided (ADR-0009, proposed). v2.0 was drawn by
generate_state_machines.py (A3); this diagram now has its own generator so that the lifecycle state machine
(Student 1, DA-06) and this one can change independently.
Sources: UC-D6, UC-I4, FR-T-10, FR-T-11, ADR-0003, ADR-0004, ADR-0009; sequence diagrams (c), (g) and (h).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import EDGE_BASE, Diagram  # noqa: E402

# actor colours, as in the A3 state machines
C_P, C_M, C_S = "#00796B", "#7B3FA0", "#5F6B76"

ST = ("rounded=1;arcSize=24;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2B3A4A;"
      "fontSize=12;fontColor=#1D1D1D;verticalAlign=middle;")
ST_TERM = ST + "strokeWidth=3;fillColor=#F4F6F8;"
COMPOSITE = ("rounded=1;arcSize=2;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=10;"
             "spacingTop=3;fontStyle=1;fontSize=13;fillColor=#F7F9FC;strokeColor=#7A8A9A;container=1;"
             "collapsible=0;recursiveResize=0;")
INIT = "ellipse;html=1;fillColor=#000000;strokeColor=#000000;"
FINAL = "ellipse;html=1;shape=endState;fillColor=#000000;strokeColor=#000000;"
NOTE = ("shape=note;whiteSpace=wrap;html=1;size=14;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;"
        "fillColor=#FFFDF2;strokeColor=#B8A660;fontSize=10.5;fontColor=#33404D;")
LEGEND = ("rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;"
          "fillColor=#FFFFFF;strokeColor=#9AA5B1;fontSize=10.5;fontColor=#33404D;")


def tr(colour: str, system: bool = False) -> str:
    s = EDGE_BASE + f"strokeColor={colour};fontColor={colour};endArrow=open;endFill=0;strokeWidth=1.6;"
    if system:
        s += "dashed=1;dashPattern=6 3;"
    return s


def state(d, name, x, y, w=200, h=56, style=ST, body="", parent=None):
    label = f"<b>{name}</b>"
    if body:
        label += f"<hr style='margin:3px 0'><span style='font-size:10px'>{body}</span>"
    return d.node(label, x, y, w, h, style, id=name, parent=parent)


def escalation_case() -> Diagram:
    d = Diagram("Escalation case (DA-07)", 1560, 1000)
    d.text("<b>Digital Mohalla &#8212; Escalation case state machine</b> (EscalationCase, DA-07, v3.0, iteration 2)",
           40, 12, 1100, 24, size=16, check=False)
    d.text("Case types: dispute (loan DISPUTED) and non-dispute hold (request HELD_FOR_REVIEW). Sources: UC-D6, UC-I4, "
           "FR-T-10, FR-T-11, ADR-0003, ADR-0004, ADR-0009 (proposed). Transition IDs C01&#8211;C11: "
           "State_Machine_Design.md section 4.", 40, 36, 1400, 20, size=11, color="#4A5560", check=False)

    U = d.node("UNDECIDED", 50, 110, 500, 640, COMPOSITE, id="UNDECIDED")
    d.mark_container(U)
    d.node("", 290, 142, 20, 20, INIT, id="c_init", parent=U)
    state(d, "OPEN", 100, 250, w=400, h=150, parent=U,
          body="entry / assemble the evidence trail from the event log;<br>set trigger type, priority, reason; "
               "assign a moderator<br>of the community (Admin if none, D6 2a); notify<br>"
               "trigger_attached / reuse this case, no duplicate (D6 1b)<br>"
               "escalated_to_admin [unresolvable, or a moderator is<br>a party] / assignee := Admin "
               "(I4 3a, 3b) &nbsp;<b><font color='#0A7A36'>C05</font></b>")
    state(d, "AWAITING_INFORMATION", 100, 610, w=400, h=100, parent=U,
          body="entry / store the question; info_deadline := now +<br>response window (config); notify the "
               "party<br>(sequence g)")

    state(d, "DECIDED", 760, 250, w=320, h=150,
          body="entry / issue one lifecycle command:<br>dispute: dispute_resolved with possession<br>"
               "&nbsp;&nbsp;NOT_HANDED_OVER &#8594; NO_SHOW<br>&nbsp;&nbsp;WITH_BORROWER &#8594; ACTIVE<br>"
               "&nbsp;&nbsp;RETURNED | LOST &#8594; COMPLETED (ADR-0009)<br>"
               "hold: hold_cleared | request_declined; notify parties")
    state(d, "WITHDRAWN", 760, 640, w=280, h=70, style=ST_TERM, body="entry / close without a decision")
    state(d, "APPEALED", 1240, 250, w=270, h=100,
          body="entry / assigned_to := a moderator other<br>than the first decider (Admin if none);<br>"
               "notify the other party (I4 4b)")
    state(d, "REVERSED", 1240, 600, w=270, h=110, style=ST_TERM,
          body="entry / keep both decisions; flag the<br>affected outcomes FLAGGED_FOR_<br>REEVALUATION; "
               "refresh trust edges;<br>notify both parties (ES-11)")
    d.node("", 888, 790, 24, 24, FINAL, id="fin1")
    d.node("", 1363, 790, 24, 24, FINAL, id="fin2")

    E = d.edge
    E("c_init", "OPEN", "case_opened [no open case for this transaction] <b>C01</b><br>trigger &#8712; {dispute, "
      "manipulation_flag, high_value_low_confidence,<br>locality_hold, engine_failure}", style=tr(C_S, True),
      exit=(0.5, 1), entry=(0.5, 0), label_dy=-4, label_w=360)
    E("OPEN", "AWAITING_INFORMATION", "info_requested [assigned<br>moderator; reason]<br>"
      "/ deadline &nbsp;<b>C02</b>", style=tr(C_M), exit=(0.25, 1), entry=(0.25, 0), label_dx=-62)
    E("AWAITING_INFORMATION", "OPEN", "info_received [party to the<br>loan; before the deadline]<br>"
      "/ append statement &nbsp;<b>C03</b>", style=tr(C_P), exit=(0.55, 0), entry=(0.55, 1), label_dx=-8,
      label_dy=-30)
    E("AWAITING_INFORMATION", "OPEN", "deadline_passed [scheduler<br>run_due_jobs] / note no<br>"
      "response &nbsp;<b>C04</b>", style=tr(C_S, True), exit=(0.85, 0), entry=(0.85, 1), label_dx=40,
      label_dy=48)
    E("OPEN", "DECIDED", "decision_recorded [authorised,<br>not a party, reason, allowed<br>for the hold reason (I4 3c);<br>"
      "dispute: possession allowed by<br>the stored previous_state;<br>case still undecided] <b><font color='#0A7A36'>C06</font></b>",
      style=tr(C_M), exit=(1, 0.5), entry=(0, 0.5), label_dy=-62)
    E("UNDECIDED", "WITHDRAWN", "the loan left the trigger state<br>without a decision: dispute_withdrawn,<br>"
      "request_cancelled, request_declined<br>(dates taken) / close &nbsp;<b>C07</b>", style=tr(C_S, True),
      exit=(1, (675 - 110) / 640), entry=(0, 0.5), label_dy=-46)
    E("DECIDED", "APPEALED", "appeal_filed [party, within the<br>appeal window, one appeal<br>per case] <b>C08</b>",
      style=tr(C_P), exit=(1, 0.25), entry=(0, 0.375), label_dy=-30)
    E("APPEALED", "DECIDED", "appeal_decided [upheld; second<br>moderator &#8800; first; reason]<br>"
      "/ APPEAL_UPHELD &nbsp;<b>C09</b>", style=tr(C_M), exit=(0, 0.8), entry=(1, 0.533), label_dy=30)
    E("APPEALED", "REVERSED", "appeal_decided [overturned;<br>same guards] / APPEAL_<br>OVERTURNED &nbsp;"
      "<b>C10</b>", style=tr(C_M), exit=(0.5, 1), entry=(0.5, 0), label_dx=74)
    E("DECIDED", "REVERSED", "decision_reversed [moderator or<br>admin of the community; reason]<br>"
      "/ REVERSAL &nbsp;<b>C11</b>", style=tr(C_M), exit=(0.6, 1), entry=(0, 0.5),
      points=[(952, 520), (1160, 520), (1160, 655)], label_x=-0.1, label_dy=-26)
    E("WITHDRAWN", "fin1", "", style=tr(C_S, True), exit=(0.5, 1), entry=(0.5, 0))
    E("REVERSED", "fin2", "", style=tr(C_S, True), exit=(0.5, 1), entry=(0.5, 0))

    d.node("<b>Why possession is recorded (ADR-0009, review action DM14).</b> A dispute can be raised before "
           "handover, while the item is out, or during the return. Sending every resolved dispute to COMPLETED would "
           "record a return that never happened and release the dates of an item that is not back. The moderator "
           "therefore records where the item is, and only the answers that fit the stored previous state are "
           "offered.", 600, 840, 560, 110, NOTE, check=False)
    d.node("<b>Legend</b><br><span style='color:#00796B'>&#9472;&#9472;&#9658;</span> party &nbsp; "
           "<span style='color:#7B3FA0'>&#9472;&#9472;&#9658;</span> moderator or admin &nbsp; "
           "<span style='color:#5F6B76'>- - &#9658;</span> system or completion<br>event [guard] / effect; "
           "bold border = final state; <font color='#0A7A36'><b>green ID</b> = added or changed in iteration 2 (C05; C06 records possession, ADR-0009)</font>. Case actions are not lifecycle events: each is an audit_log entry and the case "
           "row keeps the status. The decision itself becomes one lifecycle event.", 50, 840, 520, 110, LEGEND,
           check=False)
    return d


if __name__ == "__main__":
    escalation_case().save(os.path.join(HERE, "escalation_case_state_machine.drawio"))
