/**
 * The four app themes, each built around one image:
 *
 * - terracotta:    the sunset aerial view of a Pakistani neighbourhood (assets/images/themes/terracotta.jpg).
 *                  Warm clay primary, forest-green accent, Fraunces serif headlines (team design system).
 * - creamGreen:    the illustrated houses under a sky (assets/images/themes/cream-green.jpg).
 *                  Cream paper, sage/moss primary, slate text, sky accent, Plus Jakarta Sans headlines.
 * - stonyBlue:     mountain goat on alpine rocks (assets/images/themes/option3.jpeg).
 *                  Warm cream base, steel-blue primary (#608FA3), dusty-plum accent (#895377).
 * - ridgeline:     panoramic mountain ridge (assets/images/themes/option4.jpeg).
 *                  Soft lavender base, indigo-slate primary (#536299), deep-rust accent (#7C3539).
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

// ─── Theme 3: Stony Blue ─────────────────────────────────────────────────────
// Exact palette from option3.jpeg:
//   #EFE9E7 warm cream  ·  #BCCC83 lime-sage  ·  #608FA3 steel-blue
//   #895377 dusty plum  ·  #55565B charcoal
//
// Design rationale:
//   Primary  → #608FA3 steel-blue   — calm, trustworthy, great WCAG contrast on cream
//   Accent   → #895377 dusty plum   — warm complement to blue, used for highlights
//   BG       → #EFE9E7 warm cream   — the lightest chip, airy and clean
//   #BCCC83 (lime-sage) → reserved for success / positive states only
//   #55565B  → body text
// ─────────────────────────────────────────────────────────────────────────────
export const stonyBlue: Theme = {
  name: 'stony-blue',
  label: 'Stony Blue',
  tagline: 'Still waters, sure footing',
  colors: {
    // ── Backgrounds ──────────────────────────────────────────────────────────
    bg:       '#EFE9E7',              // exact palette chip 1 — warm cream
    surface:  '#FDFAF9',             // lightest card white with warm cast
    surface2: '#E4DDD9',             // slightly deeper cream for inputs/chips
    glass:    'rgba(253,250,249,0.82)',
    // ── Text ─────────────────────────────────────────────────────────────────
    text:          '#2A2B2F',        // deeper than #55565B — crisp on cream bg
    textSecondary: '#55565B',        // exact palette chip 5
    textMuted:     '#8E9094',        // lightened charcoal for placeholders
    // ── Borders ──────────────────────────────────────────────────────────────
    border:   '#D5CEC9',
    hairline: 'rgba(42,43,47,0.08)',
    // ── Primary — steel blue ─────────────────────────────────────────────────
    primary:     '#608FA3',          // exact palette chip 3
    primaryDeep: '#477284',          // 15 % darker — pressed state
    primarySoft: '#DFF0F6',          // very light blue tint — avatar bg, chips
    onPrimary:   '#FFFFFF',
    // ── Accent — dusty plum ──────────────────────────────────────────────────
    accent:     '#895377',           // exact palette chip 4
    accentSoft: '#F3E8F0',           // faint plum tint
    // ── Semantic tones ───────────────────────────────────────────────────────
    // success reuses lime-sage (#BCCC83) — the only right spot for it
    success: tone('#5C7A30', '#EDF3DC', '#BCCC83'),
    warning: tone('#8A6010', '#FBF3E0', '#EAD39C'),
    danger:  tone('#A0302A', '#FCEDEC', '#F2B8B5'),
    info:    tone('#608FA3', '#DFF0F6', '#AED2E0'),
    neutral: tone('#55565B', '#E4DDD9', '#CFC6C0'),
  },
  state: {
    SUFFICIENT_EVIDENCE:   tone('#5C7A30', '#EDF3DC', '#BCCC83'),
    REVIEW_RECOMMENDED:    tone('#8A6010', '#FBF3E0', '#EAD39C'),
    INSUFFICIENT_EVIDENCE: tone('#608FA3', '#DFF0F6', '#AED2E0'),
    ACTIVE_DISPUTE:        tone('#A0302A', '#FCEDEC', '#F2B8B5'),
  },
  hero: {
    image: require('../../assets/images/themes/option3.jpeg'),
    // Dark-blue scrim matches the steel-blue primary family
    scrim:
      'linear-gradient(180deg, rgba(22,38,52,0.08) 0%, rgba(22,38,52,0.28) 45%, rgba(22,38,52,0.92) 100%)',
    text:     '#F5F0EE',
    textSoft: 'rgba(240,232,228,0.88)',
    // Gradient runs from a lighter tint of primary to primaryDeep
    button:   'linear-gradient(135deg, #72A4BA 0%, #608FA3 50%, #477284 100%)',
    statusBar: 'light',
    position:  'top',
  },
  shadow: {
    card:  '0px 6px 20px rgba(96,143,163,0.12)',
    float: '0px 14px 36px rgba(96,143,163,0.24)',
  },
  radius: { sm: 12, md: 18, lg: 26, xl: 32, pill: 9999 },
  fonts: {
    display:    'PlusJakartaSans_800ExtraBold',
    displayAlt: 'PlusJakartaSans_800ExtraBold',
    ...jakarta,
  },
};

// ─── Theme 4: Ridgeline ───────────────────────────────────────────────────────
// Exact palette from option4.jpeg:
//   #536299 indigo-slate  ·  #6D6F61 army-olive  ·  #7C3539 deep rust
//   #73708D muted lavender  ·  #C5C4D4 soft lavender
//
// Design rationale:
//   Primary  → #536299 indigo-slate  — rich, modern, high contrast against lavender bg
//   Accent   → #7C3539 deep rust     — warm-cool split-complementary pair, used for
//                                       accents, icons, links — creates instant visual drama
//   BG       → lightened from #C5C4D4 — airy lavender without feeling heavy
//   #73708D  → textMuted / subtle ui (muted lavender)
//   #6D6F61  → textSecondary (earthy olive — grounds the palette)
// ─────────────────────────────────────────────────────────────────────────────
export const ridgeline: Theme = {
  name: 'ridgeline',
  label: 'Ridgeline',
  tagline: 'Bold heights, quiet confidence',
  colors: {
    // ── Backgrounds ──────────────────────────────────────────────────────────
    bg:       '#ECEBF2',              // lightened #C5C4D4 — soft lavender
    surface:  '#F6F5FA',             // near-white with cool-lavender cast
    surface2: '#DFDEEb',             // muted blue-grey for inputs/chips
    glass:    'rgba(246,245,250,0.84)',
    // ── Text ─────────────────────────────────────────────────────────────────
    text:          '#1C1D2A',        // deep blue-black — maximum contrast
    textSecondary: '#4E5050',        // close to #6D6F61 — earthy olive-grey
    textMuted:     '#73708D',        // exact palette chip 4 — muted lavender
    // ── Borders ──────────────────────────────────────────────────────────────
    border:   '#C8C7D4',
    hairline: 'rgba(28,29,42,0.09)',
    // ── Primary — indigo slate ───────────────────────────────────────────────
    primary:     '#536299',          // exact palette chip 1
    primaryDeep: '#3D4A7A',          // 15 % darker — pressed state
    primarySoft: '#DDE0F0',          // very light indigo tint
    onPrimary:   '#FFFFFF',
    // ── Accent — deep rust ───────────────────────────────────────────────────
    accent:     '#7C3539',           // exact palette chip 3 — the warm spark
    accentSoft: '#F4E0E1',           // faint rust tint — badge bgs, soft pills
    // ── Semantic tones ───────────────────────────────────────────────────────
    success: tone('#3E7044', '#E2F0E4', '#B4D6B8'),
    warning: tone('#7A5C10', '#F7EED8', '#DFC988'),
    danger:  tone('#7C3539', '#F4E0E1', '#E8AAAC'),
    info:    tone('#536299', '#DDE0F0', '#AAAEC8'),
    neutral: tone('#4E5050', '#DFDEEb', '#C4C3CE'),
  },
  state: {
    SUFFICIENT_EVIDENCE:   tone('#3E7044', '#E2F0E4', '#B4D6B8'),
    REVIEW_RECOMMENDED:    tone('#7A5C10', '#F7EED8', '#DFC988'),
    INSUFFICIENT_EVIDENCE: tone('#536299', '#DDE0F0', '#AAAEC8'),
    ACTIVE_DISPUTE:        tone('#7C3539', '#F4E0E1', '#E8AAAC'),
  },
  hero: {
    image: require('../../assets/images/themes/option4.jpeg'),
    // Deep indigo scrim — matches the primary family, looks stunning on the mountain photo
    scrim:
      'linear-gradient(180deg, rgba(28,30,52,0.06) 0%, rgba(28,30,52,0.22) 40%, rgba(28,30,52,0.92) 100%)',
    text:     '#F2F2F8',
    textSoft: 'rgba(224,224,238,0.88)',
    // Button gradient across the full indigo range
    button:   'linear-gradient(135deg, #6475AD 0%, #536299 50%, #3D4A7A 100%)',
    statusBar: 'light',
    position:  'center',
  },
  shadow: {
    card:  '0px 6px 20px rgba(83,98,153,0.12)',
    float: '0px 14px 36px rgba(83,98,153,0.26)',
  },
  radius: { sm: 12, md: 18, lg: 26, xl: 32, pill: 9999 },
  fonts: {
    display:    'PlusJakartaSans_800ExtraBold',
    displayAlt: 'PlusJakartaSans_800ExtraBold',
    ...jakarta,
  },
};

export const themes: Theme[] = [terracotta, creamGreen, stonyBlue, ridgeline];
