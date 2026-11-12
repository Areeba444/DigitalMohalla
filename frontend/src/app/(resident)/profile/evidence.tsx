/**
 * W16 — My Evidence & Trust Profile (FR-D-02, FR-T-08, NFR-U-01)
 *
 * The definitive multi-dimensional evidence profile.
 * ZERO single composite trust scores. The Beta credible interval is the signal.
 *
 * HCI notes:
 * - Each dimension is a MultiDimRow (icon + label + value chip).
 * - Interval bar shows [low, high] range, not a point score.
 * - Manipulation risk shown as a RiskPill (level 1–4), never a number alone.
 * - INSUFFICIENT_EVIDENCE is rendered neutral (blue-grey), never red.
 */
import { View } from 'react-native';

import {
  AssuranceBadge,
  Avatar,
  BackButton,
  Banner,
  Body,
  Card,
  Caption,
  Collapsible,
  HeroScreen,
  IntervalBar,
  MultiDimRow,
  RiskPill,
  SectionLabel,
  Title,
} from '@/components/ui';
import { mockEvidenceProfile } from '@/api/mocks/iteration2Mocks';
import { useTheme } from '@/theme/ThemeProvider';

export default function EvidenceProfile() {
  const { theme } = useTheme();
  const p = mockEvidenceProfile;

  return (
    <HeroScreen
      height={200}
      hero={
        <View style={{ flex: 1, justifyContent: 'flex-end', gap: 6 }}>
          <Avatar name={p.user_name} size={52} />
          <Title size={22} color={theme.hero.text}>{p.user_name}</Title>
          <Caption style={{ color: theme.hero.textSoft }}>
            {p.community} · Member since {p.member_since}
          </Caption>
        </View>
      }>
      <BackButton />

      {/* Assurance state — prominent but NOT a single number */}
      <Card>
        <SectionLabel>Your assurance state</SectionLabel>
        <AssuranceBadge state={p.assurance_state} />
        <Body muted style={{ fontSize: 14, marginTop: 4 }}>
          Based on {p.transaction_count} verified transactions. This is a range, not a score.
        </Body>
      </Card>

      {/* Beta credible interval — the core statistical signal */}
      <Card>
        <SectionLabel>Direct reliability estimate (90% credible interval)</SectionLabel>
        <IntervalBar low={p.interval.low} high={p.interval.high} mean={p.interval.mean} />
        <Collapsible label="What does this mean?">
          <Body muted style={{ fontSize: 13 }}>
            The bar shows the range where your true reliability likely falls, based on verified loan outcomes.
            A narrower bar means more consistent evidence. The mark shows the most likely value.
          </Body>
        </Collapsible>
      </Card>

      {/* Individual dimensions */}
      <Card>
        <SectionLabel>Dimension breakdown</SectionLabel>
        {Object.values(p.dimensions).map((dim) => (
          <MultiDimRow
            key={dim.label}
            icon={dim.icon}
            label={dim.label}
            value={dim.value}
            tone={theme.colors.success}
          />
        ))}
      </Card>

      {/* Manipulation risk */}
      <Card>
        <SectionLabel>Manipulation risk signal</SectionLabel>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <RiskPill level={p.manipulation_risk.level} />
          <Body muted style={{ fontSize: 14, flex: 1 }}>{p.manipulation_risk.label}</Body>
        </View>
        <Collapsible label="What does this check?">
          <Body muted style={{ fontSize: 13 }}>
            The system checks for abnormal patterns like reciprocal review rings or coordinated borrowing clusters.
            This signal is separate from your transaction history and is never used to auto-restrict you.
          </Body>
        </Collapsible>
      </Card>

      <Banner tone={theme.colors.info} title="Data & privacy" icon="shield">
        <Body muted style={{ fontSize: 13 }}>
          No identity numbers or exact GPS coordinates are stored. Only anonymised transaction outcomes contribute to your evidence.
        </Body>
      </Banner>
    </HeroScreen>
  );
}

