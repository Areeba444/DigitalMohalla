# Assurance Data Dictionary (engine contract, Module 5)

| Field | Value |
|---|---|
| Owner | Student 2 (engine contract); §5 mapping added in integration |
| Version | 1.1, 11 October 2026. v1.0 (Student 2): engine classes and enumerations. v1.1 (integration, decision D14): §5 maps every contract field and enumeration to the persisted schema (`schema.sql` v2.3, `Data_Dictionary.md`); the Phase 3 merge points are closed there |
| Status | Awaiting Student 2's confirmation of §5 and A14 review |
| Companion | `Data_Dictionary.md` (A4, persisted columns, generated from the database) |

This is the Student 2 contribution to the full Digital Mohalla domain model: the in-memory contract of the assurance engine. The persisted form of the same data is the A4 data dictionary; §5 below maps one onto the other.

## Ownership and persistence conventions

- `OutcomeEvent` is immutable evidence. It is not edited after creation.
- Trust estimates, paths, manipulation assessments and decisions are derived
  values. They can be recomputed when parameters change.
- Identifiers reference the shared domain entities; the assurance module does
  not duplicate the complete `User`, `Item`, `Transaction` or `Dispute` model.
- Decimal values representing probabilities, weights or scores are bounded as
  stated below.
- All timestamps are timezone-aware.
- **Naming convention:** Domain entities and classes use standard OOP `camelCase` 
  properties; serialization payloads and Python engine contracts use corresponding 
  `snake_case` fields (e.g. `subjectId` $\leftrightarrow$ `subject_id`).

## Core assurance entities

| Class | Field | Type | Constraint / meaning |
|---|---|---|---|
| `OutcomeEvent` | `eventId` | String | Unique immutable evidence identifier |
| `OutcomeEvent` | `subjectId` | String | User whose behavior is measured |
| `OutcomeEvent` | `observerId` | String | User or system confirming the outcome |
| `OutcomeEvent` | `transactionId` | String | Source transaction identifier |
| `OutcomeEvent` | `role` | Role | Role in which the outcome is evaluated |
| `OutcomeEvent` | `metric` | Metric | Observable binary behavior |
| `OutcomeEvent` | `success` | Boolean | Bernoulli outcome |
| `OutcomeEvent` | `status` | EvidenceStatus | `CONFIRMED`, `DISPUTED` or `RESOLVED` |
| `OutcomeEvent` | `handoverConfirmed` | Boolean | Handover evidence exists |
| `OutcomeEvent` | `returnConfirmed` | Boolean | Return evidence exists |
| `OutcomeEvent` | `itemCategory` | String | Category used for context similarity |
| `OutcomeEvent` | `valueBand` | ValueBand | Risk/value grouping |
| `OutcomeEvent` | `durationDays` | Integer | Transaction duration; non-negative |
| `OutcomeEvent` | `occurredAt` | DateTime | Time of the measured outcome |
| `TrustEdge` | `sourceId`, `targetId` | String | Directed graph relationship |
| `TrustEdge` | `role`, `metric` | Enum | Graph edges are role- and metric-specific |
| `TrustEdge` | `weight` | Decimal | Inclusive range 0 to 1; derived, not a manual vouch |
| `TrustEdge` | `evidenceCount` | Integer | Non-negative supporting evidence count |
| `TrustEdge` | `updatedAt` | DateTime | Last derivation time |
| `TrustEstimate` | `subjectId` | String | Target user identifier |
| `TrustEstimate` | `role` | Role | Evaluated interaction role |
| `TrustEstimate` | `metric` | Metric | Measured behavior metric |
| `TrustEstimate` | `alpha`, `beta` | Decimal | Beta posterior parameters; positive |
| `TrustEstimate` | `mean` | Decimal | Posterior mean, range 0 to 1 |
| `TrustEstimate` | `lower90`, `upper90` | Decimal | Equal-tailed 90% credible interval |
| `TrustEstimate` | `effectiveSampleSize` | Decimal | Sum of recency/similarity weights (\(n_{\text{eff}}\)) |
| `TrustEstimate` | `directEventCount` | Integer | Count of eligible raw events |
| `TrustEstimate` | `computedAt` | DateTime | Derivation timestamp |
| `PathEvidence` | `nodes` | List<String> | Simple path node IDs, no cycles |
| `PathEvidence` | `hops` | Integer | 1 through configured maximum `k` |
| `PathEvidence` | `pathWeight` | Decimal | Path strength, range 0 to 1 |
| `IndirectTrustResult` | `requesterId` | String | Requesting user identifier |
| `IndirectTrustResult` | `targetId` | String | Target user identifier |
| `IndirectTrustResult` | `role`, `metric` | Enum | Role- and metric-specific context |
| `IndirectTrustResult` | `pathsUsed` | List<PathEvidence> | Candidate paths evaluated |
| `IndirectTrustResult` | `evidenceStrength` | Decimal | Noisy-OR path strength \(I\), range 0 to 1 |
| `IndirectTrustResult` | `reliability` | Decimal | Indirect confidence \(\rho\), capped at 0.6 initially |
| `IndirectTrustResult` | `diversity` | Decimal | First-hop diversity factor, range 0 to 1 |
| `IndirectTrustResult` | `estimate` | Decimal | Indirect estimate \(t_{\text{ind}}\), range 0 to 1 |
| `IndirectTrustResult` | `priorBacked` | Boolean | True when target has no direct evidence |

