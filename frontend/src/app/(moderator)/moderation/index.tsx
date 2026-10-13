// W6: the moderator's triage queue (UC-D6 2, UC-I4 1; FR-T-10; NFR-S-03; TC-106).
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { useModerationQueue, type QueueCase } from '@/api/hooks';
import { Badge, Body, Caption, Card, Chip, EmptyState, ErrorText, Icon, Loading, Screen } from '@/components/ui';
import { age, caseCode, caseTitle, filterQueue, isDispute, priorityLabel, type QueueFilter } from '@/lib/moderation';
import { useTheme } from '@/theme/ThemeProvider';

function CaseRow({ c }: { c: QueueCase }) {
  const { theme } = useTheme();
  const dispute = isDispute(c);
  // red is reserved for an open dispute (theme rule); priority uses amber, never red
  const tone = c.priority <= 1 ? theme.colors.warning : theme.colors.info;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`Review ${caseTitle(c)}`}
      onPress={() => router.push(`/moderation/${c.id}`)}>
      <Card>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Caption>{caseCode(c)}</Caption>
          <Badge label={dispute ? 'Dispute' : 'Hold'} tone={dispute ? theme.colors.danger : theme.colors.info} />
          <View style={{ flex: 1 }} />
          <Badge label={priorityLabel(c.priority)} tone={tone} />
        </View>
        <Text style={{ fontFamily: theme.fonts.bold, fontSize: 16, color: theme.colors.text }}>{caseTitle(c)}</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          <Caption>{age(c.opened_at)}</Caption>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 2 }}>
            <Text style={{ fontFamily: theme.fonts.bold, color: theme.colors.primary }}>Review</Text>
            <Icon name="chevron_right" size={20} color={theme.colors.primary} />
          </View>
        </View>
      </Card>
    </Pressable>
  );
}

export default function ModerationQueue() {
  const { data, isLoading, error } = useModerationQueue();
  const [filter, setFilter] = useState<QueueFilter>('all');
  const cases = data ?? [];
  const shown = filterQueue(cases, filter);
  const chips: [QueueFilter, string][] = [
    ['all', `All (${cases.length})`],
    ['disputes', `Disputes (${filterQueue(cases, 'disputes').length})`],
    ['holds', `Holds (${filterQueue(cases, 'holds').length})`],
    ['high', 'High priority'],
  ];
  return (
    <Screen title="Triage queue" subtitle="Moderator" back>
      {isLoading ? <Loading /> : null}
      <ErrorText message={error?.message} />
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        {chips.map(([key, label]) => (
          <Chip key={key} label={label} selected={filter === key} onPress={() => setFilter(key)} />
        ))}
      </View>
      {!isLoading && shown.length === 0 ? (
        <EmptyState
          icon="task_alt"
          title="Nothing waiting"
          body="Disputes and held requests from the communities you moderate appear here."
        />
      ) : null}
      {shown.map((c) => (
        <CaseRow key={c.id} c={c} />
      ))}
      <Body muted style={{ fontSize: 13 }}>
        Only cases from the communities you moderate are shown. Priority comes from the type of case, never from
        anyone&apos;s trust evidence.
      </Body>
    </Screen>
  );
}
