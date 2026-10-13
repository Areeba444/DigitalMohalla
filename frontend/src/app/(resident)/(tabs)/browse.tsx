import { useState } from 'react';
import { ScrollView } from 'react-native';

import { useItems } from '@/api/hooks';
import { ItemRow } from '@/components/ItemCard';
import { Caption, Chip, EmptyState, ErrorText, Field, Loading, Screen } from '@/components/ui';

const FILTERS = [
  { key: 'ALL', label: 'All' },
  { key: 'LOW', label: 'Low value' },
  { key: 'MEDIUM', label: 'Medium value' },
  { key: 'HIGH', label: 'High value' },
  { key: 'NO_DEPOSIT', label: 'No deposit' },
] as const;

type FilterKey = (typeof FILTERS)[number]['key'];

export default function Browse() {
  const { data, isLoading, error } = useItems();
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<FilterKey>('ALL');

  const q = query.trim().toLowerCase();
  const shown = (data ?? []).filter((item) => {
    if (q && !`${item.title} ${item.owner_name}`.toLowerCase().includes(q)) return false;
    if (filter === 'NO_DEPOSIT') return item.deposit_amount <= 0;
    if (filter !== 'ALL') return item.value_band === filter;
    return true;
  });

  return (
    <Screen title="Browse" subtitle="Shared by neighbours in your community" tabs>
      <Field icon="search" value={query} onChangeText={setQuery} placeholder="Search items or neighbours" />
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ marginHorizontal: -16 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
        {FILTERS.map((f) => (
          <Chip key={f.key} label={f.label} selected={filter === f.key} onPress={() => setFilter(f.key)} />
        ))}
      </ScrollView>

      {isLoading ? <Loading /> : null}
      {error ? <ErrorText message={error.message} /> : null}
      {data ? <Caption>{shown.length === 1 ? '1 item' : `${shown.length} items`}</Caption> : null}
      {shown.map((item) => (
        <ItemRow key={item.id} item={item} />
      ))}
      {data && shown.length === 0 ? (
        <EmptyState
          icon="travel_explore"
          title={data.length === 0 ? 'Nothing shared yet' : 'No matches'}
          body={
            data.length === 0
              ? 'When neighbours share items in your community, they appear here.'
              : 'Try another word or clear the filter.'
          }
        />
      ) : null}
    </Screen>
  );
}
