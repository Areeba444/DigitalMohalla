# HCI Design Analysis — Digital Mohalla, Iteration 1
> Role: Expert HCI Researcher & Principal Product Designer  
> Scope: Borrowing lifecycle + Assurance Engine screens (A12 wireframe set)  
> Prepared: 2026-10-11

---

## 0 · Ground-Truth Extraction

### Problem
Neighbours in Pakistani localities cannot reliably trust strangers for physical item exchanges because evidence is **sparse, role-dependent, and possibly manipulated**. Existing infrastructure (WhatsApp groups, OLX) provides no structured trust signal. The specific computational challenge is: given limited verified history, produce an *explained assurance state* — not a single number — that guides a lender's decision while protecting location privacy and escalating uncertain cases to a human moderator.

### Core Users (Iteration 1)
| Role | Mental Model & Goal | Pain Points |
|------|-------------------|-------------|
| **Borrower** | Wants an item temporarily; unfamiliar with their own "evidence weight" | Doesn't understand why a request stalls; fears silent rejection |
| **Lender** | Has an item; needs enough confidence to hand it to a near-stranger | Overwhelmed by unfamiliar-person risk; no clear decision signal |
| **Community Moderator** | Manages disputes and held requests; acts as the safety backstop | Buried in context-switching; needs a triage-first layout |
| **New Resident (Newcomer)** | Zero history; framed by the system as INSUFFICIENT_EVIDENCE | Anxious about first interaction; fairness-sensitive |

### Stakeholders
- Dr. Ali Zeeshan (supervisor / evaluator) — needs live, explainable demo
- FYP panel — checking for genuine complexity, not CRUD screens
- Pilot participants (30–50 residents of F-7, Islamabad) — SUS score target
- Future iterations will add vendors and event organisers

### Purpose (Iteration 1)
Build the **request-to-return loop with assurance**: request → locality check → assessment → lender accept/decline → handover checklist → return checklist → (dispute path) → moderator resolution. Every assurance screen must surface **evidence components**, never a single trust number (NFR-U-01).

---

## 1 · Three Core HCI Principles (Ranked by Impact for This Audience)

### Principle 1 — **Progressive Disclosure** (Miller 1956 / Shneiderman's 8 Golden Rules)
> *Show only what is needed at each decision point; reveal complexity on demand.*

**Why it dominates here:**  
The assurance output object contains nine fields: assurance state, confidence, direct evidence, indirect evidence, manipulation-risk signals, safeguards, explanation, credible interval, and config version. Dumping all of this on a lender violates cognitive load limits for a semi-literate mobile audience in Islamabad. But hiding it entirely violates NFR-U-01 (evidence must be visible) and user fairness expectations.

**Design consequence:**
- **Layer 1 (always visible):** Assurance state badge + one-sentence plain-language explanation + recommended safeguard callout.
- **Layer 2 (tap to expand):** Direct vs. indirect evidence breakdown, credible interval visualised as a bar, manipulation signal count.
- **Layer 3 (moderator/power user only):** Raw signal values, config version, evidence trail, audit log link.

**Specific Iteration 1 screens impacted:** W1 (lender decision), W7 (moderator case view).

---

### Principle 2 — **Error Prevention + Meaningful Recovery** (Nielsen's Heuristic #5 + #9)
> *Make invalid paths impossible, then make recovery paths clear and blame-free.*

**Why it is critical here:**  
The system has a 14-state machine with strict invalid-transition rejection (NFR-R-02). Users who trigger an invalid transition will receive an error. In addition, the system's design philosophy is *"unknown ≠ unreliable"* — a newcomer in INSUFFICIENT_EVIDENCE must not feel accused, and a borrower in HELD_FOR_REVIEW must understand why and what happens next.

The borrower audience is Pakistani neighbourhood residents — not tech-savvy, potentially using mid-range Android, possibly Urdu-speaking. Error messages must be warm, non-technical, and action-oriented (NFR-U-05 flags the language decision as open).

