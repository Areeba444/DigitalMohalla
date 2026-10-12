/**
 * Three candidate themes for the team to compare.
 *
 * - terracotta: from docs/design/Digital-MohallaUI/.../styles/design-system.css
 * - nordic:     from .../styles/theme-nordic.css (slate navy, sky blue, brick, sage)
 * - midnight:   dark navy and teal from the wireframe prompts in UI_Generation_Guide
 *
 * Assurance states describe the evidence, not the person. INSUFFICIENT_EVIDENCE is deliberately
 * never red in any theme (HCI constraint 2); red is reserved for an active dispute.
 */

export type Tone = { fg: string; bg: string; border: string };

export type Theme = {
  name: string;
  label: string;
  dark: boolean;
  colors: {
    bg: string;
    surface: string;
    surface2: string;
    text: string;
    textSecondary: string;
    textMuted: string;
    border: string;
    primary: string;
    onPrimary: string;
    accent: string;
    success: Tone;
    warning: Tone;
    danger: Tone;
    info: Tone;
    neutral: Tone;
  };
  state: {
    SUFFICIENT_EVIDENCE: Tone;
    REVIEW_RECOMMENDED: Tone;
    INSUFFICIENT_EVIDENCE: Tone;
    ACTIVE_DISPUTE: Tone;
  };
  radius: { sm: number; md: number; lg: number; pill: number };
  fontDisplay: string;
  fontBody: string;
};

const tone = (fg: string, bg: string, border: string): Tone => ({ fg, bg, border });
const system = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';

export const terracotta: Theme = {
  name: 'terracotta',
  label: 'Terracotta',
  dark: false,
  colors: {
    bg: '#FAF7F2',
    surface: '#FFFFFF',
    surface2: '#F8F4EE',
    text: '#1C1917',
    textSecondary: '#57534E',
    textMuted: '#8C857D',
    border: '#E6D9CC',
    primary: '#C2673B',
    onPrimary: '#FFFFFF',
    accent: '#2D5A46',
    success: tone('#2D5A46', '#EDF6F1', '#BCE0CE'),
    warning: tone('#B45309', '#FEF9ED', '#FDE68A'),
    danger: tone('#DC2626', '#FEF2F2', '#FECACA'),
    info: tone('#475569', '#F1F5F9', '#CBD5E1'),
    neutral: tone('#57534E', '#F4EFE7', '#D9C9B8'),
  },
  state: {
    SUFFICIENT_EVIDENCE: tone('#2D5A46', '#EDF6F1', '#BCE0CE'),
    REVIEW_RECOMMENDED: tone('#C2673B', '#FDF5EF', '#F3CBB5'),
    INSUFFICIENT_EVIDENCE: tone('#475569', '#F1F5F9', '#CBD5E1'),
    ACTIVE_DISPUTE: tone('#DC2626', '#FEF2F2', '#FECACA'),
  },
  radius: { sm: 10, md: 16, lg: 22, pill: 9999 },
  fontDisplay: 'Fraunces, Georgia, "Times New Roman", serif',
  fontBody: system,
};

export const nordic: Theme = {
  name: 'nordic',
  label: 'Nordic',
  dark: false,
  colors: {
    bg: '#F6F3E9',
    surface: '#FFFFFF',
    surface2: '#F3EFE3',
    text: '#1A2833',
    textSecondary: '#506373',
    textMuted: '#8294A2',
    border: '#DDD8C6',
    primary: '#243644',
    onPrimary: '#FFFFFF',
    accent: '#CB6045',
    success: tone('#5C8244', '#EDF5E8', '#C8DEB9'),
    warning: tone('#B4691B', '#FDF6E6', '#F2DCA8'),
    danger: tone('#B3261E', '#FDF1EE', '#F4C6BC'),
    info: tone('#3B9FB8', '#E6F5F9', '#BCE2EB'),
    neutral: tone('#506373', '#F3EFE3', '#DDD8C6'),
  },
  state: {
    SUFFICIENT_EVIDENCE: tone('#5C8244', '#EDF5E8', '#C8DEB9'),
    REVIEW_RECOMMENDED: tone('#CB6045', '#FDF1EE', '#F4C6BC'),
    INSUFFICIENT_EVIDENCE: tone('#3B7C91', '#E6F5F9', '#BCE2EB'),
    ACTIVE_DISPUTE: tone('#B3261E', '#FCEDEC', '#F2B8B5'),
  },
  radius: { sm: 10, md: 14, lg: 20, pill: 9999 },
  fontDisplay: system,
  fontBody: system,
};

export const midnight: Theme = {
  name: 'midnight',
  label: 'Midnight',
  dark: true,
  colors: {
    bg: '#0F172A',
    surface: '#1E293B',
    surface2: '#162033',
    text: '#E2E8F0',
    textSecondary: '#A9B6C8',
    textMuted: '#7B8BA1',
    border: '#2B3A52',
    primary: '#14B8A6',
    onPrimary: '#062C28',
    accent: '#14B8A6',
    success: tone('#34D399', '#0F2A24', '#1F5A48'),
    warning: tone('#FBBF24', '#2B2210', '#5C4A17'),
    danger: tone('#F87171', '#2D1618', '#6B2A2E'),
    info: tone('#7DD3FC', '#0F2234', '#1E4A6B'),
    neutral: tone('#A9B6C8', '#1A2538', '#2B3A52'),
  },
  state: {
    SUFFICIENT_EVIDENCE: tone('#34D399', '#0F2A24', '#1F5A48'),
    REVIEW_RECOMMENDED: tone('#FBBF24', '#2B2210', '#5C4A17'),
    INSUFFICIENT_EVIDENCE: tone('#FBBF24', '#2B2210', '#5C4A17'),
    ACTIVE_DISPUTE: tone('#F87171', '#2D1618', '#6B2A2E'),
  },
  radius: { sm: 10, md: 14, lg: 20, pill: 9999 },
  fontDisplay: system,
  fontBody: system,
};

export const themes: Theme[] = [terracotta, nordic, midnight];
