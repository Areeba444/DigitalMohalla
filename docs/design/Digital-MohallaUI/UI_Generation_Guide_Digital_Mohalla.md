# Digital Mohalla — UI Generation Toolkit Guide
> Where to build, what to prompt, and how to integrate with the backend
> Prepared: 2026-10-11

---

## 1 · Tool Comparison at a Glance

| Tool | Best For | Output | Figma needed? | Code Export | Cost | My Rating |
|------|----------|--------|--------------|------------|------|-----------|
| **Google Stitch** | Fast polished mobile UI from natural language | High-fidelity UI screens | ❌ No | Android XML / Flutter / Web | Free (beta) | ⭐⭐⭐⭐ |
| **v0.dev (Vercel)** | Code-first UI; generates React + Tailwind you can actually run | Production-ready React code | ❌ No | React / Next.js | Free tier available | ⭐⭐⭐⭐⭐ **RECOMMENDED** |
| **Galileo AI** | Stunning visuals from one-line prompts | Figma frames | ❌ No (but exports to Figma) | Figma → export | Paid | ⭐⭐⭐ |
| **Anima / Locofy** | Converting wireframes/designs to code | React Native code | Needs Figma | React Native | Paid | ⭐⭐ (needs Figma) |
| **Builder.io (AI)** | Marketing/CMS pages; drag-drop | React/Vue/Angular | ❌ No | React, Vue, Angular | Free tier | ⭐⭐⭐ |
| **Me (Antigravity)** | Direct production HTML/CSS/JS or React Native screens | Runnable code files in your repo | ❌ No | Any stack | Free | ⭐⭐⭐⭐⭐ **RECOMMENDED** |

---

## 2 · My Honest Recommendation

> [!IMPORTANT]
> **Don't use one tool — use two in sequence.**
>
> **Step 1 → Google Stitch:** Generate the visual reference (high-fidelity images) per screen.  
> **Step 2 → v0.dev OR me:** Convert those visuals + your requirements into real, runnable React Native / React code that your teammates can plug into the backend.

Here's why this combo wins for your specific situation:

- Your teammates are **setting up a FastAPI + PostgreSQL backend right now** — they need components they can hook up to real API endpoints, not static screenshots.
- Google Stitch gives you supervisor-presentable **design artefacts** (exactly what Form 2 asks for).
- v0.dev / me gives you **working code** that can replace the stub UI in Slice A (D-14 deadline).
- You avoid Figma entirely. Zero drawing.

---

## 3 · Option A — Google Stitch (Visual Reference Route)

### Setup
1. Go to **labs.google/stitch** (currently in Labs, free)
2. Select "Mobile App" as the project type
3. Use **390×844 px** (standard iPhone 14 / Android size — matches your wireframe spec)

### Screen-by-Screen Prompt Templates

Use these exactly. Each prompt is engineered to enforce your HCI principles and NFR-U-01.

---

#### **Screen W1 — Lender Decision with Assurance Summary**

```
Design a mobile app screen (390×844px) for a neighborhood borrowing platform called 
"Digital Mohalla". This is the LENDER'S view when they receive a borrowing request.

Visual style: Dark mode, deep navy/slate background (#0F172A), teal accent (#14B8A6), 
clean sans-serif font (Inter), card-based layout, premium feel.

Screen layout from top to bottom:

1. TOP BAR: Back arrow, title "Borrowing Request", a small amber badge that says 
   "INSUFFICIENT EVIDENCE" (amber color, pill shape, not red)

2. REQUESTOR CARD: Profile photo (placeholder avatar), name "Ayesha K.", 
   location "F-7, Sector 4", request message "Need it for a shelf project – 3 days"
   Dates: Oct 14–16

3. ASSURANCE PANEL (most important section):
   Title: "Evidence Summary" in small caps
   - A horizontal bar labeled "Direct Reliability" showing a confidence interval 
     spanning roughly 10%–90% of the bar (wide = uncertain), with text 
     "6 verified transactions — wide confidence interval"
   - A separate row labeled "Manipulation Risk" with a LOW green pill
   - An expandable section "Why this assessment?" with 2-line explanation text

4. SAFEGUARDS SECTION: Title "Recommended Safeguards", 3 checklist items with 
   checkboxes: "Record deposit before handover", "Take item photos at handover", 
   "Set a fixed return date"

5. ACTION BUTTONS at bottom: Full-width green "Accept Request" button, 
   below it outline "Decline Request" button

IMPORTANT RULES:
- NO star ratings, NO single trust score number anywhere
- The amber badge must be clearly NOT red (never imply the borrower is risky)
- Show evidence as a range/bar, not a point score
```

