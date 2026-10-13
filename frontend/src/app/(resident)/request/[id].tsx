import { router, useLocalSearchParams } from 'expo-router';
import { Text, View } from 'react-native';

import { useEvents, useRequest } from '@/api/hooks';
import { ActionPanel } from '@/components/request/ActionPanel';
import { AssurancePanel } from '@/components/request/AssurancePanel';
import {
  Avatar,
  Banner,
  Body,
  Button,
  Caption,
  Card,
  Collapsible,
  ErrorText,
  Icon,
  ItemThumb,
  LifecycleBadge,
  Loading,
  LoanProgress,
  Screen,
  Title,
} from '@/components/ui';
import { formatPeriod, formatTime } from '@/lib/format';
import { useTheme } from '@/theme/ThemeProvider';

// Why a request is held, who acts next and that nothing was rejected (HCI analysis, principle 2).
const HOLD_TEXT: Record<string, string> = {
  locality_inconclusive: 'We could not confirm the neighbourhood yet, so a moderator will check it.',
  locality_conflict: 'The neighbourhood check needs a human look, so a moderator will check it.',
  manipulation_risk: 'Some patterns in the evidence need a moderator to look at them before the lender decides.',
  high_value_low_confidence: 'This is a high-value item with limited similar history, so a moderator reviews it first.',
  engine_failure: 'The evidence summary could not be prepared in time, so a moderator will review the request.',
};

const EVENT_TEXT: Record<string, string> = {
  request_created: 'Request sent',
  locality_checked: 'Neighbourhood confirmed',
  held_for_review: 'Sent to a moderator',
  hold_cleared: 'Moderator cleared the hold',
  assessment_generated: 'Evidence summary prepared',
  request_accepted: 'Lender accepted',
  request_declined: 'Declined',
  request_cancelled: 'Cancelled',
  request_expired: 'Expired',
  handover_confirmed: 'Handover confirmed',
  no_show: 'Marked as no-show',
  return_initiated: 'Return started',
  return_confirmed: 'Return inspected',
  transaction_closed: 'Loan completed',
  dispute_opened: 'Dispute opened',
  dispute_withdrawn: 'Dispute withdrawn',
  dispute_resolved: 'Moderator resolved the dispute',
  reminder_sent: 'Reminder sent',
  extension_requested: 'Extension requested',
  extension_approved: 'Extension approved',
  extension_declined: 'Extension declined',
};

/** The request's event log as a vertical timeline (each step is a stored, unchangeable event). */
function Timeline({ id }: { id: string }) {
  const { theme } = useTheme();
  const { data } = useEvents(id);
  const events = data ?? [];
  return (
    <Card>
      {events.map((e, i) => (
        <View key={e.stream_seq} style={{ flexDirection: 'row', gap: 12 }}>
          <View style={{ alignItems: 'center', width: 14 }}>
            <View
              style={{
                width: 12,
                height: 12,
                borderRadius: 6,
                marginTop: 4,
                backgroundColor: i === events.length - 1 ? theme.colors.primary : theme.colors.border,
              }}
            />
            {i < events.length - 1 ? <View style={{ flex: 1, width: 2, backgroundColor: theme.colors.border }} /> : null}
          </View>
          <View style={{ flex: 1, paddingBottom: i < events.length - 1 ? 14 : 0 }}>
            <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 14.5, color: theme.colors.text }}>
              {EVENT_TEXT[e.event_type] ?? e.event_type}
            </Text>
            <Caption>{formatTime(e.occurred_at)}</Caption>
          </View>
        </View>
      ))}
      <Caption>Every step is stored as a record that cannot be edited later.</Caption>
    </Card>
  );
}

