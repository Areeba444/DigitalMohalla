/**
 * W18 — Party Response to Moderator Information Request (FR-I-04, UC-I4)
 *
 * Party must respond before the SLA countdown expires.
 * CountdownTimer turns amber under 24h and red under 1h.
 *
 * HCI notes:
 * - Moderator's question is quoted verbatim — reduces user confusion.
 * - SLA countdown is visually prominent (top of screen), with text + icon (never colour alone).
 * - Photo slot optional; response textarea required.
 */
import { router } from 'expo-router';
import { useState } from 'react';

import {
  BackButton,
  Body,
  Button,
  Card,
  CountdownTimer,
  Field,
  PhotoEvidenceSlot,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { mockInfoRequestContext } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

export default function InfoRequestResponse() {
  const { theme } = useTheme();
  const ctx = mockInfoRequestContext;

  const [response, setResponse] = useState('');
  const [hasPhoto, setHasPhoto] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 800));
    setSubmitting(false);
    router.back();
  }

  return (
    <Screen title="Moderator information request" subtitle={ctx.item_title}>
      <BackButton />

      <CountdownTimer hoursLeft={ctx.sla_hours_left} />

      {/* Moderator's question — quoted for clarity */}
      <Card>
        <SectionLabel>Moderator&apos;s question</SectionLabel>
        <Body style={{ fontSize: 14, fontStyle: 'italic', color: theme.colors.textSecondary }}>
          {`"${ctx.moderator_query}"`}
        </Body>
      </Card>

      <Field
        label="Your response"
        value={response}
        onChangeText={setResponse}
        placeholder="Explain clearly what happened or provide the requested information..."
        multiline
      />

      <Card>
        <SectionLabel>Supporting photo (optional)</SectionLabel>
        <PhotoEvidenceSlot
          label="Evidence photo"
          hasPhoto={hasPhoto}
          onPress={() => setHasPhoto((v) => !v)}
        />
      </Card>

      <Button
        label="Submit response to moderator"
        icon="send"
        onPress={handleSubmit}
        loading={submitting}
        disabled={!response.trim() || submitting}
      />
    </Screen>
  );
}

