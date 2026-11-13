"""Generates the A7 class diagrams of Student 2's and Student 3's packages.

    python generate_class_diagrams_s2_s3.py  ->  class_diagram_s2.drawio
    (class_diagram_s3.drawio: generate_class_diagram_s3.py since iteration 2, DA-11)

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
from generate_class_model import (AGGREG, COMPOSE, DEPEND, REALISE, G, klass, link)  # noqa: E402

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
    d = Diagram("S2 (1 of 2): assurance engine", 2140, 1800)
    d.text("<b>Digital Mohalla &#8212; Class diagram, Student 2 packages (1 of 2)</b> (A7 v1.0; iteration 2 v2.0, DA-11): "
           "Module 5 estimation, manipulation detection, decision policy and explanation", 40, 12, 1900, 24, size=16,
           check=False)
    d.text("Python design classes (iteration 1), from the Algorithm doc &#167;2&#8211;&#167;6 and the assurance data "
           "dictionary. Each class lists the FRs it realises. <font color='#0A7A36'>Green = added or changed in iteration 2</font>; "
           "new iteration 2 classes are on page 2. Student 1 classes appear only as the interfaces Student 2 depends on "
           "(blue).", 40, 36, 1900, 20, size=11, color="#4A5560", check=False)
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
    K("Beta", "BetaPosteriorEstimator", COLS[2], y2, W, [], [G("estimate(subject, role, metric, events, profile?)"),
                                                            G("&#160;&#160;: TrustEstimate  # roles never mixed"),
                                                            "posterior_mean(s_w, f_w): float  {shared, ADR-0006}",
                                                            "weight(age_days, similarity): float",
                                                            G("repeat_discount(events): weights  # same pair")],
      frs="FR-T-02, FR-T-03")
    K("Explain", "ExplanationBuilder", COLS[3], y2, W, [], ["build(direct, indirect, risk, decision): "
                                                           "list[EvidenceRecord]", "render(records): str"],
      frs="FR-T-08, NFR-U-01 (never one number)")
    K("Policy", "DecisionPolicy", COLS[4], y2, W, ["- thresholds: tau_mu, tau_L, n_min, rho_sup"],
      ["decide(direct, indirect, risk, ctx)", "&#160;&#160;: DecisionPolicyResult", "&#160;&#160;rules R1&#8211;R5, R6_DISPUTE,",
       "&#160;&#160;R6_SPARSE, R7&#8211;R9", G("&#160;&#160;order R1, R2, R4, R3, ... (ADR-0010)")],
      frs="FR-T-06, ADR-0007, ADR-0008, DM09")
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
                                                          "- corroboration: 2 signals &#8805; 0.5",
                                                          G("- S1 to S5 all active (S2, S3, S5 new)")],
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
    # iteration 2: the three remaining signals of ADR-0007 (green border = new class)
    for k, (cid, name, attr) in enumerate((("SigS2", "RatingVelocity", "S2: ratings in 7 d vs 83 d"),
                                           ("SigS3", "NewAccountActivity", "S3: age &lt; 30 d, 14 d count"),
                                           ("SigS5", "InvitationLinkage", "S5: invite tree, 90 d"))):
        K(cid, name, 810 + k * 290, y6, 250, [attr], ["evaluate(...)"], frs="FR-T-05, ADR-0007", new=True)
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
    for k, cid in enumerate(("SigS2", "SigS3", "SigS5")):
        link(d, cid, "SignalCheck", "", style=REALISE, exit=(0.5, 0), entry=(0.95, 1),
             points=[(935 + k * 290, y6 - 32), (685, y6 - 32)])
    link(d, "IInd", "IndEv", "&#171;returns&#187;", style=DEPEND, exit=(0.5, 1), entry=(0.5, 0), label_dx=40, label_dy=0)
    notes(d, "<b>Notes</b><br>&#8226; AssuranceFacade is the only entry point: Module 3 calls IAssess.assess() once per "
          "request (A8); a timeout gives an engine_failure hold, never a default state (FR-T-07).<br>&#8226; Trust and "
          "manipulation risk stay separate attributes of AssessmentResult and are never averaged (FR-T-06).<br>&#8226; "
          "RatingVelocity (S2), NewAccountActivity (S3) and InvitationLinkage (S5) are the iteration 2 SignalCheck "
          "realisations (green).<br>&#8226; BetaPosteriorEstimator.posterior_mean is also the trust-edge weight (ADR-0006).<br>"
          "&#8226; Relationship ends: &#9670; composition, &#9671; aggregation, dashed open arrow = dependency, dashed "
          "hollow triangle = realisation.", 1100, y6 + 130, 620, 150)
    d.by_id["p_s2"]["h"] = y6 + 320 - 70
    d.height = y6 + 350
    return d


# =============================================================================== Student 3
# class_diagram_s3 moved to generate_class_diagram_s3.py in iteration 2 (DA-11, v2.0), so Student 2's and
# Student 3's diagrams can change independently.


if __name__ == "__main__":
    # class_diagram_s2.drawio (page 1 = class_diagram_s2(), page 2 = iteration 2 packages) is written by
    # generate_class_diagrams_iteration2.py.
    pass
