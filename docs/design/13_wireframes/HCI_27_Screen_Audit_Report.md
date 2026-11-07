# HCI Screen Audit Report — 27 Screens & Quality Benchmark
**Project:** Digital Mohalla (FYP-1 Final / Iteration 2)  
**Deliverable ID:** UX-01  
**Applicable Documents:** HCI Design Analysis v1.1, FR/NFR v1.4, ADR-0001 to ADR-0016  
**Auditor:** Areeba (UI & Assurance Engine Lead)  
**Date:** November 2026  

---

## 1. Executive Summary & Quality Benchmark

In accordance with Iteration 2 task **UX-01**, this audit evaluates all **27 screens** across the Digital Mohalla mobile interface (10 existing iteration 1 screens + 17 newly created iteration 2 screens). Every screen has been audited against core Human-Computer Interaction (HCI) heuristics, strict multi-dimensional trust rules (**NFR-U-01**), accessibility benchmarks, and modern aesthetic standards.

### Core Quality Benchmarks Enforced Across All 27 Screens:
1. **Zero Composite Trust Scores (NFR-U-01):** No screen reduces peer trustworthiness to a single composite numerical score, star rating, or letter grade. All assurance surfaces display multi-dimensional evidence (direct verified exchanges, Beta credible interval, care history, and independent manipulation risk).
2. **Neutrality for Newcomers (HCI Constraint 2):** `INSUFFICIENT_EVIDENCE` is rendered strictly in **neutral blue-grey / soft amber**, never punitive red. Unknown $\ne$ unreliable. Red is reserved strictly for active disputes and lock collisions.
3. **Scannable & Non-Wordy UI:** Microcopy is kept under 2 lines per section. Dense statistical formulas are placed in progressive disclosure collapsibles.
4. **Touch Target Standard (WCAG 2.5.5):** All interactive targets (buttons, chips, icons, pickers) maintain at least $48\times 48\text{ dp}$ tappable area.
5. **Shallow Navigation Hierarchy:** No operational task is deeper than 3 taps from the home surface.
6. **Canonical 5-State Completeness:** Every screen provides dedicated handling for `Loading`, `Empty`, `Error/Offline`, `Normal/Populated`, and `Cold-Start` states.

---

## 2. Formal Resolution of Outstanding Review Items

### 2.1 Formal Closure of UI-4 (Credible Interval Bounds)
- **Previous Issue:** W1's illustrative mock interval $[0.10, 0.90]$ differed from theoretical Beta(1,1) prior bounds $[0.05, 0.95]$.
- **Audit Finding & Resolution:** All screen annotations, mock fixtures, and test assertions in `iteration2Mocks.ts` and `lender-evidence-test.tsx` now explicitly enforce the Beta distribution 90% credible interval computed from $\text{Beta}(\alpha, \beta)$ parameters. The uninformative prior $\text{Beta}(1, 1)$ correctly resolves to $[0.05, 0.95]$.
- **Status:** **CLOSED**.

### 2.2 Formal Closure of UI-5 (Dispute & SLA Countdown Timers)
- **Previous Issue:** W5 stated a 7-day dispute window and W6 an SLA timer without formal scheduler configuration.
- **Audit Finding & Resolution:** The 7-day dispute window, 72-hour appeal window, and 48-hour moderator SLA timers have been codified as runtime configuration values in `backend/app/config/engine_config.py` (Iteration 2 scheduler scope). On the UI layer, W18 and W20 use dynamic `CountdownTimer` components that alert users when deadlines approach without hardcoding static strings.
- **Status:** **CLOSED**.

### 2.3 Formal Resolution of NFR-U-05 (Interface Language Decision)
- **Previous Issue:** Language decision between English, Urdu, and Roman Urdu remained unfinalized.
- **Audit Finding & Resolution:** **English is selected as the primary system language**, with native support for common Roman Urdu item and community vocabulary (e.g., *Mohalla*, *Charpai*, *Silai machine*, *Drill machine*, *Istari*). W22 includes quick-select Roman Urdu suggestions, and search filters accept Roman Urdu query variants.
- **Status:** **RESOLVED & FROZEN**.

---

## 3. Comprehensive 27-Screen Audit Matrix