**Design consequence:**
- State-aware UI: buttons that would trigger invalid transitions are **absent** (not greyed — absent), removing temptation entirely.
- Every HELD_FOR_REVIEW screen includes: *why* it is held (hold reason in plain language), *who* will act next (the moderator), and *expected timeline*.
- INSUFFICIENT_EVIDENCE badge reads "Lender decides — not enough history yet" rather than "Untrusted borrower."
- Dispute form (W5) uses a stepped wizard to prevent incomplete submissions (disputed outcome needs evidence, reason, and a response window timer).

**Specific Iteration 1 screens impacted:** W1, W5, W6, W7, plus all transition-triggered notifications.

---

### Principle 3 — **Jakob's Law + Recognition over Recall** (Nielsen 2000)
> *Users spend most of their time on other apps — design to match familiar interaction patterns.*

**Why it applies here:**  
The primary analogy for Pakistani mobile users is WhatsApp (messaging-first, bottom-nav, card lists), OLX (listing cards, photo-first), and easypaisa/JazzCash (step-confirm flows, receipt screens). The platform must piggyback on these mental models to reduce training time (NFR-U-02 measures first-attempt task completion).

Moderators are quasi-professional; their closest comparable tool is a ticketing interface (like Freshdesk or even a WhatsApp Business inbox). They context-switch between multiple cases and need scannable queues.

**Design consequence:**
- **Bottom navigation** with 5 tabs matching the POC-Lite: Home, Search, Communities, Messages, Profile.
- **Card-based listing** with photo left, key details right — matches OLX.
- Handover/return checklists (W3a, W3b, W4) use a WhatsApp-like dual-confirm pattern (lender submits → borrower confirms) with status bubbles, mirroring message read-receipts.
- Moderator queue (W6) uses a Kanban-lite: Pending → Awaiting Info → Decided, scannable without needing to open cases.
- No novel gestures; long-press, swipe-to-delete, and pull-to-refresh are the only non-tap interactions.

---

## 2 · UI Layout Strategy

### 2.1 Information Architecture (IA)

```
Digital Mohalla App
├── Home (Dashboard)
│   ├── Active transaction status cards (if any)
│   ├── Pending action items (accept, confirm handover, etc.)
│   ├── Neighbourhood feed (seeded for Iter 1)
│   └── Quick actions: Browse Items | Post Item | Request Help
├── Search / Browse
│   ├── Keyword + filter bar
│   ├── Item cards (photo, title, lender badge, availability)
│   └── [Seeded/stub in Iter 1]
├── Communities
│   └── [Seeded/stub in Iter 1]
├── Messages / Notifications
│   ├── Transaction threads (linked to booking)
│   └── System alerts (state changes, moderator decisions)
└── Profile
    ├── Evidence Summary (assurance factors, NOT a single score)
    ├── My Transactions (timeline view)
    └── Settings

Moderator Overlay (role-gated, same app)
├── Case Queue (W6) — triage-first layout
└── Case Detail (W7) — evidence trail + decision form
```

**Rationale:** Flat, 3-tap-maximum depth. The borrowing lifecycle is accessed from Home (active transaction) or from a listing detail. Moderator functions live as a role-gated section, not a separate app, so moderators can quickly switch between their member view and their mod queue.

---

### 2.2 Navigation Pattern

**Pattern: Bottom Navigation + Contextual Floating Action Button (FAB)**

| Tab | Icon | Badge |
|-----|------|-------|
| Home | house | unread actions count |
| Browse | search | — |
| + (FAB, centre) | plus | — |
| Inbox | chat bubble | unread messages |
| Profile | avatar | — |

- The centre **FAB** (`+`) is the primary affordance: triggers "Post an Item" or "Request an Item" — the two actions that begin a lifecycle. This is the dominant entry point.
- Transaction-specific actions (Accept, Handover Confirm, Raise Dispute) live **inline within transaction cards** — no hunting in menus.
- Moderator queue is accessed via Profile → "Moderator View" (role check), opening a full-screen sheet, not a new tab.

**Navigation depth contract:** No screen deeper than 3 taps from Home. The borrower's critical path is: Home → Active Transaction Card → Confirm Handover = 2 taps.

---

### 2.3 Information Density Level

**Level: Medium-low density, mobile-first**

