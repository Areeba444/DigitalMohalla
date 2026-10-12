import { router } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
  type StyleProp,
  type TextStyle,
  type ViewStyle,
} from 'react-native';

import { useTheme } from '@/theme/ThemeProvider';
import type { Tone } from '@/theme/themes';

/* ------------------------------------------------------------------ layout */

export function Screen({
  title,
  subtitle,
  back,
  right,
  children,
}: {
  title: string;
  subtitle?: string;
  back?: boolean;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  const { theme } = useTheme();
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.bg }}>
      <View
        style={{
          width: '100%',
          maxWidth: 480,
          alignSelf: 'center',
          flex: 1,
          backgroundColor: theme.colors.bg,
        }}>
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 10,
            paddingHorizontal: 16,
            paddingVertical: 14,
            borderBottomWidth: 1,
            borderBottomColor: theme.colors.border,
            backgroundColor: theme.colors.surface,
          }}>
          {back ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Back"
              onPress={() => (router.canGoBack() ? router.back() : router.replace('/'))}
              hitSlop={10}>
              <Text style={{ fontSize: 22, color: theme.colors.primary }}>←</Text>
            </Pressable>
          ) : null}
          <View style={{ flex: 1 }}>
            <Text
              style={{
                fontSize: 18,
                fontWeight: '700',
                color: theme.colors.text,
                fontFamily: theme.fontDisplay,
              }}>
              {title}
            </Text>
            {subtitle ? (
              <Text style={{ fontSize: 12, color: theme.colors.textMuted }}>{subtitle}</Text>
            ) : null}
          </View>
          {right}
        </View>
        <ScrollView contentContainerStyle={{ padding: 16, gap: 14, paddingBottom: 48 }}>
          {children}
        </ScrollView>
      </View>
    </View>
  );
}

export function Card({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  const { theme } = useTheme();
  return (
    <View
      style={[
        {
          backgroundColor: theme.colors.surface,
          borderRadius: theme.radius.md,
          borderWidth: 1,
          borderColor: theme.colors.border,
          padding: 16,
          gap: 10,
        },
        style,
      ]}>
      {children}
    </View>
  );
}

export function SectionLabel({ children }: { children: string }) {
  const { theme } = useTheme();
  return (
    <Text
      style={{
        fontSize: 11,
        fontWeight: '700',
        letterSpacing: 1,
        textTransform: 'uppercase',
        color: theme.colors.textMuted,
      }}>
      {children}
    </Text>
  );
}

export function Body({
  children,
  muted,
  style,
}: {
  children: React.ReactNode;
  muted?: boolean;
  style?: StyleProp<TextStyle>;
}) {
  const { theme } = useTheme();
  return (
    <Text
      style={[
        {
          fontSize: 14,
          lineHeight: 21,
          color: muted ? theme.colors.textSecondary : theme.colors.text,
          fontFamily: theme.fontBody,
        },
        style,
      ]}>
      {children}
    </Text>
  );
}

export function Row({ label, value }: { label: string; value: string }) {
  const { theme } = useTheme();
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 12 }}>
      <Text style={{ fontSize: 13, color: theme.colors.textMuted }}>{label}</Text>
      <Text
        style={{
          fontSize: 13,
          fontWeight: '600',
          color: theme.colors.text,
          flexShrink: 1,
          textAlign: 'right',
        }}>
        {value}
      </Text>
    </View>
  );
}

/* ------------------------------------------------------------------ controls */

export function Button({
  label,
  onPress,
  variant = 'primary',
  loading,
  disabled,
}: {
  label: string;
  onPress: () => void;
  variant?: 'primary' | 'outline' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
}) {
  const { theme } = useTheme();
  const off = disabled || loading;
  const primary = variant === 'primary';
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: !!off }}
      onPress={off ? undefined : onPress}
      style={({ pressed }) => ({
        minHeight: 48,
        paddingHorizontal: 18,
        borderRadius: theme.radius.sm,
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'row',
        gap: 8,
        opacity: off ? 0.55 : pressed ? 0.85 : 1,
        backgroundColor: primary ? theme.colors.primary : 'transparent',
        borderWidth: variant === 'outline' ? 1.5 : 0,
        borderColor: theme.colors.primary,
      })}>
      {loading ? (
        <ActivityIndicator color={primary ? theme.colors.onPrimary : theme.colors.primary} />
      ) : null}
      <Text
        style={{
          fontSize: 15,
          fontWeight: '700',
          color: primary ? theme.colors.onPrimary : theme.colors.primary,
        }}>
        {label}
      </Text>
    </Pressable>
  );
}

