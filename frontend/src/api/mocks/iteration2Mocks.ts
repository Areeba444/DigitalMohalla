/**
 * Typed mock fixtures for Iteration 2 screens (W8–W24).
 *
 * All data is synthetic and representative of the Digital Mohalla domain.
 * These mocks are consumed by screen shells when the backend is unavailable
 * (design phase / local development) and by Jest render tests.
 *
 * NFR-U-01: No single composite trust score appears in any mock. All assurance
 * data is multi-dimensional (direct evidence, manipulation risk, interval bounds).
 */

// ─────────────────────────────────────────────────────────────
// W8 — Registration
// ─────────────────────────────────────────────────────────────

export const mockRegistrationResult = {
  id: 'usr_mock_01',
  email: 'areeba@example.com',
  name: 'Areeba K.',
  status: 'REGISTERED' as const,
};

// ─────────────────────────────────────────────────────────────
// W9 — Community Directory
// ─────────────────────────────────────────────────────────────

export type MockCommunity = {
  id: string;
  name: string;
  sector: string;
  city: string;
  members_count: number;
  active_listings: number;
  rules_summary: string;
  requires_code: boolean;
};

export const mockCommunities: MockCommunity[] = [
  {
    id: 'comm_f7_s4',
    name: 'F-7 Sector 4',
    sector: 'F-7',
    city: 'Islamabad',
    members_count: 48,
    active_listings: 23,
    rules_summary: 'Max 7-day loans · Photo handover required · PKR 500 deposit convention',
    requires_code: false,
  },
  {
    id: 'comm_g10_2',
    name: 'G-10/2 Mohalla',
    sector: 'G-10',
    city: 'Islamabad',
    members_count: 31,
    active_listings: 11,
    rules_summary: 'Max 5-day loans · Voucher from existing member required',
    requires_code: true,
  },
  {
    id: 'comm_i8_3',
    name: 'I-8/3 Community',
    sector: 'I-8',
    city: 'Islamabad',
    members_count: 62,
    active_listings: 40,
    rules_summary: 'Max 10-day loans · Open to neighbourhood residents',
    requires_code: false,
  },
];

// ─────────────────────────────────────────────────────────────
// W10 — Locality Verification
// ─────────────────────────────────────────────────────────────

export type LocalityVerificationResult =
  | { status: 'VERIFIED'; message: string }
  | { status: 'INCONCLUSIVE'; message: string; next: string }
  | { status: 'CONFLICTING'; message: string; next: string };

export const mockVerificationResults: Record<string, LocalityVerificationResult> = {
  VERIFIED: {
    status: 'VERIFIED',
    message: 'Your location matches the community boundary.',
  },
  INCONCLUSIVE: {
    status: 'INCONCLUSIVE',
    message: 'Could not confirm your location automatically.',
    next: 'Your request has been sent to the community moderator for a quick review. You will be notified within 24 hours.',
  },
  CONFLICTING: {
    status: 'CONFLICTING',
    message: 'Location signal was ambiguous — this is common with indoor readings.',
    next: 'The moderator will review your request alongside your invitation code. No action required from you.',
  },
};

// ─────────────────────────────────────────────────────────────
// W11 — Moderator Membership Queue
// ─────────────────────────────────────────────────────────────

export type MockMembershipRequest = {
  id: string;
  user_name: string;
  email_masked: string;
  method: 'GEOFENCE' | 'VOUCHER' | 'MANUAL';
  voucher_by?: string;
  locality_signal: 'MATCH' | 'INCONCLUSIVE' | 'CONFLICTING';
  applied_at: string;
  status: 'PENDING_MODERATOR' | 'APPROVED' | 'MORE_INFO_REQUESTED';
};

