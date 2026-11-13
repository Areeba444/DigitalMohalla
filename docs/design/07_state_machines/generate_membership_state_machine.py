"""Generates the membership state machine (DA-08, Student 3, iteration 2).

    python generate_membership_state_machine.py

Output (next to this file):
    membership_state_machine.drawio    UML state machine, Membership (the six membership_status values)

Sources: schema v2.3 (`membership_status`, `membership_decided_ck`, `membership_one_live_uq`), UC-A3, UC-A4,
FR-A-08 to FR-A-11, FR-M-01, the A11 locality design. Edit this file, not the diagram, then re-run it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))

from drawio import EDGE_BASE, Diagram  # noqa: E402

# actor colours, as in the A3 state machines: member (applicant) blue, moderator/admin purple, system grey
C_A, C_M, C_S = "#1F5FA8", "#7B3FA0", "#5F6B76"

ST = ("rounded=1;arcSize=24;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2B3A4A;"
      "fontSize=12;fontColor=#1D1D1D;verticalAlign=middle;")
ST_LIVE = ST + "fillColor=#EAF2FB;strokeColor=#1F5FA8;strokeWidth=2.5;"  # not green: green means added in iteration 2
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


def state(d, name, x, y, w=220, h=56, style=ST, body="", parent=None):
    label = f"<b>{name}</b>"
    if body:
        label += f"<hr style='margin:3px 0'><span style='font-size:10px'>{body}</span>"
    return d.node(label, x, y, w, h, style, id=name, parent=parent)


def membership() -> Diagram:
    d = Diagram("Membership (DA-08)", 1500, 940)
    d.text("<b>Digital Mohalla &#8212; Membership state machine</b> (Membership, design artefact DA-08, v1.1, "
           "iteration 2)", 40, 12, 1100, 24, size=16, check=False)
    d.text("States are the six values of <i>membership_status</i> (schema v2.3). Sources: UC-A3, UC-A4, FR-A-08 to "
           "FR-A-11, FR-M-01, locality design A11, schema v2.4 (community.join_policy). Transition IDs M01&#8211;M09 are "
           "rows of the table in "
           "Membership_State_Machine.md.", 40, 36, 1300, 20, size=11, color="#4A5560", check=False)

    # undecided requests: decided_at IS NULL (membership_decided_ck)
    U = d.node("UNDECIDED &nbsp;<span style='font-weight:normal;font-size:11px'>(request open, decided_at is "
               "null)</span>", 40, 110, 470, 560, COMPOSITE, id="UNDECIDED")
    d.mark_container(U)
    d.node("", 255, 145, 20, 20, INIT, id="m_init", parent=U)
    state(d, "PENDING", 90, 255, w=370, h=118, parent=U,
          body="entry / store the coarse locality result only:<br>VERIFIED, INCONCLUSIVE or CONFLICTING (A11);<br>"
               "attach duplicate-account and mismatch flags;<br>notify the community's moderators<br>"
               "do / wait in the moderator queue (UC-A4 step 1)")
    state(d, "AWAITING_INFORMATION", 90, 540, w=370, h=90, parent=U,
          body="entry / notify the applicant; set the response<br>deadline (window in config, DA-03)<br>"
               "(UC-A4 2a)")

    state(d, "APPROVED", 760, 150, w=300, h=126, style=ST_LIVE,
          body="entry / role := MEMBER; decided_at := now;<br>audit entry; notify the applicant;<br>"
               "MODERATOR_APPROVAL locality result if<br>the outcome was not VERIFIED (A11)<br>"
               "The member can now borrow in this<br>community (txn_guard_create, G1)")
    state(d, "REJECTED", 760, 430, w=300, h=80,
          body="entry / reason recorded; audit entry;<br>notify the applicant")
    state(d, "WITHDRAWN", 760, 640, w=300, h=60, style=ST_TERM,
          body="entry / close the request")
    state(d, "REVOKED", 1220, 150, w=250, h=96, style=ST_TERM,
          body="entry / reason recorded; audit entry;<br>open loans are routed to a<br>moderator (FR-M-01)")
    d.node("", 898, 760, 24, 24, FINAL, id="fin_w")
    d.node("", 1333, 330, 24, 24, FINAL, id="fin_r")

    E = d.edge
    E("m_init", "PENDING", "join_requested [contact verified; no live membership<br>in this community; community "
      "active; invitation<br>code valid] / one coarse GPS check and the invitation<br>evaluated in memory; "
      "coordinates discarded &nbsp;<b>M01</b>", style=tr(C_A), exit=(0.5, 1), entry=(0.5, 0), label_dy=-4,
      label_w=310)
    E("PENDING", "AWAITING_INFORMATION", "info_requested [moderator of<br>this community; reason]<br>"
      "/ deadline &nbsp;<b>M02</b>", style=tr(C_M), exit=(0.25, 1), entry=(0.25, 0), label_dx=-52)
    E("AWAITING_INFORMATION", "PENDING", "info_provided [applicant]<br>| deadline_passed / note<br>"
      "no response &nbsp;<b>M03</b>", style=tr(C_A), exit=(0.75, 0), entry=(0.75, 1), label_dx=62)
    E("UNDECIDED", "APPROVED", "approved [moderator of this community, not the<br>applicant; reason; applicant "
      "active (A4 4c);<br>still undecided (A4 4a)] &nbsp;<b>M04</b>", style=tr(C_M), exit=(1, (205 - 110) / 560),
      entry=(0, 55 / 110), label_dy=-34)
    E("UNDECIDED", "REJECTED", "rejected [same guards; reason].<br>An INCONCLUSIVE or CONFLICTING<br>result never "
      "rejects by itself<br>(FR-A-08) &nbsp;<b>M05</b>", style=tr(C_M), exit=(1, (470 - 110) / 560),
      entry=(0, 0.5), label_dy=-38)
    E("UNDECIDED", "WITHDRAWN", "withdrawn [applicant]<br>/ decided_at := now &nbsp;<b>M06</b>", style=tr(C_A),
      exit=(1, (670 - 110) / 560), entry=(0, 0.5), points=[(640, 670)], label_dx=0, label_dy=-20, label_x=0.4)
    E("APPROVED", "REVOKED", "revoked [moderator<br>of this community<br>or admin; reason] <b>M07</b>",
      style=tr(C_M), exit=(1, 0.36), entry=(0, 40 / 96), label_dy=-30)
    E("REJECTED", "APPROVED", "decision_reversed [another moderator<br>or admin; reason] / both decisions<br>"
      "kept in the log (FR-A-11) &nbsp;<b>M08</b>", style=tr(C_M), exit=(0.5, 0), entry=(0.5, 1), label_dx=128)
    E("PENDING", "APPROVED", "auto_approved [join_policy = OPEN;<br>locality outcome VERIFIED] / role := MEMBER;"
      "<br>notify the moderators (UC-A3 4a) &nbsp;<b>M09</b>", style=tr(C_S, True), exit=(1, 45 / 118),
      entry=(0, 100 / 126), points=[(700, 300), (700, 250)], label_x=-0.3, label_dy=40)
    E("WITHDRAWN", "fin_w", "", style=tr(C_S, True), exit=(0.5, 1), entry=(0.5, 0))
    E("REVOKED", "fin_r", "", style=tr(C_S, True), exit=(0.5, 1), entry=(0.5, 0))

    d.node("<b>Database rules this machine relies on</b><br>&#8226; <i>membership_decided_ck</i>: decided_at is "
           "null exactly while the status is PENDING or<br>&nbsp;&nbsp;AWAITING_INFORMATION, so every exit from "
           "UNDECIDED sets it.<br>&#8226; <i>membership_one_live_uq</i>: at most one PENDING, AWAITING_INFORMATION "
           "or APPROVED<br>&nbsp;&nbsp;row per user and community (UC-A3 4b). A rejected, withdrawn or revoked "
           "applicant<br>&nbsp;&nbsp;may apply again: that is a new row and a new M01 (UC-A4 4d).<br>"
           "&#8226; No column stores coordinates or an address (NFR-PR-01); locality_verification keeps<br>"
           "&nbsp;&nbsp;only the coarse outcome and signal.", 1100, 430, 380, 200, NOTE, id="note_db")
    d.node("<b>Open points (to settle in DA-03 / decision record)</b><br>&#8226; Open-join communities "
           "(UC-A3 4a, issue I-10): settled by schema v2.4,<br>&nbsp;&nbsp;community.join_policy; only a VERIFIED "
           "result is approved by itself (M09).<br>&#8226; Response deadline value for M02/M03 (DA-03).<br>"
           "&#8226; Granting the MODERATOR role is an admin action (FR-M-01), not part of this machine.",
           1100, 650, 380, 120, NOTE, id="note_open")
    d.node("<b>Legend</b><br><span style='color:#1F5FA8'>&#9472;&#9472;&#9658;</span> applicant (member) &nbsp; "
           "<span style='color:#7B3FA0'>&#9472;&#9472;&#9658;</span> moderator or admin &nbsp; "
           "<span style='color:#5F6B76'>- - &#9658;</span> system or completion<br>"
           "event [guard] / effect; blue border = live membership; bold border = final state.<br>"
           "Membership changes are not lifecycle events: each one is an audit_log entry (FR-M-05).",
           40, 820, 700, 72, LEGEND, id="legend")
    return d


if __name__ == "__main__":
    membership().save(os.path.join(HERE, "membership_state_machine.drawio"))
