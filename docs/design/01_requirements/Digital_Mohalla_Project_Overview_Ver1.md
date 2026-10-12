# Digital Mohalla

### Platform Overview & Feature Specification

| Field | Value |
| --- | --- |
| Version | Post-defence, revision of 2026-10-10 |
| Status | Overview; superseded where `01_requirements/DigitalMohalla_Use_Cases_Ver1.md`, `01_requirements/DigitalMohalla_FR_NFR_Ver1.md` (v1.2), an accepted ADR or a completed design step differ |
| Changes in this revision | Interview dependencies removed (Problem Validation, §1 locality method, §11 scenarios, §12, §15); proposed scenario ES-13 added to §11; text-encoding errors and the "Muhalla" spelling fixed; broken table headers repaired. No technical content changed. |

## Table of Contents

Executive Overview

Post-Defence Direction

1. User & Community Management

2. Community Events & Activities

3. Resource Sharing & Item Management

4. Search, Discovery & Matching Engine

5. Trust, Reputation & Safety

6. Community Forum & Chatbot

7. Communication & Notifications

8. Vendor Management

9. Administration & Moderation

10. Analytics & Reports

11. UI & UX

12. Deployment

13. Testing & Debugging

14. Design & Analysis

15. Documentation

## Executive Overview

### What is Digital Mohalla?

Digital Mohalla is a neighborhood-based digital ecosystem designed to make local communities more connected, trustworthy, and resourceful. It brings together borrowing and lending, savings circles, community discussions, vendor services, and AI-powered matching into one platform so people can share what they have, find what they need, and build stronger social ties.

### At Its Core

At its core, the platform helps Pakistani neighborhoods move from informal, disconnected interactions to a structured system where trust, reputation, and convenience are built into every interaction. A user can create a verified profile, post an item to lend or rent, search for nearby resources, join community events, ask for advice in a community forum, or buy from a trusted local vendor — all within the same app.

### Core Value Proposition

What makes the idea strong is that it is not just a marketplace or just a social network. It combines utility + community + trust + intelligence. The AI layer improves search, recommendation, matching, fraud detection, and predictions, while the trust system makes people more comfortable sharing items, money, and advice with neighbors.

### Key Benefits

Reduce waste by encouraging reuse and sharing

Make borrowing safer through verification and reputation

Support savings culture in the neighborhood.

Strengthen local relationships through forums and community events.

Help small vendors reach nearby buyers

Provide transparency through tracking, reviews, and admin moderation

Overall, Digital Mohalla is positioned as a smart community operating system for local neighborhoods — one that supports daily needs, social connection, financial cooperation, and local commerce in a single trusted platform.

## Post-Defence Direction

### Defence Outcome

The proposal was approved with minor modifications. The panel made three points: location needs to be shown to be a real issue, the project has positive social potential, and it has limited technical challenges. The third point is treated as the serious one, because a platform made of generic ratings and CRUD screens would not satisfy the computing requirement. The rest of this document has been updated so that the computing core is the assurance engine described in section 5.

### Project Direction and Central Computing Problem

Digital Mohalla focuses on verified, uncertainty-aware neighbourhood borrowing and lending, from request to return. The central computing problem is:

Determine whether a proposed borrowing transaction has sufficient trustworthy evidence under sparse, role-dependent and potentially manipulated history, while protecting location privacy and escalating uncertain cases to humans.

### Committed Core and Supporting Scope

Committed core:

Community membership

Privacy-preserving locality verification

Borrowing requests

Transaction lifecycle (event-sourced, section 3)

Evidence-based assurance (section 5)

Handover and return confirmation

Dispute management

Moderator review

Supporting or stretch scope, built only after the core works:

Vendors

Community events

Kameti management

General chatbot

Social feed

Advertisements

Broad analytics

Sections 2, 6, 7, 9 and the neighbourhood analysis in section 11 describe supporting or stretch modules and are marked that way at the start of each section. Search and matching (section 4) were not placed in either group by the post-defence plan, so they are treated as supporting scope here. [Team to confirm.]

### Scope Protections

Digital Mohalla must not become:

A generic social network

A conventional listings application

A neighbourhood surveillance system

An opaque social-scoring system

An LLM-based substitute for a computing challenge

### Problem Validation

The team does not run interviews or a survey. The team treats locality and location spoofing as a real issue for physical handover between neighbours, and answers the panel's point that location must be shown to be a real issue with design evidence:

The location threats in the extended threat model (section 5.13), including location spoofing

The six locality test cases in section 1 (spoofing, boundary users, visitors, permission refusal, duplicate accounts, false rejection of genuine residents)

A comparison of the verification methods in section 1 on false accepts and rejects, privacy, spoofing resistance and cost (design step A11)

The privacy design: coarse community only, no raw location traces, no exact addresses, exact meeting point disclosed only after both parties agree

Location is used as eligibility and safety evidence for a physical handover, not for tracking. This evidence is recorded against the location action in the panel action register (Form 10).

### Work Division and Milestones

Student 1, transaction and location infrastructure: membership, location verification, state machine, privacy and security

Student 2, assurance and manipulation engine: evidence model, uncertainty, adversarial cases and technical evaluation

Student 3, product and validation: resident application, moderator interface, dispute workflow, stakeholder studies and deployment

Milestones:

Week 1: freeze the borrowing and lending workflow, define the assurance states

Weeks 2 to 3: implement the state machine, one location-verification method and the first six evaluation scenarios

Weeks 4 to 6: implement the assurance engine, dispute workflow and manipulation tests

Before the supervisory mid-evaluation: demonstrate one request-to-return case involving uncertain evidence, human review and transparent evidence updating

## 1. User & Community Management

### Core Features

User registration and login

Email, phone, or social authentication

User profile management

Profile photo and basic biography

Household or individual account type

Neighborhood selection or location-based community assignment

Approximate location rather than public exact address

Community membership request

Admin approval for registration communities

Multiple roles: Lender, Borrower, Community Moderator, Vendor (supporting scope)

Interest and skill categories

Privacy settings

Profile visibility settings

Account blocking and reporting

### Locality Verification and Location Privacy

Location provides eligibility and safety evidence. It is not used for continuous tracking. The design is:

A user joins a coarse neighbourhood or housing society

Membership is verified once or periodically

Public profiles show only the community or an approximate distance

The exact meeting location is disclosed only after both parties agree

Continuous location tracking is not used

Only the coarse community and the verification result are stored, not raw location traces [retention rules to be defined]

Verification methods to be evaluated:

Coarse GPS geofencing

Community invitation

Moderator approval

Privacy-preserving address evidence

A combination of location and social verification

Selected method (design step A11, 2026-10-11): a one-time coarse GPS geofence check plus an invitation from a verified member; both must agree for VERIFIED, and a moderator decides anything inconclusive or conflicting. The comparison, decision table and the six test cases are in `design/locality/Locality_Design_A11.md`. Whether it is built in iteration 1 or iteration 2 is decided at the iteration 1 build gate (D-11).

Test cases for locality verification:

GPS spoofing

Boundary users, just inside and just outside the coarse area

Visitors

Location-permission refusal

Duplicate accounts

False rejection of genuine residents

Measures for this component are location-verification error (false accepts and false rejects) and privacy acceptability as reported by pilot participants.

## 2. Community Events & Activities

Post-defence scope note: this section is supporting or stretch scope. It is not part of the committed core and is built only after the core works.

### Overview

Automate online events: Plan, Recommend items, Reviews, Suggestions

### Event Types

Savings gathering

Kitty parties

Community meeting

Workshop or training

Sports activity

Children's activity

Religious or cultural gathering

Skill-sharing session

Gardening activity

Cleanup or community-service project

Local celebration

Buy/sell/trade event

Online session

Private household event

### Event Creation

An organizer should be able to define:

Event title, description, type, and cover image

Date, time, and duration

Physical, online, or hybrid mode

Approximate location

Maximum capacity

Registration deadline

Eligibility requirements and age group

Required materials

Participation fee and deposit (if applicable)

Organizer contact method

Public, community-only, invitation-only, or private visibility

Cancellation policy

Accessibility information

Event rules and code of conduct

### Event Registration

Participants should be able to:

View event details

Register for an event

Cancel registration

Join a waitlist

Provide custom registration information

Select a ticket or participation category

Invite another community member

View their upcoming events

Receive registration confirmation

Receive cancellation or schedule-change notifications

### Event Capacity and Attendance

Capacity control and automatic registration closure

Waitlist management with promotion

Attendee list for authorized organizers

Registration status: Registered, Waitlisted, Cancelled, Attended, No-show

QR-code or short-code check-in

Manual check-in fallback

Attendance history

Post-event feedback

### Event Agenda and Tasks

For larger events, support:

Agenda or schedule with multiple sessions

Speakers or facilitators assignment

Volunteer assignments

Required resources

Task assignment and organizer checklist

Event announcements

Shared documents or instructions

### Event Communication

Each event should have:

Event announcement feed

Organizer-to-attendee messaging

Group discussion

Pinned updates

Questions and answers

Polls

Reminder notifications

Change notifications

