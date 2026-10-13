import { router } from 'expo-router';
import { Image } from 'expo-image';
import { Pressable, Text, View } from 'react-native';

import { useModerationQueue } from '@/api/hooks';
import { useAuth } from '@/auth/AuthProvider';
import {
  ASSURANCE,
  assuranceTone,
  Body,
  Button,
  Caption,
  Card,
  HeroScreen,
  Icon,
  type IconName,
  SectionLabel,
  Title,
} from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

// Plain-language meaning of each assurance state (HCI analysis, "Assurance Card - Detailed States").
const STATE_TEXT: Record<string, string> = {
  SUFFICIENT_EVIDENCE: 'Verified loans like this one went well. The lender still decides.',
  REVIEW_RECOMMENDED: 'Some evidence is mixed, old or unusual, so it is worth a closer look. This is normal.',
  INSUFFICIENT_EVIDENCE: 'Too little verified history to judge yet. This is not a negative finding; the lender decides.',
  ACTIVE_DISPUTE: 'A dispute is open, so a moderator reviews it before anything else happens.',
};

const PROMISES: [IconName, string][] = [
  ['lock', 'Only your neighbourhood is stored, never your exact location or address.'],
  ['badge', 'No identity-card numbers are kept.'],
  ['gavel', 'Nobody is restricted without a moderator decision and a recorded reason.'],
  ['history', 'Every step of a loan is recorded and cannot be edited afterwards.'],
];

function ThemeOption({ name }: { name: string }) {
  const { theme, themes, setTheme } = useTheme();
  const t = themes.find((x) => x.name === name);
  if (!t) return null;
  const selected = theme.name === t.name;
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityLabel={`${t.label} theme`}
      accessibilityState={{ selected }}
      onPress={() => setTheme(t.name)}
      style={({ pressed }) => ({
        flex: 1,
        borderRadius: theme.radius.md,
        overflow: 'hidden',
        borderWidth: 2.5,
        borderColor: selected ? theme.colors.primary : theme.colors.hairline,
        backgroundColor: t.colors.surface,
        opacity: pressed ? 0.9 : 1,
      })}>
      <Image source={t.hero.image} contentFit="cover" contentPosition="top" style={{ height: 96 }} />
      <View style={{ padding: 10, gap: 6 }}>
        <View style={{ flexDirection: 'row', gap: 4 }}>
          {[t.colors.primary, t.colors.accent, t.colors.bg].map((c) => (
            <View key={c} style={{ width: 16, height: 16, borderRadius: 8, backgroundColor: c, borderWidth: 1, borderColor: t.colors.border }} />
          ))}
        </View>
        <Text style={{ fontFamily: t.fonts.bold, fontSize: 15, color: t.colors.text }}>{t.label}</Text>
        <Text style={{ fontFamily: t.fonts.regular, fontSize: 12, color: t.colors.textSecondary }}>{t.tagline}</Text>
      </View>
      {selected ? (
        <View
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            width: 26,
            height: 26,
            borderRadius: 13,
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: theme.colors.primary,
          }}>
          <Icon name="check" size={18} color={theme.colors.onPrimary} />
        </View>
      ) : null}
    </Pressable>
  );
}

export default function Profile() {
  const { theme, themes } = useTheme();
  const { signOut } = useAuth();
  const queue = useModerationQueue();
  const waiting = queue.data?.length ?? 0;
  return (
    <HeroScreen
      tabs
      height={190}
      hero={
        <View style={{ flex: 1, justifyContent: 'flex-end', gap: 4 }}>
          <SectionLabel color={theme.hero.textSoft}>Profile</SectionLabel>
          <Title size={30} color={theme.hero.text} style={{ fontFamily: theme.fonts.displayAlt }}>
            You and your evidence
          </Title>
        </View>
      }>
      {waiting > 0 ? (
        <Card>
          <SectionLabel>Moderation</SectionLabel>
          <Body muted style={{ fontSize: 14 }}>
            {waiting} {waiting === 1 ? 'case is' : 'cases are'} waiting in the communities you moderate.
          </Body>
          <Button label="Open the triage queue" icon="gavel" onPress={() => router.push('/moderation')} />
        </Card>
      ) : null}
      <Card>
        <SectionLabel>Appearance</SectionLabel>
        <View accessibilityRole="radiogroup" style={{ flexDirection: 'row', gap: 12 }}>
          {themes.map((t) => (
            <ThemeOption key={t.name} name={t.name} />
          ))}
        </View>
      </Card>

      <Card>
        <SectionLabel>How the evidence summary works</SectionLabel>
        <Body muted>
          When you ask to borrow, the lender sees a summary of verified evidence from earlier loans, not a
          score about you. It is one of four states:
        </Body>
        {Object.entries(ASSURANCE).map(([state, a]) => {
          const tone = assuranceTone(theme, state);
          return (
            <View key={state} style={{ flexDirection: 'row', gap: 12, alignItems: 'flex-start' }}>
              <View
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 12,
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: tone.bg,
                  borderWidth: 1,
                  borderColor: tone.border,
                }}>
                <Icon name={a.icon} size={20} color={tone.fg} />
              </View>
              <View style={{ flex: 1, gap: 2 }}>
                <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: tone.fg }}>{a.label}</Text>
                <Caption style={{ color: theme.colors.textSecondary }}>{STATE_TEXT[state]}</Caption>
              </View>
            </View>
          );
        })}
      </Card>

      <Card>
        <SectionLabel>Our promises</SectionLabel>
        {PROMISES.map(([icon, text]) => (
          <View key={icon} style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
            <Icon name={icon} size={22} color={theme.colors.accent} />
            <Body style={{ flex: 1, fontSize: 14 }}>{text}</Body>
          </View>
        ))}
      </Card>

      <Button label="Sign out" variant="outline" icon="logout" onPress={signOut} />
      <Caption style={{ textAlign: 'center' }}>
        Digital Mohalla · iteration 1 · all accounts and items are synthetic test data
      </Caption>
    </HeroScreen>
  );
}
