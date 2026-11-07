/**
 * W12 — Notification Center (FR-G-03, Module 7)
 *
 * HCI notes:
 * - Categorized tabs: All / Action Required / Updates.
 * - Unread indicator = tinted background + dot (never colour alone).
 * - Every notification with a deep link shows a "View" action — 1 tap to context.
 * - Empty state is warm and positive, never a blank screen.
 */
import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, View } from 'react-native';

import { Chip, EmptyState, InboxRow, Screen } from '@/components/ui';
import { mockNotifications } from '@/api/mocks/iteration2Mocks';
import type { IconName } from '@/components/ui';

const TABS = [
  { key: 'ALL', label: 'All' },
  { key: 'ACTION', label: 'Action required' },
  { key: 'UPDATE', label: 'Updates' },
] as const;

type Tab = (typeof TABS)[number]['key'];

export default function Notifications() {
  const [tab, setTab] = useState<Tab>('ALL');

  const shown = mockNotifications.filter((n) => {
    if (tab === 'ACTION') return n.type === 'ACTION';
    if (tab === 'UPDATE') return n.type === 'UPDATE' || n.type === 'SYSTEM';
    return true;
  });

  const unreadCount = mockNotifications.filter((n) => n.unread).length;

  return (
    <Screen
      title="Notifications"
      subtitle={unreadCount > 0 ? `${unreadCount} unread` : 'All caught up'}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ marginHorizontal: -16 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
        {TABS.map((t) => (
          <Chip key={t.key} label={t.label} selected={tab === t.key} onPress={() => setTab(t.key)} />
        ))}
      </ScrollView>

      {shown.length === 0 ? (
        <EmptyState
          icon="notifications_none"
          title="All caught up"
          body="New notifications will appear here when something needs your attention."
        />
      ) : (
        <View style={{ marginHorizontal: -16 }}>
          {shown.map((n) => (
            <InboxRow
              key={n.id}
              icon={n.icon as IconName}
              title={n.title}
              body={n.body}
              timestamp={n.timestamp}
              unread={n.unread}
              onPress={n.deep_link ? () => router.push(n.deep_link as any) : undefined}
            />
          ))}
        </View>
      )}
    </Screen>
  );
}

