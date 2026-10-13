import { useState } from 'react';
import { Text, View } from 'react-native';

import { ApiError } from '@/api/client';
import { useAuth } from '@/auth/AuthProvider';
import {
  Body,
  Button,
  Caption,
  Card,
  ErrorText,
  Field,
  HeroScreen,
  Icon,
  SectionLabel,
  ThemeSwitcher,
  Title,
} from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

// Local demo helpers: the seeded SYNTHETIC users (scripts/seed_demo.py). The password comes from
// frontend/.env.local (EXPO_PUBLIC_DEMO_PASSWORD) and is never committed or built into the deployed site.
const DEMO_PASSWORD = process.env.EXPO_PUBLIC_DEMO_PASSWORD ?? '';
const DEMO_USERS = [
  ['Bilal (borrower)', 'borrower@example.test'],
  ['Chand (borrower)', 'borrower2@example.test'],
  ['Ayesha (lender)', 'lender@example.test'],
] as const;

function Pledge({ icon, text }: { icon: 'verified_user' | 'lock' | 'groups'; text: string }) {
  const { theme } = useTheme();
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
      <Icon name={icon} size={16} color={theme.hero.textSoft} />
      <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 12.5, color: theme.hero.textSoft }}>{text}</Text>
    </View>
  );
}

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
      await signIn(e.trim(), p);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? 'That email and password do not match. Check them and try again.'
          : 'We could not reach the server. It may be waking up; wait a few seconds and try again.',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <HeroScreen
      height={430}
      hero={
        <View style={{ flex: 1, justifyContent: 'space-between' }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <View
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                gap: 8,
                paddingVertical: 6,
                paddingHorizontal: 12,
                borderRadius: 9999,
                backgroundColor: 'rgba(255,255,255,0.28)',
              }}>
              <Icon name="location_city" size={18} color={theme.hero.text} />
              <Text style={{ fontFamily: theme.fonts.bold, fontSize: 13, color: theme.hero.text }}>
                Digital Mohalla
              </Text>
            </View>
            <ThemeSwitcher onImage />
          </View>
          <View style={{ gap: 10 }}>
            <Title size={34} color={theme.hero.text} style={{ fontFamily: theme.fonts.displayAlt }}>
              Borrow from neighbours, with evidence you can see.
            </Title>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 14 }}>
              <Pledge icon="verified_user" text="Verified neighbours" />
              <Pledge icon="lock" text="Private by design" />
              <Pledge icon="groups" text="Moderated" />
            </View>
          </View>
        </View>
      }>
      <Card style={{ padding: 22, gap: 16, borderRadius: theme.radius.lg }}>
        <View style={{ gap: 4 }}>
          <Title size={26}>Welcome back</Title>
          <Body muted>Sign in to see your requests and loans.</Body>
        </View>
        <Field
          label="Email"
          icon="mail"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoComplete="email"
          placeholder="you@example.test"
        />
        <Field
          label="Password"
          icon="lock"
          value={password}
          onChangeText={setPassword}
          secure
          autoComplete="password"
          placeholder="Your password"
        />
        <ErrorText message={error} />
        <Button
          label="Sign in"
          icon="login"
          loading={busy}
          disabled={!email || !password}
          onPress={() => submit(email, password)}
        />
      </Card>

      {DEMO_PASSWORD ? (
        <Card>
          <SectionLabel>Demo accounts (synthetic data)</SectionLabel>
          <View style={{ gap: 8 }}>
            {DEMO_USERS.map(([label, mail]) => (
              <Button
                key={mail}
                label={label}
                variant="soft"
                icon="person"
                compact
                disabled={busy}
                onPress={() => submit(mail, DEMO_PASSWORD)}
              />
            ))}
          </View>
        </Card>
      ) : null}

      <View style={{ flexDirection: 'row', gap: 8, paddingHorizontal: 6 }}>
        <Icon name="info" size={16} color={theme.colors.textMuted} />
        <Caption style={{ flex: 1 }}>
          Every account and item here is synthetic test data. Your exact location is never stored or shown;
          only your neighbourhood is.
        </Caption>
      </View>
    </HeroScreen>
  );
}