export const mockMembershipQueue: MockMembershipRequest[] = [
  {
    id: 'mem_req_01',
    user_name: 'Bilal Tariq',
    email_masked: 'bi***@gmail.com',
    method: 'VOUCHER',
    voucher_by: 'Hamza M.',
    locality_signal: 'INCONCLUSIVE',
    applied_at: '2026-11-03T10:00:00Z',
    status: 'PENDING_MODERATOR',
  },
  {
    id: 'mem_req_02',
    user_name: 'Sana Riaz',
    email_masked: 'sa***@yahoo.com',
    method: 'GEOFENCE',
    locality_signal: 'CONFLICTING',
    applied_at: '2026-11-04T08:30:00Z',
    status: 'PENDING_MODERATOR',
  },
  {
    id: 'mem_req_03',
    user_name: 'Kamran Ali',
    email_masked: 'ka***@hotmail.com',
    method: 'MANUAL',
    locality_signal: 'MATCH',
    applied_at: '2026-11-02T14:15:00Z',
    status: 'MORE_INFO_REQUESTED',
  },
];

// ─────────────────────────────────────────────────────────────
// W12 — Notification Center
// ─────────────────────────────────────────────────────────────

export type MockNotification = {
  id: string;
  type: 'ACTION' | 'UPDATE' | 'SYSTEM';
  icon: string;
  title: string;
  body: string;
  timestamp: string;
  unread: boolean;
  deep_link?: string;
};

export const mockNotifications: MockNotification[] = [
  {
    id: 'notif_01',
    type: 'ACTION',
    icon: 'handshake',
    title: 'Handover due tomorrow',
    body: 'Power Drill handover with Ayesha K. is scheduled for 10:00 AM.',
    timestamp: '9:00 AM',
    unread: true,
    deep_link: '/request/txn-001',
  },
  {
    id: 'notif_02',
    type: 'UPDATE',
    icon: 'check_circle',
    title: 'Request accepted',
    body: 'Sara M. accepted your request to borrow the Pressure Cooker for Nov 10–13.',
    timestamp: 'Yesterday',
    unread: true,
    deep_link: '/request/txn-002',
  },
  {
    id: 'notif_03',
    type: 'SYSTEM',
    icon: 'gavel',
    title: 'Moderator decision',
    body: 'Case #D-014 has been resolved. The booking has been closed.',
    timestamp: '2d ago',
    unread: false,
  },
  {
    id: 'notif_04',
    type: 'ACTION',
    icon: 'rate_review',
    title: 'Leave a review',
    body: 'Your loan of the Lawn Mower was completed. Share how it went.',
    timestamp: '3d ago',
    unread: false,
    deep_link: '/request/txn-003/review',
  },
];

// ─────────────────────────────────────────────────────────────
// W13 — Loan Extension
// ─────────────────────────────────────────────────────────────

export const mockExtensionContext = {
  transaction_id: 'txn-001',
  item_title: 'Power Drill',
  current_return_date: 'Nov 10, 2026',
  max_extension_date: 'Nov 17, 2026', // +7 days
  borrower_name: 'Ayesha K.',
  lender_name: 'Zainab M.',
};

// ─────────────────────────────────────────────────────────────
// W14 — Counter-Offer
// ─────────────────────────────────────────────────────────────

export const mockCounterOfferContext = {
  transaction_id: 'txn-002',
  item_title: 'Pressure Cooker',
  original_start: 'Nov 8, 2026',
  original_end: 'Nov 10, 2026',
  lender_name: 'Sara M.',
  borrower_name: 'Hamza K.',
};

// ─────────────────────────────────────────────────────────────
// W15 — Bilateral Review
// ─────────────────────────────────────────────────────────────

export const mockReviewContext = {
  transaction_id: 'txn-003',
  item_title: 'Lawn Mower',
  peer_name: 'Bilal T.',
  peer_role: 'LENDER' as const,
  completed_at: 'Nov 4, 2026',
};

// ─────────────────────────────────────────────────────────────
// W16 — My Evidence Profile (multi-dimensional, NO single score)
// ─────────────────────────────────────────────────────────────

export const mockEvidenceProfile = {
  user_name: 'Areeba K.',
  community: 'F-7 Sector 4',
  member_since: 'Sep 2026',
  assurance_state: 'SUFFICIENT_EVIDENCE' as const,
  // Beta posterior credible interval — the meaningful signal, not a point score
  interval: { low: 0.72, high: 0.95, mean: 0.86 },
  transaction_count: 12,
  // Individual dimensions — never collapsed into one number
  dimensions: {
    return_punctuality: { label: 'On-time returns', value: '12 / 12', icon: 'schedule' as const },
    care_history: { label: 'No damage reports', value: '0 issues', icon: 'verified_user' as const },
    handover_completion: { label: 'Dual sign-offs completed', value: '100%', icon: 'handshake' as const },
    communication: { label: 'Responsive', value: 'Avg reply < 1 h', icon: 'chat' as const },
  },
  manipulation_risk: {
    level: 1 as const, // 1 = Low
    label: 'No abnormal patterns detected',
  },
};

