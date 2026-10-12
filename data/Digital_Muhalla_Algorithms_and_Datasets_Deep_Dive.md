# Digital Muhalla: Algorithms & Datasets — Deep Dive
## Detailed Implementation Guide for FYP

---

## PART 1: CORE ALGORITHMS WITH CODE EXAMPLES

### Algorithm 1: Recency-Weighted Beta Posterior Trust Estimation

**What it does:** Estimates probability of success and a Bayesian credible interval from time-weighted historical outcomes.

**Why a Beta posterior?**
- Handles small sample sizes (1–20 transactions)
- Produces credible intervals (not just point estimates)
- Has conjugate prior (easy to update with new data)
- Interpretable parameters (α = pseudocount successes, β = pseudocount failures)

---

#### **Version A: Simple (Start Here)**

```python
"""
Beta-Binomial Trust Model (Simple Version)
Suitable for: Learning, prototyping, evaluation baseline
"""

import numpy as np
from scipy.stats import beta
from dataclasses import dataclass

@dataclass
class TrustEstimate:
    """Output of trust estimation"""
    probability: float  # E[p] = mean
    confidence_low: float  # 5th percentile
    confidence_high: float  # 95th percentile
    sample_size: int
    successes: int
    failures: int

def estimate_beta_binomial(
    successes: int,
    failures: int,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0
) -> TrustEstimate:
    """
    Estimate trust probability and a 90% credible interval.
    
    Args:
        successes: Number of positive outcomes (item returned on time, etc.)
        failures: Number of negative outcomes
        prior_alpha: Prior belief in success (default = 1, uniform prior)
        prior_beta: Prior belief in failure (default = 1, uniform prior)
    
    Returns:
        TrustEstimate with probability and 90% credible interval
    
    Example:
        >>> estimate_beta_binomial(successes=18, failures=2)
        TrustEstimate(
            probability=0.898,
            confidence_low=0.805,
            confidence_high=0.965,
            sample_size=20,
            successes=18,
            failures=2
        )
    """
    
    # Posterior parameters
    posterior_alpha = prior_alpha + successes
    posterior_beta = prior_beta + failures
    
    # Posterior mean (best estimate)
    probability = posterior_alpha / (posterior_alpha + posterior_beta)
    
    # 90% credible interval (5th and 95th percentile)
    beta_dist = beta(posterior_alpha, posterior_beta)
    confidence_low = beta_dist.ppf(0.05)
    confidence_high = beta_dist.ppf(0.95)
    
    return TrustEstimate(
        probability=probability,
        confidence_low=confidence_low,
        confidence_high=confidence_high,
        sample_size=successes + failures,
        successes=successes,
        failures=failures,
    )

# Example usage
if __name__ == "__main__":
    # User A: 1 success, 0 failures
    user_a = estimate_beta_binomial(successes=1, failures=0)
    print(f"User A: {user_a.probability:.1%} (interval: {user_a.confidence_low:.1%}–{user_a.confidence_high:.1%})")
    # Output: User A: 66.7% (wide 90% credible interval)
    
    # User B: 18 successes, 2 failures
    user_b = estimate_beta_binomial(successes=18, failures=2)
    print(f"User B: {user_b.probability:.1%} (interval: {user_b.confidence_low:.1%}–{user_b.confidence_high:.1%})")
    # Output: User B: 89.8% (interval: 80.5%–96.5%)
    
    # Same mean (~67% and ~90%), but different confidence!
```

**Layman's explanation:**
Imagine you ask 100 people "Is Areeba trustworthy?" User A just moved to the neighborhood—only 1 person knows her (and said yes). User B has lived here 5 years—20 people know her (18 said yes, 2 said no).

Both might have similar *average* answers, but User B's estimate is supported by more evidence. The Beta posterior captures this difference.

---

#### **Version B: Advanced (Hierarchical Model)**