Post-event message

Event photo or document sharing

### Event Recommendations

The system could recommend events using:

User interests

Neighborhood

Age group

Previous participation

Availability

Event type

Trust or eligibility requirements

Technical Approach: Content-Based Personalization

The recommendation engine combines multiple event features to score each event for each user:

Feature Scoring (Weighted Combination):

Category Match: Does the event category align with the user's stated interests (e.g., "gardening", "skill-sharing")? Users who joined gardening communities or posted about gardening receive higher scores for gardening events.

Location Proximity: Is the event geographically near the user? Events in or immediately adjacent to the user's neighborhood score higher.

Organizer Trust: Is the event organized by someone with a strong community reputation? Events from trusted organizers (based on their completion history and community ratings) rank higher.

Temporal Alignment: Does the event time fit the user's availability? Events scheduled at times when the user has attended similar events before score higher.

Capacity & Accessibility: Is the event suitable for the user? Events with capacity remaining and accessible facilities score appropriately.

Diversity Bonus: To encourage exploration, events outside the user's typical preferences receive a small boost This ensures users discover new activities and organizers are not locked into "popular" status.

How It Works (Backend Process):

For each active event and each user, the system computes:

recommendation_score=

0.30 × category_similarity +

0.25 x location_score +

0.20 x organizer_trust_score +

0.15 x temporal_fit +

0.10 (capacity_available + accessibility_match) +

0.05 × diversity_bonus

The top-N events (e.g., top 10) are displayed in the user's feed, sorted by this score.

Data Sources:

User interests: Extracted from profile fields, communities joined, items they've listed, and past event participation.

Event metadata: Title, description, category, date/time, location, organizer info, capacity, and accessibility flags.

Trust scores: Organizer reputation from past event attendance, community feedback, and completion rates.

User history: Past event attendance, timing patterns, and engagement.

Why This Matters:

Without personalization, new event organizers would struggle to reach attendees; only "popular" events would be discovered. Personalized recommendations ensure diverse events get visibility.

Users discover events outside their typical preferences, strengthening community ties across different groups.

The transparent, explainable scoring means users understand why they see an event recommendation.

Evaluation:

Offline: Hand-label 20-30 user-event pairs as "likely interested" or "not interested" based on their profile. Measure precision of recommendations against these labels.

Online: Track engagement metrics - click-through rate on recommendations, registration from recommended events, post-event satisfaction ratings.

## 3. Resource Sharing & Item Management

### Overview

This is the main borrowing, lending, renting, selling, swapping, and requesting module.

### Item Listing

Users should be able to create listings containing:

Item title, description, category, and images

Condition

Transaction type: Borrow, Lend, Rent, Sell, Swap

Availability dates

Approximate location

Price or free-to-borrow status

Security deposit

Usage instructions

Restrictions

Preferred handover method

Listing expiry date

### Item Categories

Start with a smaller set of categories:

Household

Tools and DIY

Books

Baby and children

Party and event equipment

Sports

Gardening

Electronics

Medical items, automotive items, and high-value electronics may create additional safety and liability issues. Treat them as optional categories or apply stronger restrictions.

### Availability

Availability calendar

Booking requests

Conflicting request detection

Expiry alerts

Temporarily unavailable status

Listing pause

Item usage history

### Requests

A user should be able to:

Search for an item

Post a request when no item is found

Specify date, duration, distance, and transaction type

Receive matching listings

Save a request

Cancel a request

Mark a request as fulfilled

### Transaction and Interaction Lifecycle

Create a shared workflow engine for borrowing, event participation, and possibly vendor orders. In the committed core the engine is built for borrowing first. Event participation and vendor orders are supporting scope.

### Borrowing Lifecycle

Draft → Published → Request received → Accepted → Handover pending → Active → Return requested → Returned → Completed

Additional states: Rejected, Cancelled, Expired, Disputed, No-show

### Post-Defence Borrowing Lifecycle (Event-Sourced)

For the committed core, borrowing follows the lifecycle below. It starts at the request rather than at listing publication, and it replaces the general borrowing lifecycle above wherever the two differ.

Request created

Locality eligibility checked

Evidence summary generated

Lender accepts or declines

Handover confirmed

Loan becomes active

Reminder or extension issued

Return initiated

Both parties confirm condition

Dispute opened where necessary

Moderator reviews evidence

Transaction closes

Verified events update future assessments

The lifecycle is event-sourced: every transition is stored as an event and the current state is derived from the event history. Each event records:

The actor

The timestamp

The previous state

The new state

The supporting evidence

The authorisation under which the actor made the transition

Step 13 is how completed transactions become evidence for later assessments (see section 5.12).

### Event Lifecycle

Draft → Published → Registration open → Registration closed → Ongoing → Completed

Additional states: Cancelled, Postponed, Full, Waitlisted

### Why This Matters

A state-based design gives your project technical depth. It requires you to handle:

Invalid transitions

Concurrent requests

Capacity limits

Cancellation rules

Notifications

Audit history

Disputes

Recovery from failures

This is stronger than implementing disconnected screens.

## 4. Search, Discovery & Matching Engine

Post-defence scope note: this section was not placed in the committed core or the listed stretch scope by the post-defence plan, so it is treated as supporting scope. Where a trust_score appears in the formulas below, it stands for a feature derived
from the evidence-based assurance output of section 5; it must not be shown to users
as a single unexplained number.

Search: Learning-to-Rank with Phased Rollout

Overview

When a user searches for an item, they often use different language than the person who listed it. For example, someone might search for "digging tool" while a lender listed it as "spade". A traditional keyword-match search would fail. Beyond word matching, ranking is also a genuinely multi-objective problem: a fixed weighted formula (e.g., trust + distance + relevance) cannot adapt to the fact that different users care about different things - one user prioritizes trust, another prioritizes proximity. The end-state goal is a Learning-to-Rank (LTR) system that learns these priorities from real user behavior, reached through a phased rollout rather than built all at once.

The Core Problem with Learning-to-Rank

LambdaMART-style LTR models are trained on real interaction logs (query, results shown, item clicked, outcome). No such logs exist before the platform has real users, and a university pilot (roughly 50 active users over a semester) will only generate an estimated 700-900 clicks total - borderline for training a reliable model, and certainly not available in week one. Building the full LTR system in isolation risks spending most of a semester with nothing to show and no data to train on. The approach below is designed to avoid that failure mode.

Tier 1: Semantic Retrieval + Hybrid Ranking (available from day one)

Before any learning can happen, the platform needs a working, reasonably good ranker with zero training data. This tier combines three technical layers and serves as both the live search experience and the cold-start fallback:

1. Query & Item Encoding (Natural Language Processing):

Both the search query and all item titles/descriptions are processed through a pre-trained transformer model (BERT, from Hugging Face) to produce 768-dimensional semantic embeddings. The query "gardening tools" and the item "spade for digging" end up close together in vector space because they share meaning, even though the words differ. Embeddings are computed once at indexing time and cached in PostgreSQL.

2. Vector Search (Information Retrieval):

Item embeddings are indexed using FAISS (Facebook AI Similarity Search) for fast nearest-neighbor search. A user's query is encoded and matched against the index to retrieve the top-100 semantically closest items, targeting under 50ms latency.

3. Hybrid Ranking (Feature Combination):

Semantic similarity alone is not enough - a close match from an unreliable, distant lender is a bad result. The top-100 candidates are re-scored using a hand-weighted combination of signals:

final_score =

0.40 x semantic_similarity(query, item) +

0.30 x trust_score(lender) +

0.15 x availability_match(requested_dates) +

0.10 x distance_score(location) +

0.05 x recency_bonus(listing_freshness)

This is the same formula an LTR model would eventually learn to weight automatically - here the weights are fixed by hand as a reasonable starting point, and this hybrid ranker doubles as the permanent fallback if the learned model ever underperforms it.

Tier 2: LTR Pipeline Validation (public/synthetic data)

While Tier 1 serves real users, the engineering for the eventual LTR model is built and proven in parallel using a public classifieds or e-commerce dataset (e.g., an OLX-style listings dump, or click/purchase-event data such as RetailRocket). This dataset is used to build and stress-test the full LTR machinery end-to-end: click-log schema, feature computation (BM25, semantic similarity, distance, trust, recency - roughly 20-30 features per candidate), FAISS retrieval, a LightGBM/LambdaMART training loop, and offline evaluation (NDCG@10, precision@k, latency benchmarking). Domain-specific fields the public data lacks (location, trust score, transaction type) are synthetically overlaid so the feature pipeline can be exercised end-to-end.

This tier validates that the code is correct, not that the learned weights apply to Digital Mohalla. A model trained on retail purchase behavior has learned patterns specific to that domain (e.g., "low price and many reviews predict a click"), which do not transfer to neighborhood borrowing, where distance and return punctuality matter in ways online shopping never captures. Any model weights or rankings produced in this tier are reported as pipeline-validation results only, never presented as reflecting real Digital Mohalla user preferences.

Tier 3: Production LTR (real pilot data)