export function Field({
  label,
  value,
  onChangeText,
  placeholder,
  multiline,
  secure,
  keyboardType,
}: {
  label: string;
  value: string;
  onChangeText: (v: string) => void;
  placeholder?: string;
  multiline?: boolean;
  secure?: boolean;
  keyboardType?: 'default' | 'email-address' | 'numeric';
}) {
  const { theme } = useTheme();
  return (
    <View style={{ gap: 6 }}>
      <Text style={{ fontSize: 13, fontWeight: '600', color: theme.colors.textSecondary }}>
        {label}
      </Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={theme.colors.textMuted}
        multiline={multiline}
        secureTextEntry={secure}
        keyboardType={keyboardType}
        autoCapitalize="none"
        style={{
          minHeight: multiline ? 84 : 46,
          paddingHorizontal: 12,
          paddingVertical: 10,
          borderRadius: theme.radius.sm,
          borderWidth: 1,
          borderColor: theme.colors.border,
          backgroundColor: theme.colors.surface2,
          color: theme.colors.text,
          fontSize: 15,
          textAlignVertical: multiline ? 'top' : 'center',
        }}
      />
    </View>
  );
}

export function Check({
  label,
  checked,
  onToggle,
}: {
  label: string;
  checked: boolean;
  onToggle: () => void;
}) {
  const { theme } = useTheme();
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityState={{ checked }}
      onPress={onToggle}
      style={{ flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 6 }}>
      <View
        style={{
          width: 22,
          height: 22,
          borderRadius: 6,
          borderWidth: 2,
          borderColor: theme.colors.primary,
          backgroundColor: checked ? theme.colors.primary : 'transparent',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
        {checked ? (
          <Text style={{ color: theme.colors.onPrimary, fontSize: 14, fontWeight: '800' }}>✓</Text>
        ) : null}
      </View>
      <Text style={{ flex: 1, fontSize: 14, color: theme.colors.text }}>{label}</Text>
    </Pressable>
  );
}

/* ------------------------------------------------------------------ status */

export function Badge({ label, tone }: { label: string; tone: Tone }) {
  return (
    <View
      style={{
        alignSelf: 'flex-start',
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 9999,
        borderWidth: 1,
        borderColor: tone.border,
        backgroundColor: tone.bg,
      }}>
      <Text style={{ fontSize: 11, fontWeight: '700', color: tone.fg }}>{label}</Text>
    </View>
  );
}

const LIFECYCLE: Record<string, [string, 'success' | 'warning' | 'danger' | 'info' | 'neutral']> = {
  REQUEST_CREATED: ['Request created', 'neutral'],
  LOCALITY_CHECKED: ['Checking', 'neutral'],
  HELD_FOR_REVIEW: ['Held for review', 'warning'],
  ASSESSED: ['Awaiting lender', 'info'],
  ACCEPTED: ['Accepted', 'success'],
  ACTIVE: ['In progress', 'success'],
  RETURN_INITIATED: ['Return started', 'info'],
  RETURNED: ['Returned', 'success'],
  COMPLETED: ['Completed', 'success'],
  DECLINED: ['Declined', 'neutral'],
  CANCELLED: ['Cancelled', 'neutral'],
  EXPIRED: ['Expired', 'neutral'],
  NO_SHOW: ['No show', 'neutral'],
  DISPUTED: ['Disputed', 'danger'],
};

export function LifecycleBadge({ state }: { state: string | null | undefined }) {
  const { theme } = useTheme();
  const [label, tone] = LIFECYCLE[state ?? ''] ?? [state ?? 'Unknown', 'neutral'];
  return <Badge label={label} tone={theme.colors[tone]} />;
}

const ASSURANCE_LABEL: Record<string, string> = {
  SUFFICIENT_EVIDENCE: 'Sufficient evidence',
  REVIEW_RECOMMENDED: 'Review recommended',
  INSUFFICIENT_EVIDENCE: 'Not enough history yet',
  ACTIVE_DISPUTE: 'Open dispute',
};

export function AssuranceBadge({ state }: { state: string }) {
  const { theme } = useTheme();
  const tone = theme.state[state as keyof typeof theme.state] ?? theme.colors.neutral;
  return <Badge label={`● ${ASSURANCE_LABEL[state] ?? state}`} tone={tone} />;
}

export function Banner({
  tone,
  title,
  children,
}: {
  tone: Tone;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <View
      style={{
        borderRadius: 12,
        borderWidth: 1,
        borderLeftWidth: 4,
        borderColor: tone.border,
        borderLeftColor: tone.fg,
        backgroundColor: tone.bg,
        padding: 12,
        gap: 4,
      }}>
      <Text style={{ fontSize: 13, fontWeight: '700', color: tone.fg }}>{title}</Text>
      <View>{children}</View>
    </View>
  );
}

/** 90% credible interval drawn as a range, never a single score (NFR-U-01). */
export function IntervalBar({ low, high, mean }: { low: number; high: number; mean: number }) {
  const { theme } = useTheme();
  const pct = (v: number) => `${Math.round(Math.min(Math.max(v, 0), 1) * 100)}%` as const;
  const wide = high - low > 0.5;
  return (
    <View style={{ gap: 6 }}>
      <View
        accessibilityLabel={`90% credible interval from ${low.toFixed(2)} to ${high.toFixed(2)}`}
        style={{
          height: 14,
          borderRadius: 9999,
          backgroundColor: theme.colors.surface2,
          borderWidth: 1,
          borderColor: theme.colors.border,
          overflow: 'hidden',
        }}>
        <View
          style={{
            position: 'absolute',
            left: pct(low),
            width: `${Math.round((high - low) * 100)}%`,
            top: 0,
            bottom: 0,
            backgroundColor: theme.colors.primary,
            opacity: 0.28,
          }}
        />
        <View
          style={{
            position: 'absolute',
            left: pct(mean),
            width: 3,
            top: 0,
            bottom: 0,
            backgroundColor: theme.colors.primary,
          }}
        />
      </View>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={{ fontSize: 11, color: theme.colors.textMuted }}>Less reliable</Text>
        <Text style={{ fontSize: 11, fontWeight: '600', color: theme.colors.textSecondary }}>
          {wide ? 'Wide interval · high uncertainty' : 'Narrow interval'}
        </Text>
        <Text style={{ fontSize: 11, color: theme.colors.textMuted }}>More reliable</Text>
      </View>
      <Text style={{ fontSize: 11, color: theme.colors.textMuted }}>
        90% credible interval [{low.toFixed(2)} – {high.toFixed(2)}]
      </Text>
    </View>
  );
}

const RISK_LABEL: Record<number, string> = {
  1: 'Low',
  2: 'Monitor',
  3: 'Verification advised',
  4: 'Moderator review',
};

export function RiskPill({ level, score }: { level: number; score: number }) {
  const { theme } = useTheme();
  const tone = level <= 1 ? theme.colors.success : level === 2 ? theme.colors.info : theme.colors.warning;
  return <Badge label={`${RISK_LABEL[level] ?? 'Unknown'} · ${score}/100`} tone={tone} />;
}

export function Collapsible({ title, children }: { title: string; children: React.ReactNode }) {
  const { theme } = useTheme();
  const [open, setOpen] = useState(false);
  return (
    <View style={{ gap: 8 }}>
      <Pressable accessibilityRole="button" onPress={() => setOpen(!open)}>
        <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.primary }}>
          {open ? '▼' : '▶'} {title}
        </Text>
      </Pressable>
      {open ? children : null}
    </View>
  );
}

