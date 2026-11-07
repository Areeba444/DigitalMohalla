/**
 * W11 — Moderator Membership Queue & Triage (FR-A-10, FR-A-11, UC-A4)
 *
 * Tenant-isolated. Moderator reviews pending applicants for their community.
 * Approval or "request more info" with mandatory reason (audit trail).
 *
 * HCI notes:
 * - Method pill uses text + icon, never colour alone.
 * - Decision form has a mandatory reason textarea; submit is blocked without it.
 * - Tenant isolation badge at the top of every screen (NFR-S-03 visual enforcement).
 */
import { useState } from 'react';
import { View, Text } from 'react-native';

import {
  Avatar,
  Badge,
  Banner,
  Body,
  Button,
  Card,
  Caption,
  EmptyState,
  Field,
  Screen,
} from '@/components/ui';
import { mockMembershipQueue, type MockMembershipRequest } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

function MethodPill({ method }: { method: MockMembershipRequest['method'] }) {
  const { theme } = useTheme();
  const map: Record<string, [string, string]> = {
    GEOFENCE: ['location_on', 'Location check'],
    VOUCHER: ['group', 'Voucher'],
    MANUAL: ['edit', 'Manual'],
  };
  const [icon, label] = map[method] ?? ['help', method];
  return <Badge label={label} tone={theme.colors.neutral} icon={icon as any} />;
}

function SignalPill({ signal }: { signal: MockMembershipRequest['locality_signal'] }) {
  const { theme } = useTheme();
  const tone =
    signal === 'MATCH'
      ? theme.colors.success
      : signal === 'INCONCLUSIVE'
      ? theme.colors.warning
      : theme.colors.info; // CONFLICTING is neutral-info, never red
  const label = signal === 'MATCH' ? 'Signal match' : signal === 'INCONCLUSIVE' ? 'Inconclusive' : 'Conflicting signal';
  const icon = signal === 'MATCH' ? 'check_circle' : 'info';
  return <Badge label={label} tone={tone} icon={icon as any} />;
}

function MemberCard({
  req,
  onDecide,
}: {
  req: MockMembershipRequest;
  onDecide: (id: string, action: 'APPROVE' | 'REQUEST_INFO', reason: string) => void;
}) {
  const { theme } = useTheme();
  const [reason, setReason] = useState('');
  const [acting, setActing] = useState(false);

  async function decide(action: 'APPROVE' | 'REQUEST_INFO') {
    setActing(true);
    await new Promise((r) => setTimeout(r, 600));
    setActing(false);
    onDecide(req.id, action, reason);
  }

  return (
    <Card>
      <View style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
        <Avatar name={req.user_name} size={44} />
        <View style={{ flex: 1, gap: 4 }}>
          <Text style={{ fontFamily: theme.fonts.bold, fontSize: 16, color: theme.colors.text }}>
            {req.user_name}
          </Text>
          <Caption>{req.email_masked}</Caption>
          <Caption>Applied {req.applied_at.substring(0, 10)}</Caption>
        </View>
      </View>

      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
        <MethodPill method={req.method} />
        <SignalPill signal={req.locality_signal} />
        {req.voucher_by ? (
          <Badge label={`Vouched by ${req.voucher_by}`} tone={theme.colors.info} icon={'group' as any} />
        ) : null}
      </View>

      <Field
        label="Decision reason (required)"
        value={reason}
        onChangeText={setReason}
        placeholder="Explain your decision for the audit log..."
        multiline
      />

      <View style={{ flexDirection: 'row', gap: 10 }}>
        <Button
          label="Approve"
          icon="check"
          onPress={() => decide('APPROVE')}
          loading={acting}
          disabled={!reason.trim() || acting}
          style={{ flex: 1 }}
        />
        <Button
          label="Request more info"
          icon="help"
          variant="outline"
          onPress={() => decide('REQUEST_INFO')}
          loading={acting}
          disabled={!reason.trim() || acting}
          style={{ flex: 1 }}
        />
      </View>
    </Card>
  );
}

export default function MembershipQueue() {
  const { theme } = useTheme();
  const [queue, setQueue] = useState(mockMembershipQueue.filter((r) => r.status === 'PENDING_MODERATOR'));

  function handleDecide(id: string, action: 'APPROVE' | 'REQUEST_INFO', reason: string) {
    setQueue((prev) => prev.filter((r) => r.id !== id));
  }

  return (
    <Screen title="Membership queue" subtitle="F-7 Sector 4 [Isolated]">
      {/* Tenant isolation badge */}
      <Banner tone={theme.colors.warning} title="Community moderator scope" icon="apartment">
        <Body muted style={{ fontSize: 13 }}>
          You can only see applicants within your community. Cross-community requests are handled separately.
        </Body>
      </Banner>

      {queue.length === 0 ? (
        <EmptyState
          icon="group_add"
          title="No pending applicants"
          body="New membership requests for your community will appear here."
        />
      ) : (
        queue.map((req) => (
          <MemberCard key={req.id} req={req} onDecide={handleDecide} />
        ))
      )}
    </Screen>
  );
}

