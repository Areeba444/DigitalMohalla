import { Text, View } from 'react-native';

import type { Assessment } from '@/api/hooks';
import {
  ASSURANCE,
  assuranceTone,
  Badge,
  Body,
  Caption,
  Card,
  Collapsible,
  Icon,
  IntervalBar,
  Row,
  RiskPill,
  SectionLabel,
} from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

const SAFEGUARD_LABEL: Record<string, string> = {
  DEPOSIT_RECORD: 'Record the deposit before handover',
  HANDOVER_PHOTOS: 'Take item photos at handover',
  FIXED_RETURN_DATE: 'Agree a fixed return date',
};

function safeguardLabel(s: unknown): string {
  if (typeof s === 'string') return SAFEGUARD_LABEL[s] ?? s;
  if (s && typeof s === 'object') {
    const o = s as { code?: string; label?: string };
    return o.label ?? SAFEGUARD_LABEL[o.code ?? ''] ?? String(o.code ?? 'Safeguard');
  }
  return String(s);
}

/** What the evidence says, in plain language and about this request only (HCI analysis, W1). */
function stateSentence(state: string, name: string): string {
  switch (state) {
    case 'SUFFICIENT_EVIDENCE':
      return `${name} has verified loans like this one that went well. You still decide.`;
    case 'REVIEW_RECOMMENDED':
      return `${name}'s evidence is mixed, old or unusual for this item. Look at the details before deciding.`;
    case 'ACTIVE_DISPUTE':
      return `An unresolved dispute affects this request. A moderator is handling it.`;
    default:
      return `${name} has little or no verified history yet. That is normal for new members and does not mean they are risky. You decide.`;
  }
}

/**
 * The lender's evidence summary in three layers (HCI analysis, principle 1):
 * 1. always visible: the state, one sentence and the suggested safeguards;
 * 2. on tap: the evidence (interval, amount of evidence, manipulation checks, the engine's explanation);
 * 3. on tap: technical details (rule, configuration version, raw risk score).
 * Never a single trust number (NFR-U-01).
 */
export function AssurancePanel({ assessment, name }: { assessment: Assessment; name: string }) {
  const { theme } = useTheme();
  const state = assessment.assurance_state;
  const tone = assuranceTone(theme, state);
  const a = ASSURANCE[state] ?? { label: state, icon: 'info' as const };
  const hasInterval =
    assessment.ci90_low != null && assessment.ci90_high != null && assessment.posterior_mean != null;
  const n = assessment.effective_evidence ?? 0;
  // Until the detector ships (Slice C) the engine says so in its explanation; never imply checks ran.
  const checksActive = !/manipulation checks: not active/i.test(assessment.explanation);

  return (
    <View style={{ gap: 12 }}>
      <SectionLabel>Evidence summary</SectionLabel>
      <Card style={{ backgroundColor: tone.bg, borderColor: tone.border, borderWidth: 1, gap: 14 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <View
            style={{
              width: 48,
              height: 48,
              borderRadius: 16,
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: theme.colors.surface,
            }}>
            <Icon name={a.icon} size={26} color={tone.fg} />
          </View>
          <View style={{ flex: 1 }}>
            <Caption style={{ color: tone.fg }}>About this request</Caption>
            <Text style={{ fontFamily: theme.fonts.display, fontSize: 21, color: tone.fg }}>{a.label}</Text>
          </View>
        </View>
        <Body style={{ fontSize: 15 }}>{stateSentence(state, name)}</Body>
        {assessment.safeguards.length > 0 ? (
          <View style={{ gap: 8 }}>
            <SectionLabel color={tone.fg}>Suggested safeguards</SectionLabel>
            {assessment.safeguards.map((s, i) => (
              <View
                key={i}
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  gap: 10,
                  padding: 10,
                  borderRadius: theme.radius.sm,
                  backgroundColor: theme.colors.surface,
                }}>
                <Icon name="shield" size={18} color={theme.colors.accent} />
                <Body style={{ flex: 1, fontSize: 14 }}>{safeguardLabel(s)}</Body>
              </View>
            ))}
          </View>
        ) : null}
      </Card>

      <Card>
        <Collapsible title="See the evidence" icon="visibility">
          <View style={{ gap: 16 }}>
            <View style={{ gap: 8 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
                  Past loans as a borrower
                </Text>
                <Caption>
                  {n === 0 ? 'none verified yet' : `${n.toFixed(1)} verified, weighted`}
                </Caption>
              </View>
              {hasInterval ? (
                <IntervalBar
                  low={assessment.ci90_low as number}
                  high={assessment.ci90_high as number}
                  mean={assessment.posterior_mean as number}
                />
              ) : (
                <Body muted>No direct evidence yet.</Body>
              )}
              <Caption>
                The bar shows a range, not a score: it is wide when there is little evidence and narrows as
                verified loans add up. Recent loans and loans of similar items count more.
              </Caption>
            </View>

            <View style={{ gap: 8 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
                  Manipulation checks
                </Text>
                {checksActive ? (
                  <RiskPill level={assessment.manipulation_level ?? 1} />
                ) : (
                  <Badge label="Not active yet" tone={theme.colors.neutral} icon="schedule" />
                )}
              </View>
              <Caption>
                {checksActive
                  ? 'Checked separately and never averaged with the evidence above. A flag is a reason to look, not an accusation.'
                  : 'Checks for collusion and retaliation arrive in a later version, so nothing is flagged yet.'}
              </Caption>
            </View>

            <View
              style={{
                padding: 12,
                gap: 6,
                borderRadius: theme.radius.sm,
                backgroundColor: theme.colors.surface2,
              }}>
              <SectionLabel>In the engine&apos;s words</SectionLabel>
              <Body muted style={{ fontSize: 14 }}>
                {assessment.explanation}
              </Body>
            </View>
          </View>
        </Collapsible>
      </Card>

      <Card>
        <Collapsible title="Technical details" icon="tune">
          <View style={{ gap: 8 }}>
            <Row label="Rule" value={assessment.rule_fired} />
            <Row label="Policy decision" value={assessment.policy_decision} />
            {hasInterval ? (
              <Row
                label="90% credible interval"
                value={`${(assessment.ci90_low as number).toFixed(2)} to ${(assessment.ci90_high as number).toFixed(2)}`}
              />
            ) : null}
            <Row label="Manipulation risk score" value={`${assessment.manipulation_risk ?? 0} of 100`} />
            <Row label="Configuration" value={assessment.config_version} />
          </View>
        </Collapsible>
      </Card>
    </View>
  );
}
