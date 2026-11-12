"""Generates the iteration 2 sequence diagrams of Student 1 (DA-12).

    python generate_sequences_d_e_f.py
        -> sequence_d_join_community.drawio      UC-A3 + UC-A4: join a community with the locality check
        -> sequence_e_overdue_escalation.drawio  UC-B13: scheduler, overdue loan -> automatic dispute (T24)
        -> sequence_f_review_to_signals.drawio   UC-D1: review -> flags -> manipulation signals in the next assessment

Same notation as iteration 1 sequence (b) (../08_sequence_diagrams/generate_sequence_b.py): lifelines are
components of component_diagram_v2.drawio, messages use the REST table of Architecture_Design_v2.md section 4, and
event types and transition IDs are those of lifecycle v3. Sequences (g) and (h) are Minahil's.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_tools"))
from drawio import Diagram, EDGE_BASE  # noqa: E402

TOP, HEAD = 80, 56
SYNC = EDGE_BASE + "endArrow=block;endFill=1;strokeColor=#1D1D1D;fontSize=10.5;"
ASYNC = EDGE_BASE + "endArrow=open;endFill=0;strokeColor=#1D1D1D;fontSize=10.5;"
RET = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#46535F;fontColor=#33404D;fontSize=10.5;"
FAIL = EDGE_BASE + "endArrow=open;endFill=0;dashed=1;strokeColor=#B00020;fontColor=#B00020;fontSize=10.5;"


class Seq:
    def __init__(self, d, xs):
        self.d, self.X, self.y, self.n = d, xs, TOP + HEAD + 30, 0

    def msg(self, a, b, text, style=SYNC, step=30, number=True, dx=0):
        self.n += number
        label = (f"<b>{self.n}</b> " if number else "") + text
        x1, x2 = self.X[a], self.X[b]
        off = 5 if x2 > x1 else -5
        self.d.edge(None, None, label, style=style, src_pt=(x1 + off, self.y), tgt_pt=(x2 - off, self.y),
                    label_dy=-9, label_dx=dx, check=True)
        self.y += step

    def self_msg(self, a, text, step=40):
        self.n += 1
        x = self.X[a] + 5
        self.d.edge(None, None, f"<b>{self.n}</b> {text}", style=SYNC, src_pt=(x, self.y),
                    tgt_pt=(x, self.y + 18), points=[(x + 30, self.y), (x + 30, self.y + 18)], check=True)
        e = self.d.cells[-1]
        e["label_x"] = 0
        e["label_dx"] = 12 + len(text) * 2.6
        self.y += step

    def frame(self, op, y0, y1, x0, x1, guards=()):
        d = self.d
        d.node(op, x0, y0, x1 - x0, y1 - y0, "shape=umlFrame;whiteSpace=wrap;html=1;width=52;height=22;"
               "boundedLbl=1;verticalAlign=middle;align=left;spacingLeft=4;fontStyle=1;fontSize=11;fillColor=none;"
               "strokeColor=#5F6B76;", check=False)
        for k, (gy, text) in enumerate(guards):
            if k:
                d.edge(None, None, "", style="endArrow=none;dashed=1;html=1;strokeColor=#5F6B76;",
                       src_pt=(x0, gy - 6), tgt_pt=(x1, gy - 6), check=False)
            d.text(f"<b>{text}</b>", x0 + 58 if k == 0 else x0 + 8, gy - 16 if k == 0 else gy - 4, 900, 18, size=10.5,
                   color="#33404D", check=False)

    def note(self, text, x, w, h=34, colour="#FFF8E1"):
        self.d.node(text, x, self.y - 6, w, h, "shape=note;size=10;whiteSpace=wrap;html=1;fontSize=10;align=left;"
                    f"spacingLeft=6;fillColor={colour};strokeColor=#B26A00;", check=False)
        self.y += h + 6

    def heading(self, text):
        self.d.text(text, 30, self.y - 14, 900, 18, size=12, color="#1F4E79", check=False)
        self.y += 34


def lifelines(d, life, bottom):
    for k, label, x, colour in life:
        if colour is None:
            d.node(label, x - 40, TOP, 80, HEAD, "shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;"
                   f"whiteSpace=wrap;html=1;container=0;verticalAlign=top;spacingTop=36;size={HEAD - 14};fontSize=11;"
                   "fontStyle=1;", check=False, id=f"ll_{k}")
            d.by_id[f"ll_{k}"]["h"] = bottom - TOP
        else:
            d.node(label, x - 80, TOP, 160, bottom - TOP, "shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;"
                   f"html=1;container=0;collapsible=0;size={HEAD};fontSize=11;fillColor={colour};strokeColor=#46535F;",
                   check=False, id=f"ll_{k}")


def finish(d, s, life):
    end = s.y + 30
    for k, *_ in life:
        d.by_id[f"ll_{k}"]["h"] = end - TOP
    d.height = end + 30
    return d


def header(d, title, sub):
    d.text(title, 30, 12, 1600, 24, size=15, check=False)
    d.text(sub, 30, 36, 1640, 20, size=11, color="#4A5560", check=False)


# =============================================================================== (d) join a community
def sequence_d() -> Diagram:
    life = [("M", "Member", 70, None), ("MOD", "Moderator", 190, None), ("API", ":REST API", 340, "#F2F2F2"),
            ("MEM", ":MembershipService<br>(M1)", 540, "#E3EEF9"), ("INV", ":InvitationService<br>(M1)", 740, "#E3EEF9"),
            ("VER", ":GeofenceInvitation-<br>Verifier (M1)", 940, "#E3EEF9"),
            ("DB", ":Database<br>(PostgreSQL, triggers)", 1140, "#E3EEF9"), ("NOT", ":NotificationService<br>(M7)", 1340, "#FDEBDD")]
    X = {k: x for k, _, x, _ in life}
    d = Diagram("Sequence (d) A3 + A4 (DA-12)", 1720, 2000)
    header(d, "<b>Digital Mohalla &#8212; Sequence diagram (d): join a community with the locality check (UC-A3) and "
              "the moderator's decision (UC-A4)</b> &#8212; iteration 2, DA-12, Student 1, v1.0",
           "Locality method A11: one coarse fix evaluated in memory plus a single-use invitation; inconclusive or conflicting "
           "goes to a moderator, never an automatic rejection (FR-A-08). The request body with the fix is never logged.")
    lifelines(d, life, 1960)
    s = Seq(d, X)
    s.heading("<b>UC-A3 Select neighbourhood and request membership</b> (FR-A-06 to FR-A-09)")
    s.msg("M", "API", "GET /communities?query=", dx=20)
    s.msg("API", "MEM", "communities(query)")
    s.msg("MEM", "DB", "SELECT community (name, rules, join_policy)")
    s.msg("API", "M", "200 [communities with rules and methods]", style=RET)
    s.msg("M", "API", "POST /communities/{id}/join {fix | permission_refused, mock_flag, invitation_code}", dx=230)
    s.msg("API", "MEM", "request_join(member, community, LocalityInput, code)  [body not logged]", dx=60)
    alt1 = s.y - 8
    g_code = s.y + 22
    s.y += 50
    s.msg("MEM", "INV", "redeem(code, community)")
    s.msg("INV", "DB", "SELECT invitation by SHA-256(code): unexpired, same community, inviter approved")
    s.msg("INV", "MEM", "Invitation", style=RET)
    g_bad = s.y + 4
    s.y += 34
    s.msg("INV", "MEM", "InvalidInvitation (expired, used, other community, self)", style=FAIL)
    s.msg("API", "M", "422 code not valid: retry or continue without (UC-A3 3d)", style=FAIL)
    s.frame("alt", alt1, s.y, 20, 1680, [(g_code, "[invitation code given]"), (g_bad, "[code invalid]")])
    s.y += 30
    s.msg("MEM", "VER", "evaluate(fix, accuracy, mock_flag, permission_refused, invitation, duplicate_suspected)", dx=40)
    s.self_msg("VER", "point-in-polygon on community.boundary_polygon, margin and accuracy -> geofence signal; fix dropped")
    s.msg("VER", "MEM", "LocalityResult {outcome: VERIFIED | INCONCLUSIVE | CONFLICTING, signal}  [no coordinates]", style=RET,
          dx=40)
    s.msg("MEM", "DB", "INSERT membership (PENDING); INSERT locality_verification (coarse only)", dx=60)
    s.self_msg("DB", "locality_rule_ck: outcome follows its signals; locality_guard: invitation single-use, same community")
    alt2 = s.y - 8
    g_open = s.y + 22
    s.y += 50
    s.msg("MEM", "DB", "UPDATE membership APPROVED (open-join community, UC-A3 4a)")
    s.msg("MEM", "NOT", "notify(moderators, member_joined)", style=ASYNC)
    g_mod = s.y + 4
    s.y += 34
    s.msg("MEM", "NOT", "notify(moderators, membership_request, dedupe_key = membership id)", style=ASYNC)
    s.frame("alt", alt2, s.y, 20, 1680, [(g_open, "[outcome = VERIFIED and join_policy = OPEN]"),
                                         (g_mod, "[otherwise: moderator decides; INCONCLUSIVE and CONFLICTING are never rejected "
                                                 "automatically]")])
    s.y += 26
    s.msg("API", "M", "201 {membership: PENDING | APPROVED, locality: outcome in neutral words}", style=RET, dx=40)
    s.y += 20
    s.heading("<b>UC-A4 Approve or reject the membership request</b> (FR-A-10, FR-A-11)")
    s.msg("MOD", "API", "GET /moderation/memberships", dx=10)
    s.msg("API", "MEM", "queue(moderator)")
    s.msg("MEM", "DB", "SELECT pending requests of the moderator's communities + coarse evidence + flags", dx=40)
    s.msg("API", "MOD", "200 [requests with locality outcome, duplicate / mock flags]", style=RET)
    s.msg("MOD", "API", "POST /moderation/memberships/{id}/decision {kind: APPROVED | REJECTED | INFO_REQUESTED, reason}",
          dx=230)
    s.msg("API", "MEM", "decide(moderator, membership, kind, reason)")
    alt3 = s.y - 8
    g_ok = s.y + 22
    s.y += 50
    s.msg("MEM", "DB", "INSERT membership_decision; UPDATE membership status (one DB transaction)", dx=40)
    s.self_msg("DB", "membership_decision_guard: moderator of this community or admin; not the applicant; still undecided")
    s.msg("MEM", "DB", "approving an INCONCLUSIVE check: INSERT locality_verification (MODERATOR_APPROVAL, approved_by)", dx=60)
    s.msg("MEM", "NOT", "notify(applicant, membership_decided, reason)", style=ASYNC)
    s.msg("API", "MOD", "200 {status}", style=RET)
    g_race = s.y + 4
    s.y += 34
    s.msg("DB", "MEM", "40001 already decided by another moderator: nothing applied (UC-A4 4a)", style=FAIL, dx=40)
    s.msg("API", "MOD", "409 show the current status", style=FAIL)
    s.frame("alt", alt3, s.y, 20, 1680, [(g_ok, "[authorised and the request is still undecided]"),
                                         (g_race, "[another moderator decided first]")])
    s.y += 26
    s.note("Reversal (FR-A-11) is the same call with kind REVERSED and reverses_decision_id: a new row, the old decision "
           "stays. Privacy: the fix exists only in the request and in the verifier's memory; storage holds the coarse signal "
           "and outcome (NFR-PR-01, NFR-PR-02); suite 14 checks logs and responses.", 40, 1640, 46, colour="#F4F6F8")
    return finish(d, s, life)


# =============================================================================== (e) overdue escalation
def sequence_e() -> Diagram:
    life = [("GHA", "GitHub<br>schedule", 80, None), ("API", ":REST API", 240, "#F2F2F2"),
            ("RUN", ":JobRunner<br>(M3)", 430, "#E3EEF9"), ("JOB", ":OverdueJob<br>(M3)", 620, "#E3EEF9"),
            ("BOR", ":BorrowingService<br>(M3)", 810, "#E3EEF9"), ("DB", ":Database<br>(PostgreSQL, triggers)", 1010, "#E3EEF9"),
            ("NOT", ":NotificationService<br>(M7)", 1210, "#FDEBDD")]
    X = {k: x for k, _, x, _ in life}
    d = Diagram("Sequence (e) B13 overdue (DA-12)", 1660, 1700)
    header(d, "<b>Digital Mohalla &#8212; Sequence diagram (e): scheduled jobs, an overdue loan becomes a dispute (UC-B13, "
              "T24)</b> &#8212; iteration 2, DA-12, Student 1, v1.0",
           "ADR-0012: an external schedule calls the API every 15 minutes; every job claims its work in job_run, so a second "
           "run changes nothing (NFR-R-05). Timers come from config scheduler_b13. The same pattern runs every job.")
    lifelines(d, life, 1660)
    s = Seq(d, X)
    s.heading("<b>Every 15 minutes</b> (FR-B-18)")
    s.msg("GHA", "API", "POST /internal/jobs/run  [Authorization: job token]")
    s.msg("API", "RUN", "run_due_jobs(now)")
    s.msg("RUN", "DB", "pg_try_advisory_lock('dm.jobs')")
    alt0 = s.y - 8
    g_lock = s.y + 22
    s.y += 50
    s.msg("DB", "RUN", "true", style=RET)
    s.msg("RUN", "JOB", "due(now)")
    s.msg("JOB", "DB", "SELECT ACTIVE loans: due_at + overdue_limit < now AND reminders_sent >= 2", dx=40)
    s.msg("JOB", "RUN", "[due items]", style=RET)
    loop = s.y - 8
    g_item = s.y + 22
    s.y += 50
    s.msg("RUN", "DB", "INSERT job_run (overdue_escalation, '<txn>:overdue') ON CONFLICT DO NOTHING", dx=40)
    alt1 = s.y - 8
    g_new = s.y + 22
    s.y += 50
    s.msg("RUN", "JOB", "run(item, service)")
    s.msg("JOB", "BOR", "escalate_overdue(txn)")
    s.msg("BOR", "DB", "append dispute_opened {reason: NON_RETURN}  system:scheduler  (ACTIVE -> DISPUTED, T24)", dx=40)
    s.self_msg("DB", "event_validate: system opens only NON_RETURN; event_apply: case opened (D6), deposit record frozen")
    s.msg("BOR", "NOT", "notify(borrower and lender, dispute_opened, dedupe '<txn>:overdue')", style=ASYNC, dx=20)
    s.msg("RUN", "DB", "UPDATE job_run SUCCEEDED")
    g_dup = s.y + 4
    s.y += 34
    s.msg("DB", "RUN", "0 rows: already claimed by an earlier run, skip", style=RET)
    g_err = s.y + 4
    s.y += 34
    s.msg("BOR", "JOB", "error (e.g. state changed: the borrower just started the return)", style=FAIL, dx=40)
    s.msg("RUN", "DB", "UPDATE job_run FAILED, attempts + 1; retried next run up to max_attempts", style=FAIL, dx=40)
    s.frame("alt", alt1, s.y, 330, 1600, [(g_new, "[claimed now]"), (g_dup, "[claimed before]"), (g_err, "[command refused]")])
    s.y += 24
    s.frame("loop", loop, s.y, 300, 1615, [(g_item, "[for each due loan]")])
    s.y += 24
    s.msg("RUN", "DB", "pg_advisory_unlock('dm.jobs')")
    g_busy = s.y + 4
    s.y += 34
    s.msg("DB", "RUN", "false: another run is active", style=RET)
    s.frame("alt", alt0, s.y, 20, 1630, [(g_lock, "[lock acquired]"), (g_busy, "[lock busy]")])
    s.y += 26
    s.msg("RUN", "API", "JobReport {ran, skipped, failed per job}", style=RET)
    s.msg("API", "GHA", "200 JobReport", style=RET)
    s.y += 10
    s.note("<b>ref</b> before T24: return reminders I02 at due - 24 h and at the due date use the same claim pattern with "
           "due keys '<txn>:return_reminder:1' and ':2'. Other jobs: request expiry T15, no-show T19, confirmation reminder "
           "I06, listing expiry, embedding backfill, population baseline. A late schedule only delays a job; events keep the "
           "database's own timestamps.", 40, 1580, 60, colour="#F4F6F8")
    return finish(d, s, life)


# =============================================================================== (f) review to signals
def sequence_f() -> Diagram:
    life = [("P", "Party<br>(reviewer)", 70, None), ("API", ":REST API", 230, "#F2F2F2"),
            ("REV", ":ReviewService<br>(M5)", 420, "#FDEBDD"), ("DB", ":Database<br>(PostgreSQL)", 610, "#E3EEF9"),
            ("BOR", ":BorrowingService<br>(M3)", 800, "#E3EEF9"), ("FAC", ":AssuranceFacade<br>(M5)", 990, "#FDEBDD"),
            ("DET", ":ManipulationDetector<br>(M5)", 1180, "#FDEBDD"), ("POL", ":DecisionPolicy<br>(M5)", 1370, "#FDEBDD")]
    X = {k: x for k, _, x, _ in life}
    d = Diagram("Sequence (f) D1 review to signals (DA-12)", 1760, 1500)
    header(d, "<b>Digital Mohalla &#8212; Sequence diagram (f): a review is checked and later feeds the manipulation "
              "signals (UC-D1, D3)</b> &#8212; iteration 2, DA-12, Student 1 for Student 2, v1.0",
           "Reviews never enter the trust estimate, which uses verified loan outcomes (D19); they feed only S1 to S5 and the "
           "retaliation check. A signal is not proof of wrongdoing: only level 4 with two corroborating signals holds a request.")
    lifelines(d, life, 1460)
    s = Seq(d, X)
    s.heading("<b>UC-D1 Submit review</b> (FR-T-09, FR-B-15)")
    s.msg("P", "API", "POST /transactions/{id}/review {ratings, comment}")
    s.msg("API", "REV", "submit(actor, txn, ratings, comment)")
    s.msg("REV", "DB", "SELECT loan COMPLETED, parties, earlier review by this party, complaints in 14 d", dx=60)
    s.self_msg("REV", "retaliation check: low rating within 14 d of the reviewee's complaint about a confirmed return")
    s.self_msg("REV", "similarity check: 3-gram TF-IDF cosine against reviews the reviewee received")
    s.msg("REV", "DB", "INSERT review {retaliation_flag, similarity_flag}  [review_guard; review_once_uq]", dx=40)
    s.msg("API", "P", "201 (flags are not shown to the reviewer)", style=RET)
    s.y += 20
    s.heading("<b>Later: the reviewee's next request is assessed</b> (FR-T-05, FR-T-06; sequence (a) of iteration 1)")
    s.msg("BOR", "FAC", "assess(request)  [timeout 2,000 ms]")
    s.msg("FAC", "DET", "assess(subject, data, window 90 d)")
    s.msg("DET", "DB", "reviews given and received, account age, invitations of the same inviter", dx=-30)
    s.self_msg("DET", "S1 partners, S2 velocity, S3 new account, S4 text, S5 invitation linkage; flagged retaliation set aside")
    s.self_msg("DET", "weighted mean over available signals -> score, band, corroboration (two signals >= 0.5)")
    s.msg("DET", "FAC", "ManipulationRisk {score, level, signals with evidence}", style=RET)
    s.msg("FAC", "POL", "decide(direct, indirect, risk, ctx)  [rule order R1, R2, R4, R3, ...]", dx=20)
    alt = s.y - 8
    g4 = s.y + 22
    s.y += 50
    s.msg("POL", "FAC", "R2: REVIEW_RECOMMENDED + hold manipulation_risk", style=RET)
    s.msg("FAC", "BOR", "AssessmentResult (hold)", style=RET)
    s.msg("BOR", "DB", "insert assessment; append held_for_review (T06); case opened for a moderator", dx=-40)
    g3 = s.y + 4
    s.y += 34
    s.msg("POL", "FAC", "R5 or later rule; level 3 adds a verification safeguard, nobody is held", style=RET)
    s.msg("FAC", "BOR", "AssessmentResult", style=RET)
    s.msg("BOR", "DB", "insert assessment; append assessment_generated (T05)", dx=-40)
    s.frame("alt", alt, s.y, 540, 1700, [(g4, "[level 4: score >= 60 and corroborated]"), (g3, "[otherwise]")])
    s.y += 26
    s.note("Wording rule (FR-T-05): the explanation describes anomalies with their evidence and never accuses anyone; a "
           "family group with one strong signal stays at level 3 (C3 guard, suite 24). S5 uses only invitation links, "
           "because device and network data are not collected.", 40, 1660, 46, colour="#F4F6F8")
    return finish(d, s, life)


if __name__ == "__main__":
    sequence_d().save(os.path.join(HERE, "sequence_d_join_community.drawio"))
    sequence_e().save(os.path.join(HERE, "sequence_e_overdue_escalation.drawio"))
    sequence_f().save(os.path.join(HERE, "sequence_f_review_to_signals.drawio"))
