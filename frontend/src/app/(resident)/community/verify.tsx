/**
 * W10 — Locality Verification (FR-A-07, FR-A-08, FR-A-09, ES-09, ES-10, DM02)
 *
 * Shows a 3-valued result — VERIFIED / INCONCLUSIVE / CONFLICTING.
 * Never auto-rejects. CONFLICTING is neutral, not a failure.
 *
 * HCI notes:
 * - Result banner uses appropriate tone: success (green) for VERIFIED,
 *   neutral info (blue-grey) for INCONCLUSIVE and CONFLICTING. NEVER red.
 * - GPS coordinates are checked in-memory and immediately discarded — communicated clearly.
 */
import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import {
  BackButton,
  Banner,
  Body,
  Button,
  Caption,
  Card,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { mockVerificationResults, type LocalityVerificationResult } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

function ResultBanner({ result }: { result: LocalityVerificationResult }) {
  const { theme } = useTheme();
  const tone =
    result.status === 'VERIFIED'
      ? theme.colors.success
      : theme.colors.info; // INCONCLUSIVE and CONFLICTING are both neutral-info, never red

  const icon =
    result.status === 'VERIFIED' ? 'check_circle' : 'info';

  return (
    <Banner tone={tone} title={result.status === 'VERIFIED' ? 'Location confirmed' : 'Sent for review'} icon={icon}>
      <Body muted style={{ fontSize: 13 }}>
        {result.message}
      </Body>
      {'next' in result ? (
        <Caption style={{ marginTop: 4, color: tone.fg, opacity: 0.85 }}>{result.next}</Caption>
      ) : null}
    </Banner>
  );
}

export default function LocalityVerify() {
  const { theme } = useTheme();
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<LocalityVerificationResult | null>(null);

  async function handleGeofenceCheck() {
    setChecking(true);
    // Stub: replace with real expo-location call that checks geofence and immediately discards coordinates
    await new Promise((r) => setTimeout(r, 1200));
    setChecking(false);
    // Cycle through mock results for testing (random pick simulates backend response)
    const statuses: (keyof typeof mockVerificationResults)[] = ['VERIFIED', 'INCONCLUSIVE', 'CONFLICTING'];
    const pick = statuses[Math.floor(Math.random() * statuses.length)];
    setResult(mockVerificationResults[pick]);
  }

  const isVerified = result?.status === 'VERIFIED';

  return (
    <Screen title="Confirm your locality" subtitle="Step 2 of 2">
      <BackButton />

      {/* Privacy reassurance — featured prominently before any location action */}
      <Banner tone={theme.colors.info} title="How we use your location" icon="location_off">
        <Body muted style={{ fontSize: 13 }}>
          Your coordinates are checked in-memory and immediately discarded. We never store a GPS pin.
        </Body>
      </Banner>

      {!result ? (
        <>
          <Card>
            <SectionLabel>Method A — Automatic check</SectionLabel>
            <Body muted style={{ fontSize: 14 }}>
              Allow a one-time location check to confirm you are within the community boundary.
            </Body>
            <Button
              label="Verify my location"
              icon="my_location"
              onPress={handleGeofenceCheck}
              loading={checking}
              disabled={checking}
            />
          </Card>

          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
            <View style={{ flex: 1, height: 1, backgroundColor: theme.colors.hairline }} />
            <Caption>or</Caption>
            <View style={{ flex: 1, height: 1, backgroundColor: theme.colors.hairline }} />
          </View>

          <Card>
            <SectionLabel>Method B — Invitation code</SectionLabel>
            <Body muted style={{ fontSize: 14 }}>
              If you already entered a code on the previous screen, tap below to submit your request.
            </Body>
            <Button
              label="Submit invitation code"
              icon="key"
              variant="outline"
              onPress={() => setResult(mockVerificationResults['INCONCLUSIVE'])}
            />
          </Card>
        </>
      ) : (
        <>
          <ResultBanner result={result} />

          {isVerified ? (
            <Button
              label="Continue to home"
              icon="arrow_forward"
              onPress={() => router.replace('/')}
            />
          ) : (
            <Button
              label="Done — I will wait for the moderator"
              icon="check"
              variant="outline"
              onPress={() => router.replace('/')}
            />
          )}
        </>
      )}
    </Screen>
  );
}

