"""Generates sequence diagram (g): information request, party response and deadline (DA-12, Student 3).

    python generate_sequence_g.py   ->  sequence_g_information_request.drawio

UC-I4 step 2 and extension 2a; UC-B12 / FR-B-17 (the other party responds with evidence); escalation-case
transitions C02, C03 and C04. Endpoints are proposals for the DA-10 REST table (Fatima), marked "proposed".
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seqlib import ASYNC, F_S1, F_S2, F_S3, F_SH, FAIL, RET, Diagram, Seq  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

LIFE = [  # key, label, x-centre, fill (None = actor)
    ("MOD", "Moderator", 80, None),
    ("P", "Party<br>(borrower or lender)", 210, None),
    ("API", ":REST API", 380, F_SH),
    ("CS", ":CaseService<br>(M9)", 590, F_S3),
    ("DB", ":Database (PostgreSQL)<br>escalation_case, case_statement", 820, F_SH),
    ("AUD", ":AuditLogService (M9)<br>audit_log, hash chain", 1040, F_S3),
    ("NOT", ":NotificationService (M7)<br>&#171;INotify&#187;", 1250, F_S2),
    ("SCH", ":JobRunner (M3)<br>scheduler, ADR-0012", 1450, F_S1),
]
BOTTOM = 1290


def build() -> Diagram:
    d = Diagram("Sequence (g) information request (DA-12)", 1560, BOTTOM + 60)
    d.text("<b>Digital Mohalla &#8212; Sequence diagram (g): information request, party response and deadline</b> "
           "&#8212; DA-12, Student 3, v1.1 draft (iteration 2)", 30, 12, 1500, 24, size=15, check=False)
    d.text("Precondition: an escalation case is OPEN (sequence c, transition C01) and assigned to a moderator of the "
           "transaction's community. Case transitions C02&#8211;C04: escalation-case state machine. Endpoints are "
           "in the DA-10 REST table. NotificationService (Module 7, ADR-0013) and JobRunner (the scheduler, ADR-0012) "
           "are iteration 2 components owned by Areeba and Fatima.", 30, 36, 1500, 34, size=11, color="#4A5560", check=False)
    s = Seq(d, LIFE, BOTTOM)

    # ------------------------------------------------------------ 1. moderator asks
    s.heading("<b>1. The moderator asks for more information</b> (UC-I4 step 2; C02)")
    s.msg("MOD", "API", "POST /moderation/cases/{id}/information-requests {to: borrower | lender | both, question} "
          "(proposed)", dx=330)
    s.msg("API", "CS", "requestInformation(case, moderator, to, question)")
    s.msg("CS", "DB", "SELECT case FOR UPDATE; moderator of this community, not a party, status OPEN", dx=40)
    alt = s.y - 8
    s.y += 30
    s.msg("CS", "DB", "UPDATE escalation_case SET status = AWAITING_INFORMATION, info_deadline = now() + window")
    s.msg("CS", "DB", "store the question (needs a moderator-authored record: open point, schema v2.4)", dx=40)
    s.msg("CS", "AUD", "record(info_requested, case, moderator, authorisation)")
    s.msg("CS", "NOT", "notify(party, information_requested, {case, question, deadline})", style=ASYNC)
    s.msg("API", "MOD", "200 {status: AWAITING_INFORMATION, deadline}", style=RET)
    g2 = s.y + 18
    s.y += 44
    s.msg("CS", "AUD", "record(rejected command, reason)")
    s.msg("API", "MOD", "403 not authorised | 409 case already decided (UC-I4 4a)", style=FAIL)
    s.frame("alt", alt, s.y + 4, 40, 1330, guards=[(alt + 22, "[authorised and case OPEN]"),
                                                 (g2, "[not authorised, a party to the loan, or case no longer OPEN]")])
    s.y += 50

    # ------------------------------------------------------------ 2. response or deadline
    s.heading("<b>2. The party answers, or the deadline passes</b> (UC-I4 2a; FR-B-17; C03, C04)")
    alt2 = s.y - 8
    s.y += 30
    s.msg("P", "API", "POST /cases/{id}/statements {statement, attachment_ids?} (proposed; photos via uploads, M4)",
          dx=250)
    s.msg("API", "CS", "addStatement(case, party, statement)")
    s.msg("CS", "DB", "party to this loan; status AWAITING_INFORMATION; now &lt; info_deadline", dx=10)
    s.msg("CS", "DB", "INSERT case_statement (append-only); UPDATE status = OPEN")
    s.msg("CS", "AUD", "record(info_received, case, party)")
    s.msg("CS", "NOT", "notify(moderator, information_received, {case})", style=ASYNC)
    s.msg("API", "P", "201 statement recorded", style=RET)
    g_dead = s.y + 18
    s.y += 44
    s.msg("SCH", "CS", "run_due_jobs(now) &#8594; expire_information(now)", dx=-40)
    s.msg("CS", "DB", "SELECT cases WHERE status = AWAITING_INFORMATION AND info_deadline &lt; now "
          "FOR UPDATE SKIP LOCKED", dx=80)
    s.msg("CS", "DB", "UPDATE status = OPEN (deadline kept as evidence of non-response)")
    s.msg("CS", "AUD", "record(info_deadline_passed, case, SYSTEM)")
    s.msg("CS", "NOT", "notify(moderator, deadline_passed, {case}) &#8212; dedupe key = case + deadline", style=ASYNC)
    s.msg("CS", "SCH", "n cases closed (a re-run finds none: idempotent, NFR-R-05)", style=RET)
    s.frame("alt", alt2, s.y + 4, 40, 1520, guards=[(alt2 + 22, "[the party answers before the deadline] C03"),
                                                  (g_dead, "[the deadline passes without an answer] C04")])
    s.y += 50

    # ------------------------------------------------------------ 3. decision
    s.heading("<b>3. The moderator decides on the evidence available</b> (UC-I4 2a, step 3; C06)")
    s.note("The case is OPEN again in both branches. The moderator decides as in sequence (c) and, for disputes, with "
           "the item's possession recorded (ADR-0009, sequence h). A non-response is shown to the moderator as a fact, "
           "never as an automatic loss for the party.", 360, 900, h=48)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "sequence_g_information_request.drawio"))
