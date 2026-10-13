import { router } from 'expo-router';
import { Text, View } from 'react-native';

import type { BrowseItem } from '@/api/hooks';
import { Badge, Caption, Card, Icon, ItemThumb } from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

export const BAND_LABEL: Record<string, string> = {
  LOW: 'Low value',
  MEDIUM: 'Medium value',
  HIGH: 'High value',
};

const open = (id: string) => router.push({ pathname: '/item/[id]', params: { id } });

/** Photo-left row (HCI analysis C5: the listing pattern residents know from OLX). */
export function ItemRow({ item }: { item: BrowseItem }) {
  const { theme } = useTheme();
  return (
    <Card accessibilityLabel={`${item.title}, shared by ${item.owner_name}`} onPress={() => open(item.id)}>
      <View style={{ flexDirection: 'row', gap: 14, alignItems: 'center' }}>
        <ItemThumb title={item.title} size={76} />
        <View style={{ flex: 1, gap: 6 }}>
          <Text numberOfLines={1} style={{ fontFamily: theme.fonts.bold, fontSize: 17, color: theme.colors.text }}>
            {item.title}
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Icon name="person" size={15} color={theme.colors.textMuted} />
            <Caption>Shared by {item.owner_name}</Caption>
          </View>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
            <Badge label={BAND_LABEL[item.value_band] ?? item.value_band} tone={theme.colors.neutral} />
            {item.deposit_amount > 0 ? (
              <Badge label="Deposit at handover" tone={theme.colors.info} icon="payments" />
            ) : null}
          </View>
        </View>
        <Icon name="chevron_right" size={22} color={theme.colors.textMuted} />
      </View>
    </Card>
  );
}

/** Compact tile for the home carousel. */
export function ItemTile({ item }: { item: BrowseItem }) {
  const { theme } = useTheme();
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
      <Badge label={BAND_LABEL[item.value_band] ?? item.value_band} tone={theme.colors.neutral} />
    </Card>
  );
}
