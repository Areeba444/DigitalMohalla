import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView } from 'react-native';

import { useMyRequests } from '@/api/hooks';
import { RequestCard } from '@/components/RequestCard';
import { Button, Chip, EmptyState, ErrorText, Loading, Screen } from '@/components/ui';
import { isClosed, needsYou } from '@/lib/requests';

const SEGMENTS = [
  { key: 'all', label: 'All' },
  { key: 'you', label: 'Needs you' },
  { key: 'open', label: 'In progress' },
  { key: 'closed', label: 'Closed' },
] as const;

type Segment = (typeof SEGMENTS)[number]['key'];

export default function Activity() {
  const { data, isLoading, error, refetch } = useMyRequests();
  const [segment, setSegment] = useState<Segment>('all');
  const all = data ?? [];
  const shown = all.filter((r) =>
    segment === 'you' ? needsYou(r) : segment === 'open' ? !isClosed(r) && !needsYou(r) : segment === 'closed' ? isClosed(r) : true,
  );
  const count = (s: Segment) =>
    s === 'all' ? all.length : all.filter((r) => (s === 'you' ? needsYou(r) : s === 'open' ? !isClosed(r) && !needsYou(r) : isClosed(r))).length;

  return (
    <Screen title="Activity" subtitle="Everything you borrowed or lent" tabs>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ marginHorizontal: -16 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
        {SEGMENTS.map((s) => (
          <Chip
            key={s.key}
            label={data ? `${s.label} · ${count(s.key)}` : s.label}
            selected={segment === s.key}
            onPress={() => setSegment(s.key)}
          />
        ))}
      </ScrollView>
      {isLoading ? <Loading /> : null}
      {error ? (
        <>
          <ErrorText message={error.message} />
          <Button label="Try again" variant="outline" icon="refresh" onPress={() => refetch()} />
        </>
      ) : null}
      {shown.map((r) => (
        <RequestCard key={r.id} r={r} highlight={needsYou(r)} />
      ))}
      {data && shown.length === 0 ? (
        <EmptyState
          icon={segment === 'you' ? 'task_alt' : 'history'}
          title={segment === 'you' ? 'You are all caught up' : 'Nothing here yet'}
          body={
            segment === 'you'
              ? 'Nothing is waiting for you right now.'
              : 'Requests you send or receive will appear here with their full history.'
          }>
          {all.length === 0 ? (
            <Button label="Browse items" icon="search" onPress={() => router.navigate('/browse')} />
          ) : null}
        </EmptyState>
      ) : null}
    </Screen>
  );
}
