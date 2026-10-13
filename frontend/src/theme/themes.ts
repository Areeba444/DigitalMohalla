/**
 * The two app themes, each built around one image:
 *
 * - terracotta:  the sunset aerial view of a Pakistani neighbourhood (assets/images/themes/terracotta.jpg).
 *                Warm clay primary, forest-green accent, Fraunces serif headlines (team design system).
 * - creamGreen:  the illustrated houses under a sky (assets/images/themes/cream-green.jpg).
 *                Cream paper, sage/moss primary, slate text, sky accent, Plus Jakarta Sans headlines.
 *
 * Assurance states describe the evidence, not the person. INSUFFICIENT_EVIDENCE is a neutral blue-grey in
 * both themes and never red or a warning colour (HCI analysis, constraint 2); red is reserved for an open
 * dispute.
 */
import type { ImageSourcePropType } from 'react-native';

export type Tone = { fg: string; bg: string; border: string };

export type Fonts = {
  display: string; // large headlines
  displayAlt: string; // hero titles
  regular: string;
  medium: string;
  semibold: string;
  bold: string;
  black: string;
};

export type Theme = {
  name: string;
  label: string;
  tagline: string;
  colors: {
    bg: string;
    surface: string;
    surface2: string;
    glass: string;
    text: string;
    textSecondary: string;
    textMuted: string;
    border: string;
    hairline: string;
    primary: string;
    primaryDeep: string;
    primarySoft: string;
    onPrimary: string;
    accent: string;
    accentSoft: string;
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
  hero: {
    image: ImageSourcePropType;
    /** CSS gradient laid over the image so text on it stays readable. */
    scrim: string;
    /** Text colours on the hero, after the scrim. */
    text: string;
    textSoft: string;
    /** Gradient for the primary button. */
    button: string;
    /** Status-bar text over the hero image. */
    statusBar: 'light' | 'dark';
    /** Which part of the image stays in view when it is cropped. */
    position: 'top' | 'center';
  };
  shadow: { card: string; float: string };
  radius: { sm: number; md: number; lg: number; xl: number; pill: number };
  fonts: Fonts;
};

const tone = (fg: string, bg: string, border: string): Tone => ({ fg, bg, border });

const jakarta = {
  regular: 'PlusJakartaSans_400Regular',
  medium: 'PlusJakartaSans_500Medium',
  semibold: 'PlusJakartaSans_600SemiBold',
  bold: 'PlusJakartaSans_700Bold',
  black: 'PlusJakartaSans_800ExtraBold',
};

export const terracotta: Theme = {
  name: 'terracotta',
  label: 'Terracotta',
  tagline: 'Warm evenings, trusted neighbours',
  colors: {
    bg: '#FAF6F0',
    surface: '#FFFFFF',
    surface2: '#F6EFE6',
    glass: 'rgba(255, 250, 244, 0.80)',
    text: '#1F1A17',
    textSecondary: '#5A524C',
    textMuted: '#857C73',
    border: '#EADCCD',
    hairline: 'rgba(31, 26, 23, 0.08)',
    primary: '#C2673B',
    primaryDeep: '#9E4F28',
    primarySoft: '#FBEDE3',
    onPrimary: '#FFFFFF',
    accent: '#2D5A46',
    accentSoft: '#E6F1EB',
    success: tone('#2D5A46', '#EDF6F1', '#BCE0CE'),
    warning: tone('#A65A0B', '#FEF6E7', '#F5D9A8'),
    danger: tone('#C2261F', '#FEF1F0', '#F7C6C2'),
    info: tone('#475569', '#F1F5F9', '#CBD5E1'),
    neutral: tone('#5A524C', '#F4EDE4', '#DCCBB8'),
  },
  state: {
    SUFFICIENT_EVIDENCE: tone('#2D5A46', '#EDF6F1', '#BCE0CE'),
    REVIEW_RECOMMENDED: tone('#A65A0B', '#FEF6E7', '#F5D9A8'),
    INSUFFICIENT_EVIDENCE: tone('#475569', '#F1F5F9', '#CBD5E1'),
    ACTIVE_DISPUTE: tone('#C2261F', '#FEF1F0', '#F7C6C2'),
  },
  hero: {
    image: require('../../assets/images/themes/terracotta.jpg'),
    scrim:
      'linear-gradient(180deg, rgba(30, 16, 8, 0.12) 0%, rgba(30, 16, 8, 0.28) 40%, rgba(46, 22, 10, 0.90) 100%)',
    text: '#FFF8F1',
    textSoft: 'rgba(255, 244, 232, 0.88)',
    button: 'linear-gradient(135deg, #D27A4C 0%, #C2673B 45%, #A9542D 100%)',
    statusBar: 'light',
    position: 'top',
  },
  shadow: {
    card: '0px 6px 20px rgba(120, 66, 34, 0.08)',
    float: '0px 14px 36px rgba(90, 44, 18, 0.22)',
  },
  radius: { sm: 12, md: 18, lg: 26, xl: 32, pill: 9999 },
  fonts: { display: 'Fraunces_600SemiBold', displayAlt: 'Fraunces_700Bold', ...jakarta },
};

export const creamGreen: Theme = {
  name: 'cream-green',
  label: 'Cream Green',
  tagline: 'Leafy lanes, shared things',
  colors: {
    bg: '#F5F1E4',
    surface: '#FFFDF7',
    surface2: '#EFEADA',
    glass: 'rgba(255, 253, 247, 0.82)',
    text: '#1E2B33',
    textSecondary: '#4E5F6B',
    textMuted: '#76858F',
    border: '#E1DAC4',
    hairline: 'rgba(30, 43, 51, 0.08)',
    primary: '#4F7A3A',
    primaryDeep: '#3B5E2B',
    primarySoft: '#E7F0DE',
    onPrimary: '#FFFFFF',
    accent: '#2F8AA3',
    accentSoft: '#E2F2F6',
    success: tone('#4F7A3A', '#EAF3E2', '#C6DDB5'),
    warning: tone('#9A6412', '#FBF3E1', '#EBD39E'),
    danger: tone('#B3261E', '#FCEDEC', '#F2B8B5'),
    info: tone('#3E6A86', '#E8F1F6', '#C3D8E5'),
    neutral: tone('#4E5F6B', '#EFEADA', '#D9D1BA'),
  },
  state: {
    SUFFICIENT_EVIDENCE: tone('#4F7A3A', '#EAF3E2', '#C6DDB5'),
    REVIEW_RECOMMENDED: tone('#9A6412', '#FBF3E1', '#EBD39E'),
    INSUFFICIENT_EVIDENCE: tone('#3E6A86', '#E8F1F6', '#C3D8E5'),
    ACTIVE_DISPUTE: tone('#B3261E', '#FCEDEC', '#F2B8B5'),
  },
  hero: {
    image: require('../../assets/images/themes/cream-green.jpg'),
    scrim:
      'linear-gradient(180deg, rgba(245, 241, 228, 0) 0%, rgba(245, 241, 228, 0) 28%, rgba(245, 241, 228, 0.90) 50%, #F5F1E4 64%)',
    text: '#1E2B33',
    textSoft: '#4E5F6B',
    button: 'linear-gradient(135deg, #5F8E46 0%, #4F7A3A 50%, #3F6530 100%)',
    statusBar: 'dark',
    position: 'center',
  },
  shadow: {
    card: '0px 6px 20px rgba(36, 54, 68, 0.07)',
    float: '0px 14px 36px rgba(36, 54, 68, 0.18)',
  },
  radius: { sm: 12, md: 18, lg: 26, xl: 32, pill: 9999 },
  fonts: {
    display: 'PlusJakartaSans_800ExtraBold',
    displayAlt: 'PlusJakartaSans_800ExtraBold',
    ...jakarta,
  },
};

export const themes: Theme[] = [terracotta, creamGreen];
