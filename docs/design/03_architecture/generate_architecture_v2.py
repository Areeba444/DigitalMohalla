"""Generates the iteration 2 architecture diagrams (DA-10, Student 1).

    python generate_architecture_v2.py   ->  component_diagram_v2.drawio, layer_diagram_v2.drawio

Same notation and helpers as iteration 1 (../03_architecture/generate_architecture.py). Iteration 2 adds
Module 4 Search & Discovery (supervisor's request), builds Module 7 in-app notifications and the scheduler, and shows
the iteration 2 owners: S1 Fatima, S2 Areeba, S3 Minahil. New components carry a green border.
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
    d = Diagram("Component diagram, iteration 2 (DA-10)", 2400, 1700)
    d.text("<b>Digital Mohalla &#8212; Component diagram, iteration 2</b> (DA-10, v2.0): Modules 1, 3, 4, 5, 7, 9 and 10 in "
           "detail; Module 4 Search &amp; Discovery added by the supervisor", 40, 12, 1900, 24, size=16, check=False)
    d.text("Ball = provided interface; dashed arrow = required interface (dependency). Colour = owner in iteration 2 "
           "(S1 Fatima, S2 Areeba, S3 Minahil). <b>Green border = new in iteration 2.</b> Operations: Architecture_Design_v2.md "
           "section 3.", 40, 36, 1900, 20, size=11, color="#4A5560", check=False)

    NEWB = "strokeColor=#0A7A36;strokeWidth=2;"

    def new(cid):
        d.by_id[cid]["style"] += NEWB

    # clients and external actors
    component(d, "app", "Mobile app (Expo / React Native)<br><span style='font-weight:normal;font-size:10px'>residents, lenders, "
              "moderators, admins; screens W1&#8211;W24</span>", 600, 72, 560, 60, owner="S2", stereo="component")
    component(d, "cron", "GitHub Actions schedule<br><span style='font-weight:normal;font-size:10px'>every 15 min, "
              "token (ADR-0012)</span>", 1600, 72, 300, 60, owner="OFF", stereo="external")
    new("cron")

    sysb = d.node("<span style='font-size:10px'>&#171;subsystem&#187;</span> <b>Digital Mohalla backend</b> "
                  "<span style='font-size:10.5px'>(Python / FastAPI on Render, ADR-0011)</span>", 40, 190, 2320, 1300,
                  "rounded=0;html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontSize=12;"
                  "fillColor=#FCFCFD;strokeColor=#6B7B8C;dashed=0;container=1;collapsible=0;", id="backend")
    d.mark_container(sysb, pass_through=True)

    api = component(d, "api", "REST API  /api/v1", 440, 250, 860, 80, owner="ALL", parent=sysb)
    d.text("authentication &#183; authorisation &#183; validation &#183; privacy filter (NFR-PR-01) &#183; errors 403 / 409 / 422 "
           "&#183; /health &#183; /internal/jobs/run (token)", 455, 294, 830, 30, size=10.5, parent=api, check=False)

    SUBW = 400
    # ---------------- Module 1 (S1)
    m1 = component(d, "m1", "Module 1 &#8212; Accounts &amp; communities  [S1]", 70, 400, 450, 390, owner="S1", parent=sysb)
    component(d, "m1_auth", "AuthService<br><span style='font-weight:normal'>login, roles, <b>registration (A1)</b></span>",
              95, 445, SUBW, 64, owner="S1", sub=True, parent=m1)
    component(d, "m1_mem", "MembershipService<br><span style='font-weight:normal'>join request, moderator queue, decisions, "
              "reversal (A3, A4)</span>", 95, 525, SUBW, 64, owner="S1", sub=True, parent=m1)
    new("m1_mem")
    component(d, "m1_loc", "LocalityVerifier<br><span style='font-weight:normal'>geofence + invitation, three-valued; fix "
              "used in memory only (A11)</span>", 95, 605, SUBW, 64, owner="S1", sub=True, parent=m1)
    new("m1_loc")
    component(d, "m1_inv", "InvitationService<br><span style='font-weight:normal'>single-use codes, hash stored</span>",
              95, 685, SUBW, 64, owner="S1", sub=True, parent=m1)
    new("m1_inv")

    # ---------------- Module 3 (S1)
    m3 = component(d, "m3", "Module 3 &#8212; Resource sharing &amp; borrowing lifecycle  [S1]", 580, 400, 620, 390,
                   owner="S1", parent=sysb)
    subs3 = [("m3_svc", "BorrowingService<br><span style='font-weight:normal'>B5&#8211;B8, B12; counter-offer, "
              "extension</span>", 605, 445, False),
             ("m3_val", "TransitionValidator<br><span style='font-weight:normal'>lifecycle v3 table + authorisation</span>",
              900, 445, False),
             ("m3_es", "EventStore &amp; Replay<br><span style='font-weight:normal'>append-only; state = fold(events)</span>",
              605, 525, False),
             ("m3_book", "BookingGuard<br><span style='font-weight:normal'>EXCLUDE constraint (ADR-0002)</span>", 900, 525,
              False),
             ("m3_list", "ListingService<br><span style='font-weight:normal'>create, edit, draft, expiry (B1)</span>", 605, 605,
              True),
             ("m3_out", "OutcomePublisher<br><span style='font-weight:normal'>closing events &#8594; IOutcomeSink</span>", 900,
              605, False),
             ("m3_job", "JobRunner (scheduler)<br><span style='font-weight:normal'>run_due_jobs(now); job_run once-only; "
              "expiry, no-show, reminders, overdue (B13, ADR-0012)</span>", 605, 685, True)]
    for cid, label, x, y, is_new in subs3:
        w = 570 if cid == "m3_job" else 275
        component(d, cid, label, x, y, w, 64, owner="S1", sub=True, parent=m3)
        if is_new:
            new(cid)

    # ---------------- Module 5 (S2 + S1)
    m5 = component(d, "m5", "Module 5 &#8212; Trust, reputation &amp; safety (assurance engine)  [S2 + S1]", 1260, 400, 1060,
                   390, owner="S2", parent=sysb)
    subs5 = [("m5_fac", "AssuranceFacade<br><span style='font-weight:normal'>assess(request); timeout</span>", 1290, 445, "S2",
              False),
             ("m5_beta", "BetaPosteriorEstimator<br><span style='font-weight:normal'>roles and metrics; pair-repeat discount"
              "</span>", 1630, 445, "S2", True),
             ("m5_ind", "IndirectTrust  [S1]<br><span style='font-weight:normal'>k-hop paths, noisy-OR, &#961; &#8804; 0.6"
              "</span>", 1970, 445, "S1", False),
             ("m5_det", "ManipulationDetector<br><span style='font-weight:normal'>S1&#8211;S5, retaliation; S2, S3, S5 new"
              "</span>", 1290, 525, "S2", True),
             ("m5_pol", "DecisionPolicy &amp; Explanation<br><span style='font-weight:normal'>rules R1&#8211;R9 (R4 before R3, "
              "ADR-0010)</span>", 1630, 525, "S2", True),
             ("m5_base", "PopulationBaseline<br><span style='font-weight:normal'>per role and metric, nightly</span>", 1970,
              525, "S2", True),
             ("m5_rev", "ReviewService<br><span style='font-weight:normal'>D1: parties only, once, flags</span>", 1290, 605,
              "S2", True),
             ("m5_len", "LenderEvidence<br><span style='font-weight:normal'>lender factors for search, item page (S-04)"
              "</span>", 1630, 605, "S2", True),
             ("m5_cfg", "ConfigLoader<br><span style='font-weight:normal'>config 1.4.0, config_version</span>", 1970, 605,
              "S2", False)]
    for cid, label, x, y, owner, is_new in subs5:
        component(d, cid, label, x, y, 320, 64, owner=owner, sub=True, parent=m5)
        if is_new:
            new(cid)
    d.text("Data: assessment, outcome, trust_edge, review (schema v2.4).", 1290, 690, 600, 20, size=10, parent=m5,
           color="#6A4A2A", check=False)

    # ---------------- Module 4 (new; split S1 / S2 / S3)
    m4 = component(d, "m4", "Module 4 &#8212; Search &amp; discovery  [S1 + S2 + S3]", 70, 880, 690, 330, owner="S2",
                   parent=sysb)
    new("m4")
    component(d, "m4_kw", "KeywordRetriever  [S1]<br><span style='font-weight:normal'>full-text + trigram; filters inside "
              "the query (I-5)</span>", 95, 925, 310, 70, owner="S1", sub=True, parent=m4)
    component(d, "m4_sem", "SemanticRetriever  [S2]<br><span style='font-weight:normal'>embeddings, pgvector exact search; "
              "falls back to keywords</span>", 425, 925, 310, 70, owner="S2", sub=True, parent=m4)
    component(d, "m4_rank", "HybridRanker  [S2]<br><span style='font-weight:normal'>Algorithm 5: relevance, lender evidence, "
              "availability, same community, freshness; reason line</span>", 95, 1015, 640, 70, owner="S2", sub=True,
              parent=m4)
    component(d, "m4_log", "SearchLogger  [S3]<br><span style='font-weight:normal'>queries, impressions, clicks; no location"
              "</span>", 95, 1105, 310, 70, owner="S3", sub=True, parent=m4)
    component(d, "m4_emb", "EmbeddingJob  [S2]<br><span style='font-weight:normal'>on listing save + backfill job</span>",
              425, 1105, 310, 70, owner="S2", sub=True, parent=m4)
    for cid in ("m4_kw", "m4_sem", "m4_rank", "m4_log", "m4_emb"):
        new(cid)

    # ---------------- Module 7 (new build, S2)
    m7 = component(d, "m7", "Module 7 &#8212; Notifications  [S2]", 820, 880, 300, 160, owner="S2", parent=sysb)
    new("m7")
    d.text("NotificationService: notify(user, type, payload); in-app table, dedupe key, polled by the app (ADR-0013). "
           "Email, push, chat: iteration 3.", 835, 930, 270, 100, size=10.5, parent=m7, check=False)

    # ---------------- Module 9 (S3)
    m9 = component(d, "m9", "Module 9 &#8212; Administration &amp; moderation  [S3]", 1180, 880, 620, 330, owner="S3",
                   parent=sysb)
    subs9 = [("m9_case", "CaseService<br><span style='font-weight:normal'>queue, information requests, deadlines, admin "
              "routing</span>", 1205, 925, True),
             ("m9_dec", "DecisionService<br><span style='font-weight:normal'>decision + reason; possession (ADR-0009)</span>",
              1500, 925, True),
             ("m9_app", "AppealService<br><span style='font-weight:normal'>second moderator; reversal flags outcomes</span>",
              1205, 1015, True),
             ("m9_audit", "AuditLogService<br><span style='font-weight:normal'>API + screen: filters, masking, tamper "
              "warning</span>", 1500, 1015, True),
             ("m9_att", "AttachmentService<br><span style='font-weight:normal'>photos, EXIF stripped (ADR-0014)</span>",
              1205, 1105, True)]
    for cid, label, x, y, is_new in subs9:
        component(d, cid, label, x, y, 275, 70, owner="S3", sub=True, parent=m9)
        if is_new:
            new(cid)

    # ---------------- Module 10 (S3)
    m10 = component(d, "m10", "Module 10 &#8212; Analytics &amp; evaluation  [S3]", 1860, 880, 460, 330, owner="S3",
                    parent=sysb)
    component(d, "m10_es", "ScenarioSuite<br><span style='font-weight:normal'>ES-01&#8211;ES-13 with workflows, in CI</span>",
              1885, 925, 410, 64, owner="S3", sub=True, parent=m10)
    component(d, "m10_eval", "EvaluationHarness<br><span style='font-weight:normal'>baselines, time-ordered holdout, "
              "Brier, calibration</span>", 1885, 1005, 410, 64, owner="S3", sub=True, parent=m10)
    component(d, "m10_srch", "SearchEvaluation<br><span style='font-weight:normal'>labelled queries; precision@5, "
              "NDCG@10; keyword vs hybrid</span>", 1885, 1085, 410, 64, owner="S3", sub=True, parent=m10)
    for cid in ("m10_eval", "m10_srch"):
        new(cid)

    # ---------------- deferred modules
    for k, (n, txt) in enumerate([("Module 2 &#8212; Community events", "stretch"),
                                  ("Module 6 &#8212; Forum &amp; chatbot", "stretch"),
                                  ("Module 8 &#8212; Vendors", "stretch")]):
        component(d, f"mx{k}", f"{n}<br><span style='font-weight:normal;font-size:10px'>{txt}; iteration 3 at the earliest"
                  "</span>", 1430 + k * 300, 1300, 285, 60, owner="OFF", sub=True, parent=sysb)

    # ---------------- interfaces: API
    ball(d, api, "IRestApi", 880, 222, "T", "REST API (JSON over HTTPS)", (892, 200, 200, "left"))
    uses(d, (880, 132), "i_IRestApi", (0.5, 0))
    ball(d, api, "IJobTrigger", 1250, 222, "T", "IJobTrigger", (1262, 200, 100, "left"))
    uses(d, (1750, 132), "i_IJobTrigger", (0.5, 0), points=[(1750, 166), (1250, 166)])
    # Module 1
    ball(d, m1, "IAuth", 300, 372, "T", "IAuth", (312, 350, 60, "left"))
    uses(d, (440, 290), "i_IAuth", (0.5, 0), points=[(300, 290)])
    ball(d, m1, "IMembership", 550, 560, "R", "IMember-<br>ship", (522, 570, 56, "center"))
    ball(d, m1, "ILocality", 550, 690, "R", "ILocality", (522, 700, 56, "center"))
    uses(d, (580, 560), "i_IMembership", (1, 0.5))
    uses(d, (580, 690), "i_ILocality", (1, 0.5))
    # Module 3
    ball(d, m3, "IBorrowingCommands", 900, 372, "T", "IBorrowingCommands", (912, 350, 140, "left"))
    uses(d, (900, 330), "i_IBorrowingCommands", (0.5, 0))
    ball(d, m3, "ILifecycleCommands", 1100, 818, "B", "ILifecycleCommands", (1112, 803, 130, "left"))
    uses(d, (1300, 880), "i_ILifecycleCommands", (0.5, 1), points=[(1300, 846), (1100, 846)])
    # Module 5
    ball(d, m5, "IAssess", 1230, 480, "L", "IAssess", (1202, 454, 56, "center"))
    uses(d, (1200, 480), "i_IAssess", (0, 0.5))
    ball(d, m5, "IOutcomeSink", 1230, 640, "L", "IOutcome-<br>Sink", (1204, 650, 52, "center"))
    uses(d, (1200, 640), "i_IOutcomeSink", (0, 0.5))
    ball(d, m5, "ILenderEvidence", 1500, 818, "B", "ILenderEvidence", (1512, 803, 110, "left"))
    uses(d, (590, 880), "i_ILenderEvidence", (0.5, 1), points=[(590, 870), (1500, 870)])
    ball(d, m5, "IAssessEval", 2090, 818, "B", "IAssess (evaluation)", (2102, 803, 140, "left"))
    uses(d, (2090, 880), "i_IAssessEval", (0.5, 1))
    # Module 4
    ball(d, m4, "ISearch", 170, 852, "T", "ISearch", (182, 830, 60, "left"))
    uses(d, (440, 320), "i_ISearch", (0.5, 0), points=[(60, 320), (60, 836), (170, 836)])
    # Module 7
    ball(d, m7, "INotify", 970, 852, "T", "INotify", (982, 830, 60, "left"))
    uses(d, (970, 790), "i_INotify", (0.5, 0))
    uses(d, (1180, 960), "i_INotify", (1, 0.5), points=[(1150, 960), (1150, 852)])
    # Module 9
    ball(d, m9, "IModeration", 1650, 852, "T", "IModeration", (1556, 846, 86, "right"))
    # API -> IModeration via the right-hand gutter
    d.edge(None, "i_IModeration", "", style=USE, src_pt=(1300, 300), entry=(0.5, 0),
           points=[(2345, 300), (2345, 840), (1650, 840)])

    # ---------------- database, object storage, legend
    db = component(d, "db", "PostgreSQL 16 on Neon</b> (schema dm, external)<b><br><span style='font-weight:normal;"
                   "font-size:10px'>schema v2.4 = v2.3 + migration 0002; extensions btree_gist, vector, pg_trgm</span>",
                   720, 1540, 640, 80, owner="ALL", stereo="external")
    d.edge(None, db, "&#171;use&#187; SQL (psycopg)", style=USE, src_pt=(1040, 1490), entry=(0.5, 0), label_dx=70)
    store = component(d, "store", "Object storage</b> (external)<b><br><span style='font-weight:normal;font-size:10px'>"
                      "photo files; metadata in attachment (ADR-0014)</span>", 1460, 1540, 420, 80, owner="OFF",
                      stereo="external")
    new("store")
    d.edge(None, store, "&#171;use&#187;", style=USE, src_pt=(1240, 1210), entry=(0.5, 0), points=[(1240, 1460),
                                                                                                 (1670, 1460)],
           label_x=0.6, label_dy=-10)
    d.node("", 40, 1520, 640, 160, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#B0BAC4;", check=False)
    leg = ("<b>Legend</b><br><span style='background:#E3EEF9'>&nbsp;S1 Fatima&nbsp;</span> lifecycle, membership, locality, "
           "scheduler, keyword search<br><span style='background:#FDEBDD'>&nbsp;S2 Areeba&nbsp;</span> engine, reviews, "
           "meaning-based search and ranking, notifications, app<br>"
           "<span style='background:#EEE5F6'>&nbsp;S3 Minahil&nbsp;</span> moderation, audit, uploads, search logging, "
           "evaluation<br><span style='background:#F7F7F7;color:#999'>&nbsp;grey&nbsp;</span> external or deferred &nbsp; "
           "<span style='border:2px solid #0A7A36'>&nbsp;green border&nbsp;</span> new in iteration 2<br>"
           "&#9675;&#8212; provided interface &nbsp;&nbsp; - - -&gt; required interface. Module 4 uses ILenderEvidence, so "
           "ranking never computes trust itself and never shows a single number (FR-S-04).")
    d.text(leg, 50, 1528, 625, 150, size=10.5, check=False)
    return d


# =============================================================================== layer diagram
def layer_diagram() -> Diagram:
    d = Diagram("Layer diagram, iteration 2 (DA-10)", 1700, 1030)
    d.text("<b>Digital Mohalla &#8212; Layer diagram, iteration 2</b> (UML package diagram; DA-10, v2.0)", 40, 12, 1300, 24,
           size=16, check=False)
    d.text("Same layer rules as iteration 1: each upper layer uses only the layer below it; the domain layer has no I/O; "
           "infrastructure implements the ports declared in the application layer. Iteration 2 adds, in green, the "
           "search, membership, notification and scheduler parts.", 40, 36, 1600, 20, size=11, color="#4A5560", check=False)
    G = "<span style='color:#0A7A36'><b>+</b></span> "
    layers = [
        ("Presentation", "#EEE5F6", "#5B2C83",
         [("Resident and lender screens", "W1&#8211;W5 plus " + G + "W8&#8211;W10, W12&#8211;W17, W22&#8211;W24 (join, "
           "notifications, extension, counter-offer, review, my evidence, photos, listing, search, item details)", "S2"),
          ("Moderator and admin screens", "W6, W7 plus " + G + "W11 membership queue, W18&#8211;W21 responses, possession, "
           "appeal, audit log", "S3")], "One Expo app for every role (Areeba leads the app in iteration 2)."),
        ("API / interface", "#F2F2F2", "#4D4D4D",
         [("REST endpoints /api/v1", "Architecture_Design_v2.md section 4; " + G + "membership, listings, search, "
           "notifications, reviews, jobs", "ALL"),
          ("Auth &amp; authorisation", "role and community scope; " + G + "job-trigger token", "S1"),
          ("Validation &amp; error mapping", "422, 403, 409 (invalid transition, dates taken, counter-offer open)", "S1"),
          ("Privacy filter", "no address, coordinates or CNIC; " + G + "locality fix never logged", "S1")], ""),
        ("Application (use-case services)", "#E3EEF9", "#1F4E79",
         [("BorrowingService, ListingService, JobRunner (M3)", "B1, B5&#8211;B8, B12, B13", "S1"),
          (G + "MembershipService, LocalityVerifier (M1)", "A1, A3, A4", "S1"),
          (G + "SearchService (M4)", "keyword + semantic retrieval, ranking, logging", "S2"),
          ("CaseService, DecisionService, AppealService (M9)", "D6, I4, I6", "S3"),
          (G + "NotificationService (M7), ReviewService (M5)", "G3, D1", "S2")], ""),
        ("Domain (pure logic, no I/O)", "#E2F0D9", "#2E5E1E",
         [("Lifecycle model v3", "14 states, T01&#8211;T29, I01&#8211;I08; possession exits T25a&#8211;c (ADR-0009)", "S1"),
          ("Assurance engine (M5)", "posterior per role and metric, policy, S1&#8211;S5", "S2"),
          ("Indirect trust (M5)", "bounded k-hop, noisy-OR, cap", "S1"),
          (G + "Locality rule, hybrid ranking", "A11 decision table; Algorithm 5", "S1"),
          ("EscalationCase model", "C01&#8211;C11", "S3")], ""),
        ("Infrastructure", "#FDEBDD", "#8A4B12",
         [("EventStore &amp; projections", "lifecycle_event, replay; " + G + "v3 triggers", "S1"),
          (G + "Search store", "search_tsv, item_embedding (pgvector), search logs", "S1"),
          (G + "Notification and job tables", "notification, job_run", "S1"),
          ("ConfigLoader", "config 1.4.0, config_version", "S2"),
          (G + "Storage adapter", "object storage for photos (ADR-0014)", "S3")], ""),
        ("Platform (as built)", "#F4F6F8", "#46535F",
         [("PostgreSQL 16 on Neon", "btree_gist, " + G + "vector, pg_trgm; migrations 0001, 0002", "S1"),
          ("Render", "API Docker web service, web app static site (ADR-0011)", "S1"),
          ("GitHub Actions", "ci.yml; " + G + "scheduled job trigger every 15 min (ADR-0012)", "S1"),
          (G + "Embedding model runtime", "small sentence-embedding model in the API (ADR-0016)", "S2")], ""),
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
            d.node(f"<b>{title}</b><br><span style='font-size:10px'>{desc}</span>", 55 + k * (cw + 12), y + 32, cw, 64,
                   f"rounded=0;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FFFFFF;strokeColor={i2};", parent=bid)
        if note:
            d.text(note, 55, y + 98, 900, 18, size=10, color="#5B2C83", parent=bid, check=False)
        band_ids.append(bid)
        y += h + 26
    dep = "endArrow=open;endFill=0;dashed=1;strokeColor=#46535F;strokeWidth=1.5;fontSize=10;"
    boxes = [d.box(b) for b in band_ids]
    for upper, lower in ((0, 1), (1, 2), (2, 3), (4, 5)):
        d.edge(None, None, "&#171;use&#187;", style=EDGE_BASE + dep, src_pt=(1300, boxes[upper][3] - 50),
               tgt_pt=(1300, boxes[lower][1] + 50), label_dx=0, check=False)
    d.edge(None, None, "&#171;realize&#187;<br>ports", style=EDGE_BASE + dep.replace("strokeColor=#46535F",
           "strokeColor=#8A4B12"), src_pt=(1345, boxes[4][1] + 50), tgt_pt=(1345, boxes[2][3] - 30),
           label_dx=0, check=False)
    cc = d.node("&#171;crosscutting&#187; <b>Policies</b>", 1400, 70, 260, 866,
                "shape=folder;tabWidth=170;tabHeight=22;tabPosition=left;html=1;whiteSpace=wrap;verticalAlign=top;"
                "align=left;spacingLeft=8;spacingTop=2;fontSize=12;fillColor=#FFF8E1;strokeColor=#B26A00;"
                "container=1;collapsible=0;", id="cc")
    d.mark_container(cc)
    for k, (t, s) in enumerate([("Authorisation on every transition", "NFR-S-02; recorded in the event"),
                                ("Audit logging", "append-only, hash-chained (FR-M-05)"),
                                ("Event schema", "frozen fields; v3 adds three event types (signed)"),
                                ("Configuration", "config_version on every assessment and search"),
                                ("Location privacy", "coarse outcome only; no location in logs or payloads"),
                                ("Idempotent jobs", "job_run once per (job, due key) (NFR-R-05)"),
                                ("Synthetic data labels", "seed data and search catalogue marked synthetic")]):
        d.node(f"<b>{t}</b><br><span style='font-size:10px'>{s}</span>", 1415, 112 + k * 115, 230, 90,
               "rounded=0;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FFFFFF;strokeColor=#B26A00;", parent=cc)
    d.text("UML package diagram: folder = package with stereotype &#171;layer&#187;; dashed open arrow = dependency "
           "(&#171;use&#187; downward; &#171;realize&#187; from infrastructure up to the ports it implements). Border colour "
           "= owner (purple S3, blue S1, orange S2, grey shared). Green + = new in iteration 2.",
           40, 960, 1300, 20, size=10.5, color="#4A5560", check=False)
    return d


if __name__ == "__main__":
    component_diagram().save(os.path.join(HERE, "component_diagram_v2.drawio"))
    layer_diagram().save(os.path.join(HERE, "layer_diagram_v2.drawio"))
