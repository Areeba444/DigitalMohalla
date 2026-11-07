/**
 * W22 — Create & Edit Item Listing (FR-B-01, Module 3)
 *
 * 3-step stepper: Details → Photos & Terms → Publish.
 * Roman Urdu hints as autocomplete suggestions.
 * Draft saving affordance alongside primary Publish CTA.
 *
 * HCI notes:
 * - Multi-step wizard (Hick's Law) — only the current step's form is shown.
 * - LoanProgress stepper shows where you are (3 steps, not 5).
 * - Deposit field is clearly "record-only, no in-app payment" (plain language).
 */
import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View, Text } from 'react-native';

import {
  BackButton,
  Banner,
  Body,
  Button,
  Card,
  Caption,
  Chip,
  Field,
  PhotoEvidenceSlot,
  Screen,
  SectionLabel,
} from '@/components/ui';
import {
  ITEM_CATEGORIES,
  ITEM_CONDITIONS,
  ROMAN_URDU_HINTS,
} from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

type Step = 1 | 2 | 3;

function StepIndicator({ step, theme }: { step: Step; theme: any }) {
  const labels = ['Details', 'Photos', 'Publish'];
  return (
    <View style={{ flexDirection: 'row', gap: 0, marginBottom: 4 }}>
      {labels.map((label, i) => {
        const done = i + 1 < step;
        const current = i + 1 === step;
        return (
          <View key={label} style={{ flex: 1, alignItems: 'center', gap: 4 }}>
            <View
              style={{
                width: 28,
                height: 28,
                borderRadius: 14,
                backgroundColor: done || current ? theme.colors.primary : theme.colors.surface,
                borderWidth: 2,
                borderColor: done || current ? theme.colors.primary : theme.colors.border,
                alignItems: 'center',
                justifyContent: 'center',
              }}>
              <Text
                style={{
                  fontFamily: theme.fonts.bold,
                  fontSize: 13,
                  color: done || current ? theme.colors.onPrimary : theme.colors.textMuted,
                }}>
                {i + 1}
              </Text>
            </View>
            <Caption
              style={{
                color: current ? theme.colors.primary : theme.colors.textMuted,
                fontFamily: current ? theme.fonts.semibold : theme.fonts.regular,
              }}>
              {label}
            </Caption>
          </View>
        );
      })}
    </View>
  );
}

export default function CreateItem() {
  const { theme } = useTheme();

  const [step, setStep] = useState<Step>(1);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [condition, setCondition] = useState('');
  const [description, setDescription] = useState('');
  const [deposit, setDeposit] = useState('');
  const [hasPhoto1, setHasPhoto1] = useState(false);
  const [hasPhoto2, setHasPhoto2] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const step1Valid = title.trim().length >= 2 && category && condition;

  async function handlePublish() {
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 900));
    setSubmitting(false);
    router.back();
  }

  return (
    <Screen title="Share an item" subtitle="Step-by-step listing">
      <BackButton />
      <StepIndicator step={step} theme={theme} />

      {step === 1 && (
        <>
          <Card>
            <SectionLabel>What are you sharing?</SectionLabel>
            <Field
              label="Item name"
              value={title}
              onChangeText={setTitle}
              placeholder="e.g. Power Drill, Silai machine, Istari"
            />
            {/* Roman Urdu hints */}
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={{ marginHorizontal: -4 }}
              contentContainerStyle={{ paddingHorizontal: 4, gap: 6 }}>
              {ROMAN_URDU_HINTS.map((hint) => (
                <Chip
                  key={hint}
                  label={hint}
                  selected={false}
                  onPress={() => setTitle(hint)}
                />
              ))}
            </ScrollView>
          </Card>

          <Card>
            <SectionLabel>Category</SectionLabel>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
              {ITEM_CATEGORIES.map((c) => (
                <Chip
                  key={c.key}
                  label={c.label}
                  selected={category === c.key}
                  onPress={() => setCategory(c.key)}
                />
              ))}
            </View>
          </Card>

          <Card>
            <SectionLabel>Condition</SectionLabel>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
              {ITEM_CONDITIONS.map((c) => (
                <Chip
                  key={c.key}
                  label={c.label}
                  selected={condition === c.key}
                  onPress={() => setCondition(c.key)}
                />
              ))}
            </View>
          </Card>

          <Field
            label="Description"
            value={description}
            onChangeText={setDescription}
            placeholder="Describe your item — the more detail, the better the search match."
            multiline
          />

          <Button label="Next: Photos & terms" icon="arrow_forward" disabled={!step1Valid} onPress={() => setStep(2)} />
        </>
      )}

      {step === 2 && (
        <>
          <Card>
            <SectionLabel>Item photos (optional but recommended)</SectionLabel>
            <View style={{ flexDirection: 'row', gap: 12 }}>
              <PhotoEvidenceSlot label="Main photo" hasPhoto={hasPhoto1} onPress={() => setHasPhoto1((v) => !v)} />
              <PhotoEvidenceSlot label="Detail / label" hasPhoto={hasPhoto2} onPress={() => setHasPhoto2((v) => !v)} />
            </View>
          </Card>

          <Card>
            <SectionLabel>Security deposit (optional)</SectionLabel>
            <Field
              label="Deposit amount (PKR) — record only"
              value={deposit}
              onChangeText={(t) => setDeposit(t.replace(/[^0-9]/g, ''))}
              placeholder="e.g. 500"
            />
            <Banner tone={theme.colors.info} title="Record-only" icon="info">
              <Body muted style={{ fontSize: 13 }}>
                No money is transferred in-app. This amount is a community agreement — record it on paper.
              </Body>
            </Banner>
          </Card>

          <View style={{ flexDirection: 'row', gap: 10 }}>
            <Button label="Back" icon="arrow_back" variant="outline" onPress={() => setStep(1)} style={{ flex: 1 }} />
            <Button label="Review & publish" icon="arrow_forward" onPress={() => setStep(3)} style={{ flex: 1 }} />
          </View>
        </>
      )}

      {step === 3 && (
        <>
          <Card>
            <SectionLabel>Review your listing</SectionLabel>
            <Body style={{ fontSize: 15, fontFamily: theme.fonts.bold }}>{title || '(no title)'}</Body>
            <Caption>{category} · {condition}</Caption>
            {description ? <Body muted style={{ fontSize: 14 }}>{description}</Body> : null}
            {deposit ? <Caption>Deposit: PKR {deposit} (record-only)</Caption> : null}
          </Card>

          <View style={{ flexDirection: 'row', gap: 10 }}>
            <Button label="Save draft" icon="save" variant="outline" onPress={() => router.back()} style={{ flex: 1 }} />
            <Button
              label="Publish listing"
              icon="publish"
              onPress={handlePublish}
              loading={submitting}
              style={{ flex: 1 }}
            />
          </View>
        </>
      )}
    </Screen>
  );
}

