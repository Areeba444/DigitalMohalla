import { router } from 'expo-router';
import { Text, View } from 'react-native';

import type { BrowseItem } from '@/api/hooks';
import { Badge, Caption, Card, Icon, ItemThumb, ReasonLine } from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

export const BAND_LABEL: Record<string, string> = {
  LOW: 'Low value',
  MEDIUM: 'Medium value',
  HIGH: 'High value',
};

const open = (id: string) => router.push({ pathname: '/item/detail/[id]', params: { id } });

/** Photo-left row (HCI analysis C5: the listing pattern residents know from OLX). */
export function ItemRow({ item, reasons }: { item: BrowseItem; reasons?: string[] }) {
  const { theme } = useTheme();

  // Color-code the value band: LOW=success (green), MEDIUM=warning (amber), HIGH=danger (red)
  const bandTone =
    item.value_band === 'LOW'
      ? theme.colors.success
      : item.value_band === 'HIGH'
        ? theme.colors.danger
        : theme.colors.warning;

  // Owner initial for avatar-style display
  const ownerFirstName = item.owner_name.split(' ')[0] ?? item.owner_name;

  return (
    <Card accessibilityLabel={`${item.title}, shared by ${item.owner_name}`} onPress={() => open(item.id)}>
      <View style={{ flexDirection: 'row', gap: 14, alignItems: 'center' }}>
        <ItemThumb title={item.title} size={76} />
        <View style={{ flex: 1, gap: 7 }}>
          <Text numberOfLines={1} style={{ fontFamily: theme.fonts.bold, fontSize: 17, color: theme.colors.text }}>
            {item.title}
          </Text>
          {/* Owner row: initial avatar + name */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 7 }}>
            <View
              style={{
                width: 22,
                height: 22,
                borderRadius: 11,
                backgroundColor: theme.colors.primarySoft,
                alignItems: 'center',
                justifyContent: 'center',
              }}>
              <Text style={{ fontFamily: theme.fonts.bold, fontSize: 10, color: theme.colors.primary }}>
                {ownerFirstName.charAt(0).toUpperCase()}
              </Text>
            </View>
            <Caption>{ownerFirstName}</Caption>
          </View>
          {/* Value badge + deposit */}
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
            <Badge label={BAND_LABEL[item.value_band] ?? item.value_band} tone={bandTone} />
            {item.deposit_amount > 0 ? (
              <Badge label="Deposit" tone={theme.colors.info} icon="payments" />
            ) : null}
          </View>
          {reasons && reasons.length > 0 ? <ReasonLine reasons={reasons} /> : null}
        </View>
        <Icon name="chevron_right" size={22} color={theme.colors.textMuted} />
      </View>
    </Card>
  );
}

/** Compact tile for the home carousel. */
export function ItemTile({ item }: { item: BrowseItem }) {
  const { theme } = useTheme();
  const bandTone =
    item.value_band === 'LOW'
      ? theme.colors.success
      : item.value_band === 'HIGH'
        ? theme.colors.danger
        : theme.colors.warning;
  return (
    <Card
      accessibilityLabel={`${item.title}, shared by ${item.owner_name}`}
      onPress={() => open(item.id)}
      style={{ width: 168, padding: 12, gap: 10 }}>
      <View style={{ alignItems: 'center' }}>
        <ItemThumb title={item.title} size={144} />
      </View>
      <View style={{ gap: 3 }}>
        <Text numberOfLines={1} style={{ fontFamily: theme.fonts.bold, fontSize: 15.5, color: theme.colors.text }}>
          {item.title}
        </Text>
        <Caption>{item.owner_name}</Caption>
      </View>
      <Badge label={BAND_LABEL[item.value_band] ?? item.value_band} tone={bandTone} />
    </Card>
  );
}
