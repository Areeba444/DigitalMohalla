"""Generates sequence diagram (h): appeal, second moderator, reversal and flagged evidence (DA-12, Student 3).

    python generate_sequence_h.py   ->  sequence_h_appeal_reversal.drawio

UC-I4 extensions 4b (appeal to a second moderator) and 4c (reversal keeps both decisions and flags the affected
evidence, ES-11); FR-T-11; escalation-case transitions C08 to C11. Endpoints are proposals for the DA-10 REST table.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seqlib import ASYNC, F_S1, F_S2, F_S3, F_SH, FAIL, RET, Diagram, Seq  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

LIFE = [  # key, label, x-centre, fill (None = actor)
    ("P", "Party<br>(appellant)", 70, None),
    ("M2", "Second<br>moderator", 180, None),
    ("ADM", "Moderator<br>or admin", 290, None),
    ("API", ":REST API", 440, F_SH),
    ("CS", ":CaseService<br>(M9, new module)", 640, F_S3),
    ("RUL", ":DecisionRules<br>(moderation/decisions.py)", 850, F_S3),
    ("DB", ":Case store (PostgreSQL)<br>escalation_case, moderator_decision", 1070, F_S3),
    ("OUT", ":Evidence<br>outcome, trust_edge", 1290, F_S2),
    ("AUD", ":AuditLog", 1470, F_S1),
    ("NOT", ":Notifier (M7)", 1640, F_SH),
]
BOTTOM = 1420


def build() -> Diagram:
    d = Diagram("Sequence (h) appeal and reversal (DA-12)", 1760, BOTTOM + 60)
    d.text("<b>Digital Mohalla &#8212; Sequence diagram (h): appeal, second moderator, reversal and flagged evidence"
           "</b> &#8212; DA-12, Student 3, v1.0 draft (iteration 2)", 30, 12, 1650, 24, size=15, check=False)
    d.text("Precondition: the case is DECIDED (C06) and its decision is stored in moderator_decision. A reversal never "
           "rewinds a closed loan: COMPLETED, DECLINED and NO_SHOW are final lifecycle states. It changes the evidence "
           "instead, so the next assessment of either party sees the corrected record (ES-11). Endpoints are proposals "
           "for the DA-10 REST table; the appeal window is a config value (DA-03).", 30, 36, 1650, 34, size=11,
           color="#4A5560", check=False)
    s = Seq(d, LIFE, BOTTOM)

    # ------------------------------------------------------------ 1. appeal
    s.heading("<b>1. A party appeals</b> (UC-I4 4b; C08)")
    s.msg("P", "API", "POST /cases/{id}/appeal {reason} (proposed)", dx=60)
    s.msg("API", "CS", "appeal(case, party, reason)")
    s.msg("CS", "DB", "SELECT case FOR UPDATE: status DECIDED; party to this loan; within the appeal window", dx=30)
    s.msg("CS", "DB", "UPDATE status = APPEALED; assigned_to := a moderator other than the first decider "
          "(admin if none)", dx=60)
    s.msg("CS", "AUD", "record(appeal_filed, case, party)")
    s.msg("CS", "NOT", "notify(second moderator and the other party, appeal_filed, {case})", style=ASYNC)
    s.msg("API", "P", "202 appeal received", style=RET)
    s.y += 20

    # ------------------------------------------------------------ 2. second moderator
    s.heading("<b>2. The second moderator decides the appeal</b> (UC-I4 4b; C09, C10)")
    s.msg("M2", "API", "POST /moderation/cases/{id}/appeal-decision {upheld | overturned, reason} (proposed)", dx=170)
    s.msg("API", "CS", "decideAppeal(case, moderator, result, reason)")
    s.msg("CS", "RUL", "plan(APPEALED, result) &#8212; reason present; decider &#8800; first decider; same community",
          dx=40)
    s.msg("RUL", "CS", "Plan(kind, reverses?)", style=RET)
    alt = s.y - 8
    s.y += 30
    s.msg("CS", "DB", "INSERT moderator_decision(kind = APPEAL_UPHELD); UPDATE status = DECIDED")
    s.msg("CS", "NOT", "notify(both parties, appeal_upheld, {case, reason})", style=ASYNC)
    g_over = s.y + 18
    s.y += 44
    s.msg("CS", "DB", "INSERT moderator_decision(kind = APPEAL_OVERTURNED, reverses_decision_id = first)", dx=30)
    s.msg("CS", "DB", "UPDATE status = REVERSED; closed_at := now")
    s.msg("CS", "OUT", "flagOutcomes(decision): outcomes from the overturned decision &#8594; FLAGGED_FOR_REEVALUATION, "
          "flagged_by_decision_id", dx=120)
    s.self_msg("OUT", "refresh both parties' trust edges (ADR-0006): flagged outcomes stop counting", dx=-260)
    s.msg("CS", "NOT", "notify(both parties, appeal_overturned, {case, reason})", style=ASYNC)
    g_bad = s.y + 18
    s.y += 44
    s.msg("API", "M2", "403 same moderator as the first decision, other community, or no reason | 409 already "
          "decided", style=FAIL, dx=250)
    s.frame("alt", alt, s.y + 4, 40, 1730, guards=[(alt + 22, "[upheld] C09"), (g_over, "[overturned] C10"),
                                                 (g_bad, "[guard fails]")])
    s.msg("CS", "AUD", "record(appeal_decided | rejected command, case, moderator, authorisation)", dx=0)
    s.y += 30

    # ------------------------------------------------------------ 3. later reversal
    s.heading("<b>3. A decision is reversed later</b> (UC-I4 4c; C11; ES-11)")
    s.msg("ADM", "API", "POST /moderation/cases/{id}/reversal {reason} (proposed)", dx=60)
    s.msg("API", "CS", "reverse(case, actor, reason)")
    s.msg("CS", "RUL", "plan(DECIDED, REVERSAL) &#8212; authorised for this community; reason present")
    s.msg("RUL", "CS", "Plan(REVERSAL, reverses = latest decision)", style=RET)
    s.msg("CS", "DB", "INSERT moderator_decision(kind = REVERSAL, reverses_decision_id); UPDATE status = REVERSED",
          dx=40)
    s.msg("CS", "OUT", "flagOutcomes(decision) and refresh trust edges, as in step 2", dx=0)
    s.msg("CS", "AUD", "record(decision_reversed, case, actor, authorisation)")
    s.msg("CS", "NOT", "notify(both parties, decision_reversed, {case, reason})", style=ASYNC)
    s.msg("API", "ADM", "200 {status: REVERSED, flagged_outcomes: n}", style=RET)
    s.y += 16
    s.note("Both decisions stay in moderator_decision (append-only; decision_reversal_ck requires reverses_decision_id "
           "for REVERSAL and APPEAL_OVERTURNED). The estimator and the trust edges already skip "
           "FLAGGED_FOR_REEVALUATION outcomes, so the next assessment of either party changes without any engine "
           "change. Restoring a flagged outcome after re-evaluation is a later moderator action (FYP-2).", 470, 1000,
           h=62)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "sequence_h_appeal_reversal.drawio"))
