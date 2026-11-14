/**
 * W9 — Join Community: Directory & Rules (FR-A-06, UC-A3)
 *
 * HCI notes:
 * - Scannable card list; community rules in a collapsible section, not a wall of text.
 * - Code input for invite-only communities stays hidden until needed (progressive disclosure).
 * - Single primary CTA "Select & Continue".
 */
import { router } from 'expo-router';
import { useState } from 'react';
import { Text, View } from 'react-native';

import {
  BackButton,
  Body,
  Button,
  Caption,
  Card,
  Collapsible,
  EmptyState,
  Field,
  Icon,
  Screen,
  SectionLabel,
} from '@/components/ui';
import { mockCommunities, type MockCommunity } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

function CommunityCard({
  community,
  selected,
  onSelect,
}: {
  community: MockCommunity;
  selected: boolean;
  onSelect: () => void;
}) {
  const { theme } = useTheme();
  return (
    <Card
      style={{
        borderWidth: selected ? 2 : 1,
        borderColor: selected ? theme.colors.primary : theme.colors.border,
        backgroundColor: selected ? theme.colors.primarySoft : theme.colors.surface,
      }}
      onPress={onSelect}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <View style={{ flex: 1, gap: 2 }}>
          <Text style={{ fontFamily: theme.fonts.bold, fontSize: 16, color: selected ? theme.colors.primaryDeep : theme.colors.text }}>
            {community.name}
          </Text>
          <Caption>{community.city}</Caption>
        </View>
        {selected ? <Icon name="check_circle" size={22} color={theme.colors.primary} /> : null}
      </View>

      <View style={{ flexDirection: 'row', gap: 16 }}>
        <View style={{ flexDirection: 'row', gap: 4, alignItems: 'center' }}>
          <Icon name="group" size={15} color={theme.colors.textMuted} />
          <Caption>{community.members_count} members</Caption>
        </View>
        <View style={{ flexDirection: 'row', gap: 4, alignItems: 'center' }}>
          <Icon name="inventory_2" size={15} color={theme.colors.textMuted} />
          <Caption>{community.active_listings} items shared</Caption>
        </View>
        {community.requires_code ? (
          <View style={{ flexDirection: 'row', gap: 4, alignItems: 'center' }}>
            <Icon name="lock" size={15} color={theme.colors.warning.fg} />
            <Caption style={{ color: theme.colors.warning.fg }}>Invite only</Caption>
          </View>
        ) : null}
      </View>

      <Collapsible label="Community rules">
        <Body muted style={{ fontSize: 13 }}>{community.rules_summary}</Body>
      </Collapsible>
    </Card>
  );
}

export default function JoinCommunity() {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [code, setCode] = useState('');

  const filtered = mockCommunities.filter(
    (c) =>
      !query ||
      c.name.toLowerCase().includes(query.toLowerCase()) ||
      c.sector.toLowerCase().includes(query.toLowerCase()),
  );

  const selectedCommunity = mockCommunities.find((c) => c.id === selected);
  const needsCode = selectedCommunity?.requires_code;

  function handleSelect(c: MockCommunity) {
    setSelected(c.id);
    if (!c.requires_code) {
      router.push({ pathname: '/community/verify', params: { communityId: c.id, communityName: c.name } });
    }
  }

  return (
    <Screen title="Choose your community" subtitle="Your neighbourhood in Digital Mohalla">
      <BackButton />
      <Field icon="search" value={query} onChangeText={setQuery} placeholder="Search by name or sector" />

      {filtered.length === 0 ? (
        <EmptyState
          icon="location_off"
          title="No communities found"
          body="Try a different sector or city name."
        />
      ) : (
        filtered.map((c) => (
          <CommunityCard
            key={c.id}
            community={c}
            selected={selected === c.id}
            onSelect={() => handleSelect(c)}
          />
        ))
      )}

      {/* Invite code — only shown when needed (progressive disclosure) */}
      {needsCode ? (
        <View style={{ gap: 6 }}>
          <SectionLabel>Invitation code</SectionLabel>
          <Body muted style={{ fontSize: 13 }}>
            This community requires a 6-character code from an existing member.
          </Body>
          <Field
            label="Invitation code"
            value={code}
            onChangeText={(t) => setCode(t.toUpperCase().slice(0, 6))}
            placeholder="e.g. INV-XYZ"
          />
        </View>
      ) : null}

      <Button
        label="Select & continue to verification"
        icon="arrow_forward"
        disabled={!selected || (needsCode ? code.length < 3 : false)}
        onPress={() => router.push('/community/verify')}
      />
    </Screen>
  );
}

