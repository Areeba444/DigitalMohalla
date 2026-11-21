# Digital Mohalla: frontend prototype (v3)

This is a clickable, responsive web prototype of the whole platform described in `project overview/digital_mohalla_overview_updated.docx`. It has light and dark themes.
- Every iteration 2 workflow (wireframes W1–W24) is live.
- Every module planned for later is fully designed and marked **Coming soon**: forum, assistant, events, vendors, kameti, insights, matching and admin management.

v3 was rebuilt from scratch after earlier versions were rejected as dated.

**For the team:** this is a design proposal to review before it's ported to the React Native app in `frontend/`. Please comment on the pull request, or change the files directly on this branch and push. Once we agree, the screens get rebuilt in React Native against the real API.

## Run it

No build step. From the repository root:

```
python -m http.server 8765 --directory prototype
```

| URL | What it is |
| --- | --- |
| http://localhost:8765 | The app. It starts on the public website; use **Explore the demo** or **Log in** |
| http://localhost:8765/devices.html | Five live screens in phone frames, in groups, with a light/dark switch |

Shortcuts inside the app:
- **Ctrl K** (or `/`) opens the command palette, which searches pages, items and actions.
- The sun/moon button switches theme, with a circular reveal.
- **Screens** (bottom right) lists all 93 screens with their wireframe IDs and FR IDs.

Fonts, icons and photos load from Google Fonts, unpkg and Unsplash, so the first load needs internet.

## Design system, built with the UI/UX Pro Max and frontend-design skills

- **Style:** "Vibrant and block-based" with bento grids, as recommended by the UI/UX Pro Max design-system search for a community app. It's a modern product-website shell:
  - a sticky glass top navigation;
  - a command palette;
  - bento dashboards;
  - floating bottom tabs on phones;
  - a separate sidebar console for moderators and admins.
- **Colour, "Bazaar daylight":** neutral off-white and near-black surfaces. Mehndi emerald is the primary colour (`#0F7B53` light, `#34D399` dark). Saffron, coral, sky and violet are used only for meaning:

  | Colour | Meaning |
  | --- | --- |
  | Emerald | Enough evidence |
  | Saffron | Review recommended, deadlines |
  | Sky | Not enough history yet (neutral, never red) |
  | Coral | Disputes |
  | Violet | Held for a moderator, and "coming soon" |

- **Dark mode:** designed alongside light mode, using toned-down tonal colours rather than inverted ones (skill rule `color-dark-mode`). Every text pair passes 4.5:1 in both themes. The theme follows the system setting until the user picks one.
- **Type:** Geist for everything and Geist Mono for codes and IDs.
- **The signature element is the evidence report.** It draws the recency-weighted Beta posterior from the assurance engine as a curve, with the 90% interval shaded:
  - flat for a new member;
  - wide for some evidence;
  - narrow and high for lots of evidence.

  It is never a single number. Community paths are drawn as a network with neighbours' photos.
- **Motion** (skill rules `shared-element-transition`, `spring-physics`, `stagger-sequence`):
  - View Transitions between pages, with the item photo carried over from card to detail page;
  - a circular reveal when switching theme;
  - spring tab indicators;
  - staggered scroll reveals;
  - a cursor-following glow on cards;
  - a live activity feed and marquee;
  - simulated push notifications;
  - typing indicators and the assistant's answer appearing word by word;
  - animated counters, drawn charts, a check-and-confetti moment on success, and a radar pulse during the location check.
  - All of it switches off under `prefers-reduced-motion`.

## Coverage

