/**
 * W24 — Item Details with Lender Assurance Tier (FR-S-04, FR-B-04, NFR-U-01)
 *
 * Shows full item info + lender multi-dimensional evidence panel before requesting.
 * ZERO composite trust score. Assurance state + multi-line summary only.
 */
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { ScrollView, Text, View } from 'react-native';

import { mockItemDetail } from '@/api/mocks/iteration2Mocks';
import {
  AssuranceBadge,
  Avatar,
  Body,
  Button,
  Caption,
  Card,
  Collapsible,
  Icon,
  ItemThumb,
  Screen,
  SectionLabel,
  Title,
} from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

function conditionTone(condition: string, theme: ReturnType<typeof useTheme>['theme']) {
  const c = condition.toLowerCase();
  if (c.includes('like new') || c.includes('new')) {
    return { bg: theme.colors.success.bg, border: theme.colors.success.border, fg: theme.colors.success.fg };
  }
  if (c.includes('good')) {
    return { bg: theme.colors.accentSoft, border: theme.colors.border, fg: theme.colors.primary };
  }
  if (c.includes('fair')) {
    return { bg: theme.colors.warning.bg, border: theme.colors.warning.border, fg: theme.colors.warning.fg };
  }
  return { bg: theme.colors.danger.bg, border: theme.colors.danger.border, fg: theme.colors.danger.fg };
}

export default function ItemDetail() {
  const { theme } = useTheme();
  const item = mockItemDetail;
  const photoUrl = (item as unknown as { photo_url?: string }).photo_url;
  const condTone = conditionTone(item.condition, theme);

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
            }}>
            <ItemThumb title={item.title} size={90} />
          </View>
        )}

        <View style={{ gap: 8 }}>
          <Title size={22}>{item.title}</Title>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
            {/* Condition grade with color code */}
            <View
              style={{
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: theme.radius.pill,
                backgroundColor: condTone.bg,
                borderWidth: 1,
                borderColor: condTone.border,
              }}>
              <Text style={{ fontFamily: theme.fonts.bold, fontSize: 12, color: condTone.fg }}>
                Condition: {item.condition}
              </Text>
            </View>

            {/* Type badge */}
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
                Type: {item.category.replace('_', ' ').toLowerCase()}
              </Text>
            </View>

            {/* Deposit badge */}
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
                {item.deposit_amount > 0 ? `Deposit: Rs ${item.deposit_amount}` : 'No deposit'}
              </Text>
            </View>
          </View>
        </View>

        <Body muted style={{ fontSize: 14 }}>
          {item.description}
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
          {item.available_dates.map((d) => (
            <View
              key={d.date}
              style={{
                width: 44,
                height: 52,
                borderRadius: 10,
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                backgroundColor: d.available ? theme.colors.success.bg : theme.colors.surface2,
                borderWidth: 1,
                borderColor: d.available ? theme.colors.success.border : theme.colors.border,
                // Dashed border style for unavailable — pattern, not colour alone
                borderStyle: d.available ? 'solid' : 'dashed',
              }}>
              <Caption style={{ fontSize: 11, color: d.available ? theme.colors.success.fg : theme.colors.textMuted }}>
                {d.date.substring(8)}
              </Caption>
              <Icon
                name={d.available ? 'check_small' : 'close'}
                size={14}
                color={d.available ? theme.colors.success.fg : theme.colors.textMuted}
              />
            </View>
          ))}
        </ScrollView>
      </Card>

      {/* Lender assurance panel — collapsed by default (progressive disclosure) */}
      <Card>
        <View style={{ flexDirection: 'row', gap: 10, alignItems: 'center' }}>
          <Avatar name={item.lender.name} size={42} />
          <View style={{ flex: 1, gap: 2 }}>
            <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
              {item.lender.name}
            </Text>
            <Caption>{item.lender.community}</Caption>
          </View>
          {/* Assurance state badge — text + icon, never colour alone */}
          <AssuranceBadge state={item.lender.assurance_state} />
        </View>

        <Collapsible label="About this lender's evidence">
          <Body muted style={{ fontSize: 14 }}>
            {item.lender.is_new_lender
              ? 'New to Digital Mohalla — standard community safeguards apply. No negative finding.'
              : item.lender.summary_line}
          </Body>
          {item.lender.is_new_lender ? (
            <Caption style={{ marginTop: 4, color: theme.colors.info.fg }}>
              New lenders carry the population baseline — this is not a risk signal.
            </Caption>
          ) : null}
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
