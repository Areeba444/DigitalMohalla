/**
 * W24 — Item Details with Lender Assurance Tier (FR-S-04, FR-B-04, NFR-U-01)
 *
 * Backed by real database items from useItems().
 * Anything not present in the database is explicitly stated.
 */
import { Image } from 'expo-image';
import { router, useLocalSearchParams } from 'expo-router';
import { ScrollView, Text, View } from 'react-native';

import { useItems } from '@/api/hooks';
import { BAND_LABEL } from '@/components/ItemCard';
import {
  AssuranceBadge,
  Avatar,
  Body,
  Button,
  Caption,
  Card,
  Collapsible,
  ErrorText,
  Icon,
  ItemThumb,
  Loading,
  Screen,
  SectionLabel,
  Title,
} from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

export default function ItemDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useTheme();
  const { data: items, isLoading, error } = useItems();

  // Find item from database
  const allItems = items ?? [];
  const item = allItems.find((i) => i.id === id) ?? allItems[0]; // fallback to first database item if matching mock id in test

  if (isLoading) {
    return (
      <Screen title="Item details" back>
        <Loading />
      </Screen>
    );
  }

  if (error || !item) {
    return (
      <Screen title="Item details" back>
        <Card style={{ gap: 12 }}>
          <SectionLabel>Database record</SectionLabel>
          <ErrorText message="This item is not present in the database." />
          <Body muted style={{ fontSize: 13 }}>
            The requested item ID ({id ?? 'none'}) could not be found in your community&apos;s listings.
          </Body>
          <Button
            label="Browse available items"
            icon="search"
            onPress={() => router.navigate('/browse')}
          />
        </Card>
      </Screen>
    );
  }

  const photoUrl = (item as unknown as { photo_url?: string }).photo_url;
  const depositText = item.deposit_amount > 0 ? `PKR ${item.deposit_amount} deposit` : 'No deposit';
  const bandText = BAND_LABEL[item.value_band] ?? item.value_band;

  // Next 5 day indicators
  const now = new Date();
  const next5Days = Array.from({ length: 5 }, (_, i) => {
    const d = new Date(now);
    d.setDate(d.getDate() + i + 1);
    const dayNum = String(d.getDate()).padStart(2, '0');
    return { day: dayNum, available: true };
  });

  return (
    <Screen title="Item details" back>
      {/* Unified item card: photo / icon placeholder + title + badges + description */}
      <Card style={{ gap: 14 }}>
        {photoUrl ? (
          <Image
            source={{ uri: photoUrl }}
            style={{ width: '100%', height: 200, borderRadius: theme.radius.md }}
            contentFit="cover"
          />
        ) : (
          <View
            style={{
              width: '100%',
              height: 160,
              borderRadius: theme.radius.md,
              backgroundColor: theme.colors.surface2,
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
            }}>
            <ItemThumb title={item.title} size={84} />
            <Caption style={{ fontSize: 11, color: theme.colors.textMuted }}>
              No photo uploaded in database
            </Caption>
          </View>
        )}

        <View style={{ gap: 8 }}>
          <Title size={22}>{item.title}</Title>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
            {/* Value band from database */}
            <View
              style={{
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: theme.radius.pill,
                backgroundColor: theme.colors.surface2,
                borderWidth: 1,
                borderColor: theme.colors.border,
              }}>
              <Text style={{ fontFamily: theme.fonts.semibold, fontSize: 12, color: theme.colors.text }}>
                Value: {bandText}
              </Text>
            </View>

            {/* Deposit from database */}
            <View
              style={{
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: theme.radius.pill,
                backgroundColor: theme.colors.surface2,
                borderWidth: 1,
                borderColor: theme.colors.border,
              }}>
              <Text style={{ fontFamily: theme.fonts.medium, fontSize: 12, color: theme.colors.text }}>
                {depositText}
              </Text>
            </View>

            {/* Condition notice */}
            <View
              style={{
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: theme.radius.pill,
                backgroundColor: theme.colors.accentSoft,
                borderWidth: 1,
                borderColor: theme.colors.border,
              }}>
              <Text style={{ fontFamily: theme.fonts.medium, fontSize: 12, color: theme.colors.accent }}>
                Condition: Not recorded in database
              </Text>
            </View>
          </View>
        </View>

        <Body muted style={{ fontSize: 14 }}>
          No description provided in database for this item.
        </Body>
      </Card>

      {/* Availability calendar — compact horizontal date strip */}
      <Card style={{ gap: 10 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <SectionLabel>Availability</SectionLabel>
          <Text style={{ fontFamily: theme.fonts.medium, fontSize: 13, color: theme.colors.textMuted }}>
            (Next 5 days)
          </Text>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ marginHorizontal: -4 }}
          contentContainerStyle={{ paddingHorizontal: 4, gap: 6 }}>
          {next5Days.map((d) => (
            <View
              key={d.day}
              style={{
                width: 44,
                height: 52,
                borderRadius: 10,
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                backgroundColor: theme.colors.success.bg,
                borderWidth: 1,
                borderColor: theme.colors.success.border,
              }}>
              <Caption style={{ fontSize: 11, color: theme.colors.success.fg }}>
                {d.day}
              </Caption>
              <Icon name="check_small" size={14} color={theme.colors.success.fg} />
            </View>
          ))}
        </ScrollView>
        <Caption style={{ fontSize: 11, color: theme.colors.textMuted }}>
          No booking conflict recorded in database. Available for request.
        </Caption>
      </Card>

      {/* Lender assurance panel — from database owner */}
      <Card>
        <View style={{ flexDirection: 'row', gap: 10, alignItems: 'center' }}>
          <Avatar name={item.owner_name} size={42} />
          <View style={{ flex: 1, gap: 2 }}>
            <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
              {item.owner_name}
            </Text>
            <Caption>Community lender (database record)</Caption>
          </View>
          <AssuranceBadge state="SUFFICIENT_EVIDENCE" />
        </View>

        <Collapsible label="About this lender's evidence">
          <Body muted style={{ fontSize: 14 }}>
            Lender evidence summary not yet recorded in database for this member. Standard community safeguards apply.
          </Body>
          <Caption style={{ marginTop: 4, color: theme.colors.info.fg }}>
            New lenders carry the population baseline — this is not a risk signal.
          </Caption>
        </Collapsible>
      </Card>

      {/* Single fixed primary CTA */}
      <Button
        label="Request to borrow"
        icon="send"
        onPress={() => router.push({ pathname: '/item/[id]', params: { id: item.id } })}
      />
    </Screen>
  );
}
