"""Generates membership_decision_activity_diagram.drawio: joining a community, from the locality check to the
moderator's decision, as a UML 2.5 activity diagram (DA-13, Student 3, iteration 2).

    python generate_membership_decision_activity.py

Same notation as the decision-policy activity diagram: decision nodes carry no text and every outgoing edge has a
guard; alternative flows meet in explicit merge nodes; partitions are the actors and the system part that act.
Sources: UC-A3, UC-A4, FR-A-07 to FR-A-11, Locality_Design_A11.md (decision table and test cases),
membership_state_machine.drawio (M01 to M05).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import EDGE_BASE, Diagram  # noqa: E402

LANE = ("swimlane;html=1;startSize=34;horizontal=1;fillColor=#F4F6F8;swimlaneFillColor=#FFFFFF;strokeColor=#5F6B76;"
        "fontStyle=1;fontSize=12;")
ACTION = ("rounded=1;arcSize=24;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FFFFFF;strokeColor=#33404D;"
          "spacing=4;")
OUTCOME = {"VER": "#E3F4E3", "INC": "#FFF6D6", "CON": "#FDE3E0", "ERR": "#F2F2F2"}
DECISION = "rhombus;html=1;fillColor=#FFFFFF;strokeColor=#33404D;"
INITIAL = "ellipse;html=1;fillColor=#1D1D1D;strokeColor=#1D1D1D;"
FINAL = "ellipse;shape=endState;html=1;fillColor=#1D1D1D;strokeColor=#1D1D1D;"
FLOW = EDGE_BASE + "endArrow=open;endFill=0;strokeColor=#1D1D1D;fontSize=10.5;"
NOTE = ("shape=note;whiteSpace=wrap;html=1;size=14;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;"
        "fillColor=#FFFDF2;strokeColor=#B8A660;fontSize=10.5;fontColor=#33404D;")


def build() -> Diagram:
    d = Diagram("Membership decision activity (DA-13)", 1500, 1720)
    d.text("<b>Digital Mohalla &#8212; Joining a community: locality check and membership decision (UML activity "
           "diagram)</b> &#8212; DA-13, Student 3, v1.1 draft (iteration 2)", 30, 10, 1400, 24, size=15, check=False)
    d.text("Locality rule from Locality_Design_A11.md (geofence + invitation, moderator for anything uncertain). "
           "Membership states M01&#8211;M05, M09: membership_state_machine.drawio. No outcome is ever an automatic "
           "rejection (FR-A-08); only a VERIFIED result in an OPEN community is approved without a moderator (UC-A3 4a).", 30, 34, 1400, 20, size=11, color="#4A5560", check=False)
    top, h = 64, 1620
    for x, w, name in ((30, 300, "Applicant (member)"),
                       (330, 640, "System: membership and locality (M1)"),
                       (970, 500, "Moderator of the community (M9)")):
        lid = d.node(name, x, top, w, h, LANE, check=False)
        d.mark_container(lid, pass_through=True)

    n = {}
    A = lambda key, label, x, y, w, h, fill="#FFFFFF": n.__setitem__(  # noqa: E731
        key, d.node(label, x, y, w, h, ACTION + f"fillColor={fill};"))
    D = lambda key, x, y: n.__setitem__(key, d.node("", x, y, 40, 40, DECISION))  # noqa: E731
    E = lambda a, b, label="", **kw: d.edge(n[a], n[b], label, style=FLOW, **kw)  # noqa: E731

    # ---------------------------------------------------------------- applicant
    n["init"] = d.node("", 165, 110, 30, 30, INITIAL)
    A("choose", "Open <i>Join a community</i>; choose a community; read its rules and methods", 80, 160, 200, 60)
    D("m_retry", 160, 250)
    A("give", "Allow one coarse location fix (optional) and enter an invitation code (optional)", 80, 320, 200, 64)

    # ---------------------------------------------------------------- system: locality
    A("eval", "Evaluate the fix against the community's coarse boundary and the invitation in memory (A11 rule); "
      "discard the coordinates", 520, 316, 250, 72)
    D("d_code", 625, 420)
    A("err", "Show an error; no request is created", 360, 412, 150, 56, OUTCOME["ERR"])
    D("d_out", 625, 520)
    A("con", "Outcome CONFLICTING, flagged for the moderator", 360, 600, 190, 60, OUTCOME["CON"])
    A("inc", "Outcome INCONCLUSIVE", 565, 600, 160, 60, OUTCOME["INC"])
    A("ver", "Outcome VERIFIED", 760, 600, 180, 60, OUTCOME["VER"])
    D("m_out", 625, 720)
    D("d_dup", 625, 800)
    A("dup", "Show the existing request or membership; nothing new is created (UC-A3 4b)", 345, 790, 170, 64)
    n["f_dup"] = d.node("", 417, 890, 26, 26, FINAL)
    A("store", "Store only the coarse outcome and flags; create the request PENDING (M01); notify the community's "
      "moderators", 520, 880, 250, 76)

    D("d_open", 850, 898)
    A("auto", "APPROVED by the system: role MEMBER, decided_at, audit entry; moderators notified (M09)", 770, 980,
      190, 76, OUTCOME["VER"])
    n["f_auto"] = d.node("", 852, 1090, 26, 26, FINAL)

    # ---------------------------------------------------------------- moderator
    D("m_queue", 1150, 898)
    A("open", "Open the request from the queue (own community only): coarse outcome, flags, minimal profile",
      1060, 980, 220, 64)
    D("d_ev", 1150, 1080)
    A("ask", "Request information with a reason; a deadline is set (M02)", 1300, 1072, 150, 56)
    A("wait", "Wait for the applicant's answer, or the deadline, then &#8220;no response&#8221; is noted (M03)",
      1300, 960, 150, 76)
    D("m_dec", 1150, 1170)
    A("decide", "Choose approve or reject and enter a reason", 1070, 1240, 200, 50)
    D("d_reason", 1150, 1330)

    # ---------------------------------------------------------------- system: apply
    D("d_live", 625, 1330)
    A("cur", "Show the current status; apply nothing (UC-A4 4a, 4c)", 360, 1410, 190, 56)
    n["f_cur"] = d.node("", 442, 1500, 26, 26, FINAL)
    D("d_kind", 625, 1430)
    A("appr", "APPROVED: role MEMBER, decided_at, audit entry, applicant notified (M04)", 720, 1500, 230, 64,
      OUTCOME["VER"])
    A("rej", "REJECTED: reason, decided_at, audit entry, applicant notified (M05)", 520, 1500, 180, 64)
    n["f_appr"] = d.node("", 822, 1610, 26, 26, FINAL)
    n["f_rej"] = d.node("", 597, 1610, 26, 26, FINAL)

    # ---------------------------------------------------------------- flows
    E("init", "choose", exit=(0.5, 1), entry=(0.5, 0))
    E("choose", "m_retry", exit=(0.5, 1), entry=(0.5, 0))
    E("m_retry", "give", exit=(0.5, 1), entry=(0.5, 0))
    E("give", "eval", exit=(1, 0.5), entry=(0, 0.5))
    E("eval", "d_code", exit=(0.5, 1), entry=(0.5, 0))
    E("d_code", "err", "[code invalid, expired,<br>used or for another<br>community]", exit=(0, 0.5), entry=(1, 0.5),
      label_dy=-32)
    E("err", "m_retry", "", exit=(0, 0.5), entry=(1, 0.5), points=[(305, 440), (305, 270)])
    E("d_code", "d_out", "[code valid, or none given]", exit=(0.5, 1), entry=(0.5, 0), label_dx=80)
    E("d_out", "con", "[mock location, duplicate-account<br>signal, or fix outside]", exit=(0, 0.5), entry=(0.5, 0),
      points=[(455, 540)], label_dx=-20, label_dy=-22, label_x=-0.3)
    E("d_out", "inc", "[otherwise: weak fix, near the<br>edge, permission refused or<br>no invitation]",
      exit=(0.5, 1), entry=(0.5, 0), label_dx=0, label_dy=0)
    E("d_out", "ver", "[fix inside and a<br>valid invitation]", exit=(1, 0.5), entry=(0.5, 0), points=[(850, 540)],
      label_dy=-20, label_x=-0.3)
    E("con", "m_out", exit=(0.5, 1), entry=(0, 0.5), points=[(455, 740)])
    E("inc", "m_out", exit=(0.5, 1), entry=(0.5, 0))
    E("ver", "m_out", exit=(0.5, 1), entry=(1, 0.5), points=[(850, 740)])
    E("m_out", "d_dup", exit=(0.5, 1), entry=(0.5, 0))
    E("d_dup", "dup", "[a live request or<br>membership exists]", exit=(0, 0.5), entry=(1, 0.5), label_dy=-24)
    E("dup", "f_dup", exit=(0.5, 1), entry=(0.5, 0))
    E("d_dup", "store", "[none]", exit=(0.5, 1), entry=(0.5, 0), label_dx=24)
    E("store", "d_open", "", exit=(1, 0.5), entry=(0, 0.5))
    E("d_open", "m_queue", "[otherwise]", exit=(1, 0.5), entry=(0, 0.5), label_dy=-12)
    E("d_open", "auto", "[OPEN community and<br>outcome VERIFIED]", exit=(0.5, 1), entry=(0.5, 0), label_dx=62)
    E("auto", "f_auto", exit=(0.5, 1), entry=(0.5, 0))
    E("m_queue", "open", exit=(0.5, 1), entry=(0.5, 0))
    E("open", "d_ev", exit=(0.5, 1), entry=(0.5, 0))
    E("d_ev", "ask", "[evidence<br>insufficient (2a)]", exit=(1, 0.5), entry=(0, 0.5), label_dy=-22)
    E("ask", "wait", exit=(0.5, 0), entry=(0.5, 1))
    E("wait", "m_queue", exit=(0.5, 0), entry=(1, 0.5), points=[(1375, 918)])
    E("d_ev", "m_dec", "[enough evidence]", exit=(0.5, 1), entry=(0.5, 0), label_dx=-62)
    E("m_dec", "decide", exit=(0.5, 1), entry=(0.5, 0))
    E("decide", "d_reason", exit=(0.5, 1), entry=(0.5, 0))
    E("d_reason", "m_dec", "[reason missing (3a)]", exit=(1, 0.5), entry=(1, 0.5),
      points=[(1300, 1350), (1300, 1190)], label_dx=48, label_dy=0, label_x=0.0)
    E("d_reason", "d_live", "[reason given]", exit=(0, 0.5), entry=(1, 0.5), label_dy=-10)
    E("d_live", "cur", "[another moderator decided<br>first, or the applicant<br>withdrew]", exit=(0, 0.5),
      entry=(0.5, 0), points=[(455, 1350)], label_dx=-10, label_dy=-26, label_x=-0.4)
    E("cur", "f_cur", exit=(0.5, 1), entry=(0.5, 0))
    E("d_live", "d_kind", "[still undecided]", exit=(0.5, 1), entry=(0.5, 0), label_dx=50)
    E("d_kind", "appr", "[approve]", exit=(1, 0.5), entry=(0.5, 0), points=[(835, 1450)], label_dy=-10)
    E("d_kind", "rej", "[reject]", exit=(0.5, 1), entry=(0.5, 0), points=[(645, 1480), (610, 1480)], label_dx=30)
    E("appr", "f_appr", exit=(0.5, 1), entry=(0.5, 0))
    E("rej", "f_rej", exit=(0.5, 1), entry=(0.5, 0))

    d.node("<b>Why this flow</b><br>The locality check produces evidence, never a verdict: every outcome creates a "
           "request for a human, except a VERIFIED result in a community whose join policy is OPEN (schema v2.4). Only an unusable invitation code stops the flow, and the applicant can "
           "retry. The decision is applied only while the request is still undecided, so a second moderator or a "
           "withdrawal cannot be overwritten. The applicant's answer to an information request is drawn in sequence "
           "(g) and SSD-A4.", 40, 1430, 280, 210, NOTE, check=False)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "membership_decision_activity_diagram.drawio"))
