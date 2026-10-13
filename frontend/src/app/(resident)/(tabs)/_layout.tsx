import { Slot } from 'expo-router';
import { View } from 'react-native';

import { useMyRequests } from '@/api/hooks';
import { TabBar } from '@/components/TabBar';
import { needsYou } from '@/lib/requests';

export default function TabsLayout() {
  const { data } = useMyRequests();
  const waiting = (data ?? []).filter(needsYou).length;
  return (
    <View style={{ flex: 1 }}>
      <Slot />
      <TabBar badge={waiting || undefined} />
    </View>
  );
}
