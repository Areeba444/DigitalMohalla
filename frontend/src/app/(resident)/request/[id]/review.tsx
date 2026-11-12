/**
 * W15 — Bilateral Review & Rating Submission (FR-D-01, FR-T-09, FR-B-15)
 *
 * Unlocked only on COMPLETED loans. Multi-dimensional — NO star ratings.
 * Both parties review independently; reviews are immutable after submission.
 *
 * HCI notes:
 * - Three toggle rows (not 1–5 stars) — aligns with NFR-U-01 multi-dimensional design.
 * - Each choice has an icon + text, never colour alone.
 * - Anti-collusion notice shown before submission (transparency).
 */
import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import {
  BackButton,
  Banner,
  Body,
  Button,
  Card,
  Chip,
  Field,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { mockReviewContext } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

type DimChoice<T extends string> = { key: T; label: string };

function DimRow<T extends string>({
  label,
  choices,
  value,
  onChange,
}: {
  label: string;
  choices: DimChoice<T>[];
  value: T | null;
  onChange: (v: T) => void;
}) {
  return (
    <View style={{ gap: 6 }}>
      <SectionLabel>{label}</SectionLabel>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        {choices.map((c) => (
          <Chip
            key={c.key}
            label={c.label}
            selected={value === c.key}
            onPress={() => onChange(c.key)}
          />
        ))}
      </View>
    </View>
  );
}

export default function BilateralReview() {
  const { theme } = useTheme();
  const ctx = mockReviewContext;

  const [punctuality, setPunctuality] = useState<string | null>(null);
  const [care, setCare] = useState<string | null>(null);
  const [neighborly, setNeighborly] = useState<string | null>(null);
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = punctuality && care && neighborly;

  async function handleSubmit() {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 900));
    setSubmitting(false);
    router.back();
  }

  return (
    <Screen
      title="Review your exchange"
      subtitle={`With ${ctx.peer_name} · ${ctx.item_title}`}>
      <BackButton />

      <Card>
        <Body muted style={{ fontSize: 14 }}>
          Reviews are multi-dimensional — not stars. Your honest input helps the community make better lending decisions.
        </Body>
      </Card>

      <DimRow
        label="Punctuality & communication"
        choices={[
          { key: 'ON_TIME', label: 'On time' },
          { key: 'DELAYED_OK', label: 'Slightly delayed — communicated' },
          { key: 'DELAYED_NO_NOTICE', label: 'Delayed with no notice' },
        ]}
        value={punctuality}
        onChange={setPunctuality}
      />

      <DimRow
        label="Item condition care"
        choices={[
          { key: 'AS_DESCRIBED', label: 'Returned as described' },
          { key: 'MINOR_WEAR', label: 'Minor acceptable wear' },
          { key: 'ISSUE_REPORTED', label: 'Issue reported — was noted' },
        ]}
        value={care}
        onChange={setCare}
      />

      <DimRow
        label="Neighbourliness"
        choices={[
          { key: 'COOPERATIVE', label: 'Cooperative & friendly' },
          { key: 'NEUTRAL', label: 'Neutral — no issues' },
          { key: 'DIFFICULT', label: 'Difficult to coordinate' },
        ]}
        value={neighborly}
        onChange={setNeighborly}
      />

      <Field
        label="Objective comments (optional)"
        value={comments}
        onChangeText={setComments}
        placeholder="Describe what happened — focus on observable facts."
        multiline
      />

      {/* Anti-collusion transparency notice */}
      <Banner tone={theme.colors.info} title="How reviews are used" icon="info">
        <Body muted style={{ fontSize: 13 }}>
          Reviews are screened for reciprocal collusion rings before entering assurance history.
        </Body>
      </Banner>

      <Button
        label="Submit review (immutable)"
        icon="rate_review"
        onPress={handleSubmit}
        loading={submitting}
        disabled={!canSubmit || submitting}
      />
    </Screen>
  );
}