## Manipulation and decision classes

| Class | Field | Type | Constraint / meaning |
|---|---|---|---|
| `ManipulationSignal` | `name` | String | Explainable signal name |
| `ManipulationSignal` | `available` | Boolean | False means data was unavailable, not safe |
| `ManipulationSignal` | `value` | Decimal | Normalised signal value \(s_i\), range 0 to 1 |
| `ManipulationSignal` | `weight` | Decimal | Initial weights: 0.30, 0.20, 0.20, 0.20, 0.10 |
| `ManipulationSignal` | `evidence` | List<String> | Privacy-preserving supporting facts |
| `ManipulationRiskAssessment` | `score` | Decimal | Weighted score, capped at 100 |
| `ManipulationRiskAssessment` | `level` | RiskLevel | Four bands: 1, 2, 3 or 4 |
| `ManipulationRiskAssessment` | `signals` | List<ManipulationSignal> | Constituent signal evaluations |
| `ManipulationRiskAssessment` | `corroborated` | Boolean | At least two signals at or above 0.5 |
| `TransactionContext` | `itemValue` | Decimal | Non-negative transaction value |
| `TransactionContext` | `valueBand` | ValueBand | Low, medium or high |
| `TransactionContext` | `isHighValue` | Boolean | True if item belongs to high-value band |
| `TransactionContext` | `mediumValue` | Boolean | True if item belongs to medium-value band |
| `TransactionContext` | `categoryRestricted` | Boolean | Whether category rules add restrictions |
| `TransactionContext` | `transactionType` | TransactionType | Borrow, lend or service |
| `TransactionContext` | `openDispute` | Boolean | Dispute precedence input |
| `TransactionContext` | `resolvedDisputes12m` | Integer | Recent resolved-dispute count |
| `TransactionContext` | `verificationLevel` | VerificationLevel | Current verification state |
| `TransactionContext` | `verificationOk` | Boolean | True if verification level satisfies policy |
| `TransactionContext` | `requestSimilarity` | Decimal | Similarity to prior evidence, range 0 to 1 |
| `SafeguardRecommendation` | `type` | SafeguardType | Recommended control |
| `SafeguardRecommendation` | `parameters` | Map<String, Any> | Configured amount, deadline or scope |
| `SafeguardRecommendation` | `reason` | String | Explainable reason |
| `DecisionPolicyResult` | `decision` | DecisionAction | Policy action |
| `DecisionPolicyResult` | `safeguards` | List<SafeguardRecommendation> | Zero or more controls |
| `DecisionPolicyResult` | `escalate` | Boolean | Human review required |
| `DecisionPolicyResult` | `ruleFired` | String | Deterministic rule identifier (e.g. R1..R9) |
| `EvidenceRecord` | `factor` | String | Displayed factor name |
| `EvidenceRecord` | `value` | String | Human-readable value |
| `EvidenceRecord` | `confidence` | Decimal | Factor confidence, range 0 to 1 |
| `EvidenceRecord` | `supportingEventIds` | List<String> | Evidence references |
| `AssuranceResult` | `state` | AssuranceState | State for one proposed transaction |
| `AssuranceResult` | `direct` | TrustEstimate | Direct Beta posterior estimate |
| `AssuranceResult` | `indirect` | IndirectTrustResult | Bounded k-hop indirect trust result |
| `AssuranceResult` | `manipulation` | ManipulationRiskAssessment | Manipulation risk evaluation |
| `AssuranceResult` | `decision` | DecisionPolicyResult | Applied policy action and safeguards |
| `AssuranceResult` | `explanation` | List<EvidenceRecord> | Factor-level explanation list |
| `AssuranceResult` | `computedAt` | DateTime | Derivation timestamp |

