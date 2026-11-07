/**
 * W20 — Dispute Appeal & Second Moderator Review (FR-T-11, ES-11)
 *
 * Either party can appeal within the 72-hour window.
 * Assigned to an independent second moderator (never the same one).
 *
 * HCI notes:
 * - Initial decision is shown as a summary card — provides context without hiding it.
 * - Grounds are a checkbox group, not a free-form field (guides structured appeals).
 * - Governance notice sets correct expectations (independent review, not a reversal guarantee).
 */
import { router } from 'expo-router';
import { useState } from 'react';

import {
  BackButton,
  Banner,
  Body,
  Button,
  Card,
  Caption,
  Check,
  CountdownTimer,
  Field,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { mockAppealContext } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

export default function DisputeAppeal() {
  const { theme } = useTheme();
  const ctx = mockAppealContext;

  const [selectedGrounds, setSelectedGrounds] = useState<string[]>([]);
  const [statement, setStatement] = useState('');
  const [submitting, setSubmitting] = useState(false);

  function toggleGround(id: string) {
    setSelectedGrounds((prev) => (prev.includes(id) ? prev.filter((g) => g !== id) : [...prev, id]));
  }

  const canSubmit = selectedGrounds.length > 0 && statement.trim().length >= 20;

  async function handleSubmit() {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 900));
    setSubmitting(false);
    router.back();
  }

  return (
    <Screen title="Appeal decision" subtitle="Request an independent review">
      <BackButton />

      {/* Appeal window countdown */}
      <CountdownTimer hoursLeft={ctx.appeal_window_hours_left} />

      {/* Original decision — shown for context */}
      <Card>
        <SectionLabel>Original moderator decision</SectionLabel>
        <Body muted style={{ fontSize: 14 }}>{ctx.original_decision}</Body>
        <Caption style={{ marginTop: 4 }}>Decided {ctx.decided_at.substring(0, 10)}</Caption>
      </Card>

      {/* Grounds for appeal */}
      <Card>
        <SectionLabel>Grounds for appeal</SectionLabel>
        <Body muted style={{ fontSize: 13, marginBottom: 8 }}>
          Select all that apply.
        </Body>
        {ctx.grounds.map((g) => (
          <Check
            key={g.id}
            label={g.label}
            checked={selectedGrounds.includes(g.id)}
            onPress={() => toggleGround(g.id)}
          />
        ))}
      </Card>

      {/* Statement */}
      <Field
        label="Statement of appeal (required)"
        value={statement}
        onChangeText={setStatement}
        placeholder="Describe the new evidence or procedural issue in detail..."
        multiline
      />
      {statement.length > 0 && statement.length < 20 && (
        <Caption style={{ color: theme.colors.warning.fg }}>
          {20 - statement.length} more characters required.
        </Caption>
      )}

      {/* Governance notice */}
      <Banner tone={theme.colors.info} title="Independent review" icon="balance">
        <Body muted style={{ fontSize: 13 }}>
          Your appeal will be assigned to a different moderator in your community or a platform overseer. This is a fair review — not a guaranteed reversal.
        </Body>
      </Banner>

      <Button
        label="Submit formal appeal"
        icon="send"
        onPress={handleSubmit}
        loading={submitting}
        disabled={!canSubmit || submitting}
      />
    </Screen>
  );
}

