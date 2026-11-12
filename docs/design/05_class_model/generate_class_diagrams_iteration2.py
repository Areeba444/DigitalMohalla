"""Generates the iteration 2 class diagrams of Student 1's and Student 2's packages (DA-11, drawn by Student 1).

    python generate_class_diagrams_iteration2.py  ->  class_diagram_s1_iteration2.drawio, class_diagram_s2_iteration2.drawio

These diagrams show what iteration 2 adds or changes. Unchanged iteration 1 classes are in
../05_class_model/ and are not redrawn; a changed class carries <<changed>> and lists only what it adds.
Notation and helpers are the iteration 1 ones (klass, link), so all class diagrams look alike. Each class names the
FRs it realises. Student 3's diagram (Module 9, 10) is Minahil's DA-11 part.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "class_model_it1", os.path.join(HERE, "generate_class_model.py"))
_cm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cm)
klass, link = _cm.klass, _cm.link
AGGREG, COMPOSE, DEPEND, REALISE, ASSOC = _cm.AGGREG, _cm.COMPOSE, _cm.DEPEND, _cm.REALISE, _cm.ASSOC

GAP = 46


def pkg(d, pid, name, x, y, w, h, colour):
    tab = int(len(name.replace("&#8212;", "-")) * 6.6) + 30
    p = d.node(f"<b>{name}</b>", x, y, w, h, f"shape=folder;fontStyle=0;tabWidth={tab};tabHeight=24;tabPosition=left;"
               f"html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=10;spacingTop=2;fontSize=12;"
               f"fillColor={colour};strokeColor=#8A9AAA;container=1;collapsible=0;", id=pid)
    d.mark_container(p, pass_through=True)
    return p


class Column:
    """Stacks classes top to bottom at one x; next() returns the y for the next class."""

    def __init__(self, d, x, y, w):
        self.d, self.x, self.y, self.w = d, x, y, w

    def add(self, cid, name, attrs=(), ops=(), frs="", owner="S1", stereo=None, w=None, x=None, keep_y=False):
        c = klass(self.d, cid, name, x if x is not None else self.x, self.y, w or self.w, attrs, ops, frs=frs,
                  owner=owner, stereo=stereo)
        if not keep_y:
            self.y = self.d.box(c)[3] + GAP
        return c

    def row(self, specs, w):
        """Several small classes side by side; the column continues under the tallest."""
        ids = []
        for k, (cid, name, attrs, ops, frs, owner, stereo) in enumerate(specs):
            ids.append(klass(self.d, cid, name, self.x + k * (w + 10), self.y, w, attrs, ops, frs=frs, owner=owner,
                             stereo=stereo))
        self.y = max(self.d.box(i)[3] for i in ids) + GAP
        return ids


def fit(d, pid, *cids, pad=24):
    """Grow a package to contain its classes."""
    p = d.by_id[pid]
    bottom = max(d.box(c)[3] for c in cids)
    p["h"] = bottom + pad - p["y"]


def vlink(d, a, b, style, fa=0.5, fb=0.5, name=""):
    """Vertical link from the bottom of a to the top of b (a above b)."""
    return link(d, a, b, name, style=style, exit=(fa, 1), entry=(fb, 0))


def lane_link(d, a, b, lane_x, style, side="R", name=""):
    """Link between two classes in one column through a vertical lane beside it."""
    ya = (d.box(a)[1] + d.box(a)[3]) / 2
    yb = (d.box(b)[1] + d.box(b)[3]) / 2
    f = 1 if side == "R" else 0
    return link(d, a, b, name, style=style, exit=(f, 0.5), entry=(f, 0.5), points=[(lane_x, ya), (lane_x, yb)])


# =============================================================================== Student 1
def class_diagram_s1() -> Diagram:
    d = Diagram("Class diagram S1, iteration 2 (DA-11)", 2320, 1900)
    d.text("<b>Digital Mohalla &#8212; Class diagram, Student 1 packages, iteration 2</b> (DA-11, v2.0): Module 1 joining "
           "and locality, Module 3 listings, counter-offer and scheduler, Module 4 keyword search", 40, 12, 2200, 24,
           size=16, check=False)
    d.text("Shows only what iteration 2 adds or changes; unchanged classes are in the iteration 1 diagram "
           "(class_diagram_s1.drawio). &#171;changed&#187; = existing class, only its additions listed. Orange = Student 2 "
           "interfaces Student 1 depends on.", 40, 36, 2200, 20, size=11, color="#4A5560", check=False)
    pa = pkg(d, "p_acc", "accounts  (Module 1)", 30, 70, 540, 200, "#F7FAFD")
    pl = pkg(d, "p_life", "lifecycle and listings  (Module 3)", 600, 70, 1040, 200, "#F7FAFD")
    ps = pkg(d, "p_srch", "search  (Module 4, Student 1 part)", 1670, 70, 620, 200, "#F7FAFD")

    # ---------------- accounts
    A = Column(d, 60, 120, 480)
    A.add("Reg", "RegistrationService", [], ["register(email, password, display_name, terms_accepted): Account",
                                             "  # generic error if the identifier exists (FR-A-01)"],
          frs="FR-A-01, NFR-S-01", stereo="service")
    A.add("Acc", "User", ["terms_accepted_at: datetime | None"], [], frs="FR-A-01", stereo="changed")
    A.add("MemSvc", "MembershipService", ["- locality: GeofenceInvitationVerifier", "- notify: INotify"],
          ["communities(query): list[CommunitySummary]", "request_join(user, community, LocalityInput, code)",
           "  : Membership", "queue(moderator): list[MembershipRequest]",
           "decide(moderator, membership, kind, reason): MembershipDecision", "reverse(moderator, decision, reason)"],
          frs="FR-A-06, A-09, A-10, A-11", stereo="application service")
    A.add("Ver", "GeofenceInvitationVerifier", [], ["evaluate(fix, accuracy, mock_flag, permission_refused,",
                                                    "  invitation, duplicate): LocalityResult",
                                                    "  # fix kept in memory only; never stored"],
          frs="FR-A-07, A-08 (built in it. 2; designed in A11)", stereo="service")
    A.add("Inv", "InvitationService", [], ["issue(member, community): str  # code shown once", "redeem(code, community): "
                                                                                           "Invitation"],
          frs="FR-A-07, UC-A3 3d", stereo="service")
    A.add("MemDec", "MembershipDecision", ["membership_id, decided_by: UUID", "kind: MembershipDecisionKind",
                                          "reason: str", "reverses_decision_id: UUID | None", "decided_at: datetime"],
          frs="FR-A-10, FR-A-11 (append-only)", stereo="entity")
    A.add("MemKind", "MembershipDecisionKind", ["APPROVED, REJECTED,", "INFO_REQUESTED, REVERSED"], owner="ENUM",
          stereo="enumeration")
    vlink(d, "Reg", "Acc", DEPEND, name="&#171;create&#187;")
    vlink(d, "MemSvc", "Ver", DEPEND)
    vlink(d, "Ver", "Inv", DEPEND)
    lane_link(d, "MemSvc", "MemDec", 556, DEPEND, name="")
    vlink(d, "MemDec", "MemKind", ASSOC)
    fit(d, "p_acc", "MemKind")

    # ---------------- lifecycle: column 1
    L1 = Column(d, 630, 120, 470)
    L1.add("Bor", "BorrowingService", ["- notify: INotify"],
           ["counter_offer(id, lender, period)  # I07", "respond_counter(id, borrower, accept: bool)  # T29 / I08",
            "request_extension(id, borrower, new_due)  # I03", "respond_extension(id, lender, approve)  # I04 / I05",
            "expire(id) / no_show(id) / remind(id, step)  # system", "escalate_overdue(id)  # T24"],
           frs="FR-B-10, B-12, B-14 (adds to iteration 1)", stereo="changed")
    L1.add("Ctr", "CounterOffer", ["proposed_period: DateTimeRange", "offered_at: datetime", "open: bool"],
           ["from_events(events): CounterOffer | None"], frs="FR-B-10, ADR-0015", stereo="value")
    L1.add("Life", "TransitionTable", ["lifecycle v3: 39 leaf rows", "T25a, T25b, T25c by possession", "T29, I07, I08"],
           ["lookup(state, event): list[Transition]"], frs="FR-B-08, ADR-0009, ADR-0015", stereo="changed")
    L1.add("Pos", "Possession", ["NOT_HANDED_OVER, WITH_BORROWER,", "RETURNED, LOST  (ADR-0009)"], owner="ENUM",
           stereo="enumeration")
    vlink(d, "Bor", "Ctr", COMPOSE, name="")
    lane_link(d, "Bor", "Life", 616, DEPEND, side="L")
    vlink(d, "Life", "Pos", ASSOC)

    # ---------------- lifecycle: column 2
    L2 = Column(d, 1150, 120, 470)
    L2.add("LstSvc", "ListingService", ["- embeddings: EmbeddingQueue"],
           ["create(lender, draft): Listing", "update(lender, id, changes): Listing", "publish(id) / pause(id) / expire(id)"],
           frs="FR-B-01, FR-B-18", stereo="application service")
    L2.add("Lst", "Item", ["condition: ItemCondition", "usage_terms, handover_method: str", "search_terms: str  # e.g. Roman Urdu",
                           "expires_at, updated_at: datetime"], ["can_publish(): bool  # description + condition"],
           frs="FR-B-01", stereo="changed")
    L2.add("Run", "JobRunner", ["- jobs: list[Job]", "- runs: JobRunStore"], ["run_due_jobs(now, as_of=None): JobReport",
                                                                               "  # advisory lock; claim, act, finish"],
           frs="FR-B-18, NFR-R-05, ADR-0012", stereo="application service")
    L2.add("Job", "Job", [], ["name: str", "due(now): list[DueItem]", "run(item, service: BorrowingService): None"],
           frs="FR-B-18", stereo="interface")
    jobs = L2.row([("J1", "NoShowJob", [], ["due: ACCEPTED past grace"], "FR-B-12", "S1", None),
                   ("J2", "OverdueJob", [], ["due: ACTIVE past limit"], "FR-B-14", "S1", None),
                   ("J3", "ExpiryJob", [], ["due: ASSESSED past window"], "FR-B-10", "S1", None)], 150)
    L2.add("Store", "JobRunStore", [], ["claim(job, due_key): bool  # unique (job, key)", "finish(id, status, error)"],
           frs="NFR-R-05 (job_run table)", stereo="port")
    vlink(d, "LstSvc", "Lst", DEPEND)
    vlink(d, "Run", "Job", AGGREG, name="")
    for k, j in enumerate(jobs):
        link(d, j, "Job", "", style=REALISE, exit=(0.5, 0), entry=((75 + k * 160) / 470, 1))
    lane_link(d, "Run", "Store", 1636, DEPEND)
    # JobRunner appends events through BorrowingService (same validator and audit as a user's command)
    yr = (d.box("Run")[1] + d.box("Run")[3]) / 2
    yb = d.box("Bor")[1] + 40
    link(d, "Run", "Bor", "", style=DEPEND, exit=(0, 0.5), entry=(1, (yb - d.box("Bor")[1]) / (d.box("Bor")[3] - d.box("Bor")[1])),
         points=[(1125, yr), (1125, yb)])
    fit(d, "p_life", "Store", "Pos")

    # ---------------- search (S1 part)
    S = Column(d, 1700, 120, 560)
    S.add("IRet", "IRetriever", [], ["retrieve(query, filters, limit): list[Candidate]"], frs="FR-S-01, FR-S-02",
          stereo="interface")
    S.add("Kw", "KeywordRetriever", [], ["retrieve(...)  # search_tsv @@ query, trigram on title",
                                        "  # community, PUBLISHED, not blocked: inside the query (I-5)"],
          frs="FR-S-02, FR-S-03", stereo="service")
    S.add("Flt", "SearchFilters", ["category_id, community_id: optional", "dates: DateTimeRange | None",
                                  "max_deposit: Decimal | None", "condition: ItemCondition | None",
                                  "sort: relevance | evidence | newest"], frs="FR-S-03 (no radius: no coordinates)",
          stereo="value")
    S.add("Cand", "Candidate", ["item_id: UUID", "keyword_score: float", "semantic_score: float | None"],
          frs="FR-S-01", stereo="value")
    link(d, "Kw", "IRet", "", style=REALISE, exit=(0.5, 0), entry=(0.5, 1))
    vlink(d, "Kw", "Flt", DEPEND)
    lane_link(d, "Kw", "Cand", 2276, DEPEND)
    fit(d, "p_srch", "Cand")

    # ---------------- boundary: Student 2 interfaces
    by = d.box("p_srch")[3] + 40
    pkg(d, "p_b2", "boundary: Student 2 (Modules 4, 5, 7)", 1670, by, 620, 200, "#FFFAF5")
    B = Column(d, 1700, by + 50, 560)
    B.add("INot", "INotify", [], ["notify(user, type, payload, dedupe_key)"], frs="FR-C-02 (used by jobs, membership)",
          owner="S2", stereo="interface")
    B.add("IAss", "IAssess", [], ["assess(request): AssessmentResult  # re-run after T29"], frs="FR-T-01", owner="S2",
          stereo="interface")
    B.add("ISem", "SemanticRetriever", [], ["retrieve(...)  # implements IRetriever"], frs="FR-S-01", owner="S2",
          stereo="service")
    fit(d, "p_b2", "ISem")
    d.height = int(max(d.box("p_acc")[3], d.box("p_life")[3], d.box("p_b2")[3]) + 40)
    return d


# =============================================================================== Student 2
def class_diagram_s2() -> Diagram:
    d = Diagram("Class diagram S2, iteration 2 (DA-11)", 2320, 1900)
    d.text("<b>Digital Mohalla &#8212; Class diagram, Student 2 packages, iteration 2</b> (DA-11, v2.0, drawn by Student 1 "
           "for Areeba's review): Module 5 completion, Module 4 meaning-based search and ranking, Module 7 notifications",
           40, 12, 2200, 24, size=16, check=False)
    d.text("Shows only what iteration 2 adds or changes; unchanged classes are in class_diagram_s2.drawio of iteration 1. "
           "&#171;changed&#187; = existing class, only its additions listed. Blue = Student 1 and purple = Student 3 classes "
           "Student 2 depends on.", 40, 36, 2200, 20, size=11, color="#4A5560", check=False)
    pkg(d, "p_as", "assurance  (Module 5)", 30, 70, 1040, 200, "#FFFCF8")
    pkg(d, "p_se", "search  (Module 4, Student 2 part)", 1100, 70, 560, 200, "#FFFCF8")
    pkg(d, "p_no", "notifications  (Module 7)", 1690, 70, 600, 200, "#FFFCF8")
    K = dict(owner="S2")

    A1 = Column(d, 60, 120, 470)
    A1.add("Beta", "BetaPosteriorEstimator", [], ["estimate(subject, role, metric, events, profile)", "  : TrustEstimate",
                                                 "repeat_discount(events): weights  # trivial exchanges"],
           frs="FR-T-02, FR-T-03 (roles and metrics, pair-repeat discount)", stereo="changed", **K)
    A1.add("RM", "RoleMetric", ["role: BORROWER | LENDER", "metric: ON_TIME_RETURN | CONDITION_AGREED |", "  DISPUTE_FREE"],
           frs="Overview §5.2 (never mixed)", stereo="value", **K)
    A1.add("Pop", "PopulationBaseline", [], ["baseline(role, metric): float  # fallback 0.5 below 30",
                                            "refresh(now)  # nightly job"], frs="FR-T-04 baseline b, DA-15",
           stereo="service", **K)
    A1.add("Len", "LenderEvidence", ["- estimator: BetaPosteriorEstimator", "- baseline: PopulationBaseline"],
           ["lender_factors(lender, profile): list[EvidenceRecord]", "ranking_value(lender): float  # internal only"],
           frs="FR-S-04, FR-S-01; never one number to users", stereo="service", **K)
    A1.add("Rev", "ReviewService", [], ["submit(actor, txn, ratings, comment): Review", "edit(actor, review, changes)  # "
                                                                                     "edit window"],
           frs="FR-T-09, FR-B-15 (D1)", stereo="application service", **K)
    A1.add("RevE", "Review", ["retaliation_flag, similarity_flag: bool", "  # set by the service, confirmed by a moderator"],
           [], frs="FR-T-09", stereo="changed", **K)
    vlink(d, "Beta", "RM", ASSOC)
    vlink(d, "Pop", "Len", DEPEND, name="")
    lane_link(d, "Len", "Beta", 46, DEPEND, side="L")
    vlink(d, "Rev", "RevE", DEPEND, name="&#171;create&#187;")

    A2 = Column(d, 570, 120, 470)
    A2.add("Det", "ManipulationDetector", ["- signals: list[Signal]"], ["assess(subject, data, window): ManipulationRisk",
                                                                        "  # weights renormalised over available signals"],
           frs="FR-T-05, ADR-0007 (all five signals in it. 2)", stereo="changed", **K)
    A2.add("Sig", "Signal", [], ["name, weight: from config", "compute(subject, data): SignalValue"], frs="FR-T-05",
           stereo="interface", **K)
    sigs = A2.row([("S2", "RatingVelocity", [], ["7 d vs 83 d"], "S2", "S2", None),
                   ("S3", "NewAccountActivity", [], ["age < 30 d, 14 d count"], "S3", "S2", None),
                   ("S5", "InvitationLinkage", [], ["invite tree, 90 d"], "S5", "S2", None)], 150)
    A2.add("Pol", "DecisionPolicy", [], ["decide(direct, indirect, risk, ctx)", "  # rule order R1, R2, R4, R3, ... "
                                                                             "(ADR-0010)"],
           frs="FR-T-06, DM09", stereo="changed", **K)
    vlink(d, "Det", "Sig", AGGREG, name="")
    for k, s in enumerate(sigs):
        link(d, s, "Sig", "", style=REALISE, exit=(0.5, 0), entry=((75 + k * 160) / 470, 1))
    fit(d, "p_as", "RevE", "Pol")

    S = Column(d, 1130, 120, 500)
    S.add("Svc", "SearchService", ["- keyword: IRetriever", "- semantic: SemanticRetriever", "- ranker: HybridRanker",
                                  "- log: SearchLogger"], ["search(actor, query, filters, sort): SearchResults",
                                                           "  # mode HYBRID or KEYWORD_ONLY"],
          frs="FR-S-01, S-02, S-05", stereo="application service", **K)
    S.add("Sem", "SemanticRetriever", [], ["retrieve(query, filters, limit): list[Candidate]",
                                          "  # cosine over item_embedding, filters in SQL"], frs="FR-S-01", stereo="service",
          **K)
    S.add("Emb", "EmbeddingProvider", [], ["model: str", "embed(texts): list[Vector]  # may raise ModelUnavailable"],
          frs="FR-S-02 fallback, ADR-0016", stereo="port", **K)
    S.add("EJob", "EmbeddingJob", [], ["due(now): items whose text hash changed", "run(item)"],
          frs="FR-B-03 (retry later)", stereo="service", **K)
    S.add("Rank", "HybridRanker", ["- weights: RankingWeights", "- lenders: ILenderEvidence"],
          ["rank(candidates, ctx): list[RankedResult]", "reason(result): str  # one line, no score"],
          frs="FR-S-01, Algorithm 5", stereo="service", **K)
    S.add("W", "RankingWeights", ["relevance 0.40, lender_evidence 0.30,", "availability 0.15, same_community 0.10,",
                                  "freshness 0.05; config_version"], frs="NFR-D-01", stereo="value", **K)
    S.add("RR", "RankedResult", ["item_id: UUID", "score_parts: dict  # stored, not shown", "reason: str"],
          frs="FR-S-01, FR-S-05", stereo="value", **K)
    vlink(d, "Svc", "Sem", DEPEND)
    vlink(d, "Sem", "Emb", DEPEND)
    link(d, "EJob", "Emb", "", style=DEPEND, exit=(0.5, 0), entry=(0.5, 1))
    lane_link(d, "Svc", "Rank", 1646, DEPEND)
    vlink(d, "Rank", "W", ASSOC)
    lane_link(d, "Rank", "RR", 1116, DEPEND, side="L")
    fit(d, "p_se", "RR")

    N = Column(d, 1720, 120, 540)
    N.add("NSvc", "NotificationService", [], ["notify(user, type, payload, dedupe_key): None  # once per key",
                                             "inbox(user, unread_only): list[Notification]", "mark_read(user, ids)"],
          frs="FR-C-02 (in-app), FR-B-06, FR-B-17, ADR-0013", stereo="application service", **K)
    N.add("Note", "Notification", ["user_id: UUID", "type: str", "payload: dict  # no location", "dedupe_key: str",
                                  "created_at, read_at"], frs="FR-C-02", stereo="entity", **K)
    vlink(d, "NSvc", "Note", COMPOSE, name="")
    fit(d, "p_no", "Note")

    by = d.box("p_no")[3] + 40
    pkg(d, "p_b", "boundary: Students 1 and 3", 1690, by, 600, 200, "#F7FAFD")
    B = Column(d, 1720, by + 50, 540)
    B.add("BRet", "IRetriever / KeywordRetriever", [], ["retrieve(...)  # Student 1"], frs="FR-S-02", owner="S1",
          stereo="interface")
    B.add("BLog", "SearchLogger", [], ["log_query(...), log_impressions(...), log_click(...)  # Student 3"],
          frs="FR-S-05", owner="S3", stereo="service")
    fit(d, "p_b", "BLog")
    d.height = int(max(d.box("p_as")[3], d.box("p_se")[3], d.box("p_b")[3]) + 40)
    return d


if __name__ == "__main__":
    class_diagram_s1().save(os.path.join(HERE, "class_diagram_s1_iteration2.drawio"))
    class_diagram_s2().save(os.path.join(HERE, "class_diagram_s2_iteration2.drawio"))