## Enumerations

- `Role`: borrower, lender, vendor, event organiser, forum contributor.
- `Metric`: returned on time, returned in good condition, handover reliability, transaction completion.
- `EvidenceStatus`: confirmed, disputed, resolved.
- `RiskLevel`: level 1 (0–19), level 2 (20–39), level 3 (40–59), level 4 (60–100).
- `AssuranceState`: sufficient evidence, review recommended, insufficient evidence, active dispute.
- `DecisionAction`: proceed, proceed with safeguards, request verification, restrict high value, escalate.
- `ValueBand`: low, medium, high.
- `TransactionType`: borrow, lend, service.
- `VerificationLevel`: unverified, basic_community, verified_identity.
- `SafeguardType`: security_deposit, handover_photos, return_date_fixed, identity_verification, public_place_handover, lender_review.

## Phase 3 merge points (status after integration, see §5)

1. Replace the external ID-only `User` reference with the team User entity.
2. Link `OutcomeEvent.transactionId` to the shared Transaction aggregate.
3. Link `TransactionContext` to the shared Item and transaction value model.
4. Link `openDispute` to the shared Dispute state rather than duplicating dispute status.
5. Confirm enum names and value-band thresholds with the shared ER diagram.
6. Keep assurance outputs derived and avoid adding a permanent global “trust score” to `User`.

Status: points 1 to 5 are resolved by the mapping in §5 (decision D14); point 6 holds: no table stores a global trust score (`schema.sql` has none, and the assessment row is per request).

## 5. Mapping: engine contract ↔ persisted schema (decision D14)

The database spelling (upper case enums, snake_case columns) is the persisted, frozen spelling. The engine uses the snake_case names on the left; the adapter in Module 5 converts at the `assess()` boundary and in the outcome extractor.

### 5.1 Classes and fields

