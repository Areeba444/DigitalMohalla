"""Generates the A2 domain model and the A7 class diagram for Student 1's packages.

    python generate_class_model.py  ->  domain_model.drawio, class_diagram_s1.drawio

Domain model (A2, shared by all three students): the twelve classes listed in the Iteration 1 plan step A2
plus LocalityResult, ConditionReport and Booking, which carry nouns of the dressed use cases (UC-A3/B5
"coarse locality result", UC-B7/B8 "checklist", ADR-0002 "accepted booking").
Class diagram (A7): Student 1's parts only - Module 1 (accounts, locality), Module 3 (lifecycle) and the
indirect-trust part of Module 5, with the Student 2 interfaces they depend on shown as boundaries.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

LINE = 15
COL = {"S1": ("#E3EEF9", "#1F4E79"), "S2": ("#FDEBDD", "#8A4B12"), "S3": ("#EEE5F6", "#5B2C83"),
       "ENUM": ("#F4F6F8", "#46535F")}


def klass(d, cid, name, x, y, w, attrs=(), ops=(), frs="", owner="S1", stereo=None):
    fill, ink = COL[owner]
    head = (f"<span style='font-weight:normal;font-size:10px'>&#171;{stereo}&#187;</span><br>" if stereo else "") + \
        f"<b>{name}</b>"
    hh = 38 if stereo else 26
    body = "<br>".join(attrs)
    if ops:
        body += ("<hr style='margin:3px 0'>" if attrs else "") + "<br>".join(ops)
    if frs:
        body += f"<hr style='margin:3px 0'><i style='color:#6A7A8A'>{frs}</i>"
    n_lines = max(1, len(attrs)) + len(ops) + (1 if frs else 0) + math.ceil(len(frs) / (w / 6.2)) - (1 if frs else 0)
    h = hh + n_lines * LINE + 8 + (6 if ops else 0) + (6 if frs else 0)
    c = d.node(head, x, y, w, h, f"swimlane;html=1;startSize={hh};fillColor={fill};strokeColor={ink};fontColor=#1D1D1D;"
               "swimlaneFillColor=#FFFFFF;fontSize=12;whiteSpace=wrap;collapsible=0;container=1;childLayout=stackLayout;"
               "horizontalStack=0;resizeParent=1;resizeParentMax=0;marginBottom=0;rounded=0;", id=cid)
    d.mark_container(c)
    d.by_id[c]["label_block"] = True            # edge labels must not sit on a class
    d.node(body, x, y + hh, w, h - hh, "text;html=1;align=left;verticalAlign=top;spacingLeft=6;spacingTop=2;fontSize=10.5;"
           "whiteSpace=wrap;overflow=hidden;", id=f"{cid}_body", parent=c)
    d.by_id[f"{cid}_body"]["no_label_check"] = True
    return c


ASSOC = EDGE_BASE + "endArrow=none;strokeColor=#2B3A4A;strokeWidth=1.3;"
COMPOSE = EDGE_BASE + "endArrow=none;startArrow=diamondThin;startFill=1;startSize=14;strokeColor=#2B3A4A;strokeWidth=1.3;"
AGGREG = EDGE_BASE + "endArrow=none;startArrow=diamondThin;startFill=0;startSize=14;strokeColor=#2B3A4A;strokeWidth=1.3;"
DEPEND = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;dashPattern=6 3;strokeColor=#46535F;strokeWidth=1.2;"
REALISE = EDGE_BASE + "endArrow=block;endFill=0;endSize=12;dashed=1;dashPattern=6 3;strokeColor=#46535F;strokeWidth=1.2;"
NAV = EDGE_BASE + "endArrow=open;endFill=0;strokeColor=#2B3A4A;strokeWidth=1.3;"


def link(d, a, b, name="", ma="", mb="", style=ASSOC, exit=None, entry=None, points=(), label_x=0.0, label_dx=0,
         label_dy=-10, ma_off=(0, 1), mb_off=(0, 1)):
    """Association with multiplicities. ma_off / mb_off = (extra distance along the line, side: +1 or -1)."""
    e = d.edge(a, b, name, style=style, exit=exit, entry=entry, points=list(points), label_x=label_x, label_dx=label_dx,
               label_dy=label_dy)
    r = d.route(d.by_id[e])
    for txt, (px, py), (qx, qy), off in ((ma, r[0], r[1], ma_off), (mb, r[-1], r[-2], mb_off)):
        if not txt:
            continue
        dx, dy = qx - px, qy - py
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        w, h = 8 + 6.4 * len(txt), 16
        along = abs(ux) * w / 2 + abs(uy) * h / 2 + 4 + off[0]
        side = (abs(uy) * w / 2 + abs(ux) * h / 2 + 3) * (1 if off[1] >= 0 else -1)
        cx = px + ux * along + uy * side
        cy = py + uy * along - ux * side
        d.text(txt, cx - w / 2, cy - h / 2, w, h, size=10.5, align="center", color="#1D1D1D",
               id=f"m_{e}_{'a' if (px, py) == r[0] else 'b'}")
    return e


# =============================================================================== domain model (A2)
def domain_model() -> Diagram:
    d = Diagram("Domain model (A2)", 2010, 1020)
    d.text("<b>Digital Mohalla &#8212; Domain model (conceptual), iteration-1 core</b> (design step A2, v1.0 baseline; "
           "LocalityResult, ConditionReport and Booking kept, decision D18)", 40, 12, 1400, 24, size=16, check=False)
    d.text("Conceptual classes and associations only (no operations, no implementation types). Colour = owning module. "
           "References to User inside Outcome, TrustEdge, Review and ModeratorDecision are shown as role attributes.",
           40, 36, 1700, 20, size=11, color="#4A5560", check=False)
    K = lambda *a, **k: klass(d, *a, **k)  # noqa: E731
    K("Community", "Community", 40, 110, 300, ["name", "rules", "isActive"], owner="S1")
    K("Membership", "Membership", 40, 330, 300, ["role {member, moderator}", "status {pending, approved, &#8230;}",
                                                 "requestedAt, decidedAt"], owner="S1")
    K("LocalityResult", "LocalityResult", 40, 560, 300, ["method (geofence + invitation, A11)", "outcome {verified, inconclusive, "
                                                          "conflicting}", "permissionRefused, boundaryCase", "checkedAt, "
                                                          "validUntil", "no coordinates, no address"], owner="S1")
    K("User", "User", 430, 110, 300, ["displayName", "contact (email or phone)", "verificationLevel", "platformRole "
                                      "{member, admin}", "status", "isSynthetic"], owner="S1")
    K("Item", "Item", 430, 450, 300, ["title, category", "valueBand", "depositAmount (record-only)", "status "
                                      "{published, &#8230;}"], owner="S1")
    K("Booking", "Booking", 430, 720, 300, ["period", "status {held, released}"], owner="S1")
    K("BorrowingTransaction", "BorrowingTransaction", 840, 110, 320, ["requestedPeriod", "message",
                                                                      "lifecycleState (14 states, A3)",
                                                                      "holdReason (while held)", "dueAt", "createdAt"], owner="S1")
    K("ConditionReport", "ConditionReport", 840, 470, 320, ["phase {handover, return}", "reporterRole {borrower, lender}",
                                                            "checklist, photos", "conditionAgreed", "depositReceived "
                                                            "(lender, handover)"], owner="S1")
    K("Review", "Review", 840, 740, 320, ["reviewer, reviewee : User", "ratings, comment", "retaliationFlag, "
                                          "similarityFlag", "(seeded in iteration 1)"], owner="S2")
    K("LifecycleEvent", "LifecycleEvent", 1270, 110, 320, ["eventId, streamSeq", "eventType, schemaVersion",
                                                           "actor, occurredAt", "previousState, newState",
                                                           "evidenceRefs, authorisation", "configVersion "
                                                           "(assessment events)", "payload (ADR-0005)"], owner="S1")
    K("Assessment", "Assessment", 1270, 400, 320, ["assuranceState (4 states)", "policyDecision", "posteriorMean, "
                                                   "ci90, effectiveEvidence", "indirectEvidence (paths, &#961;)",
                                                   "manipulationRisk 0&#8211;100, level, corroborated", "ruleFired, safeguards, explanation",
                                                   "configVersion"], owner="S2")
    K("Outcome", "Outcome", 1270, 720, 320, ["subject, observer : User", "subjectRole, metric", "success", "occurredAt",
                                             "category, valueBand, duration (snapshot)", "status {valid, flagged}"],
      owner="S2")
    K("EscalationCase", "EscalationCase", 1670, 110, 300, ["triggerType", "holdReason | disputeReason", "status (A3)",
                                                           "priority, reason", "assignedTo : User"], owner="S3")
    K("ModeratorDecision", "ModeratorDecision", 1670, 420, 300, ["decidedBy : User", "kind, reason", "safeguards",
                                                                 "decidedAt"], owner="S3")
    K("TrustEdge", "TrustEdge", 1670, 720, 300, ["source, target : User", "role, metric", "weight = posterior mean (ADR-0006)",
                                                 "evidenceCount"], owner="S1")

    def Y(cid, f):
        b = d.box(cid)
        return b[1] + f * (b[3] - b[1])

    link(d, "Community", "Membership", "has", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0), label_dx=-22, label_dy=0,
         ma_off=(0, -1), mb_off=(0, -1))
    link(d, "Membership", "LocalityResult", "evidenced by", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0), label_dx=-45,
         label_dy=0, ma_off=(0, -1), mb_off=(0, -1))
    link(d, "User", "Membership", "holds", "1", "0..*", exit=(0, 0.7), entry=(1, 0.4),
         points=[(390, Y("User", 0.7)), (390, Y("Membership", 0.4))], label_x=-0.05, label_dx=-18, label_dy=0,
         mb_off=(0, -1))
    link(d, "Community", "Item", "lists", "1", "0..*", exit=(1, 0.75), entry=(0.1, 0),
         points=[(410, Y("Community", 0.75)), (410, 420), (460, 420)], label_x=0.0, label_dx=-17, label_dy=0)
    link(d, "User", "Item", "owns (lender)", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0), label_dx=45, label_dy=0)
    link(d, "Item", "Booking", "booked as", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0), label_dx=35, label_dy=0)
    link(d, "User", "BorrowingTransaction", "", "borrower  1", "0..*", exit=(1, 0.25), entry=(0, 0.25), ma_off=(0, -1), mb_off=(0, -1))
    link(d, "User", "BorrowingTransaction", "", "lender  1", "0..*", exit=(1, 0.65), entry=(0, 0.65), ma_off=(0, -1), mb_off=(0, -1))
    link(d, "Item", "BorrowingTransaction", "requested for", "1", "0..*", exit=(1, 0.5), entry=(0, 0.85),
         points=[(770, Y("Item", 0.5)), (770, Y("BorrowingTransaction", 0.85))], label_x=0.0, label_dx=-48, label_dy=0)
    link(d, "BorrowingTransaction", "Booking", "holds dates<br>(ADR-0002)", "1", "0..1", exit=(0.06, 1), entry=(1, 0.5),
         points=[(860.0, 250), (800, 250), (800, Y("Booking", 0.5))], label_x=0.46, label_dx=-35, label_dy=0,
         ma_off=(0, 1))
    link(d, "BorrowingTransaction", "ConditionReport", "confirmed by", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0),
         label_dx=45, label_dy=0)
    link(d, "BorrowingTransaction", "LifecycleEvent", "", "1", "1..* {ordered}", style=COMPOSE,
         exit=(1, 0.15), entry=(0, (Y("BorrowingTransaction", 0.15) - 110) / (d.box("LifecycleEvent")[3] - 110)),
         ma_off=(10, 1), mb_off=(0, 1))
    link(d, "BorrowingTransaction", "Assessment", "", "1", "0..*", exit=(1, 0.5), entry=(0, 0.25),
         points=[(1210, Y("BorrowingTransaction", 0.5)), (1210, Y("Assessment", 0.25))], label_x=0.1, label_dx=-34,
         label_dy=0)
    link(d, "BorrowingTransaction", "Outcome", "", "1", "0..*", exit=(1, 0.7), entry=(0, 0.3),
         points=[(1200, Y("BorrowingTransaction", 0.7)), (1200, Y("Outcome", 0.3))], label_x=0.45, label_dx=-46,
         label_dy=0)
    link(d, "BorrowingTransaction", "Review", "", "1", "0..2", exit=(1, 0.92), entry=(1, 0.5),
         points=[(1190, Y("BorrowingTransaction", 0.92)), (1190, Y("Review", 0.5))], label_x=0.75, label_dx=-38,
         label_dy=0, mb_off=(0, -1))
    link(d, "BorrowingTransaction", "EscalationCase", "escalated in", "1", "0..*", exit=(0.85, 0), entry=(0.5, 0),
         points=[(1112, 80), (1820, 80)], label_x=0.1, label_dy=-10, ma_off=(0, -1), mb_off=(0, -1))
    link(d, "EscalationCase", "ModeratorDecision", "decided by", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0),
         label_dx=38, label_dy=0)
    link(d, "ModeratorDecision", "Outcome", "flags for re-evaluation (ES-11)", "0..1", "0..*", exit=(0, 0.75),
         entry=(1, 0.78), points=[(1630, Y("ModeratorDecision", 0.75)), (1630, Y("Outcome", 0.78))], label_x=-0.5,
         label_dx=-62, label_dy=0)
    link(d, "LifecycleEvent", "Outcome", "source (closing event)", "1", "0..*", exit=(1, 0.85), entry=(1, 0.2),
         points=[(1615, Y("LifecycleEvent", 0.85)), (1615, Y("Outcome", 0.2))], label_x=-0.55, label_dx=-60, label_dy=0,
         mb_off=(0, -1))
    link(d, "Outcome", "TrustEdge", "&#171;derive&#187;", style=DEPEND, exit=(1, 0.92), entry=(0, 0.85), label_dy=10)
    d.node("", 40, 910, 1930, 80, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#B0BAC4;", check=False)
    d.text("<b>Separate attributes, deliberately:</b> BorrowingTransaction.lifecycleState (where the loan is) and "
           "Assessment.assuranceState (what the evidence says) &#8212; e.g. HELD_FOR_REVIEW with REVIEW_RECOMMENDED (ES-04). "
           "<b>Deliberately left out of iteration 1:</b> chat thread and messages (G1), notifications (G3), calendar blocks "
           "(B2), listing photos, counter-offer, appeal (modelled as later ModeratorDecisions). &#9670; composition: events "
           "live and die with their transaction. Colours: <span style='background:#E3EEF9'>&nbsp;S1&nbsp;</span> "
           "<span style='background:#FDEBDD'>&nbsp;S2&nbsp;</span> <span style='background:#EEE5F6'>&nbsp;S3&nbsp;</span>.",
           50, 916, 1860, 70, size=10.5, check=False)
    return d


# =============================================================================== class diagram (A7, Student 1)
def class_diagram() -> Diagram:
    d = Diagram("Class diagram, Student 1 (A7)", 2280, 1650)
    d.text("<b>Digital Mohalla &#8212; Class diagram, Student 1 packages</b> (design step A7, v1.0): Module 1 accounts &amp; "
           "locality, Module 3 borrowing lifecycle, Module 5 indirect trust", 40, 12, 1800, 24, size=16, check=False)
    d.text("Python design classes (iteration 1). Each class lists the FRs it realises. Student 2 classes appear only as the "
           "interfaces Student 1 depends on (orange).", 40, 36, 1700, 20, size=11, color="#4A5560", check=False)

    def pkg(pid, name, x, y, w, h, colour):
        tab = int(len(name.replace("&#8212;", "-")) * 6.6) + 30
        p = d.node(f"<b>{name}</b>", x, y, w, h, f"shape=folder;fontStyle=0;tabWidth={tab};tabHeight=24;tabPosition=left;"
                   f"html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=10;spacingTop=2;fontSize=12;"
                   f"fillColor={colour};strokeColor=#8A9AAA;container=1;collapsible=0;", id=pid)
        d.mark_container(p, pass_through=True)

    pkg("p_acc", "accounts  (Module 1)", 30, 70, 520, 1260, "#F7FAFD")
    pkg("p_life", "lifecycle  (Module 3)", 590, 70, 1000, 1460, "#F7FAFD")
    pkg("p_ind", "assurance.indirect  (Module 5, S1 part)", 1630, 70, 620, 1008, "#F7FAFD")
    pkg("p_s2", "assurance  (Module 5, Student 2) &#8212; boundary only", 1630, 1092, 620, 438, "#FFFAF5")
    K = lambda *a, **k: klass(d, *a, **k)  # noqa: E731

    # ---------------- accounts
    K("c_User", "User", 60, 120, 460, ["id: UUID", "display_name: str", "verification_level: VerificationLevel",
                                       "platform_role: PlatformRole", "status: AccountStatus", "is_synthetic: bool"],
      frs="FR-A-04 (part), NFR-S-07: no CNIC / address fields")
    K("c_Membership", "Membership", 60, 309, 460, ["user_id: UUID", "community_id: UUID", "role: MembershipRole",
                                                   "status: MembershipStatus"],
      ["is_moderator_of(community_id): bool"], frs="FR-A-09 (seeded), NFR-S-03")
    K("c_Loc", "LocalityResult", 60, 489, 460, ["membership_id: UUID", "method: VerificationMethod",
                                                "outcome: LocalityOutcome  # never negative",
                                                "geofence_signal: GeofenceSignal | None",
                                                "invitation_id: UUID | None",
                                                "permission_refused, mock_provider_detected, duplicate_suspected: bool",
                                                "approved_by: UUID | None  # moderator path",
                                                "checked_at, valid_until: datetime"],
      frs="FR-A-07, FR-A-08, NFR-PR-02 (no coordinates)", stereo="value")
    K("c_Inv", "Invitation", 60, 720, 460, ["community_id, inviter_id: UUID", "code_hash: bytes  # SHA-256 only",
                                            "expires_at: datetime"], frs="FR-A-07, UC-A3 3d (A11; single use)")
    K("c_Verifier", "GeofenceInvitationVerifier", 60, 838, 460, [],
      ["evaluate(fix, permission_refused, invitation, duplicate_suspected)", "  : LocalityResult  # fix used in memory only"],
      frs="FR-A-07, FR-A-08 (A11 decision table)", stereo="service")
    K("c_LocIf", "LocalityChecker", 60, 974, 460, [], ["outcome_for(user_id, community_id): LocalityOutcome"],
      frs="FR-B-07 (UC-B5 step 4)", stereo="interface")
    K("c_LocStub", "StoredResultLocalityChecker", 60, 1095, 460, [], ["outcome_for(...): LocalityOutcome  "
                                                                     "# latest valid stored result"],
      frs="FR-B-07, FR-A-08; reads results written by the verifier")
    K("c_Auth", "AuthService", 60, 1204, 460, [], ["login(identifier, password): Session", "current_actor(token): Actor"],
      frs="FR-A-04 (part), NFR-S-01")

    # ---------------- lifecycle
    K("c_Svc", "BorrowingService", 620, 120, 440, ["- store: EventStore", "- validator: TransitionValidator",
                                                   "- engine: AssuranceEngine", "- locality: LocalityChecker",
                                                   "- outcomes: OutcomeSink"],
      ["create_request(cmd: CreateRequest): BorrowingTransaction", "accept(id, actor) / decline(id, actor, reason)",
       "cancel(id, actor)", "record_handover_checklist(id, actor, report)", "confirm_handover(id, actor, agreed)",
       "initiate_return(id, actor)", "confirm_return(id, actor, report)", "open_dispute(id, actor, reason) / "
       "withdraw_dispute(id, actor)", "apply_decision(id, decision: ModeratorDecision)"],
      frs="FR-B-05, B-06, B-07, B-10, B-11, B-13, B-15, B-16, B-17", stereo="application service")
    K("c_Txn", "BorrowingTransaction", 1120, 120, 440, ["id: UUID  # = stream_id", "item_id, borrower_id, lender_id: UUID",
                                                        "requested_period: DateTimeRange", "lifecycle_state: LifecycleState",
                                                        "hold_reason: HoldReason | None", "due_at: datetime | None",
                                                        "stream_version: int"],
      ["apply(event: LifecycleEvent): None", "replay(events): BorrowingTransaction  &#171;static&#187;"],
      frs="FR-B-08, FR-B-09, NFR-R-03", stereo="aggregate")
    K("c_Event", "LifecycleEvent", 1120, 470, 440, ["event_id: int", "stream_id: UUID", "stream_seq: int",
                                                    "event_type: EventType", "schema_version: int",
                                                    "actor_id: UUID | None", "occurred_at: datetime",
                                                    "previous_state, new_state: LifecycleState",
                                                    "evidence_refs: dict", "authorisation: str",
                                                    "config_version: str | None", "payload: dict  # ADR-0005"],
      frs="FR-B-09, FR-N-03, NFR-D-01 (frozen schema)", stereo="value, immutable")
    K("c_Val", "TransitionValidator", 620, 590, 460, ["- table: TransitionTable"],
      ["validate(txn, event_type, target, actor): Transition", "  raises InvalidTransition, NotAuthorised, GuardFailed"],
      frs="FR-B-08, NFR-R-02, NFR-S-02, NFR-S-03")
    K("c_Table", "TransitionTable", 620, 780, 460, ["rows: list[Transition]  # 34, from transition_table.csv"],
      ["lookup(state, event_type, target): Transition | None"], frs="FR-B-08, NFR-R-02 (A3 table = test matrix)")
    K("c_Trans", "Transition", 620, 940, 460, ["from_state, to_state: LifecycleState", "event_type: EventType",
                                               "allowed_roles: frozenset[ActorRole]", "guard: Callable[[Context], bool]",
                                               "ref: str  # T01..T26"], frs="FR-B-08", stereo="value")
    K("c_Store", "EventStore", 1120, 820, 440, [], ["append(stream_id, expected_seq, event): None", "  raises StaleStream",
                                                    "load(stream_id): list[LifecycleEvent]"],
      frs="FR-B-09, ADR-0002 (unique stream_id + stream_seq)", stereo="interface")
    K("c_PgStore", "PostgresEventStore", 1120, 990, 440, [], ["append(...)  # one DB transaction: event + booking",
                                                              "load(...)"], frs="FR-M-05, NFR-S-05 (append-only, hash chain)")
    K("c_Booking", "Booking", 620, 1150, 420, ["transaction_id, item_id: UUID", "period: DateTimeRange",
                                               "status: BookingStatus {HELD, RELEASED}"],
      frs="FR-B-05, NFR-R-01 (EXCLUDE constraint, ADR-0002)")
    K("c_Report", "ConditionReport", 1120, 1150, 400, ["phase: ConditionPhase", "reporter_role: PartyRole",
                                                       "checklist: dict", "condition_agreed: bool",
                                                       "deposit_received: bool | None", "reduced_evidence: bool"],
      frs="FR-B-11, FR-B-13; I-4 record-only deposit", stereo="value")
    K("c_Enums", "LifecycleState / EventType / HoldReason", 620, 1340, 460,
      ["14 states, 21 event types, 5 hold reasons", "(lists: State_Machine_Design.md v2.0)"],
      frs="FR-B-08, FR-B-09, ADR-0003", stereo="enumeration",
      owner="ENUM")
    K("c_Actor", "Actor", 1120, 1390, 440, ["user_id: UUID | None", "role: ActorRole", "authorisation: str"],
      frs="NFR-S-02", stereo="value")

    # ---------------- indirect trust
    K("c_Proj", "TrustEdgeProjector", 1660, 120, 560, [], ["on_outcomes(outcomes: list[Outcome]): None"],
      frs="FR-T-04 (edges from verified outcomes only, FR-T-03)")
    K("c_Edge", "TrustEdge", 1660, 260, 560, ["source_id, target_id: UUID", "role: PartyRole", "metric: OutcomeMetric",
                                               "weight: float  # Beta posterior mean, ADR-0006", "evidence_count: int"], frs="FR-T-04")
    K("c_Graph", "TrustGraph", 1660, 470, 560, ["- edges: dict[UUID, list[TrustEdge]]"],
      ["neighbours(u, role, metric): list[TrustEdge]"], frs="FR-T-04")
    K("c_Search", "KHopPathSearch", 1660, 620, 560, ["k: int  # from config (initial 3)"],
      ["paths(u, v, role, metric): list[Path]  # simple paths, len <= k"], frs="FR-T-04, NFR-P-03 (k sweep)")
    K("c_Path", "Path", 1660, 770, 260, ["nodes: list[UUID]", "hops: int", "q: float"], frs="FR-T-04", stereo="value")
    K("c_IndEv", "IndirectEvidence", 1980, 770, 240, ["paths: list[Path]", "strength_i: float", "rho: float  # <= 0.6",
                                                      "t_indirect: float", "prior_backed: bool"],
      frs="FR-T-04, FR-T-01 (paths in explanation, ES-13)", stereo="value")
    K("c_Ind", "IndirectTrustEngine", 1660, 965, 560, ["gamma, cap: float  # config"],
      ["indirect_evidence(lender, borrower, role, metric, t_v, b): IndirectEvidence"],
      frs="FR-T-04 (realises IIndirectEvidence)")

    # ---------------- Student 2 boundary
    K("c_Assess", "AssuranceEngine  (IAssess)", 1660, 1140, 560, [], ["assess(request: AssessmentRequest): "
                                                                      "AssessmentResult"],
      frs="FR-T-01..T-07; implemented by Student 2", stereo="interface", owner="S2")
    K("c_Result", "AssessmentResult", 1660, 1275, 270, ["assurance_state: AssuranceState", "policy_decision",
                                                        "rule_fired: str", "hold_reason | None", "config_version: str"],
      frs="FR-T-01, NFR-D-01", stereo="value",
      owner="S2")
    K("c_Sink", "OutcomeSink", 1960, 1275, 260, [], ["record_outcome(closing_event_id)"], frs="FR-B-15",
      stereo="interface", owner="S2")

    # ---------------- relationships
    def Y(cid, f):
        b = d.box(cid)
        return b[1] + f * (b[3] - b[1])

    link(d, "c_User", "c_Membership", "", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0))
    link(d, "c_Membership", "c_Loc", "", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0))
    link(d, "c_Loc", "c_Inv", "uses", "0..1", "0..1", exit=(0.5, 1), entry=(0.5, 0), label_dx=-35, label_dy=0,
         mb_off=(0, -1))
    link(d, "c_Verifier", "c_Inv", "", style=DEPEND, exit=(0.8, 0), entry=(0.8, 1))
    link(d, "c_LocStub", "c_LocIf", "", style=REALISE, exit=(0.5, 0), entry=(0.5, 1))
    link(d, "c_Svc", "c_LocIf", "&#171;use&#187;", style=DEPEND, exit=(0, 0.92), entry=(1, 0.5),
         points=[(570, Y("c_Svc", 0.92)), (570, Y("c_LocIf", 0.5))], label_x=0.3, label_dx=-20, label_dy=0)
    link(d, "c_Svc", "c_Val", "&#171;use&#187;", style=DEPEND, exit=(0.3, 1), entry=(0.3, 0), label_dx=30, label_dy=0)
    link(d, "c_Val", "c_Table", "", style=NAV, exit=(0.5, 1), entry=(0.5, 0))
    link(d, "c_Table", "c_Trans", "", "1", "34", style=COMPOSE, exit=(0.5, 1), entry=(0.5, 0), ma_off=(8, 1))
    link(d, "c_Svc", "c_Txn", "&#171;create,<br>load&#187;", style=DEPEND, exit=(1, 0.2), entry=(0, (Y("c_Svc", 0.2) - d.box("c_Txn")[1]) /
         (d.box("c_Txn")[3] - d.box("c_Txn")[1])), label_dy=-10)
    link(d, "c_Txn", "c_Event", "{ordered}", "1", "1..*", style=COMPOSE, exit=(0.5, 1), entry=(0.5, 0), label_dx=40,
         label_dy=0, ma_off=(8, 1))
    link(d, "c_Svc", "c_Store", "&#171;use&#187;", style=DEPEND, exit=(1, 0.97), entry=(0, 0.25),
         points=[(1090, Y("c_Svc", 0.97)), (1090, Y("c_Store", 0.25))], label_x=0.0, label_dx=12, label_dy=0)
    link(d, "c_PgStore", "c_Store", "", style=REALISE, exit=(0.5, 0), entry=(0.5, 1))
    link(d, "c_Store", "c_Event", "&#171;stores&#187;", style=DEPEND, exit=(0.85, 0), entry=(0.85, 1), label_dx=35,
         label_dy=0)
    link(d, "c_Txn", "c_Booking", "", "1", "0..1", exit=(1, 0.75), entry=(1, 0.5),
         points=[(1618, Y("c_Txn", 0.75)), (1618, 1350), (1100, 1350), (1100, Y("c_Booking", 0.5))], ma_off=(0, 1),
         mb_off=(0, -1))
    link(d, "c_Txn", "c_Report", "", "1", "0..*", exit=(1, 0.5), entry=(1, 0.3),
         points=[(1605, Y("c_Txn", 0.5)), (1605, Y("c_Report", 0.3))], ma_off=(0, 1), mb_off=(0, 1))
    link(d, "c_Svc", "c_Assess", "&#171;use&#187; assess()", style=DEPEND, exit=(0.5, 0), entry=(0, 0.5),
         points=[(850, 95), (1645, 95), (1645, Y("c_Assess", 0.5))], label_x=-0.2, label_dy=-10)
    link(d, "c_Svc", "c_Sink", "&#171;use&#187;", style=DEPEND, exit=(0.15, 0), entry=(0.5, 0),
         points=[(689, 85), (2265, 85), (2265, 1255), (2090, 1255)], label_x=0.0, label_dy=-10)
    link(d, "c_Assess", "c_Result", "&#171;returns&#187;", style=DEPEND, exit=(0.3, 1), entry=(0.6, 0), label_dx=40,
         label_dy=0)
    link(d, "c_Proj", "c_Edge", "&#171;upserts&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    link(d, "c_Graph", "c_Edge", "", "1", "0..*", style=AGGREG, exit=(0.85, 0), entry=(0.85, 1), ma_off=(8, 1))
    link(d, "c_Search", "c_Graph", "&#171;use&#187;", style=DEPEND, exit=(0.5, 0), entry=(0.5, 1), label_dx=30, label_dy=0)
    link(d, "c_Search", "c_Path", "&#171;creates&#187;", style=DEPEND, exit=(0.23, 1), entry=(0.5, 0), label_dx=40,
         label_dy=0)
    link(d, "c_Ind", "c_Search", "&#171;use&#187;", style=DEPEND, exit=(0, 0.5), entry=(0, 0.5),
         points=[(1645, Y("c_Ind", 0.5)), (1645, Y("c_Search", 0.5))], label_x=0.44, label_dx=40, label_dy=0)
    link(d, "c_Ind", "c_IndEv", "&#171;returns&#187;", style=DEPEND, exit=(0.85, 0), entry=(0.5, 1), label_dx=40, label_dy=0)
    link(d, "c_IndEv", "c_Path", "", "", "1..*", style=AGGREG, exit=(0, 0.3), entry=(1, (Y("c_IndEv", 0.3) - 770) /
         (d.box("c_Path")[3] - 770)), mb_off=(0, -1))

    d.node("", 30, 1350, 520, 266, "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#B0BAC4;", check=False)
    d.text("<b>Notes</b><br>&#8226; lifecycle_state (where the loan is) and AssessmentResult.assurance_state (what the "
           "evidence says) are separate attributes of separate classes (ES-04: HELD_FOR_REVIEW with "
           "REVIEW_RECOMMENDED).<br>&#8226; BorrowingTransaction is rebuilt only through apply(); nothing sets "
           "lifecycle_state directly (FR-B-09).<br>&#8226; Student 2 implements AssuranceEngine and OutcomeSink; Student 1 "
           "implements IndirectTrustEngine, which the AssuranceEngine calls through IIndirectEvidence.<br>&#8226; Module 9 "
           "(Student 3) calls BorrowingService.apply_decision() through ILifecycleCommands; it is not drawn here.<br>"
           "&#8226; Relationship ends: &#9670; composition, &#9671; aggregation, dashed open arrow = dependency, dashed "
           "hollow triangle = realisation.", 40, 1354, 500, 258, size=10.5, check=False)
    return d


if __name__ == "__main__":
    domain_model().save(os.path.join(HERE, "domain_model.drawio"))
    class_diagram().save(os.path.join(HERE, "class_diagram_s1.drawio"))
