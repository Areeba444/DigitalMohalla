import { Text, View } from 'react-native';

import type { Assessment } from '@/api/hooks';
import type { components } from '@/api/schema';
import {
  ASSURANCE,
  assuranceTone,
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

// Manipulation detection arrives with the human loop (Slice C); until then every request is level 1.
const MANIPULATION_CHECKS_ACTIVE = false;

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

type Community = components['schemas']['CommunityOut'];

/** What the evidence says, in plain language and about this request only (HCI analysis, W1). */
function stateSentence(state: string, name: string): string {
  switch (state) {
    case 'SUFFICIENT_EVIDENCE':
      return `${name} has enough verified history for this item. You still decide.`;
    case 'REVIEW_RECOMMENDED':
      return `${name}'s evidence is mixed, dated or unusual for this item. Look at the details before deciding.`;
    case 'ACTIVE_DISPUTE':
      return `${name} has an unresolved dispute that affects this request. A moderator is handling it.`;
    default:
      return `${name} has no verified transaction history yet. This is normal for new members and does not mean they are risky. You decide.`;
  }
}

function evidenceCount(a: Assessment): string {
  const weighted = (a.effective_evidence ?? 0).toFixed(1);
  if (a.verified_loans == null) return `${weighted} verified transactions (weighted)`;
  const loans = `${a.verified_loans} verified loan${a.verified_loans === 1 ? '' : 's'}`;
  return `${loans} · ${weighted} after weighting for recency and similarity`;
}

/** Indirect evidence (FR-T-04): people the lender trusts who lent to this borrower. */
function CommunityPaths({ community, name }: { community: Community; name: string }) {
  const { theme } = useTheme();
  return (
    <View style={{ gap: 8 }}>
      <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
        Community paths
      </Text>
      {community.paths.length === 0 ? (
        <Body muted style={{ fontSize: 14 }}>
          No community paths found between you and {name}.
        </Body>
      ) : (
        <>
          {community.paths.map((p, i) => (
            <View
              key={i}
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                gap: 10,
                padding: 10,
                borderRadius: theme.radius.sm,
                backgroundColor: theme.colors.accentSoft,
              }}>
              <Icon name="hub" size={18} color={theme.colors.accent} />
              <Body style={{ flex: 1, fontSize: 14 }}>
                • {p.via.length > 0 ? `Through ${p.via.join(' → ')}` : `${name} borrowed from you before`} (path
                strength {p.strength.toFixed(2)})
              </Body>
            </View>
          ))}
          <Caption>
            Community support {community.reliability.toFixed(2)}. It can support a request but is never enough
            on its own.
          </Caption>
        </>
      )}
    </View>
  );
}

/**
 * The lender's evidence summary in three layers (HCI analysis, principle 1):
 * 1. the state, one sentence and the suggested safeguards;
 * 2. the evidence (interval, verified loans, community paths, manipulation checks),
 *    open by default because the lender's decision rests on it (TC-100), and collapsible;
 * 3. technical details (rule, policy decision, configuration version and the engine's own wording, which
 *    contains raw values), closed by default.
 * Never a single trust number or rating (NFR-U-01).
 */
export function AssurancePanel({ assessment, name }: { assessment: Assessment; name: string }) {
  const { theme } = useTheme();
  const state = assessment.assurance_state;
  const tone = assuranceTone(theme, state);
  const a = ASSURANCE[state] ?? { label: state, icon: 'info' as const };
  const hasInterval =
    assessment.ci90_low != null && assessment.ci90_high != null && assessment.posterior_mean != null;

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
        <Collapsible title="The evidence" icon="visibility" defaultOpen>
          <View style={{ gap: 18 }}>
            <View style={{ gap: 8 }}>
              <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
                Direct reliability
              </Text>
              <Caption>{evidenceCount(assessment)}</Caption>
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
                The bar shows a range, wide when there is little evidence and narrower as verified loans add up.
                Recent loans and loans of similar items count more.
              </Caption>
            </View>

            {assessment.community ? <CommunityPaths community={assessment.community} name={name} /> : null}

            <View style={{ gap: 8 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
                  Manipulation risk
                </Text>
                <RiskPill level={assessment.manipulation_level ?? 1} />
              </View>
              {MANIPULATION_CHECKS_ACTIVE ? null : (
                <Body muted style={{ fontSize: 14 }}>
                  Manipulation checks are not active in this version yet.
                </Body>
              )}
              <Caption>
                Shown separately from reliability and never averaged with it. A flag is a reason to look, not an
                accusation.
              </Caption>
            </View>
          </View>
        </Collapsible>
      </Card>

      <Card>
        <Collapsible title="Technical details" icon="tune">
          <View style={{ gap: 12 }}>
            <View style={{ gap: 8 }}>
              <Row label="Rule" value={assessment.rule_fired} />
              <Row label="Policy decision" value={assessment.policy_decision} />
              <Row label="Configuration" value={assessment.config_version} />
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
    </View>
  );
}