The target device is a mid-range Android (likely 5.5–6.2" screen, ~360dp width). The audience includes semi-literate users and older residents.

| Design Token | Value |
|---|---|
| Base font size | 16sp body, 14sp secondary |
| Touch target minimum | 48dp × 48dp (WCAG 2.5.5) |
| Card height (list items) | ≥ 72dp |
| Line length | ≤ 65 chars per line |
| Primary colour action | Single, persistent CTA per screen |
| Evidence panels | Expandable (collapsed by default, visible summary) |

**Density exception — Moderator Case View (W7):** Moderators are trained and time-pressured. This single screen can be ~medium-high density: two-column evidence trail on tablet, dense table on mobile with horizontal scroll.

---

## 3 · Component Breakdown — Primary Dashboard View (Home)

The Home screen is the most important surface. It serves all four roles with the same shell but dynamically composed content. Below is the component breakdown:

```
┌─────────────────────────────────────────┐
│  HEADER BAR                             │
│  [Community name + radius selector]     │
│  [Bell icon + avatar]                   │
├─────────────────────────────────────────┤
│  ACTIVE TRANSACTION BANNER              │  ← Priority #1: If a transaction
│  "You have a pending action"            │    needs the user's input, it
│  [Confirm Handover] [View Details]      │    occupies the top slot.
│  State pill: ACTIVE · Due in 2 days     │
├─────────────────────────────────────────┤
│  SECTION: "For You"                     │
│  ┌──────────────────────────────────┐   │
│  │ ASSURANCE NUDGE CARD             │   │  ← Contextual. If a request is
│  │ "Your borrowing request for      │   │    ASSESSED, shows the state and
│  │  Power Drill is being reviewed"  │   │    a plain-language explanation.
│  │ State: INSUFFICIENT_EVIDENCE     │   │    Never shows a single number.
│  │ "Lender will decide — not        │   │
│  │  enough history yet. Your        │   │
│  │  request is safe and pending."   │   │
│  │ [View Full Evidence] →           │   │
│  └──────────────────────────────────┘   │
├─────────────────────────────────────────┤
│  SECTION: "Nearby Items"                │
│  [Horizontal scroll, item cards]        │  ← OLX-style cards: photo, title,
│  [Card] [Card] [Card] → See All         │    approximate distance, lender
│                                         │    assurance badge (not score).
├─────────────────────────────────────────┤
│  SECTION: "Neighbour Requests"          │
│  "Sara K. needs a pressure cooker"      │  ← Demand-side: "I Have This"
│  [I Have This] button                   │    response entry point.
├─────────────────────────────────────────┤
│  SECTION: "Community"  (seeded Iter 1)  │
│  [Event chips / Group cards, horizontal]│
├─────────────────────────────────────────┤
│  BOTTOM NAV: Home | Browse | + | Msgs | Profile │
└─────────────────────────────────────────┘
```

### Component Inventory

| # | Component | Purpose | HCI Principle |
|---|-----------|---------|--------------|
| C1 | **Active Transaction Banner** | Surfaces the single most urgent action. One CTA. Disappears when no pending action. | Error prevention: keeps user on track |
| C2 | **Assurance Nudge Card** | Shows the assurance state in plain language. No score. Expandable to full evidence. | Progressive Disclosure + NFR-U-01 |
| C3 | **State Pill** | Colour-coded lifecycle state (ASSESSED=amber, ACTIVE=green, DISPUTED=red, HELD=orange). Text + colour — never colour alone. | Accessibility + Recognition |
| C4 | **Evidence Expand Panel** | Collapsed by default. Opens to show direct evidence bar, indirect paths count, manipulation risk level, safeguards, and credible interval. | Progressive Disclosure (Layer 2) |
| C5 | **Item Card (Nearby)** | Photo-left, details-right. Distance, availability badge, lender's assurance tier (not score). Max 3 lines of text. | Jakob's Law (OLX pattern) |
| C6 | **Lender Assurance Badge** | Small visual on item cards: "Verified · 12 transactions" or "New Lender." Never a number. | NFR-U-01 compliance |
| C7 | **Neighbour Request Row** | Name (first name + initial), item, distance, "I Have This" CTA. | Recognition + social trigger |
| C8 | **FAB (Centre)** | Persistent +. On tap: bottom sheet with "Post Item" or "Request Item." | Fitts's Law: large, centred, always reachable |
| C9 | **Bottom Nav** | 5-tab persistent nav. Active tab highlighted. Badges for pending actions. | Jakob's Law + Recognition |
| C10 | **Section Header** | Label + optional "See All" link. Keeps IA scannable. | Visual hierarchy |

---

### Assurance Card — Detailed States

The Assurance Nudge Card (C2) must render correctly across all 4 assurance states:

| State | Colour | Headline | Sub-text tone |
|-------|--------|----------|---------------|
| SUFFICIENT_EVIDENCE | Green | "Evidence looks good" | "The lender can see your verified history." |
| REVIEW_RECOMMENDED | Amber | "Lender will review" | "Some factors need a closer look. This is normal." |
| INSUFFICIENT_EVIDENCE | Blue-grey | "Not enough history yet" | "Your request is safe and pending. Lender decides." |
| ACTIVE_DISPUTE | Red | "A dispute is open" | "A moderator will review. No further actions until resolved." |

> [!IMPORTANT]
> The INSUFFICIENT_EVIDENCE card must never use red or warning iconography. The requirement ("Unknown ≠ unreliable") demands neutral, trust-preserving framing. Blue-grey is intentional.

---

### Moderator Dashboard — Component Breakdown (W6/W7)

```
┌─────────────────────────────────────────┐
│  MOD HEADER: "Moderator Queue"          │
│  [My Community: F-7 Sector 4] ▼         │
│  Summary chips: 3 Disputes · 1 Hold     │
├─────────────────────────────────────────┤
│  FILTER TABS: All | Disputes | Holds    │
├─────────────────────────────────────────┤
│  CASE CARD (priority-ranked)            │
│  [Trigger type pill: DISPUTE]           │
│  Borrower: Ahmad K. ↔ Lender: Sara M.  │
│  Item: Electric Drill · Since: 2d ago   │
│  Evidence: 3 photos, 2 messages         │
│  [Open Case →]                          │
├─────────────────────────────────────────┤
│  ... more cases ...                     │
└─────────────────────────────────────────┘
```

| # | Component | Purpose |
|---|-----------|---------|
| M1 | **Priority Case Queue** | Sorted by trigger type (immediate-safety first), then age. Never alphabetical. |
| M2 | **Trigger Type Pill** | DISPUTE / MANIPULATION_HOLD / ENGINE_FAILURE / LOCALITY_HOLD — scannable at a glance. |
| M3 | **Evidence Count Badge** | "#photos · #messages · #prior outcomes" — tells moderator what they're walking into before tapping. |
| M4 | **Case Detail: Evidence Trail** | Timeline of events from the frozen event log. Tamper-evident (FR-M-05). Expandable per event. |
| M5 | **Decision Form** | Mandatory reason field + action buttons (Resolve / Request More Info / Escalate to Admin). Blocks submit without reason. |
| M6 | **Audit Trail Footer** | Shows which previous moderator actions exist on this case. Prevents double-handling. |

---

## 4 · Key Design Constraints to Carry Into UI Generation

1. **Never a single trust number** (NFR-U-01) — this is a hard design rule, not a preference.
2. **No red for newcomers** — INSUFFICIENT_EVIDENCE is not a negative verdict.
3. **State-aware button rendering** — buttons for invalid transitions must not appear (not just be disabled).
4. **Evidence must be legible, not dense** — evidence panels use plain-language labels, not algorithm names.
5. **Dual-confirm pattern for handover/return** — both parties must explicitly confirm; no unilateral state change.
6. **Language** — English first (Urdu/Roman Urdu TBD), but layout must support RTL-ready spacing if Urdu is added.
7. **Mobile-first, 360dp baseline** — no desktop-first thinking; moderator view scales up to tablet.
8. **Approximate location only** — no map pins showing exact addresses anywhere (NFR-PR-01).

---

*This analysis is the HCI foundation for generating high-fidelity UI screens in subsequent steps. All recommendations trace directly to ground-truth requirements.*
