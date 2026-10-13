# **Digital Mohalla – A Trust-Based Platform for Neighbors**

**Final Year Project (Stream B – Application Derived)** Supervisor: Dr. Ali Zeeshan Team: Areeba Javed (23i-0570), Minahil Kashif (23i-0554), Fatima Khursheed (23i-0746)

## **1\. Overview**

Digital Mohalla is a neighborhood platform that helps residents share resources, ask for help, find local services and join community activities, with trust as its core infrastructure. The project's guiding idea is that trust is the missing infrastructure of neighborhood life.

The platform connects local needs (resources, help, services) to local interaction (sharing, seeking help, finding services, joining activities), supported by a trust and safety layer (trust estimation, risk detection, manipulation detection), and ultimately produces community connection: safer exchanges, repeat interaction and stronger reciprocity.

## **2\. Problem Statement**

### **2.1 Trust at neighborhood scale**

Trust works very differently in a neighborhood than on traditional online platforms.

| Traditional platforms | Neighborhood reality |
| :---- | :---- |
| Abundant evidence | Sparse evidence |
| One-time interactions | Repeated relationships |
| Easy user exit | No easy exit |

### **2.2 The hard part**

Two difficulties make neighborhood trust hard to model:

* **Unknown ≠ unreliable.** A person with no history is not necessarily a risky person.  
* **Legitimate groups ≈ manipulation rings.** A real friend group can look statistically similar to a coordinated fake-rating ring.

### **2.3 Who faces the problem**

* **Newcomers:** have no connections or reputation and find it hard to become visible.  
* **Community members:** have resources and skills but do not know who needs them, and hesitate to interact with unfamiliar people.  
* **Residents:** face everyday local problems, and existing solutions remain fragmented.

### **2.4 The gap: willingness exists, infrastructure doesn't**

Survey evidence cited in the project shows people are open to sharing with neighbors:

* 53% are open to borrowing (YouGov "Daily Questions" survey, 15–18 March 2024, n \= 35,878 U.S. adults).  
* 75% are willing to lend and 80% are open to neighbors (Silesian University of Technology, "Propensity of Generation Z to Share", 2024).

## **3\. Sustainable Development Goal Alignment**

* **SDG 12 – Responsible Consumption & Production:** resource sharing, reuse behavior, waste reduction, local circulation.  
* **SDG 11 – Sustainable Cities & Communities:** inclusive neighborhoods, safe interaction, trust infrastructure, repeated engagement, community bonds.

## **4\. Comparison with Existing Products**

Legend: ✓ supported, \~ partially supported, ✗ not supported.

### **4.1 Against existing market products**

| Feature | Digital Mohalla | OLX / Facebook | WhatsApp & kameti apps | Nextdoor | Peerby / Fat Llama |
| :---- | :---- | :---- | :---- | :---- | :---- |
| P2P lending | ✓ | ✓ | \~ | ✗ | ✓ |
| Kameti | ✓ | ✗ | ✓ | ✗ | ✗ |
| Structured, searchable community forum | ✓ | \~ | ✗ | ✓ | ✗ |
| Vendor marketplace | ✓ | ✓ | \~ | \~ | ✗ |
| Shared reputation | ✓ | \~ | ✗ | \~ | \~ |
| Trust-aware matching | ✓ | ✗ | ✗ | ✗ | \~ |
| Moderation workflow | ✓ | \~ | \~ | \~ | \~ |
| Unified neighborhood platform | ✓ | ✗ | ✗ | ✓ | ✗ |

### **4.2 Against prior FAST FYPs**

| Feature | Digital Mohalla | Kiraya (F22-071) | AIRental (F23-029) | Kitabiyat (S25-040) | PawPal (F25-101) |
| :---- | :---- | :---- | :---- | :---- | :---- |
| P2P lending | ✓ | \~ | ✓ | ✓ | ✗ |
| Kameti | ✓ | ✗ | ✗ | ✗ | ✗ |
| Structured, searchable community forum | ✓ | ✗ | ✗ | \~ | ✓ |
| Vendor marketplace | ✓ | \~ | ✗ | \~ | ✓ |
| Shared reputation | ✓ | ✗ | ✗ | ✗ | \~ |
| Trust-aware matching | ✓ | ✗ | \~ | \~ | ✗ |
| Moderation workflow | ✓ | ✗ | ✗ | ✗ | \~ |
| Unified neighborhood platform | ✓ | ✗ | ✗ | ✗ | \~ |

