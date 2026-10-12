import { router } from 'expo-router';
import { Pressable, Text, View } from 'react-native';

import { useItems } from '@/api/hooks';
import { Badge, Body, Card, ErrorText, Loading, Screen } from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

export default function Browse() {
  const { theme } = useTheme();
  const { data, isLoading, error } = useItems();
  return (
    <Screen title="Browse items" subtitle="Available in your community" back>
      {isLoading ? <Loading /> : null}
      {error ? <ErrorText message={error.message} /> : null}
      {data && data.length === 0 ? (
        <Card>
          <Body muted>Nothing to borrow right now.</Body>
        </Card>
      ) : null}
      {(data ?? []).map((item) => (
        <Pressable
          key={item.id}
          accessibilityRole="button"
          onPress={() => router.push({ pathname: '/item/[id]', params: { id: item.id } })}>
          <Card>
            <Text style={{ fontSize: 16, fontWeight: '700', color: theme.colors.text }}>
              {item.title}
            </Text>
            <Body muted>Shared by {item.owner_name}</Body>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <Badge label={`Value: ${item.value_band.toLowerCase()}`} tone={theme.colors.neutral} />
              {item.deposit_amount > 0 ? (
                <Badge label="Deposit recorded at handover" tone={theme.colors.info} />
              ) : null}
            </View>
          </Card>
        </Pressable>
      ))}
    </Screen>
  );
}
