"""Generates Data_Dictionary.md (design step A4) from the live catalogue plus the meanings below.

    set DM_TEST_DSN=postgresql://...     (schema "dm" loaded, e.g. by test_schema.py)
    python generate_data_dictionary.py

Fails if any column in the database has no meaning here, or a meaning names a column that no longer exists,
so the dictionary and schema.sql cannot drift apart ("done when every data dictionary field has a column").
"""
import json
import os
import sys

import psycopg2

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_CONFIG = os.path.join(HERE, "..", "11_assurance_engine", "Assurance_Engine_Config_Draft.json")

TABLES = {
    "app_user": ("User", "Module 1", "A registered person. Holds no address, coordinates or identity-document number."),
    "user_block": (None, "Module 1", "One user blocking another; requests between them are refused without revealing the block."),
    "community": ("Community", "Module 1", "A neighbourhood or housing society."),
    "membership": ("Membership", "Module 1", "A user's membership of a community, with role and status."),
    "invitation": (None, "Module 1", "A single-use invitation from a verified member (A11 locality method)."),
    "locality_verification": ("LocalityResult", "Module 1", "The coarse result of one locality check (A11). Never coordinates."),
    "category": (None, "Module 3", "Item category, with restricted categories."),
    "item": ("Item", "Module 3", "An item offered for borrowing (seeded in iteration 1)."),
    "borrowing_transaction": ("BorrowingTransaction", "Module 3",
                              "One request-to-return loan. Its state columns are a projection of lifecycle_event."),
    "lifecycle_event": ("LifecycleEvent", "Module 3", "The append-only event store; the source of truth (FR-B-09)."),
    "allowed_transition": (None, "Module 3", "The A3 transition table as reference data (34 rows)."),
    "booking": ("Booking", "Module 3", "Dates held for an accepted request (ADR-0002)."),
    "condition_report": ("ConditionReport", "Module 3", "One party's handover or return confirmation."),
    "attachment": (None, "Module 3 / 9", "Metadata of a photo or document; the file is stored outside the database."),
    "assessment": ("Assessment", "Module 5", "One run of the assurance engine for a request (fields owned by Student 2)."),
    "outcome": ("Outcome", "Module 5", "A verified outcome used as evidence (fields owned by Student 2)."),
    "trust_edge": ("TrustEdge", "Module 5", "Directed evidence edge for k-hop indirect trust (Student 1, ADR-0006)."),
    "review": ("Review", "Module 5", "A rating after a completed loan (seeded for ES-04 and ES-05 in iteration 1)."),
    "escalation_case": ("EscalationCase", "Module 9", "A case for a moderator: a hold or a dispute."),
    "case_statement": (None, "Module 9", "A party's claim, response or requested information on a case."),
    "moderator_decision": ("ModeratorDecision", "Module 9", "A moderator's or admin's decision on a case, with a reason."),
    "audit_log": (None, "Module 9", "Append-only, hash-chained log of privileged actions, rejected commands and log views."),
}

