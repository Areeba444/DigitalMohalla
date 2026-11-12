# User Interface Wireframes & Architectural Annotations (Iteration 2)

**Deliverable ID:** Design Step A12 / UX-02  
**Applicable Documents:** Use Cases v1.4, FR/NFR v1.4, ADR-0009 to ADR-0016  
**Design Standard:** Mobile (iOS/Android 390×844), Mid-Fidelity Wireframes & Code Shells  
**Milestone:** FYP-1 Final Evaluation (Iteration 2)  
**Author:** Areeba (UI & Assurance Engine Lead)  

---

## 1. Overview and Iteration 2 Additions

Building on the 8 baseline wireframes from Iteration 1 (W1 through W7), Iteration 2 adds **17 new architectural views** (W8 through W24) to complete the borrowing lifecycle, community locality verification, bilateral condition evidence, dispute possession exits (DM14), and explainable search and discovery.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              Iteration 2 Wireframe Catalog                             │
├─────────┬──────────────────────────────────────────┬──────────────┬────────────────────┤
│ Screen  │ Description                              │ Viewport     │ Code Route         │
├─────────┼──────────────────────────────────────────┼──────────────┼────────────────────┤
│ W8      │ Registration, Terms & Privacy Notice     │ Mobile (390) │ /register          │
│ W9      │ Join Community: Directory & Rules        │ Mobile (390) │ /community/join    │
│ W10     │ Locality Verification (3-Valued Outcome) │ Mobile (390) │ /community/verify  │
│ W11     │ Moderator Membership Queue & Triage      │ Mobile (390) │ /members/index     │
│ W12     │ Notification Center & Action Inbox       │ Mobile (390) │ /notifications     │
│ W13     │ Loan Extension Request & Response        │ Mobile (390) │ /request/[id]/ext  │
│ W14     │ Counter-Offer: Propose & Review          │ Mobile (390) │ /request/[id]/cntr │
│ W15     │ Bilateral Multi-Dimensional Review       │ Mobile (390) │ /request/[id]/rev  │
│ W16     │ My Evidence & Personal Trust Profile     │ Mobile (390) │ /profile/evidence  │
│ W17     │ Handover/Return Photos (EXIF Stripped)   │ Mobile (390) │ /request/[id]/pht  │
│ W18     │ Party Response to Info Request (w/ SLA)  │ Mobile (390) │ /dispute/[id]/resp │
│ W19     │ Moderator Adjudication (Possession Exit) │ Mobile (390) │ /moderation/[id]/a │
│ W20     │ Dispute Appeal & Second Moderator Review │ Mobile (390) │ /dispute/[id]/app  │
│ W21     │ Admin Audit Log & Privacy Masking Feed   │ Mobile (390) │ /(admin)/audit     │
│ W22     │ Create & Edit Item Listing (with Drafts) │ Mobile (390) │ /item/create       │
│ W23     │ Search Results with Hybrid Re-Ranking    │ Mobile (390) │ /(tabs)/browse     │
│ W24     │ Item Details with Lender Evidence Tier   │ Mobile (390) │ /item/detail/[id]  │
└─────────┴──────────────────────────────────────────┴──────────────┴────────────────────┘
```

---

## 2. Screen Specifications & Engineering Annotations

### Screen W8 — Registration, Terms & Privacy Notice
- **Engineering Annotations:**
  1. **Zero GPS Coordinate Storage Banner [NFR-PR-01]:** Informs applicants that Digital Mohalla never records or shares precise GPS coordinates.
  2. **Validated Identity Input:** Input fields for Name, Email, and Password with inline validation feedback (minimum 8 characters).
  3. **Community Standards Covenant:** Mandatory checkbox agreeing to care of borrowed neighborhood goods.
  4. **Privacy Protection Agreement:** Checkbox confirming understanding of identity verification safeguards.
  5. **Single Primary Action:** Prominent 52dp "Create Account" CTA; secondary navigation link for existing users.
  6. **Anti-Leak Account Existence Rule [FR-A-01]:** Registration endpoints return generic confirmations without disclosing whether an email address already exists.
- **Traceability:** UC-A1, FR-A-01, NFR-PR-01, ADR-0011.

---

### Screen W9 — Join Community: Directory & Rules
- **Engineering Annotations:**
  1. **Mohalla Search Bar:** Real-time filter by community name, sector (e.g., F-7, G-10), or mohalla code.
  2. **Community Density Metrics:** Cards display active neighbor count and total shared items, providing social proof.
  3. **Progressive Rules Disclosure:** Collapsible drawer exposing maximum loan duration, deposit norms, and photo requirements.
  4. **Access Control Gating:** Badges distinguish open neighborhood communities from invite-only communities.
  5. **Conditional Voucher Affordance:** Invitation code entry field appears only when an invite-only community is selected.
  6. **Single Primary CTA:** "Select & Continue to Verification" guides applicants to Step 2.
- **Traceability:** UC-A3, FR-A-06, NFR-U-01.

---

### Screen W10 — Locality Verification (3-Valued Outcome)
- **Engineering Annotations:**
  1. **Transient Geofence Check [FR-A-07, DM02]:** Executes client-side coordinate boundary check; coordinates are cleared from memory immediately following evaluation.
  2. **Voucher Invitation Code Input [FR-A-09]:** 6-character code fallback allowing neighbors to vouch for applicants.
  3. **Three-Valued Neutral Feedback [FR-A-08]:** Displays `VERIFIED`, `INCONCLUSIVE`, or `CONFLICTING`. Conflicting readings are never auto-rejected; they transfer gracefully to a human moderator.
  4. **Non-Blaming Microcopy:** Advisory explaining that indoor readings frequently produce ambiguous signals.
  5. **Moderator Queue Dispatch:** Inconclusive and conflicting outcomes automatically dispatch an audit packet to local moderators.
  6. **Contextual Primary Action:** "Continue to Home" on verification, or "Done — Wait for Moderator" on review dispatch.
- **Traceability:** UC-A3, FR-A-07, FR-A-08, FR-A-09, DM02, NFR-Q-04.

---

### Screen W11 — Moderator Membership Queue & Triage
- **Engineering Annotations:**
  1. **Tenant Boundary Banner [NFR-S-03]:** Header displays community scope (`F-7 Sector 4 [Isolated]`), enforcing strict multi-tenant partition.
  2. **Voucher Context Inspection:** Surfaces vouching neighbor's identity and historical standing when voucher was utilized.
  3. **Signal Quality Badge:** Text-and-icon badges displaying whether signal was `MATCH`, `INCONCLUSIVE`, or `CONFLICTING`.
  4. **Mandatory Audit Justification:** Decision form enforces mandatory text rationale before approving or requesting info.
  5. **Dual Decision Affordance:** Binary buttons for "Approve" (green) and "Request More Info" (outline).
  6. **Concurrency Safety [FR-A-11]:** Optimistic locking prevents duplicate moderator determinations on the same applicant.
- **Traceability:** UC-A4, FR-A-10, FR-A-11, NFR-S-03.

---

### Screen W12 — Notification Center & Action Inbox
- **Engineering Annotations:**
  1. **Categorized Triage Tabs:** Segmented filter chips for "All", "Action Required", and "Updates".
  2. **Visual Unread Affirmation:** Unread items feature subtle tint, bold headline, and primary color dot (never color alone).
  3. **1-Tap Deep Linking:** Tapping an action notification routes directly to the relevant transaction or review screen.
  4. **Idempotent Polling:** Polled notifications check deduplication key (`notification_id`) preventing duplicate visual alerts.
  5. **Urgent Lifecycle Alerts:** Overdue return warnings and dispute notifications display high-contrast priority icons.
  6. **Calm Empty State:** "All caught up" state provides positive psychological closure when no tasks are pending.
- **Traceability:** UC-G3, FR-G-03, FR-C-02, Module 7.

---

### Screen W13 — Loan Extension Request & Response
- **Engineering Annotations:**
  1. **Dual Role Views:** Borrower view displays duration stepper and justification; lender view displays accept/decline actions.
  2. **Bounded Extension Stepper:** Numerical stepper restricting extensions to between +1 and +7 days.
  3. **Date Delta Pill:** Displays original return date contrasted against new proposed return date.
  4. **Automatic Escalation Notice:** Reassures that extensions must be agreed prior to due date to prevent automatic dispute logging.
  5. **Binary Lender Actions:** "Accept Extension" updates return timestamp; "Decline" preserves original timeline.
  6. **Assessment Invariant:** Accepted extensions trigger background loan duration re-evaluation without invalidating deposit.
- **Traceability:** UC-B8, FR-B-14, FR-B-10.

---

### Screen W14 — Counter-Offer: Propose & Review
- **Engineering Annotations:**
  1. **Original Schedule Baseline:** Summarizes borrower's requested reservation dates.
  2. **Alternative Date Inputs:** Date pickers allowing lender to propose alternative windows when originally requested dates conflict.
  3. **Duration Similarity Notice [ADR-0015]:** Informs that counter-offers re-evaluate loan duration similarity in the background.
  4. **Optional Coordination Message:** Text input for lender remarks (e.g., "Drill available starting Friday").
  5. **Borrower Confirmation Card:** Borrower inspects proposed dates with 1-tap "Accept Dates" or "Decline".
  6. **Soft-Hold Release:** Declining a counter-offer cleanly releases booking holds without penalty.
- **Traceability:** UC-B6, FR-B-10, FR-B-06, ADR-0015.

---

### Screen W15 — Bilateral Multi-Dimensional Review
- **Engineering Annotations:**
  1. **Completion Gating [FR-B-15]:** Review screen is locked until booking state achieves `COMPLETED`.
  2. **Multi-Axis Rating Chips (No Stars):** Three discrete dimensions evaluated via chips: Punctuality, Condition Care, and Neighborliness.
  3. **Anti-Collusion Screening Notice:** Advisory informing parties that reviews are checked for reciprocal collusion rings before affecting assurance weights.
  4. **Observable Facts Prompt:** Freeform text area guiding users toward objective behavioral descriptions.
  5. **Immutable Submission:** Submitting commits review permanently to the event store; no post-hoc tampering permitted.
  6. **Symmetric Independence:** Review submission is bilateral; one party's rating is blinded until both submit or window expires.
- **Traceability:** UC-D1, FR-D-01, FR-T-09, FR-B-15, NFR-U-01.

---

### Screen W16 — My Evidence & Personal Trust Profile
- **Engineering Annotations:**
  1. **Zero Composite Trust Score [NFR-U-01]:** No numerical rating, star, or grade is visible anywhere on the surface.
  2. **Posterior Beta Credible Interval Bar:** Visualizes the 90% credible interval $[low, high]$ derived from Beta posterior distribution with marked mean.
  3. **Narrow vs. Wide Range Indicator:** Plain-text explanation clarifying that wide intervals denote sparse evidence rather than untrustworthiness.
  4. **Dimensional Breakdown Cards:** Granular statistics on verified loan count, return punctuality rate, and zero-damage records.
  5. **Independent Manipulation Risk Pill:** Manipulation risk displayed strictly as a security status (Low / Monitor), decoupled from transaction counts.
  6. **Data Minimization Assurance:** Prominent notice reminding that no identity cards or precise GPS coordinates are retained.
- **Traceability:** UC-D2, FR-D-02, FR-T-08, NFR-U-01.

---

### Screen W17 — Handover/Return Photos (EXIF Stripped)
- **Engineering Annotations:**
  1. **Dual Inspection Slots:** Slot 1 for overall item condition; Slot 2 for serial number / critical working surface.
  2. **EXIF Security Badging [ADR-0014]:** Reassures users with "GPS stripped" badge on each camera affordance.
  3. **Reduced Evidence Fallback:** Checkbox allowing users without functional cameras to proceed under "reduced evidence" status without aborting.
  4. **Handover vs. Return Contrast:** Side-by-side thumbnail layout allowing immediate delta identification upon return.
  5. **Storage Port Abstraction:** Uploaded media interacts with abstract StoragePort (local disk in development, object storage in production).
  6. **File Integrity Guards:** Upload handlers reject files exceeding 5MB or non-image MIME types (TC-59, TC-85).
- **Traceability:** UC-B7, UC-B8, FR-B-11, FR-B-12, FR-B-17, ADR-0014.

---

### Screen W18 — Party Response to Info Request (w/ SLA)
- **Engineering Annotations:**
  1. **Urgent SLA Countdown Timer:** Visual countdown badge alerting party to remaining response window; shifts from neutral info to warning (<24h) and danger (<1h).
  2. **Quoted Moderator Query:** Quotes the exact question or clarification requested by the adjudicating moderator.
  3. **Evidence Attachment Affordance:** Allows party to attach supplementary photographs or receipts.
  4. **Response Text Validation:** Mandatory text explanation required prior to enabling submission.
  5. **Automatic Closure Advisory:** Warns party that expiration without response routes case to default moderator resolution.
  6. **Direct Submission Action:** 1-tap "Submit Response to Moderator" committing event `information_response_provided`.
- **Traceability:** UC-I4, FR-I-04, FR-B-17.

---

### Screen W19 — Moderator Adjudication (Possession Exit / DM14 Fix)
- **Engineering Annotations:**
  1. **Item Possession Selector [DM14]:** Radio group requiring explicit physical item possession determination before case closure:
     - Item returned to lender (Closes booking as `COMPLETED`).
     - Item still with borrower (Transitions back to `ACTIVE`, booking held).
     - Never handed over / No-show (Transitions to `NO_SHOW`, booking released).
     - Irreparably lost/damaged (Closes with failure flag, pauses item listing).
  2. **Human-Only Adjudication Banner:** Enforces invariant that automated algorithms never unilaterally penalize or restrict members.
  3. **Deposit Disposition Ruling:** Radio selection to return deposit to borrower or forfeit deposit to lender.
  4. **Mandatory Justification Field:** Enforces minimum 20-character written rationale for the audit record.
  5. **Immutable Event Commitment:** "Commit Binding Resolution" appends signed `dispute_resolved` event.
  6. **Transition Table Regeneration:** Supported by expanded 294-pair state machine transition matrix.
- **Traceability:** UC-I4, FR-I-04, DM14, ADR-0009.

---

### Screen W20 — Dispute Appeal & Second Moderator Review
- **Engineering Annotations:**
  1. **Appeal Window Timer:** Displays hours remaining within the 72-hour formal appeal window.
  2. **First-Instance Decision Summary:** Context card detailing the initial moderator determination and possession ruling.
  3. **Categorized Grounds Checkboxes:** Structured selection for appeal grounds (new evidence, procedural error, pre-existing condition).
  4. **Detailed Statement Box:** Text input for appellant's comprehensive grievance statement.
  5. **Independent Re-Assignment Guarantee:** Informs that appeal is routed strictly to an independent second moderator or platform administrator.
  6. **Formal Appeal Commitment:** Commits `dispute_appealed` event, updating case state to `APPEAL_PENDING`.
- **Traceability:** UC-I4, FR-T-11, ES-11.

---

### Screen W21 — Admin Audit Log & Privacy Masking Feed
- **Engineering Annotations:**
  1. **Tamper-Evident Hash Chain Banner:** Displays SHA-256 event hash chain verification status (`VALID`).
  2. **Domain Event Filter Carousel:** Filter chips for `ALL`, `TRANSACTION`, `DISPUTE`, `MEMBERSHIP`, and `ASSURANCE`.
  3. **Masked Privacy Boundary [NFR-PR-01]:** Replaces raw coordinates, CNIC, and phone numbers with `[MASKED_PRIVACY_BOUNDARY]`.
  4. **Masked Actor Identifiers:** Replaces sensitive user IDs with anonymized actor hashes (`usr_...4f2a`).
  5. **Immutable Event Metadata:** Displays exact UTC timestamps, event types, and structured domain payloads.
  6. **Self-Auditing Observer Notice:** Informs administrator that the current audit view action has been appended to access logs.
- **Traceability:** UC-I6, FR-M-05, FR-I-06, NFR-PR-01.

---

### Screen W22 — Create & Edit Item Listing (with Drafts)
- **Engineering Annotations:**
  1. **3-Step Listing Wizard:** Segmented wizard (Details → Photos & Terms → Review & Publish) eliminating cognitive overload.
  2. **Roman Urdu Autocomplete Hints [NFR-U-05]:** Quick-tap chips suggesting common Pakistani household goods (*Drill machine*, *Silai machine*, *Charpai*, *Istari*).
  3. **Standard Category Taxonomy:** Dropdowns for Tools, Appliances, Gardening, Sports, and Books.
  4. **Condition Assessment Radios:** Graded chips for `Like New`, `Good`, `Fair`, and `Heavily Used`.
  5. **Record-Only Deposit Advisory:** Prominent notice confirming that cash deposits are recorded on paper only (zero in-app financial transactions).
  6. **Draft Persistence Affordance:** "Save Draft" allows saving incomplete listings without publishing to community browse feed.
- **Traceability:** UC-B1, FR-B-01, NFR-U-05.

---

### Screen W23 — Search Results with Hybrid Re-Ranking
- **Engineering Annotations:**
  1. **Hybrid Retrieval Query Bar:** Search input supporting full-text keyword queries and semantic vector embeddings.
  2. **Model Fallback Notice [FR-S-02]:** Automatic advisory banner when vector embedding model is offline: "Showing keyword search results".
  3. **ReasonLine per Result [NFR-Q-05]:** Explanatory chips below each item card detailing ranking factors (e.g., *"Same Mohalla · 100% on-time return · Available this week"*).
  4. **Population Baseline Fairness Banner:** Guarantees that new lenders receive the population baseline and are not penalized in ranking for lack of history.
  5. **Multi-Parameter Filter Carousel:** Horizontal filter chips for Category, Value Band, Deposit, and Same Mohalla.
  6. **Multi-Axis Sorting:** Allows sorting by Relevance, Lender Evidence, or Newest.
- **Traceability:** UC-B3, FR-S-01, FR-S-02, FR-S-03, NFR-Q-05, ADR-0016.

---

### Screen W24 — Item Details with Lender Evidence Tier
- **Engineering Annotations:**
  1. **Item Photographic Hero:** High-contrast illustration or photo preview with condition and category tags.
  2. **Visual Availability Strip:** Horizontal 5-day availability calendar using color AND dashed borders (not color alone) to distinguish reserved dates.
  3. **Lender Multi-Dimensional Assurance Card:** Displays lender avatar, verified mohalla tag, and assurance state badge (`SUFFICIENT_EVIDENCE` or neutral `INSUFFICIENT_EVIDENCE`).
  4. **Zero Single Trust Number Guarantee [NFR-U-01]:** Strictly displays plain-language evidence summaries (completed loans, care history) rather than composite star ratings.
  5. **Newcomer Non-Penalization Notice:** Explicitly clarifies that new lenders carry the population baseline and are not risky.
  6. **Single Persistent CTA:** "Request to Borrow" opens date reservation modal.
- **Traceability:** UC-B4, FR-S-04, FR-B-04, NFR-U-01.