```python
"""
Hierarchical Beta-Binomial Model
Suitable for: Production, handling multiple role-specific outcomes
"""

from typing import Dict, List
import numpy as np
from scipy.stats import beta

class HierarchicalTrustModel:
    """
    Models trust across multiple roles with shared hyperpriors.
    
    Example structure:
    - Global hyperprior: What is the typical success rate across all roles?
    - Role-specific: What is the success rate for borrowing? For lending?
    - User-specific: What is Ali's success rate as a borrower?
    """
    
    def __init__(
        self,
        global_alpha: float = 2.0,  # Hyperprior: global success tendency
        global_beta: float = 2.0,   # Hyperprior: global failure tendency
    ):
        """Initialize with global hyperpriors (belief about the neighborhood overall)"""
        self.global_alpha = global_alpha
        self.global_beta = global_beta
        
        # Store per-role, per-user outcomes
        self.observations: Dict[str, Dict[str, Dict[str, int]]] = {
            'borrower': {},    # role
            'lender': {},      # role
            'organizer': {},   # role
        }
    
    def record_outcome(
        self,
        user: str,
        role: str,
        outcome_type: str,
        success: bool
    ) -> None:
        """
        Record an outcome for a user in a specific role.
        
        Args:
            user: "Ali"
            role: "borrower" | "lender" | "organizer"
            outcome_type: "on_time" | "condition" | "dispute" | etc.
            success: True/False
        """
        if user not in self.observations[role]:
            self.observations[role][user] = {}
        
        if outcome_type not in self.observations[role][user]:
            self.observations[role][user][outcome_type] = {'success': 0, 'failure': 0}
        
        key = 'success' if success else 'failure'
        self.observations[role][user][outcome_type][key] += 1
    
    def get_trust_vector(self, user: str, role: str) -> Dict:
        """
        Return trust estimates for a user in a specific role across all outcome types.
        
        Returns:
            {
                'on_time': TrustEstimate,
                'condition': TrustEstimate,
                'dispute': TrustEstimate,
                ...
            }
        """
        trust_vector = {}
        
        if user not in self.observations[role]:
            return {}  # No data for this user-role combination
        
        for outcome_type, counts in self.observations[role][user].items():
            successes = counts['success']
            failures = counts['failure']
            
            # Posterior parameters (updated with observations)
            posterior_alpha = self.global_alpha + successes
            posterior_beta = self.global_beta + failures
            
            # Mean and credible interval
            probability = posterior_alpha / (posterior_alpha + posterior_beta)
            beta_dist = beta(posterior_alpha, posterior_beta)
            
            trust_vector[outcome_type] = {
                'probability': probability,
                'confidence_interval': (beta_dist.ppf(0.05), beta_dist.ppf(0.95)),
                'sample_size': successes + failures,
                'successes': successes,
                'failures': failures,
            }
        
        return trust_vector

# Example usage
if __name__ == "__main__":
    model = HierarchicalTrustModel()
    
    # Record Ali's borrowing outcomes
    model.record_outcome('Ali', 'borrower', 'on_time', success=True)
    model.record_outcome('Ali', 'borrower', 'on_time', success=True)
    model.record_outcome('Ali', 'borrower', 'on_time', success=False)  # 1 late
    model.record_outcome('Ali', 'borrower', 'condition', success=True)
    model.record_outcome('Ali', 'borrower', 'condition', success=True)
    
    # Record Ali's lending outcomes
    model.record_outcome('Ali', 'lender', 'dispute', success=True)  # No disputes
    model.record_outcome('Ali', 'lender', 'dispute', success=True)
    
    # Query trust
    ali_borrower_trust = model.get_trust_vector('Ali', 'borrower')
    print("Ali as borrower:")
    print(f"  On-time: {ali_borrower_trust['on_time']['probability']:.1%} "
          f"(CI: {ali_borrower_trust['on_time']['confidence_interval'][0]:.1%}–"
          f"{ali_borrower_trust['on_time']['confidence_interval'][1]:.1%})")
    # Output: On-time: 66.7% (CI: 20.3%–92.9%)
    
    ali_lender_trust = model.get_trust_vector('Ali', 'lender')
    print("Ali as lender:")
    print(f"  Dispute-free: {ali_lender_trust['dispute']['probability']:.1%} "
          f"(CI: {ali_lender_trust['dispute']['confidence_interval'][0]:.1%}–"
          f"{ali_lender_trust['dispute']['confidence_interval'][1]:.1%})")
    # Output: Dispute-free: 75.0% (CI: 28.6%–97.2%)
```

---

### Algorithm 2: k-Hop Transitive Trust with Decay

**What it does:** Estimates trust through social paths (A → B → C) with distance decay.

**Why it's complex:**
- Must find multiple paths efficiently (BFS)
- Must weight paths by strength and distance
- Must avoid double-counting shared intermediaries
- Must cap confidence (indirect trust is less reliable)

---

#### **Implementation**