export function ThemeSwitcher() {
  const { theme, themes, setTheme } = useTheme();
  return (
    <View
      accessibilityRole="radiogroup"
      style={{
        flexDirection: 'row',
        borderRadius: 9999,
        borderWidth: 1,
        borderColor: theme.colors.border,
        overflow: 'hidden',
      }}>
      {themes.map((t) => (
        <Pressable
          key={t.name}
          accessibilityRole="radio"
          accessibilityState={{ selected: t.name === theme.name }}
          onPress={() => setTheme(t.name)}
          style={{
            paddingHorizontal: 10,
            paddingVertical: 6,
            backgroundColor: t.name === theme.name ? theme.colors.primary : 'transparent',
          }}>
          <Text
            style={{
              fontSize: 11,
              fontWeight: '700',
              color: t.name === theme.name ? theme.colors.onPrimary : theme.colors.textSecondary,
            }}>
            {t.label}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

export function ErrorText({ message }: { message?: string | null }) {
  const { theme } = useTheme();
  if (!message) return null;
  return (
    <Banner tone={theme.colors.danger} title="Could not do that">
      <Text style={{ fontSize: 13, color: theme.colors.text }}>{message}</Text>
    </Banner>
  );
}

export function Loading() {
  const { theme } = useTheme();
  return <ActivityIndicator style={{ marginTop: 40 }} color={theme.colors.primary} />;
}
