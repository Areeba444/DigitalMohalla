import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { Platform } from 'react-native';

import { themes, terracotta, type Theme } from './themes';

const STORAGE_KEY = 'dm-theme';

type Ctx = { theme: Theme; themes: Theme[]; setTheme: (name: string) => void };
const ThemeContext = createContext<Ctx>({ theme: terracotta, themes, setTheme: () => {} });

// Per-viewer convenience only: remembered on web, ignored if storage is unavailable.
function readSaved(): string | null {
  try {
    return Platform.OS === 'web' ? window.localStorage.getItem(STORAGE_KEY) : null;
  } catch {
    return null;
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [name, setName] = useState('terracotta');

  useEffect(() => {
    const saved = readSaved();
    // The web build is pre-rendered (app.json web.output = "static"), so storage is read after the first
    // render; reading it in useState would make the browser's first render differ from the pre-rendered page.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (saved && themes.some((t) => t.name === saved)) setName(saved);
  }, []);

  const setTheme = useCallback((next: string) => {
    setName(next);
    try {
      if (Platform.OS === 'web') window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* storage blocked: the choice just lasts for this visit */
    }
  }, []);

  const value = useMemo(
    () => ({ theme: themes.find((t) => t.name === name) ?? terracotta, themes, setTheme }),
    [name, setTheme],
  );
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
