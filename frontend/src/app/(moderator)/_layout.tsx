import { Stack } from 'expo-router';

/** Moderator screens (W6, W7). The API decides who may see each case; nothing is hidden only here. */
export default function ModeratorLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
