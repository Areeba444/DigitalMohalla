import { router } from 'expo-router';
import { ScrollView, Text, View } from 'react-native';

import { useItems, useMyRequests } from '@/api/hooks';
import { ItemTile } from '@/components/ItemCard';
import { RequestCard } from '@/components/RequestCard';
import {
  Button,
  Caption,
  EmptyState,
  ErrorText,
  HeroScreen,
  Icon,
  type IconName,
  Loading,
  SectionHeader,
  SectionLabel,
  Title,
} from '@/components/ui';
import { isClosed, needsYou } from '@/lib/requests';
import { useTheme } from '@/theme/ThemeProvider';

function Stat({ icon, value, label }: { icon: IconName; value: number; label: string }) {
  const { theme } = useTheme();
  return (
    <View
      style={{
        flex: 1,
        padding: 12,
        gap: 6,
        borderRadius: theme.radius.md,
        backgroundColor: theme.colors.surface,
        boxShadow: theme.shadow.card,
      }}>
      <View
        style={{
          width: 32,
          height: 32,
          borderRadius: 10,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: theme.colors.primarySoft,
        }}>
        <Icon name={icon} size={18} color={theme.colors.primary} />
      </View>
      <Text style={{ fontFamily: theme.fonts.black, fontSize: 22, color: theme.colors.text }}>{value}</Text>
      <Caption>{label}</Caption>
    </View>
  );
}

export default function Home() {
  const { theme } = useTheme();
  const requests = useMyRequests();
  const items = useItems();
  const all = requests.data ?? [];
  const waiting = all.filter(needsYou);
  const onLoan = all.filter((r) => ['ACCEPTED', 'ACTIVE', 'RETURN_INITIATED', 'RETURNED'].includes(r.state ?? ''));
  const done = all.filter((r) => r.state === 'COMPLETED');
  const recent = all.filter((r) => !needsYou(r) && !isClosed(r)).slice(0, 3);
  const [first, ...moreWaiting] = waiting;

  return (
    <HeroScreen
      tabs
      height={250}
      hero={
        <View style={{ flex: 1, justifyContent: 'space-between' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Icon name="location_city" size={20} color={theme.hero.text} />
            <Text style={{ fontFamily: theme.fonts.bold, fontSize: 14, color: theme.hero.text, letterSpacing: 0.4 }}>
              Digital Mohalla
            </Text>
          </View>
          <View style={{ gap: 6 }}>
            <SectionLabel color={theme.hero.textSoft}>Your neighbourhood</SectionLabel>
            <Title size={32} color={theme.hero.text} style={{ fontFamily: theme.fonts.displayAlt }}>
              Share more, worry less.
            </Title>
          </View>
        </View>
      }>
      <View style={{ flexDirection: 'row', gap: 10 }}>
        <Stat icon="notifications_active" value={waiting.length} label="Waiting for you" />
        <Stat icon="handshake" value={onLoan.length} label="In progress" />
        <Stat icon="task_alt" value={done.length} label="Completed" />
      </View>

      {requests.isLoading ? <Loading /> : null}
      {requests.error ? (
        <>
          <ErrorText message={requests.error.message} />
          <Button label="Try again" variant="outline" icon="refresh" onPress={() => requests.refetch()} />
        </>
      ) : null}

      {first ? (
        <>
          <SectionHeader title="Needs your attention" />
          <RequestCard r={first} highlight />
          {moreWaiting.map((r) => (
            <RequestCard key={r.id} r={r} />
          ))}
        </>
      ) : null}

      <SectionHeader title="Available nearby" action="See all" onAction={() => router.navigate('/browse')} />
      {items.isLoading ? <Loading /> : null}
      {items.data && items.data.length > 0 ? (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ marginHorizontal: -16 }}
          contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 4, gap: 12 }}>
          {items.data.map((item) => (
            <ItemTile key={item.id} item={item} />
          ))}
        </ScrollView>
      ) : null}
      {items.data && items.data.length === 0 ? (
        <EmptyState
          icon="inventory_2"
          title="Nothing to borrow yet"
          body="When neighbours share items in your community, they appear here."
        />
      ) : null}

      {recent.length > 0 ? (
        <>
          <SectionHeader title="In progress" action="All activity" onAction={() => router.navigate('/activity')} />
          {recent.map((r) => (
            <RequestCard key={r.id} r={r} />
          ))}
        </>
      ) : null}

      {requests.data && all.length === 0 ? (
        <EmptyState
          icon="volunteer_activism"
          title="Your first borrow is a tap away"
          body="Pick an item a neighbour is sharing and send a request. The lender sees your evidence summary, never a score.">
          <Button label="Browse items" icon="search" onPress={() => router.navigate('/browse')} />
        </EmptyState>
      ) : null}
    </HeroScreen>
  );
}
