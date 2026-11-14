import { useQueryClient } from '@tanstack/react-query';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { loadToken, loadUser, saveToken, saveUser, type StoredUser } from '@/api/client';
import { useLogin } from '@/api/hooks';

type Auth = {
  ready: boolean;
  signedIn: boolean;
  user: StoredUser | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<Auth>({
  ready: false,
  signedIn: false,
  user: null,
  signIn: async () => {},
  signOut: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [user, setUser] = useState<StoredUser | null>(null);
  const login = useLogin();
  const qc = useQueryClient();

  useEffect(() => {
    Promise.all([loadToken(), loadUser()]).then(([token, u]) => {
      setSignedIn(!!token);
      setUser(u);
      setReady(true);
    });
  }, []);

  const signIn = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await login.mutateAsync({ email, password });
      await saveToken(access_token);
      // Determine display name: match synthetic test users or fallback to email local-part
      const em = email.toLowerCase().trim();
      const name =
        em.includes('lender')
          ? 'Ayesha (lender)'
          : em.includes('borrower2')
            ? 'Chand (borrower)'
            : em.includes('borrower')
              ? 'Bilal (borrower)'
              : em.includes('moderator')
                ? 'Dua (moderator)'
                : em.includes('admin')
                  ? 'Admin'
                  : em.split('@')[0];
      const stored = { email: em, name };
      await saveUser(stored);
      setUser(stored);
      qc.clear(); // never show the previous user's data
      setSignedIn(true);
    },
    [login, qc],
  );

  const signOut = useCallback(async () => {
    await saveToken(null);
    await saveUser(null);
    setUser(null);
    qc.clear();
    setSignedIn(false);
  }, [qc]);

  const value = useMemo(
    () => ({ ready, signedIn, user, signIn, signOut }),
    [ready, signedIn, user, signIn, signOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
