/**
 * W17 — Inspection Photo Gallery & Upload Modal (FR-B-11, FR-B-12, FR-B-17)
 *
 * Shows two photo slots (front/overall and working parts).
 * EXIF metadata stripping is surfaced to the user (privacy by design).
 *
 * HCI notes:
 * - Each slot is a large Pressable area — well above 48dp minimum target.
 * - "GPS stripped" badge on each slot reassures without lecturing.
 * - Fallback checkbox: "Cannot provide photos" — reduces evidence state, never blocks the flow.
 */
import { useState } from 'react';
import { View } from 'react-native';

import {
  BackButton,
  Banner,
  Body,
  Button,
  Card,
  Check,
  PhotoEvidenceSlot,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { mockPhotoSlots } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';
import { router } from 'expo-router';

export default function PhotoEvidence() {
  const { theme } = useTheme();
  const [slots, setSlots] = useState(mockPhotoSlots.map((s) => ({ ...s })));
  const [noPhotos, setNoPhotos] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  function togglePhoto(id: string) {
    // Stub: replace with expo-image-picker call
    setSlots((prev) => prev.map((s) => (s.id === id ? { ...s, hasPhoto: !s.hasPhoto } : s)));
  }

  const hasAnyPhoto = slots.some((s) => s.hasPhoto);
  const canContinue = noPhotos || hasAnyPhoto;

  async function handleContinue() {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 600));
    setSubmitting(false);
    router.back();
  }

  return (
    <Screen title="Handover photos" subtitle="Evidence of item condition at handover">
      <BackButton />

      <Banner tone={theme.colors.info} title="Privacy protected" icon="shield">
        <Body muted style={{ fontSize: 13 }}>
          EXIF metadata including GPS location is automatically stripped from every photo you upload.
        </Body>
      </Banner>

      <Card>
        <SectionLabel>Add up to 2 photos</SectionLabel>
        <View style={{ flexDirection: 'row', gap: 12 }}>
          {slots.map((slot) => (
            <PhotoEvidenceSlot
              key={slot.id}
              label={slot.label}
              hasPhoto={slot.hasPhoto}
              onPress={() => !noPhotos && togglePhoto(slot.id)}
            />
          ))}
        </View>
      </Card>

      <Check
        label="I cannot provide photos right now — proceed with reduced evidence status"
        checked={noPhotos}
        onPress={() => {
          setNoPhotos((v) => !v);
          if (!noPhotos) setSlots((prev) => prev.map((s) => ({ ...s, hasPhoto: false })));
        }}
      />

      <Button
        label="Continue"
        icon="arrow_forward"
        onPress={handleContinue}
        loading={submitting}
        disabled={!canContinue || submitting}
      />
    </Screen>
  );
}

