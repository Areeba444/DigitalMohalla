// TC-105 (W5 dispute), TC-106 (W6 queue), TC-107 (W7 case): screens rendered with mocked API hooks.
// Shapes follow the generated API types; all names and cases are synthetic.
import { fireEvent, render, screen } from '@testing-library/react-native';

import DisputeScreen from '@/app/(resident)/dispute/[id]';
import CaseScreen from '@/app/(moderator)/moderation/[id]';
import ModerationQueue from '@/app/(moderator)/moderation/index';

// The first render of a screen loads its whole module tree; slow machines need more than 5 s.
jest.setTimeout(20_000);

let mockRequest: any;
let mockTrail: any;
let mockQueue: any[];
let mockCase: any;
const mockAction = jest.fn();
const mockDecide = jest.fn();

jest.mock('expo-router', () => ({
  router: { back: jest.fn(), canGoBack: () => false, replace: jest.fn(), push: jest.fn() },
  useLocalSearchParams: () => ({ id: 'txn-1' }),
}));

jest.mock('@/api/hooks', () => ({
  useRequest: () => ({ data: mockRequest, isLoading: false, error: null }),
  useDisputeTrail: () => ({ data: mockTrail, isLoading: false }),
  useAction: () => ({ mutate: mockAction, isPending: false }),
  useModerationQueue: () => ({ data: mockQueue, isLoading: false, error: null }),
  useModeratorCase: () => ({ data: mockCase, isLoading: false, error: null, refetch: jest.fn() }),
  useDecide: () => ({ mutate: mockDecide, isPending: false }),
}));

beforeEach(() => {
  mockAction.mockReset();
  mockDecide.mockReset();
});

const request = (state: string, actions: string[]) => ({
  transaction_id: 'txn-1',
  item_title: 'Power Drill',
  state,
  available_actions: actions,
});

const trail = (yourRole: string, raisedBy: string, actions: string[]) => ({
  case: {
    id: 'abcd0000-0000-0000-0000-000000000000',
    trigger_type: 'DISPUTE',
    dispute_reason: 'DAMAGE',
    raised_by_role: raisedBy,
    status: 'OPEN',
    priority: 1,
    reason: 'Synthetic: a crack on the handle.',
    opened_at: '2026-10-13T08:00:00Z',
  },
  your_role: yourRole,
  available_actions: actions,
});

// ----------------------------------------------------------------------------- TC-105
describe('TC-105 W5 dispute form and progress', () => {
  test('offers the five reasons, warns about the freeze and submits the choice', async () => {
    mockRequest = request('ACTIVE', ['initiate_return', 'raise_dispute']);
    await render(<DisputeScreen />);
    for (const label of ['Damage', 'Non-return', 'Condition mismatch', 'No-show', 'Other']) {
      expect(screen.getByRole('button', { name: label })).toBeOnTheScreen();
    }
    expect(screen.getByText(/frozen until a community moderator rules/)).toBeOnTheScreen();
    expect(screen.getByText(/later version \(decision D20\)/)).toBeOnTheScreen();
    const submit = screen.getByRole('button', { name: 'Submit dispute' });
    expect(submit).toBeDisabled(); // a reason must be chosen first
    await fireEvent.press(screen.getByRole('button', { name: 'Damage' }));
    await fireEvent.changeText(screen.getByLabelText('Your statement'), 'A crack near the chuck.');
    await fireEvent.press(screen.getByRole('button', { name: 'Submit dispute' }));
    expect(mockAction).toHaveBeenCalledWith(
      { name: 'raise_dispute', body: { reason: 'DAMAGE', description: 'A crack near the chuck.' } },
      expect.anything(),
    );
  });

  test('no dispute is offered once the loan is closed', async () => {
    mockRequest = request('COMPLETED', []);
    await render(<DisputeScreen />);
    expect(screen.getByText("A dispute can't be raised now")).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Submit dispute' })).toBeNull();
  });

  test('an open dispute shows its case, with withdraw for the raising party only', async () => {
    mockRequest = request('DISPUTED', ['withdraw_dispute']);
    mockTrail = trail('LENDER', 'LENDER', ['withdraw_dispute']);
    await render(<DisputeScreen />);
    expect(screen.queryByRole('button', { name: 'Submit dispute' })).toBeNull(); // no second form
    expect(screen.getByText('You raised this dispute.')).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Withdraw dispute (restores the previous state)' }));
    expect(mockAction).toHaveBeenCalledWith({ name: 'withdraw_dispute' }, expect.anything());
  });

  test('the other party sees the case but cannot withdraw it', async () => {
    mockRequest = request('DISPUTED', []);
    mockTrail = trail('BORROWER', 'LENDER', []);
    await render(<DisputeScreen />);
    expect(screen.getByText('The other party raised this dispute.')).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: /Withdraw dispute/ })).toBeNull();
    expect(screen.getByText('Only the person who raised it can withdraw it.')).toBeOnTheScreen();
  });
});

// ----------------------------------------------------------------------------- TC-106
const queueCase = (id: string, trigger: string, priority: number, extra: object) => ({
  id,
  transaction_id: `t-${id}`,
  trigger_type: trigger,
  dispute_reason: null,
  hold_reason: null,
  status: 'OPEN',
  priority,
  reason: 'Synthetic.',
  opened_at: '2026-10-13T08:00:00Z',
  item_title: 'Power Drill',
  state: trigger === 'DISPUTE' ? 'DISPUTED' : 'HELD_FOR_REVIEW',
  ...extra,
});

