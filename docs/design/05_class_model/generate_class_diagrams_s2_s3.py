"""Generates the A7 class diagrams of Student 2's and Student 3's packages.

    python generate_class_diagrams_s2_s3.py  ->  class_diagram_s2.drawio, class_diagram_s3.drawio

Plan step A7: "each owner draws their module ... Done when each class names the FRs it realises."
Student 2: Module 5 estimation, manipulation detection, decision policy and explanation (Algorithm doc §2-§6,
Assurance_Data_Dictionary.md). Student 3: Module 9 cases, decisions and audit, and the Module 10 scenario suite
(UC-D6, UC-I4, UC-I6, schema.sql, Test_Plan.md). Classes of other students appear only as boundary interfaces.
Drawn with the helpers of generate_class_model.py, so all three class diagrams share one notation.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram  # noqa: E402
from generate_class_model import (AGGREG, COMPOSE, DEPEND, REALISE, klass, link)  # noqa: E402

COLS = [60, 400, 740, 1080, 1420]
W = 300
GAP = 70


def pkg(d, pid, name, x, y, w, h, colour):
    tab = int(len(name.replace("&#8212;", "-")) * 6.6) + 30
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


# =============================================================================== Student 2
def class_diagram_s2() -> Diagram:
    d = Diagram("Class diagram, Student 2 (A7)", 2140, 1800)
    d.text("<b>Digital Mohalla &#8212; Class diagram, Student 2 packages</b> (design step A7, v1.0): Module 5 estimation, "
           "manipulation detection, decision policy and explanation", 40, 12, 1900, 24, size=16, check=False)
    d.text("Python design classes (iteration 1), from the Algorithm doc &#167;2&#8211;&#167;6 and the assurance data "
           "dictionary. Each class lists the FRs it realises. Student 1 classes appear only as the interfaces Student 2 "
           "depends on (blue).", 40, 36, 1900, 20, size=11, color="#4A5560", check=False)
    pkg(d, "p_s2", "assurance  (Module 5, Student 2)", 30, 70, 1720, 1700, "#FFFCF8")
    pkg(d, "p_s1", "boundary: Student 1 (Module 5 indirect trust)", 1780, 70, 340, 600, "#F7FAFD")
    K = lambda *a, **k: klass(d, *a, owner=k.pop("owner", "S2"), **k)  # noqa: E731

    y1 = 110
    K("IAssess", "IAssess", COLS[0], y1, W, [], ["assess(request: AssessmentRequest): AssessmentResult",
                                                "&#160;&#160;raises EngineTimeout (2,000 ms)"],
      frs="FR-T-01, FR-T-07", stereo="interface")
    K("ISink", "IOutcomeSink", COLS[1], y1, W, [], ["record_outcome(closing_event_id: int): None  {idempotent}"],
      frs="FR-B-15, NFR-R-04", stereo="interface")
    K("Loader", "ConfigLoader", COLS[2], y1, W, ["- path: str"], ["load(): EngineConfig"], frs="NFR-D-01")
    K("Config", "EngineConfig", COLS[3], y1, W, ["config_version: str", "prior, half_life, interval_level",
                                                "k, gamma, cap, divisors, baseline", "signal weights, bands, corroboration",
                                                "thresholds, value_bands, timeout_ms"],
      frs="NFR-D-01 (Assurance_Engine_Config_Draft.json)", stereo="value")
    K("Request", "AssessmentRequest", COLS[4], y1, W, ["transaction_id: UUID", "borrower_id, lender_id: UUID",
                                                      "item_id: UUID", "role: Role, metric: Metric"],
      frs="FR-B-07, FR-T-01", stereo="value")
    y2 = bottom(d, "IAssess", "ISink", "Loader", "Config", "Request") + GAP
    K("Facade", "AssuranceFacade", COLS[0], y2, W, ["- extractor: OutcomeExtractor", "- estimator: BetaPosteriorEstimator",
                                                   "- indirect: IIndirectEvidence", "- detector: ManipulationDetector",
                                                   "- policy: DecisionPolicy", "- explainer: ExplanationBuilder",
                                                   "- config: EngineConfig"],
      ["assess(request): AssessmentResult", "record_outcome(closing_event_id)"],
      frs="FR-T-01, FR-T-07, FR-B-15, NFR-D-01")
    K("Extractor", "OutcomeExtractor", COLS[1], y2, W, [], ["extract(closing_event): list[OutcomeEvent]",
                                                           "eligible(subject, role, metric): list[OutcomeEvent]"],
      frs="FR-T-03 (confirmed outcomes only; disputed excluded)")
    K("Beta", "BetaPosteriorEstimator", COLS[2], y2, W, [], ["estimate(events, profile?): TrustEstimate",
                                                            "posterior_mean(s_w, f_w): float  {shared, ADR-0006}",
                                                            "weight(age_days, similarity): float"],
      frs="FR-T-02, FR-T-03")
    K("Explain", "ExplanationBuilder", COLS[3], y2, W, [], ["build(direct, indirect, risk, decision): "
                                                           "list[EvidenceRecord]", "render(records): str"],
      frs="FR-T-08, NFR-U-01 (never one number)")
    K("Policy", "DecisionPolicy", COLS[4], y2, W, ["- thresholds: tau_mu, tau_L, n_min, rho_sup"],
      ["decide(direct, indirect, risk, ctx)", "&#160;&#160;: DecisionPolicyResult", "&#160;&#160;rules R1&#8211;R5, R6_DISPUTE,",
       "&#160;&#160;R6_SPARSE, R7&#8211;R9"], frs="FR-T-06, ADR-0007, ADR-0008")
    y3 = bottom(d, "Facade", "Extractor", "Beta", "Explain", "Policy") + GAP
    K("Result", "AssessmentResult", COLS[0], y3, W, ["state: AssuranceState", "direct: TrustEstimate",
                                                    "indirect: IndirectEvidence", "manipulation: ManipulationRiskAssessment",
                                                    "decision: DecisionPolicyResult", "explanation: list[EvidenceRecord]",
                                                    "config_version: str", "computed_at: datetime"],
      frs="FR-T-01, NFR-D-01 (stored as one assessment row)", stereo="value")
    K("Outcome", "OutcomeEvent", COLS[1], y3, W, ["event_id, transaction_id", "subject_id, observer_id",
                                                  "role: Role, metric: Metric", "success: bool", "status: EvidenceStatus",
                                                  "item_category, value_band, duration_days", "occurred_at: datetime"],
      frs="FR-T-03 (persisted as outcome)", stereo="value")
    K("Estimate", "TrustEstimate", COLS[2], y3, W, ["alpha, beta: float", "mean: float", "lower_90, upper_90: float",
                                                    "effective_sample_size: float", "direct_event_count: int"],
      frs="FR-T-02", stereo="value")
    K("Evidence", "EvidenceRecord", COLS[3], y3, W, ["factor: str", "value: str", "confidence: float",
                                                    "supporting_event_ids: list"], frs="FR-T-08", stereo="value")
    K("Decision", "DecisionPolicyResult", COLS[4], y3, W, ["decision: DecisionAction", "rule_fired: str",
                                                          "hold_reason: HoldReason | None", "escalate: bool  {= hold set}"],
      frs="FR-T-06, ADR-0003", stereo="value")
    y4 = bottom(d, "Result", "Outcome", "Estimate", "Evidence", "Decision") + GAP + 20
    K("Retaliation", "RetaliationCheck", COLS[0], y4, W, ["- window_days: int = 14"],
      ["is_suspected(review, records): bool"], frs="FR-T-09, ES-05")
    K("Detector", "ManipulationDetector", COLS[1], y4, W, ["- signals: list[SignalCheck]", "- weights, bands",
                                                          "- corroboration: 2 signals &#8805; 0.5"],
      ["assess(subject, window): ManipulationRiskAssessment"], frs="FR-T-05, ADR-0007")
    K("Risk", "ManipulationRiskAssessment", COLS[2], y4, W, ["score: float  {0..100}", "level: int  {1..4}",
                                                            "corroborated: bool"], frs="FR-T-05", stereo="value")
    K("Context", "TransactionContext", COLS[3], y4, W, ["item_value, value_band", "is_high_value, medium_value: bool",
                                                       "open_dispute: bool", "resolved_disputes_12m: int",
                                                       "verification_ok: bool", "request_similarity: float"],
      frs="FR-T-06", stereo="value")
    K("Safeguard", "SafeguardRecommendation", COLS[4], y4, W, ["type: SafeguardType", "parameters: dict",
                                                              "reason: str"], frs="FR-T-01", stereo="value")
    y5 = bottom(d, "Retaliation", "Detector", "Risk", "Context", "Safeguard") + GAP
    K("SignalCheck", "SignalCheck", COLS[1], y5, W, ["name: str", "weight: float"],
      ["evaluate(subject, data): ManipulationSignal"], frs="FR-T-05", stereo="interface")
    K("Signal", "ManipulationSignal", COLS[2], y5, W, ["name: str", "available: bool", "value: float  {0..1}",
                                                      "weight: float", "evidence: list[str]"],
      frs="FR-T-05 (evidence, never accusation)", stereo="value")
    K("Enums", "AssuranceState, DecisionAction, EvidenceStatus, SafeguardType", COLS[3], y5, 640,
      ["AssuranceState: SUFFICIENT_EVIDENCE | REVIEW_RECOMMENDED |", "&#160;&#160;INSUFFICIENT_EVIDENCE | ACTIVE_DISPUTE",
       "DecisionAction: PROCEED | PROCEED_WITH_SAFEGUARDS |", "&#160;&#160;REQUEST_VERIFICATION | RESTRICT_HIGH_VALUE | ESCALATE",
       "EvidenceStatus: CONFIRMED | DISPUTED | RESOLVED (Assurance DD &#167;5)",
       "SafeguardType: security_deposit | handover_photos | return_date_fixed | ..."],
      stereo="enumeration", owner="ENUM")
    y6 = bottom(d, "SignalCheck", "Signal") + GAP
    K("Recip", "ReciprocalClustering", 230, y6, 250, ["S1, weight 0.30"], ["evaluate(...)"], frs="FR-T-05, ES-04")
    K("Similar", "ReviewSimilarity", 520, y6, 250, ["S4, weight 0.20"], ["evaluate(...)  {char n-gram TF-IDF}"],
      frs="FR-T-05, ES-04, ADR-0007")
    # Student 1 boundary
    K("IInd", "IIndirectEvidence", 1810, 110, 290, [], ["indirect_evidence(lender, borrower, role, metric, t_v, b): "
                                                       "IndirectEvidence"], frs="FR-T-04 (Student 1)", stereo="interface",
      owner="S1")
    K("IndEv", "IndirectEvidence", 1810, 330, 290, ["paths: list[Path]", "I, rho: float  {rho &#8804; 0.6}",
                                                   "t_indirect: float", "prior_backed: bool"],
      frs="FR-T-04, ADR-0006 (Student 1)", stereo="value", owner="S1")

    # ---------------- relationships
    link(d, "Facade", "IAssess", "", style=REALISE, exit=(0.5, 0), entry=(0.5, 1))
    link(d, "Facade", "ISink", "", style=REALISE, exit=(0.85, 0), entry=(0.3, 1),
         points=[(315, y2 - 25), (490, y2 - 25)])
    bus = y2 - 40
    link(d, "Facade", "Loader", "&#171;use&#187;", style=DEPEND, exit=(0.95, 0), entry=(0.5, 1),
         points=[(345, bus), (890, bus)], label_x=0.35, label_dy=-10)
    link(d, "Loader", "Config", "", style=DEPEND, exit=(1, 0.5), entry=(0, 0.3))
    link(d, "Facade", "Extractor", "", "1", "1", style=COMPOSE, exit=(1, 0.12), entry=(0, 0.3))
    lane = y3 - 30
    for k, (tgt, ex) in enumerate((("Beta", 0.5), ("Explain", 0.5), ("Policy", 0.5))):
        link(d, "Facade", tgt, "", "", "1", style=COMPOSE, exit=(1, 0.86 + 0.04 * k), entry=(ex, 1),
             points=[(375 + 6 * k, Y(d, "Facade", 0.86 + 0.04 * k)), (375 + 6 * k, lane - 8 * k),
                     (d.box(tgt)[0] + W * ex, lane - 8 * k)])
    link(d, "Facade", "Detector", "", "", "1", style=COMPOSE, exit=(0, 0.95), entry=(0.2, 0),
         points=[(45, Y(d, "Facade", 0.95)), (45, y4 - 30), (460, y4 - 30)])
    link(d, "Facade", "IInd", "&#171;use&#187;", style=DEPEND, exit=(0, 0.5), entry=(0.5, 0),
         points=[(40, Y(d, "Facade", 0.5)), (40, 90), (1955, 90)], label_x=0.6, label_dy=-10)
    link(d, "Facade", "Result", "&#171;creates&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    link(d, "Extractor", "Outcome", "&#171;creates&#187;", style=DEPEND, exit=(0.3, 1), entry=(0.3, 0), label_dx=40,
         label_dy=0)
    link(d, "Beta", "Estimate", "&#171;returns&#187;", style=DEPEND, exit=(0.3, 1), entry=(0.3, 0), label_dx=40,
         label_dy=0)
    link(d, "Explain", "Evidence", "&#171;creates&#187;", style=DEPEND, exit=(0.3, 1), entry=(0.3, 0), label_dx=40,
         label_dy=0)
    link(d, "Policy", "Decision", "&#171;returns&#187;", style=DEPEND, exit=(0.3, 1), entry=(0.3, 0), label_dx=40,
         label_dy=0)
    link(d, "Policy", "Context", "&#171;use&#187;", style=DEPEND, exit=(0, 0.9), entry=(1, 0.3),
         points=[(1400, Y(d, "Policy", 0.9)), (1400, Y(d, "Context", 0.3))], label_x=0.0, label_dx=-1, label_dy=-10)
    link(d, "Decision", "Safeguard", "", "1", "0..*", style=COMPOSE, exit=(0.7, 1), entry=(0.7, 0))
    rb = bottom(d, "Result", "Outcome", "Estimate", "Evidence", "Decision") + 22
    for k, (tgt, mult, entry) in enumerate((("Estimate", "1", (0.75, 1)), ("Evidence", "1..*", (0.75, 1)),
                                            ("Decision", "1", (0.15, 1)), ("Risk", "1", (0.5, 0)))):
        ex = 0.55 + 0.1 * k
        tx = d.box(tgt)[0] + W * entry[0]
        ty = d.box(tgt)[3] if entry[1] == 1 else d.box(tgt)[1]
        link(d, "Result", tgt, "", "", mult, style=COMPOSE, exit=(ex, 1), entry=entry,
             points=[(60 + W * ex, rb + 7 * k), (tx, rb + 7 * k)], mb_off=(0, 1 if entry[1] == 1 else -1))
    link(d, "Detector", "Risk", "", style=DEPEND, exit=(1, 0.5), entry=(0, 0.5))
    link(d, "Detector", "Retaliation", "", "1", "1", style=COMPOSE, exit=(0, 0.5), entry=(1, 0.5))
    link(d, "Detector", "SignalCheck", "", "1", "1..*", style=AGGREG, exit=(0.5, 1), entry=(0.5, 0))
    link(d, "Risk", "Signal", "", "1", "1..*", style=COMPOSE, exit=(0.5, 1), entry=(0.5, 0))
    link(d, "Recip", "SignalCheck", "", style=REALISE, exit=(0.5, 0), entry=(0.15, 1),
         points=[(355, y6 - 30), (445, y6 - 30)])
    link(d, "Similar", "SignalCheck", "", style=REALISE, exit=(0.5, 0), entry=(0.85, 1),
         points=[(645, y6 - 22), (655, y6 - 22)])
    link(d, "IInd", "IndEv", "&#171;returns&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    notes(d, "<b>Notes</b><br>&#8226; AssuranceFacade is the only entry point: Module 3 calls IAssess.assess() once per "
          "request (A8); a timeout gives an engine_failure hold, never a default state (FR-T-07).<br>&#8226; Trust and "
          "manipulation risk stay separate attributes of AssessmentResult and are never averaged (FR-T-06).<br>&#8226; "
          "Iteration 2 adds RatingVelocity (S2), NewAccountActivity (S3) and Linkage (S5) as further SignalCheck "
          "realisations.<br>&#8226; BetaPosteriorEstimator.posterior_mean is also the trust-edge weight (ADR-0006).<br>"
          "&#8226; Relationship ends: &#9670; composition, &#9671; aggregation, dashed open arrow = dependency, dashed "
          "hollow triangle = realisation.", 1100, y6 - 10, 620, 150)
    d.by_id["p_s2"]["h"] = y6 + 190 - 70
    d.height = y6 + 220
    return d


# =============================================================================== Student 3
def class_diagram_s3() -> Diagram:
    d = Diagram("Class diagram, Student 3 (A7)", 2040, 1500)
    d.text("<b>Digital Mohalla &#8212; Class diagram, Student 3 packages</b> (design step A7, v1.0): Module 9 cases, "
           "decisions and audit; Module 10 scenario suite", 40, 12, 1900, 24, size=16, check=False)
    d.text("Python design classes (iteration 1), from UC-D6, UC-I4, UC-I6, the escalation-case state machine and "
           "schema.sql. Each class lists the FRs it realises. Other students' classes appear only as boundary "
           "interfaces (blue S1, orange S2, grey shared).", 40, 36, 1900, 20, size=11, color="#4A5560", check=False)
    pkg(d, "p_mod", "moderation  (Module 9)", 30, 70, 1340, 1380, "#FBF8FE")
    pkg(d, "p_eval", "evaluation  (Module 10)", 1400, 70, 610, 620, "#FBF8FE")
    pkg(d, "p_bnd", "boundary: other modules", 1400, 720, 610, 730, "#F7F7F7")
    X = [60, 390, 720, 1050]
    w = 290
    K = lambda *a, **k: klass(d, *a, owner=k.pop("owner", "S3"), **k)  # noqa: E731

    y1 = 110
    K("IMod", "IModeration", X[0], y1, w, [], ["queue(community_id, filters): list[CaseSummary]",
                                              "case_detail(case_id): CaseDetail", "request_information(case_id, "
                                              "request, deadline)", "record_decision(case_id, kind, reason, ...)",
                                              "audit_log(filters): list[AuditEntry]"],
      frs="FR-T-10, FR-T-11, FR-M-05 (REST: /cases, /audit-log)", stereo="interface")
    K("IIntake", "ICaseIntake", X[1], y1, w, [], ["open_or_attach(transaction_id, trigger, reason): EscalationCase",
                                                 "withdraw(transaction_id)"],
      frs="FR-T-10, UC-D6 1b (one live case per transaction)", stereo="interface")
    K("Audit", "AuditLogService", X[2], y1, w, [], ["record(actor, action, target, outcome, reason?)",
                                                   "query(filters): list[AuditEntry]  {the view is logged}",
                                                   "verify_chain(): bool", "mask(entry): AuditEntry"],
      frs="FR-M-05, NFR-S-05, UC-I6")
    K("Entry", "AuditEntry", X[3], y1, w, ["occurred_at, actor_id, authorisation", "action, target_type, target_id",
                                          "previous_value, new_value (masked)", "outcome: SUCCESS | REJECTED, reason",
                                          "prev_hash, row_hash"], frs="FR-M-05 (audit_log row)", stereo="value")
    y2 = bottom(d, "IMod", "IIntake", "Audit", "Entry") + GAP
    K("CaseSvc", "CaseService", X[0], y2, w, ["- cases: CaseRepository", "- notifier: INotify"],
      ["open_or_attach(transaction_id, trigger, reason)", "queue(community_id, filters)", "case_detail(case_id)",
       "request_information(case_id, request,", "&#160;&#160;deadline)", "add_statement(case_id, party, text,", "&#160;&#160;attachments)",
       "withdraw(transaction_id)", "route_to_admin(case_id)"],
      frs="FR-T-10, FR-T-11 (step 2), FR-B-17, UC-D6 2a")
    K("Trail", "EvidenceTrailBuilder", X[1], y2, w, ["- events: IEventQuery"], ["build(case): EvidenceTrail",
                                                                              "gaps(trail): list[str]"],
      frs="FR-T-10, UC-D6 1, 1a (trail derived from the event log)")
    K("DecSvc", "DecisionService", X[2], y2, w, ["- lifecycle: ILifecycleCommands", "- audit: AuditLogService"],
      ["record_decision(case_id, moderator, kind,", "&#160;&#160;reason, safeguards?, resolved_outcome?)",
       "&#160;&#160;: ModeratorDecision", "allowed_kinds(case): set[DecisionKind]", "&#160;&#160;{ADR-0003}"],
      frs="FR-T-11, ADR-0003, ADR-0004, UC-I4 3c, 4a")
    K("Enums", "CaseTrigger, CaseStatus, DecisionKind", X[3], y2, w,
      ["CaseTrigger: DISPUTE | MANIPULATION_FLAG |", "&#160;&#160;HIGH_VALUE_LOW_CONFIDENCE |", "&#160;&#160;LOCALITY_HOLD | ENGINE_FAILURE",
       "CaseStatus: OPEN | AWAITING_INFORMATION |", "&#160;&#160;DECIDED | APPEALED | REVERSED | WITHDRAWN",
       "DecisionKind: CLEARED | SAFEGUARDS_IMPOSED |", "&#160;&#160;RESTRICTED | DISPUTE_RESOLVED", "&#160;&#160;(appeal, reversal kinds: iteration 2)"],
      stereo="enumeration", owner="ENUM")
    y3 = bottom(d, "CaseSvc", "Trail", "DecSvc", "Enums") + GAP
    K("Case", "EscalationCase", X[0], y3, w, ["id, transaction_id: UUID", "opened_event_id: int",
                                             "trigger_type: CaseTrigger", "hold_reason | dispute_reason",
                                             "raised_by: UUID | None", "status: CaseStatus", "priority: int {1..3}",
                                             "reason: str", "assigned_to: UUID | None", "info_deadline, opened_at, "
                                             "closed_at"], ["assign(moderator)", "await_information(deadline)",
                                                            "mark_no_response()", "close(decision | withdrawn)"],
      frs="FR-T-10; state machine C01&#8211;C11")
    K("TrailV", "EvidenceTrail", X[1], y3, w, ["events: list[LifecycleEvent]", "assessment: AssessmentResult | None",
                                              "condition_reports, statements", "attachments (metadata stripped)",
                                              "gaps: list[str]"], frs="FR-T-10, NFR-PR-03 (chat only if disputed)",
      stereo="value")
    K("Dec", "ModeratorDecision", X[2], y3, w, ["id, case_id: UUID", "decided_by: UUID, decider_role",
                                               "kind: DecisionKind", "reason: str  {mandatory}", "safeguards: list",
                                               "resolved_outcome: dict | None", "reverses_decision_id: UUID | None",
                                               "decided_at: datetime"],
      frs="FR-T-11, FR-B-15 (resolved outcome is evidence), ES-11")
    y4 = bottom(d, "Case", "TrailV", "Dec") + GAP + 30
    K("Stmt", "CaseStatement", X[0], y4, w, ["author_id, author_role", "statement: str", "created_at"],
      frs="FR-B-17, UC-B12 5, UC-I4 2")

    # evaluation (Module 10)
    K("Suite", "ScenarioSuite", 1430, 110, 270, ["- fixtures: list[ScenarioFixture]"],
      ["run(engine: IAssess): list[ScenarioResult]", "load(path): list[ScenarioFixture]"],
      frs="NFR-Q-01 (7 of 13 at Mid-1), test suite 11")
    K("Fixture", "ScenarioFixture", 1430, 330, 270, ["scenario_id: str", "transaction_context", "direct_evidence, "
                                                    "indirect_evidence", "manipulation_risk", "expected: ExpectedResult"],
      frs="scenario_fixtures_iteration1.json", stereo="value")
    K("Expected", "ExpectedResult", 1730, 330, 250, ["rule_fired, decision, state", "lifecycle_state, hold_reason",
                                                    "explanation facts"], frs="NFR-Q-01", stereo="value")
    K("SResult", "ScenarioResult", 1730, 110, 250, ["scenario_id: str", "state_ok, rule_ok: bool",
                                                   "lifecycle_ok, explanation_ok: bool", "passed: bool  {all four}"],
      frs="NFR-Q-01", stereo="value")
    # boundary interfaces
    K("ILife", "ILifecycleCommands", 1430, 770, 270, [], ["apply_decision(transaction_id, decision): event"],
      frs="Student 1, Module 3", stereo="interface", owner="S1")
    K("IEvt", "IEventQuery", 1730, 770, 250, [], ["load_stream(id)", "replay(id)", "verify_chain(id)"],
      frs="Student 1, Module 3", stereo="interface", owner="S1")
    K("INotify", "INotify", 1430, 1000, 270, [], ["notify(user, type, payload)"], frs="Module 7 stub",
      stereo="interface", owner="ENUM")
    K("IAssessB", "IAssess", 1730, 1000, 250, [], ["assess(request): AssessmentResult"], frs="Student 2, Module 5",
      stereo="interface", owner="S2")

    # ---------------- relationships
    gap1 = y2 - 30
    link(d, "CaseSvc", "IMod", "", style=REALISE, exit=(0.3, 0), entry=(0.3, 1))
    link(d, "CaseSvc", "IIntake", "", style=REALISE, exit=(0.7, 0), entry=(0.5, 1),
         points=[(60 + w * 0.7, gap1), (X[1] + w * 0.5, gap1)])
    link(d, "DecSvc", "IMod", "", style=REALISE, exit=(0.15, 0), entry=(0.75, 1),
         points=[(X[2] + w * 0.15, gap1 - 12), (60 + w * 0.75, gap1 - 12)])
    link(d, "DecSvc", "Audit", "&#171;use&#187;", style=DEPEND, exit=(0.6, 0), entry=(0.6, 1), label_dx=36, label_dy=0)
    link(d, "Audit", "Entry", "", style=DEPEND, exit=(1, 0.5), entry=(0, 0.5))
    link(d, "CaseSvc", "Trail", "&#171;use&#187;", style=DEPEND, exit=(1, 0.3), entry=(0, 0.3), label_dy=-10)
    link(d, "Trail", "TrailV", "&#171;creates&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    link(d, "CaseSvc", "Case", "manages", "1", "0..*", exit=(0.5, 1), entry=(0.5, 0), label_dx=36, label_dy=0)
    link(d, "DecSvc", "Dec", "&#171;creates&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    cb = bottom(d, "Case", "TrailV", "Dec") + 22
    link(d, "Case", "Dec", "decided by", "1", "0..*", exit=(0.8, 1), entry=(0.5, 1),
         points=[(60 + w * 0.8, cb), (X[2] + w * 0.5, cb)], label_x=0.0, label_dy=-10, mb_off=(0, 1))
    link(d, "Case", "Stmt", "", "1", "0..*", style=COMPOSE, exit=(0.3, 1), entry=(0.3, 0))
    link(d, "DecSvc", "ILife", "&#171;use&#187;", style=DEPEND, exit=(1, 0.9), entry=(0, 0.5),
         points=[(1030, Y(d, "DecSvc", 0.9)), (1030, Y(d, "ILife", 0.5))], label_x=0.4, label_dx=-28, label_dy=0)
    link(d, "Trail", "IEvt", "&#171;use&#187;", style=DEPEND, exit=(1, 0.6), entry=(0.5, 1),
         points=[(X[1] + w + 15, Y(d, "Trail", 0.6)), (X[1] + w + 15, cb + 26), (1855, cb + 26)], label_x=0.1,
         label_dy=-10)
    link(d, "CaseSvc", "INotify", "&#171;use&#187;", style=DEPEND, exit=(0, 0.5), entry=(0, 0.5),
         points=[(45, Y(d, "CaseSvc", 0.5)), (45, 1430), (1415, 1430), (1415, Y(d, "INotify", 0.5))], label_x=0.0,
         label_dy=-10)
    link(d, "Suite", "Fixture", "", "1", "7..*", style=AGGREG, exit=(0.5, 1), entry=(0.5, 0))
    link(d, "Fixture", "Expected", "", "1", "1", style=COMPOSE, exit=(1, 0.5), entry=(0, 0.5))
    link(d, "Suite", "SResult", "", style=DEPEND, exit=(1, 0.5), entry=(0, 0.5))
    link(d, "Suite", "IAssessB", "&#171;use&#187;", style=DEPEND, exit=(0, 0.5), entry=(0.5, 0),
         points=[(1415, Y(d, "Suite", 0.5)), (1415, 700), (1715, 700), (1715, 980), (1855, 980)], label_x=0.4,
         label_dy=-10)
    notes(d, "<b>Notes</b><br>&#8226; Module 9 changes a lifecycle state only through ILifecycleCommands.apply_decision() "
          "(one writer of lifecycle events, A8); the allowed decision kinds depend on the case type and hold reason "
          "(ADR-0003).<br>&#8226; The evidence trail is derived from the event log, never stored separately (UC-D6).<br>"
          "&#8226; ICaseIntake is realised inside the same database transaction as the hold or dispute event in iteration 1 "
          "(AR-3).<br>&#8226; The scenario suite tests the engine only through IAssess; the held-out attack generator "
          "(iteration 3) is a separate package.<br>&#8226; Relationship ends as in the Student 1 class diagram.",
          X[1], y4, 700, 130)
    return d


if __name__ == "__main__":
    class_diagram_s2().save(os.path.join(HERE, "class_diagram_s2.drawio"))
    class_diagram_s3().save(os.path.join(HERE, "class_diagram_s3.drawio"))
