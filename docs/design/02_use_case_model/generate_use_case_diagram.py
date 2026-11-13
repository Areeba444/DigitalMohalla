"""Generates use_case_diagram.drawio: the use case diagram at iteration 2 (A9 v0.3 core + DA-02, owner Student 3).

    python generate_use_case_diagram.py

Cumulative: the iteration 1 core use cases plus the ten built in iteration 2 (green border). The iteration 1 version is
archive_v1/use_case_diagram_iteration1.drawio.
v0.3 redrew Student 3's v0.2 in standard UML 2.5 notation with the same use cases and relationships:
  * actors are outside the system boundary only; the Trust Engine is a component of the system, so it is not an
    actor (D3/4/5 is reached through B5's «include», D6 through B12's «include» and D3/4/5's «extend»);
  * «include» and «extend» are dashed arrows with open heads; «extend» points from the extending to the base use
    case, and the base use case lists its extension points;
  * generalisation (Borrower, Lender → Booking party → Member) uses a hollow triangle; associations are plain lines.
Iteration 2 adds the Guest and Member actors and the Scheduler (the external timer of UC-B13, ADR-0012).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

UC = {"M1": ("#E1D5E7", "#9673A6"), "M3": ("#DAE8FC", "#6C8EBF"), "M4": ("#F5F5F5", "#666666"),
      "M5": ("#D5E8D4", "#82B366"), "M7": ("#FFF2CC", "#B09030"), "M9": ("#FFE6CC", "#D79B00")}
NEW_INK = "#0A7A36"     # shared convention: added in iteration 2
ACTOR = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontStyle=1;fontSize=11;"
ASSOC = EDGE_BASE + "endArrow=none;strokeColor=#33404D;"
DEP = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#33404D;fontSize=10;"
GEN = EDGE_BASE + "endArrow=block;endFill=0;endSize=12;strokeColor=#33404D;"
W, H = 230, 64
COL_A, COL_B, COL_C = 340, 710, 1090


def uc(d, text, x, y, mod, w=W, h=H, new=False):
    fill, line = UC[mod]
    if new:
        text += f"<br><i style='font-size:9.5px;color:{NEW_INK}'>iteration 2</i>"
        stroke = f"strokeColor={NEW_INK};strokeWidth=2.5;"
    else:
        stroke = f"strokeColor={line};"
    return d.node(text, x, y, w, h, f"ellipse;whiteSpace=wrap;html=1;fillColor={fill};{stroke}fontSize=11;")


def build():
    d = Diagram("Use case diagram (A9, iteration 2)", 1700, 1500)
    d.text("<b>Digital Mohalla: use case diagram, iteration 2</b> &#8212; design step A9 v0.3 (iteration 1 core) and "
           "DA-02 v1.0 (iteration 2) &#183; Use Cases v1.4, FR/NFR v1.4", 30, 12, 1600, 22, size=14, check=False)
    d.text("The use cases built by the end of iteration 2 (Use Cases §3). <font color='#0A7A36'>Green border = added in "
           "iteration 2</font>. Iteration 1 version: archive_v1/use_case_diagram_iteration1.drawio.",
           30, 36, 1600, 20, size=11, color="#4A5560", check=False)
    sysb = d.node("<b>Digital Mohalla</b> (iteration 1 core + iteration 2)", 300, 80, 1180, 1250,
                  "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#1D1D1D;verticalAlign=top;align=left;"
                  "spacingLeft=10;spacingTop=6;fontSize=12;")
    d.mark_container(sysb, pass_through=True)
    a1 = uc(d, "A1 Register", COL_A, 110, "M1", new=True)
    b3 = uc(d, "B3 Search for items", COL_A, 200, "M4", new=True)
    b4 = uc(d, "B4 View item details and lender evidence", COL_A, 290, "M4", new=True)
    b5 = uc(d, "B5 Send borrowing request", COL_A, 380, "M3")
    b1 = uc(d, "B1 Create item listing", COL_A, 470, "M3", new=True)
    b6 = uc(d, "B6 Respond to request<br><i style='font-size:9.5px'>incl. counter-offer (ext 3b, it. 2)</i>", COL_A, 560,
            "M3")
    b7 = uc(d, "B7 Confirm handover<br><i style='font-size:9.5px'>extension points: condition disputed (step 3)</i>",
            COL_A, 650, "M3", h=80)
    b8 = uc(d, "B8 Return item and complete<br><i style='font-size:9.5px'>extension points: damage or disagreement "
               "(step 3)</i>", COL_A, 760, "M3", h=80)
    b12 = uc(d, "B12 Raise dispute", COL_A, 870, "M3")
    d1 = uc(d, "D1 Submit review and rating", COL_A, 960, "M5", new=True)
    a3 = uc(d, "A3 Request community membership", COL_A, 1050, "M1", new=True)
    d2 = uc(d, "D2 View my evidence", COL_A, 1140, "M5", new=True)
    g3 = uc(d, "G3 Receive in-app notifications", COL_A, 1230, "M7", new=True)
    d3 = uc(d, "D3/4/5 Assess transaction assurance<br><i style='font-size:9.5px'>extension points: manipulation "
               "risk (step 4)</i>", COL_B, 370, "M5", h=90)
    d6 = uc(d, "D6 Escalate case with evidence trail", COL_B, 560, "M5")
    a4 = uc(d, "A4 Approve or reject membership", COL_C, 110, "M1", new=True)
    i4 = uc(d, "I4 Resolve escalated case or dispute", COL_C, 560, "M9")
    i6 = uc(d, "I6 View audit logs", COL_C, 700, "M9")
    b13 = uc(d, "B13 Run scheduled jobs", COL_C, 870, "M3", new=True)

    guest = d.node("Guest", 145, 110, 30, 60, ACTOR)
    bor = d.node("Borrower", 145, 290, 30, 60, ACTOR)
    lend = d.node("Lender", 145, 560, 30, 60, ACTOR)
    party = d.node("<i>Booking party</i><br>{abstract}", 145, 880, 30, 60, ACTOR)
    member = d.node("Member", 145, 1130, 30, 60, ACTOR)
    mod = d.node("Moderator", 1580, 320, 30, 60, ACTOR)
    adm = d.node("Admin", 1580, 640, 30, 60, ACTOR)
    sch = d.node("Scheduler<br><span style='font-weight:normal'>(timer, ADR-0012)</span>", 1580, 870, 30, 60, ACTOR)

    E = d.edge
    # associations
    E(guest, a1, "", style=ASSOC, exit=(1, 0.5), entry=(0, 0.5))
    for u, f in ((b3, 0.3), (b4, 0.5), (b5, 0.7)):
        E(bor, u, "", style=ASSOC, exit=(1, f), entry=(0, 0.5))
    E(bor, b8, "", style=ASSOC, exit=(1, 0.9), entry=(0, 0.35))
    for u, f in ((b1, 0.3), (b6, 0.5), (b7, 0.7)):
        E(lend, u, "", style=ASSOC, exit=(1, f), entry=(0, 0.5))
    E(party, b12, "", style=ASSOC, exit=(1, 0.3), entry=(0, 0.6))
    E(party, d1, "", style=ASSOC, exit=(1, 0.7), entry=(0, 0.4))
    for u, f in ((a3, 0.2), (d2, 0.5), (g3, 0.8)):
        E(member, u, "", style=ASSOC, exit=(1, f), entry=(0, 0.5))
    E(mod, a4, "", style=ASSOC, exit=(0, 0.3), entry=(1, 0.5))
    E(mod, i4, "", style=ASSOC, exit=(0, 0.7), entry=(1, 0.3))
    E(adm, i4, "", style=ASSOC, exit=(0, 0.3), entry=(1, 0.7))
    E(adm, i6, "", style=ASSOC, exit=(0, 0.7), entry=(1, 0.5))
    E(sch, b13, "", style=ASSOC, exit=(0, 0.5), entry=(1, 0.5))
    # generalisation: Borrower and Lender are Booking parties; every Booking party is a Member
    E(bor, party, "", style=GEN, exit=(0, 0.5), entry=(0, 0.3), points=[(110, 320), (110, 898)], check=False)
    E(lend, party, "", style=GEN, exit=(0, 0.7), entry=(0, 0.6), points=[(124, 602), (124, 916)], check=False)
    E(party, member, "", style=GEN, exit=(0.5, 1), entry=(0.5, 0), check=False)
    # include / extend
    E(b5, d3, "&#171;include&#187;", style=DEP, exit=(1, 0.5), entry=(0, 0.6), label_dy=-9)
    E(b12, d6, "&#171;include&#187;", style=DEP, exit=(1, 0.3), entry=(0, 0.7), points=[(680, 889), (680, 605)], label_x=0.1, label_dx=36)
    E(d6, d3, "&#171;extend&#187;<br>[corroborated risk &#8805; 60, level 4]", style=DEP, exit=(0.5, 0),
      entry=(0.5, 1), label_dx=118)
    E(b12, b8, "&#171;extend&#187; [damage /<br>disagreement]", style=DEP, exit=(0.5, 0), entry=(0.5, 1),
      label_dx=-2)
    E(b12, b7, "&#171;extend&#187;<br>[condition disputed]", style=DEP, exit=(1, 0.5), entry=(1, 0.5),
      points=[(650, 902), (650, 690)], label_x=0.5, label_dx=56)

    d.node("<b>Notation (UML 2.5).</b> Stick figure = actor outside the system; ellipse = use case; box = system "
           "boundary; plain line = association; hollow triangle = generalisation (Borrower and Lender are Booking "
           "parties, the primary actor of B12 and D1; every Booking party is a Member); dashed open arrow = "
           "&#171;include&#187; (always happens: B5 step 5, B12 step 4) or &#171;extend&#187; (conditional, from the "
           "extending use case to the base use case's extension point: B7 ext 3a, B8 ext 3a, D3/4/5 ext 4a).<br>"
           "<b>Not actors:</b> the Trust Engine (Module 5) is part of the system. The Scheduler is the external timer "
           "that calls the job endpoint (UC-B13, ADR-0012); B13 carries out B6 *b (expiry), B7 *a (no-show) and B8 *a "
           "(overdue dispute) inside those use cases. D6 hands a case to I4 at D6 step 3 (no UML relationship). Colour "
           "= module: purple 1, blue 3, grey 4, green 5, yellow 7, orange 9.", 30, 1350, 1640, 110,
           "shape=note;size=12;whiteSpace=wrap;html=1;fontSize=10.5;align=left;verticalAlign=top;spacingLeft=8;"
           "spacingTop=4;fillColor=#F4F6F8;strokeColor=#8C99A6;", check=False)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "use_case_diagram.drawio"))