describe('TC-106 W6 moderator queue', () => {
  test('disputes and holds in one feed, priority from the case type, with filters', async () => {
    mockQueue = [
      queueCase('d0000001', 'DISPUTE', 1, { dispute_reason: 'DAMAGE' }),
      queueCase('h0000002', 'ENGINE_FAILURE', 2, { hold_reason: 'engine_failure' }),
    ];
    await render(<ModerationQueue />);
    expect(screen.getByText('Damage: Power Drill')).toBeOnTheScreen();
    expect(screen.getByText('Assessment did not finish: Power Drill')).toBeOnTheScreen();
    expect(screen.getByText('High')).toBeOnTheScreen();
    expect(screen.getByText('Medium')).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'All (2)' })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Holds (1)' }));
    expect(screen.queryByText('Damage: Power Drill')).toBeNull();
    expect(screen.getByText('Assessment did not finish: Power Drill')).toBeOnTheScreen();
  });

  test('an empty queue says nothing is waiting', async () => {
    mockQueue = [];
    await render(<ModerationQueue />);
    expect(screen.getByText('Nothing waiting')).toBeOnTheScreen();
  });
});

// ----------------------------------------------------------------------------- TC-107
const caseView = (state: string, holdReason: string | null, status = 'OPEN') => ({
  case: {
    id: 'abcd0000-0000-0000-0000-000000000000',
    trigger_type: state === 'DISPUTED' ? 'DISPUTE' : 'ENGINE_FAILURE',
    dispute_reason: state === 'DISPUTED' ? 'DAMAGE' : null,
    hold_reason: holdReason,
    raised_by_role: state === 'DISPUTED' ? 'LENDER' : null,
    status,
    priority: 1,
    reason: 'Synthetic: a crack on the handle.',
    opened_at: '2026-10-13T08:00:00Z',
  },
  transaction_id: 'txn-1',
  item_title: 'Power Drill',
  state,
  hold_reason: holdReason,
  borrower_name: 'Borrower One',
  lender_name: 'Lender One',
  requested_period: '["2026-10-23 00:00:00+00","2026-10-26 00:00:00+00")',
  reports: [],
  events: [
    { stream_seq: 2, event_type: 'locality_checked', previous_state: 'REQUEST_CREATED', new_state: 'LOCALITY_CHECKED', occurred_at: '2026-10-13T08:00:01Z', authorisation: 'system:engine' },
    { stream_seq: 1, event_type: 'request_created', previous_state: null, new_state: 'REQUEST_CREATED', occurred_at: '2026-10-13T08:00:00Z', authorisation: 'party:borrower' },
  ],
  assessment: null,
  decisions:
    status === 'OPEN'
      ? []
      : [{ decider_role: 'MODERATOR', kind: 'CLEARED', reason: 'Checked.', safeguards: [], decided_at: '2026-10-13T09:00:00Z' }],
});

describe('TC-107 W7 case adjudication', () => {
  test('a dispute offers findings and needs a reason before it can be confirmed', async () => {
    mockCase = caseView('DISPUTED', null);
    await render(<CaseScreen />);
    expect(screen.getByText(/Lender \(Lender One\)/)).toBeOnTheScreen();
    for (const label of ['Borrower at fault', 'Lender at fault', 'Nobody at fault']) {
      expect(screen.getByRole('button', { name: label })).toBeOnTheScreen();
    }
    await fireEvent.press(screen.getByRole('button', { name: 'Lender at fault' }));
    expect(screen.getByRole('button', { name: 'Confirm decision' })).toBeDisabled(); // no reason yet
    await fireEvent.changeText(screen.getByLabelText('Reason (required, kept in the record)'), 'Listing was wrong.');
    await fireEvent.press(screen.getByRole('button', { name: 'Confirm decision' }));
    expect(mockDecide).toHaveBeenCalledWith(
      { kind: 'DISPUTE_RESOLVED', reason: 'Listing was wrong.', safeguards: [], at_fault: 'lender' },
      expect.anything(),
    );
  });

  test('an engine-failure hold never offers safeguards', async () => {
    mockCase = caseView('HELD_FOR_REVIEW', 'engine_failure');
    await render(<CaseScreen />);
    expect(screen.getByRole('button', { name: 'Clear' })).toBeOnTheScreen();
    expect(screen.getByRole('button', { name: 'Decline' })).toBeOnTheScreen();
    expect(screen.queryByRole('button', { name: 'Clear with safeguards' })).toBeNull();
  });

  test('the event trail is shown in stream order', async () => {
    mockCase = caseView('HELD_FOR_REVIEW', 'engine_failure');
    await render(<CaseScreen />);
    await fireEvent.press(screen.getByText('Event trail'));
    const lines = screen.getAllByText(/^\d+\. /).map((n) => String(n.props.children[0]));
    expect(lines).toEqual(['1', '2']);
  });

  test('"already decided" applies nothing and says so', async () => {
    const { ApiError } = jest.requireActual('@/api/client');
    mockDecide.mockImplementation((_body, opts) => opts.onError(new ApiError(409, 'this case is already decided')));
    mockCase = caseView('HELD_FOR_REVIEW', 'engine_failure');
    await render(<CaseScreen />);
    await fireEvent.press(screen.getByRole('button', { name: 'Clear' }));
    await fireEvent.changeText(screen.getByLabelText('Reason (required, kept in the record)'), 'Engine is back.');
    await fireEvent.press(screen.getByRole('button', { name: 'Confirm decision' }));
    expect(screen.getByText('Already decided')).toBeOnTheScreen();
    expect(screen.getByText(/Nothing you entered was applied/)).toBeOnTheScreen();
  });

  test('a decided case shows its decision and no form', async () => {
    mockCase = caseView('ASSESSED', null, 'DECIDED');
    await render(<CaseScreen />);
    expect(screen.queryByRole('button', { name: 'Confirm decision' })).toBeNull();
    expect(screen.getByText(/cleared by moderator/)).toBeOnTheScreen();
  });
});
