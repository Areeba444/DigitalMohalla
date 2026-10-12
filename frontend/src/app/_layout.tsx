import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { useState } from 'react';

import { AuthProvider, useAuth } from '@/auth/AuthProvider';
import { Loading } from '@/components/ui';
import { ThemeProvider } from '@/theme/ThemeProvider';

function Routes() {
  const { ready, signedIn } = useAuth();
  if (!ready) return <Loading />;
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={signedIn}>
        <Stack.Screen name="(resident)" />
      </Stack.Protected>
      <Stack.Protected guard={!signedIn}>
        <Stack.Screen name="login" />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 5_000 } } }),
  );
  return (
    <QueryClientProvider client={client}>
      <ThemeProvider>
        <AuthProvider>
          <Routes />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
