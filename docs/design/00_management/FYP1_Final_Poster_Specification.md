# FYP-1 Final Poster Specification & Layout Blueprint
**Project:** Digital Mohalla: Multi-Dimensional Assurance & Peer Lending  
**Deliverable ID:** UX-06 (Week 13 Milestone, 10 Marks)  
**Lead Author:** Areeba (UI & Assurance Engine Lead)  
**Collaborators:** Fatima, Minahil  
**Supervisor:** Dr. Ali Zeeshan  
**Date:** November 2026  

---

## 1. Physical & Print Specifications

- **Dimensions:** 22.5 inches (width) × 34.5 inches (height) — **Portrait orientation**.
- **Viewing Distance:** Optimized for readability from 1 to 1.5 meters away.
- **Color Profile:** CMYK for print; RGB digital export.
- **Palette Hierarchy:**
  - Background: Off-white / Cream `#FAF6F0` (Terracotta theme background).
  - Primary Accent: Terracotta Clay `#8B4513` and Slate `#1F1A17`.
  - Secondary Accent: Sage / Forest Green `#2E7D32` and Teal `#14B8A6`.
  - Assurance Neutral Tone: Blue-grey `#64748B` (strict adherence to NFR-U-01: neutral, never red for newcomers).
- **Typography:**
  - Display Headers: *Fraunces* (72pt–96pt bold).
  - Section Headings: *Plus Jakarta Sans* Bold (36pt–48pt).
  - Body & Annotations: *Plus Jakarta Sans* Medium (20pt–24pt).
- **Deliverable Formats:** Original layered vector/design asset (Photoshop / Illustrator / Corel) + 300 DPI high-resolution PDF/JPEG.

---

## 2. Poster Grid & Layout Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│ [TOP LEFT]                                              [TOP RIGHT]    │
│ Project Title & Subtitle                                Problem & Goals │
│ "Digital Mohalla: Decentralized Trust & Peer Lending"   Urban Pakistan  │
│ Team: Areeba, Fatima, Minahil                           Sparse history  │
│ Supervisor: Dr. Ali Zeeshan                             NFR-U-01 rule   │
├────────────────────────────────────────────────────────────────────────┤
│ [CENTER SECTION — 50% VERTICAL HEIGHT]                                 │
│                                                                        │
│ ┌──────────────────────────────┐    ┌────────────────────────────────┐ │
│ │ Assurance Engine Arch Diagram│    │ High-Fidelity UI Showcase      │ │
│ │ • Direct Beta Posterior      │    │ • W1 Lender Evidence Panel     │ │
│ │ • Indirect Graph Discounting │    │ • W16 My Evidence Profile      │ │
│ │ • Multi-Signal Anti-Ring     │    │ • W10 3-Valued Locality Check  │ │
│ └──────────────────────────────┘    └────────────────────────────────┘ │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│ [BOTTOM SECTION — 30% VERTICAL HEIGHT]                                 │
│                                                                        │
│ ┌──────────────────────────────┐    ┌────────────────────────────────┐ │
│ │ Iteration 2 Scope (67%)      │    │ Testing & Baseline Results     │ │
│ │ • 40 of 60 FRs Verified      │    │ • 46/46 Frontend Tests Green   │ │
│ │ • Locality, Search & Disputes│    │ • Zero Single Trust Numbers    │ │
│ │ • DM14 & DM09 Closed         │    │ • Latency P95 <= 500ms         │ │
│ └──────────────────────────────┘    └────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Section Content Blueprint

### 3.1 Header (Top Left)
- **Title:** Digital Mohalla: Multi-Dimensional Assurance & Safe Peer Item Sharing for Urban Pakistan
- **Team Members:**
  - Areeba (UI, Assurance Engine Lead & Evaluation)
  - Fatima (Backend, Locality & Lifecycle Lead)
  - Minahil (Moderation, Testing & Handover Lead)
- **Supervisor:** Dr. Ali Zeeshan

### 3.2 Context & Goals (Top Right)
- **The Problem:** In Pakistani urban neighborhoods, mutual item borrowing (tools, medical gear, appliances) is paralyzed by lack of trusted infrastructure. WhatsApp groups and classifieds lack verifiable accountability.
- **The Core Computational Challenge:** Computing an explainable, manipulation-resistant assurance state from sparse, cold-start transaction graphs without storing user GPS coordinates or reducing humans to a single credit-score number.
- **Key Invariants:**
  1. *Unknown $\ne$ Unreliable:* Newcomers in `INSUFFICIENT_EVIDENCE` receive neutral framing, not punitive red warnings.
  2. *Bilateral Confirmation:* Physical handovers and returns require dual photo-verified sign-offs.
  3. *Human-in-the-Loop Governance:* Automated systems flag holds; only local community moderators commit binding restrictions.

### 3.3 Centerpiece Visuals (50% Area)
- **Visual 1 (Left): Multi-Dimensional Assurance Engine Pipeline**
  - Diagram showing: Raw Transaction Events $\to$ Beta Distribution Prior/Posterior $\to$ Graph Hop Decay ($k \le 4$) $\to$ Collusion Ring S1–S5 Filtering $\to$ 9-Field Assurance Output Object.
- **Visual 2 (Right): Modern Mobile UI Showcase**
  - High-res mockups of Screen **W1** (Lender Assurance Panel with 90% credible interval bar $[0.05, 0.95]$) and Screen **W16** (My Evidence Profile showing punctuality, care history, and manipulation risk status).

### 3.4 Scope, Evidence & FYP-2 Roadmap (Bottom Section)
- **Scope Metric:** **67% Committed Scope Completed** (40 of 60 FRs fully implemented and passing automated tests in Iteration 2, exceeding the 60% handbook threshold).
- **Testing & Verification Evidence:**
  - 46/46 React Native / Expo UI tests passing in Jest with 100% NFR-U-01 compliance assertions.
  - Zero composite scores detected across all 27 audited screen surfaces.
  - Sub-second assessment response time ($P95 \le 500\text{ ms}$).
- **FYP-2 Roadmap Preview:**
  - Search Tier 2 & 3 Learning-to-Rank on pilot click logs.
  - Pilot community deployment (30–50 households in Islamabad F-7 sector).
  - Formal SUS (System Usability Scale) and perceived fairness evaluation.

