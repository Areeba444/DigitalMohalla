// Pure helpers behind W5, W6 and W7 (TC-105 to TC-107). Case data is synthetic.
import type { QueueCase } from '@/api/hooks';
import {
  age,
  caseCode,
  caseTitle,
  decisionOptions,
  DISPUTE_REASONS,
  filterQueue,
  priorityLabel,
} from '@/lib/moderation';

const base: QueueCase = {
  id: 'abcd1234-0000-0000-0000-000000000000',
  transaction_id: 'txn-1',
  trigger_type: 'DISPUTE',
  dispute_reason: 'DAMAGE',
  hold_reason: null,
  status: 'OPEN',
  priority: 1,
  reason: 'Synthetic claim.',
  opened_at: '2026-10-13T08:00:00Z',
  item_title: 'Power Drill',
  state: 'DISPUTED',
};
const hold: QueueCase = {
  ...base,
  id: 'ffff0000-0000-0000-0000-000000000000',
  trigger_type: 'ENGINE_FAILURE',
  dispute_reason: null,
  hold_reason: 'engine_failure',
  priority: 2,
  state: 'HELD_FOR_REVIEW',
};

test('TC-105: the five reasons of UC-B12, including Other', () => {
  expect(DISPUTE_REASONS.map((r) => r.value)).toEqual([
    'DAMAGE',
    'NON_RETURN',
    'CONDITION_MISMATCH',
    'NO_SHOW',
    'OTHER',
  ]);
});

test('TC-106: titles, codes and priority come from the case type', () => {
  expect(caseTitle(base)).toBe('Damage: Power Drill');
  expect(caseTitle(hold)).toBe('Assessment did not finish: Power Drill');
  expect(caseCode(base)).toBe('D-ABCD');
  expect(caseCode(hold)).toBe('H-FFFF');
  expect([1, 2, 3].map(priorityLabel)).toEqual(['High', 'Medium', 'Low']);
});

test('TC-106: disputes and holds in one feed, with filters', () => {
  const all = [base, hold];
  expect(filterQueue(all, 'all')).toHaveLength(2);
  expect(filterQueue(all, 'disputes')).toEqual([base]);
  expect(filterQueue(all, 'holds')).toEqual([hold]);
  expect(filterQueue(all, 'high')).toEqual([base]);
});

test('TC-107: only the options ADR-0003 allows for each case', () => {
  expect(decisionOptions('DISPUTED').map((o) => o.at_fault)).toEqual(['borrower', 'lender', 'none']);
  expect(decisionOptions('HELD_FOR_REVIEW', 'engine_failure').map((o) => o.kind)).toEqual([
    'CLEARED',
    'RESTRICTED',
  ]);
  expect(decisionOptions('HELD_FOR_REVIEW', 'manipulation_risk').map((o) => o.kind)).toEqual([
    'CLEARED',
    'SAFEGUARDS_IMPOSED',
    'RESTRICTED',
  ]);
  expect(decisionOptions('HELD_FOR_REVIEW', 'locality_conflict')[0].help).toBe('The assessment runs again');
  expect(decisionOptions('ASSESSED')).toEqual([]);
});

test('age is shown in hours, then days', () => {
  const now = new Date('2026-10-14T10:30:00Z');
  expect(age('2026-10-14T10:10:00Z', now)).toBe('Opened just now');
  expect(age('2026-10-14T08:00:00Z', now)).toBe('Opened 2h ago');
  expect(age('2026-10-11T08:00:00Z', now)).toBe('Opened 3d ago');
});