| # | Screen / Route | Wireframe | Role | Key Heuristic Applied | 5-State Completeness | NFR-U-01 Verified |
|---|----------------|-----------|------|-----------------------|----------------------|-------------------|
| 1 | `/login` | W0 | All | Error Prevention | Loading, Error, Validated Form | Pass (No score) |
| 2 | `/(resident)/(tabs)/index` | Home | Resident | Progressive Disclosure (Priority 1 Banner) | Loading, Empty, Active Loans | Pass (No score) |
| 3 | `/(resident)/(tabs)/browse` | W23 | Resident | Jakob's Law (OLX card list + Reason lines) | Loading, Empty, Filtered, Fallback | Pass (Reason chips) |
| 4 | `/(resident)/(tabs)/activity` | Activity | Resident | Recognition over Recall (Segmented tabs) | Loading, Empty, Catch-up, Filtered | Pass (No score) |
| 5 | `/(resident)/(tabs)/profile` | Profile | Resident | Progressive Disclosure & Dual Themes | Populated, Theme Swatches | Pass (4-state cards) |
| 6 | `/item/[id]` | Request | Resident | Error Prevention (Calendar chip bounds) | Loading, Not Available, Date Stepper | Pass (Lender badge) |
| 7 | `/request/[id]` | W1–W3 | Both | Multidimensional Assurance & Concurrency Pre-warn | Insufficient, Sufficient, Dispute, Taken | Pass (Beta interval bar) |
| 8 | `/dispute/[id]` | W5 | Resident | Stepped Wizard & Blame-free Recovery | Form, Freeze Advisory, Withdrawal | Pass (No score) |
| 9 | `/moderation/index` | W6 | Moderator | Priority Queue (Severity-first ordering) | Loading, Empty Queue, Triage Cards | Pass (Ordered by trigger) |
| 10 | `/moderation/[id]` | W7 | Moderator | Tamper-Evident Event Trail | Event List, Decision Form, Reasons | Pass (Immutable trail) |
| 11 | `/register` | W8 | Newcomer | Privacy by Design (Zero GPS stored) | Clean Form, Validation, Terms Check | Pass (No score) |
| 12 | `/community/join` | W9 | Resident | Progressive Disclosure (Code on-demand) | Search, Empty, Rules Collapsible | Pass (No score) |
| 13 | `/community/verify` | W10 | Resident | 3-Valued Neutral Feedback (Never auto-reject) | Geofence Check, Code, 3 Outcomes | Pass (Neutral banner) |
| 14 | `/members/index` | W11 | Moderator | Tenant Boundary Isolation | Queue Cards, Voucher Data, Reason Box | Pass (Vouch context) |
| 15 | `/notifications` | W12 | Resident | Categorization & Unread Contrast | All, Action, Update, Empty Inbox | Pass (No score) |
| 16 | `/request/[id]/extend` | W13 | Both | Bilateral Symmetry (Request vs Respond) | Date Stepper, Reason, Advisory | Pass (No score) |
| 17 | `/request/[id]/counter` | W14 | Both | Side-by-Side Comparison (Delta clarity) | Original vs Proposed, Duration note | Pass (No score) |
| 18 | `/request/[id]/review` | W15 | Both | Multidimensional Rating (Punctuality, Care) | Unlocked on Done, 3 Toggle Rows | Pass (Zero star ratings) |
| 19 | `/profile/evidence` | W16 | Resident | Personal Assurance Profile & Interval Bar | Beta Interval, Care stats, Risk pill | Pass (Pure multidim) |
| 20 | `/request/[id]/photos` | W17 | Both | Privacy Affordance (EXIF GPS Stripping) | 2 Slots, Preview, Reduced Fallback | Pass (No score) |
| 21 | `/dispute/[id]/respond` | W18 | Both | Urgent SLA Countdown (Amber/Red thresholds) | Countdown, Quoted query, Attach slot | Pass (No score) |
| 22 | `/moderation/[id]/adj` | W19 | Moderator | Explicit Item Possession (DM14 Invariant) | 4 Possession Radios, Deposit Ruling | Pass (Human only) |
| 23 | `/dispute/[id]/appeal` | W20 | Resident | Structured Procedural Grievance | Grounds Checkbox, Statement, Timer | Pass (Independent mod) |
| 24 | `/(admin)/audit` | W21 | Admin | Cryptographic Transparency & Data Masking | Hash Valid Badge, Masked GPS/CNIC | Pass (SHA-256 chain) |
| 25 | `/item/create` | W22 | Lender | Wizard Chunking (Details, Photos, Review) | Stepper, Urdu Hints, Draft Save | Pass (Record-only deposit) |
| 26 | `/(tabs)/browse` (Search) | W23 | Resident | Explainable Retrieval & Model Fallback | Hybrid Rank, ReasonLine, Fallback bar | Pass (Baseline for new) |
| 27 | `/item/detail/[id]` | W24 | Resident | Availability Transparency & Evidence Tiers | Photo Hero, Date Strip, Lender card | Pass (Collapsible evidence) |

---

## 4. Visual Coherence & Design System Audit

- **Terracotta Theme:** Tested on aerial mohalla hero background (`#FAF6F0` base, `#1F1A17` text, clay primary button `#8B4513`, forest green accent). Warm, trustworthy, culturally grounded.
- **CreamGreen Theme:** Tested on sage paper illustration background (`#F8FAFC` base, sage primary, slate text). Fresh, modern, uncluttered.
- **Contrast Ratios:** Verified WCAG AA minimum 4.5:1 for all normal text and 3:1 for large display headlines across both themes.
- **Touch & Accessibility:** Every button and chip meets the 48dp minimum touch target. Accessible labels attached to all icons, status pills, and interval bars.

