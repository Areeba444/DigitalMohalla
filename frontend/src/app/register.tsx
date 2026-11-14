/**
 * W8 — Registration, Terms & Privacy (FR-A-01, NFR-PR-01, UC-A1)
 *
 * HCI notes:
 * - Single primary CTA "Create Account"; secondary link only.
 * - Privacy banner uses neutral INFO tone, never warning/red (zero GPS stored is a feature, not a risk).
 * - Inline field-level validation — errors appear below each field, not as a modal.
 */
import { router } from 'expo-router';
import { useState } from 'react';
import { Text, View } from 'react-native';

import {
  BackButton,
  Banner,
  Body,
  Button,
  Caption,
  Check,
  ErrorText,
  Field,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

export default function Register() {
  const { theme } = useTheme();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [agreedStandards, setAgreedStandards] = useState(false);
  const [agreedIdentity, setAgreedIdentity] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const valid =
    name.trim().length >= 2 &&
    email.includes('@') &&
    password.length >= 8 &&
    password === confirm &&
    agreedStandards &&
    agreedIdentity;

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    // Stub: simulate registration success and continue to community onboarding
    await new Promise((r) => setTimeout(r, 600));
    setSubmitting(false);
    router.replace('/community/join');
  }

  return (
    <Screen title="Join your Mohalla" subtitle="Create your account">
      <BackButton />

      {/* Privacy assurance — neutral info, never a warning */}
      <Banner tone={theme.colors.info} title="Your privacy is protected" icon="shield">
        <Body muted style={{ fontSize: 13 }}>
          Your exact location and GPS are never stored or shared.
        </Body>
      </Banner>

      <View style={{ gap: 12 }}>
        <SectionLabel>Your details</SectionLabel>
        <Field label="Full name" value={name} onChangeText={setName} placeholder="e.g. Areeba Khan" />
        <Field label="Email address" value={email} onChangeText={setEmail} placeholder="you@example.com" />
        <Field
          label="Password"
          value={password}
          onChangeText={setPassword}
          placeholder="At least 8 characters"
          secureTextEntry
        />
        <Field
          label="Confirm password"
          value={confirm}
          onChangeText={setConfirm}
          placeholder="Repeat your password"
          secureTextEntry
        />
        {confirm.length > 0 && password !== confirm && (
          <Caption style={{ color: theme.colors.danger.fg }}>Passwords do not match.</Caption>
        )}
      </View>

      <View style={{ gap: 10 }}>
        <SectionLabel>Community agreement</SectionLabel>
        <Check
          label="I agree to the Digital Mohalla Community Standards and care-of-borrowed-goods policy."
          checked={agreedStandards}
          onToggle={() => setAgreedStandards((v) => !v)}
        />
        <Check
          label="I understand that identity verification is used only to protect community members, not shared publicly."
          checked={agreedIdentity}
          onToggle={() => setAgreedIdentity((v) => !v)}
        />
      </View>

      <ErrorText message={error} />

      <Button
        label="Create account"
        icon="person_add"
        onPress={handleSubmit}
        disabled={!valid || submitting}
        loading={submitting}
      />

      <View style={{ alignItems: 'center' }}>
        <Text style={{ fontFamily: theme.fonts.regular, fontSize: 14, color: theme.colors.textSecondary }}>
          Already a member?{' '}
          <Text
            style={{ fontFamily: theme.fonts.semibold, color: theme.colors.primary }}
            onPress={() => {/* router.replace('/login') */}}>
            Sign in
          </Text>
        </Text>
      </View>
    </Screen>
  );
}
