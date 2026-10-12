import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { useCreateRequest, useItems } from '@/api/hooks';
import {
  Banner,
  Body,
  Button,
  Card,
  ErrorText,
  Field,
  Loading,
  Row,
  Screen,
} from '@/components/ui';
import { addDays, isoDate } from '@/lib/format';
import { useTheme } from '@/theme/ThemeProvider';

export default function NewRequest() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useTheme();
  const { data, isLoading } = useItems();
  const create = useCreateRequest();
  const item = data?.find((i) => i.id === id);

  const [start, setStart] = useState(isoDate(addDays(new Date(), 3)));
  const [days, setDays] = useState(3);
  const [message, setMessage] = useState('');
  const [error, setError] = useState<string | null>(null);

  const valid = /^\d{4}-\d{2}-\d{2}$/.test(start) && !Number.isNaN(Date.parse(start));
  const end = valid ? isoDate(addDays(new Date(`${start}T00:00:00Z`), days)) : '';

  const send = () => {
    setError(null);
    create.mutate(
      { item_id: id, start_date: start, end_date: end, message: message || undefined },
      {
        onSuccess: (r) =>
          router.replace({ pathname: '/request/[id]', params: { id: r.transaction_id } }),
        onError: (e) => setError(e.message),
      },
    );
  };

  if (isLoading) {
    return (
      <Screen title="Request" back>
        <Loading />
      </Screen>
    );
  }
  if (!item) {
    return (
      <Screen title="Request" back>
        <ErrorText message="This item is not available." />
      </Screen>
    );
  }

  return (
    <Screen title="Request to borrow" subtitle={item.title} back>
      <Card>
        <Row label="Item" value={item.title} />
        <Row label="Shared by" value={item.owner_name} />
        {item.deposit_amount > 0 ? (
          <Row label="Deposit" value="Recorded at handover (no payment in app)" />
        ) : null}
      </Card>
      <Card>
        <Field label="First day (YYYY-MM-DD)" value={start} onChangeText={setStart} />
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <Button label="−" variant="outline" onPress={() => setDays(Math.max(1, days - 1))} />
          <Body>
            {days} day{days === 1 ? '' : 's'}
            {valid ? ` · returned by ${end}` : ''}
          </Body>
          <Button label="+" variant="outline" onPress={() => setDays(Math.min(30, days + 1))} />
        </View>
        <Field
          label="Message to the lender (optional)"
          value={message}
          onChangeText={setMessage}
          multiline
        />
      </Card>
      <Banner tone={theme.colors.info} title="Soft hold">
        <Body muted>
          Sending a request does not block the dates for anyone else. Dates are reserved only when
          the lender accepts.
        </Body>
      </Banner>
      <ErrorText message={error} />
      <Button label="Send request" loading={create.isPending} disabled={!valid} onPress={send} />
    </Screen>
  );
}
