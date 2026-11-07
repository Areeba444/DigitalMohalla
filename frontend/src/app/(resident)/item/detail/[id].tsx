/**
 * W24 — Item Details with Lender Assurance Tier (FR-S-04, FR-B-04, NFR-U-01)
 *
 * Shows full item info + lender multi-dimensional evidence panel before requesting.
 * ZERO composite trust score. Assurance state + multi-line summary only.
 *
 * HCI notes:
 * - Availability calendar: color + pattern (not color alone) distinguishes available/reserved.
 * - Lender assurance panel collapses by default (progressive disclosure).
 * - Bottom fixed "Request to Borrow" is the ONLY primary CTA.
 * - New lenders display population baseline — never penalized in ranking or displayed as risky.
 */
import { router } from 'expo-router';
import { View, Text, ScrollView } from 'react-native';

import {
  AssuranceBadge,
  Avatar,
  Body,
  Button,
  Card,
  Caption,
  Chip,
  Collapsible,
  Icon,
  ItemThumb,
  Screen,
  SectionLabel,
  Title,
} from '@/components/ui';
import { mockItemDetail } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

export default function ItemDetail() {
  const { theme } = useTheme();
  const item = mockItemDetail;

  return (
    <Screen title={item.title} subtitle={item.category.replace('_', ' ')} back>
      {/* Item hero illustration */}
      <Card style={{ alignItems: 'center', paddingVertical: 24 }}>
        <ItemThumb title={item.title} size={120} />
      </Card>

      {/* Core item details */}
      <Card>
        <Title size={20}>{item.title}</Title>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
          <Chip label={item.condition} selected={false} />
          <Chip label={item.category.replace('_', ' ')} selected={false} />
          {item.deposit_amount > 0 ? (
            <Chip label={`PKR ${item.deposit_amount} deposit`} selected={false} />
          ) : (
            <Chip label="No deposit" selected={false} />
          )}
        </View>
        <Body muted style={{ fontSize: 14, marginTop: 4 }}>{item.description}</Body>
      </Card>

      {/* Availability calendar — compact horizontal date strip */}
      <Card>
        <SectionLabel>Availability</SectionLabel>
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
        <Caption style={{ marginTop: 4 }}>Showing next 5 days · dates update when requests are confirmed</Caption>
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

