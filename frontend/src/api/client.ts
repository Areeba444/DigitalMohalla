/** Typed API client generated from the backend's OpenAPI spec (`npm run api:generate`). */
import createClient from 'openapi-fetch';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import type { paths } from './schema';

export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const TOKEN_KEY = 'dm-token';
const USER_KEY = 'dm-user';

export type StoredUser = { email?: string; name?: string };

// Login token: session storage on web (cleared when the tab closes), secure store on Android.
let memoryToken: string | null = null;
let memoryUser: StoredUser | null = null;

export async function loadUser(): Promise<StoredUser | null> {
  try {
    const raw =
      Platform.OS === 'web'
        ? window.sessionStorage.getItem(USER_KEY)
        : await SecureStore.getItemAsync(USER_KEY);
    memoryUser = raw ? JSON.parse(raw) : null;
  } catch {
    memoryUser = null;
  }
  return memoryUser;
}

export async function saveUser(user: StoredUser | null): Promise<void> {
  memoryUser = user;
  try {
    const raw = user ? JSON.stringify(user) : null;
    if (Platform.OS === 'web') {
      if (raw) window.sessionStorage.setItem(USER_KEY, raw);
      else window.sessionStorage.removeItem(USER_KEY);
    } else if (raw) await SecureStore.setItemAsync(USER_KEY, raw);
    else await SecureStore.deleteItemAsync(USER_KEY);
  } catch {
    /* ignore */
  }
}

export async function loadToken(): Promise<string | null> {
  try {
    memoryToken =
      Platform.OS === 'web'
        ? window.sessionStorage.getItem(TOKEN_KEY)
        : await SecureStore.getItemAsync(TOKEN_KEY);
  } catch {
    memoryToken = null;
  }
  return memoryToken;
}

export async function saveToken(token: string | null): Promise<void> {
  memoryToken = token;
  try {
    if (Platform.OS === 'web') {
      if (token) window.sessionStorage.setItem(TOKEN_KEY, token);
      else window.sessionStorage.removeItem(TOKEN_KEY);
    } else if (token) await SecureStore.setItemAsync(TOKEN_KEY, token);
    else await SecureStore.deleteItemAsync(TOKEN_KEY);
  } catch {
    /* the in-memory token still works for this session */
  }
}

export const api = createClient<paths>({ baseUrl: API_URL });

api.use({
  onRequest({ request }) {
    if (memoryToken) request.headers.set('Authorization', `Bearer ${memoryToken}`);
    return request;
  },
});

/** Turns an openapi-fetch error body into a readable message. */
export function errorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((d) => d?.msg ?? String(d)).join('; ');
  }
  return 'Something went wrong. Please try again.';
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

/** Unwraps `{ data, error, response }` from openapi-fetch, throwing ApiError on failure. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || result.data === undefined) {
    throw new ApiError(result.response.status, errorMessage(result.error));
  }
  return result.data;
}