---

#### **Screen W2 — Concurrency Conflict Alert**

```
Design a mobile app screen (390×844px) for "Digital Mohalla" neighborhood platform. 
Dark mode (#0F172A background, teal #14B8A6 accents).

This is the lender's CONFIRMATION screen after they decide to accept. 
The screen shows a race condition has occurred.

Layout:

1. TOP BAR: Back arrow, "Confirm Decision"

2. DECISION SUMMARY CARD: 
   - Radio option selected: "Accept Booking — Ayesha K., Oct 14–16"
   - Small note: "Accepting will auto-decline 2 other pending requests for these dates"

3. ALERT BANNER (full width, amber background):
   Warning icon + text: "Date Conflict Detected"
   Body: "Another lender accepted these dates first. This request has been 
   automatically declined with reason: dates taken."
   The banner has a subtle border-left in amber

4. RESULT STATE: The original request card now shows status "DECLINED" with 
   reason chip "Dates Taken" in grey

5. NEXT STEPS: A card saying "What happens now?" with 2 bullet points:
   - "The borrower has been notified"
   - "Your other pending requests are unaffected"

6. Single action button: "Return to Dashboard"

Style: Clean, informative, not alarming. Use amber not red for the conflict state.
```

---

#### **Screen W3a — Handover Inspection (Lender View)**

```
Design a mobile screen (390×844px) for "Digital Mohalla". Dark mode, teal accents.
This is the LENDER's handover checklist — they are handing the item to the borrower.

Layout:

1. TOP BAR: "Handover Checklist" title, status chip "ACTIVE"

2. BOOKING SUMMARY: Item name "Black & Decker Drill", Borrower "Ayesha K.", 
   Due date "Oct 16"

3. CONDITION CHECKLIST (the main content):
   Title: "Document Item Condition"
   4 checkbox rows:
   - ✅ "All parts present and accounted for"
   - ✅ "No visible damage"
   - ☐ "Accessories included (drill bits)"  
   - ☐ "Battery charged"
   Each row has a small (+) icon to add a note

4. PHOTO UPLOAD SECTION: 
   Title: "Add Handover Photos"
   A 2×2 grid of photo placeholder cards with camera icon, text "Tap to add photo"
   Below: small text "Photos create a tamper-evident record for disputes"

5. PROGRESS INDICATOR: "Step 1 of 2 — Lender submits, then borrower confirms"

6. BOTTOM BUTTON: "Submit Handover Record" (teal, full width, disabled until 
   at least 2 checkboxes checked)

Style: Task-completion feel. Progress bar at top showing step 1 of 2 active.
```

---

#### **Screen W3b — Handover Confirmation (Borrower View)**

```
Design a mobile screen (390×844px) for "Digital Mohalla". Dark mode, teal accents.
This is the BORROWER's view — they are confirming they have received the item.

Layout:

1. TOP BAR: "Confirm Receipt" — status "Awaiting Your Confirmation"

2. BANNER: Teal background, "The lender has submitted their handover record. 
   Please review and confirm."

3. LENDER'S CHECKLIST (read-only):
   Title: "Lender Reported Condition"
   Same 4 items from W3a, all showing as ticked (read-only grey style)
   Photos row: 2 photo thumbnails (placeholder images)

4. BORROWER CONFIRMATION:
   Title: "Do you confirm receiving the item in this condition?"
   Two large radio buttons:
   - "Yes, I confirm this condition"
   - "No, I dispute the condition report" (opens a note field when selected)

5. STEP INDICATOR: "Step 2 of 2 — Lender submitted ✅ · Awaiting your confirmation"

6. BOTTOM BUTTON: "Confirm Receipt" (green) + secondary "Dispute Condition" (outline red, 
   only enabled when dispute radio selected)

Style: Dual-confirm pattern, clear what the OTHER party already did.
```