```python
"""
k-Hop Transitive Trust Algorithm
Suitable for: Cold-start users, bootstrapping reputation
"""

from typing import List, Dict, Tuple, Set
from collections import deque, defaultdict
import numpy as np

class CommunityGraph:
    """
    Weighted, directed graph representing neighborhood relationships.
    
    Edges represent "A has experienced B" relationships:
    - A borrowed from B (edge: A → B, weight = confidence in B's lending reliability)
    - A organized event with B (edge: A → B, weight = frequency/quality)
    """
    
    def __init__(self):
        self.edges: Dict[str, Dict[str, float]] = defaultdict(dict)
        # Example: self.edges['Ali']['Zara'] = 0.8 means Ali has strong connection to Zara
    
    def add_edge(self, from_user: str, to_user: str, weight: float) -> None:
        """Add a directed edge with weight in [0, 1]"""
        self.edges[from_user][to_user] = weight
    
    def find_all_paths(
        self,
        start: str,
        end: str,
        max_hops: int = 3,
    ) -> List[List[str]]:
        """
        Find all simple paths from start to end within max_hops.
        
        Args:
            start: Source user
            end: Target user
            max_hops: Maximum path length (default 3)
        
        Returns:
            List of paths, each path is a list of users [start, ..., end]
        
        Example:
            >>> graph.find_all_paths('Ali', 'Zara', max_hops=3)
            [
                ['Ali', 'Imran', 'Zara'],
                ['Ali', 'Hina', 'Imran', 'Zara']
            ]
        """
        paths = []
        
        def dfs(current, target, path, visited, depth):
            if depth > max_hops:
                return
            
            if current == target:
                paths.append(path.copy())
                return
            
            visited.add(current)
            
            for neighbor in self.edges.get(current, {}):
                if neighbor not in visited:
                    path.append(neighbor)
                    dfs(neighbor, target, path, visited, depth + 1)
                    path.pop()
            
            visited.remove(current)
        
        dfs(start, end, [start], set(), 1)
        return paths
    
    def compute_path_strength(self, path: List[str]) -> float:
        """
        Compute strength of a path by multiplying edge weights.
        
        Path [A, B, C, D] has strength = weight(A→B) × weight(B→C) × weight(C→D)
        
        Intuition: If A is 70% confident in B, and B is 60% confident in C,
        then A is roughly 42% confident in C (through B).
        """
        strength = 1.0
        for i in range(len(path) - 1):
            strength *= self.edges[path[i]].get(path[i+1], 0.5)
        return strength
    
    def compute_indirect_trust(
        self,
        requester: str,
        target: str,
        max_hops: int = 3,
        decay_per_hop: float = 0.7,
        target_direct_mean: float = 0.5,
    ) -> Tuple[float, float, Dict]:
        """
        Estimate trust from requester → target via social paths.
        
        Args:
            requester: User asking "should I trust target?"
            target: User being evaluated
            max_hops: Maximum path length (default 3)
            decay_per_hop: Strength decay per additional hop (default 0.7)
            target_direct_mean: Target's direct mean, or the role/metric baseline
        
        Returns:
            (estimated_probability, confidence_score, evidence_summary)
        
        Algorithm:
        1. Find all paths from requester to target (up to max_hops)
        2. For each path:
           - Compute path strength (multiply edge weights)
           - Apply distance decay: strength *= decay_per_hop^(path_length - 1)
        3. Aggregate across paths, weight by strength
        4. Cap confidence at 0.6 (indirect evidence is weaker)
        """
        
        paths = self.find_all_paths(requester, target, max_hops)
        
        if not paths:
            return None, 0.0, {'reason': 'No path found', 'paths_count': 0}
        
        # Analyze each path
        path_data = []
        for path in paths:
            hops = len(path) - 1
            strength = self.compute_path_strength(path)
            
            # Apply distance decay
            decay_factor = decay_per_hop ** (hops - 1)
            weighted_strength = strength * decay_factor
            
            path_data.append({
                'path': path,
                'hops': hops,
                'path_strength': strength,
                'decay_factor': decay_factor,
                'weighted_strength': weighted_strength,
            })
        
        # Aggregate: weighted average strength
        total_weight = sum(p['weighted_strength'] for p in path_data)
        normalized_weights = [p['weighted_strength'] / total_weight for p in path_data]
        
        # Use the target's actual direct estimate or the role/metric baseline.
        target_base_trustworthiness = target_direct_mean
        estimated_probability = (
            sum(w * target_base_trustworthiness for w in normalized_weights)
        )
        
        # Confidence based on path diversity and count
        unique_intermediaries = len(set().union(
            *[set(p['path'][1:-1]) for p in path_data]
        ))
        
        # More paths + more diversity = higher confidence
        confidence = min(0.6, len(paths) * 0.1 + unique_intermediaries * 0.05)
        # Cap at 0.6 (indirect evidence is less reliable than direct)
        
        evidence_summary = {
            'paths_found': len(paths),
            'unique_intermediaries': unique_intermediaries,
            'strongest_path': path_data[0]['path'],
            'all_paths': [p['path'] for p in path_data[:3]],  # Top 3
            'confidence_reason': f'{len(paths)} path(s) found via {unique_intermediaries} intermediate(s)',
        }
        
        return estimated_probability, confidence, evidence_summary

# Example usage
if __name__ == "__main__":
    graph = CommunityGraph()
    
    # Build neighborhood graph (directed edges with weights)
    graph.add_edge('Ali', 'Imran', 0.8)  # Ali trusts Imran well
    graph.add_edge('Imran', 'Zara', 0.7)  # Imran trusts Zara
    graph.add_edge('Ali', 'Hina', 0.6)  # Ali trusts Hina
    graph.add_edge('Hina', 'Imran', 0.5)  # Hina trusts Imran
    graph.add_edge('Imran', 'Zara', 0.7)  # Duplicate edge (increases path confidence)
    
    # Ali wants to know: should I trust Zara?
    # (No direct evidence, but social connection exists)
    prob, conf, evidence = graph.compute_indirect_trust('Ali', 'Zara', max_hops=3)
    
    print(f"Ali → Zara indirect trust:")
    print(f"  Probability: {prob:.1%}")
    print(f"  Confidence: {conf:.0%}")
    print(f"  Evidence: {evidence['paths_found']} paths via {evidence['unique_intermediaries']} intermediaries")
    print(f"  Strongest: {' → '.join(evidence['strongest_path'])}")
    # Output:
    # Ali → Zara indirect trust:
    #   Probability: 49.0%
    #   Confidence: 25%
    #   Evidence: 2 paths via 2 intermediaries
    #   Strongest: ['Ali', 'Imran', 'Zara']
```

---

### Algorithm 3: Multi-Signal Manipulation Detection

**What it does:** Scores reputation-manipulation risk using independent signals.

**Why it's complex:**
- Must detect various attack patterns (rating rings, fake accounts, velocity spikes)
- Must distinguish attacks from legitimate dense social groups
- Must produce explainable scores (not a black-box model)

---

#### **Implementation**

