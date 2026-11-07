/**
 * W14 — Counter-Offer: Propose & Review (FR-B-10, FR-B-06, ADR-0015)
 *
 * Lender proposes alternative dates; borrower sees and responds.
 * role param: 'LENDER' (compose) | 'BORROWER' (review)
 *
 * HCI notes:
 * - Side-by-side: original dates vs proposed dates helps user scan the delta instantly.
 * - Duration recalculation notice is a neutral info banner, not an alarm.
 * - Two buttons are styled as primary (Accept) + outline (Decline) — clear visual hierarchy.
 */
import { useLocalSearchParams, router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import {
  BackButton,
  Banner,
  Body,
  Button,
  Card,
  DateRangePill,
  Field,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { mockCounterOfferContext } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

export default function CounterOffer() {
  const { theme } = useTheme();
  const { role = 'LENDER' } = useLocalSearchParams<{ role?: string }>();
  const ctx = mockCounterOfferContext;

  const [altStart, setAltStart] = useState('Nov 12, 2026');
  const [altEnd, setAltEnd] = useState('Nov 14, 2026');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isLender = role === 'LENDER';

  async function handleAction(accepted: boolean) {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 700));
    setSubmitting(false);
    router.back();
  }

  return (
    <Screen
      title={isLender ? 'Propose alternative dates' : 'Counter-offer received'}
      subtitle={ctx.item_title}>
      <BackButton />

      {/* Original request summary */}
      <Card>
        <SectionLabel>Original request</SectionLabel>
        <DateRangePill start={ctx.original_start} end={ctx.original_end} />
        <Body muted style={{ fontSize: 13, marginTop: 4 }}>
          Requested by {ctx.borrower_name}
        </Body>
      </Card>

      {isLender ? (
        <>
          <Card>
            <SectionLabel>Your proposed dates</SectionLabel>
            <DateRangePill start={altStart} end={altEnd} />
            <Body muted style={{ fontSize: 13, marginTop: 6 }}>
              Adjust by editing the dates below (max 7 days).
            </Body>
            <Field label="New start date" value={altStart} onChangeText={setAltStart} placeholder="e.g. Nov 12, 2026" />
            <Field label="New end date" value={altEnd} onChangeText={setAltEnd} placeholder="e.g. Nov 14, 2026" />
          </Card>

          <Field
            label="Note to borrower (optional)"
            value={message}
            onChangeText={setMessage}
            placeholder="e.g. Drill is currently in use; available this weekend instead."
            multiline
          />

          <Banner tone={theme.colors.info} title="Dates re-evaluated" icon="info">
            <Body muted style={{ fontSize: 13 }}>
              Changing dates re-checks availability and re-calculates the loan duration.
            </Body>
          </Banner>

          <Button
            label="Send counter-offer"
            icon="swap_horiz"
            onPress={() => handleAction(true)}
            loading={submitting}
            disabled={!altStart || !altEnd || submitting}
          />
        </>
      ) : (
        /* Borrower response view */
        <>
          <Card>
            <SectionLabel>Proposed by {ctx.lender_name}</SectionLabel>
            <DateRangePill start={altStart} end={altEnd} />
            {message ? (
              <Body muted style={{ fontSize: 14, marginTop: 6 }}>{`"${message}"`}</Body>
            ) : null}
          </Card>

          <View style={{ flexDirection: 'row', gap: 12 }}>
            <Button
              label="Accept dates"
              icon="check"
              onPress={() => handleAction(true)}
              loading={submitting}
              style={{ flex: 1 }}
            />
            <Button
              label="Decline"
              icon="close"
              variant="outline"
              onPress={() => router.back()}
              style={{ flex: 1 }}
            />
          </View>
        </>
      )}
    </Screen>
  );
}

