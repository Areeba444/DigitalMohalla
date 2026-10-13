/**
 * Shared UI kit. Every colour, font and radius comes from the active theme (src/theme/themes.ts).
 *
 * HCI rules applied here (docs/design/Digital-MohallaUI/HCI_Design_Analysis_Digital_Mohalla.md):
 * - touch targets are at least 48 dp; one primary action per surface;
 * - status is shown with text and an icon, never colour alone;
 * - assurance is shown as a state and evidence, never a single trust number (NFR-U-01);
 * - "not enough history" is neutral, never red (constraint 2).
 */
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SymbolView, type AndroidSymbol } from 'expo-symbols';
import { useContext, useState } from 'react';
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type StyleProp,
  type TextStyle,
  type ViewStyle,
} from 'react-native';
import { SafeAreaInsetsContext } from 'react-native-safe-area-context';

import { useTheme } from '@/theme/ThemeProvider';
import type { Theme, Tone } from '@/theme/themes';

/* ------------------------------------------------------------------ helpers */

/** A CSS linear-gradient as a background: CSS on web, the native gradient property on Android. */
export function gradient(css: string): ViewStyle {
  return (Platform.OS === 'web'
    ? { backgroundImage: css }
    : { experimental_backgroundImage: css }) as unknown as ViewStyle;
}

const useT = () => useTheme().theme;

const NO_INSETS = { top: 0, bottom: 0, left: 0, right: 0 };

/** Safe-area insets; zero when rendered without a provider (e.g. in screen tests). Expo Router provides one in the app. */
export function useInsets() {
  return useContext(SafeAreaInsetsContext) ?? NO_INSETS;
}

export type IconName = AndroidSymbol;

export function Icon({
  name,
  size = 22,
  color,
  style,
}: {
  name: IconName;
  size?: number;
  color?: string;
  style?: StyleProp<ViewStyle>;
}) {
  const theme = useT();
  return (
    <SymbolView
      name={{ android: name, web: name }}
      size={size}
      tintColor={color ?? theme.colors.text}
      style={style}
    />
  );
}

/* ------------------------------------------------------------------ type */

export function Title({
  children,
  size = 26,
  color,
  style,
}: {
  children: React.ReactNode;
  size?: number;
  color?: string;
  style?: StyleProp<TextStyle>;
}) {
  const theme = useT();
  return (
    <Text
      style={[
        {
          fontFamily: theme.fonts.display,
          fontSize: size,
          lineHeight: Math.round(size * 1.18),
          color: color ?? theme.colors.text,
          letterSpacing: -0.3,
        },
        style,
      ]}>
      {children}
    </Text>
  );
}

export function Heading({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) {
  const theme = useT();
  return (
    <Text style={[{ fontFamily: theme.fonts.bold, fontSize: 17, color: theme.colors.text }, style]}>
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
  const theme = useT();
  return (
    <Text
      style={[
        {
          fontFamily: theme.fonts.regular,
          fontSize: 15,
          lineHeight: 22,
          color: muted ? theme.colors.textSecondary : theme.colors.text,
        },
        style,
      ]}>
      {children}
    </Text>
  );
}

export function Caption({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) {
  const theme = useT();
  return (
    <Text
      style={[
        { fontFamily: theme.fonts.medium, fontSize: 12.5, lineHeight: 17, color: theme.colors.textMuted },
        style,
      ]}>
      {children}
    </Text>
  );
}

export function SectionLabel({ children, color }: { children: string; color?: string }) {
  const theme = useT();
  return (
    <Text
      style={{
        fontFamily: theme.fonts.bold,
        fontSize: 11.5,
        letterSpacing: 1.2,
        textTransform: 'uppercase',
        color: color ?? theme.colors.textMuted,
      }}>
      {children}
    </Text>
  );
}

export function SectionHeader({
  title,
  action,
  onAction,
}: {
  title: string;
  action?: string;
  onAction?: () => void;
}) {
  const theme = useT();
  return (
    <View
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: 6,
      }}>
      <Text style={{ fontFamily: theme.fonts.bold, fontSize: 18, color: theme.colors.text }}>
        {title}
      </Text>
      {action && onAction ? (
        <Pressable accessibilityRole="button" onPress={onAction} hitSlop={12}>
          <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 14, color: theme.colors.primary }}>
            {action}
          </Text>
        </Pressable>
      ) : null}
    </View>
  );
}

