import { useLocalSearchParams } from 'expo-router';
import { Text, View } from 'react-native';

import { useEvents, useRequest } from '@/api/hooks';
import { ActionPanel } from '@/components/request/ActionPanel';
import { AssurancePanel } from '@/components/request/AssurancePanel';
import {
  Banner,
  Body,
  Card,
  Collapsible,
  ErrorText,
  LifecycleBadge,
  Loading,
  Row,
  Screen,
} from '@/components/ui';
import { formatPeriod, formatTime } from '@/lib/format';
import { useTheme } from '@/theme/ThemeProvider';

const HOLD_TEXT: Record<string, string> = {
  locality_inconclusive:
    'We could not confirm your neighbourhood yet. A moderator will review this. Nothing has been rejected.',
  locality_conflict:
    'The neighbourhood check needs a human look. A moderator will review this. Nothing has been rejected.',
  manipulation_risk:
    'This request needs a moderator to look at it before it goes to the lender. This is a review, not a rejection.',
  high_value_low_confidence:
    'This is a high-value item with limited history, so a moderator will review it first. This is a review, not a rejection.',
  engine_failure:
    'The assessment could not be completed in time, so a moderator will review this. Nothing has been rejected.',
};

function Timeline({ id }: { id: string }) {
  const { theme } = useTheme();
  const { data } = useEvents(id);
  return (
    <Card>
      {(data ?? []).map((e) => (
        <View key={e.stream_seq} style={{ flexDirection: 'row', gap: 8 }}>
          <Text style={{ width: 22, color: theme.colors.textMuted, fontSize: 12 }}>
            {e.stream_seq}
          </Text>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 13, fontWeight: '600', color: theme.colors.text }}>
              {e.event_type}
            </Text>
            <Text style={{ fontSize: 11, color: theme.colors.textMuted }}>
              → {e.new_state} · {formatTime(e.occurred_at)}
            </Text>
          </View>
        </View>
      ))}
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
        <ErrorText message={error?.message ?? 'Not found'} />
      </Screen>
    );
  }

  const lender = r.your_role === 'LENDER';
  const other = lender ? r.borrower_name : r.lender_name;

  return (
    <Screen
      title={lender ? 'Borrowing request' : 'Your request'}
      subtitle={r.item_title}
      back
      right={<LifecycleBadge state={r.state} />}>
      <Card>
        <Row label="Item" value={r.item_title} />
        <Row label={lender ? 'Requested by' : 'Lender'} value={other} />
        <Row label="Dates" value={formatPeriod(r.requested_period)} />
        {r.message ? (
          <Body muted style={{ fontStyle: 'italic' }}>
            “{r.message}”
          </Body>
        ) : null}
      </Card>

      {r.hold_reason ? (
        <Banner tone={theme.colors.warning} title="Held for review">
          <Body muted>{HOLD_TEXT[r.hold_reason] ?? 'A moderator will review this request.'}</Body>
        </Banner>
      ) : null}

      {lender && r.assessment ? (
        <AssurancePanel assessment={r.assessment} name={r.borrower_name} />
      ) : null}

      {!lender && r.state === 'ASSESSED' ? (
        <Banner tone={theme.colors.info} title="Request sent">
          <Body muted>{r.lender_name} has been asked. You will see their decision here.</Body>
        </Banner>
      ) : null}

      <ActionPanel key={`${r.state}-${r.available_actions.join()}`} request={r} id={id} />

      {r.state === 'COMPLETED' ? (
        <Banner tone={theme.colors.success} title="Completed">
          <Body muted>The loan is finished and recorded. Thank you for sharing.</Body>
        </Banner>
      ) : null}

      <Collapsible title="History of this request">
        <Timeline id={id} />
      </Collapsible>
    </Screen>
  );
}
