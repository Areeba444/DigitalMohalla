import { router, usePathname, type Href } from 'expo-router';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, type IconName, useInsets } from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

const TABS: { href: Href; path: string; label: string; icon: IconName }[] = [
  { href: '/', path: '/', label: 'Home', icon: 'home' },
  { href: '/browse', path: '/browse', label: 'Browse', icon: 'search' },
  { href: '/activity', path: '/activity', label: 'Activity', icon: 'receipt_long' },
  { href: '/profile', path: '/profile', label: 'Profile', icon: 'person' },
];

/**
 * Floating bottom navigation (HCI analysis 2.2: bottom tabs, the pattern residents know from WhatsApp).
 * Four tabs because iteration 1 has four destinations; there is no "post an item" button until the API
 * can create listings, so no control appears that cannot work.
 */
export function TabBar({ badge }: { badge?: number }) {
  const { theme } = useTheme();
  const insets = useInsets();
  const pathname = usePathname();
  return (
    <View
      pointerEvents="box-none"
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        paddingBottom: Math.max(insets.bottom, 12),
        alignItems: 'center',
      }}>
      <View
        accessibilityRole="tablist"
        style={{
          flexDirection: 'row',
          width: '92%',
          maxWidth: 440,
          padding: 6,
          borderRadius: theme.radius.xl,
          backgroundColor: theme.colors.glass,
          borderWidth: StyleSheet.hairlineWidth,
          borderColor: theme.colors.hairline,
          boxShadow: theme.shadow.float,
          ...(Platform.OS === 'web' ? ({ backdropFilter: 'blur(16px)' } as object) : null),
        }}>
        {TABS.map((t) => {
          const active = pathname === t.path;
          return (
            <Pressable
              key={t.path}
              accessibilityRole="tab"
              accessibilityLabel={t.label}
              accessibilityState={{ selected: active }}
              onPress={() => {
                if (!active) router.navigate(t.href);
              }}
              style={({ pressed }) => ({
                flex: 1,
                minHeight: 52,
                borderRadius: theme.radius.lg,
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                backgroundColor: active ? theme.colors.primarySoft : 'transparent',
                opacity: pressed ? 0.8 : 1,
              })}>
              <View>
                <Icon name={t.icon} size={24} color={active ? theme.colors.primary : theme.colors.textMuted} />
                {t.path === '/' && badge ? (
                  <View
                    accessibilityLabel={`${badge} waiting for you`}
                    style={{
                      position: 'absolute',
                      top: -4,
                      right: -10,
                      minWidth: 18,
                      height: 18,
                      paddingHorizontal: 4,
                      borderRadius: 9,
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: theme.colors.primary,
                      borderWidth: 2,
                      borderColor: theme.colors.surface,
                    }}>
                    <Text style={{ fontFamily: theme.fonts.bold, fontSize: 10, color: theme.colors.onPrimary }}>
                      {badge}
                    </Text>
                  </View>
                ) : null}
              </View>
              <Text
                style={{
                  fontFamily: active ? theme.fonts.bold : theme.fonts.medium,
                  fontSize: 11.5,
                  color: active ? theme.colors.primary : theme.colors.textMuted,
                }}>
                {t.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}