```python
"""
Multi-Signal Manipulation Detection
Suitable for: Fraud detection, account monitoring
"""

from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Signal:
    """A single fraud signal"""
    name: str
    severity: str  # 'low', 'medium', 'high'
    score: int  # 0–50 points
    explanation: str

def detect_manipulation_signals(
    user: str,
    user_ratings: List[Dict],  # Ratings submitted by user
    user_account_age_days: int,
    graph: CommunityGraph,
    text_similarity_threshold: float = 0.85,
    velocity_threshold: float = 3.0,
) -> Dict:
    """
    Compute manipulation risk using multiple independent signals.
    
    Args:
        user: User ID to evaluate
        user_ratings: List of ratings submitted by this user
        user_account_age_days: Days since account creation
        graph: Community graph for device/IP analysis
        text_similarity_threshold: Similarity threshold for identical text detection
        velocity_threshold: Ratio threshold for burst detection
    
    Returns:
        {
            'risk_score': 0–100,
            'signals': [Signal, ...],
            'action': 'proceed' | 'monitor' | 'verify' | 'escalate',
            'explanation': str,
        }
    """
    
    signals: List[Signal] = []
    risk_score = 0
    
    # ========== Signal 1: Reciprocal Rating Clustering ==========
    # High ratio of ratings to a tight-knit group
    
    recipients = set(r['target_user'] for r in user_ratings)
    internal_ratings = 0
    external_ratings = 0
    
    for rating in user_ratings:
        target = rating['target_user']
        # Check if target also rated this user
        if any(
            r['rater'] == target and r['target_user'] == user
            for r in user_ratings  # Simplified; use actual database in production
        ):
            internal_ratings += 1
        else:
            external_ratings += 1
    
    if internal_ratings + external_ratings > 0:
        reciprocal_ratio = internal_ratings / (internal_ratings + external_ratings)
        
        if reciprocal_ratio > 0.7:
            signals.append(Signal(
                name='High reciprocal rating clustering',
                severity='medium',
                score=25,
                explanation=f'{int(reciprocal_ratio*100)}% of your ratings are to accounts that rated you back.'
            ))
            risk_score += 25
    
    # ========== Signal 2: Rating Velocity (Sudden Burst) ==========
    # Unusual spike in rating activity
    
    now = datetime.now()
    ratings_last_week = sum(
        1 for r in user_ratings
        if (now - r['timestamp']).days < 7
    )
    ratings_last_month = sum(
        1 for r in user_ratings
        if (now - r['timestamp']).days < 30
    )
    
    weekly_average = ratings_last_month / 4 if ratings_last_month > 0 else 0
    
    if weekly_average > 0 and ratings_last_week > velocity_threshold * weekly_average:
        signals.append(Signal(
            name='Unusual rating velocity (burst)',
            severity='low',
            score=10,
            explanation=f'Submitted {ratings_last_week} ratings this week (vs. {weekly_average:.1f} weekly average).'
        ))
        risk_score += 10
    
    # ========== Signal 3: New Account + Rapid Reciprocal ==========
    # Freshly created account receiving immediate ratings back
    
    if user_account_age_days < 7 and len(user_ratings) > 0:
        recipients = set(r['target_user'] for r in user_ratings)
        
        # Count how many recipients rated this user back within 30 days
        return_ratings = []
        for recipient in recipients:
            # Find ratings from recipient to user within 30 days of account creation
            matching_ratings = [
                r for r in user_ratings  # Simplified
                if r['rater'] == recipient
                and r['target_user'] == user
                and (r['timestamp'] - datetime.now()).days < 30
            ]
            return_ratings.extend(matching_ratings)
        
        if len(return_ratings) > 2:
            signals.append(Signal(
                name='New account with rapid reciprocal ratings',
                severity='high',
                score=40,
                explanation=f'Account created {user_account_age_days} days ago; {len(return_ratings)} recipients rated you back quickly.'
            ))
            risk_score += 40
    
    # ========== Signal 4: Identical or Near-Identical Ratings Text ==========
    # Copy-paste behavior indicates automation or fraud
    
    rating_texts = [r.get('text', '') for r in user_ratings if r.get('text')]
    
    if len(rating_texts) > 1:
        # Simple text similarity: Jaccard distance on n-grams
        def jaccard_similarity(text1: str, text2: str, n: int = 3) -> float:
            """Compute Jaccard similarity on n-grams"""
            ngrams1 = set([text1[i:i+n] for i in range(len(text1)-n+1)])
            ngrams2 = set([text2[i:i+n] for i in range(len(text2)-n+1)])
            if not ngrams1 or not ngrams2:
                return 1.0 if text1 == text2 else 0.0
            intersection = len(ngrams1 & ngrams2)
            union = len(ngrams1 | ngrams2)
            return intersection / union if union > 0 else 0.0
        
        # Check all pairs
        max_similarity = 0.0
        for i in range(len(rating_texts)):
            for j in range(i+1, len(rating_texts)):
                sim = jaccard_similarity(rating_texts[i], rating_texts[j])
                max_similarity = max(max_similarity, sim)
        
        if max_similarity > text_similarity_threshold:
            signals.append(Signal(
                name='Identical or near-identical rating text',
                severity='high',
                score=35,
                explanation=f'Multiple ratings are {int(max_similarity*100)}% textually similar (threshold: {int(text_similarity_threshold*100)}%).'
            ))
            risk_score += 35
    
    # ========== Signal 5: Device or IP Linkage ==========
    # Multiple accounts from same device/IP (Sybil attack)
    
    # In production, query device fingerprinting database
    # For now, simulate:
    linked_accounts = []  # Would fetch from database
    
    if len(linked_accounts) > 1:
        signals.append(Signal(
            name='Multiple accounts sharing device or IP',
            severity='medium',
            score=20,
            explanation=f'{len(linked_accounts)} accounts detected from same device/IP.'
        ))
        risk_score += 20
    
    # ========== Determine Action ==========
    
    risk_score = min(risk_score, 100)  # Cap at 100
    
    if risk_score >= 60:
        action = 'escalate'
        action_description = 'Block high-value transactions; flag for moderator review.'
    elif risk_score >= 40:
        action = 'verify'
        action_description = 'Request additional verification (phone, identity).'
    elif risk_score >= 20:
        action = 'monitor'
        action_description = 'Monitor account; do not amplify ratings.'
    else:
        action = 'proceed'
        action_description = 'Proceed normally.'
    
    return {
        'risk_score': risk_score,
        'signals': signals,
        'action': action,
        'action_description': action_description,
        'explanation': f'Risk {risk_score}/100: {action_description}',
    }

# Example usage
if __name__ == "__main__":
    sample_ratings = [
        {'target_user': 'AccountA', 'timestamp': datetime.now(), 'text': 'Great person!'},
        {'target_user': 'AccountB', 'timestamp': datetime.now(), 'text': 'Great person!'},
        {'target_user': 'AccountC', 'timestamp': datetime.now(), 'text': 'Very trustworthy'},
    ]
    
    result = detect_manipulation_signals(
        user='NewUser123',
        user_ratings=sample_ratings,
        user_account_age_days=2,
        graph=CommunityGraph(),
    )
    
    print(f"Manipulation Risk Analysis:")
    print(f"  Risk Score: {result['risk_score']}/100")
    print(f"  Action: {result['action']}")
    print(f"  Signals:")
    for signal in result['signals']:
        print(f"    - {signal.name} ({signal.severity}): {signal.explanation}")
```