export function Row({ label, value }: { label: string; value: string }) {
  const theme = useT();
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 12 }}>
      <Text style={{ fontFamily: theme.fonts.medium, fontSize: 14, color: theme.colors.textMuted }}>
        {label}
      </Text>
      <Text
        style={{
          fontFamily: theme.fonts.semibold,
          fontSize: 14,
          color: theme.colors.text,
          flexShrink: 1,
          textAlign: 'right',
        }}>
        {value}
      </Text>
    </View>
  );
}

/* ------------------------------------------------------------------ layout */

const MAX_WIDTH = 480;

/** Page with a glassy top bar. `tabs` adds room for the floating tab bar. */
export function Screen({
  title,
  subtitle,
  back,
  right,
  tabs,
  children,
}: {
  title: string;
  subtitle?: string;
  back?: boolean;
  right?: React.ReactNode;
  tabs?: boolean;
  children: React.ReactNode;
}) {
  const theme = useT();
  const insets = useInsets();
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.bg }}>
      <StatusBar style="dark" />
      <View style={{ width: '100%', maxWidth: MAX_WIDTH, alignSelf: 'center', flex: 1 }}>
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 12,
            paddingHorizontal: 16,
            paddingTop: insets.top + 10,
            paddingBottom: 12,
            backgroundColor: theme.colors.glass,
            borderBottomWidth: StyleSheet.hairlineWidth,
            borderBottomColor: theme.colors.hairline,
          }}>
          {back ? <BackButton /> : null}
          <View style={{ flex: 1 }}>
            <Text
              numberOfLines={1}
              style={{ fontFamily: theme.fonts.display, fontSize: 21, color: theme.colors.text }}>
              {title}
            </Text>
            {subtitle ? <Caption>{subtitle}</Caption> : null}
          </View>
          {right}
        </View>
        <ScrollView
          contentContainerStyle={{ padding: 16, gap: 16, paddingBottom: tabs ? 128 : 48 }}
          showsVerticalScrollIndicator={false}>
          {children}
        </ScrollView>
      </View>
    </View>
  );
}

/** Page that opens with a full-bleed theme image (home, login, profile). */
export function HeroScreen({
  height = 300,
  hero,
  tabs,
  children,
}: {
  height?: number;
  hero: React.ReactNode;
  tabs?: boolean;
  children: React.ReactNode;
}) {
  const theme = useT();
  const insets = useInsets();
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.bg }}>
      <ScrollView
        contentContainerStyle={{ paddingBottom: tabs ? 128 : 48 }}
        showsVerticalScrollIndicator={false}>
        <View style={{ width: '100%', maxWidth: MAX_WIDTH, alignSelf: 'center' }}>
          <Hero height={height + insets.top}>
            <View style={{ flex: 1, paddingTop: insets.top + 14, paddingHorizontal: 20, paddingBottom: 26 }}>
              {hero}
            </View>
          </Hero>
          <View style={{ paddingHorizontal: 16, gap: 16, marginTop: -22 }}>{children}</View>
        </View>
      </ScrollView>
    </View>
  );
}

/** The theme image with its scrim; children sit on top. */
export function Hero({ height, children }: { height: number; children: React.ReactNode }) {
  const theme = useT();
  return (
    <View
      style={{
        height,
        overflow: 'hidden',
        borderBottomLeftRadius: theme.radius.xl,
        borderBottomRightRadius: theme.radius.xl,
        backgroundColor: theme.colors.surface2,
      }}>
      <StatusBar style={theme.hero.statusBar} />
      <Image
        source={theme.hero.image}
        contentFit="cover"
        contentPosition={theme.hero.position}
        style={StyleSheet.absoluteFill}
        accessibilityIgnoresInvertColors
      />
      <View style={[StyleSheet.absoluteFill, gradient(theme.hero.scrim)]} />
      {children}
    </View>
  );
}

export function Card({
  children,
  style,
  onPress,
  accessibilityLabel,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
  accessibilityLabel?: string;
}) {
  const theme = useT();
  const base: ViewStyle = {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: theme.colors.hairline,
    padding: 16,
    gap: 12,
    boxShadow: theme.shadow.card,
  };
  if (!onPress) return <View style={[base, style]}>{children}</View>;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      style={({ pressed }) => [base, style, pressed ? { transform: [{ scale: 0.985 }], opacity: 0.94 } : null]}>
      {children}
    </Pressable>
  );
}

