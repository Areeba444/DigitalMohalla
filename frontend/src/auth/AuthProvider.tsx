import { useQueryClient } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { loadToken, saveToken } from '@/api/client';
import { useLogin } from '@/api/hooks';

type Auth = {
  ready: boolean;
  signedIn: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<Auth>({
  ready: false,
  signedIn: false,
  signIn: async () => {},
  signOut: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const login = useLogin();
  const qc = useQueryClient();

  useEffect(() => {
    loadToken().then((token) => {
      setSignedIn(!!token);
      setReady(true);
    });
  }, []);

  const signIn = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await login.mutateAsync({ email, password });
      await saveToken(access_token);
      qc.clear(); // never show the previous user's data
      setSignedIn(true);
    },
    [login, qc],
  );

  const signOut = useCallback(async () => {
    await saveToken(null);
    qc.clear();
    setSignedIn(false);
  }, [qc]);

  const value = useMemo(
    () => ({ ready, signedIn, signIn, signOut }),
    [ready, signedIn, signIn, signOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
