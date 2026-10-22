"""Generates the A8 architecture diagrams (Student 1).

    python generate_architecture.py   ->  component_diagram.drawio, layer_diagram.drawio

Module numbers are the overview's ten modules (Iteration 1 plan, "Module numbering: agreed").
Modules 1, 3, 5, 9 and 10 are drawn in detail; 2, 4, 6, 8 are deferred (supporting / stretch scope).
Owners follow the plan's proposed work division (S1 lifecycle + indirect trust + locality; S2 estimation,
policy, detection; S3 moderation, evaluation, apps).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

OWNER = {"S1": ("#E3EEF9", "#1F4E79"), "S2": ("#FDEBDD", "#8A4B12"), "S3": ("#EEE5F6", "#5B2C83"),
         "ALL": ("#F2F2F2", "#4D4D4D"), "OFF": ("#F7F7F7", "#9A9A9A")}

MODULE = ("rounded=0;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=8;spacingTop=4;fontSize=12;"
          "container=1;collapsible=0;recursiveResize=0;")
SUB = "rounded=0;whiteSpace=wrap;html=1;fontSize=10.5;verticalAlign=middle;align=center;spacing=3;"
BALL = "ellipse;html=1;fillColor=#FFFFFF;strokeColor=#2B3A4A;strokeWidth=1.5;"
ICON = "shape=component;html=1;jettyWidth=6;jettyHeight=3;fillColor=#FFFFFF;strokeColor=#555555;"
STICK = EDGE_BASE + "endArrow=none;strokeColor=#2B3A4A;strokeWidth=1.5;"
USE = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;dashPattern=6 3;strokeColor=#46535F;strokeWidth=1.3;"


def component(d, cid, title, x, y, w, h, owner="S1", sub=False, parent=None, stereo="component"):
    fill, ink = OWNER[owner]
    if sub:
        label = f"<b>{title}</b>"
        node = d.node(label, x, y, w, h, SUB + f"fillColor={fill};strokeColor={ink};fontColor=#1D1D1D;", id=cid,
                      parent=parent)
    else:
        label = f"<span style='font-size:10px;color:{ink}'>&#171;{stereo}&#187;</span><br><b>{title}</b>"
        node = d.node(label, x, y, w, h, MODULE + f"fillColor={fill};strokeColor={ink};fontColor=#1D1D1D;", id=cid,
                      parent=parent)
        d.mark_container(node)
    d.node("", x + w - 24, y + 6, 16, 14, ICON, parent=node, check=False)
    return node


def ball(d, owner_cell, name, cx, cy, side, label, label_pos, parent_pt=None):
    """Provided interface: ball at (cx, cy) attached to owner_cell on `side` (T, B, L, R)."""
    b = d.node("", cx - 8, cy - 8, 16, 16, BALL, id=f"i_{name}")
    ob = d.box(owner_cell)
    if side == "T":
        pt = (cx, ob[1])
    elif side == "B":
        pt = (cx, ob[3])
    elif side == "L":
        pt = (ob[0], cy)
    else:
        pt = (ob[2], cy)
    d.edge(None, b, "", style=STICK, src_pt=pt, entry={"T": (0.5, 1), "B": (0.5, 0), "L": (1, 0.5), "R": (0, 0.5)}[side])
    lx, ly, lw, align = label_pos
    d.text(label, lx, ly, lw, 18, size=10.5, align=align, id=f"lbl_{name}")
    return b


def uses(d, src_pt, ball_id, entry, points=()):
    d.edge(None, ball_id, "", style=USE, src_pt=src_pt, entry=entry, points=list(points))


# =============================================================================== component diagram
def component_diagram() -> Diagram:
    d = Diagram("Component diagram (A8)", 2140, 1440)
    d.text("<b>Digital Mohalla &#8212; Component diagram, iteration 1</b> (design step A8, v1.1): the overview's ten "
           "modules; 1, 3, 5, 9 and 10 in detail", 40, 12, 1500, 24, size=16, check=False)
    d.text("Ball = provided interface; dashed arrow = required interface (dependency). Colour = owner (S1 / S2 / S3, "
           "Iteration 1 plan work division). Operations of every interface: Architecture_Design.md section 3.",
           40, 36, 1500, 20, size=11, color="#4A5560", check=False)

    # clients
    component(d, "app", "Mobile app (Expo / React Native)<br><span style='font-weight:normal;font-size:10px'>one app for "
              "residents, lenders, moderators and admins (screens W1&#8211;W7)</span>", 520, 72, 540, 60, owner="S3")

    sysb = d.node("<span style='font-size:10px'>&#171;subsystem&#187;</span> <b>Digital Mohalla backend</b> "
                  "<span style='font-size:10.5px'>(Python / FastAPI service, PostgreSQL; proposal &#167;8.1, confirmed at "
                  "the D-15 design gate)</span>", 40, 190, 2060, 1050,
                  "rounded=0;html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontSize=12;"
                  "fillColor=#FCFCFD;strokeColor=#6B7B8C;dashed=0;container=1;collapsible=0;", id="backend")
    d.mark_container(sysb, pass_through=True)

    # API layer
    api = component(d, "api", "REST API  /api/v1", 440, 250, 800, 80, owner="ALL", parent=sysb)
    d.text("authentication &#183; authorisation &#183; validation &#183; privacy filter (NFR-PR-01) &#183; "
           "errors 403 / 409 / 422 &#183; /health", 455, 294, 700, 30, size=10.5, parent=api, check=False)

    # ---------------- Module 1
    m1 = component(d, "m1", "Module 1 &#8212; Accounts &amp; communities  [S1]", 140, 400, 420, 360, owner="S1", parent=sysb)
    component(d, "m1_auth", "AuthService<br><span style='font-weight:normal'>password login, sessions, roles<br>"
              "(FR-A-04 part; seeded users)</span>", 170, 450, 360, 70, owner="S1", sub=True, parent=m1)
    component(d, "m1_mem", "MembershipDirectory<br><span style='font-weight:normal'>memberships, moderator of "
              "community<br>(seeded in it.1; A3/A4 in it.2)</span>", 170, 545, 360, 70, owner="S1", sub=True, parent=m1)
    component(d, "m1_loc", "LocalityVerifier<br><span style='font-weight:normal'>coarse outcome only: verified | "
              "inconclusive | conflicting<br>A11: geofence + invitation; &#171;stub&#187; until the D-11 gate "
              "decides the build</span>", 170, 640, 360, 90, owner="S1", sub=True, parent=m1)

    # ---------------- Module 3
    m3 = component(d, "m3", "Module 3 &#8212; Borrowing lifecycle  [S1]", 660, 400, 580, 360, owner="S1", parent=sysb)
    subs3 = [("m3_svc", "BorrowingService<br><span style='font-weight:normal'>command handlers B5&#8211;B8, B12</span>", 690, 450),
             ("m3_val", "TransitionValidator<br><span style='font-weight:normal'>A3 transition table + authorisation</span>",
              970, 450),
             ("m3_es", "EventStore<br><span style='font-weight:normal'>append-only, stream_id + stream_seq</span>", 690, 545),
             ("m3_rep", "Projector &amp; Replay<br><span style='font-weight:normal'>current state = fold(events)</span>",
              970, 545),
             ("m3_book", "BookingGuard<br><span style='font-weight:normal'>EXCLUDE constraint (ADR-0002)</span>", 690, 640),
             ("m3_out", "OutcomePublisher<br><span style='font-weight:normal'>closing events &#8594; IOutcomeSink</span>",
              970, 640)]
    for cid, label, x, y in subs3:
        component(d, cid, label, x, y, 250, 70, owner="S1", sub=True, parent=m3)

    # ---------------- Module 5
    m5 = component(d, "m5", "Module 5 &#8212; Trust, reputation &amp; safety (assurance engine)  [S2 + S1]", 1340, 400,
                   720, 360, owner="S2", parent=sysb)
    component(d, "m5_fac", "AssuranceFacade<br><span style='font-weight:normal'>assess(request) pipeline, timeout</span>",
              1365, 450, 200, 80, owner="S2", sub=True, parent=m5)
    component(d, "m5_ext", "OutcomeExtractor<br><span style='font-weight:normal'>confirmed outcomes only</span>",
              1365, 550, 200, 80, owner="S2", sub=True, parent=m5)
    component(d, "m5_cfg", "ConfigLoader<br><span style='font-weight:normal'>versioned parameters, config_version "
              "(NFR-D-01)</span>", 1365, 650, 200, 80, owner="S2", sub=True, parent=m5)
    component(d, "m5_ind", "IndirectTrust  [S1]<br><span style='font-weight:normal'>TrustEdgeProjector, KHopPathSearch "
              "(k from config), noisy-OR, &#961; &#8804; 0.6</span>", 1625, 450, 200, 80, owner="S1", sub=True, parent=m5)
    component(d, "m5_det", "ManipulationDetector<br><span style='font-weight:normal'>reciprocal clustering, retaliation"
              "</span>", 1625, 550, 200, 80, owner="S2", sub=True, parent=m5)
    component(d, "m5_beta", "BetaPosteriorEstimator<br><span style='font-weight:normal'>recency-weighted, 90% interval"
              "</span>", 1860, 450, 180, 80, owner="S2", sub=True, parent=m5)
    component(d, "m5_pol", "DecisionPolicy &amp;<br>ExplanationBuilder<br><span style='font-weight:normal'>assurance "
              "state, safeguards</span>", 1625, 650, 415, 80, owner="S2", sub=True, parent=m5)
    d.node("data: assessment, outcome, trust_edge, review tables (schema.sql)", 1860, 550, 180, 80,
           "shape=note;size=12;whiteSpace=wrap;html=1;fontSize=10;fillColor=#FFFFFF;strokeColor=#9A9A9A;fontColor=#555555;",
           id="m5_note", parent=m5)
    # internal interface between S2 and S1 parts of Module 5
    b_ind = d.node("", 1592, 482, 16, 16, BALL, id="i_IIndirectEvidence")
    d.edge(None, b_ind, "", style=STICK, src_pt=(1625, 490), entry=(1, 0.5))
    uses(d, (1565, 490), b_ind, (0, 0.5))
    d.text("IIndirect-<br>Evidence", 1568, 500, 58, 30, size=9.5, align="center", id="lbl_IIndirectEvidence")

    # ---------------- Module 9
    m9 = component(d, "m9", "Module 9 &#8212; Administration &amp; moderation  [S3]", 140, 870, 820, 330, owner="S3",
                   parent=sysb)
    component(d, "m9_case", "CaseService<br><span style='font-weight:normal'>EscalationCase lifecycle (A3), queue, "
              "routing to Admin</span>", 170, 920, 370, 70, owner="S3", sub=True, parent=m9)
    component(d, "m9_trail", "EvidenceTrailBuilder<br><span style='font-weight:normal'>trail from the event log (D6)</span>",
              560, 920, 370, 70, owner="S3", sub=True, parent=m9)
    component(d, "m9_dec", "DecisionService<br><span style='font-weight:normal'>I4: decision + reason &#8594; lifecycle "
              "command</span>", 170, 1010, 370, 70, owner="S3", sub=True, parent=m9)
    component(d, "m9_audit", "AuditLogService<br><span style='font-weight:normal'>hash-chained log, filters, masking "
              "(I6)</span>", 560, 1010, 370, 70, owner="S3", sub=True, parent=m9)
    d.text("Appeal and reversal: iteration 2.", 170, 1100, 400, 20, size=10, color="#5B2C83", parent=m9, check=False)

    # ---------------- Module 7, 10 and deferred modules
    m7 = component(d, "m7", "Module 7 &#8212; Communication &amp; notifications", 1000, 870, 240, 140, owner="ALL",
                   parent=sysb)
    d.text("notify(user, type, payload)<br>&#171;stub&#187; in it.1 (log only);<br>in-app notifications it.2;<br>"
           "chat thread (G1) it.3", 1012, 935, 220, 70, size=10, parent=m7, check=False)
    m10 = component(d, "m10", "Module 10 &#8212; Analytics &amp; evaluation  [S3]", 1340, 870, 300, 200, owner="S3",
                    parent=sysb)
    component(d, "m10_es", "ScenarioSuite<br><span style='font-weight:normal'>ES-01&#8211;ES-06, ES-13 fixtures; runs "
              "in CI</span>", 1365, 920, 250, 60, owner="S3", sub=True, parent=m10)
    d.text("Frozen event logging (FR-N-03) is the Module 3 event store.", 1365, 990, 250, 40, size=10, parent=m10,
           check=False)
    for k, (n, txt) in enumerate([("Module 2 &#8212; Community events", "stretch, it.3 at the earliest"),
                                  ("Module 4 &#8212; Search, discovery &amp; matching", "supporting, it.3"),
                                  ("Module 6 &#8212; Forum &amp; chatbot", "stretch, it.3 at the earliest"),
                                  ("Module 8 &#8212; Vendors", "stretch, it.3 at the earliest")]):
        component(d, f"mx{k}", f"{n}<br><span style='font-weight:normal;font-size:10px'>{txt}</span>", 1700,
                  870 + k * 82, 360, 70, owner="OFF", sub=True, parent=sysb)

    # ---------------- interfaces
    ball(d, api, "IRestApi", 790, 222, "T", "REST API (JSON over HTTPS)", (850, 203, 200, "left"))
    uses(d, (790, 132), "i_IRestApi", (0.5, 0))
    # Module 1
    ball(d, m1, "IAuth", 330, 372, "T", "IAuth", (340, 350, 60, "left"))
    uses(d, (440, 315), "i_IAuth", (0.5, 0), points=[(330, 315)])
    ball(d, m1, "IMembership", 588, 520, "R", "IMembership", (562, 494, 96, "center"))
    ball(d, m1, "ILocality", 588, 640, "R", "ILocality", (562, 614, 96, "center"))
    uses(d, (660, 520), "i_IMembership", (1, 0.5))
    uses(d, (660, 640), "i_ILocality", (1, 0.5))
    # Module 3
    ball(d, m3, "IBorrowingCommands", 950, 372, "T", "IBorrowingCommands", (962, 350, 140, "left"))
    uses(d, (950, 330), "i_IBorrowingCommands", (0.5, 0))
    ball(d, m3, "ILifecycleCommands", 790, 788, "B", "ILifecycleCommands", (800, 773, 130, "left"))
    ball(d, m3, "IEventQuery", 940, 788, "B", "IEventQuery", (950, 773, 90, "left"))
    uses(d, (790, 870), "i_ILifecycleCommands", (0.5, 1))
    uses(d, (940, 870), "i_IEventQuery", (0.5, 1))
    # Module 9
    ball(d, m9, "IModeration", 112, 1000, "L", "IModeration", (44, 1012, 90, "left"))
    uses(d, (440, 290), "i_IModeration", (0.5, 0), points=[(90, 290), (90, 980), (112, 980)])
    ball(d, m9, "ICaseIntake", 700, 842, "T", "ICaseIntake", (606, 827, 86, "right"))
    uses(d, (700, 760), "i_ICaseIntake", (0.5, 0))
    # Module 7
    ball(d, m7, "INotify", 1120, 842, "T", "INotify", (1130, 822, 60, "left"))
    uses(d, (1120, 760), "i_INotify", (0.5, 0))
    uses(d, (960, 900), "i_INotify", (0, 0.5), points=[(985, 900), (985, 842)])
    # Module 5
    ball(d, m5, "IOutcomeSink", 1312, 600, "L", "IOutcomeSink", (1245, 574, 92, "center"))
    uses(d, (1240, 600), "i_IOutcomeSink", (0, 0.5))
    ball(d, m5, "IAssess", 1400, 790, "B", "<b>IAssess</b>: assess(request) &#8594; AssessmentResult",
         (1412, 776, 330, "left"))
    uses(d, (1240, 730), "i_IAssess", (0, 0.5), points=[(1290, 730), (1290, 790)])
    uses(d, (1400, 870), "i_IAssess", (0.5, 1))

    # ---------------- database and legend
    db = component(d, "db", "PostgreSQL 16</b> (schema dm, external)<b><br><span style='font-weight:normal;"
                   "font-size:10px'>event store, projections, bookings (EXCLUDE), assessments, outcomes, trust edges, "
                   "cases, audit log &#8212; 06_data_model/schema.sql v2.3</span>", 700, 1300, 640, 90, owner="ALL")
    d.edge(None, db, "&#171;use&#187; SQL (psycopg)", style=USE, src_pt=(1020, 1240), entry=(0.5, 0), label_dx=60)
    d.node("", 40, 1270, 600, 150, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#B0BAC4;", check=False)
    leg = ("<b>Legend</b><br><span style='background:#E3EEF9'>&nbsp;S1&nbsp;</span> lifecycle, indirect trust, locality "
           "&nbsp;<span style='background:#FDEBDD'>&nbsp;S2&nbsp;</span> estimation, policy, detection "
           "&nbsp;<span style='background:#EEE5F6'>&nbsp;S3&nbsp;</span> moderation, evaluation, apps<br>"
           "<span style='background:#F2F2F2'>&nbsp;shared&nbsp;</span> API and notification stub "
           "&nbsp;<span style='background:#F7F7F7;color:#999'>&nbsp;deferred&nbsp;</span> not in iteration 1<br>"
           "&#9675;&#8212; provided interface (ball) &nbsp;&nbsp; - - -&gt; required interface (dependency)<br>"
           "The S1/S2 boundary is <b>IAssess</b> (Module 3 &#8594; Module 5) and, inside Module 5, IIndirectEvidence.")
    d.text(leg, 50, 1278, 585, 140, size=10.5, check=False)
    return d


# =============================================================================== layer diagram
def layer_diagram() -> Diagram:
    d = Diagram("Layer diagram (A8)", 1700, 1030)
    d.text("<b>Digital Mohalla &#8212; Layer diagram, iteration 1</b> (UML package diagram; design step A8, v1.2, "
           "as built 14 October 2026)", 40, 12, 1300, 24, size=16, check=False)
    d.text("Layers with dependency inversion: each upper layer uses only the layer directly below it; the domain layer "
           "has no I/O and depends on no other layer; infrastructure implements the ports (store and repository "
           "interfaces) declared in the application layer, and uses the platform.",
           40, 36, 1600, 20, size=11, color="#4A5560", check=False)
    layers = [
        ("Presentation", "#EEE5F6", "#5B2C83",
         [("Mobile app: resident and lender screens", "W1&#8211;W2 request and decision, W3a&#8211;W4 handover and "
           "return, W5 dispute", "S3"),
          ("Mobile app: moderator and admin screens", "W6 case queue, W7 case view and decision; audit log view "
           "(screen to be designed)", "S3")],
         "One Expo / React Native app for every role, with screens chosen by role (NFR-D-05); Android and web."),
        ("API / interface", "#F2F2F2", "#4D4D4D",
         [("REST endpoints /api/v1", "Architecture_Design.md section 4; JSON over HTTPS", "ALL"),
          ("Auth &amp; authorisation", "session, role, community scope (NFR-S-02, S-03)", "S1"),
          ("Validation &amp; error mapping", "422 invalid input, 403 not allowed, 409 invalid transition / stale / dates taken",
           "S1"),
          ("Privacy filter", "no address, coordinates or CNIC in any response (NFR-PR-01)", "S1")], ""),
        ("Application (use-case services)", "#E3EEF9", "#1F4E79",
         [("BorrowingService (M3)", "B5&#8211;B8, B12 command handlers; ports LifecycleStore, AuditLog", "S1"),
          ("CaseService, DecisionService (M9)", "D6, I4", "S3"),
          ("AuditLogService (M9)", "I6", "S3"),
          ("Auth &amp; Membership (M1)", "login, roles, coarse locality outcome", "S1"),
          ("ScenarioSuite runner (M10)", "CI only", "S3")], ""),
        ("Domain (pure logic, no I/O)", "#E2F0D9", "#2E5E1E",
         [("Lifecycle model", "14 states, transition table T01&#8211;T26, guards; BorrowingTransaction + replay", "S1"),
          ("Assurance engine (M5)", "Beta posterior, decision policy, explanation, manipulation checks", "S2"),
          ("Indirect trust (M5)", "trust graph, bounded k-hop paths, noisy-OR, reliability cap", "S1"),
          ("EscalationCase model", "case states C01&#8211;C11", "S3")], ""),
        ("Infrastructure", "#FDEBDD", "#8A4B12",
         [("EventStore &amp; projections", "lifecycle_event, borrowing_transaction, replay_state()", "S1"),
          ("Booking constraint", "EXCLUDE on held bookings (ADR-0002)", "S1"),
          ("Repositories", "assessment, outcome, trust_edge, case, decision, audit_log", "ALL"),
          ("ConfigLoader", "versioned engine config, config_version (NFR-D-01)", "S2"),
          ("Notification adapter", "planned, iteration 2 (not built)", "OFF")], ""),
        ("Platform (as built)", "#F4F6F8", "#46535F",
         [("PostgreSQL 16 + btree_gist", "on Neon (AWS Singapore); schema.sql v2.3 via Alembic migration 0001", "S1"),
          ("Render", "API as a Docker web service, web app as a static site; deploys main after CI passes", "S1"),
          ("GitHub Actions", "ci.yml: lint, types, security scan, backend and frontend tests, API client check", "S1"),
          ("Local run", "PostgreSQL 16, Uvicorn, Expo dev server: development and demo fallback", "ALL")], ""),
    ]
    y = 70
    band_ids = []
    for name, fill, ink, chips, note in layers:
        h = 120
        bid = d.node(f"&#171;layer&#187; <b>{name}</b>", 40, y, 1240, h,
                     f"shape=folder;tabWidth=290;tabHeight=22;tabPosition=left;html=1;whiteSpace=wrap;"
                     f"verticalAlign=top;align=left;spacingLeft=10;spacingTop=2;fontSize=12;fillColor={fill};"
                     f"strokeColor={ink};container=1;collapsible=0;", id=f"L{len(band_ids)}")
        d.mark_container(bid)
        cw = (1240 - 30 - 12 * (len(chips) - 1)) / len(chips)
        for k, (title, desc, owner) in enumerate(chips):
            f2, i2 = OWNER[owner]
            dash = "dashed=1;fontColor=#7A7A7A;" if owner == "OFF" else ""
            d.node(f"<b>{title}</b><br><span style='font-size:10px'>{desc}</span>", 55 + k * (cw + 12), y + 32, cw, 64,
                   f"rounded=0;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FFFFFF;strokeColor={i2};{dash}",
                   parent=bid)
        if note:
            d.text(note, 55, y + 98, 900, 18, size=10, color="#5B2C83", parent=bid, check=False)
        band_ids.append(bid)
        y += h + 26
    dep = ("endArrow=open;endFill=0;dashed=1;strokeColor=#46535F;strokeWidth=1.5;fontSize=10;")
    boxes = [d.box(b) for b in band_ids]
    # downward use: presentation -> API -> application -> domain, and infrastructure -> platform
    for upper, lower in ((0, 1), (1, 2), (2, 3), (4, 5)):
        d.edge(None, None, "&#171;use&#187;", style=EDGE_BASE + dep, src_pt=(1300, boxes[upper][3] - 50),
               tgt_pt=(1300, boxes[lower][1] + 50), label_dx=0, check=False)
    # dependency inversion: infrastructure realises the application layer's ports (arrow points upward)
    d.edge(None, None, "&#171;realize&#187;<br>ports", style=EDGE_BASE + dep.replace("strokeColor=#46535F",
           "strokeColor=#8A4B12"), src_pt=(1345, boxes[4][1] + 50), tgt_pt=(1345, boxes[2][3] - 30),
           label_dx=0, check=False)
    # cross-cutting concerns
    cc = d.node("&#171;crosscutting&#187; <b>Policies</b>", 1400, 70, 260, 866,
                "shape=folder;tabWidth=170;tabHeight=22;tabPosition=left;html=1;whiteSpace=wrap;verticalAlign=top;"
                "align=left;spacingLeft=8;spacingTop=2;fontSize=12;fillColor=#FFF8E1;strokeColor=#B26A00;"
                "container=1;collapsible=0;", id="cc")
    d.mark_container(cc)
    for k, (t, s) in enumerate([("Authorisation on every transition", "NFR-S-02; recorded in the event"),
                                ("Audit logging", "append-only, hash-chained (FR-M-05)"),
                                ("Event schema", "frozen fields + schema_version (FR-B-09)"),
                                ("Configuration", "config_version on every assessment"),
                                ("Location privacy", "coarse outcome only (NFR-PR-01/02)"),
                                ("Synthetic data labels", "seed data marked synthetic"),
                                ("Logging", "no request bodies with location; no secrets")]):
        d.node(f"<b>{t}</b><br><span style='font-size:10px'>{s}</span>", 1415, 112 + k * 115, 230, 90,
               "rounded=0;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FFFFFF;strokeColor=#B26A00;", parent=cc)
    d.text("UML package diagram: folder = package with stereotype &#171;layer&#187;; dashed open arrow = dependency "
           "(&#171;use&#187; downward; &#171;realize&#187; from infrastructure up to the ports it implements). Border colour "
           "of an element = owner (purple S3, blue S1, orange S2, grey shared); grey dashed = planned, not built.",
           40, 960, 1300, 20, size=10.5, color="#4A5560", check=False)
    return d


if __name__ == "__main__":
    component_diagram().save(os.path.join(HERE, "component_diagram.drawio"))
    layer_diagram().save(os.path.join(HERE, "layer_diagram.drawio"))