| Module (overview section) | Status | Screens |
| --- | --- | --- |
| 1 Users and community | Live | Website, register (W8), verify email, log in (+ wrong password, suspended), find community (W9), rules and methods, location + invitation (W10), three neutral results, duplicate blocked, new-member home |
| 1 Users and community | Soon | Role application (A8), blocking in chat and settings (A7) |
| 3 Borrowing lifecycle | Live | Activity board, lender decision with evidence (W1), accept / decline / "dates taken" (W2), counter-offer propose and respond (W14), loan journey, overdue → auto-dispute, no-show, handover lender and borrower (W3a, W3b, W17), extension ask and respond (W13), return, inspection (W4), report (W5), progress and withdraw, reply to moderator (W18), decision and appeal (W20), review (W15), list / edit / drafts (W22) |
| 4 Search and matching | Live | Borrow with filters, sort and reasons (W23), keyword-only, loading, empty and offline states, item details with lender evidence (W24), verified-only, already asked, own listing |
| 4 Search and matching | Soon | Ask the mohalla, fair-match proposals, saved searches (B9–B11) |
| 5 Trust and safety | Live | Evidence report (three states), My evidence with suppression (W16), report a listing, post, event, comment or vendor (D7) |
| 2 Events | Soon | Recommended with weighted reasons (C10), browse (C3), register / waitlist / cancel (C4, C5), ticket QR (C6), announcements, Q&A, poll, agenda (C7, C8), host an event (C1, C2), organizer check-in (C6), group chat (G2) |
| 6 Forum | Soon | Feed with 11 categories, votes, answered tag, post with best answer and threaded replies (E1–E3), new post with duplicate check (E4), follow and save (E5), badges with published rules (E6) |
| 7 Assistant | Soon | Cited answers, Roman Urdu, out-of-scope refusal, abstain → post to forum, helpful / report (F1–F3); knowledge base and content gaps (F4, F5) |
| 8 Communication | Live | Notifications with filters and deadlines (W12, G3); inbox with item chats, event groups and moderator messages (G1, G2); alert preferences (G4) |
| 9 Vendors | Soon | Directory (H3), profile + inquiry + reviews (H4), registration (H1, H2), admin verification (H5) |
| 10 Administration | Live | Case queue (W6), dispute with item possession (W7, W19), overdue dispute, appeal with second moderator and reversal (W20), three hold types with the ADR-0003 exit table, join requests incl. "already decided" (W11), audit log with tamper warning and concentration flag (W21) |
| 10 Administration | Soon | Reports and automatic flags (I3, I5), event approvals (C2), users and roles (I1), communities and categories (I2) |
| 11 Analytics | Live | Admin analytics (J1) |
| 11 Analytics | Soon | Personal impact (J2), neighbourhood insights with user-set weights (J3) |
| Kameti | Soon (no requirements yet) | Savings-circle rotation, record-only |

## Files

| File | Holds |
| --- | --- |
| `index.html` | Shell: top nav, main view, bottom tabs, toasts |
| `css/tokens.css` | Light and dark tokens; maps to a React Native `theme.ts` |
| `css/app.css` | Components, layout and motion |
| `js/data.js` | Mock data shaped like the backend (states, Beta parameters, hold reasons, events) |
| `js/core.js` | Router with view transitions, theme, command palette, popovers, toasts, evidence curve, calendar, timelines |
| `js/p-public.js` | Website, register, log in, community joining |
| `js/p-borrow.js` | Home, borrow, item, request, ask the mohalla |
| `js/p-loans.js` | Activity, lender decision, the whole loan lifecycle, listings |
| `js/p-community.js` | Community hub, forum, assistant, events, vendors, kameti, insights |
| `js/p-account.js` | Inbox, notifications, profile, my evidence, settings, role application, HCI notes |
| `js/p-console.js` | Moderator and admin console |
| `devices.html` | Phone-frame preview |

## Moving to React Native

| Prototype | React Native |
| --- | --- |
| `tokens.css` (light and dark) | `theme.ts` with `useColorScheme()` |
| Router + view transitions | React Navigation stacks + `react-native-reanimated` shared element transitions |
| `betaCurve`, `pathsGraph`, charts | `react-native-svg` components with the same maths |
| Bottom tabs, sheets | `@react-navigation/bottom-tabs`, `@gorhom/bottom-sheet` |
| Icons, fonts | `lucide-react-native` (same names), `expo-font` with Geist |

On the web, the same screens become the responsive website, and the console is used on tablets and laptops.

## Prototype limits

- **All people, items, cases and numbers are synthetic.** Names, statistics and evidence values are illustrative, not results from the engine or a pilot.
- Data is mocked: searches, filters, votes and chats change on screen only.
- Everything shown is decision support for residents and moderators, not a guarantee.
- It loads Lucide 0.468.0 (ISC) from unpkg and Geist / Geist Mono (OFL) from Google Fonts at runtime. Neither is a dependency of the app in `frontend/`.
- Photos are Unsplash stock images standing in for user uploads.
- The QR code is a visual placeholder.
- The Urdu interface isn't built. Roman Urdu is shown in search and the assistant.