---

#### **Screen W4 — Return Inspection (Side-by-Side)**

```
Design a mobile screen (390×844px) for "Digital Mohalla". Dark mode, teal accents.
This is the RETURN screen — lender compares current condition vs. handover record.

Layout:

1. TOP BAR: "Return Inspection" — status chip "RETURN INITIATED"

2. SIDE-BY-SIDE COMPARISON HEADER:
   Two columns: "AT HANDOVER" (left, grey tint) | "NOW — Returned" (right, teal tint)

3. CONDITION COMPARISON TABLE:
   Each row = one checklist item, shown in two columns
   Row 1: "All parts present" → ✅ | ✅
   Row 2: "No visible damage" → ✅ | ⚠ (yellow warning, lender can tap to note damage)
   Row 3: "Accessories" → ✅ | ✅
   Row 4: "Battery" → ✅ | ✅
   The ⚠ row has a subtle amber background

4. PHOTO COMPARISON:
   Two rows of photo thumbnails labeled "Handover Photos" and "Return Photos"
   Return photos row has 1 placeholder + 1 camera add button

5. CONDITION DELTA ALERT (if damage detected):
   Small amber card: "1 item differs from handover record. Tap to add damage notes 
   before confirming."

6. RETURN TIME:
   "Returned: Oct 16 at 2:34 PM · On time ✅" in a green chip

7. BOTTOM BUTTON: "Confirm Return & Complete" (teal) 
   Below: "Report Damage & Raise Dispute" (outline amber)

Style: Comparison-focused layout. The delta is immediately obvious.
```

---

#### **Screen W5 — Dispute Submission Form**

```
Design a mobile screen (390×844px) for "Digital Mohalla". Dark mode, teal accents.
This is the DISPUTE form — one party is raising a dispute about the transaction.

Layout:

1. TOP BAR: "Raise a Dispute" — booking reference "BK-2024-1041"

2. STATUS BANNER: Amber background, "Submitting this dispute will freeze the booking 
   and notify the other party. A moderator will review within 48 hours."

3. DISPUTE TYPE (required):
   Title: "What is this dispute about?"
   4 selection chips (multi-select): "Item Damage" | "Missing Parts" | 
   "Condition Mismatch" | "Non-Return" | "Other"

4. DESCRIPTION FIELD: 
   Multiline text input, placeholder "Describe what happened and what you expect 
   as a resolution..."
   Character counter: "0/500"

5. EVIDENCE UPLOAD:
   Title: "Add Evidence (Optional but recommended)"
   Row of + cards for photos, label "Add photos"

6. TIMELINE:
   A slim progress tracker at bottom of form:
   "You submit" → "Other party responds (48h)" → "Moderator reviews"

7. BOTTOM BUTTONS: "Submit Dispute" (amber, full width) | "Cancel" (text link)

Style: Stepped/wizard feel even though it's one screen. Non-alarming amber not red.
The word "dispute" is used, not "complaint" or "accusation".
```

---

#### **Screen W6 — Moderator Queue Dashboard**

```
Design a mobile screen (390×844px) for "Digital Mohalla". Dark mode, deep slate.
This is the COMMUNITY MODERATOR's case queue — triage view.

Layout:

1. TOP BAR: "Moderator Queue" — community name "F-7, Sector 4"

2. SUMMARY CHIPS ROW (horizontal, scrollable):
   "3 Open" (amber) | "1 Awaiting Info" (blue) | "2 Resolved This Week" (green)

3. FILTER TABS: "All Cases" | "Disputes" | "Held Requests" | "Reports"
   Active tab has teal underline

4. CASE CARDS (list, priority-sorted):
   
   CARD 1 (Priority HIGH — Dispute):
   - Left: Red-outline dispute icon
   - Trigger type pill: "DISPUTE" in red-tinted chip
   - Title: "Item Damage — Drill"
   - Parties: "Ayesha K. ↔ Sara M."
   - Age: "Waiting 2 days"
   - Evidence preview: "3 photos · 2 messages"
   - Right arrow →

   CARD 2 (Priority MEDIUM — Hold):
   - Left: Orange hold icon
   - Trigger type pill: "MANIPULATION HOLD" in amber chip
   - Title: "Request Flagged — Rating Anomaly"
   - Parties: "Ahmad R. borrowing from Nadia K."
   - Age: "Waiting 6 hours"
   - Evidence preview: "Reciprocal clustering detected"
   - Right arrow →

   CARD 3 (Resolved):
   - Greyed out, "RESOLVED" chip
   - Title: "Boundary Condition — Membership"

5. EMPTY STATE (shown when queue is clear): 
   Checkmark illustration, "No cases pending. Community is all clear."

Style: Triage-first. High priority cards have stronger visual weight (border-left accent).
DO NOT show any user's full name or exact address.
```