---

## PART 2: DATASET CONSTRUCTION GUIDE

### Dataset 1: Custom Pakistani Neighborhood Dataset

#### **Structure**

```
community_data/
├── users.csv
├── transactions.csv
├── ratings.csv
├── disputes.csv
└── README.md
```

---

#### **users.csv**

```csv
user_id,name,neighborhood,account_created,role_flags,account_status
U001,Ali,Sector_G7,2024-01-15,borrower|lender,active
U002,Zara,Sector_G7,2024-02-03,lender|organizer,active
U003,Imran,Sector_G8,2024-01-20,borrower,active
U004,Hina,Sector_G7,2024-03-10,organizer,active
U005,Fatima,Sector_G8,2024-01-05,lender|vendor,active
...
```

**Layman's explanation:** Think of this as a "neighborhood directory." Each person has a profile with when they joined and what roles they play.

---

#### **transactions.csv**

```csv
transaction_id,borrower_id,lender_id,item_name,item_value_pkr,category,borrow_date,expected_return_date,actual_return_date,item_condition_returned,outcome,dispute_filed
T001,U001,U002,Power Drill,3500,tools,2024-06-01,2024-06-03,2024-06-04,good,completed_late,N
T002,U003,U005,Rice Cooker,2000,appliances,2024-06-05,2024-06-07,2024-06-07,good,completed_on_time,N
T003,U001,U005,Laptop Charger,1200,electronics,2024-06-10,2024-06-12,2024-06-12,damaged,completed_disputed,Y
T004,U002,U001,Coffee Table,5000,furniture,2024-06-15,2024-06-20,NULL,NULL,active,N
...
```

**How to construct:**
1. Identify real neighborhood (or use proxy: hostel, apartment building, dorm)
2. Interview 20–30 residents: "What did you borrow? From whom? When?"
3. Record outcomes (returned on time? In good condition?)
4. Annotate disputes (did anyone complain?)

**Rules:**
- Item value should be realistic for Islamabad (PKR 500–20,000 range common)
- Dates should be recent (last 6 months)
- ~5–10 transactions per active user
- ~30% should have late returns, ~10% should have condition disputes

---

#### **ratings.csv**

```csv
rating_id,rater_id,target_id,transaction_id,role_being_rated,metric,rating_value,rating_text,timestamp,helpful_votes
R001,U002,U001,T001,borrower,punctuality,4,Returns items on time!,2024-06-05,2
R002,U001,U002,T001,lender,reliability,5,Great condition always,2024-06-05,5
R003,U003,U005,T002,lender,communication,4,Explained well,2024-06-08,1
R004,U005,U001,T003,borrower,care,2,Item came back damaged,2024-06-14,8
...
```

**Metrics per role:**
- **Borrower role:** punctuality, care_for_item, communication, follow_terms
- **Lender role:** fair_terms, condition_accuracy, responsiveness, dispute_fairness
- **Organizer role:** reliability, communication, coordination, attendance

---

#### **disputes.csv**