// ─────────────────────────────────────────────────────────────
// W17 — Photo Evidence (placeholder; real URI from expo-image-picker)
// ─────────────────────────────────────────────────────────────

export const mockPhotoSlots = [
  { id: 'photo_1', label: 'Front / Overall', hasPhoto: false },
  { id: 'photo_2', label: 'Working parts / Label', hasPhoto: false },
];

// ─────────────────────────────────────────────────────────────
// W18 — Moderator Information Request Response
// ─────────────────────────────────────────────────────────────

export const mockInfoRequestContext = {
  case_id: 'abcd0001-0000-0000-0000-000000000000',
  item_title: 'Power Drill',
  moderator_query: 'Please provide a photo or receipt confirming the deposit was recorded before handover.',
  sla_hours_left: 47.25,
  raised_at: '2026-11-05T10:00:00Z',
};

// ─────────────────────────────────────────────────────────────
// W19 — Possession Adjudication options
// ─────────────────────────────────────────────────────────────

export const mockPossessionOptions = [
  {
    id: 'returned',
    icon: 'check_circle',
    label: 'Item returned to lender',
    description: 'Closes the booking as COMPLETED.',
  },
  {
    id: 'still_held',
    icon: 'person',
    label: 'Item still with borrower',
    description: 'Keeps booking ACTIVE; deposit held until returned.',
  },
  {
    id: 'no_show',
    icon: 'block',
    label: 'Never handed over / no-show',
    description: 'Transitions to NO_SHOW; booking is released.',
  },
  {
    id: 'lost_damaged',
    icon: 'report',
    label: 'Item lost or irreparably damaged',
    description: 'Closes with failure flag; item listing is paused.',
  },
] as const;

// ─────────────────────────────────────────────────────────────
// W20 — Dispute Appeal
// ─────────────────────────────────────────────────────────────

export const mockAppealContext = {
  case_id: 'abcd0001-0000-0000-0000-000000000000',
  original_decision: 'Item returned to lender — booking closed as COMPLETED.',
  decided_at: '2026-11-05T14:00:00Z',
  appeal_window_hours_left: 61.5,
  grounds: [
    { id: 'new_evidence', label: 'New photographic evidence available' },
    { id: 'procedural_error', label: 'Procedural error or misinterpretation' },
    { id: 'pre_existing', label: 'Condition was pre-existing before loan' },
  ],
};

// ─────────────────────────────────────────────────────────────
// W21 — Admin Audit Log
// ─────────────────────────────────────────────────────────────

export type MockAuditEvent = {
  id: string;
  event_type: string;
  actor_masked: string;
  timestamp_utc: string;
  details: string;
  hash_valid: boolean;
};

export const mockAuditEvents: MockAuditEvent[] = [
  {
    id: 'evt_001',
    event_type: 'locality_check_evaluated',
    actor_masked: 'usr_...4f2a',
    timestamp_utc: '2026-11-04T05:12:00Z',
    details: 'Locality check: MATCH · Community: F-7 S4 · GPS: [MASKED_PRIVACY_BOUNDARY]',
    hash_valid: true,
  },
  {
    id: 'evt_002',
    event_type: 'handover_confirmed',
    actor_masked: 'usr_...8b1c',
    timestamp_utc: '2026-11-04T10:00:00Z',
    details: 'Transaction txn-001 · Dual sign-off complete · Photos: 2',
    hash_valid: true,
  },
  {
    id: 'evt_003',
    event_type: 'dispute_opened',
    actor_masked: 'usr_...4f2a',
    timestamp_utc: '2026-11-04T18:30:00Z',
    details: 'Case #D-014 · Reason: DAMAGE · Evidence: 3 photos',
    hash_valid: true,
  },
  {
    id: 'evt_004',
    event_type: 'dispute_resolved',
    actor_masked: 'mod_...2d9e',
    timestamp_utc: '2026-11-05T14:00:00Z',
    details: 'Case #D-014 · Resolution: Item returned · Moderator reason logged',
    hash_valid: true,
  },
];

