// W7: case adjudication (UC-I4 1-4, 3c, 4a; FR-T-11; ADR-0003, ADR-0004; NFR-U-01; TC-107).
import { useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Text, View } from 'react-native';

import { ApiError } from '@/api/client';
import { useDecide, useModeratorCase, type ModeratorCase } from '@/api/hooks';
import {
  ASSURANCE,
  AssuranceBadge,
  Badge,
  Banner,
  Body,
  Button,
  Caption,
  Card,
  Chip,
  Collapsible,
  ErrorText,
  Field,
  lifecycleLabel,
  Loading,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { caseCode, decisionOptions, HOLD_LABEL, isDispute, type DecisionOption } from '@/lib/moderation';
import { formatTime } from '@/lib/format';
import { useTheme } from '@/theme/ThemeProvider';

const ROLE = { BORROWER: 'Borrower', LENDER: 'Lender' } as const;

function Evidence({ c }: { c: ModeratorCase }) {
  const { theme } = useTheme();
  const dispute = isDispute(c.case);
  const raiser = c.case.raised_by_role ? ROLE[c.case.raised_by_role as keyof typeof ROLE] : null;
  const trail = [...c.events].sort((a, b) => a.stream_seq - b.stream_seq);
  return (
    <Card>
      <SectionLabel>{dispute ? 'Claims' : 'Why it is held'}</SectionLabel>
      {dispute ? (
        <>
          <Body>
            {raiser ?? 'A party'} ({c[raiser === 'Lender' ? 'lender_name' : 'borrower_name']}): “{c.case.reason}”
          </Body>
          <Caption>The other party&apos;s statement can be added in a later version.</Caption>
        </>
      ) : (
        <Body>{HOLD_LABEL[c.hold_reason ?? ''] ?? c.case.reason}</Body>
      )}
      <SectionLabel>Condition reports</SectionLabel>
      {c.reports.length === 0 ? <Caption>No checklist recorded yet.</Caption> : null}
      {c.reports.map((r) => (
        <Body key={`${r.phase}-${r.reporter_role}`} style={{ fontSize: 14 }}>
          {r.phase === 'HANDOVER' ? 'Handover' : 'Return'} · {ROLE[r.reporter_role as keyof typeof ROLE] ?? r.reporter_role}:{' '}
          {r.condition_agreed ? 'condition agreed' : 'condition disputed'}
          {r.notes ? ` · “${r.notes}”` : ''}
        </Body>
      ))}
      <Caption>Photo evidence arrives in a later version (decision D20).</Caption>
      {c.assessment ? (
        <View style={{ gap: 6 }}>
          <SectionLabel>Assessment</SectionLabel>
          <AssuranceBadge state={c.assessment.assurance_state} />
          <Collapsible title="Explanation" icon="info">
            <Body muted style={{ fontSize: 14 }}>
              {c.assessment.explanation}
            </Body>
          </Collapsible>
        </View>
      ) : null}
      <Collapsible title="Event trail" icon="history">
        <View accessibilityLabel="event trail" style={{ gap: 4 }}>
          {trail.map((e) => (
            <Text key={e.stream_seq} style={{ fontFamily: theme.fonts.regular, fontSize: 13, color: theme.colors.textSecondary }}>
              {e.stream_seq}. {e.event_type} → {lifecycleLabel(e.new_state)} · {formatTime(e.occurred_at)}
            </Text>
          ))}
        </View>
      </Collapsible>
    </Card>
  );
}

function DecisionForm({ c, onDone }: { c: ModeratorCase; onDone: () => void }) {
  const { theme } = useTheme();
  const decide = useDecide(c.case.id);
  const options = decisionOptions(c.state, c.hold_reason);
  const [choice, setChoice] = useState<DecisionOption | null>(null);
  const [reason, setReason] = useState('');
  const [safeguards, setSafeguards] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const lines = safeguards.split('\n').map((s) => s.trim()).filter(Boolean);
  const ready =
    choice !== null && reason.trim().length > 0 && (choice.kind !== 'SAFEGUARDS_IMPOSED' || lines.length > 0);
  if (options.length === 0) return null;
  return (
    <Card>
      <SectionLabel>{isDispute(c.case) ? 'Finding' : 'Decision'}</SectionLabel>
      <View accessibilityRole="radiogroup" style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        {options.map((o) => (
          <Chip key={o.key} label={o.label} selected={choice?.key === o.key} onPress={() => setChoice(o)} />
        ))}
      </View>
      {choice ? <Caption>{choice.help}</Caption> : null}
      {choice?.kind === 'SAFEGUARDS_IMPOSED' ? (
        <Field
          label="Safeguards for the lender (one per line)"
          value={safeguards}
          onChangeText={setSafeguards}
          placeholder="Record the deposit before handover"
          multiline
        />
      ) : null}
      <Field
        label="Reason (required, kept in the record)"
        value={reason}
        onChangeText={setReason}
        placeholder="What you checked and why you decided this"
        multiline
      />
      {conflict ? (
        <Banner tone={theme.colors.info} title="Already decided" icon="info">
          <Body muted style={{ fontSize: 14 }}>
            Another moderator decided this case first. Nothing you entered was applied; the current state is shown
            below.
          </Body>
        </Banner>
      ) : null}
      <ErrorText message={error} />
      <Button
        label="Confirm decision"
        icon="gavel"
        disabled={!ready}
        loading={decide.isPending}
        onPress={() =>
          choice &&
          decide.mutate(
            {
              kind: choice.kind,
              reason: reason.trim(),
              safeguards: choice.kind === 'SAFEGUARDS_IMPOSED' ? lines : [],
              at_fault: choice.at_fault ?? null,
            },
            {
              onSuccess: onDone,
              onError: (e) => {
                if (e instanceof ApiError && e.status === 409) {
                  setConflict(true);
                  onDone();
                } else setError(e.message);
              },
            },
          )
        }
      />
      <Button label="Request more information (iteration 2)" variant="outline" disabled onPress={() => {}} />
      <Caption>Nobody is restricted without a decision like this one, and every decision keeps its reason.</Caption>
    </Card>
  );
}

function Decisions({ c }: { c: ModeratorCase }) {
  if (c.decisions.length === 0) return null;
  return (
    <Card>
      <SectionLabel>Decisions</SectionLabel>
      {c.decisions.map((d) => (
        <Body key={d.decided_at} style={{ fontSize: 14 }}>
          {d.kind.toLowerCase().replace(/_/g, ' ')} by {d.decider_role.toLowerCase()} · “{d.reason}” ·{' '}
          {formatTime(d.decided_at)}
        </Body>
      ))}
    </Card>
  );
}

export default function CaseScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useTheme();
  const { data: c, isLoading, error, refetch } = useModeratorCase(id);
  if (isLoading) {
    return (
      <Screen title="Case" back>
        <Loading />
      </Screen>
    );
  }
  if (error || !c) {
    return (
      <Screen title="Case" back>
        <ErrorText message={error?.message ?? 'Not found'} />
      </Screen>
    );
  }
  const live = c.case.status === 'OPEN' || c.case.status === 'AWAITING_INFORMATION';
  return (
    <Screen
      title="Case adjudication"
      subtitle={`Case ${caseCode(c.case)} · ${c.item_title}`}
      back
      right={
        <Badge
          label={lifecycleLabel(c.state)}
          tone={c.state === 'DISPUTED' ? theme.colors.danger : theme.colors.info}
        />
      }>
      <Evidence c={c} />
      {live ? (
        <DecisionForm c={c} onDone={() => refetch()} />
      ) : (
        <Banner tone={theme.colors.success} title={`Case ${c.case.status.toLowerCase()}`} icon="task_alt">
          <Body muted style={{ fontSize: 14 }}>
            Current state: {lifecycleLabel(c.state)}.
            {c.assessment ? ` Assessment: ${ASSURANCE[c.assessment.assurance_state]?.label ?? c.assessment.assurance_state}.` : ''}
          </Body>
        </Banner>
      )}
      <Decisions c={c} />
    </Screen>
  );
}