Once the pilot has been running long enough to generate real query/click/borrow logs, the same schema and training loop proven in Tier 2 are pointed at real data - a configuration change, not a rewrite. The model is trained with implicit labels (borrowed = +1, clicked but not borrowed = 0, ignored = -1) and evaluated with a held-out test set (NDCG@10, NDCG@20) and, traffic permitting, an online A/B test against the Tier 1 hybrid ranker (CTR, conversion to borrowing). Because pilot click volume is modest, the Tier 1 hybrid ranker is kept live as the fallback; the LTR model only replaces it where it demonstrably outperforms.

Why This Phased Architecture:

Always has a working system: Tier 1 needs no training data and is live from week one, avoiding the "13 weeks with nothing to show" failure mode of building LTR in isolation.

De-risks the hardest engineering early: feature computation, model training, and evaluation infrastructure are built and debugged against a real (if mismatched) dataset in Tier 2, so the difficult plumbing is proven before real user data even exists.

Honest about what data can and cannot prove: pipeline-validation results and production results are reported separately, never blended, so the eventual academic contribution is not overstated.

Interpretable at every stage: the Tier 1 hybrid formula is transparent and debuggable; the LTR model, once trained, can be compared feature-by-feature against it.

Data Requirements:

Tier 1 needs only items and queries (100-500 synthetic items suffice to launch). Tier 2 needs a public classifieds/e-commerce dataset with synthetic domain-field overlays. Tier 3 needs real query/click/borrow logs from the pilot (roughly 700-900 clicks estimated over a semester with ~50 active users - workable but borderline for a robust model, hence the Tier 1 fallback remains in place). No external data sources are required to launch.

Technical Stack:

Embedding Service: Load BERT from Hugging Face, encode text, cache in PostgreSQL (~200 lines of Python)

Vector Search: FAISS index builder, query engine (~150 lines)

Hybrid Ranking: Score computation logic (~100 lines)

Feature Store: Feature computation and caching for LTR (~250 lines)

LTR Training: LightGBM/LambdaMART training loop, offline evaluation (~250 lines)

Search API: HTTP endpoint exposing search with explanation (~100 lines FastAPI)

Query Logging: Capture searches, clicks, and outcomes for LTR training (~150 lines)

Evaluation:

Tier 1 offline: Hand-label 20-30 representative queries (e.g., "baby stroller", "gardening tool") and mark correct matches. Measure Precision@5, Recall@10, and NDCG@10. Target: 60-70% precision, a +30-40% improvement over keyword-only search.

Tier 2 offline: NDCG@10/@20 and precision@k on the public dataset's held-out interactions, confirming the LTR pipeline trains and evaluates correctly before any real data is involved.

Tier 3 online: Track real user behavior once the LTR model is live - search adoption rate, click-through rate, conversion to borrowing, and user satisfaction ratings, compared against the Tier 1 hybrid ranker as baseline.

Intelligent Matching: Bipartite Matching with Fairness

Overview

The matching engine solves a resource allocation problem: Given a set of requests (users looking for items) and a set of available items, how do we assign them optimally and fairly?

Without intelligent matching, the system might prioritize high-reputation users, leaving new or lesser-known users unmatched. The matching engine ensures that opportunities are distributed equitably across the community.

Problem Definition:

This is a bipartite graph matching problem:

Left side (requests): Users looking for specific items on specific dates.

Right side (items): Owners with available items.

Edges (possible matches): A request can be fulfilled by an item if the category, dates, and location align.

Weights (quality scores): Each potential match has a weight based on how good the match is for both parties (e.g., trust, distance, availability).

Traditional approach: Greedy matching would assign each request to the best available item, maximizing total score. However, this creates an "rich get richer" effect where high-reputation items are snapped up by many requests, while unpopular items remain unmatched.

Core Algorithm: Hungarian Algorithm with Fairness Constraints

The matching engine uses the Hungarian algorithm, a classic graph algorithm that finds maximum weighted bipartite matching in O(n³) time.

Step 1: Build the Bipartite Graph

For each request-item pair that is compatible (same category, overlapping dates, reasonable distance), compute a match quality score combining:

Semantic similarity of request to item

Trust score of the lender

Distance between requester and lender

Availability alignment

Step 2: Apply Fairness Constraints

Before running Hungarian, apply fairness constraints to prevent monopolization:

