"""Generates use_case_diagram.drawio: the iteration-1 core use case diagram (design step A9, owner Student 3).

    python generate_use_case_diagram.py

v0.3 redraws Student 3's v0.2 in standard UML 2.5 notation with the same use cases and relationships:
  * actors are outside the system boundary only; the Trust Engine is a component of the system, so it is not an
    actor (D3/4/5 is reached through B5's «include», D6 through B12's «include» and D3/4/5's «extend»);
  * «include» and «extend» are dashed arrows with open heads; «extend» points from the extending to the base use
    case, and the base use case lists its extension points;
  * generalisation (Borrower, Lender → Booking party) uses a hollow triangle; associations are plain lines.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

UC = {"M3": ("#DAE8FC", "#6C8EBF"), "M5": ("#D5E8D4", "#82B366"), "M9": ("#FFE6CC", "#D79B00")}
ACTOR = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontStyle=1;fontSize=11;"
ASSOC = EDGE_BASE + "endArrow=none;strokeColor=#33404D;"
DEP = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#33404D;fontSize=10;"
GEN = EDGE_BASE + "endArrow=block;endFill=0;endSize=12;strokeColor=#33404D;"


def uc(d, text, x, y, mod, w=230, h=72):
    fill, line = UC[mod]
    return d.node(text, x, y, w, h, f"ellipse;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={line};fontSize=11;")


def build():
    d = Diagram("Core use case diagram (A9)", 1280, 1000)
    d.text("<b>Digital Mohalla: core use case diagram (iteration 1)</b> &#8212; design step A9, Student 3, v0.3 "
           "(standard-notation redraw, 2026-10-11) &#183; Use Cases v1.3, FR/NFR v1.3", 30, 12, 1200, 22, size=14,
           check=False)
    d.text("FRs realised: FR-B-05 to B-17 (B5, B6, B7, B8, B12); FR-T-01 to T-07 (D3/4/5); FR-T-10 (D6); FR-T-11 (I4); "
           "FR-M-05 (I6). Only the CORE use cases built in iteration 1 (Use Cases §3); A3, A4 and B13 are iteration 2.",
           30, 36, 1200, 20, size=11, color="#4A5560", check=False)
    sysb = d.node("<b>Digital Mohalla</b> (iteration 1 core)", 300, 80, 700, 760,
                  "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#1D1D1D;verticalAlign=top;align=left;"
                  "spacingLeft=10;spacingTop=6;fontSize=12;")
    d.mark_container(sysb, pass_through=True)
    b5 = uc(d, "B5 Send borrowing request", 340, 130, "M3")
    b6 = uc(d, "B6 Respond to request", 340, 250, "M3")
    b7 = uc(d, "B7 Confirm handover<br><i style='font-size:9.5px'>extension points: condition disputed (step 3)</i>",
            340, 370, "M3", h=80)
    b8 = uc(d, "B8 Return item and complete<br><i style='font-size:9.5px'>extension points: damage or disagreement "
               "(step 3)</i>", 340, 510, "M3", h=80)
    b12 = uc(d, "B12 Raise dispute", 340, 700, "M3")
    d3 = uc(d, "D3/4/5 Assess transaction assurance<br><i style='font-size:9.5px'>extension points: manipulation "
               "risk (step 4)</i>", 730, 130, "M5", h=90)
    d6 = uc(d, "D6 Escalate case with evidence trail", 730, 330, "M5")
    i4 = uc(d, "I4 Resolve escalated case or dispute", 730, 510, "M9")
    i6 = uc(d, "I6 View audit logs", 730, 690, "M9")

    bor = d.node("Borrower", 145, 150, 30, 60, ACTOR)
    party = d.node("<i>Booking party</i><br>{abstract}", 145, 420, 30, 60, ACTOR)
    lend = d.node("Lender", 145, 640, 30, 60, ACTOR)
    mod = d.node("Moderator", 1110, 480, 30, 60, ACTOR)
    adm = d.node("Admin", 1110, 690, 30, 60, ACTOR)

    E = d.edge
    # associations
    E(bor, b5, "", style=ASSOC, exit=(1, 0.4), entry=(0, 0.5))
    E(bor, b8, "", style=ASSOC, exit=(1, 0.6), entry=(0, 0.35))
    E(lend, b6, "", style=ASSOC, exit=(1, 0.3), entry=(0, 0.6))
    E(lend, b7, "", style=ASSOC, exit=(1, 0.4), entry=(0, 0.6))
    E(party, b12, "", style=ASSOC, exit=(1, 0.75), entry=(0, 0.4))
    E(mod, i4, "", style=ASSOC, exit=(0, 0.5), entry=(1, 0.4))
    E(adm, i4, "", style=ASSOC, exit=(0, 0.3), entry=(1, 0.7))
    E(adm, i6, "", style=ASSOC, exit=(0, 0.6), entry=(1, 0.5))
    # generalisation
    E(bor, party, "", style=GEN, exit=(0.5, 1), entry=(0.5, 0), points=[(160, 240), (160, 400)], check=False)
    E(lend, party, "", style=GEN, exit=(0.5, 0), entry=(1, 0.3), points=[(160, 600), (205, 600), (205, 438)], check=False)
    # include / extend
    E(b5, d3, "&#171;include&#187;", style=DEP, exit=(1, 0.5), entry=(0, 0.5), label_dy=-9)
    E(b12, d6, "&#171;include&#187;", style=DEP, exit=(0.85, 0.15), entry=(0.1, 0.85), label_x=-0.3, label_dx=40)
    E(d6, d3, "&#171;extend&#187;<br>[corroborated risk &#8805; 60, level 4]", style=DEP, exit=(0.5, 0),
      entry=(0.5, 1), label_dx=118)
    E(b12, b8, "&#171;extend&#187; [damage /<br>disagreement]", style=DEP, exit=(0.5, 0), entry=(0.5, 1),
      label_dx=-2)
    E(b12, b7, "&#171;extend&#187;<br>[condition disputed]", style=DEP, exit=(1, 0.5), entry=(1, 0.5),
      points=[(640, 736), (640, 410)], label_x=0.5, label_dx=56)

    d.node("<b>Notation (UML 2.5).</b> Stick figure = actor outside the system; ellipse = use case; box = system "
           "boundary; plain line = association; hollow triangle = generalisation (Borrower and Lender are Booking "
           "parties, the primary actor of B12); dashed open arrow = &#171;include&#187; (always happens: B5 step 5, B12 "
           "step 4) or &#171;extend&#187; (conditional, from the extending use case to the base use case's extension "
           "point: B7 ext 3a, B8 ext 3a, D3/4/5 ext 4a).<br><b>Not actors:</b> the Trust Engine (Module 5) is part of "
           "the system; its use cases run through &#171;include&#187;/&#171;extend&#187;. D6 hands a case to I4 at D6 "
           "step 3 (no UML relationship). Colour = module: blue 3, green 5, orange 9.", 30, 860, 1220, 92,
           "shape=note;size=12;whiteSpace=wrap;html=1;fontSize=10.5;align=left;verticalAlign=top;spacingLeft=8;"
           "spacingTop=4;fillColor=#F4F6F8;strokeColor=#8C99A6;", check=False)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "use_case_diagram.drawio"))
