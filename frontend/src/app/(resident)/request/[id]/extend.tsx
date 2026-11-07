/**
 * W13 — Loan Extension Request (FR-B-14, UC-B8)
 *
 * Both roles visit this screen: borrower requests → lender responds.
 * role param passed via searchParams ('BORROWER' | 'LENDER').
 *
 * HCI notes:
 * - Date stepper (+ / - days) instead of a full calendar — simpler for one task.
 * - Policy banner is advisory/neutral, never alarming.
 * - Two distinct CTAs for borrower vs lender so the action is never ambiguous.
 */
import { useLocalSearchParams, router } from 'expo-router';
import { useState } from 'react';
import { View, Text } from 'react-native';

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
import { mockExtensionContext } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

export default function LoanExtension() {
  const { theme } = useTheme();
  const { role = 'BORROWER' } = useLocalSearchParams<{ role?: string }>();
  const ctx = mockExtensionContext;

  const [extraDays, setExtraDays] = useState(1);
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isBorrower = role === 'BORROWER';

  const newReturnDate = 'Nov ' + (10 + extraDays) + ', 2026'; // mock date arithmetic

  async function handleSubmit() {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 800));
    setSubmitting(false);
    router.back();
  }

  return (
    <Screen title={isBorrower ? 'Request extension' : 'Extension request'} subtitle={ctx.item_title}>
      <BackButton />

      <Card>
        <SectionLabel>Current dates</SectionLabel>
        <Body muted style={{ fontSize: 14 }}>Return by {ctx.current_return_date}</Body>
      </Card>

      {isBorrower ? (
        <>
          <Card>
            <SectionLabel>New proposed return date</SectionLabel>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 16, justifyContent: 'center', paddingVertical: 8 }}>
              <Button
                label="-"
                variant="outline"
                onPress={() => setExtraDays((d) => Math.max(1, d - 1))}
                style={{ width: 48, height: 48 }}
              />
              <Text style={{ fontFamily: theme.fonts.black, fontSize: 26, color: theme.colors.text }}>{extraDays}d</Text>
              <Button
                label="+"
                variant="outline"
                onPress={() => setExtraDays((d) => Math.min(7, d + 1))}
                style={{ width: 48, height: 48 }}
              />
            </View>
            <DateRangePill start="Now" end={newReturnDate} />
          </Card>

          <Field
            label="Why do you need more time?"
            value={reason}
            onChangeText={setReason}
            placeholder="e.g. Project took longer than expected"
            multiline
          />

          <Banner tone={theme.colors.info} title="Extension policy" icon="info">
            <Body muted style={{ fontSize: 13 }}>
              Extensions must be agreed before the original due date to avoid automatic late-return recording.
            </Body>
          </Banner>

          <Button
            label="Send extension request"
            icon="send"
            onPress={handleSubmit}
            loading={submitting}
            disabled={!reason.trim() || submitting}
          />
        </>
      ) : (
        /* Lender response view */
        <>
          <Card>
            <SectionLabel>Borrower&apos;s request</SectionLabel>
            <Body muted>{ctx.borrower_name} has requested an extra {extraDays} day(s).</Body>
            <Body muted>New return date: {newReturnDate}</Body>
          </Card>

          <View style={{ flexDirection: 'row', gap: 12 }}>
            <Button
              label="Accept extension"
              icon="check"
              onPress={handleSubmit}
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