## **5\. Research Background (R\&D / Recent Technical Work)**

Each design decision is tied to published work.

| Finding | Source | Design consequence |
| :---- | :---- | :---- |
| One average score is not enough: averaged reputation hides uncertainty and is easy to game | Jøsang, Ismail & Boyd, *Decision Support Systems*, 2007 | Separate trust dimensions, each visible |
| Explanations are part of the output; they raise transparency and trust, not just accuracy | Zhang & Chen, *Foundations and Trends in Information Retrieval*, 2020 | Every match ships with its reason |
| Trust cues change behavior; profile photos alone shifted Airbnb booking decisions | Ert, Fleischer & Magen, *Tourism Management*, 2016 | Signals are chosen deliberately and tested for bias |
| Cold start is a policy, not a model; no algorithm recovers a history that does not exist | Schein et al., SIGIR 2002; Gil Pérez et al., *JCSS*, 2014 | Newcomers get a bounded starter tier |
| Ground the assistant: RAG answers carry provenance and update without retraining | Lewis et al., NeurIPS 2020; Karpukhin et al., EMNLP 2020 | Chatbot answers only from approved content, with citations |
| Digitising kameti is proven (80 Pakistani ROSCA users) | Mehmood et al., CSCW 2019 | Track contributions and turns; no smart contracts |

## **6\. Complex Computing Problem**

The project maps to the Seoul Accord characteristics of a complex computing problem.

| Characteristic | Digital Mohalla mapping |
| :---- | :---- |
| 1\. Conflicting requirements | Privacy vs. trust verification; fairness vs. optimal matching |
| 2\. No obvious solution / depth of analysis | Bayesian trust and fairness-constrained matching, not off-the-shelf |
| 3\. Depth of knowledge | Bayesian statistics, graph theory, optimization, NLP/IR |
| 4\. Unfamiliar issues | Collusion/manipulation detection, cold-start matching |
| 5\. Beyond standard practice | Keyword search and greedy matching fail; needs phased learning-to-rank plus fairness |
| 6\. Diverse stakeholders | Borrowers, lenders, organizers, vendors, moderators |
| 7\. Significant consequences | Safety and financial risk (trust errors); unequal access (unfair matching) |
| 8\. Interdependence | Matching depends on trust; trust depends on the transaction lifecycle |
| 9\. Ill-defined requirements | Trust, fairness and confidence thresholds are tuned experimentally |

## **7\. Our Contribution**

*A multi-layered trust system that quantifies uncertainty, propagates indirect trust, detects manipulation, and guides safe community decisions within neighborhood-based platforms.*

## **8\. System Architecture**

### **8.1 Module overview**

| Module | Role | Layer |
| :---- | :---- | :---- |
| M1 Transaction workflow | State machine and evidence log for handover and return | Workflow |
| M2 Trust estimation | Bayesian trust, per role | CCP core |
| M3 Indirect trust | Bounded k-hop graph propagation | CCP core |
| M4 Decision policy | Safeguards and human escalation | CCP core |
| M5 Manipulation detection | Detection ensemble | CCP core |
| M6 Semantic search and fair matching | FAISS item retrieval; bipartite matching with a fairness cap | Discovery |
| M7 Moderator console | Dispute resolution | Oversight and learning |
| M8 Evaluation harness | Simulation, baselines, ablations | Oversight and learning |
| M9 Platform | Auth, listings, notifications, chat, admin; deliberately minimal and never the contribution | Substrate |

Data flows from neighbors (lenders, borrowers, newcomers) into discovery (M6), which surfaces candidate matches. The decision core (M2, M3, M5 feeding M4) produces a recommended action. The assured workflow (M1) records handover and return evidence. Disputes and outcomes reach the moderator console and evaluation harness (M7, M8), and the outcomes recalibrate trust (M2) and thresholds (M4).

