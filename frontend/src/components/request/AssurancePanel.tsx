import React from 'react';
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

type Community = components['schemas']['CommunityOut'];

/** Bullet-point state summary — scannable, no wall of text. */
function stateSentence(state: string, name: string): React.ReactNode {
  const firstName = name.replace(/\s*\(.*?\)\s*/g, '').split(' ')[0];
  switch (state) {
    case 'SUFFICIENT_EVIDENCE':
      return (
        <View style={{ gap: 4 }}>
          <Body style={{ fontSize: 14 }}>✅ {firstName} has verified borrowing history</Body>
          <Body style={{ fontSize: 14 }}>✅ Enough evidence for this type of item</Body>
          <Body style={{ fontSize: 14, color: undefined }} muted>You still decide — this is guidance, not a guarantee</Body>
        </View>
      );
    case 'REVIEW_RECOMMENDED':
      return (
        <View style={{ gap: 4 }}>
          <Body style={{ fontSize: 14 }}>⚠️ {firstName}&apos;s history is limited or unusual for this item</Body>
          <Body style={{ fontSize: 14 }}>👁 Worth checking the details below before deciding</Body>
          <Body style={{ fontSize: 14 }} muted>You still decide</Body>
        </View>
      );
    case 'ACTIVE_DISPUTE':
      return (
        <View style={{ gap: 4 }}>
          <Body style={{ fontSize: 14 }}>🚩 {firstName} has an unresolved dispute</Body>
          <Body style={{ fontSize: 14 }}>⏳ A moderator is handling it</Body>
        </View>
      );
    default:
      return (
        <View style={{ gap: 4 }}>
          <Body style={{ fontSize: 14 }}>🆕 {firstName} is new to Digital Mohalla</Body>
          <Body style={{ fontSize: 14 }}>✓ This is normal — not a risk signal</Body>
          <Body style={{ fontSize: 14 }}>✓ Suggested safeguards are listed below</Body>
        </View>
      );
  }
}

/** Human-friendly borrowing history tier — no raw numbers exposed to users (NFR-U-01). */
function evidenceTier(a: Assessment): string {
  const loans = a.verified_loans ?? 0;
  const weighted = a.effective_evidence ?? 0;
  if (loans === 0) return '🆕 New member — no borrowing history yet';
  if (weighted < 1.5) return '📋 A few verified loans — just getting started';
  if (weighted < 4.0) return '✅ Some verified history';
  return '⭐ Established borrower with verified history';
}

/** Indirect evidence (FR-T-04): visual connection path between lender and borrower. */
function CommunityPaths({ community, name }: { community: Community; name: string }) {
  const { theme } = useTheme();
  const firstName = name.replace(/\s*\(.*?\)\s*/g, '').split(' ')[0];
  const hasPaths = community.paths.length > 0;
  return (
    <View style={{ gap: 8 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
          Community connection
        </Text>
        {hasPaths ? (
          <Icon name="hub" size={18} color={theme.colors.accent} />
        ) : (
          <Icon name="hub" size={18} color={theme.colors.textMuted} />
        )}
      </View>
      {!hasPaths ? (
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 8,
            padding: 10,
            borderRadius: theme.radius.sm,
            backgroundColor: theme.colors.surface2,
          }}>
          <Caption style={{ color: theme.colors.textMuted }}>You</Caption>
          <View style={{ flex: 1, borderBottomWidth: 1.5, borderColor: theme.colors.border, borderStyle: 'dashed' }} />
          <Caption style={{ color: theme.colors.textMuted }}>?</Caption>
          <View style={{ flex: 1, borderBottomWidth: 1.5, borderColor: theme.colors.border, borderStyle: 'dashed' }} />
          <Caption style={{ color: theme.colors.textMuted }}>{firstName}</Caption>
        </View>
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
                {p.via.length > 0 ? `You → ${p.via.join(' → ')} → ${firstName}` : `${firstName} borrowed from you before`}
              </Body>
            </View>
          ))}
          <Caption>
            You share {community.paths.length} community link{community.paths.length > 1 ? 's' : ''} with {firstName}.
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
        {stateSentence(state, name)}
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
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
                  Borrowing track record
                </Text>
              </View>
              <Caption>{evidenceTier(assessment)}</Caption>
              {hasInterval ? (
                <IntervalBar
                  low={assessment.ci90_low as number}
                  high={assessment.ci90_high as number}
                  mean={assessment.posterior_mean as number}
                />
              ) : (
                <Body muted>No borrowing history yet.</Body>
              )}
              {/* Bar explanation removed — labels on the bar itself are sufficient */}
            </View>

            {assessment.community ? <CommunityPaths community={assessment.community} name={name} /> : null}

            <View style={{ gap: 8 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
                  Unusual patterns
                </Text>
                <RiskPill level={assessment.manipulation_level ?? 1} />
              </View>
              {/* Caption removed — pill badge (Low/Monitor/Check needed/Needs review) is self-explanatory.
                  An ⓘ tooltip can be added here in a future iteration for curious users. */}
            </View>
          </View>
        </Collapsible>
      </Card>

      {/* Technical details card removed from resident view — engine internals (rule IDs, policy enums,
          config versions) are not meaningful to end users. Visible in moderator/admin views only. */}
    </View>
  );
}
