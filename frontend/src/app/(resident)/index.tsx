import { router } from 'expo-router';
import { Pressable, Text, View } from 'react-native';

import { useMyRequests, type MyRequest } from '@/api/hooks';
import { useAuth } from '@/auth/AuthProvider';
import {
  AssuranceBadge,
  Body,
  Button,
  Card,
  ErrorText,
  LifecycleBadge,
  Loading,
  Screen,
  SectionLabel,
  ThemeSwitcher,
} from '@/components/ui';
import { formatPeriod } from '@/lib/format';
import { useTheme } from '@/theme/ThemeProvider';

/** Does this request wait for the signed-in person? (Only groups the list; buttons come from the API.) */
function needsYou(r: MyRequest): boolean {
  const state = r.state ?? '';
  if (r.your_role === 'LENDER') return ['ASSESSED', 'ACCEPTED', 'RETURN_INITIATED'].includes(state);
  return ['ACCEPTED', 'ACTIVE', 'RETURN_INITIATED'].includes(state);
}

function RequestCard({ r }: { r: MyRequest }) {
  const { theme } = useTheme();
  return (
    <Pressable
      accessibilityRole="button"
      onPress={() => router.push({ pathname: '/request/[id]', params: { id: r.id } })}>
      <Card>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', gap: 8 }}>
          <Text style={{ flex: 1, fontSize: 16, fontWeight: '700', color: theme.colors.text }}>
            {r.title}
          </Text>
          <LifecycleBadge state={r.state} />
        </View>
        <Body muted>
          {r.your_role === 'LENDER' ? 'Requested by' : 'Lender'} {r.counterpart_name} ·{' '}
          {formatPeriod(r.requested_period)}
        </Body>
        {r.your_role === 'LENDER' && r.assurance_state ? (
          <AssuranceBadge state={r.assurance_state} />
        ) : null}
      </Card>
    </Pressable>
  );
}

export default function Home() {
  const { signOut } = useAuth();
  const { data, isLoading, error, refetch } = useMyRequests();
  const waiting = (data ?? []).filter(needsYou);
  const rest = (data ?? []).filter((r) => !needsYou(r));

  return (
    <Screen title="My requests" subtitle="Digital Mohalla" right={<ThemeSwitcher />}>
      <View style={{ flexDirection: 'row', gap: 10 }}>
        <View style={{ flex: 1 }}>
          <Button label="Browse items" onPress={() => router.push('/browse')} />
        </View>
        <Button label="Sign out" variant="ghost" onPress={signOut} />
      </View>
      {isLoading ? <Loading /> : null}
      {error ? (
        <>
          <ErrorText message={error.message} />
          <Button label="Try again" variant="outline" onPress={() => refetch()} />
        </>
      ) : null}
      {data && data.length === 0 ? (
        <Card>
          <Body muted>No requests yet. Browse items in your community to borrow something.</Body>
        </Card>
      ) : null}
      {waiting.length > 0 ? <SectionLabel>Needs your attention</SectionLabel> : null}
      {waiting.map((r) => (
        <RequestCard key={r.id} r={r} />
      ))}
      {rest.length > 0 ? <SectionLabel>Everything else</SectionLabel> : null}
      {rest.map((r) => (
        <RequestCard key={r.id} r={r} />
      ))}
    </Screen>
  );
}
