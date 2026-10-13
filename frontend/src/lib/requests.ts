import type { MyRequest } from '@/api/hooks';

/** Does this request wait for the signed-in person? (Only groups lists; the buttons come from the API.) */
export function needsYou(r: MyRequest): boolean {
  const state = r.state ?? '';
  if (r.your_role === 'LENDER') return ['ASSESSED', 'ACCEPTED', 'RETURN_INITIATED'].includes(state);
  return ['ACCEPTED', 'ACTIVE', 'RETURN_INITIATED'].includes(state);
}

const CLOSED = ['COMPLETED', 'DECLINED', 'CANCELLED', 'EXPIRED', 'NO_SHOW'];

export function isClosed(r: MyRequest): boolean {
  return CLOSED.includes(r.state ?? '');
}

/** One short line telling the person what happens next, in plain language (HCI: error prevention). */
export function nextStep(r: MyRequest): string {
  const lender = r.your_role === 'LENDER';
  switch (r.state) {
    case 'ASSESSED':
      return lender ? `${r.counterpart_name} is waiting for your decision` : `Waiting for ${r.counterpart_name} to decide`;
    case 'HELD_FOR_REVIEW':
      return 'A moderator is looking at this first. Nothing has been rejected';
    case 'ACCEPTED':
      return lender ? 'Record the handover checklist when you meet' : 'Confirm receipt after the lender records the handover';
    case 'ACTIVE':
      return lender ? `${r.counterpart_name} has the item` : 'Start the return when you are ready to give it back';
    case 'RETURN_INITIATED':
      return lender ? 'Inspect the item and record its condition' : 'Waiting for the lender to inspect the item';
    case 'RETURNED':
      return 'Both of you are confirming the condition';
    case 'COMPLETED':
      return 'Finished and recorded. Thank you for sharing';
    case 'DISPUTED':
      return 'A moderator will review the evidence';
    case 'DECLINED':
      return 'This request was declined';
    case 'CANCELLED':
      return 'This request was cancelled';
    default:
      return '';
  }
}