/* ------------------------------------------------------------------ controls */

export function BackButton() {
  const theme = useT();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Back"
      onPress={() => (router.canGoBack() ? router.back() : router.replace('/'))}
      style={({ pressed }) => ({
        width: 44,
        height: 44,
        borderRadius: 22,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: pressed ? theme.colors.primarySoft : theme.colors.surface,
        borderWidth: StyleSheet.hairlineWidth,
        borderColor: theme.colors.hairline,
      })}>
      <Icon name="arrow_back" size={22} color={theme.colors.text} />
    </Pressable>
  );
}

type ButtonVariant = 'primary' | 'soft' | 'outline' | 'ghost';

export function Button({
  label,
  onPress,
  variant = 'primary',
  icon,
  loading,
  disabled,
  compact,
}: {
  label: string;
  onPress: () => void;
  variant?: ButtonVariant;
  icon?: IconName;
  loading?: boolean;
  disabled?: boolean;
  compact?: boolean;
}) {
  const theme = useT();
  const off = disabled || loading;
  const fg =
    variant === 'primary' ? theme.colors.onPrimary : variant === 'soft' ? theme.colors.primaryDeep : theme.colors.primary;
  const surface: ViewStyle =
    variant === 'primary'
      ? { ...gradient(theme.hero.button), backgroundColor: theme.colors.primary, boxShadow: theme.shadow.card }
      : variant === 'soft'
        ? { backgroundColor: theme.colors.primarySoft }
        : variant === 'outline'
          ? { borderWidth: 1.5, borderColor: theme.colors.primary, backgroundColor: 'transparent' }
          : { backgroundColor: 'transparent' };
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: !!off, busy: !!loading }}
      onPress={off ? undefined : onPress}
      style={({ pressed }) => [
        {
          minHeight: compact ? 44 : 52,
          paddingHorizontal: compact ? 16 : 20,
          borderRadius: theme.radius.pill,
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'row',
          gap: 8,
          opacity: off ? 0.5 : 1,
        },
        surface,
        pressed && !off ? { transform: [{ scale: 0.98 }], opacity: 0.92 } : null,
      ]}>
      {loading ? <ActivityIndicator color={fg} /> : icon ? <Icon name={icon} size={20} color={fg} /> : null}
      <Text style={{ fontFamily: theme.fonts.bold, fontSize: compact ? 14 : 15.5, color: fg }}>{label}</Text>
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
  icon,
  autoComplete,
}: {
  label?: string;
  value: string;
  onChangeText: (v: string) => void;
  placeholder?: string;
  multiline?: boolean;
  secure?: boolean;
  keyboardType?: 'default' | 'email-address' | 'numeric';
  icon?: IconName;
  autoComplete?: 'email' | 'password' | 'off';
}) {
  const theme = useT();
  const [focused, setFocused] = useState(false);
  return (
    <View style={{ gap: 7 }}>
      {label ? (
        <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 13.5, color: theme.colors.textSecondary }}>
          {label}
        </Text>
      ) : null}
      <View
        style={{
          flexDirection: 'row',
          alignItems: multiline ? 'flex-start' : 'center',
          gap: 10,
          minHeight: multiline ? 96 : 52,
          paddingHorizontal: 14,
          paddingVertical: multiline ? 12 : 0,
          borderRadius: theme.radius.sm,
          borderWidth: 1.5,
          borderColor: focused ? theme.colors.primary : theme.colors.border,
          backgroundColor: focused ? theme.colors.surface : theme.colors.surface2,
        }}>
        {icon ? <Icon name={icon} size={20} color={focused ? theme.colors.primary : theme.colors.textMuted} /> : null}
        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.textMuted}
          multiline={multiline}
          secureTextEntry={secure}
          keyboardType={keyboardType}
          autoComplete={autoComplete}
          autoCapitalize="none"
          accessibilityLabel={label ?? placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            flex: 1,
            minHeight: multiline ? 72 : 50,
            fontFamily: theme.fonts.medium,
            fontSize: 15.5,
            color: theme.colors.text,
            textAlignVertical: multiline ? 'top' : 'center',
            ...(Platform.OS === 'web' ? ({ outlineStyle: 'none' } as object) : null),
          }}
        />
      </View>
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
  const theme = useT();
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityState={{ checked }}
      onPress={onToggle}
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
        minHeight: 52,
        paddingHorizontal: 12,
        borderRadius: theme.radius.sm,
        backgroundColor: checked ? theme.colors.primarySoft : theme.colors.surface2,
      }}>
      <View
        style={{
          width: 26,
          height: 26,
          borderRadius: 9,
          borderWidth: 2,
          borderColor: checked ? theme.colors.primary : theme.colors.border,
          backgroundColor: checked ? theme.colors.primary : theme.colors.surface,
          alignItems: 'center',
          justifyContent: 'center',
        }}>
        {checked ? <Icon name="check" size={18} color={theme.colors.onPrimary} /> : null}
      </View>
      <Text style={{ flex: 1, fontFamily: theme.fonts.medium, fontSize: 15, color: theme.colors.text }}>
        {label}
      </Text>
    </Pressable>
  );
}

