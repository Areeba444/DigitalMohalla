import { useState } from 'react';
import { Text, View } from 'react-native';

import { ApiError } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';
import {
  Body,
  Button,
  Card,
  ErrorText,
  Field,
  Screen,
  SectionLabel,
  ThemeSwitcher,
} from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

// Local demo helpers: the seeded SYNTHETIC users (scripts/seed_demo.py). The password comes from
// frontend/.env.local (EXPO_PUBLIC_DEMO_PASSWORD) and is never committed.
const DEMO_PASSWORD = process.env.EXPO_PUBLIC_DEMO_PASSWORD ?? '';
const DEMO_USERS = [
  ['Bilal (borrower)', 'borrower@example.test'],
  ['Chand (borrower)', 'borrower2@example.test'],
  ['Ayesha (lender)', 'lender@example.test'],
] as const;

export default function Login() {
  const { theme } = useTheme();
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: string, p: string) => {
    setBusy(true);
    setError(null);
    try {
      await signIn(e, p);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? 'Invalid email or password.'
          : 'Cannot reach the server. Check that the API is running and try again.',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen
      title="Digital Mohalla"
      subtitle="Borrow and lend within your neighbourhood"
      right={<ThemeSwitcher />}>
      <Card>
        <Text
          style={{
            fontSize: 22,
            fontWeight: '700',
            color: theme.colors.text,
            fontFamily: theme.fontDisplay,
          }}>
          Welcome back
        </Text>
        <Body muted>Sign in to see your requests and loans.</Body>
        <Field label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" />
        <Field label="Password" value={password} onChangeText={setPassword} secure />
        <ErrorText message={error} />
        <Button label="Sign in" loading={busy} onPress={() => submit(email, password)} />
      </Card>

      {DEMO_PASSWORD ? (
        <Card>
          <SectionLabel>Demo accounts (synthetic data)</SectionLabel>
          <Body muted>Tap one to sign in as a seeded test user.</Body>
          <View style={{ gap: 8 }}>
            {DEMO_USERS.map(([label, mail]) => (
              <Button
                key={mail}
                label={label}
                variant="outline"
                disabled={busy}
                onPress={() => submit(mail, DEMO_PASSWORD)}
              />
            ))}
          </View>
        </Card>
      ) : null}
    </Screen>
  );
}
