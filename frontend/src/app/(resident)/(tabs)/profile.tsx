import { router } from 'expo-router';
import { useState } from 'react';
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

// Plain-language meaning of each assurance state — concise, one line each.
const STATE_TEXT: Record<string, string> = {
  SUFFICIENT_EVIDENCE: 'Verified loans went well. The lender still decides.',
  REVIEW_RECOMMENDED: 'History is mixed or old — worth a closer look. This is normal.',
  INSUFFICIENT_EVIDENCE: 'Too little history yet. Not a negative finding; the lender decides.',
  ACTIVE_DISPUTE: 'A dispute is open. A moderator reviews before anything else happens.',
};

const PROMISES: [IconName, string][] = [
  ['lock', 'Only your neighbourhood is stored — never your exact address.'],
  ['badge', 'No identity-card numbers are kept.'],
  ['gavel', 'Nobody is restricted without a moderator decision on record.'],
  ['history', 'Every loan step is recorded and cannot be edited.'],
];

/** Compact theme picker — icon button opens a small inline picker with two colour dots. */
function CompactThemePicker() {
  const { theme, themes, setTheme } = useTheme();
  const [open, setOpen] = useState(false);

  // Representative swatch colours per theme
  const swatches: Record<string, string> = {
    terracotta: '#C1623F',
    creamgreen: '#4A7C59',
  };

  return (
    <View style={{ position: 'relative' }}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Choose theme"
        onPress={() => setOpen((v) => !v)}
        style={({ pressed }) => ({
          width: 36,
          height: 36,
          borderRadius: 18,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: theme.colors.surface,
          borderWidth: 1,
          borderColor: theme.colors.border,
          opacity: pressed ? 0.7 : 1,
        })}>
        <Icon name="palette" size={20} color={theme.colors.textSecondary} />
      </Pressable>

      {open ? (
        <View
          style={{
            position: 'absolute',
            top: 44,
            right: 0,
            flexDirection: 'row',
            gap: 10,
            padding: 12,
            borderRadius: theme.radius.md,
            backgroundColor: theme.colors.surface,
            borderWidth: 1,
            borderColor: theme.colors.border,
            zIndex: 100,
            shadowColor: '#000',
            shadowOpacity: 0.1,
            shadowRadius: 8,
            shadowOffset: { width: 0, height: 2 },
            elevation: 4,
          }}>
          {themes.map((t) => {
            const selected = theme.name === t.name;
            const color = swatches[t.name] ?? t.colors.primary;
            return (
              <Pressable
                key={t.name}
                accessibilityRole="radio"
                accessibilityLabel={`${t.label} theme`}
                accessibilityState={{ selected }}
                onPress={() => { setTheme(t.name); setOpen(false); }}
                style={({ pressed }) => ({
                  alignItems: 'center',
                  gap: 6,
                  opacity: pressed ? 0.75 : 1,
                })}>
                <View
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 16,
                    backgroundColor: color,
                    borderWidth: selected ? 3 : 1.5,
                    borderColor: selected ? theme.colors.text : theme.colors.border,
                  }}>
                  {selected ? (
                    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
                      <Icon name="check" size={16} color="#fff" />
                    </View>
                  ) : null}
                </View>
                <Text style={{ fontFamily: theme.fonts.regular, fontSize: 11, color: theme.colors.textSecondary }}>
                  {t.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      ) : null}
    </View>
  );
}

export default function Profile() {
  const { theme } = useTheme();
  const { signOut } = useAuth();
  const queue = useModerationQueue();
  const waiting = queue.data?.length ?? 0;

  // Mock user stats — wired to real API in Part B
  const mockStats: { icon: IconName; value: number; label: string }[] = [
    { icon: 'handshake', value: 3, label: 'Loans made' },
    { icon: 'inventory_2', value: 2, label: 'Items shared' },
    { icon: 'task_alt', value: 5, label: 'Completed' },
  ];

  return (
    <HeroScreen
      tabs
      height={190}
      hero={
        <View style={{ flex: 1, justifyContent: 'space-between' }}>
          {/* Theme picker in top-right of hero */}
          <View style={{ flexDirection: 'row', justifyContent: 'flex-end' }}>
            <CompactThemePicker />
          </View>
          <View style={{ gap: 4 }}>
            <SectionLabel color={theme.hero.textSoft}>Profile</SectionLabel>
            <Title size={30} color={theme.hero.text} style={{ fontFamily: theme.fonts.displayAlt }}>
              You and your evidence
            </Title>
          </View>
        </View>
      }>

      {/* User identity + stats card */}
      <Card style={{ gap: 14 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
          <View
            style={{
              width: 60,
              height: 60,
              borderRadius: 30,
              backgroundColor: theme.colors.primarySoft,
              alignItems: 'center',
              justifyContent: 'center',
            }}>
            <Text style={{ fontFamily: theme.fonts.black, fontSize: 24, color: theme.colors.primary }}>
              A
            </Text>
          </View>
          <View style={{ flex: 1, gap: 2 }}>
            <Text style={{ fontFamily: theme.fonts.bold, fontSize: 18, color: theme.colors.text }}>
              Areeba K.
            </Text>
            <Caption>Member of Gulberg Mohalla</Caption>
          </View>
        </View>

        {/* Stats row */}
        <View style={{ flexDirection: 'row', gap: 10 }}>
          {mockStats.map(({ icon, value, label }) => (
            <View
              key={label}
              style={{
                flex: 1,
                alignItems: 'center',
                gap: 4,
                padding: 10,
                borderRadius: theme.radius.sm,
                backgroundColor: theme.colors.accentSoft,
              }}>
              <Icon name={icon} size={18} color={theme.colors.accent} />
              <Text style={{ fontFamily: theme.fonts.black, fontSize: 20, color: theme.colors.text }}>{value}</Text>
              <Caption style={{ textAlign: 'center', fontSize: 11 }}>{label}</Caption>
            </View>
          ))}
        </View>

        {/* My Evidence link */}
        <Pressable
          accessibilityRole="button"
          onPress={() => router.push('/profile/evidence')}
          style={({ pressed }) => ({
            flexDirection: 'row',
            alignItems: 'center',
            gap: 10,
            padding: 12,
            borderRadius: theme.radius.sm,
            backgroundColor: theme.colors.surface2,
            opacity: pressed ? 0.75 : 1,
          })}>
          <Icon name="visibility" size={18} color={theme.colors.primary} />
          <Body style={{ flex: 1, fontSize: 14 }}>View my evidence profile</Body>
          <Icon name="chevron_right" size={18} color={theme.colors.textSecondary} />
        </Pressable>
      </Card>

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
        <SectionLabel>How Digital Mohalla works</SectionLabel>
        <Body muted style={{ fontSize: 13 }}>
          Lenders see a summary of verified loans — not a score about you. It is one of four states:
        </Body>
        {Object.entries(ASSURANCE).map(([state, a]) => {
          const tone = assuranceTone(theme, state);
          return (
            <View key={state} style={{ flexDirection: 'row', gap: 10, alignItems: 'flex-start' }}>
              <View
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 10,
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: tone.bg,
                  borderWidth: 1,
                  borderColor: tone.border,
                }}>
                <Icon name={a.icon} size={18} color={tone.fg} />
              </View>
              <View style={{ flex: 1, gap: 1 }}>
                <Text style={{ fontFamily: theme.fonts.bold, fontSize: 14, color: tone.fg }}>{a.label}</Text>
                <Caption style={{ color: theme.colors.textSecondary }}>{STATE_TEXT[state]}</Caption>
              </View>
            </View>
          );
        })}
      </Card>

      <Card>
        <SectionLabel>Our promises</SectionLabel>
        {PROMISES.map(([icon, text]) => (
          <View key={icon} style={{ flexDirection: 'row', gap: 10, alignItems: 'center' }}>
            <Icon name={icon} size={20} color={theme.colors.accent} />
            <Body style={{ flex: 1, fontSize: 13 }}>{text}</Body>
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
