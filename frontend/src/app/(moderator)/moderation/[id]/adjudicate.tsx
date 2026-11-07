/**
 * W19 — Moderator Adjudication: Possession Exit (FR-I-04, DM14, ADR-0009)
 *
 * DM14 FIX: Dispute resolution MUST specify physical item possession.
 * Moderator selects one of four possession outcomes before committing.
 *
 * HCI notes:
 * - PossessionRadio component: icon + label + description + radio indicator.
 * - Decision reason is mandatory — submit button blocked until filled.
 * - "Commit" button uses a strong, unambiguous label (never just "Submit").
 */
import { useState } from 'react';
import { View } from 'react-native';

import {
  BackButton,
  Banner,
  Body,
  Button,
  Card,
  Caption,
  Field,
  PossessionRadio,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { mockPossessionOptions } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';
import { router } from 'expo-router';

export default function PossessionAdjudication() {
  const { theme } = useTheme();

  const [selectedPossession, setSelectedPossession] = useState<string | null>(null);
  const [depositRuling, setDepositRuling] = useState<'RETURN' | 'FORFEIT' | null>(null);
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = selectedPossession && reason.trim().length >= 20 && depositRuling;

  async function handleCommit() {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 1000));
    setSubmitting(false);
    router.back();
  }

  return (
    <Screen title="Adjudication" subtitle="Item possession & resolution">
      <BackButton />

      {/* Human-only mandate */}
      <Banner tone={theme.colors.warning} title="Human decision required" icon="gavel">
        <Body muted style={{ fontSize: 13 }}>
          Only authenticated moderators may commit a binding resolution. This action is final and appended to the immutable event log.
        </Body>
      </Banner>

      {/* Item possession selector — DM14 fix */}
      <Card>
        <SectionLabel>Where is the item now?</SectionLabel>
        <Caption style={{ marginBottom: 8 }}>
          Select the physical possession state before closing this case.
        </Caption>
        <View style={{ gap: 8 }}>
          {mockPossessionOptions.map((opt) => (
            <PossessionRadio
              key={opt.id}
              icon={opt.icon}
              label={opt.label}
              description={opt.description}
              selected={selectedPossession === opt.id}
              onPress={() => setSelectedPossession(opt.id)}
            />
          ))}
        </View>
      </Card>

      {/* Deposit ruling */}
      <Card>
        <SectionLabel>Deposit ruling</SectionLabel>
        <View style={{ flexDirection: 'row', gap: 10 }}>
          {(['RETURN', 'FORFEIT'] as const).map((v) => (
            <PossessionRadio
              key={v}
              icon={v === 'RETURN' ? 'undo' : 'savings'}
              label={v === 'RETURN' ? 'Return deposit to borrower' : 'Deposit forfeited to lender'}
              description={
                v === 'RETURN'
                  ? 'No damage or policy breach found.'
                  : 'Item damaged, not returned, or no-show.'
              }
              selected={depositRuling === v}
              onPress={() => setDepositRuling(v)}
            />
          ))}
        </View>
      </Card>

      {/* Mandatory reason */}
      <Field
        label="Adjudication reason (required — min 20 characters)"
        value={reason}
        onChangeText={setReason}
        placeholder="Explain your decision based on the evidence trail and applicable community rules..."
        multiline
      />
      {reason.length > 0 && reason.length < 20 && (
        <Caption style={{ color: theme.colors.warning.fg }}>
          {20 - reason.length} more characters required.
        </Caption>
      )}

      <Button
        label="Commit binding resolution"
        icon="gavel"
        onPress={handleCommit}
        loading={submitting}
        disabled={!canSubmit || submitting}
      />
    </Screen>
  );
}

