"""Generates sequence diagram (i): search, ranking, fallbacks and logging (DA-24, Student 3).

    python generate_sequence_i.py   ->  sequence_i_search.drawio

UC-B3 and UC-B4 (Use Cases v1.4); FR-S-01 to S-05; NFR-R-04. Retrieval follows ADR-0016 (proposed, Student 1):
Postgres full-text search for keywords, pgvector exact search for meaning, eligibility filters inside the same
query. Ranking weights are DA-22 (Students 1 and 2) and are not set here. Endpoints are proposals for the DA-10
REST table (Student 1), marked "proposed".
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seqlib import ASYNC, F_S1, F_S2, F_S3, F_SH, RET, Diagram, Seq  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

LIFE = [  # key, label, x-centre, fill (None = actor)
    ("B", "Borrower", 70, None),
    ("APP", ":App<br>(W23 search screen)", 210, F_SH),
    ("API", ":REST API", 370, F_SH),
    ("SS", ":SearchService (M4)<br>retrieval: Student 1", 570, F_S1),
    ("EMB", ":EmbeddingProvider (M4)<br>sentence model in the API", 780, F_S2),
    ("DB", ":Database (PostgreSQL)<br>item, search_tsv,<br>item_embedding (pgvector)", 990, F_SH),
    ("RK", ":HybridRanker (M4)<br>Student 2; weights DA-22", 1190, F_S2),
    ("EV", ":LenderEvidence (M5)", 1380, F_S2),
    ("LOG", ":SearchLogger (M4)<br>Student 3; search logs", 1570, F_S3),
]
BOTTOM = 1500


def build() -> Diagram:
    d = Diagram("Sequence (i) search (DA-24)", 1780, BOTTOM + 60)
    d.text("<b>Digital Mohalla &#8212; Sequence diagram (i): search, ranking, fallbacks and logging</b> "
           "&#8212; DA-24, Student 3, v1.1 draft (iteration 2)", 30, 12, 1600, 24, size=15, check=False)
    d.text("Precondition: the borrower is logged in with an APPROVED membership (UC-B3). Retrieval: ADR-0016 "
           "(proposed). Ranking weights: DA-22 (not set here). Endpoints are proposals for the DA-10 REST table. No "
           "location or coordinates are sent, stored or logged at any step (NFR-PR-01).", 30, 36, 1600, 34, size=11,
           color="#4A5560", check=False)
    s = Seq(d, LIFE, BOTTOM)

    # ------------------------------------------------------------ 1. query and retrieval
    s.heading("<b>1. Query and retrieval with eligibility inside the query</b> (UC-B3 steps 1&#8211;2; FR-S-01, "
              "S-02, S-03)")
    s.msg("B", "APP", "types a query; optional filters and sort", dx=0)
    s.msg("APP", "API", "GET /search?q=&amp;category=&amp;from=&amp;to=&amp;max_deposit=&amp;condition=&amp;sort= "
          "(proposed)", dx=170)
    s.msg("API", "SS", "search(member, query, filters, sort)")
    s.self_msg("SS", "community := the member's APPROVED community; eligible := PUBLISHED, not the member's own, "
               "owner has not blocked the member, free on the dates")
    alt = s.y - 8
    s.y += 30
    s.msg("SS", "EMB", "embed(query)")
    s.msg("EMB", "SS", "query vector", style=RET)
    s.msg("SS", "DB", "one SELECT: keyword rank (full-text) and vector distance (exact) WHERE eligible AND "
          "filters; LIMIT N", dx=60)
    s.msg("DB", "SS", "candidates with keyword rank and similarity; mode = HYBRID", style=RET)
    g2 = s.y + 18
    s.y += 56
    s.msg("SS", "DB", "SELECT ... full-text rank only WHERE eligible AND filters; LIMIT N", dx=20)
    s.msg("DB", "SS", "candidates; mode = KEYWORD_ONLY", style=RET)
    s.frame("alt", alt, s.y + 4, 480, 1080, guards=[(alt + 22, "[model and vector column available]"),
                                                   (g2, "[model fails, times out, or is too large for the "
                                                        "host: FR-S-02]")])
    s.y += 50

    # ------------------------------------------------------------ 2. ranking
    s.heading("<b>2. Re-ranking with lender evidence; a reason line per result</b> (UC-B3 step 3; FR-S-01, "
              "FR-S-04)")
    s.msg("SS", "RK", "rank(candidates, member, dates, sort)")
    alt3 = s.y - 8
    s.y += 30
    s.msg("RK", "EV", "lender_evidence(lender ids, role LENDER)")
    s.msg("EV", "RK", "per lender: factors with confidence, or \"not enough history yet\"", style=RET)
    g3 = s.y + 18
    s.y += 44
    s.self_msg("RK", "every lender gets the same default prior; no lender is penalised (FR-S-02)")
    s.frame("alt", alt3, s.y + 4, 1090, 1480, guards=[(alt3 + 22, "[engine available]"),
                                                     (g3, "[engine unavailable]")])
    s.y += 30
    s.self_msg("RK", "score from similarity, lender evidence, availability, recency (DA-22); no history = the "
               "prior, never negative")
    s.msg("RK", "SS", "ranked list with the factors behind each position", style=RET)
    s.self_msg("SS", "reason line per result, e.g. \"matches: drill; free on your dates; lender has verified "
               "loans\"; never one trust number")
    s.y += 20

    # ------------------------------------------------------------ 3. logging and response
    s.heading("<b>3. Logging without location, then the response</b> (UC-B3 step 4; FR-S-05)")
    s.msg("SS", "LOG", "log_query(session, query, filters, mode)")
    s.msg("SS", "LOG", "log_results(query_id, [(item_id, rank)])")
    s.msg("LOG", "SS", "query_id", style=RET)
    s.msg("SS", "API", "results, mode, query_id", style=RET)
    s.msg("API", "APP", "200 {query_id, mode, results: [item, reason, lender factors]}", style=RET)
    s.msg("APP", "B", "results; \"keyword results only\" notice when mode = KEYWORD_ONLY", style=RET, dx=150)
    s.y += 20

    # ------------------------------------------------------------ 4. click
    s.heading("<b>4. Opening a result</b> (UC-B3 step 6; continues in UC-B4)")
    opt = s.y - 8
    s.y += 30
    s.msg("B", "APP", "opens the third result")
    s.msg("APP", "API", "POST /search/{query_id}/clicks {item_id} (proposed)", style=ASYNC, dx=40)
    s.msg("API", "LOG", "log_click(query_id, item_id)", style=ASYNC)
    s.msg("APP", "API", "GET /items/{item_id} (existing endpoint; lender evidence added for FR-S-04)", dx=60)
    s.frame("opt", opt, s.y + 4, 40, 1660, guards=[(opt + 22, "[the borrower opens a result]")])
    s.y += 40
    s.note("Results shown but not opened are not logged one by one: the evaluation (DA-25) derives ignored "
           "impressions as shown minus clicked for each query_id. The log holds a pseudonymous session, the query, "
           "the filters, the mode and the ranks, and never a location.", 360, 960, h=48)
    return d


if __name__ == "__main__":
    build().save(os.path.join(HERE, "sequence_i_search.drawio"))
