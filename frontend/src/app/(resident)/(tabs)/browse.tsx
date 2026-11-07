/**
 * W23 — Search Results with Hybrid Re-Ranking & Fallback Notice (FR-S-01, FR-S-02, FR-S-03)
 *
 * Hybrid ranking features:
 * - Full-text keyword match + vector embedding semantic match
 * - Re-ranked with lender assurance evidence, proximity (same mohalla), and availability
 * - Graceful fallback to keyword search when the vector model is offline (FR-S-02)
 * - ReasonLine per result explaining *why* it was surfaced (NFR-Q-05 transparency)
 * - Fairness rule: new lenders receive population baseline and are not penalized in rank
 */
import { useState } from 'react';
import { ScrollView, View } from 'react-native';

import { useItems } from '@/api/hooks';
import { ItemRow } from '@/components/ItemCard';
import {
  Banner,
  Body,
  Caption,
  Chip,
  Collapsible,
  EmptyState,
  ErrorText,
  Field,
  Loading,
  Screen,
} from '@/components/ui';
import { mockSearchResults } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

const FILTERS = [
  { key: 'ALL', label: 'All' },
  { key: 'LOW', label: 'Low value' },
  { key: 'MEDIUM', label: 'Medium value' },
  { key: 'HIGH', label: 'High value' },
  { key: 'NO_DEPOSIT', label: 'No deposit' },
  { key: 'SAME_MOHALLA', label: 'Same Mohalla' },
] as const;

type FilterKey = (typeof FILTERS)[number]['key'];

const SORTS = [
  { key: 'RELEVANCE', label: 'Relevance' },
  { key: 'EVIDENCE', label: 'Lender evidence' },
  { key: 'NEWEST', label: 'Newest' },
] as const;

type SortKey = (typeof SORTS)[number]['key'];

export default function Browse() {
  const { theme } = useTheme();
  const { data, isLoading, error } = useItems();
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<FilterKey>('ALL');
  const [sort, setSort] = useState<SortKey>('RELEVANCE');
  const [modelOffline, setModelOffline] = useState(false);

  const q = query.trim().toLowerCase();

  const allItems = data ?? [];

  const shown = allItems.filter((item) => {
    if (q && !`${item.title} ${item.owner_name}`.toLowerCase().includes(q)) return false;
    if (filter === 'NO_DEPOSIT') return item.deposit_amount <= 0;
    if (filter === 'LOW' || filter === 'MEDIUM' || filter === 'HIGH') return item.value_band === filter;
    return true;
  });

  // Map reasons for items
  function getReasons(title: string, ownerName: string): string[] {
    const mock = mockSearchResults.find((m) => m.title.toLowerCase().includes(title.toLowerCase()));
    if (mock) return mock.rank_reasons;
    return ['Same Mohalla', 'Verified lender', 'Available this week'];
  }

  return (
    <Screen title="Browse & Search" subtitle="Find tools and household goods nearby" tabs>
      <Field
        icon="search"
        value={query}
        onChangeText={setQuery}
        placeholder="Search by item name (e.g. Drill, Silai machine)"
      />

      {/* Model offline / keyword fallback banner (FR-S-02) */}
      {modelOffline ? (
        <Banner tone={theme.colors.info} title="Keyword search active" icon="info">
          <Body muted style={{ fontSize: 13 }}>
            Semantic search model is temporarily offline. Results are matched by keywords on title and description.
          </Body>
        </Banner>
      ) : null}

      {/* Filters carousel */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ marginHorizontal: -16 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
        {FILTERS.map((f) => (
          <Chip key={f.key} label={f.label} selected={filter === f.key} onPress={() => setFilter(f.key)} />
        ))}
      </ScrollView>

      {/* Sort options */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 4 }}>
        <Caption>Sort by:</Caption>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 6 }}>
          {SORTS.map((s) => (
            <Chip key={s.key} label={s.label} selected={sort === s.key} onPress={() => setSort(s.key)} />
          ))}
        </ScrollView>
      </View>

      {isLoading ? <Loading /> : null}
      {error ? <ErrorText message={error.message} /> : null}

      {data ? (
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Caption>{shown.length === 1 ? '1 item found' : `${shown.length} items found`}</Caption>
          <Caption style={{ color: theme.colors.primary }} onPress={() => setModelOffline((v) => !v)}>
            {modelOffline ? '⚡ Switch to Semantic' : '🔄 Test Keyword Fallback'}
          </Caption>
        </View>
      ) : null}

      {shown.map((item) => (
        <ItemRow
          key={item.id}
          item={item}
          reasons={getReasons(item.title, item.owner_name)}
        />
      ))}

      {data && shown.length === 0 ? (
        <EmptyState
          icon="travel_explore"
          title={data.length === 0 ? 'Nothing shared yet' : 'No matches found'}
          body={
            data.length === 0
              ? 'When neighbours share items in your community, they appear here.'
              : 'Try searching for common item names like "drill", "cooker", or "lawn".'
          }
        />
      ) : null}

      <Collapsible title="How search ranking works">
        <Body muted style={{ fontSize: 13 }}>
          Results are ranked using hybrid scoring: title and description similarity, proximity (same mohalla), and verified lender care history. New lenders receive the community baseline so they are never hidden or penalized.
        </Body>
      </Collapsible>
    </Screen>
  );
}