/** Selectable chip for filters, dates and segmented choices. */
export function Chip({
  label,
  selected,
  onPress,
  icon,
  sublabel,
}: {
  label: string;
  selected?: boolean;
  onPress: () => void;
  icon?: IconName;
  sublabel?: string;
}) {
  const theme = useT();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: !!selected }}
      onPress={onPress}
      style={({ pressed }) => ({
        minHeight: 44,
        paddingHorizontal: 14,
        paddingVertical: sublabel ? 8 : 0,
        borderRadius: sublabel ? theme.radius.sm : theme.radius.pill,
        flexDirection: sublabel ? 'column' : 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: sublabel ? 2 : 6,
        backgroundColor: selected ? theme.colors.primary : theme.colors.surface,
        borderWidth: 1,
        borderColor: selected ? theme.colors.primary : theme.colors.border,
        opacity: pressed ? 0.85 : 1,
      })}>
      {icon ? <Icon name={icon} size={18} color={selected ? theme.colors.onPrimary : theme.colors.textSecondary} /> : null}
      {sublabel ? (
        <Text
          style={{
            fontFamily: theme.fonts.semibold,
            fontSize: 11,
            textTransform: 'uppercase',
            letterSpacing: 0.6,
            color: selected ? theme.colors.onPrimary : theme.colors.textMuted,
          }}>
          {sublabel}
        </Text>
      ) : null}
      <Text
        style={{
          fontFamily: theme.fonts.bold,
          fontSize: sublabel ? 17 : 14,
          color: selected ? theme.colors.onPrimary : theme.colors.text,
        }}>
        {label}
      </Text>
    </Pressable>
  );
}