export default function RequestScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useTheme();
  const { data: r, isLoading, error } = useRequest(id);

  if (isLoading) {
    return (
      <Screen title="Request" back>
        <Loading />
      </Screen>
    );
  }
  if (error || !r) {
    return (
      <Screen title="Request" back>
        <ErrorText message={error?.message ?? 'This request could not be found.'} />
      </Screen>
    );
  }

  const lender = r.your_role === 'LENDER';
  const other = lender ? r.borrower_name : r.lender_name;
  const state = r.state ?? '';

  return (
    <Screen title={lender ? 'Borrowing request' : 'Your request'} subtitle={r.item_title} back>
      <Card style={{ gap: 14 }}>
        <View style={{ flexDirection: 'row', gap: 14, alignItems: 'center' }}>
          <ItemThumb title={r.item_title} size={64} />
          <View style={{ flex: 1, gap: 6 }}>
            <Title size={21}>{r.item_title}</Title>
            <LifecycleBadge state={r.state} role={r.your_role} />
          </View>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <Avatar name={other} size={40} />
          <View style={{ flex: 1 }}>
            <Caption>{lender ? 'Requested by' : 'Lender'}</Caption>
            <Body style={{ fontFamily: theme.fonts.bold }}>{other}</Body>
          </View>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <View
            style={{
              width: 40,
              height: 40,
              borderRadius: 20,
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: theme.colors.primarySoft,
            }}>
            <Icon name="calendar_month" size={20} color={theme.colors.primary} />
          </View>
          <View style={{ flex: 1 }}>
            <Caption>Dates</Caption>
            <Body style={{ fontFamily: theme.fonts.bold }}>{formatPeriod(r.requested_period)}</Body>
          </View>
        </View>
        {r.message ? (
          <View
            style={{
              alignSelf: lender ? 'flex-start' : 'flex-end',
              maxWidth: '88%',
              padding: 12,
              borderRadius: theme.radius.md,
              borderTopLeftRadius: lender ? 4 : theme.radius.md,
              borderTopRightRadius: lender ? theme.radius.md : 4,
              backgroundColor: lender ? theme.colors.surface2 : theme.colors.primarySoft,
            }}>
            <Body style={{ fontSize: 14.5 }}>{r.message}</Body>
          </View>
        ) : null}
        {state !== 'COMPLETED' ? <LoanProgress state={state} /> : null}
      </Card>

      {r.hold_reason ? (
        <Banner tone={theme.colors.warning} title="A moderator is reviewing this" icon="policy">
          <Body muted style={{ fontSize: 14 }}>
            {HOLD_TEXT[r.hold_reason] ?? 'A moderator will review this request.'} Nothing has been rejected; you
            will see the outcome here.
          </Body>
        </Banner>
      ) : null}

      {state === 'DISPUTED' ? (
        <Banner tone={theme.colors.danger} title="This loan is disputed" icon="flag">
          <Body muted style={{ fontSize: 14 }}>
            A community moderator reviews the case. Nothing else can change until then.
          </Body>
          <Button label="See the dispute" variant="soft" compact onPress={() => router.push(`/dispute/${id}`)} />
        </Banner>
      ) : null}

      {lender && r.assessment ? <AssurancePanel assessment={r.assessment} name={r.borrower_name} /> : null}

      {!lender && state === 'ASSESSED' ? (
        <Banner tone={theme.colors.info} title="Request sent" icon="send">
          <Body muted style={{ fontSize: 14 }}>
            {r.lender_name} has been asked and sees an evidence summary, never a score about you. Their decision
            appears here.
          </Body>
        </Banner>
      ) : null}

      <ActionPanel key={`${r.state}-${r.available_actions.join()}`} request={r} id={id} />

      {state === 'COMPLETED' ? (
        <Banner tone={theme.colors.success} title="Loan completed" icon="task_alt">
          <Body muted style={{ fontSize: 14 }}>
            Returned and recorded. This verified loan now counts as evidence for future requests. Thank you for
            sharing.
          </Body>
        </Banner>
      ) : null}

      <Collapsible title="History of this request" icon="history">
        <Timeline id={id} />
      </Collapsible>
    </Screen>
  );
}