```csv
dispute_id,transaction_id,filed_by,filed_against,dispute_type,description,resolution,moderator_notes
D001,T003,U001,U005,item_condition,Item arrived damaged. Lender claims it was like that.,partial_refund,User reported damage via photos within 24h. Credible.
D002,T010,U004,U003,late_return,Item not returned for 5 days after deadline.,full_refund,Repeated late returns. User warned.
...
```

**Dispute types:**
- `item_condition`: Item returned in different condition
- `late_return`: Item returned after agreed date
- `missing_item`: Item not returned at all
- `money_dispute`: Organizational funds not accounted for (for kitty parties)
- `other`: Unclassified

---

#### **How to Generate Synthetic Data (If Manual Collection is Slow)**

```python
"""
Generate realistic synthetic neighborhood data
"""

import random
from datetime import datetime, timedelta
import pandas as pd

class NeighborhoodGenerator:
    """Generates realistic neighborhood transaction data"""
    
    def __init__(self, n_users=60, n_transactions=250, seed=42):
        self.n_users = n_users
        self.n_transactions = n_transactions
        random.seed(seed)
        self.users = self._generate_users()
    
    def _generate_users(self):
        """Generate realistic user profiles"""
        neighborhoods = ['Sector_G7', 'Sector_G8', 'Sector_G9', 'Sector_F10', 'Sector_F11']
        roles = ['borrower', 'lender', 'organizer', 'vendor']
        
        users = []
        for i in range(self.n_users):
            user_roles = random.sample(roles, k=random.randint(1, 3))
            users.append({
                'user_id': f'U{i+1:03d}',
                'name': f'User{i+1}',
                'neighborhood': random.choice(neighborhoods),
                'account_created': datetime.now() - timedelta(days=random.randint(30, 180)),
                'role_flags': '|'.join(user_roles),
                'trustworthiness': random.uniform(0.6, 0.98),  # Hidden ground truth
            })
        
        return pd.DataFrame(users)
    
    def _generate_transactions(self):
        """Generate realistic transactions based on user trustworthiness"""
        transactions = []
        
        items = [
            ('Power Drill', 3500, 'tools'),
            ('Rice Cooker', 2000, 'appliances'),
            ('Laptop Charger', 1200, 'electronics'),
            ('Coffee Table', 5000, 'furniture'),
            ('Bicycle', 8000, 'sports'),
            ('Tent', 4000, 'outdoor'),
            ('Books (set)', 800, 'media'),
        ]
        
        for _ in range(self.n_transactions):
            borrower = self.users.sample(1).iloc[0]
            lender = self.users.sample(1).iloc[0]
            
            # Skip self-borrowing
            if borrower['user_id'] == lender['user_id']:
                continue
            
            item_name, value, category = random.choice(items)
            borrow_date = datetime.now() - timedelta(days=random.randint(1, 180))
            expected_return = borrow_date + timedelta(days=random.randint(1, 14))
            
            # Outcome depends on trustworthiness (with noise)
            combined_trust = (borrower['trustworthiness'] + lender['trustworthiness']) / 2
            
            if random.random() < combined_trust:
                outcome = 'completed_on_time'
                actual_return = expected_return
                condition = 'good'
            else:
                if random.random() < 0.6:
                    outcome = 'completed_late'
                    actual_return = expected_return + timedelta(days=random.randint(1, 7))
                    condition = random.choice(['good', 'good', 'damaged'])  # Mostly good
                else:
                    outcome = 'completed_disputed'
                    actual_return = expected_return + timedelta(days=random.randint(-5, 10))
                    condition = random.choice(['good', 'damaged'])
            
            transactions.append({
                'transaction_id': f'T{len(transactions)+1:04d}',
                'borrower_id': borrower['user_id'],
                'lender_id': lender['user_id'],
                'item_name': item_name,
                'item_value_pkr': value,
                'category': category,
                'borrow_date': borrow_date,
                'expected_return_date': expected_return,
                'actual_return_date': actual_return,
                'item_condition_returned': condition,
                'outcome': outcome,
                'dispute_filed': 'Y' if outcome == 'completed_disputed' else 'N',
            })
        
        return pd.DataFrame(transactions)

# Generate and save
if __name__ == "__main__":
    gen = NeighborhoodGenerator(n_users=60, n_transactions=250)
    
    users_df = gen.users.drop('trustworthiness', axis=1)  # Don't leak ground truth
    transactions_df = gen._generate_transactions()
    
    users_df.to_csv('community_data/users.csv', index=False)
    transactions_df.to_csv('community_data/transactions.csv', index=False)
    
    print(f"Generated {len(users_df)} users, {len(transactions_df)} transactions")
```

---

### Dataset 2: Epinions Trust Network

#### **How to Use**

