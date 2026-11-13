"""Generates dfd_assurance_pipeline_level0_level1.drawio: DFD level 0 (context) and level 1, Gane & Sarson notation.

    python generate_dfd.py

Owner Student 2 (design step A10; Assurance_Pipeline_DFD_Level_0_Level_1.md holds the flow catalogue). v1.2 redraws
Student 2's hand-drawn v1.1 in strict Gane & Sarson notation with the same processes and flow IDs:
  * external entity = square box; process = rounded box with its number above a line; data store = box open on the
    right with its ID (Dn) in a left cell; data flow = labelled arrow;
  * level 0 is a context diagram: one process, the external entities, no data stores;
  * every flow starts or ends at a process (no entity-store or store-store flow);
  * level 1 balances level 0: each level-0 flow appears on level 1 with the same entity (processes 9.0 and 10.0
    carry the lender's decision and the administrator's flows, which v1.1 left out or drew straight into a store).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import EDGE_BASE, Diagram, save_pages  # noqa: E402

ENT = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#1F2D3A;strokeColor=#0F1A24;fontColor=#FFFFFF;fontStyle=1;"
       "fontSize=12;shadow=1;")
PROC = ("rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#EEF4FD;strokeColor=#2563EB;fontColor=#1E3A8A;"
        "fontSize=11;verticalAlign=top;spacingTop=2;")
PRIV = PROC.replace("#EEF4FD", "#FDEEEE").replace("#2563EB", "#C62828").replace("#1E3A8A", "#7F1D1D")
STORE = ("shape=partialRectangle;whiteSpace=wrap;html=1;right=0;top=1;bottom=1;left=1;fillColor=#F8FAFC;"
         "strokeColor=#46535F;fontSize=11;align=left;spacingLeft=6;fontColor=#1D1D1D;")
FLOW = EDGE_BASE + "endArrow=block;endFill=1;strokeColor=#33404D;fontSize=10;"
NOTE = ("shape=note;size=12;whiteSpace=wrap;html=1;fontSize=10.5;align=left;verticalAlign=top;spacingLeft=8;"
        "spacingTop=4;fillColor=#F4F6F8;strokeColor=#8C99A6;")


def proc(d, num, name, who, x, y, w=180, h=100, style=PROC):
    return d.node(f"<b>{num}</b><hr style='margin:3px 0'>{name}<br><i style='font-size:9.5px'>{who}</i>",
                  x, y, w, h, style)


def store(d, sid, name, x, y, w=240):
    return d.node(f"<b>{sid}</b> &#9474; {name}", x, y, w, 40, STORE)


def level0():
    d = Diagram("DFD level 0 (context)", 1760, 880, grid=False)
    d.text("<b>Digital Mohalla &#8212; DFD level 0: context diagram</b> (Gane &amp; Sarson; design step A10, v1.3: "
           "iteration 2 joining and review flows added, DA-14, Student 3)", 30, 14, 1600, 24, size=15, check=False)
    p0 = proc(d, "0", "Digital Mohalla<br>borrowing and assurance system", "Modules 1, 3, 5, 9 (core)",
              760, 240, 300, 440)
    bor = d.node("Borrower", 120, 250, 170, 120, ENT)
    app = d.node("Applicant<br>(member joining)", 120, 410, 170, 80, ENT)
    adm = d.node("System administrator", 120, 540, 170, 80, ENT)
    len_ = d.node("Lender", 1530, 250, 170, 120, ENT)
    mod = d.node("Community moderator", 1530, 430, 170, 180, ENT)

    def flow(a, b, y, label, entity_left):
        """One horizontal flow between an entity and process 0 at height y (a -> b)."""
        ent, src_is_ent = (a, True) if a != p0 else (b, False)
        ey = (y - d.by_id[ent]["y"]) / d.by_id[ent]["h"]
        py = (y - d.by_id[p0]["y"]) / d.by_id[p0]["h"]
        e_side, p_side = (1, 0) if entity_left else (0, 1)
        if src_is_ent:
            d.edge(a, b, label, style=FLOW, exit=(e_side, ey), entry=(p_side, py))
        else:
            d.edge(a, b, label, style=FLOW, exit=(p_side, py), entry=(e_side, ey))

    flow(bor, p0, 270, "DF-01 Borrowing request (item, dates, message; no location)", True)
    flow(p0, bor, 310, "DF-02 Request status and safeguards", True)
    flow(bor, p0, 350, "DF-11 Review of a completed loan", True)
    flow(app, p0, 430, "DF-09 Join request: one coarse fix and invitation code", True)
    flow(p0, app, 470, "DF-10 Join request status", True)
    flow(adm, p0, 560, "DF-07 Configuration updates", True)
    flow(p0, adm, 600, "DF-08 Health and audit reports", True)
    flow(p0, len_, 270, "DF-03 Request with evidence summary and safeguards", False)
    flow(len_, p0, 310, "DF-04 Booking decision (accept / decline)", False)
    flow(len_, p0, 350, "DF-11 Review of a completed loan", False)
    flow(p0, mod, 450, "DF-05 Escalation case with evidence trail", False)
    flow(mod, p0, 490, "DF-06 Moderator decision with reason", False)
    flow(p0, mod, 540, "DF-12 Membership request with coarse outcome", False)
    flow(mod, p0, 580, "DF-13 Membership decision with reason", False)
    d.node("<b>Gane &amp; Sarson notation.</b> Dark square = external entity; rounded box = process (number above the "
           "line); arrow = data flow. A context diagram has one process and no data stores: the stores D1&#8211;D7 "
           "belong to level 1.<br><b>Privacy.</b> The only flow that touches location is DF-09, and it carries a "
           "single coarse fix that process 0 evaluates in memory and discards; nothing that leaves process 0 carries "
           "a location (A11, decision D13, NFR-PR-01).", 120, 720, 1580, 70, NOTE, check=False)
    return d


def level1():
    d = Diagram("DFD level 1 (assurance pipeline)", 2140, 1720, grid=False)
    d.text("<b>Digital Mohalla &#8212; DFD level 1: decomposition of process 0, centred on the assurance pipeline</b> "
           "(Gane &amp; Sarson; design step A10, v1.3: joining and reviews added for iteration 2, DA-14, Student 3)", 30, 14, 2000, 24, size=15, check=False)
    # entities
    bor = d.node("Borrower", 40, 245, 150, 70, ENT)
    adm = d.node("System administrator", 40, 1500, 150, 70, ENT)
    mod = d.node("Community moderator", 1950, 415, 150, 70, ENT)
    len_ = d.node("Lender", 1950, 975, 150, 70, ENT)
    # processes
    p1 = proc(d, "1.0", "Receive request and check stored locality", "BorrowingService + LocalityChecker (M3, M1)",
              330, 230, style=PRIV)
    p2 = proc(d, "2.0", "Ingest and filter historical outcomes", "OutcomeExtractor (M5)", 700, 230)
    p3 = proc(d, "3.0", "Compute direct trust posterior", "Algorithm 1 (M5)", 700, 500)
    p4 = proc(d, "4.0", "Aggregate bounded k-hop indirect trust", "Algorithm 2 (M5, S1)", 1000, 500)
    p5 = proc(d, "5.0", "Evaluate manipulation risk", "Algorithm 3 (M5)", 1300, 500)
    p6 = proc(d, "6.0", "Apply context-aware decision policy", "Algorithm 4 (M5)", 1000, 760)
    p7 = proc(d, "7.0", "Synthesise explanation and safeguards", "AssuranceFacade (M5)", 1300, 760)
    p8 = proc(d, "8.0", "Dispatch escalation and record moderator decision", "CaseService, DecisionService (M9)",
              1640, 400)
    p9 = proc(d, "9.0", "Record booking decisions and outcomes", "BorrowingService, TrustEdgeProjector (M3, M5)",
              1640, 960)
    p10 = proc(d, "10.0", "Manage configuration and reports", "ConfigLoader, AuditLogService (M5, M9)", 330, 1485)
    # stores
    d5 = store(d, "D5", "Locality results (coarse outcome only)", 200, 100, 220)
    d1 = store(d, "D1", "Event store (lifecycle events, assessments)", 700, 100, 300)
    d4 = store(d, "D4", "Escalation cases and audit log", 1620, 300, 240)
    d2 = store(d, "D2", "Trust graph (edges, ADR-0006)", 1620, 600, 240)
    d3 = store(d, "D3", "Engine configuration (versioned config_version)", 560, 1000, 380)
    # ---- iteration 2 (DA-14): joining a community and reviews
    app = d.node("Applicant<br>(member joining)", 40, 1150, 150, 70, ENT)
    mod2 = d.node("Community<br>moderator *", 40, 1330, 150, 70, ENT)
    bor2 = d.node("Borrower *", 1640, 1160, 150, 70, ENT)
    d.node("<b>Privacy boundary</b>: the coarse fix exists<br>only inside 11.0, in memory", 285, 1090, 240, 170,
           "rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=6 3;fillColor=none;strokeColor=#C62828;"
           "fontColor=#C62828;fontSize=10;verticalAlign=top;align=left;spacingLeft=4;", check=False)
    p11 = proc(d, "11.0", "Check locality at join and record the request", "MembershipService + "
               "LocalityVerifier (M1)", 300, 1140, 200, 100, style=PRIV)
    p12 = proc(d, "12.0", "Decide membership request", "MembershipService (M1, moderator queue)", 300, 1310, 200,
               100)
    p13 = proc(d, "13.0", "Record review and set flags", "ReviewService (M5, D1)", 1300, 1150, 180, 100)
    d6 = store(d, "D6", "Membership requests and decisions", 620, 1195, 260)
    d7 = store(d, "D7", "Reviews (ratings, text, flags)", 980, 1190, 220)


    E = d.edge
    # 1.0
    E(bor, p1, "DF-101 Borrowing request<br>(no location)", style=FLOW, exit=(1, 0.29), entry=(0, 0.35))
    E(p1, bor, "DF-132 Held status<br>(locality, engine)", style=FLOW, exit=(0, 0.75), entry=(1, 0.79))
    E(d5, p1, "DF-129 Stored outcome", style=FLOW, exit=(0.818, 1), entry=(0.278, 0), label_dx=58)
    E(p1, d1, "DF-102 request_created", style=FLOW, exit=(0.889, 0), entry=(0, 0.5), points=[(490, 120)],
      label_x=0.55)
    E(p1, d4, "DF-104 Locality hold / DF-125 engine-failure hold (case records)", style=FLOW, exit=(0.667, 0),
      entry=(0.5, 0), points=[(450, 180), (1740, 180)], label_x=0.1)
    E(p1, p2, "DF-103 Verified request,<br>coarse context", style=FLOW, exit=(1, 0.5), entry=(0, 0.5))
    # 2.0
    E(d1, p2, "DF-106 Outcome and<br>dispute events", style=FLOW, exit=(0.3, 1), entry=(0.5, 0), label_dx=52)
    E(p2, p3, "DF-107 Direct<br>evidence set", style=FLOW, exit=(0.278, 1), entry=(0.278, 0), label_dx=-44)
    E(p2, p4, "DF-108 Subject IDs", style=FLOW, exit=(0.667, 1), entry=(0.333, 0), points=[(820, 420), (1060, 420)])
    E(p2, p5, "DF-109 Interaction history, complaints", style=FLOW, exit=(1, 0.4), entry=(0.333, 0),
      points=[(1360, 270)], label_x=-0.35)
    E(p2, p6, "DF-109B Request valuation", style=FLOW, exit=(0, 0.8), entry=(0, 0.7), points=[(640, 310), (640, 830)],
      label_x=0.55)
    # algorithm outputs
    E(p3, p6, "DF-111 Direct estimate", style=FLOW, exit=(0.5, 1), entry=(0, 0.4), points=[(790, 800)], label_x=0.35)
    E(p4, p6, "DF-115 Indirect<br>estimate", style=FLOW, exit=(0.5, 1), entry=(0.5, 0), label_dx=-40)
    E(p5, p6, "DF-117 Risk assessment", style=FLOW, exit=(0.278, 1), entry=(0.722, 0),
      points=[(1350, 700), (1130, 700)])
    E(p5, p7, "DF-118 Signal<br>summaries", style=FLOW, exit=(0.667, 1), entry=(0.667, 0), label_dx=40)
    E(p6, p7, "DF-120 Policy<br>decision", style=FLOW, exit=(1, 0.5), entry=(0, 0.5))
    E(d2, p4, "DF-113 Trust edges", style=FLOW, exit=(0, 0.5), entry=(1, 0.8), points=[(1200, 620), (1200, 580)],
      label_x=-0.45)
    # configuration
    E(d3, p3, "DF-110 Prior,<br>half-life", style=FLOW, exit=(0.421, 0), entry=(0.111, 1), label_dx=-36)
    E(d3, p4, "DF-114 k, &#947;, cap", style=FLOW, exit=(1, 0.25), entry=(0, 0.6), points=[(960, 1010), (960, 560)],
      label_x=-0.5, label_dx=-38)
    E(d3, p5, "DF-116 Weights, windows", style=FLOW, exit=(1, 0.75), entry=(0, 0.7), points=[(1240, 1030), (1240, 570)],
      label_x=-0.15)
    E(d3, p6, "DF-119 Thresholds", style=FLOW, exit=(1, 0.5), entry=(0.667, 1), points=[(1120, 1020)], label_x=0.25)
    # 6.0 / 7.0 outputs
    E(p6, d4, "DF-124 Policy hold record (R2, R4)", style=FLOW, exit=(0.333, 1), entry=(0, 0.5),
      points=[(1060, 900), (1560, 900), (1560, 320)], label_x=-0.55)
    E(p7, d1, "DF-121 assessment_generated / held_for_review", style=FLOW, exit=(1, 0.3), entry=(0.833, 1),
      points=[(1520, 790), (1520, 200), (950, 200)], label_x=0.55)
    E(p7, len_, "DF-122 Request with evidence summary, safeguards", style=FLOW, exit=(1, 0.8), entry=(0, 0.214),
      points=[(1880, 840), (1880, 990)], label_x=-0.45)
    E(p7, bor, "DF-123 Request status (ASSESSED)", style=FLOW, exit=(0.5, 1), entry=(0.5, 1),
      points=[(1390, 940), (115, 940)], label_x=0.3)
    # 8.0
    E(d4, p8, "DF-126A Case", style=FLOW, exit=(0.458, 1), entry=(0.5, 0), label_dx=40)
    E(p8, mod, "DF-126B Case with<br>evidence trail", style=FLOW, exit=(1, 0.3), entry=(0, 0.214))
    E(mod, p8, "DF-127 Decision<br>with reason", style=FLOW, exit=(0, 0.786), entry=(1, 0.7))
    E(p8, d1, "DF-127B hold_cleared / request_declined / dispute_resolved", style=FLOW, exit=(0, 0.3),
      entry=(1, 0.75), points=[(1580, 430), (1580, 130)], label_x=0.45)
    # 9.0
    E(len_, p9, "DF-04 Booking<br>decision", style=FLOW, exit=(0, 0.5), entry=(1, 0.5))
    E(p9, d1, "DF-131 request_accepted / declined, closing events", style=FLOW, exit=(0, 0.4), entry=(1, 0.25),
      points=[(1600, 1000), (1600, 110)], label_x=0.1, label_dx=-2)
    E(p9, d2, "DF-112 Edge weights", style=FLOW, exit=(0.5, 0), entry=(0.458, 1), label_dx=52)
    # 10.0
    E(adm, p10, "DF-128 Configuration<br>updates", style=FLOW, exit=(1, 0.2), entry=(0, 0.25))
    E(p10, adm, "DF-08 Health and<br>audit reports", style=FLOW, exit=(0, 0.75), entry=(1, 0.8))
    E(p10, d3, "DF-128B Versioned config", style=FLOW, exit=(1, 0.4), entry=(0.895, 1), points=[(900, 1525)],
      label_x=-0.3)
    E(d1, p10, "DF-130 Audit events", style=FLOW, exit=(0, 0.875), entry=(1, 0.15), points=[(540, 135), (540, 1500)],
      label_x=0.0)


    # 11.0 to 13.0: iteration 2 (DA-14). The device fix never leaves 11.0; reviews reach detection through D7.
    E(app, p11, "DF-140 Coarse fix<br>+ invitation code<br>(memory only)", style=FLOW, exit=(1, 0.3),
      entry=(0, 0.21), label_dy=-28)
    E(p11, app, "DF-147 Request<br>status", style=FLOW, exit=(0, 0.8), entry=(1, 0.85), label_dy=18)
    E(p11, d5, "DF-141 Coarse outcome and signal only", style=FLOW, exit=(0, 0.2), entry=(0.214, 1),
      points=[(260, 1160), (260, 140)], label_x=0.0, label_dx=-70)
    E(p11, d6, "DF-142 Join request,<br>coarse outcome", style=FLOW, exit=(1, 0.75), entry=(0, 0.5), label_dy=-22)
    E(d6, p12, "DF-143 Pending request,<br>outcome, flags", style=FLOW, exit=(0.2, 1), entry=(1, 0.3),
      points=[(672, 1340)], label_x=0.2, label_dy=18)
    E(p12, d6, "DF-146 APPROVED / REJECTED", style=FLOW, exit=(1, 0.7), entry=(0.538, 1),
      points=[(760, 1380)], label_x=-0.2, label_dy=14)
    E(p12, mod2, "DF-144 Membership<br>queue", style=FLOW, exit=(0, 0.3), entry=(1, 0.143), label_dy=-18)
    E(mod2, p12, "DF-145 Decision<br>with reason", style=FLOW, exit=(1, 0.786), entry=(0, 0.75), label_dy=18)
    E(p12, app, "DF-147B Decision<br>outcome", style=FLOW, exit=(0, 0.1), entry=(0.85, 1),
      points=[(230, 1320), (230, 1260), (167, 1260)], label_x=0.0, label_dx=-46)
    E(bor2, p13, "DF-150 Review", style=FLOW, exit=(0, 0.5), entry=(1, 0.45), label_dy=-12)
    E(len_, p13, "DF-151 Review", style=FLOW, exit=(0.5, 1), entry=(1, 0.9), points=[(2025, 1240)],
      label_dy=-10)
    E(p13, d7, "DF-152 Review,<br>flags", style=FLOW, exit=(0, 0.6), entry=(1, 0.5), label_dy=-18)
    E(d7, p5, "DF-153 Reviews in the<br>window (S1, S4,<br>retaliation)", style=FLOW, exit=(0.5, 0),
      entry=(0, 0.92), points=[(1090, 1100), (1255, 1100), (1255, 592)], label_x=-0.27, label_dx=62)

    d.node("<b>Privacy boundary (A11, FR-A-07, NFR-PR-01).</b> The device's coarse fix (DF-140) exists only inside "
           "process 11.0, in memory: 11.0 writes the coarse outcome and signal to D5 and the request to D6, never a "
           "coordinate. Process 1.0 (red) reads only the stored outcome (DF-129). No other flow or store on this page "
           "carries a location.", 30, 1620, 1000, 70, NOTE, check=False)
    d.node("<b>Balancing with level 0:</b> DF-01 = DF-101; DF-02 = DF-123 + DF-132; DF-03 = DF-122; DF-04 = DF-04; "
           "DF-05 = DF-126B; DF-06 = DF-127; DF-07 = DF-128; DF-08 = DF-08; DF-09 = DF-140; DF-10 = DF-147 + DF-147B; "
           "DF-11 = DF-150 + DF-151; DF-12 = DF-144; DF-13 = DF-145. Every flow starts or ends at a process. "
           "* = an entity drawn a second time to avoid crossing lines (Gane &amp; Sarson duplicate mark).",
           1050, 1620, 1060, 70, NOTE, check=False)
    return d


if __name__ == "__main__":
    save_pages(os.path.join(HERE, "dfd_assurance_pipeline_level0_level1.drawio"), [level0(), level1()])