Each item can be matched to at most K requests (configurable; e.g., K = 3 means an item can fulfill up to 3 requests if it's available multiple times)

Prioritize requests from newer or lower-reputation users: Assign a fairness boost to requests from users with lower trust scores

Measure disparity using Gini coefficient: Track how unevenly matches are distributed and adjust weights if disparity becomes too high

Step 3: Compute Optimal Assignment

Run the Hungarian algorithm on the fairness-adjusted graph to find the optimal matching (maximum total score while respecting constraints).

Output: A list of request-item pairs that should be connected. For each matched pair, the system creates a transaction, sends notifications to both parties, and records the outcome.

Why This Approach:

Optimal: Maximizes total successful matches (higher score = more satisfied users overall)

Fair: Ensures new and unpopular users still get matched; prevents "rich get richer" dynamics

Scalable: Algorithm runs efficiently even with 500+ requests and items

Explainable: Constraints are transparent; users can understand why they were or were not matched

Data Requirements:

The algorithm works with synthetic data immediately (no training needed). It processes real requests and items from users as they accumulate.

Technical Stack:

Graph construction: Build bipartite graph from requests and items (~100 lines Python)

Fairness enforcement: Apply constraints, compute Gini coefficient (~150 lines)

Hungarian algorithm: Use scipy.optimize linear_sum_assignment or custom implementation (~200 lines)

Transaction creation: Persist matched pairs, send notifications (~100 lines)

Evaluation:

Offline: Generate synthetic request and item sets (100-500 items, 50-200 requests). Verify:

Optimality: Do matched pairs have high total score?

Fairness: Is the Gini coefficient low (equitable distribution)?

Constraint satisfaction: Are no items over-matched? Are fairness bounds respected?

Online: Track user acceptance of algorithmic matches and satisfaction ratings. Target: 70%+ acceptance.

Classic Search Features

In addition to the semantic and matching engines, the platform supports standard search features:

Keyword search (fallback for users or items without embeddings)

Category filtering

Neighborhood filtering

Radius search

Availability filtering

Transaction-type filtering

Price filtering

Condition filtering

Sorting by relevance, distance, trust, and newest listing

Saved searches

Similar-item discovery

## 5. Trust, Reputation & Safety

### Overview

For the committed core, trust is applied to borrowing and lending transactions. Reuse for events and vendors is supporting scope and is considered only after the borrowing case works.

### Verification

Possible levels:

Unverified

Email or phone verified

Community membership verified

Identity verified

Organizer verified

Vendor verified

### Reputation Dimensions

Calculate separate indicators for:

Transaction completion

Return punctuality

Item condition compliance

Communication responsiveness

Event attendance reliability

Contribution reliability

Community helpfulness

Reports or complaints

Avoid hiding everything inside one unexplained trust number. Show the factors contributing to the score.

### Reviews

Support:

Lender review

Borrower review

Event organizer review

Attendee review

Vendor review

Item review

Event review

Multi-dimensional ratings

Written feedback

Review eligibility only after a completed interaction

### Safety Features

Report user, item, event

Block user

Dispute initiation

Admin review queue

Suspicious behavior flag

Community rules and code of conduct

Approximate location display

Handover confirmation

Item condition checklist

### Trust Engine — Technical Specification

#### 5.1 Central Trust Problem

Digital Mohalla must estimate whether an interaction is sufficiently trustworthy when direct evidence may be sparse, trust may depend on the user's role, available evidence may come indirectly through the community network, and reputation may be manipulated.

The trust engine therefore does not produce a single unexplained reputation number. Instead, it combines multiple evidence sources and produces:

Assurance state (describes the transaction evidence, not the person)

Confidence or uncertainty

Direct evidence

Indirect evidence

Manipulation risk

Transaction context

Recommended safeguards

Escalation recommendation where necessary

The overall pipeline is:

Direct Evidence → Bayesian Trust Estimation → Indirect Trust → Manipulation Detection → Context/Risk Analysis → Decision Policy → Safeguards or Human Escalation

#### 5.2 Sparse Evidence and Recency-Weighted Beta Posterior

##### Problem

Traditional average ratings can be misleading when users have only a few interactions.

For example:

User A: 1 successful return → 100% success rate

User B: 18 successful returns and 2 late returns → 90% success rate

Although User A has a higher average, User B has substantially more evidence supporting the estimate.

##### Approach

Digital Mohalla models each binary transaction outcome with a Beta posterior. The
Beta-Binomial distribution is reserved for predicting the number of successes in a
future batch; it is not the name of the posterior itself.

An outcome such as "returned on time" is treated as a Bernoulli trial. The observed successes and failures update a prior Beta distribution:

\[
p\mid D\sim\operatorname{Beta}(\alpha_0+s,\beta_0+f)
\]

where:

\(\alpha\) and \(\beta\) represent prior parameters

successes represent successful observed outcomes

failures represent unsuccessful observed outcomes

The posterior mean is:

\[
\mathbb{E}[p]=\frac{\alpha_0+s}{\alpha_0+\beta_0+s+f}
\]

The system also retains the posterior distribution so that uncertainty can be measured rather than presenting only a point estimate.

A wider Bayesian credible interval represents greater uncertainty, while a narrower
interval represents stronger evidence. The term credible interval is used instead of
confidence interval because the interval is derived from a posterior distribution.

#### Recency decay

Older outcomes should not have exactly the same influence as recent outcomes. For an
outcome observed \(d_i\) days ago, the evidence weight is:

\[
w_i = 2^{-d_i/h}
\]

where \(h\) is the configurable half-life. The weighted success and failure evidence is:

\[
s_w=\sum_i w_i y_i,\qquad f_w=\sum_i w_i(1-y_i)
\]

and the posterior becomes:

\[
p\mid D\sim\operatorname{Beta}(\alpha_0+s_w,\beta_0+f_w).
\]

The initial implementation uses \(\alpha_0=\beta_0=1\), a 180-day half-life, and a
90% credible interval. These are starting parameters and must be compared with other
half-lives during evaluation. Raw transaction events remain stored so that estimates
can be recomputed when parameters change.

##### Why this model?

The Beta distribution is conjugate to the Binomial likelihood, allowing efficient
analytical updates while preserving uncertainty information.

This is particularly useful for Digital Mohalla because users may have very limited transaction history.

For example, with a uniform prior:

0 successes, 0 failures → Beta(1,1)

1 success, 0 failures → Beta(2,1)

18 successes, 2 failures → Beta(19,3)

The important distinction is that the system does not interpret "no history" as "bad
user." Instead, it returns the prior with high uncertainty due to insufficient evidence.

#### 5.3 Role-Specific Reputation

A single global trust score is insufficient because user behavior can differ across contexts.

Digital Mohalla therefore maintains separate reputation dimensions for different roles.

| Role | Example Evidence |
| --- | --- |
| Lender | Return condition, transaction completion, deposit handling |
| Borrower | Return punctuality, item condition, handover reliability |
| Event Organizer | Event completion, communication, attendance reliability |
| Vendor | Service completion, customer feedback, complaint history |

For example, strong event-organizer performance should not automatically imply that the same user will return borrowed equipment on time.

The system therefore estimates trust using evidence relevant to the current interaction.

#### 5.4 Cold-Start Handling

Cold start occurs when a new user has little or no direct transaction history.

Digital Mohalla mitigates cold start using multiple mechanisms:

Bayesian prior: A new user receives an explicit prior distribution rather than an artificial claim of high or low trust.

Indirect community evidence: Relevant trust relationships can provide evidence through bounded graph traversal.

Uncertainty-aware decisions: Low evidence results in lower confidence rather than an unjustified high-confidence score.

Risk-sensitive safeguards: High-value or high-risk interactions can require stronger verification when confidence is low.

Manipulation detection: New accounts attempting to rapidly manufacture reputation can be flagged.

If a user has both zero direct history and no meaningful community connections, the system cannot legitimately infer strong user-specific trust. In that situation, it falls back to the prior or an appropriate population baseline while applying safeguards based on uncertainty and transaction risk.

Therefore, the system mitigates rather than completely eliminates cold-start limitations.

#### 5.5 Graph-Based Indirect Trust

##### Problem

A user may have no direct history with another community member but may have relevant evidence through trusted connections.

The system represents community relationships as a weighted directed graph:

Nodes = users

Edges = trust relationships or relevant interaction evidence

Edge weights = verified evidence strength for the same role and metric. An edge is
derived from the source user's evidence; it is not an unrestricted manual vouch.

Trust propagation is limited to a small number of hops to prevent distant evidence from becoming unreliable.

##### Bounded k-Hop Trust

The initial design uses a maximum of three hops.

For each simple path \(P=(u=x_0,\ldots,x_l=v)\):

Path weight = Product of Edge Weights \(\times \gamma^{(hops-1)}\)

A distance-decay factor reduces the contribution of longer paths:

Decay = 0.7^(hops−1)

The 0.7 value is an initial design parameter and will be validated through sensitivity analysis rather than treated as a universal constant.

The initial value is \(\gamma=0.7\). The first hop is not penalised; each additional hop
is multiplied by \(\gamma\). This is a tunable project parameter, not a universal
constant. The system keeps at most the strongest path per first-hop intermediary so
that correlated paths are not counted as independent evidence.

For the selected paths, indirect evidence strength is:

\[
I(u,v)=1-\prod_{P}(1-q(P)).
\]

Let \(t_v\) be the target's direct mean and \(b\) the role/metric population baseline.
If direct evidence is unavailable, \(t_v=b\) and the explanation must say that the
result is prior-backed. Indirect reliability is capped at 0.6 and is reduced when
there are few paths or little first-hop diversity:

\[
\rho=\min(0.6,\; \min(1,|\mathcal P|/3)\;
\min(1,|\text{first hops}|/2)\;I(u,v)).
\]

The indirect estimate is:

\[
t_{\text{indirect}}=b+\rho(t_v-b).
\]

Indirect evidence supplements direct evidence; it does not replace it or claim the same
certainty.

##### Why limit k?

Increasing the number of hops provides greater reach but also:

increases computational cost

introduces weaker and more distant evidence

increases the possibility of correlated evidence

creates opportunities for manipulation to propagate through the network

The system will therefore evaluate different values such as \(k=1,2,3,4\) and compare
their accuracy, coverage, latency, calibration, and false-positive behaviour.

#### 5.6 Reputation Manipulation and Collusion Detection

Trust systems are vulnerable to coordinated manipulation.

Potential examples include:

Fake accounts rating one another

New accounts rapidly exchanging positive ratings

A vendor creating artificial buyer accounts

Coordinated accounts attempting to create artificial indirect trust

Multiple accounts sharing infrastructure

Digital Mohalla uses multiple interpretable signals rather than relying on a single black-box model.

Potential signals include:

Reciprocal rating clustering

Unusual rating velocity

New-account activity

Identical or highly similar review text

Device/IP account linkage where such data is legitimately available

Each signal contributes to an overall manipulation-risk score.

The initial risk categories are:

| Risk Score | Suggested Action |
| --- | --- |
| 0–19 | Proceed normally |
| 20–39 | Monitor |
| 40–59 | Request additional verification |
| 60–100 | Flag for moderator review; restrict only after a human decision |

These thresholds are initial parameters and must be validated experimentally.

The detector should be interpreted as a risk detector, not proof of fraud. A legitimate family or friend group may naturally produce reciprocal interactions, so false-positive rates must be measured during evaluation.

#### 5.7 Explainability

The trust system should not simply return:

Estimated probability is not a standalone trust score.

Instead, it should explain the evidence contributing to the recommendation.

Example:

Assurance State:REVIEW_RECOMMENDED
Estimated Success Probability: 65%
90% Bayesian Credible Interval: 42%–82%
Effective Evidence: 3.4 weighted observations

Evidence:

3 successful direct transactions, weighted by recency

2 relevant indirect connections

8 community transactions used as indirect evidence

No significant manipulation signals

Recommended Safeguards:

Security deposit

Handover photographs

Clearly defined return date

This makes the decision auditable by both users and moderators. A high estimated
probability with a wide credible interval is treated differently from the same
probability supported by substantial evidence.

#### 5.8 Context-Aware Decision Policy

The trust estimate itself is not the final decision.

The decision policy considers:

Direct trust

Indirect trust

Evidence confidence

Manipulation risk

User role

Transaction type

Item value

Dispute history

Verification status

The system can therefore produce decisions such as:

Proceed normally

Proceed with safeguards

Request verification

Restrict high-value transaction

Escalate to moderator

Trust and manipulation risk are deliberately treated as different dimensions rather than simply averaged together.

For example, a user may have a high estimated trust score but also show strong manipulation signals. Averaging the two values could hide the security concern. Instead, the decision policy should preserve both dimensions and apply appropriate safeguards.

#### 5.9 Human-in-the-Loop Escalation

Some decisions should not be fully automated.

Escalation can occur when:

An item-condition dispute is filed

A high-value transaction has low-confidence trust

A failed transaction coincides with significant manipulation signals

A user explicitly files a dispute

Evidence is contradictory or insufficient

The moderator should receive an evidence trail containing:

Transaction details

Item value

Both parties' claims

Handover and return photographs

Relevant messages

Transaction history

Trust analysis

Manipulation-risk signals

Previous disputes where appropriate

The system therefore acts as a decision-support mechanism rather than replacing human judgment in ambiguous cases.

#### 5.10 Algorithmic Implementation

The proposed trust and safety framework will be implemented as a sequence of modular computational components. Each component produces an interpretable output that is passed to the next stage of the decision pipeline.

1. Recency-Weighted Beta Posterior Trust Estimation

For each user, role, and metric, direct transaction outcomes are represented as
successes and failures. A Beta prior is updated using recency-weighted outcomes:

\[
p\sim\operatorname{Beta}(\alpha_0,\beta_0),\qquad
p\mid D\sim\operatorname{Beta}(\alpha_0+s_w,\beta_0+f_w)
\]

The posterior mean is calculated as:

\[
\hat p=\frac{\alpha_0+s_w}{\alpha_0+\beta_0+s_w+f_w}
\]

where ss represents successful outcomes and ff represents unsuccessful outcomes. The system will also retain the uncertainty associated with the estimate rather than relying only on the mean trust value. This allows users with little or no history to be distinguished from users whose trust estimate is supported by substantial evidence.

Short Pseudocode:

Input: subject, role, metric, transaction outcomes, half-life

Initialize prior \(\operatorname{Beta}(\alpha_0,\beta_0)\)

For each matching outcome:

Calculate weight = 2^(-age_in_days / half_life)

If success, update \(\alpha' = \alpha + weight\)

Otherwise, update \(\beta' = \beta + weight\)

Calculate posterior mean and 90% credible interval

Return trust estimate, effective evidence, and credible interval

2. k-Hop Indirect Trust

When direct evidence is insufficient, the system will estimate trust using the user's trust network. Users are represented as nodes and directed trust relationships as weighted edges. Trust is propagated through bounded paths up to a selected maximum number of hops. Path strength is calculated by multiplying the trust weights along the path, with a decay factor applied as the path length increases.

For each path, multiply edge weights and apply \(\gamma^{hops-1}\). Keep at most one
strong path per first-hop intermediary. Aggregate selected paths with noisy-OR,
calculate path diversity, and cap indirect reliability at 0.6. Use the target's direct
mean when available; otherwise use the role/metric baseline and label the result as
prior-backed.

Input: target user, trust graph

Find trusted paths up to k hops

Calculate strength of each path

Apply hop-based decay \(\gamma^{hops-1}\)

Aggregate with noisy-OR and account for path diversity

Apply indirect-reliability cap

Return indirect estimate, paths, reliability, and evidence explanation

The initial values for kk, decay, and the indirect-trust cap will be treated as configurable parameters and evaluated experimentally rather than assumed to be universally optimal.

3. Reputation Manipulation Detection

The system will combine multiple behavioral signals rather than relying on a single fraud indicator. These signals include reciprocal rating patterns, unusual rating velocity, newly created accounts receiving rapid ratings, and similarity between review texts. Where authorized data is available, additional linkage signals may also be considered.

The signals are combined into a bounded manipulation-risk score. Different risk ranges will correspond to actions such as monitoring, verification, restriction, or escalation.

Input: ratings, reviews, account and transaction activity

Calculate reciprocal-rating signal

Calculate rating-velocity signal

Check new-account + rapid-rating behavior

Calculate review similarity where applicable

Combine weighted signals

Cap risk score

Assign risk level

Return manipulation-risk assessment

This component is intended as a risk detector rather than proof of fraudulent behavior. Thresholds and weights will therefore be evaluated using controlled manipulation scenarios and false-positive analysis.

4. Context-Aware Decision and Moderator Escalation

The final decision component combines direct trust, indirect trust, uncertainty, manipulation risk, transaction value/type, verification status, dispute history, and other relevant contextual information. Trust and manipulation risk are kept as separate dimensions rather than being blindly averaged, because a user may have a high historical trust estimate while simultaneously showing suspicious behavior.

Depending on the combined evidence and transaction context, the system may:

Proceed normally

Proceed with additional safeguards

Request verification

Restrict high-value transactions

Escalate the case to a moderator

Input: trust evidence + manipulation risk + transaction context

Assess confidence and risk

Apply context-specific decision policy

If evidence is sufficient → proceed

If moderate risk → apply safeguards/verification

If high risk or contradictory evidence → escalate

Return decision and explanation

For escalated cases, moderators will receive the relevant transaction information, item value, claims/evidence, trust analysis, manipulation signals, and available transaction history. This creates a human-in-the-loop mechanism for cases where automated decisions may be unreliable.

The complete implementation pseudocode and detailed algorithmic procedures are provided
in [11_assurance_engine/Algorithm_and_Data_Structure_Design.md](../11_assurance_engine/Algorithm_and_Data_Structure_Design.md).

##### Trust-engine data structures

The implementation stores immutable evidence events and derives estimates from them:

```text
OutcomeEvent {
    event_id, subject_id, observer_id, role, metric,
    success, occurred_at, transaction_id
}

TrustEdge {
    source_id, target_id, role, metric,
    weight, evidence_count, updated_at
}

TrustEstimate {
    subject_id, role, metric,
    alpha, beta, mean, lower_90, upper_90,
    effective_sample_size, direct_event_count, computed_at
}

PathEvidence {
    nodes, hops, path_weight
}
```

Events are filtered by subject, role, and metric. Disputed outcomes are not converted
to successes or failures until moderation resolves them. Derived estimates are
recomputed when the half-life or other model parameters change.

#### 5.11 Assurance States

The final algorithm and data-structure baseline is maintained in
`11_assurance_engine/Algorithm_and_Data_Structure_Design.md`. It is the source of truth for the
recency-weighted Beta posterior, bounded k-hop evidence, manipulation-risk
scoring, decision policy, assurance-state mapping, data contracts and
complexity analysis. The Python Phase 2 module currently implements the
dependency-free policy slice over precomputed trust inputs; it does not claim
to be the complete event store or graph engine.

The assurance engine returns one of four states for each proposed transaction. The states describe the evidence available for that transaction. They do not label a person as trustworthy or untrustworthy.

| State | Meaning | Typical case |
| --- | --- | --- |
| SUFFICIENT_EVIDENCE | Verified evidence is adequate for this item, value and context, with no unresolved conflict or manipulation signal | Consistent history of completed, on-time, confirmed returns of similar items |
| REVIEW_RECOMMENDED | Evidence exists but is mixed, dated, dissimilar to the request or shows anomalies, so a person should look at it | Reliable history with one recent dispute; a high-value request after only small loans |
| INSUFFICIENT_EVIDENCE | There is not enough verified history to judge. This is not a negative finding | New user with no history; lender review required |
| ACTIVE_DISPUTE | An unresolved dispute affects this transaction or the current evidence of the parties | Conflicting condition reports waiting for moderator review |

A new user is not treated as dangerous. With no verified history the expected output is INSUFFICIENT_EVIDENCE with the message "Insufficient verified history; lender review required."

Final decision-to-state mapping:

Proceed normally: SUFFICIENT_EVIDENCE

Proceed with safeguards: SUFFICIENT_EVIDENCE only when the evidence also meets
the strong-evidence rule; otherwise REVIEW_RECOMMENDED

Request verification: INSUFFICIENT_EVIDENCE for cold start, otherwise
REVIEW_RECOMMENDED

Restrict high-value transaction: REVIEW_RECOMMENDED, pending a human decision

Escalate to moderator: REVIEW_RECOMMENDED, or ACTIVE_DISPUTE when a dispute is open

Open disputes always take precedence. Indirect evidence alone cannot produce
SUFFICIENT_EVIDENCE, and a high-value restriction does not take effect without
human review. These are policy rules, not labels applied to a person.

For every output the engine explains which evidence raised or lowered assurance and, where human review is requested, why.

#### 5.12 Verified Transaction Evidence

A simple average star rating is not used as the trust mechanism. The engine keeps separate evidence for each of the following, and the explanation shows them separately:

Completed transactions

Timeliness of returns

Handover and return confirmation

Item-condition agreement between both parties

Disputes and how they were resolved

Transaction recency

Evidence quantity

Transaction category and value

Conflicting reports

Suspicious reciprocal activity

Initial design for the inputs that the recency-weighted Beta posterior in section 5.2
does not cover on its own (parameters are to be validated in the evaluation):

Recency: older outcomes are down-weighted when the Beta counts are updated, so the estimate follows current behaviour. The decay rate is an experimental parameter.

Similarity to earlier transactions: past loans count for more when the requested item has a similar category, value band and duration. A history of small loans gives weak support for a high-value request.

Conflicting reports: when the two parties disagree on condition, the outcome is not counted as a success or a failure until it is resolved. It drives ACTIVE_DISPUTE, and the resolved outcome is recorded as evidence after moderator review.

Confirmation: an outcome enters the evidence when the handover and return confirmations it depends on exist.

#### 5.13 Extended Manipulation Threat Model

The controlled test cases below extend the signals in section 5.6. For each case the system shows the anomaly and the evidence behind it. It does not accuse a user.

| Case | Signal or evidence shown (initial design) |
| --- | --- |
| Collusive positive ratings | Positive ratings among a small set of accounts with little other activity, similar timing and similar text |
| Reciprocal-rating groups | Reciprocal-rating clustering from section 5.6, compared with normal patterns such as family or close friends |
| Retaliatory negative ratings | A negative rating that follows shortly after a complaint or dispute from the other party and conflicts with the confirmed handover and return records |
| Duplicate or Sybil accounts | Shared verification evidence or invitation links, and near-identical behaviour across accounts, where such data is legitimately available |
| Trivial exchanges used to manufacture reputation | Many short, low-value loans between the same few accounts; trivial items carry low evidence weight |
| Sudden high-value requests | Requested value far above the account's earlier transaction values, with low similarity to its history |
| False damage claims | A condition claim contradicted by the handover and return confirmations or photos; a repeated pattern of claims by the same party |
| Location spoofing | Location evidence that is inconsistent with other membership evidence or with earlier checks |
| Moderator misuse | Moderator decisions and reversals checked against the audit log; every decision needs recorded evidence; unusual concentration of decisions involving the same users |

Moderator decisions are events in the audit log like any other (actor, timestamp, evidence, authorisation), so they can be reviewed afterwards.

After the defence, manipulation detection is part of the committed core. The detector stays rule-based and interpretable, and it is tested on the controlled cases in section 5.13. It presents anomalies and the evidence behind them; it does not accuse users.

## 6. Community Forum & Chatbot

Post-defence scope note: the community forum is supporting or stretch scope (social feed). It is not part of the committed core.

### Community Forum

Include categories such as:

Ask the community

Local recommendations

Skill sharing

Event announcements

Parenting

Gardening

DIY and home improvement

Lost and found

Community projects

Buy, sell, or trade

Local services

### Discussion Features

Create a post

Add title and description

Select a category

Add tags

Attach images

Mention users

Comment

Reply to comments

Upvote or downvote

Mark best answer

Save a post

Report content

Search discussions

Filter by category

Follow a discussion

Edit or delete own content

### Expert and Contributor Indicators

Use carefully defined badges:

Helpful contributor

Verified expert

Event organizer

Top answerer

Community volunteer

Trusted advisor

Badges should be based on transparent criteria rather than arbitrary AI decisions.

## 7. Chatbot

Post-defence scope note: the general chatbot is stretch scope. It is built only after the core works, and it must not stand in for the computing challenge in section 5.

The chatbot should not be a generic chatbot that answers anything. It should be a community information assistant grounded in approved Digital Mohalla content.

### Chatbot Purposes

The chatbot can help users:

Find relevant community events

Explain event rules

Answer questions about event registration

Find nearby items

Explain borrowing and return policies

Summarize community discussions

Find previously answered questions

Recommend relevant forum posts

Explain the factors behind an assurance state

Guide users through creating a listing or request

Answer questions from approved local resources

Escalate unanswered questions to the community forum or moderator

### Knowledge Base Design

The chatbot's corpus is not a single pile of documents. It contains three classes of content with different structure, different volatility, and different trust levels. Each class requires a different retrieval method, and the distinction drives the entire architecture.

#### Content Classes

Class A — Policy and static content Community rules, help articles, borrowing and return policies, code of conduct, approved FAQs, admin announcements. Nature: authoritative, stable, written in prose. Retrieval: hybrid semantic and keyword search.

Class B — Structured records Events, item listings, vendor profiles. Nature: field-based, with dates, states, capacity, and location. Retrieval: parameterised database query with filters.

Class C — User-generated content Forum posts, comments, accepted answers. Nature: noisy, occasionally incorrect, but carries quality signals (upvotes, best-answer flags). Retrieval: hybrid search, weighted by quality signals.

#### Rationale for the split

A question such as "What are the rules for borrowing power tools?" is a semantic search problem. A question such as "What events are happening in my neighbourhood this weekend?" is a database query with a date filter and a location filter. Representing an event record as a block of prose and relying on embedding similarity to respect the date field produces incorrect answers. Structured records must remain queryable as records.

#### Ingestion Pipeline

Content enters the retrieval index through a controlled pipeline rather than directly:

Content is created (admin-authored, or user-posted to the forum)

Content passes moderation classification, including prompt-injection screening

Content is chunked according to its class

Chunk metadata is attached (neighbourhood, visibility, validity window, state, source type, author trust tier)

Chunk is embedded and written to the index

Content is re-indexed on edit, and removed from the index on deletion, expiry, or moderation removal

Admins can approve, exclude, or pin individual sources through the knowledge base management interface.

#### Chunking Strategy

Chunking is structure-aware rather than fixed-length:

Policy documents are split at heading boundaries, with the heading path retained as a prefix in the chunk text so that section context is preserved.

Forum threads are chunked so that a question and its accepted or best answer form a single unit. Remaining comments are indexed separately at lower weight. Splitting a question from its answer destroys the retrieval unit the system most needs.

Events and listings are not chunked. They are retained as records, with a short generated text summary indexed alongside for hybrid search.

Chunk size and overlap are tuned experimentally rather than fixed by assumption.

### Chatbot Architecture

The system uses a retrieval-augmented generation (RAG) design with query routing, filtered retrieval, and enforced grounding.

#### Processing Pipeline

Step 1 — Query intake and normalisation The query is received, language-detected, and normalised. Roman Urdu spelling variants are mapped toward canonical forms before retrieval (see Language Handling below).

Step 2 — Question classification and routing An intent classifier assigns the query to one of the following categories and routes it to the appropriate retrieval path:

| Intent | Example | Retrieval path |
| --- | --- | --- |
| Policy question | "What happens if I return an item late?" | Unstructured (Class A) |
| Event lookup | "Any cleanup drives this Saturday?" | Structured query (Class B) |
| Item lookup | "Is anyone lending a pressure cooker?" | Structured query (Class B) |
| Platform how-to | "How do I create a listing?" | Unstructured (help articles) |
| Forum recall | "Has anyone asked about water tanker rates?" | Unstructured (Class C) |
| Trust explanation | "Why does my request show REVIEW_RECOMMENDED?" | Structured plus template |
| Out of scope | Medical, legal, or financial advice; unrelated requests | Refusal response |

For structured intents, the system additionally extracts query slots such as date range, category, neighbourhood, price ceiling, and transaction type. These are bound as parameters to a whitelisted query template. The language model does not generate raw database queries.

Step 3 — Retrieval with mandatory filtering

Retrieval combines two methods whose results are fused:

Lexical retrieval (BM25) — handles exact matches on names, places, and specific terms

Semantic retrieval (dense embeddings) — handles paraphrased and differently-worded questions

Results from both are merged using Reciprocal Rank Fusion. Both methods are required: lexical retrieval alone fails on paraphrase, while semantic retrieval alone performs poorly on proper nouns such as specific neighbourhood or event names.

Filters are applied within the retrieval query, not after results are returned:

Neighbourhood scope must match the user's community memberships

Visibility level must permit access by this user

Content must be within its validity window (events not yet concluded, listings not expired)

Content state must not be draft, cancelled, expired, deleted, or removed by moderation

Filtering after retrieval rather than during it frequently leaves too few usable passages to answer from, and risks surfacing content the user is not entitled to see.

Step 4 — Reranking An initial candidate set is retrieved broadly, then reordered by a cross-encoder model that evaluates query and passage together. Only the top-ranked passages are passed to generation. This improves precision at the cost of additional latency; the trade-off is measured rather than assumed.

Step 5 — Answer generation with enforced citation The prompt is constructed with a strict separation between instructions and retrieved content. Retrieved content is enclosed in a delimited block and explicitly designated as untrusted data, never as instruction.

The model is required to attach a source reference to each factual claim. Any statement produced without a valid source reference is removed before display.

Step 6 — Groundedness verification Before the answer is shown, it is decomposed into individual claims, and each claim is checked for support against the retrieved passages. Answers falling below the groundedness threshold are suppressed and replaced with the low-confidence response.

Step 7 — Confidence assessment and response If confidence is sufficient, the answer is displayed with its supporting references and links. If not, the chatbot states that it does not know and offers to escalate the question to the community forum or an administrator.

#### Confidence and Abstention

Abstention is treated as a first-class function rather than a fallback. Confidence is computed from a combination of signals:

Top retrieval relevance score

Score gap between the highest and second-highest ranked passages

Number of retrieved passages above a relevance floor

Groundedness verification score

Intent classifier confidence

These signals are combined by a small calibrated model that predicts whether the question is answerable from available content. The decision threshold is selected from a measured trade-off curve between answering incorrectly and refusing unnecessarily, rather than set arbitrarily.

When the chatbot abstains, it offers the user the option to post the question to the community forum, preserving the question text.

### Language Handling: English and Urdu-English

Roman Urdu has no standardised spelling. A single word commonly appears in many written forms, which causes keyword retrieval to fail and degrades semantic retrieval, since most multilingual models are trained predominantly on Urdu script rather than romanised Urdu.

The system handles this through a normalisation and matching layer applied before retrieval. Four approaches are implemented and compared:

Lexical normalisation — spelling variants are mapped to a canonical form using a variant dictionary, after which standard retrieval proceeds

Multilingual embeddings applied directly to the romanised text, without normalisation (baseline)

Query rewriting — the query is normalised or translated into English before retrieval against the English corpus

Phonetic matching — a phonetic encoding scheme for Roman Urdu is used alongside keyword retrieval to match variant spellings

The approach adopted in the final system is selected on measured retrieval performance rather than assumption, and mixed-language queries are supported throughout.

### Prompt Injection and Abuse Protection

Because forum content is indexed and later retrieved into the model's prompt, any user is able to write text that the chatbot may subsequently read. A user could post instructions intended to override the chatbot's behaviour or extract private information, and that content would enter the retrieval index like any other post. This is addressed at three layers:

Layer 1 — Ingestion screening Content is screened by the moderation classifier before it is admitted to the retrieval index. Injection-shaped content is flagged and withheld from indexing.

Layer 2 — Prompt isolation Retrieved content is enclosed in a delimited block and designated as data. System instructions state explicitly that content within this block is never to be treated as instruction.

Layer 3 — Output filtering Generated answers pass through a filter that removes phone numbers, exact addresses, identity document numbers, and other personal identifiers before display, regardless of what appeared in the retrieved content.

### Important Boundaries

The chatbot should not:

| Boundary | Enforced by |
| --- | --- |
| Invent event details | Citation enforcement and groundedness verification (Steps 5–6) |
| Make financial decisions | Out-of-scope intent classification and refusal |
| Guarantee the trustworthiness of a user | Trust queries return factor explanations only, never assurances |
| Reveal private user information | Output-time personal information filter (Layer 3) |
| Expose exact addresses | Output filter, and approximate location stored in place of exact address |
| Resolve disputes automatically | Dispute intents route to the administrator escalation path |
| Provide medical, legal, or financial advice as authoritative guidance | Out-of-scope intent classification and refusal |
| Answer from unapproved private chats | Private messages are excluded from the ingestion pipeline entirely |
| Answer from expired or withdrawn content | Validity window and state filters applied during retrieval (Step 3) |
| Answer using content from another community | Neighbourhood and visibility filters applied during retrieval (Step 3) |

Each boundary is enforced by a specific mechanism in the pipeline rather than by instruction to the model alone.

### Chatbot Features

Text chat

Conversation history

Suggested questions

Source links

"Was this helpful?" feedback

Report incorrect answer

Escalate to forum

Create a forum post from a question

Language support for English and Urdu-English mixed queries

Admin-managed knowledge base

Low-confidence fallback

Abuse and prompt-injection protection

Chatbot analytics

#### Administrative Controls

Approve, exclude, or pin individual knowledge sources

Review reported incorrect answers alongside the passages that produced them

View unanswered and abstained questions as a content gap report

Trigger re-indexing after knowledge base changes

Adjust abstention threshold

#### Analytics

Question volume by intent category

Abstention rate over time

Reported incorrect answers

Escalation rate to forum and administrator

Helpfulness rating distribution

Response latency distribution

Most frequent unanswered topics, used to identify missing content

### Chatbot FYP Evaluation

A test set of community questions is constructed with manually labelled expected answers and expected supporting sources.

#### Test Set Construction

Answerable set — questions distributed across all intent categories, each with a gold answer and the passages that should support it

Unanswerable set — questions with no supporting content in the corpus, used to measure whether the system correctly abstains

Language-parallel set — the same questions rendered in English, Roman Urdu, and mixed English-Urdu, with identical gold answers, so that the effect of language can be isolated from the effect of question difficulty

#### Evaluation Measures

Retrieval quality:

Recall at k and ranking quality, reported per intent category and per language variant

Answer quality:

Answer correctness against manually labelled expected answers

Groundedness in retrieved content

Relevance to the question asked

Completeness of the answer

Behaviour under uncertainty:

Abstention quality when information is unavailable

Rate of confident answers given where no supporting content existed

Rate of unnecessary refusal where an answer was retrievable

Correctness under change:

Rate of answers grounded in expired, withdrawn, or out-of-scope content

Language:

Urdu-English query handling, measured across the language-parallel set

System:

Response latency

User helpfulness rating

Security:

Resistance to prompt injection, measured against a constructed set of adversarial inputs covering instruction override, information extraction, and address disclosure

#### Comparisons

The following configurations are compared to establish which components contribute measurable benefit:

Keyword or FAQ search baseline

Semantic retrieval only

Hybrid retrieval (keyword and semantic combined)

Hybrid retrieval with reranking

Retrieval and generation are evaluated separately as well as end to end, so that an incorrect answer can be attributed to either a retrieval failure or a generation failure.

## 8. Communication & Notification

### Communication

One-to-one chat

Event group discussion

Item-request conversation

Organizer announcements

Community moderator messages

Media attachments

Report message

Block user

Read status, if feasible

### Notifications

Notify users about:

New matching item

Request accepted or rejected

Handover reminder

Return due date

Late return

Event registration

Event reminder

Event change or cancellation

Waitlist promotion

Forum reply

Best answer

Assurance-state update

Report resolution

Chatbot escalation response

For the FYP, in-app notifications and email or push notifications are enough. SMS and WhatsApp integration can be optional.

## 9. Small Businesses & Vendor Management

Post-defence scope note: vendor management is supporting or stretch scope. It is not part of the committed core.

### Overview

This module can support neighborhood businesses, but it should not become a second full marketplace.

### Core Features

Vendor registration

Business profile

Verification status

Service categories

Product or service listings

Operating area

Working hours

Contact or inquiry request

Reviews

Nearby vendor search

Vendor report

Trusted vendor badge

## 10. Administration & Moderation

### Administration

User management

Community management

Role assignment

Event approval

Listing moderation

Forum moderation

Vendor verification

Report management

Dispute management

Badge management

Content removal

Suspension and banning

Audit logs

Configuration of categories and rules

### AI-Assisted Moderation

Start with:

Profanity detection

Spam detection

Duplicate-content flagging

Suspicious link detection

Image-content flagging, if needed

## 11. Analytics And Reports

Post-defence scope note: broad analytics and the neighbourhood analysis are stretch scope. Completed borrowing transactions, reports and disputes, and the project evaluation metrics stay in the core.

### Admin Analytics

Active users

New registrations

Active neighborhoods

Listings created

Requests created

Match success rate

Completed borrowing transactions

Event registrations

Event attendance

Event cancellation rate

Forum activity

Chatbot questions

Unanswered chatbot questions

Reports and disputes

Assurance-state distribution

### User Analytics

Items listed

Items borrowed

Events joined

Events organized

Successful transactions

Contribution history

Reputation history

Personal community impact

### Neighbourhood Analysis

Purpose

Help prospective members decide whether a community is worth joining, and help people considering relocation compare areas. The audience is someone outside the community with no prior context.

Reported Metrics

Fulfilment rate — requests matched to an item, divided by total requests

Median time to first response

Median time to fulfilment

Category coverage — categories with active listings above a minimum count

Event cadence — events held per month

Event attendance rate — attended divided by registered

Forum answer rate — posts receiving at least one substantive reply

Median time to best answer

Ninety-day retention of new members — the strongest single indicator that a community is sustaining itself

Community Structure Measures

Activity totals do not distinguish a broadly participating community from one sustained by a few highly active members. The following are computed over the graph of completed interactions:

Interaction density

Share of members in the largest connected component

Concentration of contribution

Reciprocity ratio

Centralisation

A community in which a few members generate most activity is fragile, since it does not survive their departure. No total or average reveals this.

Statistical Treatment

Rates derived from few observations are adjusted toward the platform-wide average, so that a community with three transactions and no failures does not outrank one with several hundred

Metrics on different scales are normalised before combination

Composite rankings use weights set by the user rather than fixed by the system, since a household with young children and a single student value different things

Rankings are checked for stability under perturbation of the weights

Similar Community Search

Communities are compared on their metric profiles, allowing a user to specify a community they already know and receive comparable ones in a target area.

Constraints

The view reports activity and responsiveness only. Safety and dispute indicators are excluded by design, as comparative safety judgements about identifiable areas cannot be validated with available data and are readily gamed.

Metrics are suppressed below a minimum sample threshold, since in a small community an aggregate figure can identify an individual. An insufficient-data state is displayed instead.

Data Sources

Aggregated from events already recorded by other modules — transactions and outcomes, event registration and attendance, forum posts and replies, membership joins and departures. No new data collection is introduced. A shared event-logging schema is agreed across modules at the outset, since missing fields cannot be reconstructed retrospectively.

### Project Evaluation Metrics

Your FYP evaluation should distinguish:

System testing

Technical evaluation

User acceptance

Potential measures include:

Matching precision or successful-match rate

Event registration completion time

Borrowing workflow completion

Chatbot answer correctness and groundedness

Response latency

Task completion rate

Usability score

Trust-confidence change

Error and failure rate

Successful installation and deployment

### Technical Evaluation and Ablation Studies

The trust system will be evaluated against progressively more sophisticated baselines
rather than only demonstrating that the system produces a score.

#### Baselines

Global average

Role-specific average

Recency-weighted average

Recency-weighted Beta posterior without indirect evidence

Direct transaction history only

Direct + Bayesian uncertainty

Direct + k-hop indirect trust

Full system with uncertainty, indirect evidence, manipulation detection, and context-aware decision policy

#### Evaluation Metrics

The evaluation should consider:

Precision

Recall

F1-score where applicable

Brier score

Log loss

Credible-interval coverage and calibration

False-positive rate

False-negative rate

Escalation precision and recall

Coverage and latency for \(k=1,2,3,4\)

Sensitivity to half-life, hop decay, and indirect-reliability cap

Evaluation must use time-ordered holdout data: each transaction is predicted using only
evidence available before that transaction, and the outcome is revealed afterward.
Accuracy or an 80% performance claim must not be reported unless it is measured on the
held-out data.

Coverage

Decision accuracy

Response latency

Computational cost

Fairness across new and established users

Post-defence metrics to report in addition to the above:

False trust rate

False suspicion rate

Appropriate abstention

Manipulation-detection rate

Decision consistency

Moderator workload

Dispute-resolution time

User understanding and perceived fairness

Location-verification error

Privacy acceptability

#### Ablation Study

The full system will be compared against versions with individual components removed:

Full system

Without Bayesian uncertainty

Without transitive trust

Without manipulation detection

Without context-aware policy

This will determine whether each technical component provides measurable value rather than assuming that additional complexity automatically improves the system.

#### Hyperparameter Sensitivity

Initial parameters such as:

Maximum graph depth

Path decay factor

Indirect-trust confidence cap

Rating-velocity threshold

Reciprocal-rating threshold

New-account window

will be treated as experimental parameters.

Different values will be tested to determine their effect on accuracy, coverage, latency, and false-positive behavior.

The final values will therefore be based on experimental evidence rather than arbitrary selection.

### Datasets and Evaluation Data

#### Primary Dataset — Custom Neighborhood Dataset

A custom dataset will be developed to represent the characteristics of neighborhood-based interactions.

The proposed dataset includes:

Approximately 50–100 users

Approximately 200–300 borrowing transactions

Community relationship/network information

Transaction outcomes

Ratings and reviews

Dispute scenarios

Controlled manipulation scenarios

The dataset will be used to evaluate sparse evidence, indirect trust, cold-start behavior, and manipulation detection.

Where real participants are involved, data collection will require appropriate consent, privacy protection, and ethical handling.

#### Secondary Dataset — Epinions

Epinions may be used as an external trust-network benchmark because it contains a large number of ratings and a trust relationship network.

Its main purpose is comparative evaluation rather than direct simulation of Pakistani neighborhood borrowing.

#### Controlled Manipulation Scenarios

Controlled scenarios will be created for cases such as:

Reciprocal rating rings

New-account rating bursts

Highly similar reviews

Coordinated account behavior

Shared infrastructure where legitimately available

These scenarios will be explicitly identified as controlled or synthetic test cases and will not be presented as equivalent to real-world fraud data.

#### Post-Defence Evaluation Scenarios

Each scenario has an expected assurance state and a documented justification. The states below are the team's starting position and are confirmed or revised when the decision table is fixed in design step A5. The first six scenarios and the proposed thirteenth are implemented first.

| Scenario | Expected state | Justification |
| --- | --- | --- |
| New user with no history | INSUFFICIENT_EVIDENCE | No verified history. The user is not treated as risky; lender review is required. |
| Consistently reliable participant | SUFFICIENT_EVIDENCE | Many completed, on-time, confirmed transactions and no unresolved disputes. |
| Reliable participant with one recent dispute | REVIEW_RECOMMENDED | Strong history, but a recent dispute lowers assurance and a person should look at it. If the dispute is still open the state is ACTIVE_DISPUTE. |
| Colluding participants | REVIEW_RECOMMENDED | Reciprocal, similar, closely timed positive ratings receive low weight and the anomaly is shown to a moderator without accusation. |
| Retaliatory review | REVIEW_RECOMMENDED | The negative rating follows the other party's complaint and conflicts with the confirmed records, so it is flagged for review. |
| High-value request with weak evidence | REVIEW_RECOMMENDED | History exists but is dissimilar to the requested value, so lender or moderator review and safeguards are needed. |
| Conflicting condition reports | ACTIVE_DISPUTE | The parties disagree about condition and the case is unresolved until a moderator decides. |
| Failure to return an item | ACTIVE_DISPUTE | The item is overdue after reminders and extension, a dispute is open and the moderator receives the evidence trail. |
| Location mismatch | REVIEW_RECOMMENDED | Location evidence conflicts with the claimed community. GPS can be wrong, so there is no automatic rejection. |
| Location-permission refusal | INSUFFICIENT_EVIDENCE | Locality could not be verified by the location method. This is not a negative finding and another verification route is needed. |
| Moderator reversal | REVIEW_RECOMMENDED | An earlier decision was reversed. Both decisions stay in the log and the affected evidence is flagged until re-evaluated. |
| Insufficient evidence (sparse or old history) | INSUFFICIENT_EVIDENCE | Only a few transactions, or evidence too old or too dissimilar, so the system abstains and asks for human review. |
| Proposed ES-13: history with other members, none with this lender, reachable through community paths | To be set in design step A5 | Exercises bounded k-hop indirect evidence; indirect evidence alone cannot produce SUFFICIENT_EVIDENCE (section 5.11). |

## 16. Research Grounding & Academic Positioning

Digital Mohalla's technical design is research-informed rather than based only on implementation preferences. The selected approaches are mapped to established work and will be validated experimentally during development.

### 16.1 Trust Estimation

| Research Area | Reference | Relevance to Digital Mohalla |
| --- | --- | --- |
| Trust propagation | Golbeck (2005) | Indirect trust and trust propagation |
| Multi-dimensional reputation | Malik et al. (2009) | Role-specific reputation |
| Trust and uncertainty | Bhattacharya & Devinney (1998) | Distinguishing trust/risk from uncertainty |
| Subjective Logic | Jøsang (2016) | Representation of belief and uncertainty |
| Network opinion dynamics | Hegselmann & Krause (2002) | Community influence and evidence decay |

### 16.2 Graph Analysis and Manipulation Detection

| Research Area | Reference | Relevance |
| --- | --- | --- |
| Graph anomaly detection | Akoglu et al. (2015) | Suspicious rating structures |
| Anomalous links | Liu et al. (2010) | Unusual interaction/rating behavior |
| Malicious users | Ferrara et al. (2014) | Coordinated or automated account behavior |
| Weighted graph analysis | Goldenberg et al. (2010) | Statistical analysis of graph structures |

### 16.3 Recommendation and Cold Start

| Research Area | Reference | Relevance |
| --- | --- | --- |
| Collaborative filtering | Koren et al. (2009) | Future recommendation extensions |
| Hybrid recommendation | Burke (2002) | Combining multiple recommendation signals |
| Cold-start recommendation | Schein et al. (2002) | New-user handling |
| Explainability | Ribeiro et al. (2016) | Evidence-based explanations |

### 16.4 Evaluation

| Research Area | Reference | Relevance |
| --- | --- | --- |
| Recommendation evaluation | Herlocker et al. (2004) | Precision, recall and coverage |
| Multi-dimensional evaluation | Kunkel et al. (2019) | Coverage, diversity and broader evaluation |
| Fairness in ranking | Sapiezynski et al. (2019) | Fairness and exposure analysis |

#### Research-to-Design Principle

These references are not included only as a bibliography. Their concepts will influence algorithm selection, assumptions, evaluation metrics, and comparison baselines.

The team will document where an approach is reproduced, adapted, simplified, or experimentally modified for the Digital Mohalla context.

## 11. UI & UX

This section covers user interface and user experience design considerations for the Digital Mohalla platform. Key areas to focus on:

(Detailed specifications to be added)

Post-defence additions:

Resident application: create a request, view the evidence summary and its explanation, accept or decline as lender, confirm handover, confirm return and condition, open a dispute

Moderator interface: review queue, evidence trail for each case, decision entry with a recorded reason

Any screen that shows an assurance state also shows the evidence behind it, and never a single trust number

Usability and perceived-fairness testing with real residents

## 12. Deployment

This section covers deployment strategies and infrastructure requirements for the Digital Mohalla platform. Key considerations:

(Detailed specifications to be added)

Post-defence additions:

Pilot with real residents and a moderator. Communities and size to be decided before the FYP-2 pilot.

Hosting and installation details [to be specified]

## 13. Testing & Debugging

This section covers testing strategies, debugging approaches, and quality assurance for the Digital Mohalla platform. Key areas:

(Detailed specifications to be added)

Post-defence additions:

State machine: invalid transitions, concurrent requests and replay of the event log

Locality verification cases listed in section 1

Manipulation cases in section 5.13 and the evaluation scenarios

Privacy checks that exact location is not exposed in profiles, listings or logs

## 14. Design & Analysis

This section covers system design, architecture analysis, and technical design decisions for the Digital Mohalla platform. Key areas:

(Detailed specifications to be added)

Post-defence additions:

Event-sourced architecture (section 3) and the assurance pipeline (section 5)

Privacy and security design: location data minimisation, authorisation for every transition, audit log

Decisions to record: location verification method, prior parameters, decay rate and thresholds

## 15. Documentation

This section covers documentation requirements and guidelines for the Digital Mohalla platform. Key areas:

(Detailed specifications to be added)

Post-defence additions:

Locality method comparison and the results of the six locality test cases (in place of interview records)

Evaluation scenario document with the expected state and justification for each scenario

Threat model and the results of its controlled test cases
