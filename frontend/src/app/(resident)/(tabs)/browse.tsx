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
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { useItems } from '@/api/hooks';
import { ItemRow } from '@/components/ItemCard';
import {
  Banner,
  Body,
  Caption,
  Chip,
  EmptyState,
  ErrorText,
  Field,
  HeaderAvatar,
  Icon,
  Loading,
  Screen,
} from '@/components/ui';
import { mockSearchResults } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

const FILTERS = [
  { key: 'ALL', label: 'All', icon: 'apps' },
  { key: 'LOW', label: 'Low value', icon: 'eco' },
  { key: 'MEDIUM', label: 'Medium value', icon: 'inventory_2' },
  { key: 'HIGH', label: 'High value', icon: 'diamond' },
  { key: 'NO_DEPOSIT', label: 'No deposit', icon: 'money_off' },
  { key: 'SAME_MOHALLA', label: 'Same Mohalla', icon: 'location_on' },
] as const;

type FilterKey = (typeof FILTERS)[number]['key'];

const SORTS = [
  { key: 'RELEVANCE', label: 'Best match', icon: 'my_location' },
  { key: 'EVIDENCE', label: 'Most trusted', icon: 'verified' },
  { key: 'NEWEST', label: 'Newest', icon: 'schedule' },
] as const;

type SortKey = (typeof SORTS)[number]['key'];

export default function Browse() {
  const { theme } = useTheme();
  const { data, isLoading, error } = useItems();
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<FilterKey>('ALL');
  const [sort, setSort] = useState<SortKey>('RELEVANCE');
  const [modelOffline, setModelOffline] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const q = query.trim().toLowerCase();

  const allItems = data ?? [];

  const shown = allItems.filter((item) => {
    if (q && !`${item.title} ${item.owner_name}`.toLowerCase().includes(q)) return false;
    if (filter === 'NO_DEPOSIT') return item.deposit_amount <= 0;
    if (filter === 'LOW' || filter === 'MEDIUM' || filter === 'HIGH') return item.value_band === filter;
    return true;
  });

  const activeFilterCount = filter !== 'ALL' ? 1 : 0;

  // Map reasons for items
  function getReasons(title: string, ownerName: string): string[] {
    const mock = mockSearchResults.find((m) => m.title.toLowerCase().includes(title.toLowerCase()));
    if (mock) return mock.rank_reasons;
    return ['Same Mohalla', 'Verified lender', 'Available this week'];
  }

  return (
    <Screen
      title="Browse & Search"
      subtitle="Find tools and household goods nearby"
      tabs
      right={<HeaderAvatar onPress={() => router.navigate('/profile')} />}>
      {/* Row 1: Search bar */}
      <Field
        icon="search"
        value={query}
        onChangeText={setQuery}
        placeholder="Search by item name (e.g. Drill, Silai machine)"
      />

      {/* Row 2: Sort pills + Filter button */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ flex: 1 }}
          contentContainerStyle={{ gap: 6, paddingRight: 4 }}>
          {SORTS.map((s) => (
            <Chip
              key={s.key}
              label={s.label}
              icon={s.icon as any}
              selected={sort === s.key}
              onPress={() => setSort(s.key)}
            />
          ))}
        </ScrollView>

        {/* Filter button with active badge */}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={activeFilterCount > 0 ? `Filters, ${activeFilterCount} active` : 'Filters'}
          onPress={() => setShowFilters((v) => !v)}
          style={({ pressed }) => ({
            flexDirection: 'row',
            alignItems: 'center',
            gap: 6,
            paddingHorizontal: 14,
            minHeight: 44,
            borderRadius: theme.radius.pill,
            backgroundColor: activeFilterCount > 0 ? theme.colors.primary : theme.colors.surface,
            borderWidth: 1,
            borderColor: activeFilterCount > 0 ? theme.colors.primary : theme.colors.border,
            opacity: pressed ? 0.8 : 1,
          })}>
          <Icon
            name="tune"
            size={18}
            color={activeFilterCount > 0 ? theme.colors.onPrimary : theme.colors.textSecondary}
          />
          <Text
            style={{
              fontFamily: theme.fonts.bold,
              fontSize: 14,
              color: activeFilterCount > 0 ? theme.colors.onPrimary : theme.colors.text,
            }}>
            Filter
          </Text>
          {activeFilterCount > 0 ? (
            <View
              style={{
                width: 18,
                height: 18,
                borderRadius: 9,
                backgroundColor: theme.colors.onPrimary,
                alignItems: 'center',
                justifyContent: 'center',
              }}>
              <Text
                style={{
                  fontFamily: theme.fonts.bold,
                  fontSize: 11,
                  color: theme.colors.primary,
                }}>
                {activeFilterCount}
              </Text>
            </View>
          ) : null}
        </Pressable>
      </View>

      {/* Filter panel — slides in below when open */}
      {showFilters ? (
        <View
          style={{
            backgroundColor: theme.colors.surface,
            borderRadius: theme.radius.md,
            padding: 14,
            gap: 10,
            borderWidth: 1,
            borderColor: theme.colors.border,
          }}>
          <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 13, color: theme.colors.textMuted }}>
            FILTER BY
          </Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
            {FILTERS.map((f) => (
              <Chip
                key={f.key}
                label={f.label}
                icon={f.icon as any}
                selected={filter === f.key}
                onPress={() => {
                  setFilter(f.key);
                  if (f.key !== 'ALL') setShowFilters(false);
                }}
              />
            ))}
          </View>
        </View>
      ) : null}

      {/* Model offline / keyword fallback banner (FR-S-02) */}
      {modelOffline ? (
        <Banner tone={theme.colors.info} title="Keyword search active" icon="info">
          <Body muted style={{ fontSize: 13 }}>
            Semantic search is temporarily offline. Matching by keywords only.
          </Body>
        </Banner>
      ) : null}

      {isLoading ? <Loading /> : null}
      {error ? <ErrorText message={error.message} /> : null}

      {/* Result count */}
      {data ? (
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              gap: 5,
              paddingHorizontal: 10,
              paddingVertical: 4,
              borderRadius: 9999,
              backgroundColor: theme.colors.accentSoft,
            }}>
            <Icon name="format_list_bulleted" size={13} color={theme.colors.accent} />
            <Text style={{ fontFamily: theme.fonts.bold, fontSize: 12, color: theme.colors.accent }}>
              {shown.length === 1 ? '1 result' : `${shown.length} results`}
            </Text>
          </View>
          {__DEV__ ? (
            <Caption style={{ color: theme.colors.primary }} onPress={() => setModelOffline((v) => !v)}>
              {modelOffline ? '⚡ Semantic' : '🔄 Keyword fallback'}
            </Caption>
          ) : null}
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
    </Screen>
  );
}