M = {  # (table, column): (meaning, source)
    # ---------------------------------------------------------------- Module 1
    ("app_user", "id"): ("Identifier of the user", "—"),
    ("app_user", "display_name"): ("Name shown to other members (1–80 characters)", "FR-A-12"),
    ("app_user", "email"): ("Contact e-mail; unique, case-insensitive; e-mail or phone required", "FR-A-01"),
    ("app_user", "phone"): ("Contact phone number; unique", "FR-A-01"),
    ("app_user", "password_hash"): ("Salted bcrypt or argon2 hash; never the password", "NFR-S-01"),
    ("app_user", "verification_level"): ("UNVERIFIED < CONTACT_VERIFIED < COMMUNITY_VERIFIED; compared with an item's requirement", "FR-A-02, FR-B-02"),
    ("app_user", "platform_role"): ("MEMBER or ADMIN (community roles live in membership)", "FR-M-01"),
    ("app_user", "status"): ("PENDING_VERIFICATION, ACTIVE, SUSPENDED or BANNED; only ACTIVE users act", "FR-A-05"),
    ("app_user", "is_synthetic"): ("True for seeded synthetic test users (shown as synthetic)", "plan evidence list"),
    ("app_user", "created_at"): ("When the account was created", "—"),
    ("user_block", "blocker_id"): ("User who blocks", "FR-A-14"),
    ("user_block", "blocked_id"): ("User who is blocked", "FR-A-14, UC-B5 3a"),
    ("user_block", "created_at"): ("When the block was set", "—"),
    ("community", "id"): ("Identifier of the community", "—"),
    ("community", "name"): ("Community name; unique, case-insensitive", "FR-A-06"),
    ("community", "join_code"): ("Short public code used to find the community by name or code", "FR-A-06"),
    ("community", "rules"): ("Community rules shown before joining", "FR-A-06"),
    ("community", "boundary_polygon"): ("Coarse boundary of the housing society for the A11 geofence; community data, not personal", "A11, FR-A-07"),
    ("community", "is_active"): ("False when an admin deactivates the community", "FR-M-02"),
    ("community", "created_at"): ("When the community was created", "—"),
    ("membership", "id"): ("Identifier of the membership", "—"),
    ("membership", "user_id"): ("The member", "FR-A-09"),
    ("membership", "community_id"): ("The community", "FR-A-09"),
    ("membership", "role"): ("MEMBER or MODERATOR of this community", "NFR-S-03"),
    ("membership", "status"): ("PENDING, AWAITING_INFORMATION, APPROVED, REJECTED, WITHDRAWN or REVOKED; one live membership per user and community", "FR-A-09, FR-A-10"),
    ("membership", "requested_at"): ("When the membership was requested", "UC-A3"),
    ("membership", "decided_at"): ("When it left PENDING / AWAITING_INFORMATION", "UC-A4"),
    ("invitation", "id"): ("Identifier of the invitation", "—"),
    ("invitation", "community_id"): ("Community the invitation is for; must match the invitee's membership", "A11"),
    ("invitation", "inviter_id"): ("Approved member who issued it; cannot invite themselves", "A11"),
    ("invitation", "code_hash"): ("SHA-256 of the code; the code itself is never stored", "A11, NFR-S-01"),
    ("invitation", "created_at"): ("When it was issued", "A11"),
    ("invitation", "expires_at"): ("Expiry (INVITE_TTL_DAYS after issue)", "A11, UC-A3 3d"),
    ("locality_verification", "id"): ("Identifier of the check", "—"),
    ("locality_verification", "membership_id"): ("Membership the check belongs to", "FR-A-07"),
    ("locality_verification", "method"): ("GEOFENCE_INVITATION (automatic) or MODERATOR_APPROVAL", "A11"),
    ("locality_verification", "outcome"): ("VERIFIED, INCONCLUSIVE or CONFLICTING; must follow the A11 decision table; never negative", "FR-A-08"),
    ("locality_verification", "geofence_signal"): ("Coarse GPS result: INSIDE, NEAR_BOUNDARY, OUTSIDE or UNAVAILABLE; no coordinates", "A11, NFR-PR-02"),
    ("locality_verification", "invitation_id"): ("Invitation used; unique, so a code works once", "A11, UC-A3 3d"),
    ("locality_verification", "permission_refused"): ("Location permission refused; implies UNAVAILABLE and INCONCLUSIVE", "ES-10, UC-A3 3a"),
    ("locality_verification", "mock_provider_detected"): ("Device reported a mock-location provider (spoofing signal); gives CONFLICTING", "A11, §5.13"),
    ("locality_verification", "duplicate_suspected"): ("Duplicate-account signal; gives CONFLICTING", "UC-A3 4d, FR-A-03"),
    ("locality_verification", "approved_by"): ("Moderator or admin who approved, for MODERATOR_APPROVAL only", "UC-A4, A11"),
    ("locality_verification", "checked_at"): ("When the check ran", "—"),
    ("locality_verification", "valid_until"): ("Re-verification date (VALIDITY_DAYS); after it the request-time check is INCONCLUSIVE", "Overview §1, A11"),
    # ---------------------------------------------------------------- Module 3
    ("category", "id"): ("Identifier of the category", "—"),
    ("category", "name"): ("Category name; unique", "FR-B-01"),
    ("category", "is_restricted"): ("Restricted category (medical, automotive, high-value electronics)", "FR-B-02"),
    ("category", "min_verification"): ("Verification level a borrower needs in this category", "FR-B-02"),
    ("item", "id"): ("Identifier of the item", "—"),
    ("item", "owner_id"): ("Lender who owns the listing", "FR-B-01"),
    ("item", "community_id"): ("Community the item is listed in; its only location", "FR-B-01, NFR-PR-01"),
    ("item", "category_id"): ("Category", "FR-B-01"),
    ("item", "title"): ("Listing title (1–120 characters)", "FR-B-01"),
    ("item", "description"): ("Listing description", "FR-B-01"),
    ("item", "value_band"): ("LOW, MEDIUM or HIGH; PKR thresholds in the engine config (Student 2)", "FR-T-03, D14"),
    ("item", "deposit_amount"): ("Deposit to record at handover; record-only, no money moves", "FR-B-11, I-4"),
    ("item", "required_verification"): ("Borrower verification level the lender requires", "FR-B-02"),
    ("item", "status"): ("DRAFT, PENDING_REVIEW, PUBLISHED, PAUSED, EXPIRED or REMOVED; only PUBLISHED can be requested", "FR-B-01, UC-B5 1a"),
    ("item", "created_at"): ("When the listing was created", "—"),
    ("borrowing_transaction", "id"): ("Identifier of the loan; also the stream_id of its events", "FR-B-09"),
    ("borrowing_transaction", "item_id"): ("Item requested", "FR-B-06"),
    ("borrowing_transaction", "borrower_id"): ("Borrower; must differ from the lender", "FR-B-06"),
    ("borrowing_transaction", "lender_id"): ("Lender; must be the item owner", "FR-B-06"),
    ("borrowing_transaction", "requested_period"): ("Requested [start, end) period; start in the future", "FR-B-06"),
    ("borrowing_transaction", "message"): ("Optional message from the borrower", "UC-B5 step 2"),
    ("borrowing_transaction", "created_at"): ("When the request was created", "—"),
    ("borrowing_transaction", "current_state"): ("Projection: lifecycle state after the last event (14 states)", "FR-B-08"),
    ("borrowing_transaction", "stream_version"): ("Projection: stream_seq of the last event; next command must use +1", "ADR-0002"),
    ("borrowing_transaction", "hold_reason"): ("Projection: reason while HELD_FOR_REVIEW, else empty", "ADR-0003"),
    ("borrowing_transaction", "due_at"): ("Projection: due date, set at handover, moved by an approved extension", "FR-B-11, FR-B-14"),
    ("borrowing_transaction", "last_event_at"): ("Projection: time of the last event", "—"),
    ("borrowing_transaction", "closed_at"): ("Projection: time a terminal state was reached", "—"),
    ("lifecycle_event", "event_id"): ("Global identifier of the event (frozen field)", "FR-B-09"),
    ("lifecycle_event", "stream_id"): ("Transaction the event belongs to (frozen field)", "FR-B-09"),
    ("lifecycle_event", "stream_seq"): ("Position in the stream, 1, 2, 3…; unique per stream (frozen field)", "FR-B-09, ADR-0002"),
    ("lifecycle_event", "event_type"): ("One of 21 event types (frozen field; catalogue in State_Machine_Design.md §5)", "FR-B-09"),
    ("lifecycle_event", "schema_version"): ("Version of the event schema / payload contents (frozen field)", "FR-B-09"),
    ("lifecycle_event", "actor_id"): ("User who caused the event; empty for system events (frozen field)", "FR-B-09"),
    ("lifecycle_event", "occurred_at"): ("Server time of the event; clients cannot set it (frozen field)", "FR-B-09"),
    ("lifecycle_event", "previous_state"): ("State before; empty only for request_created (frozen field)", "FR-B-09"),
    ("lifecycle_event", "new_state"): ("State after; must be an allowed transition (frozen field)", "FR-B-08, FR-B-09"),
    ("lifecycle_event", "evidence_refs"): ("References: assessment, decision, condition reports, attachments (frozen field)", "FR-B-09"),
    ("lifecycle_event", "authorisation"): ("Basis of the action: party:borrower, party:lender, role:moderator@<community>, role:admin, system:<component> (frozen field)", "NFR-S-02"),
    ("lifecycle_event", "config_version"): ("Engine configuration used; only on events that carry an assessment (frozen field)", "NFR-D-01"),
    ("lifecycle_event", "payload"): ("Event-specific data, defined per event type (hold reason, dates, decision, outcome…)", "ADR-0005"),
    ("lifecycle_event", "prev_hash"): ("Hash of the previous event in the stream (storage only)", "ADR-0005, NFR-S-05"),
    ("lifecycle_event", "row_hash"): ("Hash of this event and prev_hash; lets verify_event_chain() detect edits", "ADR-0005, NFR-S-05"),
    ("allowed_transition", "from_state"): ("State before", "A3"),
    ("allowed_transition", "event_type"): ("Event type", "A3"),
    ("allowed_transition", "to_state"): ("State after", "A3"),
    ("allowed_transition", "allowed_roles"): ("Roles that may append this transition", "A3, NFR-S-02"),
    ("allowed_transition", "ref"): ("Transition ID(s) in the A3 table (T01–T26, I01–I06)", "A3"),
    ("allowed_transition", "iteration"): ("Iteration in which it is built (1 or 2)", "Iteration 1 plan"),
    ("booking", "id"): ("Identifier of the booking", "—"),
    ("booking", "transaction_id"): ("Accepted transaction; one booking per transaction", "ADR-0002"),
    ("booking", "item_id"): ("Item booked", "ADR-0002"),
    ("booking", "period"): ("Booked period; HELD periods of one item never overlap; extended by an approved extension", "FR-B-05, NFR-R-01"),
    ("booking", "status"): ("HELD from acceptance until COMPLETED or NO_SHOW, then RELEASED", "ADR-0002"),
    ("booking", "created_at"): ("When the request was accepted", "—"),
    ("booking", "released_at"): ("When the dates were released", "FR-B-15"),
    ("condition_report", "id"): ("Identifier of the report", "—"),
    ("condition_report", "transaction_id"): ("Transaction", "FR-B-11, FR-B-13"),
    ("condition_report", "phase"): ("HANDOVER (only in ACCEPTED) or RETURN (only in RETURN_INITIATED)", "UC-B7, UC-B8"),
    ("condition_report", "reporter_id"): ("Party who confirms", "UC-B7, UC-B8"),
    ("condition_report", "reporter_role"): ("BORROWER or LENDER", "UC-B7, UC-B8"),
    ("condition_report", "checklist"): ("Condition checklist answers", "FR-B-11"),
    ("condition_report", "condition_agreed"): ("False means disagreement, which becomes a dispute", "UC-B7 3a, UC-B8 3a"),
    ("condition_report", "deposit_received"): ("Lender's record that the deposit was received (handover only; record-only)", "UC-B7 3b, I-4"),
    ("condition_report", "reduced_evidence"): ("Photos failed; checklist only", "UC-B7 2a"),
    ("condition_report", "notes"): ("Free-text comments", "UC-B7 3a"),
    ("condition_report", "created_at"): ("When the party confirmed; the latest report per party counts", "—"),
    ("attachment", "id"): ("Identifier of the attachment", "—"),
    ("attachment", "transaction_id"): ("Transaction it belongs to", "FR-B-11, FR-B-16"),
    ("attachment", "condition_report_id"): ("Condition report it supports, if any", "UC-B7 step 2"),
    ("attachment", "case_statement_id"): ("Case statement it supports, if any", "UC-B12 step 3"),
    ("attachment", "uploaded_by"): ("Uploader", "—"),
    ("attachment", "storage_key"): ("Key of the file in file storage", "—"),
    ("attachment", "content_sha256"): ("Hash of the file content, kept even if the file is deleted", "NFR-S-05"),
    ("attachment", "mime_type"): ("JPEG, PNG, WebP or PDF only", "NFR-S-06"),
    ("attachment", "metadata_stripped"): ("Must be true: location metadata (EXIF GPS) removed before acceptance", "NFR-PR-01"),
    ("attachment", "created_at"): ("Upload time", "—"),
    # ---------------------------------------------------------------- Module 5
    ("assessment", "id"): ("Identifier of the assessment", "—"),
    ("assessment", "transaction_id"): ("Request assessed", "FR-T-01"),
    ("assessment", "generated_at"): ("When the engine produced it", "—"),
    ("assessment", "config_version"): ("Engine configuration used", "NFR-D-01"),
    ("assessment", "assurance_state"): ("SUFFICIENT_EVIDENCE, REVIEW_RECOMMENDED, INSUFFICIENT_EVIDENCE or ACTIVE_DISPUTE", "FR-T-01"),
    ("assessment", "policy_decision"): ("PROCEED, PROCEED_WITH_SAFEGUARDS, REQUEST_VERIFICATION, RESTRICT_HIGH_VALUE or ESCALATE", "FR-T-06"),
    ("assessment", "hold_reason"): ("manipulation_risk (rule R2) or high_value_low_confidence (rule R4) when the policy holds the request", "ADR-0003, FR-T-06"),
    ("assessment", "posterior_mean"): ("Recency-weighted Beta posterior mean of direct evidence", "FR-T-02"),
    ("assessment", "ci90_low"): ("Lower end of the 90% credible interval", "FR-T-02"),
    ("assessment", "ci90_high"): ("Upper end of the 90% credible interval", "FR-T-02"),
    ("assessment", "effective_evidence"): ("Recency-weighted number of observations", "FR-T-02"),
    ("assessment", "direct_evidence"): ("Direct evidence summary by role and metric", "FR-T-01, FR-T-03"),
    ("assessment", "indirect_evidence"): ("Paths, I(u,v), rho, t_indirect, prior_backed (Student 1)", "FR-T-04"),
    ("assessment", "manipulation_risk"): ("Risk 0–100, separate from trust (renormalised weighted signal score)", "FR-T-05"),
    ("assessment", "manipulation_level"): ("Risk level 1–4 from the bands 0–19, 20–39, 40–59, 60–100; level 4 needs corroboration and must hold the request (rule R2)", "FR-T-06, ADR-0007"),
    ("assessment", "manipulation_corroborated"): ("At least two signals at or above 0.5; without it a score ≥ 60 is capped at level 3", "ADR-0007"),
    ("assessment", "rule_fired"): ("A5 decision-table rule: R1–R5, R6_DISPUTE, R6_SPARSE, R7–R9; fixes the state, decision and hold reason", "FR-T-06, ADR-0008"),
    ("assessment", "manipulation_signals"): ("Signals behind the risk, with evidence; no accusations", "FR-T-05"),
    ("assessment", "safeguards"): ("Recommended safeguards (deposit record, photos, fixed return date…)", "FR-T-01"),
    ("assessment", "explanation"): ("Human-readable explanation; never a single number", "FR-T-08, NFR-U-01"),
    ("outcome", "id"): ("Identifier of the outcome", "—"),
    ("outcome", "transaction_id"): ("Transaction it comes from", "FR-B-15"),
    ("outcome", "source_event_id"): ("transaction_closed or dispute_resolved event it was derived from", "FR-T-03"),
    ("outcome", "subject_id"): ("Party the evidence is about", "Overview §5.10"),
    ("outcome", "observer_id"): ("Other party, who observed it; also the source of the trust edge", "Overview §5.10, ADR-0006"),
    ("outcome", "subject_role"): ("Role of the subject: BORROWER or LENDER", "Overview §5.3"),
    ("outcome", "metric"): ("ON_TIME_RETURN, CONDITION_AGREED or DISPUTE_FREE (list owned by Student 2)", "FR-B-15"),
    ("outcome", "success"): ("Whether the outcome was a success for this metric", "Overview §5.2"),
    ("outcome", "occurred_at"): ("When it happened; drives the recency weight", "FR-T-03"),
    ("outcome", "category_id"): ("Item category at the time (similarity)", "FR-T-03"),
    ("outcome", "value_band"): ("Item value band at the time (similarity)", "FR-T-03"),
    ("outcome", "loan_duration"): ("Loan length (similarity)", "FR-T-03"),
    ("outcome", "status"): ("VALID, or FLAGGED_FOR_REEVALUATION after a reversal", "ES-11, FR-T-11"),
    ("outcome", "flagged_by_decision_id"): ("Decision that flagged it", "ES-11"),
    ("trust_edge", "source_id"): ("User whose verified experience the edge records", "FR-T-04"),
    ("trust_edge", "target_id"): ("User the experience is about", "FR-T-04"),
    ("trust_edge", "role"): ("Role of the target in those outcomes", "FR-T-04"),
    ("trust_edge", "metric"): ("Outcome metric", "FR-T-04"),
    ("trust_edge", "weight"): ("Recency-weighted Beta posterior mean of the source's confirmed outcomes about the target, in (0, 1)", "ADR-0006"),
    ("trust_edge", "evidence_count"): ("Number of outcomes behind the edge (≥ 1)", "ADR-0006"),
    ("trust_edge", "updated_at"): ("When the edge was last recomputed", "ADR-0006"),
    ("review", "id"): ("Identifier of the review", "—"),
    ("review", "transaction_id"): ("Completed transaction reviewed", "FR-T-09"),
    ("review", "reviewer_id"): ("Party who writes the review", "FR-T-09"),
    ("review", "reviewee_id"): ("Other party", "FR-T-09"),
    ("review", "reviewee_role"): ("BORROWER or LENDER", "FR-T-09"),
    ("review", "ratings"): ("One rating per dimension", "FR-T-09"),
    ("review", "comment"): ("Review text", "FR-T-09"),
    ("review", "retaliation_flag"): ("Suspected retaliation (follows a dispute, conflicts with records)", "FR-T-09, ES-05"),
    ("review", "similarity_flag"): ("Near-identical text to other reviews", "FR-T-09"),
    ("review", "created_at"): ("When it was written", "—"),
    # ---------------------------------------------------------------- Module 9
    ("escalation_case", "id"): ("Identifier of the case", "—"),
    ("escalation_case", "transaction_id"): ("Transaction; one live case at a time", "FR-T-10, UC-D6 1b"),
    ("escalation_case", "opened_event_id"): ("held_for_review or dispute_opened event that opened it", "UC-D6"),
    ("escalation_case", "trigger_type"): ("DISPUTE, MANIPULATION_FLAG, HIGH_VALUE_LOW_CONFIDENCE, LOCALITY_HOLD or ENGINE_FAILURE", "FR-T-10"),
    ("escalation_case", "hold_reason"): ("Hold reason, for non-dispute cases", "ADR-0003"),
    ("escalation_case", "dispute_reason"): ("DAMAGE, NON_RETURN, CONDITION_MISMATCH, NO_SHOW or OTHER, for disputes", "UC-B12 step 2"),
    ("escalation_case", "raised_by"): ("Party who raised the dispute; only they may withdraw it", "FR-B-17"),
    ("escalation_case", "status"): ("OPEN, AWAITING_INFORMATION, DECIDED, APPEALED, REVERSED or WITHDRAWN (A3 case states)", "A3"),
    ("escalation_case", "priority"): ("1 (highest) to 3", "FR-T-10"),
    ("escalation_case", "reason"): ("Why the case was opened", "FR-T-10"),
    ("escalation_case", "assigned_to"): ("Moderator, or admin if none or a moderator is involved", "UC-D6 2a, UC-I4 3b"),
    ("escalation_case", "info_deadline"): ("Deadline for requested information", "UC-I4 step 2"),
    ("escalation_case", "opened_at"): ("When it was opened", "—"),
    ("escalation_case", "closed_at"): ("When it was decided or withdrawn", "—"),
    ("case_statement", "id"): ("Identifier of the statement", "—"),
    ("case_statement", "case_id"): ("Live case", "FR-B-17"),
    ("case_statement", "author_id"): ("Party who wrote it", "FR-B-17"),
    ("case_statement", "author_role"): ("BORROWER or LENDER", "FR-B-17"),
    ("case_statement", "statement"): ("Claim, response or requested information", "UC-B12 step 5"),
    ("case_statement", "created_at"): ("When it was submitted", "—"),
    ("moderator_decision", "id"): ("Identifier of the decision", "—"),
    ("moderator_decision", "case_id"): ("Case decided", "FR-T-11"),
    ("moderator_decision", "decided_by"): ("Moderator or admin; never a party", "FR-T-11, NFR-S-03"),
    ("moderator_decision", "decider_role"): ("MODERATOR or ADMIN", "FR-T-11"),
    ("moderator_decision", "kind"): ("CLEARED, SAFEGUARDS_IMPOSED, RESTRICTED, DISPUTE_RESOLVED (appeal and reversal kinds: iteration 2)", "UC-I4"),
    ("moderator_decision", "reason"): ("Mandatory reason", "FR-T-11"),
    ("moderator_decision", "safeguards"): ("Safeguards imposed, only for SAFEGUARDS_IMPOSED", "ADR-0003"),
    ("moderator_decision", "resolved_outcome"): ("Dispute result, recorded as evidence", "FR-B-15, FR-T-11"),
    ("moderator_decision", "reverses_decision_id"): ("Decision this one reverses or overturns (iteration 2); both are kept", "ES-11"),
    ("moderator_decision", "decided_at"): ("When it was decided", "—"),
    ("audit_log", "id"): ("Position in the global log", "FR-M-05"),
    ("audit_log", "occurred_at"): ("Server time", "FR-M-05"),
    ("audit_log", "actor_id"): ("Who acted; empty for the system", "FR-M-05"),
    ("audit_log", "authorisation"): ("Basis of the action (same format as lifecycle_event, or member)", "NFR-S-02"),
    ("audit_log", "action"): ("What was done, e.g. transition_rejected, audit_log_viewed, case actions C02–C05", "FR-M-05"),
    ("audit_log", "target_type"): ("Kind of object acted on", "FR-M-05"),
    ("audit_log", "target_id"): ("Identifier of that object", "FR-M-05"),
    ("audit_log", "previous_value"): ("Value before, masked if sensitive", "FR-M-05"),
    ("audit_log", "new_value"): ("Value after, masked if sensitive", "FR-M-05"),
    ("audit_log", "evidence_refs"): ("References to supporting evidence", "FR-M-05"),
    ("audit_log", "outcome"): ("SUCCESS or REJECTED", "FR-B-08"),
    ("audit_log", "reason"): ("Why it was rejected (required for REJECTED)", "FR-B-08"),
    ("audit_log", "prev_hash"): ("Hash of the previous entry", "NFR-S-05"),
    ("audit_log", "row_hash"): ("Hash of this entry and prev_hash", "NFR-S-05"),
}

