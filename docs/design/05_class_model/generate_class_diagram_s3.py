"""Generates the class diagram of Student 3's packages, v2.0 (DA-11, iteration 2).

    python generate_class_diagram_s3.py  ->  class_diagram.drawio (Student 3's section of the whole-system diagram)

v1.0 (A7, iteration 1) was drawn by generate_class_diagrams_s2_s3.py. Since iteration 2 this diagram has its own
generator, so Student 2's and Student 3's diagrams can change independently; it still uses the class-drawing
helpers of generate_class_model.py, so all class diagrams share one notation.

v2.0 adds what iteration 2 builds in Student 3's modules:
  Module 9   information requests (C02 to C04), appeal (C08 to C10), reversal with flagged evidence (C11),
             the item's possession on dispute closure (ADR-0009, proposed), audit filters, masking and the
             concentration highlight (UC-I6 v1.4);
  uploads    StoragePort with local disk and object storage, type and size checks, metadata stripped (ADR-0014);
  Module 4   search logging without location (FR-S-05);
  Module 10  the full scenario suite (13 scenarios) and the search evaluation (DA-25).
Sources: UC-B12, UC-D6, UC-I4, UC-I6 (Use Cases v1.4), escalation-case state machine v3.0, sequence diagrams (g)
and (h), schema.sql. Classes of other students appear only as boundary interfaces.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram  # noqa: E402
from generate_class_model import AGGREG, COMPOSE, DEPEND, REALISE, G, link  # noqa: E402
from generate_class_model import klass as _klass  # noqa: E402

GAP = 70
NB = "&#160;&#160;"
V2 = "{v2}"


def klass(d, cid, name, x, y, w, attrs=(), ops=(), **k):
    """The shared class helper with the shared iteration 2 convention: a member or class written with {v2} here is
    drawn green (a whole new class gets a green border), the same as on every other cumulative diagram."""
    def green(lines):
        out, i = [], 0
        lines = list(lines)
        while i < len(lines):
            j = i + 1
            while j < len(lines) and lines[j].startswith(NB):      # continuation lines of one member
                j += 1
            group = lines[i:j]
            if any(V2 in t for t in group):
                group = [G(t.replace("  " + V2, "").replace(" " + V2, "").replace(V2, "")) for t in group]
            out += group
            i = j
        return out
    new = V2 in name
    name = name.replace("  " + V2, "").replace(" " + V2, "")
    return _klass(d, cid, name, x, y, w, green(attrs), green(ops), new=new, **k)


def pkg(d, pid, name, x, y, w, h, colour):
    tab = int(len(name) * 6.6) + 30
    p = d.node(f"<b>{name}</b>", x, y, w, h, f"shape=folder;fontStyle=0;tabWidth={tab};tabHeight=24;tabPosition=left;"
               f"html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=10;spacingTop=2;fontSize=12;"
               f"fillColor={colour};strokeColor=#8A9AAA;container=1;collapsible=0;", id=pid)
    d.mark_container(p, pass_through=True)


def bottom(d, *cids):
    return max(d.box(c)[3] for c in cids)


def Y(d, cid, f):
    b = d.box(cid)
    return b[1] + f * (b[3] - b[1])


def notes(d, text, x, y, w, h):
    d.node(text, x, y, w, h, "shape=note;size=12;whiteSpace=wrap;html=1;fontSize=10.5;align=left;verticalAlign=top;"
           "spacingLeft=8;spacingTop=4;fillColor=#F4F6F8;strokeColor=#8C99A6;", check=False)


def class_diagram_s3() -> Diagram:
    d = Diagram("Class diagram, Student 3 (DA-11)", 2700, 1900)
    d.text("<b>Digital Mohalla &#8212; Class diagram, Student 3 packages</b> (v2.0, iteration 2, DA-11): Module 9 "
           "cases, decisions and audit; uploads; Module 4 search logging; Module 10 evaluation", 40, 12, 2400, 24,
           size=16, check=False)
    d.text("Python design classes from UC-B12, UC-D6, UC-I4, UC-I6 (Use Cases v1.4), the escalation-case state machine "
           "v3.0, sequence diagrams (g) and (h) and schema.sql. Each class lists the FRs it realises; <font color='#0A7A36'>"
           "green = added or changed in iteration 2</font> (new class: green border). Other students' classes appear only "
           "as boundary interfaces (blue S1, orange S2).",
           40, 36, 2400, 20, size=11, color="#4A5560", check=False)
    pkg(d, "p_mod", "moderation  (Module 9)", 30, 70, 1340, 1800, "#FBF8FE")
    pkg(d, "p_up", "uploads  (ADR-0014, proposed)", 1400, 70, 620, 660, "#FBF8FE")
    pkg(d, "p_log", "search logging  (Module 4)", 1400, 760, 620, 380, "#FBF8FE")
    pkg(d, "p_eval", "evaluation  (Module 10)", 2050, 70, 620, 1070, "#FBF8FE")
    pkg(d, "p_bnd", "boundary: other modules", 1400, 1170, 1270, 700, "#F7F7F7")
    X = [60, 390, 720, 1050]
    w = 290
    K = lambda *a, **k: klass(d, *a, owner=k.pop("owner", "S3"), **k)  # noqa: E731

    # ------------------------------------------------------------------ Module 9, row 1: interfaces and audit
    y1 = 110
    K("IMod", "IModeration", X[0], y1, w, [], [
        "queue(community_id, filters): list[CaseSummary]", "case_detail(case_id): CaseDetail",
        "request_information(case_id, party,", f"{NB}question, reason)  {{v2}}",
        "record_decision(case_id, kind, reason, ...)", "file_appeal(case_id, party, reason)  {v2}",
        "decide_appeal(case_id, upheld, reason)  {v2}", "reverse(decision_id, reason)  {v2}",
        "audit_log(filters): list[AuditEntry]"],
        frs="FR-T-10, FR-T-11, FR-M-05 (REST: /cases, /audit-log; endpoints in DA-10)", stereo="interface")
    K("IIntake", "ICaseIntake", X[1], y1, w, [], ["open_or_attach(transaction_id, trigger, reason): EscalationCase",
                                                 "withdraw(transaction_id)"],
      frs="FR-T-10, UC-D6 1b (one live case per transaction)", stereo="interface")
    K("Audit", "AuditLogService", X[2], y1, w, [], [
        "record(actor, action, target, outcome, reason?)", "query(filter: AuditFilter): list[AuditEntry]",
        f"{NB}{{masked by default; the view is logged}}", "unmask(entry_id, purpose): AuditEntry  {v2}",
        f"{NB}{{logged}}", "verify_chain(): ChainCheck", "concentration(moderator_id, window)  {v2}"],
        frs="FR-M-05, NFR-S-05, NFR-S-03, UC-I6 2&#8211;4, 3b&#8211;3d")
    K("Entry", "AuditEntry, AuditFilter", X[3], y1, w, [
        "AuditEntry: occurred_at, actor_id,", f"{NB}authorisation, action, target_type,",
        f"{NB}target_id, previous_value, new_value,", f"{NB}outcome SUCCESS | REJECTED, reason,",
        f"{NB}prev_hash, row_hash", "AuditFilter {v2}: actor, user, transaction,", f"{NB}case, date range, action, result,",
        f"{NB}community (own only)"], frs="FR-M-05 (audit_log row), UC-I6 2", stereo="value")

    # ------------------------------------------------------------------ row 2: services and enums
    y2 = bottom(d, "IMod", "IIntake", "Audit", "Entry") + GAP
    K("CaseSvc", "CaseService", X[0], y2, w, ["- cases: CaseRepository", "- notifier: INotify",
                                             "- attachments: AttachmentService", "- config: timer values"], [
        "open_or_attach(transaction_id, trigger, reason)", "queue(community_id, filters)", "case_detail(case_id)",
        "request_information(case_id, party, question,", f"{NB}reason): deadline = now + window  {{v2, C02}}",
        "add_statement(case_id, party, text, files)", f"{NB}{{before the deadline: C03}}",
        "expire_information(now): int  {v2, C04;", f"{NB}idempotent, called by the scheduler}}",
        "withdraw(transaction_id)", "route_to_admin(case_id)"],
        frs="FR-T-10, FR-T-11 (step 2), FR-B-17, UC-D6 2a, ADR-0012")
    K("Trail", "EvidenceTrailBuilder", X[1], y2, w, ["- events: IEventQuery"], ["build(case): EvidenceTrail",
                                                                              "gaps(trail): list[str]"],
      frs="FR-T-10, UC-D6 1, 1a (trail derived from the event log)")
    K("DecSvc", "DecisionService", X[2], y2, w, ["- lifecycle: ILifecycleCommands", "- audit: AuditLogService"], [
        "record_decision(case_id, moderator, kind,", f"{NB}reason, safeguards?, resolved_outcome?,",
        f"{NB}possession?  {{v2}}): ModeratorDecision", "allowed_kinds(case): set[DecisionKind]  {ADR-0003}",
        "allowed_possession(previous_state)", f"{NB}: set[Possession]  {{v2, ADR-0009}}"],
        frs="FR-T-11, ADR-0003, ADR-0004, ADR-0009, UC-I4 3, 3c, 3d, 4a")
    K("Enums", "CaseTrigger, CaseStatus, DecisionKind, Possession", X[3], y2, w, [
        "CaseTrigger: DISPUTE | MANIPULATION_FLAG |", f"{NB}HIGH_VALUE_LOW_CONFIDENCE |", f"{NB}LOCALITY_HOLD | ENGINE_FAILURE",
        "CaseStatus: OPEN | AWAITING_INFORMATION |", f"{NB}DECIDED | APPEALED | REVERSED | WITHDRAWN",
        "DecisionKind: CLEARED | SAFEGUARDS_IMPOSED |", f"{NB}RESTRICTED | DISPUTE_RESOLVED |",
        f"{NB}APPEAL_UPHELD | APPEAL_OVERTURNED |", f"{NB}REVERSAL  {{v2}}",
        "Possession {v2}: NOT_HANDED_OVER |", f"{NB}WITH_BORROWER | RETURNED | LOST"],
        stereo="enumeration", owner="ENUM")

    # ------------------------------------------------------------------ row 3: entities and appeal service
    y3 = bottom(d, "CaseSvc", "Trail", "DecSvc", "Enums") + GAP
    K("Case", "EscalationCase", X[0], y3, w, [
        "id, transaction_id: UUID", "opened_event_id: int", "trigger_type: CaseTrigger", "hold_reason | dispute_reason",
        "raised_by: UUID | None", "status: CaseStatus", "priority: int {1..3}", "reason: str",
        "assigned_to: UUID | None", "info_deadline, opened_at, closed_at"], [
        "assign(moderator)", "await_information(deadline)", "resume(answered | no_response)  {v2}",
        "appeal(second_moderator)  {v2}", "close(decision | withdrawn)"],
        frs="FR-T-10; state machine C01&#8211;C11 (v3.0)")
    K("TrailV", "EvidenceTrail", X[1], y3, w, ["events: list[LifecycleEvent]", "assessment: AssessmentResult | None",
                                              "condition_reports, statements", "attachments (metadata stripped)",
                                              "gaps: list[str]"], frs="FR-T-10, NFR-PR-03 (chat only if disputed)",
      stereo="value")
    K("Dec", "ModeratorDecision", X[2], y3, w, [
        "id, case_id: UUID", "decided_by: UUID, decider_role", "kind: DecisionKind", "reason: str  {mandatory}",
        "safeguards: list", "resolved_outcome: dict | None", f"{NB}(at_fault, possession {{v2}})",
        "reverses_decision_id: UUID | None", f"{NB}{{set iff APPEAL_OVERTURNED or REVERSAL}}", "decided_at: datetime"],
        frs="FR-T-11, FR-B-15 (resolved outcome is evidence), ES-11")
    K("Appeal", "AppealService  {v2}", X[3], y3, w, ["- decisions: DecisionService", "- notifier: INotify"], [
        "file_appeal(case_id, party, reason)", f"{NB}{{within the appeal window; once per case}}",
        "assign_second(case): moderator", f"{NB}{{not the first decider; Admin if none}}",
        "decide_appeal(case_id, moderator, upheld,", f"{NB}reason): ModeratorDecision"],
        frs="FR-T-11, UC-I4 4b, C08&#8211;C10, sequence (h)")

    # ------------------------------------------------------------------ row 4
    y4 = bottom(d, "Case", "TrailV", "Dec", "Appeal") + GAP + 30
    K("Stmt", "CaseStatement", X[0], y4, w, ["author_id, author_role", f"{NB}BORROWER | LENDER", "statement: str",
                                            "created_at"],
      frs="FR-B-17, UC-B12 6, UC-I4 2 (a moderator question needs schema v2.4)")
    K("Rev", "ReversalService  {v2}", X[3], y4, w, ["- decisions: DecisionService", "- flags: IOutcomeFlags"], [
        "reverse(decision_id, actor, reason)", f"{NB}: ModeratorDecision  {{REVERSAL}}",
        "affected_outcomes(decision): list[UUID]", f"{NB}{{the loan is never rewound}}"],
        frs="FR-T-11, UC-I4 4c, C10, C11, ES-11")

    # ------------------------------------------------------------------ uploads
    ux = [1430, 1760]
    K("Store", "StoragePort", ux[0], 110, 250, [], ["put(key, bytes, mime)", "signed_url(key, ttl): str",
                                                   "delete(key)"], frs="ADR-0014", stereo="interface")
    K("AttSvc", "AttachmentService", ux[1], 110, 230, ["- storage: StoragePort"], [
        "accept(file, owner): Attachment", "check(mime, size)  {TC-85}", "strip_metadata(bytes): bytes",
        f"{NB}{{EXIF and GPS removed}}", "url_for(attachment, viewer): str", f"{NB}{{parties and moderator only}}"],
        frs="NFR-S-06, NFR-PR-01, FR-B-11, FR-B-16")
    K("Local", "LocalDiskStorage", ux[0], 330, 250, [], [], frs="development and CI", stereo="adapter")
    K("Obj", "ObjectStorage", ux[0], 450, 250, [], [], frs="deployed (provider chosen in DA-17)", stereo="adapter")
    K("Att", "Attachment", ux[1], 400, 230, ["transaction_id, uploaded_by", "storage_key, content_sha256",
                                            "mime_type: jpeg | png | webp | pdf", "metadata_stripped = true",
                                            "condition_report_id | case_statement_id"],
      frs="attachment row (schema v2.3)", stereo="value")

    # ------------------------------------------------------------------ search logging
    K("SLog", "SearchLogger", ux[0], 800, 250, [], ["log_query(session, query, filters, mode)",
                                                   "log_results(query_id, ranked_ids)", "log_click(query_id, item_id)"],
      frs="FR-S-05 (no location or coordinates)")
    K("SEntry", "SearchLogEntry", ux[1], 800, 230, ["query_id, session (pseudonymous)", "query text, filters",
                                                   "mode: HYBRID | KEYWORD_ONLY", "shown: list[(item_id, rank)]",
                                                   "clicked: list[item_id]", "at: datetime"],
      frs="FR-S-05; table in DA-23 (Student 1)", stereo="value")

    # ------------------------------------------------------------------ evaluation
    ex = [2080, 2400]
    K("Suite", "ScenarioSuite", ex[0], 110, 240, ["- fixtures: list[ScenarioFixture]"], [
        "run(engine: IAssess): list[ScenarioResult]", "load(paths): list[ScenarioFixture]"],
        frs="NFR-Q-01 (13 scenarios by the final; iteration 1 and 2 fixture files)")
    K("SResult", "ScenarioResult", ex[1], 110, 240, ["scenario_id: str", "state_ok, rule_ok: bool",
                                                    "lifecycle_ok, explanation_ok: bool", "passed: bool  {all four}"],
      frs="NFR-Q-01", stereo="value")
    K("Fixture", "ScenarioFixture", ex[0], 340, 240, ["scenario_id: str", "transaction_context", "evidence, steps",
                                                     "expected: ExpectedResult"],
      frs="scenario_fixtures_iteration1.json, _iteration2.json", stereo="value")
    K("Expected", "ExpectedResult", ex[1], 340, 240, ["rule_fired, decision, state", "lifecycle_state, hold_reason",
                                                     "explanation facts"], frs="NFR-Q-01", stereo="value")
    K("SEval", "SearchEvaluator  {v2}", ex[0], 590, 240, ["- labels: LabelSet"], [
        "precision_at(k=5), recall_at(k=10)", "ndcg_at(k=10)", "compare(keyword_only, hybrid)"],
        frs="DA-25; NFR-P-01, P-02 baselines")
    K("Labels", "LabelSet  {v2}", ex[1], 590, 240, ["queries: 20 to 30, synthetic", "judgements: two labellers",
                                                   "agreement(): Cohen's kappa"], frs="DA-25", stereo="value")

    # ------------------------------------------------------------------ boundary interfaces
    bx = [1430, 1740, 2050, 2360]
    K("ILife", "ILifecycleCommands", bx[0], 1220, 280, [], ["apply_decision(transaction_id, decision): event"],
      frs="Student 1, Module 3", stereo="interface", owner="S1")
    K("IEvt", "IEventQuery", bx[1], 1220, 280, [], ["load_stream(id)", "replay(id)", "verify_chain(id)"],
      frs="Student 1, Module 3", stereo="interface", owner="S1")
    K("IJobs", "JobRunner", bx[2], 1220, 280, [], ["register(job: Job)", "run_due_jobs(now)"],
      frs="Student 1, ADR-0012 (proposed)", stereo="application service", owner="S1")
    K("ISearch", "ISearch", bx[3], 1220, 280, [], ["search(member, query, filters, sort): SearchResults"],
      frs="Student 1 (SearchService), ADR-0016", stereo="interface", owner="S1")
    K("INotify", "INotify", bx[0], 1450, 280, [], ["notify(user, type, payload, dedupe_key)"], frs="Module 7 (Student 2)",
      stereo="interface", owner="S2")
    K("IAssessB", "IAssess", bx[1], 1450, 280, [], ["assess(request): AssessmentResult"], frs="Student 2, Module 5",
      stereo="interface", owner="S2")
    K("IFlags", "IOutcomeFlags", bx[2], 1450, 280, [], ["flag(outcome_ids, decision_id)", "refresh_edges(user_ids)"],
      frs="Student 2, Module 5 (ES-11)", stereo="interface", owner="S2")

    # ------------------------------------------------------------------ relationships, Module 9 (as v1.0)
    gap1 = y2 - 30
    link(d, "CaseSvc", "IMod", "", style=REALISE, exit=(0.3, 0), entry=(0.3, 1))
    link(d, "CaseSvc", "IIntake", "", style=REALISE, exit=(0.7, 0), entry=(0.5, 1),
         points=[(60 + w * 0.7, gap1), (X[1] + w * 0.5, gap1)])
    link(d, "DecSvc", "IMod", "", style=REALISE, exit=(0.15, 0), entry=(0.75, 1),
         points=[(X[2] + w * 0.15, gap1 - 12), (60 + w * 0.75, gap1 - 12)])
    link(d, "DecSvc", "Audit", "&#171;use&#187;", style=DEPEND, exit=(0.6, 0), entry=(0.6, 1), label_dx=36, label_dy=0)
    link(d, "Audit", "Entry", "", style=DEPEND, exit=(1, 0.5), entry=(0, 0.5))
    link(d, "CaseSvc", "Trail", "&#171;use&#187;", style=DEPEND, exit=(1, 0.2), entry=(0, 0.3), label_dy=-10)
    link(d, "Trail", "TrailV", "&#171;creates&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    link(d, "CaseSvc", "Case", "manages", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0), label_dx=36, label_dy=0)
    link(d, "DecSvc", "Dec", "&#171;creates&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    cb = bottom(d, "Case", "TrailV", "Dec", "Appeal") + 22
    link(d, "Case", "Dec", "decided by", "1", "0..*", exit=(0.8, 1), entry=(0.5, 1),
         points=[(60 + w * 0.8, cb), (X[2] + w * 0.5, cb)], label_x=0.0, label_dy=-10, mb_off=(0, 1))
    link(d, "Case", "Stmt", "", "1", "0..*", style=COMPOSE, exit=(0.3, 1), entry=(0.3, 0))
    # v2 relationships
    db = d.box("DecSvc")[3]
    link(d, "Appeal", "DecSvc", "&#171;use&#187;", style=DEPEND, exit=(0.5, 0), entry=(0.9, 1),
         points=[(X[3] + w * 0.5, db + 86), (X[2] + w * 0.9, db + 86)], label_x=0.0, label_dy=-10)
    link(d, "Rev", "DecSvc", "&#171;use&#187;", style=DEPEND, exit=(0, 0.3), entry=(0.8, 1),
         points=[(1030, Y(d, "Rev", 0.3)), (1030, db + 66), (X[2] + w * 0.8, db + 66)], label_x=-0.6,
         label_dx=-26, label_dy=0)
    link(d, "Rev", "IFlags", "&#171;use&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 1),
         points=[(X[3] + w * 0.5, 1845), (bx[2] + 140, 1845)], label_x=0.0, label_dy=-10)
    link(d, "DecSvc", "ILife", "&#171;use&#187;", style=DEPEND, exit=(0.95, 1), entry=(0, 0.3),
         points=[(X[2] + w * 0.95, db + 46), (1385, db + 46), (1385, Y(d, "ILife", 0.3))], label_x=0.4,
         label_dy=-10)
    link(d, "Trail", "IEvt", "&#171;use&#187;", style=DEPEND, exit=(1, 0.6), entry=(0.5, 0),
         points=[(X[1] + w + 15, Y(d, "Trail", 0.6)), (X[1] + w + 15, cb + 26), (1395, cb + 26), (1395, 1190),
                 (bx[1] + 140, 1190)], label_x=0.35, label_dy=-10)
    link(d, "CaseSvc", "INotify", "&#171;use&#187;", style=DEPEND, exit=(0, 0.5), entry=(0, 0.5),
         points=[(45, Y(d, "CaseSvc", 0.5)), (45, 1885), (1415, 1885), (1415, Y(d, "INotify", 0.5))], label_x=0.0,
         label_dy=-10)
    link(d, "CaseSvc", "AttSvc", "&#171;use&#187;", style=DEPEND, exit=(1, 0.05), entry=(0.5, 0),
         points=[(370, Y(d, "CaseSvc", 0.05)), (370, 90), (ux[1] + 115, 90)], label_x=0.0, label_dy=-10)
    link(d, "IJobs", "CaseSvc", "&#171;calls&#187;", style=DEPEND, exit=(0.5, 1), entry=(0, 0.8),
         points=[(bx[2] + 140, 1420), (1390, 1420), (1390, 1700), (52, 1700), (52, Y(d, "CaseSvc", 0.8))],
         label_x=0.0, label_dy=-10)
    # uploads
    link(d, "AttSvc", "Store", "&#171;use&#187;", style=DEPEND, exit=(0, 0.3), entry=(1, 0.3), label_dy=-10)
    link(d, "Local", "Store", "", style=REALISE, exit=(0.3, 0), entry=(0.3, 1))
    link(d, "Obj", "Store", "", style=REALISE, exit=(0, 0.5), entry=(0, 0.8),
         points=[(ux[0] - 15, Y(d, "Obj", 0.5)), (ux[0] - 15, Y(d, "Store", 0.8))])
    link(d, "AttSvc", "Att", "&#171;creates&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    # search logging and evaluation
    link(d, "SLog", "SEntry", "&#171;creates&#187;", style=DEPEND, exit=(1, 0.5), entry=(0, 0.5), label_dy=-10)
    link(d, "ISearch", "SLog", "&#171;use&#187;", style=DEPEND, exit=(0, 0.5), entry=(0.5, 1),
         points=[(bx[3] - 15, Y(d, "ISearch", 0.5)), (bx[3] - 15, 1160), (ux[0] + 125, 1160)], label_x=0.0,
         label_dy=-10)
    link(d, "SEval", "SEntry", "&#171;reads&#187;", style=DEPEND, exit=(0, 0.5), entry=(1, 0.5), label_dy=-10)
    link(d, "SEval", "Labels", "", "1", "1", style=COMPOSE, exit=(1, 0.5), entry=(0, 0.5))
    link(d, "Suite", "Fixture", "", "1", "13..*", style=AGGREG, exit=(0.5, 1), entry=(0.5, 0))
    link(d, "Fixture", "Expected", "", "", "1..*", style=COMPOSE, exit=(1, 0.5), entry=(0, 0.5))
    link(d, "Suite", "SResult", "", style=DEPEND, exit=(1, 0.5), entry=(0, 0.5))
    link(d, "Suite", "IAssessB", "&#171;use&#187;", style=DEPEND, exit=(0, 0.2), entry=(0.5, 0),
         points=[(2065, Y(d, "Suite", 0.2)), (2065, 1155), (2035, 1155), (2035, 1435), (bx[1] + 140, 1435)],
         label_x=0.0, label_dy=-10)

    notes(d, "<b>Notes</b><br>&#8226; Module 9 changes a lifecycle state only through ILifecycleCommands.apply_decision() "
          "(one writer of lifecycle events, A8). A reversal or an overturned appeal never rewinds the loan: "
          "ReversalService flags the outcomes that came from the reversed decision through IOutcomeFlags, and the next "
          "assessment no longer counts them (ES-11).<br>&#8226; Possession is offered only when the stored previous "
          "state allows it (ADR-0009, proposed): ACCEPTED &#8594; NOT_HANDED_OVER; ACTIVE or RETURN_INITIATED "
          "&#8594; WITH_BORROWER, RETURNED or LOST.<br>&#8226; Timer values (response window, appeal window) "
          "are configuration, proposed in FR/NFR v1.4.<br>&#8226; The evidence trail is derived from the event log, "
          "never stored separately (UC-D6). Search and ranking are Student 1's and Student 2's; Student 3 only logs and "
          "evaluates them.", X[0] + 330, y4, 650, 190)
    return d


if __name__ == "__main__":
    # Student 3's section is drawn into the one whole-system class diagram (generate_class_diagram.py)
    import generate_class_diagram
    generate_class_diagram.build().save(os.path.join(HERE, "class_diagram.drawio"))