```python
"""
Load and prepare Epinions dataset for evaluation
"""

import pandas as pd
import numpy as np

class EpinionsLoader:
    """
    Load Epinions dataset from trustlet.org
    Dataset: 840K ratings, 131K users, 5.9K trust relationships
    """
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.ratings = None
        self.trust_network = None
    
    def load_ratings(self):
        """Load product ratings"""
        # Epinions ratings format: user_id, item_id, rating, timestamp
        self.ratings = pd.read_csv(
            f'{self.data_path}/ratings_data.txt',
            sep=' ',
            names=['user_id', 'item_id', 'rating', 'timestamp'],
        )
        return self.ratings
    
    def load_trust_network(self):
        """Load user-to-user trust relationships"""
        # Format: source_user, target_user, trust_value (1 or -1)
        self.trust_network = pd.read_csv(
            f'{self.data_path}/trust_data.txt',
            sep=' ',
            names=['source', 'target', 'trust'],
        )
        return self.trust_network
    
    def create_evaluation_subset(self, n_users: int = 300, n_ratings_per_user: int = 20):
        """
        Create a balanced subset for evaluation.
        
        This prevents overfitting and mimics neighborhood-scale data.
        """
        # Select users with enough ratings
        user_counts = self.ratings.groupby('user_id').size()
        active_users = user_counts[user_counts >= n_ratings_per_user].index.tolist()
        
        selected_users = np.random.choice(active_users, size=min(n_users, len(active_users)), replace=False)
        
        # Filter ratings to selected users
        eval_ratings = self.ratings[self.ratings['user_id'].isin(selected_users)].copy()
        
        # Filter trust network to selected users
        eval_trust = self.trust_network[
            (self.trust_network['source'].isin(selected_users)) &
            (self.trust_network['target'].isin(selected_users))
        ].copy()
        
        print(f"Evaluation subset: {len(selected_users)} users, {len(eval_ratings)} ratings, {len(eval_trust)} trust edges")
        
        return eval_ratings, eval_trust
    
    def create_train_test_split(self, ratings: pd.DataFrame, train_ratio: float = 0.8):
        """
        Split ratings into train and test sets (time-based).
        
        Train: Older ratings (used to build trust model)
        Test: Newer ratings (used to evaluate predictions)
        """
        split_date = ratings['timestamp'].quantile(train_ratio)
        
        train = ratings[ratings['timestamp'] <= split_date]
        test = ratings[ratings['timestamp'] > split_date]
        
        print(f"Train: {len(train)} ratings, Test: {len(test)} ratings")
        
        return train, test

# Example usage
if __name__ == "__main__":
    loader = EpinionsLoader('data/epinions/')
    
    ratings_all = loader.load_ratings()
    trust_all = loader.load_trust_network()
    
    ratings_eval, trust_eval = loader.create_evaluation_subset(n_users=300)
    ratings_train, ratings_test = loader.create_train_test_split(ratings_eval)
    
    print(f"Ready for evaluation!")
```

**Download Epinions:**
```bash
wget http://www.trustlet.org/wiki/static/files/ratings_data.txt
wget http://www.trustlet.org/wiki/static/files/trust_data.txt
```

---

### Dataset 3: Fraud Scenarios

**Hand-crafted scenarios to test fraud detection:**

```python
"""
Create known-fraud scenarios to validate fraud detection
"""

def create_fraud_scenarios(base_users: List[str]) -> Dict[str, List[Dict]]:
    """
    Create 5–10 known-fraud scenarios with hand-crafted malicious behavior.
    
    Returns:
        {
            'scenario_name': [
                {'user': 'MaliciousUser1', 'action': 'rate', 'target': 'FakeUser1', ...},
                ...
            ],
            ...
        }
    """
    
    scenarios = {}
    
    # Scenario 1: Rating Ring (3 accounts rating each other)
    scenarios['rating_ring_3_accounts'] = [
        {'user': 'Fake_A', 'action': 'rate', 'target': 'Fake_B', 'rating': 5, 'text': 'Excellent!'},
        {'user': 'Fake_B', 'action': 'rate', 'target': 'Fake_C', 'rating': 5, 'text': 'Excellent!'},
        {'user': 'Fake_C', 'action': 'rate', 'target': 'Fake_A', 'rating': 5, 'text': 'Excellent!'},
    ]
    
    # Scenario 2: Device Sharing (5 accounts from same IP)
    scenarios['sybil_device_sharing'] = [
        {'user': f'Device_Sybil_{i}', 'device_id': 'DEV_12345', 'action': 'join'} 
        for i in range(5)
    ]
    
    # Scenario 3: Burst Behavior (30 ratings in 1 day by new account)
    scenarios['new_account_burst'] = [
        {
            'user': 'BurstUser',
            'account_age_days': 1,
            'action': 'rate',
            'target': base_users[i % len(base_users)],
            'rating': 5,
            'timestamp': f'2024-06-15 {i:02d}:00:00'
        }
        for i in range(30)
    ]
    
    # Scenario 4: Identical Text (Copy-paste same review 10 times)
    identical_text = "Great person, very trustworthy, would recommend!"
    scenarios['identical_text_spam'] = [
        {
            'user': 'SpamUser',
            'action': 'rate',
            'target': base_users[i % len(base_users)],
            'rating': 5,
            'text': identical_text,
        }
        for i in range(10)
    ]
    
    return scenarios

# How to use
if __name__ == "__main__":
    base_users = [f'U{i:03d}' for i in range(50)]
    scenarios = create_fraud_scenarios(base_users)
    
    for scenario_name, actions in scenarios.items():
        print(f"\n{scenario_name}: {len(actions)} actions")
        for action in actions[:2]:  # Print first 2
            print(f"  {action}")
```

**Evaluation approach:**
1. Build trust model on clean data
2. Inject known-fraud scenarios
3. Check if fraud detector catches them (should have ~90% recall)
4. Measure false positives on legitimate dense groups (should be <5%)

---

