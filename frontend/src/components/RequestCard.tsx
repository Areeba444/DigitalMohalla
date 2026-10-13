import { router } from 'expo-router';
import { Text, View } from 'react-native';

import type { MyRequest } from '@/api/hooks';
import { AssuranceBadge, Caption, Card, Icon, ItemThumb, LifecycleBadge } from '@/components/ui';
import { formatPeriod } from '@/lib/format';
import { nextStep } from '@/lib/requests';
import { useTheme } from '@/theme/ThemeProvider';

/** A request in a list: the item, the other person, the dates, the state and what happens next. */
export function RequestCard({ r, highlight }: { r: MyRequest; highlight?: boolean }) {
  const { theme } = useTheme();
  const lender = r.your_role === 'LENDER';
  const step = nextStep(r);
  return (
    <Card
      accessibilityLabel={`${r.title}, ${lender ? 'requested by' : 'lent by'} ${r.counterpart_name}`}
      onPress={() => router.push({ pathname: '/request/[id]', params: { id: r.id } })}
      style={
        highlight
          ? { borderWidth: 1.5, borderColor: theme.colors.primary, backgroundColor: theme.colors.surface }
          : undefined
      }>
      <View style={{ flexDirection: 'row', gap: 14 }}>
        <ItemThumb title={r.title} size={58} />
        <View style={{ flex: 1, gap: 6 }}>
          <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 8 }}>
            <Text
              numberOfLines={1}
              style={{ flex: 1, fontFamily: theme.fonts.bold, fontSize: 16.5, color: theme.colors.text }}>
              {r.title}
            </Text>
            <Icon name="chevron_right" size={22} color={theme.colors.textMuted} />
          </View>
          <Caption>
            {lender ? 'Requested by' : 'Lent by'} {r.counterpart_name} · {formatPeriod(r.requested_period)}
          </Caption>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
            <LifecycleBadge state={r.state} role={r.your_role} />
            {lender && r.assurance_state ? <AssuranceBadge state={r.assurance_state} /> : null}
          </View>
        </View>
      </View>
      {step ? (
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 8,
            paddingTop: 10,
            borderTopWidth: 1,
            borderTopColor: theme.colors.hairline,
          }}>
          <Icon name="arrow_forward" size={16} color={highlight ? theme.colors.primary : theme.colors.textMuted} />
          <Text
            style={{
              flex: 1,
              fontFamily: highlight ? theme.fonts.semibold : theme.fonts.medium,
              fontSize: 13.5,
              color: highlight ? theme.colors.primaryDeep : theme.colors.textSecondary,
            }}>
            {step}
          </Text>
        </View>
      ) : null}
    </Card>
  );
}
