/**
 * The four app themes, each built around one image:
 *
 * - terracotta:    the sunset aerial view of a Pakistani neighbourhood (assets/images/themes/terracotta.jpg).
 *                  Warm clay primary, forest-green accent, Fraunces serif headlines (team design system).
 * - creamGreen:    the illustrated houses under a sky (assets/images/themes/cream-green.jpg).
 *                  Cream paper, sage/moss primary, slate text, sky accent, Plus Jakarta Sans headlines.
 * - alpineMeadow:  mountain goat on alpine rocks (assets/images/themes/option3.jpeg).
 *                  Off-white base, olive-green primary, steel-blue accent, mauve secondary.
 * - highPeak:      panoramic mountain ridge (assets/images/themes/option4.jpeg).
 *                  Light lavender base, slate-blue primary, rust/burgundy accent, sage secondary.
 *
 * ─── HOW TO EXPERIMENT WITH COLORS ──────────────────────────────────────────
 * Edit the hex values directly in the `colors` block of any theme below.
 * The key roles are:
 *   bg            → page / screen background
 *   surface       → card / sheet background
 *   surface2      → input / chip / subtle container background
 *   primary       → buttons, active tab, links, icons
 *   primaryDeep   → pressed / hover shade of primary
 *   primarySoft   → faint primary tint (avatar bg, selected chip)
 *   onPrimary     → text / icon colour ON a filled primary button
 *   accent        → secondary highlights, promise icons, info
 *   accentSoft    → faint accent tint
 *   text          → body copy
 *   textSecondary → captions, metadata
 *   textMuted     → placeholders, disabled
 *   border        → card outlines, dividers
 *   hairline      → 1 px separator lines (semi-transparent)
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Assurance states describe the evidence, not the person. INSUFFICIENT_EVIDENCE is a neutral blue-grey in
 * all themes and never red or a warning colour (HCI analysis, constraint 2); red is reserved for an open
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

// ─── Theme 3: Alpine Meadow ──────────────────────────────────────────────────
// Inspired by the mountain-goat palette (option3.jpeg):
//   Off-white base  · Olive green primary  · Steel blue accent  · Mauve secondary
// ─────────────────────────────────────────────────────────────────────────────
export const alpineMeadow: Theme = {
  name: 'alpine-meadow',
  label: 'Alpine Meadow',
  tagline: 'Fresh heights, grounded roots',
  colors: {
    // ── Backgrounds ──────────────────────────────────────────────────────────
    bg: '#F4F1EC',           // warm off-white  (matches palette chip 1)
    surface: '#FDFCF9',      // near-white card surface
    surface2: '#EAE6DE',     // subtle warm grey for inputs / chips
    glass: 'rgba(253, 252, 249, 0.82)',
    // ── Text ─────────────────────────────────────────────────────────────────
    text: '#1C1E1A',         // near-black with green undertone
    textSecondary: '#50584C',
    textMuted: '#7F8A78',
    // ── Borders ──────────────────────────────────────────────────────────────
    border: '#D8D3C8',
    hairline: 'rgba(28, 30, 26, 0.08)',
    // ── Primary — olive green (palette chip 2: #8A9E4E approx) ───────────────
    primary: '#7A9140',      // deep olive — CTA buttons, active tab
    primaryDeep: '#5F7030',  // pressed / darker shade
    primarySoft: '#E8EDD8',  // faint tint — avatar bg, selected chip
    onPrimary: '#FFFFFF',
    // ── Accent — steel / muted teal-blue (palette chip 3) ────────────────────
    accent: '#4A7E96',       // steel blue — icons, links, info
    accentSoft: '#DDF0F5',
    // ── Semantic tones ───────────────────────────────────────────────────────
    success: tone('#5C8C3E', '#E8F4E0', '#BFD9A8'),
    warning: tone('#9A6B10', '#FBF3E0', '#EAD39C'),
    danger:  tone('#A8322C', '#FCEDEC', '#F2B8B5'),
    info:    tone('#4A7E96', '#E0EFF5', '#B8D6E5'),
    neutral: tone('#50584C', '#EAE6DE', '#CFC9BC'),
  },
  state: {
    SUFFICIENT_EVIDENCE:   tone('#5C8C3E', '#E8F4E0', '#BFD9A8'),
    REVIEW_RECOMMENDED:    tone('#9A6B10', '#FBF3E0', '#EAD39C'),
    INSUFFICIENT_EVIDENCE: tone('#4A7E96', '#E0EFF5', '#B8D6E5'),
    ACTIVE_DISPUTE:        tone('#A8322C', '#FCEDEC', '#F2B8B5'),
  },
  hero: {
    image: require('../../assets/images/themes/option3.jpeg'),
    scrim:
      'linear-gradient(180deg, rgba(20,24,18,0.10) 0%, rgba(20,24,18,0.26) 40%, rgba(20,24,18,0.88) 100%)',
    text: '#F8F6F0',
    textSoft: 'rgba(240, 238, 230, 0.88)',
    button: 'linear-gradient(135deg, #96AA52 0%, #7A9140 50%, #60741E 100%)',
    statusBar: 'light',
    position: 'top',
  },
  shadow: {
    card:  '0px 6px 20px rgba(40, 54, 24, 0.08)',
    float: '0px 14px 36px rgba(40, 54, 24, 0.20)',
  },
  radius: { sm: 12, md: 18, lg: 26, xl: 32, pill: 9999 },
  fonts: {
    display: 'PlusJakartaSans_800ExtraBold',
    displayAlt: 'PlusJakartaSans_800ExtraBold',
    ...jakarta,
  },
};

// ─── Theme 4: High Peak ──────────────────────────────────────────────────────
// Inspired by the panoramic mountain ridge palette (option4.jpeg):
//   Lavender-grey base  · Slate-blue primary  · Rust/burgundy accent  · Sage secondary
// ─────────────────────────────────────────────────────────────────────────────
export const highPeak: Theme = {
  name: 'high-peak',
  label: 'High Peak',
  tagline: 'Bold summits, steady paths',
  colors: {
    // ── Backgrounds ──────────────────────────────────────────────────────────
    bg: '#EDEEF4',           // soft lavender-grey (palette chip 5)
    surface: '#F7F8FC',      // near-white with cool tint
    surface2: '#E0E2EC',     // muted blue-grey for inputs / chips
    glass: 'rgba(247, 248, 252, 0.84)',
    // ── Text ─────────────────────────────────────────────────────────────────
    text: '#1A1C28',         // deep blue-black
    textSecondary: '#4A4E6A',
    textMuted: '#7A7F9A',
    // ── Borders ──────────────────────────────────────────────────────────────
    border: '#CBCEDC',
    hairline: 'rgba(26, 28, 40, 0.09)',
    // ── Primary — slate blue (palette chip 1: #4A5696 approx) ────────────────
    primary: '#4A5696',      // slate blue — CTA buttons, active tab
    primaryDeep: '#363E78',  // pressed / darker shade
    primarySoft: '#DDE0F2',  // faint tint — avatar bg, selected chip
    onPrimary: '#FFFFFF',
    // ── Accent — rust / burgundy (palette chip 3: #883038 approx) ────────────
    accent: '#8B3038',       // warm rust-red — highlights, links
    accentSoft: '#F5E0E2',
    // ── Semantic tones ───────────────────────────────────────────────────────
    success: tone('#4A7A44', '#E4F2E2', '#B8D9B4'),
    warning: tone('#8A6010', '#F9F0DC', '#E6CC96'),
    danger:  tone('#8B3038', '#FCEDEE', '#F2B8BC'),
    info:    tone('#4A5696', '#DDE0F2', '#B4BAE0'),
    neutral: tone('#4A4E6A', '#E0E2EC', '#C2C6D8'),
  },
  state: {
    SUFFICIENT_EVIDENCE:   tone('#4A7A44', '#E4F2E2', '#B8D9B4'),
    REVIEW_RECOMMENDED:    tone('#8A6010', '#F9F0DC', '#E6CC96'),
    INSUFFICIENT_EVIDENCE: tone('#4A5696', '#DDE0F2', '#B4BAE0'),
    ACTIVE_DISPUTE:        tone('#8B3038', '#FCEDEE', '#F2B8BC'),
  },
  hero: {
    image: require('../../assets/images/themes/option4.jpeg'),
    scrim:
      'linear-gradient(180deg, rgba(26,28,40,0.08) 0%, rgba(26,28,40,0.24) 40%, rgba(26,28,40,0.90) 100%)',
    text: '#F4F5FA',
    textSoft: 'rgba(234, 236, 248, 0.88)',
    button: 'linear-gradient(135deg, #5A69AE 0%, #4A5696 50%, #363E78 100%)',
    statusBar: 'light',
    position: 'center',
  },
  shadow: {
    card:  '0px 6px 20px rgba(26, 28, 72, 0.09)',
    float: '0px 14px 36px rgba(26, 28, 72, 0.22)',
  },
  radius: { sm: 12, md: 18, lg: 26, xl: 32, pill: 9999 },
  fonts: {
    display: 'PlusJakartaSans_800ExtraBold',
    displayAlt: 'PlusJakartaSans_800ExtraBold',
    ...jakarta,
  },
};

export const themes: Theme[] = [terracotta, creamGreen, alpineMeadow, highPeak];
