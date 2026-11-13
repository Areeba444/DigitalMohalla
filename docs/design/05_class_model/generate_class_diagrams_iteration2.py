"""Draws the iteration 2 packages of Students 1 and 2 (DA-11) as sections of the whole-system class diagram.

    python generate_class_diagrams_iteration2.py  ->  class_diagram.drawio (via generate_class_diagram.py)

class_diagram_s1_page2(unified=True) and class_diagram_s2_page2(unified=True) are the sections used there; without
unified they still draw the stand-alone two-page version described below (kept for comparison, not saved).

Each file is the whole design of that student's packages at iteration 2:
  page 1  the iteration 1 diagram (generate_class_model.class_diagram, generate_class_diagrams_s2_s3.class_diagram_s2)
          with the members iteration 2 adds or changes drawn green;
  page 2  the packages and classes that are new in iteration 2 (green border). A class whose members are on page 1
          appears here by name only (attribute and operation compartments suppressed, UML 2.5 §9.2.4).
The iteration 1 versions are kept in archive_v1/ (class_diagram_s1_iteration1.drawio, class_diagram_s2_iteration1.drawio).
Notation and helpers are the iteration 1 ones (klass, link), so all class diagrams look alike. Each class names the
FRs it realises. Student 3's diagram (class_diagram_s3.drawio) is Minahil's DA-11 part and uses the same helpers.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
sys.path.insert(0, HERE)
from drawio import Diagram, save_pages  # noqa: E402

_spec = importlib.util.spec_from_file_location("class_model_it1", os.path.join(HERE, "generate_class_model.py"))
_cm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cm)
klass, link, G = _cm.klass, _cm.link, _cm.G
AGGREG, COMPOSE, DEPEND, REALISE, ASSOC = _cm.AGGREG, _cm.COMPOSE, _cm.DEPEND, _cm.REALISE, _cm.ASSOC
import generate_class_diagrams_s2_s3 as _s23  # noqa: E402

GAP = 46
REF = "members: page 1"


def pkg(d, pid, name, x, y, w, h, colour):
    tab = int(len(name.replace("&#8212;", "-")) * 6.6) + 30
    p = d.node(f"<b>{name}</b>", x, y, w, h, f"shape=folder;fontStyle=0;tabWidth={tab};tabHeight=24;tabPosition=left;"
               f"html=1;whiteSpace=wrap;verticalAlign=top;align=left;spacingLeft=10;spacingTop=2;fontSize=12;"
               f"fillColor={colour};strokeColor=#8A9AAA;container=1;collapsible=0;", id=pid)
    d.mark_container(p, pass_through=True)
    return p


class Column:
    """Stacks classes top to bottom at one x; add() moves the column below the new class."""

    def __init__(self, d, x, y, w):
        self.d, self.x, self.y, self.w = d, x, y, w

    def add(self, cid, name, attrs=(), ops=(), frs="", owner="S1", stereo=None, new=True, w=None, x=None):
        c = klass(self.d, cid, name, x if x is not None else self.x, self.y, w or self.w, attrs, ops, frs=frs,
                  owner=owner, stereo=stereo, new=new)
        self.y = self.d.box(c)[3] + GAP
        return c

    def ref(self, cid, name, owner="S1", stereo=None):
        """A class drawn in full on page 1 (or in another student's diagram): name only."""
        return self.add(cid, name, [], [], frs=REF if owner == "S1" or owner == "S2" else "", owner=owner,
                        stereo=stereo, new=False)

    def row(self, specs, w):
        """Several small classes side by side; the column continues under the tallest."""
        ids = [klass(self.d, cid, name, self.x + k * (w + 10), self.y, w, attrs, ops, frs=frs, owner=owner,
                     stereo=stereo, new=True)
               for k, (cid, name, attrs, ops, frs, owner, stereo) in enumerate(specs)]
        self.y = max(self.d.box(i)[3] for i in ids) + GAP
        return ids


def fit(d, pid, *cids, pad=24):
    """Grow a package to contain its classes."""
    p = d.by_id[pid]
    p["h"] = max(d.box(c)[3] for c in cids) + pad - p["y"]


def vlink(d, a, b, style, fa=0.5, fb=0.5, name=""):
    """Vertical link from the bottom of a to the top of b (a above b)."""
    return link(d, a, b, name, style=style, exit=(fa, 1), entry=(fb, 0))


def lane_link(d, a, b, lane_x, style, side="R", name=""):
    """Link between two classes in one column through a vertical lane beside it."""
    ya = (d.box(a)[1] + d.box(a)[3]) / 2
    yb = (d.box(b)[1] + d.box(b)[3]) / 2
    f = 1 if side == "R" else 0
    return link(d, a, b, name, style=style, exit=(f, 0.5), entry=(f, 0.5), points=[(lane_x, ya), (lane_x, yb)])


def header(d, title, sub):
    d.text(title, 40, 12, 2200, 24, size=16, check=False)
    d.text(sub, 40, 36, 2200, 20, size=11, color="#4A5560", check=False)


# =============================================================================== Student 1, page 2
def class_diagram_s1_page2(unified: bool = False) -> Diagram:
    """unified=True: a section of the whole-system class diagram (generate_class_diagram.py): no title, no boundary
    package, no name-only references (the real classes are on the same canvas)."""
    d = Diagram("S1 (2 of 2): iteration 2 packages", 2320, 1900)
    U = unified
    if not U:
      header(d, "<b>Digital Mohalla &#8212; Class diagram, Student 1 packages (2 of 2)</b> (iteration 2 v2.0, DA-11): "
              "Module 1 registration and joining, Module 3 listings, counter-offer and scheduler, Module 4 search retrieval",
           "Classes new in iteration 2 have a <font color='#0A7A36'>green border</font>; green text = member added in iteration 2. "
           "A box showing only &#8220;members: page 1&#8221; is drawn in full on page 1. Orange = Student 2, purple = Student 3 "
           "classes Student 1 depends on.")
    pkg(d, "p_acc", "accounts.membership  (Module 1)" if U else "accounts  (Module 1)", 30, 70, 540, 200, "#F7FAFD")
    pkg(d, "p_life", "lifecycle.listings and scheduling  (Module 3)" if U else "lifecycle and listings  (Module 3)",
        600, 70, 1040, 200, "#F7FAFD")
    pkg(d, "p_srch", "search.retrieval  (Module 4, S1)" if U else "search retrieval  (Module 4, Student 1 part)", 1670,
        70, 620, 200, "#F7FAFD")

    # ---------------- accounts
    A = Column(d, 60, 120, 480)
    A.add("Reg", "RegistrationService", [], ["register(email, password, display_name, terms_accepted): User",
                                             "  # same generic answer if the e-mail exists (FR-A-01)"],
          frs="FR-A-01, NFR-S-01 (UC-A1)", stereo="application service")
    if not U:
        A.ref("Acc", "User")
    A.add("MemSvc", "MembershipService", ["- locality: GeofenceInvitationVerifier", "- invitations: InvitationService",
                                          "- notify: INotify"],
          ["communities(query): list[CommunitySummary]", "request_join(user, community, LocalityInput, code)",
           "  : Membership  # OPEN + VERIFIED: approved at once", "queue(moderator): list[MembershipRequest]",
           "decide(moderator, membership, kind, reason): MembershipDecision", "reverse(moderator, decision, reason)"],
          frs="FR-A-06, A-09, A-10, A-11 (UC-A3, UC-A4)", stereo="application service")
    A.add("Inv", "InvitationService", [], ["issue(member, community): str  # code shown once",
                                           "redeem(code, community): Invitation"],
          frs="FR-A-07, UC-A3 3d", stereo="service")
    if not U:
        A.ref("Ver", "GeofenceInvitationVerifier", stereo="service")
    A.add("MemDec", "MembershipDecision", ["membership_id, decided_by: UUID", "kind: MembershipDecisionKind",
                                          "reason: str", "reverses_decision_id: UUID | None", "decided_at: datetime"],
          frs="FR-A-10, FR-A-11 (append-only)", stereo="entity")
    A.add("MemKind", "MembershipDecisionKind", ["APPROVED, REJECTED,", "INFO_REQUESTED, REVERSED"], owner="ENUM",
          stereo="enumeration")
    if not U:
        vlink(d, "Reg", "Acc", DEPEND, name="&#171;create&#187;")
        vlink(d, "Inv", "Ver", DEPEND, name="&#171;use&#187;")
    vlink(d, "MemSvc", "Inv", DEPEND)
    lane_link(d, "MemSvc", "MemDec", 556, DEPEND, name="")
    vlink(d, "MemDec", "MemKind", ASSOC)
    fit(d, "p_acc", "MemKind")

    # ---------------- lifecycle: column 1
    L1 = Column(d, 630, 120, 470)
    if not U:
        L1.ref("Bor", "BorrowingService", stereo="application service")
    L1.add("Ctr", "CounterOffer", ["proposed_period: DateTimeRange", "offered_at: datetime", "open: bool"],
           ["from_events(events): CounterOffer | None  # replay"], frs="FR-B-10, ADR-0015", stereo="value")
    if not U:
        L1.ref("Life", "TransitionTable")
        vlink(d, "Bor", "Ctr", COMPOSE, name="")
        lane_link(d, "Bor", "Life", 616, DEPEND, side="L")

    # ---------------- lifecycle: column 2
    L2 = Column(d, 1150, 120, 470)
    L2.add("LstSvc", "ListingService", ["- embeddings: EmbeddingJob"],
           ["create(lender, draft): Item", "update(lender, id, changes): Item", "publish(id) / pause(id) / expire(id)"],
           frs="FR-B-01, FR-B-18 (UC-B1)", stereo="application service")
    L2.add("Lst", "Item", ["id, owner_id, community_id, category_id: UUID", "title: str", "value_band: ValueBand",
                           "deposit_amount: Decimal | None  # record-only", "status: ItemStatus",
                           G("description: str"), G("condition: ItemCondition"), G("usage_terms, handover_method: str"),
                           G("search_terms: str  # e.g. Roman Urdu names"), G("expires_at, updated_at: datetime")],
           [G("can_publish(): bool  # description + condition")], frs="FR-B-01 (schema v2.4)", stereo="entity", new=False)
    L2.add("Run", "JobRunner", ["- jobs: list[Job]", "- runs: JobRunStore"],
           ["register(job: Job): None", "run_due_jobs(now, as_of=None): JobReport", "  # advisory lock; claim, act, finish"],
           frs="FR-B-18, NFR-R-05, ADR-0012 (UC-B13)", stereo="application service")
    L2.add("Job", "Job", [], ["name: str", "due(now): list[DueItem]", "run(item): None"],
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
    # jobs append events through BorrowingService (same validator and audit as a user's command)
    if not U:
        yr = (d.box("Run")[1] + d.box("Run")[3]) / 2
        yb = (d.box("Bor")[1] + d.box("Bor")[3]) / 2
        link(d, "Run", "Bor", "", style=DEPEND, exit=(0, 0.5), entry=(1, 0.5), points=[(1125, yr), (1125, yb)])
    fit(d, "p_life", "Store", "Ctr" if U else "Life")

    # ---------------- search retrieval (S1 part), as in sequence (i)
    S = Column(d, 1700, 120, 560)
    S.add("ISearch", "ISearch", [], ["search(member, query, filters, sort): SearchResults"],
          frs="FR-S-01 to S-03 (used by the app through the REST API)", stereo="interface")
    S.add("Svc", "SearchService", ["- embedder: EmbeddingProvider", "- ranker: HybridRanker", "- log: SearchLogger"],
          ["search(member, query, filters, sort): SearchResults",
           "retrieve(query, vector | None, filters, limit): list[Candidate]",
           "  # one SQL query: full-text rank + vector distance;",
           "  # community, PUBLISHED, not blocked inside it (I-5)",
           "  # no vector: keyword only, mode KEYWORD_ONLY (FR-S-02)"],
          frs="FR-S-01, S-02, S-03, ADR-0016 (sequence i)", stereo="application service")
    S.add("Flt", "SearchFilters", ["category_id: UUID | None", "dates: DateTimeRange | None",
                                  "max_deposit: Decimal | None", "condition: ItemCondition | None",
                                  "sort: RELEVANCE | EVIDENCE | NEWEST"], frs="FR-S-03 (no radius: no coordinates)",
          stereo="value")
    S.add("Cand", "Candidate", ["item_id: UUID", "keyword_rank: float", "similarity: float | None"],
          frs="FR-S-01", stereo="value")
    S.add("Res", "SearchResults", ["query_id: UUID", "mode: HYBRID | KEYWORD_ONLY", "results: list[RankedResult]"],
          frs="FR-S-01, FR-S-05", stereo="value")
    link(d, "Svc", "ISearch", "", style=REALISE, exit=(0.5, 0), entry=(0.5, 1))
    vlink(d, "Svc", "Flt", DEPEND)
    lane_link(d, "Svc", "Cand", 2276, DEPEND)
    lane_link(d, "Flt", "Res", 1686, DEPEND, side="L")
    fit(d, "p_srch", "Res")

    # ---------------- boundary: classes of Students 2 and 3
    if U:
        d.height = int(max(d.box("p_acc")[3], d.box("p_life")[3], d.box("p_srch")[3]) + 40)
        return d
    by = d.box("p_srch")[3] + 40
    pkg(d, "p_b2", "boundary: Students 2 and 3", 1670, by, 620, 200, "#FFFAF5")
    B = Column(d, 1700, by + 50, 560)
    B.add("INot", "INotify", [], ["notify(user, type, payload, dedupe_key)"], frs="FR-C-02 (Student 2; used by jobs, "
          "membership, lifecycle)", owner="S2", stereo="interface", new=False)
    B.add("IAss", "IAssess", [], ["assess(request): AssessmentResult  # runs again after T29"], frs="FR-T-01 (Student 2)",
          owner="S2", stereo="interface", new=False)
    B.add("BEmb", "EmbeddingProvider / HybridRanker", [], ["embed(texts) / rank(candidates, ctx)"],
          frs="FR-S-01 (Student 2, class_diagram_s2 page 2)", owner="S2", stereo="service", new=False)
    B.add("BLog", "SearchLogger", [], ["log_query(...), log_results(...), log_click(...)"],
          frs="FR-S-05 (Student 3, class_diagram_s3)", owner="S3", stereo="service", new=False)
    fit(d, "p_b2", "BLog")
    d.height = int(max(d.box("p_acc")[3], d.box("p_life")[3], d.box("p_b2")[3]) + 40)
    return d


# =============================================================================== Student 2, page 2
def class_diagram_s2_page2(unified: bool = False) -> Diagram:
    """unified=True: a section of the whole-system class diagram; the new signals are drawn in the engine section."""
    d = Diagram("S2 (2 of 2): iteration 2 packages", 2320, 1900)
    U = unified
    if not U:
      header(d, "<b>Digital Mohalla &#8212; Class diagram, Student 2 packages (2 of 2)</b> (iteration 2 v2.0, DA-11, drawn by "
              "Student 1 for Areeba's review): Module 5 completion, Module 4 meaning-based search and ranking, "
              "Module 7 notifications",
           "Classes new in iteration 2 have a <font color='#0A7A36'>green border</font>. A box showing only &#8220;members: "
           "page 1&#8221; is drawn in full on page 1. Blue = Student 1 and purple = Student 3 classes Student 2 depends on.")
    pkg(d, "p_as", "assurance.reviews and lender evidence  (Module 5)" if U else "assurance  (Module 5)", 30, 70,
        530 if U else 1040, 200, "#FFFCF8")
    pkg(d, "p_se", "search.ranking  (Module 4, S2)" if U else "search ranking  (Module 4, Student 2 part)", 1100, 70,
        560, 200, "#FFFCF8")
    pkg(d, "p_no", "notifications  (Module 7)", 1690, 70, 600, 200, "#FFFCF8")
    K = dict(owner="S2")

    A1 = Column(d, 60, 120, 470)
    if not U:
        A1.ref("Beta", "BetaPosteriorEstimator", owner="S2")
    A1.add("RM", "RoleMetric", ["role: BORROWER | LENDER", "metric: ON_TIME_RETURN | CONDITION_AGREED |", "  DISPUTE_FREE"],
           frs="Overview §5.2 (never mixed)", stereo="value", **K)
    A1.add("Pop", "PopulationBaseline", [], ["baseline(role, metric): float  # fallback 0.5 below 30",
                                            "refresh(now)  # scheduled job"], frs="FR-T-04 baseline b, DA-15",
           stereo="service", **K)
    A1.add("Len", "LenderEvidence", ["- estimator: BetaPosteriorEstimator", "- baseline: PopulationBaseline"],
           ["lender_factors(lender, profile): list[EvidenceRecord]", "ranking_value(lender): float  # internal only"],
           frs="FR-S-04, FR-S-01; never one number to users", stereo="service", **K)
    A1.add("Rev", "ReviewService", ["- retaliation: RetaliationCheck"],
           ["submit(actor, txn, ratings, comment): Review", "edit(actor, review, changes)  # edit window"],
           frs="FR-T-09, FR-B-15 (UC-D1)", stereo="application service", **K)
    A1.add("RevE", "Review", ["transaction_id, reviewer_id, reviewee_id: UUID", "ratings: dict, comment: str",
                              "retaliation_flag, similarity_flag: bool", "  # set by the service, confirmed by a moderator"],
           [], frs="FR-T-09 (table since schema v2.3)", stereo="entity", **K)
    if not U:
        vlink(d, "Beta", "RM", ASSOC)
        lane_link(d, "Len", "Beta", 46, DEPEND, side="L")
    vlink(d, "Pop", "Len", DEPEND, name="")
    vlink(d, "Rev", "RevE", DEPEND, name="&#171;create&#187;")
    if U:
        fit(d, "p_as", "RevE")
    else:
        signals_page2(d, K)
    search_and_notifications(d, K)
    if U:
        d.height = int(max(d.box("p_as")[3], d.box("p_se")[3], d.box("p_no")[3]) + 40)
        return d
    by = d.box("p_no")[3] + 40
    pkg(d, "p_b", "boundary: Students 1 and 3", 1690, by, 600, 200, "#F7FAFD")
    B = Column(d, 1720, by + 50, 540)
    B.add("BSvc", "SearchService", [], ["search(...)  # retrieval, calls embed() and rank()"],
          frs="FR-S-01 (Student 1, class_diagram_s1 page 2)", owner="S1", stereo="application service", new=False)
    B.add("BLog", "SearchLogger", [], ["log_query(...), log_results(...), log_click(...)"],
          frs="FR-S-05 (Student 3, class_diagram_s3)", owner="S3", stereo="service", new=False)
    fit(d, "p_b", "BLog")
    d.height = int(max(d.box("p_as")[3], d.box("p_se")[3], d.box("p_b")[3]) + 40)
    return d


def signals_page2(d, K):
    A2 = Column(d, 570, 120, 470)
    A2.ref("Det", "ManipulationDetector", owner="S2")
    A2.add("Sig", "SignalCheck", [], ["name, weight: from config", "compute(subject, data): SignalValue | None",
                                      "  # None = not available; weights renormalised"],
           frs="FR-T-05, ADR-0007", stereo="interface", new=False, **K)
    sigs = A2.row([("S2", "RatingVelocity", [], ["7 d vs 83 d"], "S2", "S2", None),
                   ("S3", "NewAccountActivity", [], ["age < 30 d, 14 d count"], "S3", "S2", None),
                   ("S5", "InvitationLinkage", [], ["invite tree, 90 d"], "S5", "S2", None)], 150)
    vlink(d, "Det", "Sig", AGGREG, name="")
    for k, s in enumerate(sigs):
        link(d, s, "Sig", "", style=REALISE, exit=(0.5, 0), entry=((75 + k * 160) / 470, 1))
    fit(d, "p_as", "RevE", *sigs)


def search_and_notifications(d, K):
    S = Column(d, 1130, 120, 500)
    S.add("Emb", "EmbeddingProvider", ["model: str  # chosen by the memory test, ADR-0016"],
          ["embed(texts): list[Vector]  # may raise ModelUnavailable"], frs="FR-S-01, FR-S-02 fallback", stereo="port", **K)
    S.add("EJob", "EmbeddingJob", [], ["due(now): items whose text hash changed", "run(item)  # item_embedding row"],
          frs="FR-B-03 (retry later), ADR-0012", stereo="service", **K)
    S.add("Rank", "HybridRanker", ["- weights: RankingWeights", "- lenders: LenderEvidence"],
          ["rank(candidates, ctx): list[RankedResult]", "reason(result): str  # one line, no score"],
          frs="FR-S-01, Algorithm 5 (sequence i)", stereo="service", **K)
    S.add("W", "RankingWeights", ["relevance 0.40, lender_evidence 0.30,", "availability 0.15, same_community 0.10,",
                                  "freshness 0.05; config_version"], frs="NFR-D-01 (config 1.4.0)", stereo="value", **K)
    S.add("RR", "RankedResult", ["item_id: UUID", "score_parts: dict  # stored, not shown", "reason: str"],
          frs="FR-S-01, FR-S-05", stereo="value", **K)
    link(d, "EJob", "Emb", "", style=DEPEND, exit=(0.5, 0), entry=(0.5, 1))
    vlink(d, "Rank", "W", ASSOC)
    lane_link(d, "Rank", "RR", 1116, DEPEND, side="L")
    fit(d, "p_se", "RR")

    N = Column(d, 1720, 120, 540)
    N.add("INot", "INotify", [], ["notify(user, type, payload, dedupe_key): None"], frs="FR-C-02", stereo="interface", **K)
    N.add("NSvc", "NotificationService", [], ["notify(user, type, payload, dedupe_key): None  # once per key",
                                             "inbox(user, unread_only): list[Notification]", "mark_read(user, ids)"],
          frs="FR-C-02 (in-app), FR-B-06, FR-B-17, ADR-0013 (UC-G3)", stereo="application service", **K)
    N.add("Note", "Notification", ["user_id: UUID", "type: str", "payload: dict  # no location", "dedupe_key: str",
                                  "created_at, read_at: datetime"], frs="FR-C-02", stereo="entity", **K)
    link(d, "NSvc", "INot", "", style=REALISE, exit=(0.5, 0), entry=(0.5, 1))
    vlink(d, "NSvc", "Note", COMPOSE, name="")
    fit(d, "p_no", "Note")


if __name__ == "__main__":
    # the sections are drawn into the one whole-system class diagram
    import generate_class_diagram
    generate_class_diagram.build().save(os.path.join(HERE, "class_diagram.drawio"))