**Technology stack:** Python, FastAPI, PostgreSQL, FAISS, scikit-learn / LightGBM.

### **8.2 Solution architecture groupings**

* **Core modules:** User & Community Management; Resource Sharing & Item Management; Vendors Management; Admin & Moderation; Analytics & Reporting.  
* **Trust & intelligence:** Search, Discovery & Matching; Trust, Reputation & Safety.  
* **Community engagement:** Community Events & Activities; Communication & Notifications; Community Forum & Chatbot.

## **9\. Computational Core**

### **9.1 Trust & reputation**

The pipeline has four stages:

1. **Trust evidence:** transaction outcomes, role-specific behavior, recency and history.  
2. **Bayesian estimation:** a trust distribution with confidence/uncertainty and credible intervals.  
3. **Graph inference:** k-hop propagation, distance decay and multi-path evidence.  
4. **Decision policy:** trust plus risk, context-aware safeguards, with outcomes of proceed, verify or escalate.

The stated engineering complexity covers integration, scalability, manipulation resistance and validation.

### **9.2 Other computational components**

* **Search & matching:** hybrid semantic and keyword retrieval, multi-factor ranking, learning-to-rank, fair allocation.  
* **RAG / chatbot:** query routing, hybrid retrieval and reranking, grounded generation, abstention.  
* **Neighborhood analytics:** graph metrics, statistical normalisation, community comparison, stability analysis.

## **10\. Proof of Concept (POC-Lite)**

The POC-Lite is a mobile-style interface for a sample sector (F-7, Islamabad) with a radius filter (2 km, 3 km, 5 km, 10 km, All). Its main elements are:

* A home screen with a user trust badge (for example a 4.8 / 5 rating over 20 transactions with an "On-Time Verified" tag) and a prompt to confirm a pending handover.  
* Quick actions to find items (borrow and rent), post an item (free or paid) and create an event.  
* Community groups such as Gardening & Plants, Parenting Circle and Crochet & Crafts.  
* Recently posted items labelled Borrow or Rent, with distance and price (for example Rs 250/day).  
* Upcoming community events with capacity and registration.  
* Neighbor requests ("Looks to borrow") with an "I Have This" response.  
* Suggested verified local vendors with ratings.  
* Bottom navigation: Home, Search, Communities, Events, Forum, Profile.

## **11\. Evaluation Plan**

### **11.1 Approach**

The evaluation moves from public data to component testing, then synthetic data, then a pilot. As the team puts it, no single dataset represents the whole problem: each dataset validates a specific technical component, while synthetic and pilot data support end-to-end evaluation.

### **11.2 Three evaluation dimensions**

| Dimension | What is tested |
| :---- | :---- |
| Algorithmic | The system against a simple-average baseline; accuracy and fairness |
| Robustness | Five fraud scenarios (fake rings, rating bursts) and one legitimate friend group that should not be flagged; false positive rate |
| Acceptance | 30–50 real pilot participants; 10 users shown an explanation to check understanding; task completion rate; System Usability Scale (SUS) |

### **11.3 Success targets**

* ≥ 70% accuracy  
* \< 5% false positives  
* ≥ 60% of new users complete a first transaction  
* 8 of 10 users understand the recommendation

### **11.4 Datasets**

**Primary evaluation datasets**

1. Algorithmic: Bitcoin OTC trust network (Stanford SNAP, soc-sign-bitcoinotc).  
2. Robustness: YelpChi, obtained via the CARE-GNN repository.  
3. Acceptance: System Usability Scale (SUS).

**Other datasets researched**

* Epinions / CiaoDVD: trust links and ratings, for trust and graph propagation.  
* LETOR / MSLR-WEB10K: query–document relevance data, for search and ranking evaluation.  
* Pakistan UC Boundaries: real neighborhood polygons, for location-based matching.  
* Synthetic transaction dataset: users, listings and transactions, for controlled end-to-end testing and manipulation scenarios.

