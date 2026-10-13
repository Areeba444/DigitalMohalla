// W5: raise a dispute, or follow the open one (UC-B12; FR-B-16, FR-B-17; ADR-0004; TC-105).
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { ApiError } from '@/api/client';
import { useAction, useDisputeTrail, useRequest, type DisputeReason, type DisputeTrail } from '@/api/hooks';
import {
  Badge,
  Banner,
  Body,
  Button,
  Caption,
  Card,
  Chip,
  EmptyState,
  ErrorText,
  Field,
  lifecycleLabel,
  Loading,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { age, caseCode, DISPUTE_REASONS } from '@/lib/moderation';
import { useTheme } from '@/theme/ThemeProvider';

function CaseCard({ id, trail }: { id: string; trail: DisputeTrail }) {
  const { theme } = useTheme();
  const act = useAction(id);
  const [error, setError] = useState<string | null>(null);
  const c = trail.case;
  const yours = c.raised_by_role !== null && c.raised_by_role === trail.your_role;
  const reason = DISPUTE_REASONS.find((r) => r.value === c.dispute_reason)?.label ?? 'Dispute';
  const canWithdraw = trail.available_actions.includes('withdraw_dispute');
  return (
    <Card>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <Badge label="Disputed" tone={theme.colors.danger} icon="flag" />
        <Caption>
          Case {caseCode(c)} · {age(c.opened_at)}
        </Caption>
      </View>
      <SectionLabel>{reason}</SectionLabel>
      <Body>“{c.reason}”</Body>
      <Caption>{yours ? 'You raised this dispute.' : 'The other party raised this dispute.'}</Caption>
      <Body muted style={{ fontSize: 14 }}>
        A moderator in your community reviews it. The loan and its deposit record are frozen until then.
      </Body>
      <ErrorText message={error} />
      {canWithdraw ? (
        <Button
          label="Withdraw dispute (restores the previous state)"
          variant="outline"
          loading={act.isPending}
          onPress={() =>
            act.mutate(
              { name: 'withdraw_dispute' },
              {
                onSuccess: () => router.replace(`/request/${id}`),
                onError: (e) => setError(e.message),
              },
            )
          }
        />
      ) : (
        <Caption>Only the person who raised it can withdraw it.</Caption>
      )}
    </Card>
  );
}

function DisputeForm({ id }: { id: string }) {
  const { theme } = useTheme();
  const act = useAction(id);
  const [reason, setReason] = useState<DisputeReason | null>(null);
  const [statement, setStatement] = useState('');
  const [error, setError] = useState<string | null>(null);
  return (
    <>
      <Card>
        <SectionLabel>What happened?</SectionLabel>
        <View accessibilityRole="radiogroup" style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
          {DISPUTE_REASONS.map((r) => (
            <Chip key={r.value} label={r.label} selected={reason === r.value} onPress={() => setReason(r.value)} />
          ))}
        </View>
        <Field
          label="Your statement"
          value={statement}
          onChangeText={setStatement}
          placeholder="Describe the damage or the difference you saw"
          multiline
        />
        <Caption>
          Photo and document evidence arrives in a later version (decision D20). Describe what you saw here instead.
        </Caption>
      </Card>
      <Banner tone={theme.colors.warning} title="The loan will be frozen" icon="warning">
        <Body muted style={{ fontSize: 14 }}>
          Booking and deposit records are frozen until a community moderator rules on this case. You can withdraw
          the dispute if you settle it yourselves.
        </Body>
      </Banner>
      <ErrorText message={error} />
      <Button
        label="Submit dispute"
        icon="flag"
        disabled={reason === null}
        loading={act.isPending}
        onPress={() =>
          reason &&
          act.mutate(
            { name: 'raise_dispute', body: { reason, description: statement.trim() || undefined } },
            { onError: (e) => setError(e instanceof ApiError ? e.message : 'Could not submit the dispute.') },
          )
        }
      />
      <Button label="Cancel" variant="outline" onPress={() => router.back()} />
    </>
  );
}

export default function DisputeScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: r, isLoading, error } = useRequest(id);
  const disputed = r?.state === 'DISPUTED';
  const trail = useDisputeTrail(id, disputed);

  if (isLoading || (disputed && trail.isLoading)) {
    return (
      <Screen title="Dispute" back>
        <Loading />
      </Screen>
    );
  }
  if (error || !r) {
    return (
      <Screen title="Dispute" back>
        <ErrorText message={error?.message ?? 'Not found'} />
      </Screen>
    );
  }
  const subtitle = `${r.item_title} · ${lifecycleLabel(r.state)}`;
  if (disputed && trail.data) {
    return (
      <Screen title="Dispute" subtitle={subtitle} back>
        <CaseCard id={id} trail={trail.data} />
      </Screen>
    );
  }
  return (
    <Screen title="Raise a dispute" subtitle={subtitle} back>
      {r.available_actions.includes('raise_dispute') ? (
        <DisputeForm id={id} />
      ) : (
        <EmptyState
          icon="info"
          title="A dispute can't be raised now"
          body="Disputes are possible once a request is accepted and until the return is confirmed."
        />
      )}
    </Screen>
  );
}
