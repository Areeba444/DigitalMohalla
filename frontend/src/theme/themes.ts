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
// Exact palette from option3.jpeg, used per the design spec:
//
//   Role           Hex       Usage   Applied to
//   ────────────── ────────  ──────  ──────────────────────────────────────
//   Background     #EFE9E7   60%    bg, surface, glass
//   Text / Dark UI #55565B   20%    text (body), headings, icons
//   Primary brand  #608FA3   10%    primary buttons, active tabs, links
//   Secondary      #BCCC83    5%    success tones, tags, badges, toggles
//   Accent / CTA   #895377    5%    accent highlights, notifications, CTAs
// ─────────────────────────────────────────────────────────────────────────────
export const stonyBlue: Theme = {
  name: 'stony-blue',
  label: 'Stony Blue',
  tagline: 'Still waters, sure footing',
  colors: {
    // ── Backgrounds (60 % of screen real-estate) ──────────────────────────
    bg:       '#EFE9E7',              // exact spec — warm alabaster
    surface:  '#FDFAF9',             // card/sheet — just off-white with warm cast
    surface2: '#E4DDD9',             // inputs, chips, subtle containers
    glass:    'rgba(253,250,249,0.82)',
    // ── Text / Dark UI (20 %) ─────────────────────────────────────────────
    text:          '#55565B',        // ← EXACT spec — charcoal slate, headings + body
    textSecondary: '#757679',        // mid-step — captions, metadata
    textMuted:     '#9E9FA3',        // placeholders, disabled
    // ── Borders ──────────────────────────────────────────────────────────
    border:   '#D5CEC9',
    hairline: 'rgba(85,86,91,0.10)',
    // ── Primary brand (10 %) — Dusty Cerulean ────────────────────────────
    primary:     '#608FA3',          // exact spec — CTA buttons, active tabs, links
    primaryDeep: '#477284',          // pressed / hover — 15 % darker
    primarySoft: '#DFF0F6',          // faint tint — avatar bg, selected chips
    onPrimary:   '#FFFFFF',
    // ── Accent / CTA (5 %) — Muted Plum ─────────────────────────────────
    accent:     '#895377',           // exact spec — notifications, alerts, active indicators
    accentSoft: '#F2E8EF',           // faint plum tint — badge bgs, alert strips
    // ── Semantic tones ────────────────────────────────────────────────────
    // success = Sage Moss #BCCC83 — secondary colour per spec (tags, badges, toggles)
    success: tone('#5A7828', '#EEF4DC', '#BCCC83'),  // fg darkened for text contrast
    warning: tone('#8A6010', '#FBF3E0', '#EAD39C'),
    danger:  tone('#A0302A', '#FCEDEC', '#F2B8B5'),
    info:    tone('#608FA3', '#DFF0F6', '#AED2E0'),  // info re-uses primary family
    neutral: tone('#55565B', '#E4DDD9', '#BCCC83'),  // neutral border = sage so tags pick it up
  },
  state: {
    SUFFICIENT_EVIDENCE:   tone('#5A7828', '#EEF4DC', '#BCCC83'),
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
// Exact palette from option4.jpeg, used per the design spec:
//
//   Role           Hex       Usage   Applied to
//   ────────────── ────────  ──────  ──────────────────────────────────────────
//   Background     #C5C4D4   60%    bg (the actual spec colour), surface, glass
//   Text / Dark UI #6D6F61   20%    text, borders, inactive icons, dividers
//   Primary brand  #536299   10%    primary buttons, active tabs, headers, links
//   Secondary      #73708D    5%    info tones → tags, disabled states, sidebars
//   Accent/Merlot  #7C3539    5%    accent → alerts, destructive badges, highlights
// ─────────────────────────────────────────────────────────────────────────────
export const ridgeline: Theme = {
  name: 'ridgeline',
  label: 'Ridgeline',
  tagline: 'Bold heights, quiet confidence',
  colors: {
    // ── Backgrounds (60%) — Soft Lavender Mist ───────────────────────────────
    bg:       '#C5C4D4',              // exact spec — the page canvas
    surface:  '#D9D8E6',             // slightly lighter — cards / sheets float above bg
    surface2: '#B8B7C9',             // slightly deeper — inputs, chips, subtle containers
    glass:    'rgba(197,196,212,0.86)',
    // ── Text / Dark UI (20%) — Olive Charcoal ────────────────────────────────
    text:          '#6D6F61',        // exact spec — primary body text, headings
    textSecondary: '#888A80',        // mid-step — captions, metadata
    textMuted:     '#A6A8B0',        // placeholders, disabled labels
    // ── Borders ──────────────────────────────────────────────────────────────
    border:   '#AFAEBF',             // between bg and surface
    hairline: 'rgba(109,111,97,0.14)',
    // ── Primary (10%) — Twilight Indigo ──────────────────────────────────────
    primary:     '#536299',          // exact spec — buttons, active tabs, links
    primaryDeep: '#3D4A7A',          // pressed / hover — 15 % darker
    primarySoft: '#CFD3E8',          // indigo tint that reads on the lavender bg
    onPrimary:   '#FFFFFF',
    // ── Accent (5%) — Deep Merlot ────────────────────────────────────────────
    accent:     '#7C3539',           // exact spec — alerts, badges, active highlights
    accentSoft: '#E8CCCF',           // faint merlot tint — badge bgs, alert strips
    // ── Semantic tones ───────────────────────────────────────────────────────
    success: tone('#3A6E40', '#CEEAD2', '#99C9A0'),
    warning: tone('#7A5C10', '#EEE0C0', '#D4B870'),
    // danger uses merlot family — spec says #7C3539 = destructive actions
    danger:  tone('#7C3539', '#E8CCCF', '#CE9598'),
    // info uses Muted Iris #73708D — spec says = secondary buttons, tags, disabled
    info:    tone('#73708D', '#D4D3E2', '#AAA8BC'),
    neutral: tone('#6D6F61', '#B8B7C9', '#9E9DAE'),
  },
  state: {
    SUFFICIENT_EVIDENCE:   tone('#3A6E40', '#CEEAD2', '#99C9A0'),
    REVIEW_RECOMMENDED:    tone('#7A5C10', '#EEE0C0', '#D4B870'),
    // Muted Iris as the neutral/insufficient state — per secondary colour role
    INSUFFICIENT_EVIDENCE: tone('#73708D', '#D4D3E2', '#AAA8BC'),
    ACTIVE_DISPUTE:        tone('#7C3539', '#E8CCCF', '#CE9598'),
  },
  hero: {
    image: require('../../assets/images/themes/option4.jpeg'),
    // Deep indigo scrim — matches primary, dramatic on the mountain photo
    scrim:
      'linear-gradient(180deg, rgba(28,30,52,0.06) 0%, rgba(28,30,52,0.22) 40%, rgba(28,30,52,0.92) 100%)',
    text:     '#F0F0F6',
    textSoft: 'rgba(220,220,236,0.88)',
    // Indigo gradient button — primary family
    button:   'linear-gradient(135deg, #6475AD 0%, #536299 50%, #3D4A7A 100%)',
    statusBar: 'light',
    position:  'center',
  },
  shadow: {
    card:  '0px 6px 20px rgba(83,98,153,0.14)',
    float: '0px 14px 36px rgba(83,98,153,0.28)',
  },
  radius: { sm: 12, md: 18, lg: 26, xl: 32, pill: 9999 },
  fonts: {
    display:    'PlusJakartaSans_800ExtraBold',
    displayAlt: 'PlusJakartaSans_800ExtraBold',
    ...jakarta,
  },
};

export const themes: Theme[] = [terracotta, creamGreen, stonyBlue, ridgeline];