// ─────────────────────────────────────────────────────────────
// W22 — Create / Edit Item Listing
// ─────────────────────────────────────────────────────────────

export const ITEM_CATEGORIES = [
  { key: 'TOOLS', label: 'Tools & Hardware' },
  { key: 'HOME_APPLIANCES', label: 'Home Appliances' },
  { key: 'GARDEN', label: 'Gardening' },
  { key: 'SPORTS', label: 'Sports & Outdoor' },
  { key: 'BOOKS', label: 'Books & Stationery' },
  { key: 'OTHER', label: 'Other' },
] as const;

export const ITEM_CONDITIONS = [
  { key: 'LIKE_NEW', label: 'Like New' },
  { key: 'GOOD', label: 'Good' },
  { key: 'FAIR', label: 'Fair' },
  { key: 'HEAVILY_USED', label: 'Heavily Used' },
] as const;

// Roman Urdu hints shown as autocomplete suggestions
export const ROMAN_URDU_HINTS = [
  'Drill machine',
  'Silai machine',
  'Pressure cooker',
  'Lawn mower',
  'Charpai',
  'Istari (iron)',
  'Lawn roller',
  'Extension cord',
];

// ─────────────────────────────────────────────────────────────
// W23 — Search Results with Hybrid Ranking
// ─────────────────────────────────────────────────────────────

export type MockSearchResult = {
  id: string;
  title: string;
  owner_name: string;
  community: string;
  condition: string;
  value_band: 'LOW' | 'MEDIUM' | 'HIGH';
  deposit_amount: number;
  assurance_state: 'SUFFICIENT_EVIDENCE' | 'INSUFFICIENT_EVIDENCE' | 'REVIEW_RECOMMENDED';
  rank_reasons: string[];
};

export const mockSearchResults: MockSearchResult[] = [
  {
    id: 'item_001',
    title: 'Power Drill (Bosch 18V)',
    owner_name: 'Zainab M.',
    community: 'F-7 Sector 4',
    condition: 'Good',
    value_band: 'MEDIUM',
    deposit_amount: 500,
    assurance_state: 'SUFFICIENT_EVIDENCE',
    rank_reasons: ["Matches 'drill'", 'Same Mohalla', '12 verified loans'],
  },
  {
    id: 'item_002',
    title: 'Electric Drill (Local brand)',
    owner_name: 'Hassan K.',
    community: 'F-7 Sector 4',
    condition: 'Fair',
    value_band: 'LOW',
    deposit_amount: 200,
    assurance_state: 'INSUFFICIENT_EVIDENCE',
    rank_reasons: ["Matches 'drill'", 'No deposit history', 'Population baseline applied'],
  },
  {
    id: 'item_003',
    title: 'Hammer Drill (Makita)',
    owner_name: 'Sara M.',
    community: 'G-10/2',
    condition: 'Like New',
    value_band: 'HIGH',
    deposit_amount: 800,
    assurance_state: 'REVIEW_RECOMMENDED',
    rank_reasons: ["Matches 'drill'", 'Nearby community', 'Review recommended — read evidence'],
  },
];

// ─────────────────────────────────────────────────────────────
// W24 — Item Details with Lender Assurance
// ─────────────────────────────────────────────────────────────

export const mockItemDetail = {
  id: 'item_001',
  title: 'Power Drill (Bosch 18V)',
  category: 'TOOLS',
  condition: 'Good',
  description: 'Bosch 18V cordless drill with 2 batteries and a carrying case. Suitable for home use.',
  deposit_amount: 500,
  lender: {
    name: 'Zainab M.',
    community: 'F-7 Sector 4',
    assurance_state: 'SUFFICIENT_EVIDENCE' as const,
    // Multi-dimensional — never a single composite score
    summary_line: '12 completed loans · On-time returns · No damage reports',
    is_new_lender: false,
  },
  available_dates: [
    { date: '2026-11-08', available: true },
    { date: '2026-11-09', available: true },
    { date: '2026-11-10', available: false }, // reserved
    { date: '2026-11-11', available: false },
    { date: '2026-11-12', available: true },
  ],
};