| Engine contract | Persisted as | Note |
|---|---|---|
| `AssuranceResult.state` | `assessment.assurance_state` | same four values |
| `AssuranceResult.decision.decision` | `assessment.policy_decision` | same five values |
| `DecisionPolicyResult.ruleFired` | `assessment.rule_fired` | R1–R5, R6_DISPUTE, R6_SPARSE, R7–R9; checked against the decision table |
| `DecisionPolicyResult.holdReason` | `assessment.hold_reason` | R2 → `manipulation_risk`, R4 → `high_value_low_confidence`, otherwise null |
| `DecisionPolicyResult.safeguards` | `assessment.safeguards` (jsonb array) | `SafeguardRecommendation` objects |
| `TrustEstimate.mean`, `lower90`, `upper90`, `effectiveSampleSize` | `assessment.posterior_mean`, `ci90_low`, `ci90_high`, `effective_evidence` | role and metric of the request |
| `TrustEstimate` (whole), `directEventCount` | `assessment.direct_evidence` (jsonb) | |
| `IndirectTrustResult` (paths, I, ρ, estimate, priorBacked) | `assessment.indirect_evidence` (jsonb) | written by Student 1's `IndirectTrustEngine` |
| `ManipulationRiskAssessment.score`, `level`, `corroborated` | `assessment.manipulation_risk`, `manipulation_level`, `manipulation_corroborated` | level checked against the bands and ADR-0007 |
| `ManipulationRiskAssessment.signals` | `assessment.manipulation_signals` (jsonb) | evidence, never accusations |
| `AssuranceResult.explanation` (`EvidenceRecord` list) | `assessment.explanation` (text) plus the jsonb columns above | the text is rendered from the records |
| `AssuranceResult.computedAt`, `configVersion` | `assessment.generated_at`, `config_version` | NFR-D-01 |
| `OutcomeEvent` | `outcome` row | `subjectId` → `subject_id`, `observerId` → `observer_id`, `transactionId` → `transaction_id`, `success`, `occurredAt` → `occurred_at`, `itemCategory` → `category_id`, `valueBand` → `value_band`, `durationDays` → `loan_duration` (interval) |
| `OutcomeEvent.handoverConfirmed`, `returnConfirmed` | implied: an outcome row exists only after `transaction_closed` (both confirmations recorded) or `dispute_resolved` | FR-T-03 |
| `TrustEdge` | `trust_edge` row | `evidenceCount` → `evidence_count`, `updatedAt` → `updated_at`; weight rule ADR-0006 |
| `TransactionContext` | derived at request time from `item`, `category`, `borrowing_transaction`, `escalation_case` | not stored; `openDispute` = a live DISPUTE case for either party |

### 5.2 Enumerations

| Engine enum | Persisted enum | Mapping |
|---|---|---|
| `EvidenceStatus` confirmed / disputed / resolved | `outcome_status` VALID / FLAGGED_FOR_REEVALUATION, plus the source event | confirmed = VALID from `transaction_closed`; resolved = VALID from `dispute_resolved`; disputed = no outcome row yet (the loan is DISPUTED); flagged outcomes are excluded (ES-11) |
| `Metric` returned on time / returned in good condition / transaction completion / handover reliability | `outcome_metric` ON_TIME_RETURN / CONDITION_AGREED / DISPUTE_FREE / — | handover reliability needs `no_show` (iteration 2) and is added then; Student 2 to confirm the list |
| `Role` borrower / lender (vendor, organiser, contributor: later modules) | `party_role` BORROWER / LENDER | iteration 1 has only the two loan roles |
| `ValueBand` low / medium / high | `value_band` LOW / MEDIUM / HIGH | PKR thresholds in the config: LOW ≤ 5,000, MEDIUM ≤ 15,000, HIGH > 15,000 (VERY_HIGH removed) |
| `VerificationLevel` unverified / basic_community / verified_identity | `verification_level` UNVERIFIED / CONTACT_VERIFIED / COMMUNITY_VERIFIED | basic_community = COMMUNITY_VERIFIED; verified_identity is not used in iteration 1 (FR/NFR I-9 open; no identity documents are stored, NFR-S-07) |
| `RiskLevel` 1–4 | `assessment.manipulation_level` 1–4 | same bands; level 4 needs corroboration (ADR-0007) |
| `AssuranceState`, `DecisionAction` | `assurance_state`, `policy_decision` | identical values |
| `SafeguardType` | entries of `assessment.safeguards` and `moderator_decision.safeguards` | free list in jsonb; names as in this dictionary |
| `TransactionType` borrow / lend / service | — | iteration 1 handles borrowing only |