export function Collapsible({
  title,
  icon,
  defaultOpen = false,
  children,
}: {
  title: string;
  icon?: IconName;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const theme = useT();
  const [open, setOpen] = useState(defaultOpen);
  return (
    <View style={{ gap: 10 }}>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
        onPress={() => setOpen(!open)}
        style={{ flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 44 }}>
        {icon ? <Icon name={icon} size={20} color={theme.colors.primary} /> : null}
        <Text style={{ flex: 1, fontFamily: theme.fonts.bold, fontSize: 14.5, color: theme.colors.primary }}>
          {title}
        </Text>
        <Icon
          name="expand_more"
          size={22}
          color={theme.colors.primary}
          style={{ transform: [{ rotate: open ? '180deg' : '0deg' }] }}
        />
      </Pressable>
      {open ? children : null}
    </View>
  );
}

/* ------------------------------------------------------------------ status */

export function Badge({ label, tone, icon }: { label: string; tone: Tone; icon?: IconName }) {
  const theme = useT();
  return (
    <View
      style={{
        alignSelf: 'flex-start',
        flexDirection: 'row',
        alignItems: 'center',
        gap: 5,
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 9999,
        borderWidth: 1,
        borderColor: tone.border,
        backgroundColor: tone.bg,
      }}>
      {icon ? <Icon name={icon} size={14} color={tone.fg} /> : null}
      <Text style={{ fontFamily: theme.fonts.bold, fontSize: 12, color: tone.fg }}>{label}</Text>
    </View>
  );
}

type ToneKey = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

const LIFECYCLE: Record<string, [string, ToneKey, IconName]> = {
  REQUEST_CREATED: ['Request created', 'neutral', 'pending'],
  LOCALITY_CHECKED: ['Checking', 'neutral', 'pending'],
  HELD_FOR_REVIEW: ['With a moderator', 'warning', 'policy'],
  ASSESSED: ['Awaiting lender', 'info', 'hourglass_top'],
  ACCEPTED: ['Accepted', 'success', 'event_available'],
  ACTIVE: ['On loan', 'success', 'handshake'],
  RETURN_INITIATED: ['Return started', 'info', 'assignment_return'],
  RETURNED: ['Returned', 'success', 'task_alt'],
  COMPLETED: ['Completed', 'success', 'task_alt'],
  DECLINED: ['Declined', 'neutral', 'close'],
  CANCELLED: ['Cancelled', 'neutral', 'close'],
  EXPIRED: ['Expired', 'neutral', 'schedule'],
  NO_SHOW: ['No show', 'neutral', 'schedule'],
  DISPUTED: ['Disputed', 'danger', 'gavel'],
};

export function lifecycleLabel(state: string | null | undefined): string {
  return LIFECYCLE[state ?? '']?.[0] ?? state ?? 'Unknown';
}

export function LifecycleBadge({ state, role }: { state: string | null | undefined; role?: string | null }) {
  const theme = useT();
  const [label, tone, icon] = LIFECYCLE[state ?? ''] ?? [state ?? 'Unknown', 'neutral', 'pending'];
  // The lender is the one being waited for, so say so from their side.
  const shown = state === 'ASSESSED' && role === 'LENDER' ? 'Your decision' : label;
  return <Badge label={shown} tone={theme.colors[tone]} icon={icon} />;
}

export const ASSURANCE: Record<string, { label: string; icon: IconName }> = {
  SUFFICIENT_EVIDENCE: { label: 'Enough verified history', icon: 'verified' },
  REVIEW_RECOMMENDED: { label: 'Take a closer look', icon: 'visibility' },
  INSUFFICIENT_EVIDENCE: { label: 'Not enough history yet', icon: 'hourglass_top' },
  ACTIVE_DISPUTE: { label: 'Open dispute', icon: 'gavel' },
};

export function assuranceTone(theme: Theme, state: string): Tone {
  return theme.state[state as keyof Theme['state']] ?? theme.colors.neutral;
}

export function AssuranceBadge({ state }: { state: string }) {
  const theme = useT();
  const a = ASSURANCE[state] ?? { label: state, icon: 'info' as IconName };
  return <Badge label={a.label} tone={assuranceTone(theme, state)} icon={a.icon} />;
}

export function Banner({
  tone,
  title,
  icon,
  children,
}: {
  tone: Tone;
  title: string;
  icon?: IconName;
  children?: React.ReactNode;
}) {
  const theme = useT();
  return (
    <View
      style={{
        flexDirection: 'row',
        gap: 12,
        borderRadius: theme.radius.md,
        borderWidth: 1,
        borderColor: tone.border,
        backgroundColor: tone.bg,
        padding: 14,
      }}>
      <View
        style={{
          width: 36,
          height: 36,
          borderRadius: 12,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: theme.colors.surface,
        }}>
        <Icon name={icon ?? 'info'} size={20} color={tone.fg} />
      </View>
      <View style={{ flex: 1, gap: 3 }}>
        <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: tone.fg }}>{title}</Text>
        {children}
      </View>
    </View>
  );
}

/** 90% credible interval drawn as a range with the mean marked, never a single score (NFR-U-01). */
export function IntervalBar({ low, high, mean }: { low: number; high: number; mean: number }) {
  const theme = useT();
  const clamp = (v: number) => Math.min(Math.max(v, 0), 1);
  const pct = (v: number) => `${Math.round(clamp(v) * 100)}%` as const;
  const wide = high - low > 0.5;
  return (
    <View style={{ gap: 8 }}>
      <View
        accessible
        accessibilityLabel={`90% credible interval from ${low.toFixed(2)} to ${high.toFixed(2)}`}
        style={{
          height: 18,
          borderRadius: 9999,
          backgroundColor: theme.colors.surface2,
          borderWidth: 1,
          borderColor: theme.colors.border,
          overflow: 'hidden',
          justifyContent: 'center',
        }}>
        <View
          style={[
            {
              position: 'absolute',
              left: pct(low),
              width: `${Math.max(2, Math.round((clamp(high) - clamp(low)) * 100))}%`,
              top: 3,
              bottom: 3,
              borderRadius: 9999,
              opacity: 0.55,
            },
            gradient(`linear-gradient(90deg, ${theme.colors.primarySoft}, ${theme.colors.primary})`),
          ]}
        />
        <View
          style={{
            position: 'absolute',
            left: pct(mean),
            marginLeft: -2,
            width: 4,
            top: 1,
            bottom: 1,
            borderRadius: 2,
            backgroundColor: theme.colors.primaryDeep,
          }}
        />
      </View>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Caption>Less reliable</Caption>
        <Caption style={{ fontFamily: theme.fonts.semibold, color: theme.colors.textSecondary }}>
          {wide ? 'Wide range: little evidence' : 'Narrow range: steady evidence'}
        </Caption>
        <Caption>More reliable</Caption>
      </View>
    </View>
  );
}

