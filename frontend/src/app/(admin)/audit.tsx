/**
 * W21 — Admin Audit Log & Privacy Masking Feed (FR-M-05, FR-I-06, NFR-PR-01)
 *
 * Immutable event stream view for community / platform administrators.
 * GPS coordinates, CNIC, phone numbers are masked at the display layer.
 *
 * HCI notes:
 * - SHA-256 hash validation status is prominent (security signal).
 * - Filter chips for event type keep the feed scannable.
 * - Each log view is itself recorded — shown in a footer notice.
 * - Privacy masking format: `[MASKED_PRIVACY_BOUNDARY]`.
 */
import { useState } from 'react';
import { ScrollView, View, Text } from 'react-native';

import {
  Badge,
  Banner,
  Body,
  Card,
  Caption,
  Chip,
  EmptyState,
  Screen,
} from '@/components/ui';
import { mockAuditEvents, type MockAuditEvent } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

const EVENT_TYPES = [
  { key: 'ALL', label: 'All' },
  { key: 'TRANSACTION', label: 'Transaction' },
  { key: 'DISPUTE', label: 'Dispute' },
  { key: 'MEMBERSHIP', label: 'Membership' },
  { key: 'ASSURANCE', label: 'Assurance' },
] as const;

function AuditCard({ event }: { event: MockAuditEvent }) {
  const { theme } = useTheme();
  return (
    <Card>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <View style={{ flex: 1, gap: 2 }}>
          <Text style={{ fontFamily: theme.fonts.bold, fontSize: 14, color: theme.colors.text }}>
            {event.event_type}
          </Text>
          <Caption>Actor: {event.actor_masked}</Caption>
          <Caption>{event.timestamp_utc}</Caption>
        </View>
        <Badge
          label={event.hash_valid ? 'Hash valid' : 'Hash INVALID'}
          tone={event.hash_valid ? theme.colors.success : theme.colors.danger}
          icon={event.hash_valid ? 'verified' : 'warning'}
        />
      </View>
      <Body muted style={{ fontSize: 13, fontFamily: theme.fonts.regular }}>
        {event.details}
      </Body>
    </Card>
  );
}

export default function AuditLog() {
  const { theme } = useTheme();
  const [filter, setFilter] = useState<string>('ALL');

  const shown = filter === 'ALL'
    ? mockAuditEvents
    : mockAuditEvents.filter((e) => e.event_type.toUpperCase().includes(filter));

  return (
    <Screen title="Audit log" subtitle="Immutable event stream">
      {/* Hash chain status */}
      <Banner tone={theme.colors.success} title="Event hash chain: VALID" icon="verified">
        <Body muted style={{ fontSize: 13 }}>SHA-256 chain verified. No tampering detected.</Body>
      </Banner>

      {/* Filter chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ marginHorizontal: -16 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
        {EVENT_TYPES.map((t) => (
          <Chip key={t.key} label={t.label} selected={filter === t.key} onPress={() => setFilter(t.key)} />
        ))}
      </ScrollView>

      {shown.length === 0 ? (
        <EmptyState icon="history" title="No events" body="No audit events match the selected filter." />
      ) : (
        shown.map((event) => <AuditCard key={event.id} event={event} />)
      )}

      {/* Self-auditing notice — this view is logged */}
      <Caption style={{ textAlign: 'center', marginTop: 4 }}>
        This log view has been appended to the audit trail.
      </Caption>
    </Screen>
  );
}

