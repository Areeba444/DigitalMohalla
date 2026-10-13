// Pure helpers for the dispute form (W5) and the moderator screens (W6, W7). No React, no I/O.
import type { DecisionIn, DisputeReason, QueueCase } from '@/api/hooks';

/** UC-B12 step 2: the reasons a party can choose, in the wireframe's order. */
export const DISPUTE_REASONS: { value: DisputeReason; label: string }[] = [
  { value: 'DAMAGE', label: 'Damage' },
  { value: 'NON_RETURN', label: 'Non-return' },
  { value: 'CONDITION_MISMATCH', label: 'Condition mismatch' },
  { value: 'NO_SHOW', label: 'No-show' },
  { value: 'OTHER', label: 'Other' },
];

const REASON_LABEL: Record<string, string> = Object.fromEntries(
  DISPUTE_REASONS.map((r) => [r.value, r.label]),
);

/** Plain words for each hold, as the moderator should read it. */
export const HOLD_LABEL: Record<string, string> = {
  manipulation_risk: 'Unusual review pattern',
  high_value_low_confidence: 'High-value item, limited history',
  locality_inconclusive: 'Neighbourhood not confirmed',
  locality_conflict: 'Neighbourhood check conflict',
  engine_failure: 'Assessment did not finish',
};

/** Priority comes from the case type (set by the database), never from a trust number (TC-106). */
export function priorityLabel(priority: number): string {
  return priority <= 1 ? 'High' : priority === 2 ? 'Medium' : 'Low';
}

export function isDispute(c: Pick<QueueCase, 'trigger_type'>): boolean {
  return c.trigger_type === 'DISPUTE';
}

export function caseCode(c: Pick<QueueCase, 'id' | 'trigger_type'>): string {
  return `${isDispute(c) ? 'D' : 'H'}-${c.id.slice(0, 4).toUpperCase()}`;
}

export function caseTitle(
  c: Pick<QueueCase, 'trigger_type' | 'dispute_reason' | 'hold_reason' | 'item_title'>,
): string {
  const what = isDispute(c)
    ? (REASON_LABEL[c.dispute_reason ?? ''] ?? 'Dispute')
    : (HOLD_LABEL[c.hold_reason ?? ''] ?? 'Held request');
  return `${what}: ${c.item_title}`;
}

export function age(openedAt: string, now: Date = new Date()): string {
  const hours = Math.max(0, (now.getTime() - new Date(openedAt).getTime()) / 3_600_000);
  if (hours < 1) return 'Opened just now';
  if (hours < 24) return `Opened ${Math.floor(hours)}h ago`;
  return `Opened ${Math.floor(hours / 24)}d ago`;
}

export type QueueFilter = 'all' | 'disputes' | 'holds' | 'high';

export function filterQueue(cases: QueueCase[], f: QueueFilter): QueueCase[] {
  switch (f) {
    case 'disputes':
      return cases.filter(isDispute);
    case 'holds':
      return cases.filter((c) => !isDispute(c));
    case 'high':
      return cases.filter((c) => c.priority <= 1);
    default:
      return cases;
  }
}

export type DecisionOption = {
  key: string;
  label: string;
  help: string;
  kind: DecisionIn['kind'];
  at_fault?: DecisionIn['at_fault'];
};

const REASSESS = ['locality_inconclusive', 'locality_conflict', 'engine_failure'];

/** Only what ADR-0003 and UC-I4 allow for this case (TC-107); no safeguards for engine_failure. */
export function decisionOptions(state: string | null | undefined, holdReason?: string | null): DecisionOption[] {
  if (state === 'DISPUTED') {
    return [
      { key: 'borrower', label: 'Borrower at fault', help: 'Counts against the borrower', kind: 'DISPUTE_RESOLVED', at_fault: 'borrower' },
      { key: 'lender', label: 'Lender at fault', help: 'Counts against the lender', kind: 'DISPUTE_RESOLVED', at_fault: 'lender' },
      { key: 'none', label: 'Nobody at fault', help: 'Counts for both parties', kind: 'DISPUTE_RESOLVED', at_fault: 'none' },
    ];
  }
  if (state !== 'HELD_FOR_REVIEW') return [];
  const reassess = REASSESS.includes(holdReason ?? '');
  const options: DecisionOption[] = [
    {
      key: 'clear',
      label: 'Clear',
      help: reassess ? 'The assessment runs again' : 'The request goes to the lender',
      kind: 'CLEARED',
    },
  ];
  if (holdReason !== 'engine_failure') {
    options.push({
      key: 'safeguards',
      label: 'Clear with safeguards',
      help: 'The lender sees the safeguards you name',
      kind: 'SAFEGUARDS_IMPOSED',
    });
  }
  options.push({ key: 'restrict', label: 'Decline', help: 'The request is declined', kind: 'RESTRICTED' });
  return options;
}