---

#### **Screen W7 — Moderator Case Adjudication**

```
Design a mobile screen (390×844px) for "Digital Mohalla". Dark mode, teal/slate.
This is the MODERATOR's full case detail and decision screen.

Layout:

1. TOP BAR: Back arrow, "Case #DM-2024-047" — priority badge "HIGH"

2. CASE HEADER CARD:
   Trigger: "DISPUTE — Item Damage"
   Parties: Lender "Sara M." vs Borrower "Ayesha K."
   Item: "Black & Decker Drill, Oct 14–16"
   Opened: "2 days ago by Lender"

3. EVIDENCE TIMELINE (scrollable):
   Vertical timeline with events:
   ◉ Oct 14 — "Handover submitted by Sara M. · 4 photos · condition: Good"
   ◉ Oct 16 — "Return submitted by Ayesha K. · 2 photos"
   ◉ Oct 16 — "Dispute raised by Sara M. · reason: damage"
   ◉ Oct 17 — "Response submitted by Ayesha K. · counter-evidence"
   Each event is expandable (tap to see photos/details)

4. ASSURANCE CONTEXT (collapsed by default, expand to show):
   "Trust Context" section:
   - Ayesha's assurance profile: "4 verified transactions, 1 dispute"
   - Manipulation risk: LOW
   - Note: "Evidence is advisory. Only you can restrict access."

5. DECISION FORM:
   Title: "Your Decision (required)"
   Radio options:
   - "Resolve: Borrower responsible — damage confirmed"
   - "Resolve: Lender responsible — no damage found"  
   - "Request more information" (opens deadline picker)
   - "Escalate to Admin"
   
   Mandatory reason text field: "Reason for decision (required)"
   Character counter

6. AUDIT NOTE: Small grey text: "Your decision will be permanently recorded 
   in the audit log and cannot be silently altered."

7. BOTTOM BUTTONS: "Submit Decision" (teal, full width, disabled until reason filled)
   Secondary: "Cancel & Return to Queue"

Style: Evidence-first layout. Decision form is at the BOTTOM — moderator reads 
evidence before acting. Audit warning is visible but not alarming.
```

---

## 4 · Option B — v0.dev (Code-First Route) ⭐ Strongly Recommended

**URL:** https://v0.dev  
**Output:** Real React + Tailwind components you copy into your frontend  

### Why this wins for your situation
- Your teammates will have a **React Native / Next.js frontend** (most likely, since NFR-D-05 mentions React Native/Expo)
- v0.dev generates actual code — paste it into your repo and it works
- You can iterate: "make the assurance panel collapsible" → it updates the code
- Each screen becomes a real component your backend can wire up to API data

### v0.dev Prompt Strategy

Prefix every prompt with this **system context block** (paste once, then give the screen prompt):

```
Context for all screens:
- App: "Digital Mohalla" — a neighborhood borrowing & lending platform for Pakistani communities
- Stack: React (TypeScript), Tailwind CSS, mobile-first (390px width)
- Design: Dark mode, navy background (#0F172A), teal accent (#14B8A6), 
  Inter font, card-based layout
- Critical rule: NEVER show a single trust score number. Always show evidence 
  as ranges/components (direct reliability bar, manipulation risk as LOW/MED/HIGH label)
- Assurance states: SUFFICIENT_EVIDENCE (green), REVIEW_RECOMMENDED (amber), 
  INSUFFICIENT_EVIDENCE (blue-grey), ACTIVE_DISPUTE (red)
- Newcomers in INSUFFICIENT_EVIDENCE state must NEVER see red — use blue-grey
- All buttons that would trigger invalid state transitions must be hidden, not disabled
```