const RISK: Record<number, [string, ToneKey]> = {
  1: ['Low', 'success'],
  2: ['Monitor', 'info'],
  3: ['Verification advised', 'warning'],
  4: ['Moderator review', 'warning'],
};

/** The manipulation band only: a number next to the evidence could be read as a rating (NFR-U-01). */
export function RiskPill({ level }: { level: number }) {
  const theme = useT();
  const [label, tone] = RISK[level] ?? ['Unknown', 'neutral'];
  return <Badge label={label} tone={theme.colors[tone]} icon={level <= 1 ? 'shield' : 'flag'} />;
}

/** Initials in a tinted circle. */
export function Avatar({ name, size = 44 }: { name: string; size?: number }) {
  const theme = useT();
  const clean = name.replace(/\(.*?\)/g, '').trim();
  const initials = clean
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('');
  const tints = [theme.colors.primarySoft, theme.colors.accentSoft, theme.colors.surface2];
  const tint = tints[(clean.charCodeAt(0) || 0) % tints.length];
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: tint,
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 2,
        borderColor: theme.colors.surface,
      }}>
      <Text style={{ fontFamily: theme.fonts.bold, fontSize: size * 0.38, color: theme.colors.primaryDeep }}>
        {initials || '?'}
      </Text>
    </View>
  );
}

const ITEM_ICONS: [RegExp, IconName][] = [
  [/drill|tool|hammer|wrench|saw|screw/i, 'handyman'],
  [/ladder|stair/i, 'stairs'],
  [/tent|camp/i, 'camping'],
  [/book/i, 'menu_book'],
  [/cook|pot|pan|kitchen|cooker/i, 'skillet'],
  [/chair|table|sofa/i, 'chair'],
  [/garden|plant|hose/i, 'yard'],
  [/bat|ball|cricket|sport/i, 'sports_cricket'],
];

/** Illustrated tile standing in for an item photo (the API has no images yet). */
export function ItemThumb({ title, size = 64 }: { title: string; size?: number }) {
  const theme = useT();
  const icon = ITEM_ICONS.find(([re]) => re.test(title))?.[1] ?? 'inventory_2';
  return (
    <View
      style={[
        {
          width: size,
          height: size,
          borderRadius: theme.radius.sm + 2,
          alignItems: 'center',
          justifyContent: 'center',
        },
        gradient(`linear-gradient(145deg, ${theme.colors.primarySoft} 0%, ${theme.colors.accentSoft} 100%)`),
      ]}>
      <Icon name={icon} size={Math.round(size * 0.5)} color={theme.colors.primaryDeep} />
    </View>
  );
}

const STEPS: { key: string; label: string; states: string[] }[] = [
  { key: 'req', label: 'Requested', states: ['REQUEST_CREATED', 'LOCALITY_CHECKED', 'HELD_FOR_REVIEW', 'ASSESSED'] },
  { key: 'acc', label: 'Accepted', states: ['ACCEPTED'] },
  { key: 'act', label: 'On loan', states: ['ACTIVE'] },
  { key: 'ret', label: 'Returning', states: ['RETURN_INITIATED', 'RETURNED'] },
  { key: 'done', label: 'Completed', states: ['COMPLETED'] },
];

