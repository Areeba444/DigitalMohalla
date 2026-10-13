import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { useCreateRequest, useItems } from '@/api/hooks';
import { BAND_LABEL } from '@/components/ItemCard';
import {
  Avatar,
  Badge,
  Banner,
  Body,
  Button,
  Caption,
  Card,
  Chip,
  ErrorText,
  Field,
  Icon,
  ItemThumb,
  Loading,
  Screen,
  SectionLabel,
  Title,
} from '@/components/ui';
import { addDays, isoDate } from '@/lib/format';
import { useTheme } from '@/theme/ThemeProvider';

const WEEKDAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const longDay = (iso: string) => {
  const d = new Date(`${iso}T00:00:00Z`);
  return `${WEEKDAY[d.getUTCDay()]}, ${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`;
};

function RoundButton({ icon, label, onPress, disabled }: { icon: 'add' | 'remove'; label: string; onPress: () => void; disabled?: boolean }) {
  const { theme } = useTheme();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: !!disabled }}
      onPress={disabled ? undefined : onPress}
      style={({ pressed }) => ({
        width: 48,
        height: 48,
        borderRadius: 24,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: theme.colors.primarySoft,
        opacity: disabled ? 0.4 : pressed ? 0.8 : 1,
      })}>
      <Icon name={icon} size={24} color={theme.colors.primaryDeep} />
    </Pressable>
  );
}

export default function NewRequest() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useTheme();
  const { data, isLoading } = useItems();
  const create = useCreateRequest();
  const item = data?.find((i) => i.id === id);

  // The next two weeks as tappable days: no typed dates, so no invalid ones (HCI: error prevention).
  const [days14] = useState(() => Array.from({ length: 14 }, (_, i) => isoDate(addDays(new Date(), i + 1))));
  const [start, setStart] = useState(days14[2]);
  const [days, setDays] = useState(3);
  const [message, setMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const end = isoDate(addDays(new Date(`${start}T00:00:00Z`), days));

  const send = () => {
    setError(null);
    create.mutate(
      { item_id: id, start_date: start, end_date: end, message: message.trim() || undefined },
      {
        onSuccess: (r) => router.replace({ pathname: '/request/[id]', params: { id: r.transaction_id } }),
        onError: (e) => setError(e.message),
      },
    );
  };

  if (isLoading) {
    return (
      <Screen title="Request to borrow" back>
        <Loading />
      </Screen>
    );
  }
  if (!item) {
    return (
      <Screen title="Request to borrow" back>
        <ErrorText message="This item is not available any more." />
      </Screen>
    );
  }

  return (
    <Screen title="Request to borrow" subtitle={item.title} back>
      <Card style={{ flexDirection: 'row', gap: 16, alignItems: 'center' }}>
        <ItemThumb title={item.title} size={88} />
        <View style={{ flex: 1, gap: 8 }}>
          <Title size={22}>{item.title}</Title>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Avatar name={item.owner_name} size={28} />
            <Caption style={{ flex: 1 }}>Shared by {item.owner_name}</Caption>
          </View>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
            <Badge label={BAND_LABEL[item.value_band] ?? item.value_band} tone={theme.colors.neutral} />
            {item.deposit_amount > 0 ? <Badge label="Deposit at handover" tone={theme.colors.info} icon="payments" /> : null}
          </View>
        </View>
      </Card>

      <Card>
        <SectionLabel>When do you need it?</SectionLabel>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ marginHorizontal: -16 }}
          contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
          {days14.map((d) => {
            const date = new Date(`${d}T00:00:00Z`);
            return (
              <Chip
                key={d}
                sublabel={WEEKDAY[date.getUTCDay()]}
                label={`${date.getUTCDate()} ${MONTH[date.getUTCMonth()]}`}
                selected={d === start}
                onPress={() => setStart(d)}
              />
            );
          })}
        </ScrollView>

        <SectionLabel>For how long?</SectionLabel>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          <RoundButton icon="remove" label="One day less" disabled={days <= 1} onPress={() => setDays(days - 1)} />
          <View style={{ alignItems: 'center' }}>
            <Text style={{ fontFamily: theme.fonts.black, fontSize: 30, color: theme.colors.text }}>{days}</Text>
            <Caption>{days === 1 ? 'day' : 'days'}</Caption>
          </View>
          <RoundButton icon="add" label="One day more" disabled={days >= 30} onPress={() => setDays(days + 1)} />
        </View>
        <View style={{ flexDirection: 'row', gap: 8, justifyContent: 'center' }}>
          {[1, 3, 7].map((n) => (
            <Chip key={n} label={n === 7 ? '1 week' : `${n} day${n === 1 ? '' : 's'}`} selected={days === n} onPress={() => setDays(n)} />
          ))}
        </View>
      </Card>

      <Card style={{ gap: 14 }}>
        <View style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
          <Icon name="event_available" size={22} color={theme.colors.primary} />
          <View style={{ flex: 1 }}>
            <Caption>Pick up</Caption>
            <Body style={{ fontFamily: theme.fonts.bold }}>{longDay(start)}</Body>
          </View>
        </View>
        <View style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
          <Icon name="assignment_return" size={22} color={theme.colors.primary} />
          <View style={{ flex: 1 }}>
            <Caption>Return by</Caption>
            <Body style={{ fontFamily: theme.fonts.bold }}>{longDay(end)}</Body>
          </View>
        </View>
        <Field
          label="Message to the lender (optional)"
          value={message}
          onChangeText={setMessage}
          placeholder="Say hello and what you need it for"
          multiline
        />
      </Card>

      <Banner tone={theme.colors.info} title="Nothing is reserved yet" icon="info">
        <Body muted style={{ fontSize: 14 }}>
          Sending a request does not block these dates for anyone else. They are reserved only when the lender
          accepts.
        </Body>
      </Banner>
      <ErrorText message={error} />
      <Button label="Send request" icon="send" loading={create.isPending} onPress={send} />
    </Screen>
  );
}