Then add each screen prompt from Section 3 above, reworded as "Build a React component for..."

---

## 5 · Option C — Let Me (Antigravity) Build It Directly

**This is your fastest path to code that works.**

I can generate all 8 screens as:
- **React Native (Expo)** components → drops into your mobile app
- **Next.js pages** → if you're going web-first
- **Plain HTML/CSS** → for demo purposes or if stack is undecided

**What you'd get:** Real, runnable code files committed directly to your repo paths, with proper component structure, TypeScript types for your data models (AssessmentResult, BorrowingRequest, ModeratorCase), and placeholder API hooks your teammates can swap for real FastAPI calls.

**What I need from you:**
1. Confirm the frontend framework (React Native/Expo vs Next.js vs plain web)
2. Confirm dark mode or light mode preference
3. Tell me screen priority order (I suggest: W1 → W6/W7 → W3a/b → W4 → W5 → W2)

---

## 6 · Option D — Hybrid Workflow (What I Actually Recommend for Your Deadline)

```
Week 1 (Now — D-15 Design Gate)
│
├─ YOU: Use Google Stitch with the prompts above → get 8 screen images
│        → Submit as design artefacts to supervisor (Form 2 requirement)
│
├─ ME: Simultaneously generate the actual React Native code for the same screens
│      → Commit to frontend/ folder in your repo
│
└─ Result: Design artefacts ✅ + Working code ✅ in parallel, not sequential

Week 2 (D-15 to D-11, Slice A Build)
│
├─ YOUR TEAMMATES: Backend API endpoints for lifecycle transitions
│
└─ YOU: Wire the screens I generated to the real API endpoints
         (replace placeholder data with fetch() calls to your FastAPI)
```

---

## 7 · Screen Priority Order for FYP Mid-Eval Demo

Build in this order — it matches the demo script in your Iteration 1 plan:

| Priority | Screen | Why |
|----------|--------|-----|
| 1st | **W1** — Lender assurance view | The core CCP demo: shows INSUFFICIENT_EVIDENCE state |
| 2nd | **W6 + W7** — Moderator queue + adjudication | Dispute resolution is the second demo story beat |
| 3rd | **W3a + W3b** — Handover (lender + borrower) | Dual-confirm handover is required for the live demo |
| 4th | **W4** — Return inspection | Completes the transaction loop |
| 5th | **W5** — Dispute form | Needed for the "damaged return → dispute" demo beat |
| 6th | **W2** — Concurrency conflict | Engineering edge case — needed for Slice A gate |

---

## 8 · How the UI Connects to Your Backend

When your teammates finish the FastAPI setup, here's the exact wiring map:

| Screen | API endpoint | Payload type |
|--------|-------------|-------------|
| W1 (Lender assurance) | `GET /transactions/{id}/assessment` | `AssessmentResult` |
| W2 (Accept/Decline) | `POST /transactions/{id}/transition` | `{event_type: "request_accepted"}` |
| W3a (Lender handover) | `POST /transactions/{id}/handover/lender` | `{checklist, photo_refs}` |
| W3b (Borrower confirm) | `POST /transactions/{id}/handover/borrower` | `{confirmation: true/false}` |
| W4 (Return inspection) | `POST /transactions/{id}/return/lender` | `{checklist_delta, photo_refs}` |
| W5 (Dispute form) | `POST /transactions/{id}/dispute` | `{reason, evidence_refs}` |
| W6 (Mod queue) | `GET /moderator/cases?community_id=X` | `ModeratorCase[]` |
| W7 (Mod decision) | `POST /cases/{id}/decision` | `{decision, reason}` |

Every endpoint maps directly to a use case step and a state machine transition — zero mismatch with what your teammates are building.

---

## 9 · Quick Decision Checklist

- [ ] **Frontend stack decided?** → React Native/Expo or Next.js? (Ask teammates now — unblocks everything)
- [ ] **Dark mode confirmed?** → Yes/No (the prompts above assume dark mode)
- [ ] **English only for Iter 1?** → NFR-U-05 says TBD; confirm with Dr. Ali
- [ ] **Which tool first?** → Google Stitch for visuals, me for code, or both in parallel?

---

*Ready to generate. Just tell me the stack and which screen to start with.*