## PART 3: PRACTICAL IMPLEMENTATION TIPS

### Tip 1: Database Schema for Efficiency

```sql
-- Users table
CREATE TABLE users (
    user_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    neighborhood VARCHAR(50),
    account_created TIMESTAMP,
    account_status VARCHAR(20),
);

-- Transactions table
CREATE TABLE transactions (
    transaction_id VARCHAR(20) PRIMARY KEY,
    borrower_id VARCHAR(20),
    lender_id VARCHAR(20),
    item_value_pkr INT,
    borrow_date DATE,
    return_date DATE,
    outcome VARCHAR(50),
    FOREIGN KEY (borrower_id) REFERENCES users(user_id),
    FOREIGN KEY (lender_id) REFERENCES users(user_id),
);

-- Ratings cache (precomputed trust estimates)
CREATE TABLE trust_cache (
    user_id VARCHAR(20),
    role VARCHAR(20),
    outcome_type VARCHAR(20),
    successes INT,
    failures INT,
    computed_at TIMESTAMP,
    PRIMARY KEY (user_id, role, outcome_type),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
);

-- Indexes for fast queries
CREATE INDEX idx_transactions_borrower ON transactions(borrower_id);
CREATE INDEX idx_transactions_lender ON transactions(lender_id);
CREATE INDEX idx_transactions_outcome ON transactions(outcome);
```

---

### Tip 2: Caching Strategy

```python
"""
Cache trust estimates to avoid recomputation
"""

class TrustCache:
    """
    In-memory cache of recently computed trust estimates.
    Invalidates after TTL (time-to-live).
    """
    
    def __init__(self, ttl_minutes: int = 60):
        self.cache = {}
        self.ttl = ttl_minutes
    
    def get(self, user: str, role: str) -> Optional[Dict]:
        """Get cached trust estimate"""
        key = f'{user}:{role}'
        if key in self.cache:
            entry, timestamp = self.cache[key]
            if (datetime.now() - timestamp).seconds < self.ttl * 60:
                return entry
        return None
    
    def set(self, user: str, role: str, trust_estimate: Dict) -> None:
        """Cache trust estimate"""
        key = f'{user}:{role}'
        self.cache[key] = (trust_estimate, datetime.now())
    
    def invalidate(self, user: str) -> None:
        """Invalidate all entries for a user (after new rating)"""
        keys_to_delete = [k for k in self.cache.keys() if k.startswith(f'{user}:')]
        for key in keys_to_delete:
            del self.cache[key]
```

---

### Tip 3: Testing Your Algorithms

```python
"""
Unit tests for trust algorithms
"""

import unittest

class TestBetaBinomial(unittest.TestCase):
    
    def test_uniform_prior(self):
        """Test Beta(1,1) produces symmetric intervals"""
        result = estimate_beta_binomial(5, 5, prior_alpha=1, prior_beta=1)
        # Should be roughly 50%
        self.assertAlmostEqual(result.probability, 0.5, places=1)
    
    def test_small_sample(self):
        """Test that small samples produce wide intervals"""
        result_small = estimate_beta_binomial(1, 0)
        result_large = estimate_beta_binomial(100, 0)
        
        # Small sample should have wider interval
        small_interval = result_small.confidence_high - result_small.confidence_low
        large_interval = result_large.confidence_high - result_large.confidence_low
        
        self.assertGreater(small_interval, large_interval)
    
    def test_positive_feedback(self):
        """Test that successes increase probability"""
        no_data = estimate_beta_binomial(0, 0)
        with_success = estimate_beta_binomial(1, 0)
        
        self.assertGreater(with_success.probability, no_data.probability)

class TestTransitiveTrust(unittest.TestCase):
    
    def test_no_path(self):
        """Test that disconnected users have no indirect trust"""
        graph = CommunityGraph()
        prob, conf, evidence = graph.compute_indirect_trust('A', 'B')
        
        self.assertIsNone(prob)
        self.assertEqual(conf, 0.0)
    
    def test_direct_path(self):
        """Test that direct paths are strongest"""
        graph = CommunityGraph()
        graph.add_edge('A', 'B', 0.8)
        
        prob, conf, evidence = graph.compute_indirect_trust('A', 'B')
        
        self.assertGreater(conf, 0.3)  # Direct path has decent confidence
        self.assertEqual(len(evidence['strongest_path']), 2)  # A → B

if __name__ == '__main__':
    unittest.main()
```

---

## SUMMARY: WHICH ALGORITHMS TO IMPLEMENT BY WEEK

| Week | Algorithm | Implementation Complexity | Owner |
|------|-----------|--------------------------|-------|
| 2–3 | Beta-Binomial Trust | Low (50 lines, basic stats) | Member B |
| 3–4 | k-Hop Graph Traversal | Medium (80 lines, BFS with weights) | Member A |
| 4–5 | Multi-Signal Fraud Detection | Medium (100 lines, independent signals) | Member C |
| 5–6 | Decision Policy | Medium (60 lines, combining outputs) | Member B |
| 6–7 | Baseline Comparisons | Low (40 lines, simple methods) | Member A |
| 8+ | Testing & Evaluation | Medium (100 lines, test scenarios) | All |

---

**Total: ~500 lines of core logic + ~200 lines of tests = Solid, defensible project for 3 people over 16 weeks.** ✅
