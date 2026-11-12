import { render, screen } from '@testing-library/react-native';

// Iteration 2 screens (W8–W24)
import RegisterScreen from '@/app/register';
import JoinCommunityScreen from '@/app/(resident)/community/join';
import LocalityVerifyScreen from '@/app/(resident)/community/verify';
import MembershipQueueScreen from '@/app/(moderator)/members/index';
import NotificationsScreen from '@/app/(resident)/notifications';
import LoanExtensionScreen from '@/app/(resident)/request/[id]/extend';
import CounterOfferScreen from '@/app/(resident)/request/[id]/counter';
import BilateralReviewScreen from '@/app/(resident)/request/[id]/review';
import EvidenceProfileScreen from '@/app/(resident)/profile/evidence';
import PhotoEvidenceScreen from '@/app/(resident)/request/[id]/photos';
import InfoRequestResponseScreen from '@/app/(resident)/dispute/[id]/respond';
import PossessionAdjudicationScreen from '@/app/(moderator)/moderation/[id]/adjudicate';
import DisputeAppealScreen from '@/app/(resident)/dispute/[id]/appeal';
import AuditLogScreen from '@/app/(admin)/audit';
import CreateItemScreen from '@/app/(resident)/item/create';
import BrowseScreen from '@/app/(resident)/(tabs)/browse';
import ItemDetailScreen from '@/app/(resident)/item/detail/[id]';

jest.setTimeout(30_000);

jest.mock('expo-router', () => ({
  router: {
    back: jest.fn(),
    canGoBack: () => true,
    replace: jest.fn(),
    push: jest.fn(),
    navigate: jest.fn(),
  },
  useLocalSearchParams: () => ({ id: 'item_001', role: 'BORROWER' }),
}));

jest.mock('@/api/hooks', () => ({
  useItems: () => ({
    data: [
      {
        id: 'item_001',
        title: 'Power Drill (Bosch 18V)',
        owner_name: 'Zainab M.',
        value_band: 'MEDIUM',
        deposit_amount: 500,
      },
    ],
    isLoading: false,
    error: null,
  }),
  useMyRequests: () => ({ data: [], isLoading: false, error: null }),
  useCreateRequest: () => ({ mutate: jest.fn(), isPending: false }),
}));

function assertNoSingleScore() {
  const allText = screen
    .getAllByText(/./)
    .map((n) => String(n.props.children))
    .join(' ');
  expect(allText).not.toMatch(/\b[1-5](\.[0-9])?\s*\/\s*5\b/);
  expect(allText).not.toMatch(/★/);
  expect(allText).not.toMatch(/trust\s*score\s*:\s*[0-9]+/i);
}

