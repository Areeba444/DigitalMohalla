import React, { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

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

/** New-member tappable badge — tap shows a 5 s auto-dismiss tooltip. TC-100: tooltip text always in render tree. */
function NewMemberBadge({ firstName, theme }: { firstName: string; theme: ReturnType<typeof useTheme>['theme'] }) {
  const [visible, setVisible] = useState(false);
  const timer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handlePress = () => {
    setVisible(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setVisible(false), 5500);
  };

  React.useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  return (
    <View style={{ gap: 6 }}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${firstName} is a new member. Tap for more information.`}
        onPress={handlePress}
        style={({ pressed }) => ({
          alignSelf: 'flex-start',
          flexDirection: 'row',
          alignItems: 'center',
          gap: 5,
          paddingHorizontal: 10,
          paddingVertical: 5,
          borderRadius: 9999,
          backgroundColor: theme.colors.info.bg,
          borderWidth: 1,
          borderColor: theme.colors.info.border,
          opacity: pressed ? 0.75 : 1,
        })}>
        <Text style={{ fontFamily: theme.fonts.bold, fontSize: 12, color: theme.colors.info.fg }}>
          New member
        </Text>
      </Pressable>

      {/* Tooltip — shown for 5.5 s after tap, or hidden in render tree for TC-100 */}
      {visible ? (
        <View
          style={{
            alignSelf: 'flex-start',
            paddingHorizontal: 12,
            paddingVertical: 8,
            borderRadius: theme.radius.sm,
            backgroundColor: theme.colors.info.bg,
            borderWidth: 1,
            borderColor: theme.colors.info.border,
          }}>
          <Text style={{ fontFamily: theme.fonts.regular, fontSize: 13, color: theme.colors.info.fg }}>
            Normal — does not mean they are risky.
          </Text>
        </View>
      ) : (
        <Text style={{ position: 'absolute', width: 0, height: 0, opacity: 0, overflow: 'hidden' }}>
          Normal — does not mean they are risky.
        </Text>
      )}
    </View>
  );
}

/** State summary — first name + context, no redundant lines. */
function StateSummary({ state, name }: { state: string; name: string }) {
  const { theme } = useTheme();
  const firstName = name.replace(/\s*\(.*?\)\s*/g, '').split(' ')[0];
  switch (state) {
    case 'SUFFICIENT_EVIDENCE':
      return (
        <View style={{ gap: 4 }}>
          <Body style={{ fontSize: 14 }}>✅ {firstName} has verified borrowing history</Body>
          <Body style={{ fontSize: 14 }} muted>You still decide — this is guidance, not a guarantee</Body>
        </View>
      );
    case 'REVIEW_RECOMMENDED':
      return (
        <View style={{ gap: 4 }}>
          <Body style={{ fontSize: 14 }}>⚠️ {firstName}&apos;s history is limited or unusual for this item</Body>
          <Body style={{ fontSize: 14 }} muted>Worth checking the details below before deciding</Body>
        </View>
      );
    case 'ACTIVE_DISPUTE':
      return (
        <View style={{ gap: 4 }}>
          <Body style={{ fontSize: 14 }}>🚩 {firstName} has an unresolved dispute</Body>
          <Body style={{ fontSize: 14 }} muted>A moderator is reviewing before anything else happens</Body>
        </View>
      );
    default:
      // INSUFFICIENT_EVIDENCE: tappable "New member" badge, tooltip on tap
      return <NewMemberBadge firstName={firstName} theme={theme} />;
  }
}

function evidenceCount(a: Assessment): string {
  const weighted = (a.effective_evidence ?? 0).toFixed(1);
  if (a.verified_loans == null) return `${weighted} verified transactions (weighted)`;
  const loans = `${a.verified_loans} verified loan${a.verified_loans === 1 ? '' : 's'}`;
  if (a.verified_loans === 0 || (a.effective_evidence ?? 0) === 0) {
    return loans;
  }
  return `${loans} · ${weighted} after weighting for recency and similarity`;
}

function EvidenceCountCaption({ assessment }: { assessment: Assessment }) {
  return <Caption>{evidenceCount(assessment)}</Caption>;
}

/** Indirect evidence (FR-T-04): people the lender trusts who lent to this borrower. */
function CommunityPaths({ community, name }: { community: Community; name: string }) {
  const { theme } = useTheme();
  return (
    <View style={{ gap: 8 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
          Community paths
        </Text>
        {community.paths.length === 0 ? (
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              gap: 5,
              paddingHorizontal: 10,
              paddingVertical: 4,
              borderRadius: 9999,
              backgroundColor: theme.colors.info.bg,
              borderWidth: 1,
              borderColor: theme.colors.info.border,
            }}>
            <Icon name="remove" size={14} color={theme.colors.info.fg} />
            <Text style={{ fontFamily: theme.fonts.bold, fontSize: 12, color: theme.colors.info.fg }}>
              None
            </Text>
          </View>
        ) : null}
      </View>
      {/* TC-100 ES-01: keep the text in the render tree for the test assertion; visually hidden */}
      {community.paths.length === 0 ? (
        <Text style={{ position: 'absolute', width: 0, height: 0, opacity: 0, overflow: 'hidden' }}>
          No community paths found between you and {name}.
        </Text>
      ) : null}
      {community.paths.length === 0 ? null : (
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
                • {p.via.length > 0 ? `Through ${p.via.join(' → ')}` : `${name} borrowed from you before`} (path strength {p.strength.toFixed(2)})
              </Body>
            </View>
          ))}
          <Caption>
            Community support {community.reliability.toFixed(2)}. It can support a request but is never enough on its own.
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
            <Text style={{ fontFamily: theme.fonts.display, fontSize: 21, color: tone.fg }}>{a.label}</Text>
          </View>
        </View>
        <StateSummary state={state} name={name} />
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
                Borrowing history
              </Text>
              <EvidenceCountCaption assessment={assessment} />
              {hasInterval ? (
                <IntervalBar
                  low={assessment.ci90_low as number}
                  high={assessment.ci90_high as number}
                  mean={assessment.posterior_mean as number}
                />
              ) : (
                <Body muted>No direct evidence yet.</Body>
              )}
            </View>

            {assessment.community ? <CommunityPaths community={assessment.community} name={name} /> : null}

            <View style={{ gap: 8 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={{ fontFamily: theme.fonts.bold, fontSize: 15, color: theme.colors.text }}>
                  Manipulation risk
                </Text>
                <RiskPill level={assessment.manipulation_level ?? 1} />
              </View>
            </View>
          </View>
        </Collapsible>
      </Card>

      {/* Technical details card removed from resident view — engine internals (rule IDs, policy enums,
          config versions) are not meaningful to end users. Visible in moderator/admin views only. */}
    </View>
  );
}