/** Where a loan is in its life, as five steps. Side states (declined, disputed...) show no stepper. */
export function LoanProgress({ state }: { state: string }) {
  const theme = useT();
  const at = STEPS.findIndex((s) => s.states.includes(state));
  if (at < 0) return null;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'flex-start' }} accessibilityLabel={`Step ${at + 1} of 5: ${STEPS[at].label}`}>
      {STEPS.map((s, i) => {
        const done = i < at || state === 'COMPLETED';
        const current = i === at && state !== 'COMPLETED';
        return (
          <View key={s.key} style={{ flex: 1, alignItems: 'center', gap: 6 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', alignSelf: 'stretch' }}>
              <View
                style={{
                  flex: 1,
                  height: 3,
                  backgroundColor: i === 0 ? 'transparent' : i <= at ? theme.colors.primary : theme.colors.border,
                }}
              />
              <View
                style={{
                  width: current ? 26 : 22,
                  height: current ? 26 : 22,
                  borderRadius: 13,
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: done || current ? theme.colors.primary : theme.colors.surface,
                  borderWidth: 2,
                  borderColor: done || current ? theme.colors.primary : theme.colors.border,
                  boxShadow: current ? `0px 0px 0px 4px ${theme.colors.primarySoft}` : undefined,
                }}>
                {done ? <Icon name="check" size={15} color={theme.colors.onPrimary} /> : null}
              </View>
              <View
                style={{
                  flex: 1,
                  height: 3,
                  backgroundColor:
                    i === STEPS.length - 1 ? 'transparent' : i < at ? theme.colors.primary : theme.colors.border,
                }}
              />
            </View>
            <Text
              style={{
                fontFamily: current ? theme.fonts.bold : theme.fonts.medium,
                fontSize: 11.5,
                color: current ? theme.colors.text : theme.colors.textMuted,
                textAlign: 'center',
              }}>
              {s.label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

export function EmptyState({
  icon,
  title,
  body,
  children,
}: {
  icon: IconName;
  title: string;
  body: string;
  children?: React.ReactNode;
}) {
  const theme = useT();
  return (
    <Card style={{ alignItems: 'center', paddingVertical: 28, gap: 10 }}>
      <View
        style={{
          width: 64,
          height: 64,
          borderRadius: 32,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: theme.colors.primarySoft,
        }}>
        <Icon name={icon} size={30} color={theme.colors.primary} />
      </View>
      <Heading style={{ textAlign: 'center' }}>{title}</Heading>
      <Body muted style={{ textAlign: 'center', maxWidth: 300 }}>
        {body}
      </Body>
      {children}
    </Card>
  );
}

/** Two theme swatches; small enough for a hero corner. */
export function ThemeSwitcher({ onImage }: { onImage?: boolean }) {
  const { theme, themes, setTheme } = useTheme();
  return (
    <View
      accessibilityRole="radiogroup"
      accessibilityLabel="Theme"
      style={{
        flexDirection: 'row',
        gap: 6,
        padding: 5,
        borderRadius: 9999,
        backgroundColor: onImage ? 'rgba(255,255,255,0.28)' : theme.colors.surface,
        borderWidth: StyleSheet.hairlineWidth,
        borderColor: onImage ? 'rgba(255,255,255,0.45)' : theme.colors.hairline,
        ...(Platform.OS === 'web' ? ({ backdropFilter: 'blur(10px)' } as object) : null),
      }}>
      {themes.map((t) => {
        const selected = t.name === theme.name;
        return (
          <Pressable
            key={t.name}
            accessibilityRole="radio"
            accessibilityLabel={`${t.label} theme`}
            accessibilityState={{ selected }}
            onPress={() => setTheme(t.name)}
            hitSlop={8}
            style={{
              width: 30,
              height: 30,
              borderRadius: 15,
              borderWidth: 2,
              borderColor: selected ? '#FFFFFF' : 'transparent',
              overflow: 'hidden',
              boxShadow: selected ? '0px 0px 0px 2px rgba(0,0,0,0.18)' : undefined,
            }}>
            <View
              style={[
                { flex: 1 },
                gradient(`linear-gradient(135deg, ${t.colors.primary} 0%, ${t.colors.primary} 50%, ${t.colors.bg} 50%)`),
              ]}
            />
          </Pressable>
        );
      })}
    </View>
  );
}

export function ErrorText({ message }: { message?: string | null }) {
  const theme = useT();
  if (!message) return null;
  return (
    <Banner tone={theme.colors.danger} title="That did not work" icon="warning">
      <Body muted style={{ fontSize: 14 }}>
        {message}
      </Body>
    </Banner>
  );
}

export function Loading() {
  const theme = useT();
  return <ActivityIndicator style={{ marginTop: 40 }} size="large" color={theme.colors.primary} />;
}