def _cfg():
    with open(ENGINE_CONFIG, encoding="utf-8") as fh:
        return json.load(fh)


def config_rows():
    """Configuration parameters; the values are read from the versioned config file so they cannot drift."""
    c = _cfg()
    t1, t2 = c["trust_estimation_alg1"], c["indirect_trust_alg2"]
    m3, p4 = c["manipulation_detection_alg3"], c["decision_policy_alg4"]
    th, vb, loc = p4["thresholds"], p4["value_bands_pkr"], c["locality_a11"]
    return [
        # parameter, initial value, used by, source
        ("config_version", c["config_metadata"]["config_version"], "stored on every assessment", "NFR-D-01"),
        ("prior alpha0, beta0", f"{t1['prior']['alpha_0']:g}, {t1['prior']['beta_0']:g}", "direct estimate; trust-edge weight", "Overview §5.2; ADR-0006"),
        ("recency half-life", f"{t1['recency_decay']['half_life_days']:g} days", "direct estimate; trust-edge weight", "Overview §5.2; FR-T-03"),
        ("credible interval", f"{t1['credible_interval']['confidence_level']:.0%}", "direct estimate", "Overview §5.2; FR-T-02"),
        ("similarity floor", f"{t1['similarity_weighting']['similarity_floor']:g}", "high-value rule R4", "Overview §5.12"),
        ("k (max hops)", f"{t2['graph_traversal']['max_hops_k']}", "k-hop search", "Overview §5.5; FR-T-04"),
        ("gamma (hop decay)", f"{t2['attenuation_decay']['hop_decay_gamma']:g}", "k-hop search", "Overview §5.5; FR-T-04"),
        ("indirect reliability cap", f"{t2['aggregation']['reliability_cap_rho_max']:g}", "k-hop search", "Overview §5.5; FR-T-04"),
        ("path-count and diversity divisors", f"{t2['aggregation']['path_count_divisor']:g}, {t2['aggregation']['diversity_divisor']:g}", "k-hop reliability", "Overview §5.5"),
        ("population baseline b", f"{t2['baseline']['default_population_baseline']:g}", "k-hop estimate", "Overview §5.5"),
        ("manipulation signals active", ", ".join(m3["signal_weights"]["iteration_1_active"]), "manipulation risk", "ADR-0007"),
        ("manipulation risk bands", "0–19, 20–39, 40–59, 60–100", "decision policy", "Overview §5.6"),
        ("corroboration for level 4", f"≥ {m3['corroboration_guard']['required_corroborating_signals']} signals ≥ {m3['corroboration_guard']['min_signal_threshold']:g}", "rule R2 (hold)", "ADR-0007"),
        ("retaliation window", f"{m3['observation_windows']['retaliation_window_days']} days", "retaliation check", "FR-T-09; ES-05"),
        ("tau_mu, tau_L, n_min", f"{th['tau_mu_mean_threshold']:g}, {th['tau_L_lower_bound_threshold']:g}, {th['n_min_effective_observations']:g}", "SUFFICIENT_EVIDENCE (R7, R8)", "Algorithm doc §6"),
        ("rho_sup (indirect support)", f"{th['rho_sup_indirect_support_threshold']:g}", "rules R3, R6_SPARSE", "ADR-0008"),
        ("resolved-dispute look-back", f"{p4['context_windows']['resolved_disputes_lookback_months']} months", "rule R6_DISPUTE", "ES-03"),
        ("engine timeout", f"{p4['context_windows']['engine_timeout_ms']} ms", "assess() call; timeout → engine_failure hold", "FR-T-07"),
        ("value bands (PKR)", f"LOW ≤ {vb['low_value_max']:,}, MEDIUM ≤ {vb['medium_value_max']:,}, HIGH ≥ {vb['high_value_min']:,}", "similarity, rules R4, R7, R8", "FR-T-03; N-7"),
        ("MAX_ACCURACY_M", f"{loc['max_accuracy_m']} m", "locality geofence", "A11"),
        ("MIN_MARGIN_M", f"{loc['min_margin_m']} m", "locality geofence", "A11"),
        ("INVITE_TTL_DAYS", f"{loc['invite_ttl_days']} days", "invitations", "A11"),
        ("MAX_OPEN_INVITES", f"{loc['max_open_invites']} per member", "invitations", "A11"),
        ("VALIDITY_DAYS", f"{loc['validity_days']} days", "locality re-verification", "A11; Overview §1"),
        ("response window, handover grace, overdue limit, dispute window, confirmation window", "TBD", "scheduler (iteration 2)", "FR-B-10, B-12, B-14, B-16"),
    ]