## **12\. Risks and Mitigation**

| Risk | Mitigation |
| :---- | :---- |
| Small dataset limits statistical significance | Use the Epinions benchmark and report results with confidence intervals |
| Simulation gap: synthetic vs. real fraud | Pilot validation and added scenario variants |
| False positives block legitimate users | Tune detection thresholds iteratively |
| Pilot recruitment shortfall (fewer than 30 users) | University recruitment and UAT |

## **13\. Iteration Plan**

The project runs from August to June in four iterations.

| Iteration | Period | Focus |
| :---- | :---- | :---- |
| Iteration 1 | Aug–Oct | Design & analysis begins; testing and documentation start |
| Iteration 2 | Nov–Jan | Vendor management, community events, resource sharing and item management, search/discovery/matching and trust/reputation/safety begin |
| Iteration 3 | Feb–Apr | Community forum and chatbot, communication and notifications, administration and analytics; deployment begins |
| Iteration 4 | May–Jun | Testing, deployment and documentation wrap-up |

UI & UX spans late Iteration 1 through Iteration 3\. Testing & Debugging and Documentation run almost the whole project.

## **14\. Work Division**

| Member | Responsibilities |
| :---- | :---- |
| Fatima Khursheed | Resource Sharing & Item Management; Search, Discovery & Matching (shared); Trust, Reputation & Safety (shared); Administration & Analytics (shared) |
| Areeba Javed | UI & UX; Trust, Reputation & Safety (shared); Search, Discovery & Matching (shared); Vendor Management; Communication & Notifications |
| Minahil Kashif | Community Events & Activities; Trust, Reputation & Safety (shared); Community Forum & Chatbot; Administration & Analytics (shared) |
| All members | Design & Analysis; Testing & Debugging; Documentation; Deployment |

## **15\. DEI, Ethics and Legal Considerations**

**Diversity, equity and inclusion**

* New ≠ untrusted.  
* Fair access.  
* Accessibility and explanations.  
* Human escalation.

**Ethics**

* Decision support, not automated judgement.  
* No auto-accusations.  
* Human review.  
* Evidence-based decisions.

**Legal and privacy**

* Approximate location only.  
* Minimal data collection.  
* Consent and deletion.  
* Aggregate reports.  
* Secure data.

## **16\. References**

1. Mehmood, H., Ahmad, T., Razaq, L., Mare, S., Usmani, M. Z., Anderson, R., & Raza, A. A. (2019). Towards digitization of collaborative savings among low-income groups. *Proceedings of the ACM on Human-Computer Interaction (CSCW)*, 3, Article 35\.  
2. Jøsang, A., Ismail, R., & Boyd, C. (2007). A survey of trust and reputation systems for online service provision. *Decision Support Systems*, 43(2), 618–644.  
3. Ert, E., Fleischer, A., & Magen, N. (2016). Trust and reputation in the sharing economy: The role of personal photos in Airbnb. *Tourism Management*, 55, 62–73.  
4. Zhang, Y., & Chen, X. (2020). Explainable recommendation: A survey and new perspectives. *Foundations and Trends in Information Retrieval*, 14(1), 1–101.  
5. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, 33, 9459–9474.  
6. Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W. (2020). Dense passage retrieval for open-domain question answering. *Proceedings of EMNLP 2020*, 6769–6781.  
7. Schein, A. I., Popescul, A., Ungar, L. H., & Pennock, D. M. (2002). Methods and metrics for cold-start recommendations. *Proceedings of the 25th Annual International ACM SIGIR Conference*, 253–260.  
8. Gil Pérez, M., Gómez Mármol, F., Martínez Pérez, G., & Skarmeta Gómez, A. F. (2014). Building a reputation-based bootstrapping mechanism for newcomers in collaborative alert systems. *Journal of Computer and System Sciences*, 80(3), 571–590.

**Survey data sources**

* YouGov (2024). "Daily Questions" survey. Fielded 15–18 March 2024 (n \= 35,878 U.S. adults).  
* Silesian University of Technology (2024). *Propensity of Generation Z to share*. Research report.