describe('Iteration 2 Screens (W8–W24) Render & NFR-U-01 Conformance', () => {
  test('W8 Register: renders clean registration and privacy notice', async () => {
    await render(<RegisterScreen />);
    expect(screen.getByText('Join your Mohalla')).toBeOnTheScreen();
    expect(screen.getByText(/exact location and GPS are never stored/i)).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W9 Join Community: renders directory and rules collapsible', async () => {
    await render(<JoinCommunityScreen />);
    expect(screen.getByText('Choose your community')).toBeOnTheScreen();
    expect(screen.getByText('F-7 Sector 4')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W10 Locality Verification: renders 3-valued verification options and privacy assurance', async () => {
    await render(<LocalityVerifyScreen />);
    expect(screen.getByText('Confirm your locality')).toBeOnTheScreen();
    expect(screen.getByText('Verify my location')).toBeOnTheScreen();
    expect(screen.getByText(/coordinates are checked in-memory and immediately discarded/i)).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W11 Membership Queue: renders moderator queue with tenant isolation banner', async () => {
    await render(<MembershipQueueScreen />);
    expect(screen.getByText('Membership queue')).toBeOnTheScreen();
    expect(screen.getByText(/You can only see applicants within your community/i)).toBeOnTheScreen();
    expect(screen.getByText('Bilal Tariq')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W12 Notifications: renders categorized notification rows', async () => {
    await render(<NotificationsScreen />);
    expect(screen.getByText('Notifications')).toBeOnTheScreen();
    expect(screen.getByText('Handover due tomorrow')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W13 Loan Extension: renders extension duration stepper and policy notice', async () => {
    await render(<LoanExtensionScreen />);
    expect(screen.getByText('Request extension')).toBeOnTheScreen();
    expect(screen.getByText('Send extension request')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W14 Counter-Offer: renders alternative date negotiation view', async () => {
    await render(<CounterOfferScreen />);
    expect(screen.getByText(/counter-offer|alternative dates/i)).toBeOnTheScreen();
    expect(screen.getByText('Original request')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W15 Bilateral Review: renders multi-dimensional rating chips (no star ratings)', async () => {
    await render(<BilateralReviewScreen />);
    expect(screen.getByText('Review your exchange')).toBeOnTheScreen();
    expect(screen.getByText('Punctuality & communication')).toBeOnTheScreen();
    expect(screen.getByText('Item condition care')).toBeOnTheScreen();
    expect(screen.getByText('Neighbourliness')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W16 Evidence Profile: renders Beta credible interval bar, zero composite numbers', async () => {
    await render(<EvidenceProfileScreen />);
    expect(screen.getByText('Areeba K.')).toBeOnTheScreen();
    expect(screen.getByText(/90% credible interval/i)).toBeOnTheScreen();
    expect(screen.getByLabelText(/90% credible interval from 0.72 to 0.95/i)).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W17 Photo Evidence: renders slots with EXIF stripped notice', async () => {
    await render(<PhotoEvidenceScreen />);
    expect(screen.getByText('Handover photos')).toBeOnTheScreen();
    expect(screen.getByText(/EXIF metadata including GPS location is automatically stripped/i)).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W18 Info Request Response: renders SLA countdown and quoted query', async () => {
    await render(<InfoRequestResponseScreen />);
    expect(screen.getByText('Moderator information request')).toBeOnTheScreen();
    expect(screen.getByText(/remaining/i)).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W19 Possession Adjudication: renders DM14 physical possession options', async () => {
    await render(<PossessionAdjudicationScreen />);
    expect(screen.getByText('Adjudication')).toBeOnTheScreen();
    expect(screen.getByText('Where is the item now?')).toBeOnTheScreen();
    expect(screen.getByText('Item returned to lender')).toBeOnTheScreen();
    expect(screen.getByText('Item still with borrower')).toBeOnTheScreen();
    expect(screen.getByText('Commit binding resolution')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W20 Dispute Appeal: renders grounds selector and appeal countdown', async () => {
    await render(<DisputeAppealScreen />);
    expect(screen.getByText('Appeal decision')).toBeOnTheScreen();
    expect(screen.getByText('Grounds for appeal')).toBeOnTheScreen();
    expect(screen.getByText('Submit formal appeal')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W21 Admin Audit: renders immutable hash valid status and privacy masking', async () => {
    await render(<AuditLogScreen />);
    expect(screen.getByText('Audit log')).toBeOnTheScreen();
    expect(screen.getByText(/Event hash chain: VALID/i)).toBeOnTheScreen();
    expect(screen.getByText(/MASKED_PRIVACY_BOUNDARY/i)).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W22 Create Item: renders 3-step listing wizard with Roman Urdu hints', async () => {
    await render(<CreateItemScreen />);
    expect(screen.getByText('Share an item')).toBeOnTheScreen();
    expect(screen.getByText('Drill machine')).toBeOnTheScreen();
    expect(screen.getByText('Next: Photos & terms')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W23 Browse & Search: renders hybrid results with reason lines and fallback notice', async () => {
    await render(<BrowseScreen />);
    expect(screen.getByText('Browse & Search')).toBeOnTheScreen();
    expect(screen.getByText('Relevance')).toBeOnTheScreen();
    assertNoSingleScore();
  });

  test('W24 Item Detail: renders availability and lender assurance tier', async () => {
    await render(<ItemDetailScreen />);
    expect(screen.getAllByText('Power Drill (Bosch 18V)')[0]).toBeOnTheScreen();
    expect(screen.getByText('Availability')).toBeOnTheScreen();
    expect(screen.getByText(/About this lender's evidence/i)).toBeOnTheScreen();
    expect(screen.getByText('Request to borrow')).toBeOnTheScreen();
    assertNoSingleScore();
  });
});