def main():
    conn = psycopg2.connect(os.environ["DM_TEST_DSN"])
    with conn, conn.cursor() as cur:
        cur.execute("""SELECT c.table_name, c.column_name, c.is_nullable = 'YES',
                              CASE WHEN c.data_type = 'USER-DEFINED' THEN c.udt_name
                                   WHEN c.data_type = 'ARRAY' THEN substr(c.udt_name, 2) || '[]'
                                   WHEN c.data_type = 'timestamp with time zone' THEN 'timestamptz'
                                   WHEN c.data_type = 'numeric' THEN 'numeric(' || c.numeric_precision || ',' || c.numeric_scale || ')'
                                   ELSE c.data_type END
                       FROM information_schema.columns c JOIN information_schema.tables t
                         ON t.table_schema = c.table_schema AND t.table_name = c.table_name AND t.table_type = 'BASE TABLE'
                      WHERE c.table_schema = 'dm' ORDER BY c.table_name, c.ordinal_position""")
        cols = cur.fetchall()
        cur.execute("""SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder) FROM pg_type t
                       JOIN pg_enum e ON e.enumtypid = t.oid JOIN pg_namespace n ON n.oid = t.typnamespace
                      WHERE n.nspname = 'dm' GROUP BY t.typname ORDER BY t.typname""")
        enums = cur.fetchall()
        cur.execute("""SELECT rel.relname, att.attname, con.contype FROM pg_constraint con
                       JOIN pg_class rel ON rel.oid = con.conrelid JOIN pg_namespace ns ON ns.oid = rel.relnamespace
                       JOIN unnest(con.conkey) k(n) ON true JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = k.n
                      WHERE ns.nspname = 'dm' AND con.contype IN ('p', 'f', 'u')""")
        keys = {}
        for t, c, k in cur.fetchall():
            keys.setdefault((t, c), set()).add({"p": "PK", "f": "FK", "u": "UQ"}[k])
    db = {(t, c) for t, c, *_ in cols}
    missing, extra = db - set(M), set(M) - db
    if missing or extra:
        sys.exit(f"data dictionary out of date. Missing meanings: {sorted(missing)}. Unknown columns: {sorted(extra)}")
    if set(t for t, _ in db) != set(TABLES):
        sys.exit(f"table descriptions out of date: {set(t for t, _ in db) ^ set(TABLES)}")

    L = ["# Digital Mohalla: Data Dictionary (design step A4)", "",
         "| Field | Value |", "|---|---|",
         "| Owner | Student 1 (Student 2 owns the meaning of the assessment, outcome and review fields) |",
         "| Version | 1.1, 11 October 2026 (schema.sql v2.3: integration decisions D10–D14, ADR-0007, ADR-0008) |",
         "| Status | Generated from the live database: every column has exactly one entry. To be signed by all three, then tag `schema-v1`. |",
         "| Generated by | `06_data_model/generate_data_dictionary.py` (do not edit by hand) |",
         "| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |", "",
         f"{len(TABLES)} tables, {len(db)} columns. Key: PK primary key, FK foreign key, UQ unique; \"null\" = optional. "
         "The event catalogue (payload contents per event type) is in `07_state_machines/State_Machine_Design.md` §5.", ""]
    order = list(TABLES)
    for t in order:
        cls, mod, desc = TABLES[t]
        L += [f"## `{t}`" + (f" — {cls}" if cls else ""), "", f"*{mod}.* {desc}", "",
              "| Column | Type | Key | Null | Meaning | Source |", "|---|---|---|---|---|---|"]
        for tt, c, nullable, typ in cols:
            if tt != t:
                continue
            meaning, src = M[(t, c)]
            L.append(f"| `{c}` | {typ} | {', '.join(sorted(keys.get((t, c), [])))} | {'null' if nullable else ''} | "
                     f"{meaning} | {src} |")
        L.append("")
    L += ["## Enumerated types", "", "| Type | Values |", "|---|---|"]
    for name, vals in enums:
        L.append(f"| `{name}` | {', '.join(vals)} |")
    L += ["", "## Configuration parameters (NFR-D-01)", "",
          "All values are initial and unvalidated; each assessment stores the `config_version` it used. Values are read from "
          "`11_assurance_engine/Assurance_Engine_Config_Draft.json`, the single versioned configuration file.", "",
          "| Parameter | Initial value | Used by | Source |", "|---|---|---|---|"]
    config = config_rows()
    for row in config:
        L.append("| " + " | ".join(row) + " |")
    L += ["", "## Assessment output object (`AssessmentResult`)", "",
          "Returned by `assess(request)` (Student 2's `AssuranceResult`, Algorithm doc §2) and stored as one `assessment` row: "
          "`assurance_state`, `policy_decision`, `rule_fired`, `hold_reason`, `posterior_mean`, `ci90_low`, `ci90_high`, "
          "`effective_evidence`, `direct_evidence`, `indirect_evidence`, `manipulation_risk`, `manipulation_level`, "
          "`manipulation_corroborated`, `manipulation_signals`, `safeguards`, `explanation`, `config_version`. "
          "The field-by-field mapping between the engine contract and these columns is in `Assurance_Data_Dictionary.md` §5. "
          "The lifecycle holds the request exactly when `hold_reason` is set (rules R2, R4); on timeout or failure there is "
          "no object and the request is held with reason `engine_failure` (FR-T-07).", "",
          "## Sign-off", "", "| Student 1 | Student 2 | Student 3 | Date | Tag |", "|---|---|---|---|---|",
          "| | | | | `schema-v1` |"]
    with open(os.path.join(HERE, "Data_Dictionary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"Data_Dictionary.md: {len(TABLES)} tables, {len(db)} columns, {len(enums)} enum types, {len(config)} parameters")


if __name__ == "__main__":
    main()
