// TC-100 (W1): the lender's request screen with its evidence summary, for ES-01, ES-02 and ES-13.
// The requests are the API's real responses on the synthetic `mini` dataset, saved by
// backend/tests/scenarios/test_lender_evidence_api.py (which fails if the API stops matching them).
import { render, screen } from '@testing-library/react-native';

import RequestScreen from '@/app/(resident)/request/[id]';
import type { RequestDetail } from '@/api/hooks';

import saved from './fixtures/lender-requests.json';

const CASES = saved.cases as unknown as Record<'ES-01' | 'ES-02' | 'ES-13', RequestDetail>;
let mockCurrent: RequestDetail;

jest.mock('expo-router', () => ({
  router: { back: jest.fn(), canGoBack: () => false, replace: jest.fn(), push: jest.fn() },
  useLocalSearchParams: () => ({ id: 'txn' }),
}));

jest.mock('@/api/hooks', () => ({
  useRequest: () => ({ data: mockCurrent, isLoading: false, error: null }),
  useEvents: () => ({ data: [] }),
  useAction: () => ({ mutate: jest.fn(), isPending: false }),
}));

async function show(id: keyof typeof CASES) {
  mockCurrent = CASES[id];
  await render(<RequestScreen />);
}

/** All visible text, to check that no single trust number or rating appears anywhere. */
function allText(): string {
  return screen
    .getAllByText(/./)
    .map((n) => String(n.props.children))
    .join(' ');
}

describe('TC-100 lender request with assurance summary', () => {
  test('shows the borrower, dates and message', async () => {
    await show('ES-01');
    expect(screen.getByText(CASES['ES-01'].borrower_name)).toBeOnTheScreen();
    expect(screen.getByText('Oct 23 – Oct 26 · 3 days')).toBeOnTheScreen();
    expect(screen.getByText(/Synthetic request for the evidence screen test/)).toBeOnTheScreen();
  });

  test('ES-01: the state in words, the API interval bounds, no history, newcomer safeguards', async () => {
    await show('ES-01');
    expect(screen.getByText('Not enough history yet')).toBeOnTheScreen(); // the banner title
    expect(screen.getByText(/does not mean they are risky/)).toBeOnTheScreen();
    expect(screen.getByLabelText('90% credible interval from 0.05 to 0.95')).toBeOnTheScreen();
    expect(screen.getByText(/0 verified loans/)).toBeOnTheScreen();
    expect(screen.getByText(/No community paths found/)).toBeOnTheScreen();
    expect(screen.getByText(/Record the deposit before handover/)).toBeOnTheScreen();
    expect(screen.getByText(/Agree a fixed return date/)).toBeOnTheScreen();
  });

  test('ES-02: sufficient evidence with its loans, interval and safeguard', async () => {
    await show('ES-02');
    const a = CASES['ES-02'].assessment!;
    expect(screen.getByText('Enough verified history')).toBeOnTheScreen();
    expect(screen.getByText(/10 verified loans · 7\.1 after weighting/)).toBeOnTheScreen();
    expect(
      screen.getByLabelText(
        `90% credible interval from ${a.ci90_low!.toFixed(2)} to ${a.ci90_high!.toFixed(2)}`,
      ),
    ).toBeOnTheScreen();
    expect(screen.getByText(/Send the standard return reminder/)).toBeOnTheScreen();
  });

  test('ES-13: the community paths by name, with their strengths and the support level', async () => {
    await show('ES-13');
    const community = CASES['ES-13'].assessment!.community!;
    expect(community.paths).toHaveLength(2);
    for (const p of community.paths) {
      expect(
        screen.getByText(`• Through ${p.via[0]} (path strength ${p.strength.toFixed(2)})`, {
          exact: false,
        }),
      ).toBeOnTheScreen();
    }
    expect(screen.getByText(/Community support 0\.39\. It can support a request/)).toBeOnTheScreen();
    expect(screen.getByText('Take a closer look')).toBeOnTheScreen();
  });

  test.each(['ES-01', 'ES-02', 'ES-13'] as const)(
    '%s: manipulation band separate from the evidence, and no single trust number or rating',
    async (id) => {
      await show(id);
      expect(screen.getByText('Manipulation risk')).toBeOnTheScreen();
      expect(screen.getByText('Low')).toBeOnTheScreen();
      expect(screen.queryByText(/not active in this version/)).toBeNull(); // checks run since C1
      const text = allText();
      const mean = CASES[id].assessment!.posterior_mean!.toFixed(2);
      expect(text).not.toContain(mean); // the posterior mean is drawn as a marker, never printed
      expect(text).not.toMatch(/\/100|\/ 5|★|rating|score/i);
    },
  );

  test('Accept and Decline are enabled; counter-offer is shown as unavailable', async () => {
    await show('ES-02');
    expect(screen.getByRole('button', { name: 'Accept request' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Decline request' })).toBeEnabled();
    expect(
      screen.getByRole('button', { name: 'Counter-offer (coming in iteration 2)' }),
    ).toBeDisabled();
  });
});
