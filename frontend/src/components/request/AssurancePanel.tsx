import { Text, View } from 'react-native';

import type { Assessment } from '@/api/hooks';
import type { components } from '@/api/schema';
import {
  AssuranceBadge,
  Banner,
  Body,
  Card,
  Collapsible,
  IntervalBar,
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

/** What the evidence says, in plain language. Never one trust number (NFR-U-01, W1). */
function stateBanner(state: string, name: string) {
  switch (state) {
    case 'SUFFICIENT_EVIDENCE':
      return ['Enough verified history', `${name} has enough verified history for this item. You still decide.`];
    case 'REVIEW_RECOMMENDED':
      return ['Take a closer look', `${name}'s evidence is mixed, dated or unusual. Review the details below before deciding.`];
    case 'ACTIVE_DISPUTE':
      return ['Open dispute', `${name} has an unresolved dispute that affects this request.`];
    default:
      return [
        'Not enough history yet',
        `${name} has no verified transaction history. This is normal for new members and does not mean they are risky. You decide.`,
      ];
  }
}

function evidenceCount(a: Assessment): string {
  const weighted = (a.effective_evidence ?? 0).toFixed(1);
  if (a.verified_loans == null) return `${weighted} verified transactions (weighted)`;
  const loans = `${a.verified_loans} verified loan${a.verified_loans === 1 ? '' : 's'}`;
  return `${loans} · ${weighted} after weighting for recency and similarity`;
}

/** Indirect evidence (FR-T-04): people the lender trusts who lent to this borrower. */
function CommunityCard({ community, name }: { community: Community; name: string }) {
  const { theme } = useTheme();
  return (
    <Card>
      <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.text }}>
        Community paths
      </Text>
      {community.paths.length === 0 ? (
        <Body muted>No community paths found between you and {name}.</Body>
      ) : (
        <>
          {community.paths.map((p, i) => (
            <Body key={i}>
              • {p.via.length > 0 ? `Through ${p.via.join(' → ')}` : `${name} borrowed from you before`} (path
              strength {p.strength.toFixed(2)})
            </Body>
          ))}
          <Text style={{ fontSize: 11, color: theme.colors.textMuted }}>
            Community support {community.reliability.toFixed(2)}. It can support a request but is never
            enough on its own.
          </Text>
        </>
      )}
    </Card>
  );
}

export function AssurancePanel({ assessment, name }: { assessment: Assessment; name: string }) {
  const { theme } = useTheme();
  const [title, body] = stateBanner(assessment.assurance_state, name);
  const tone = theme.state[assessment.assurance_state as keyof typeof theme.state] ?? theme.colors.info;
  const hasInterval =
    assessment.ci90_low != null && assessment.ci90_high != null && assessment.posterior_mean != null;

  return (
    <View style={{ gap: 12 }}>
      <SectionLabel>Evidence summary</SectionLabel>
      <AssuranceBadge state={assessment.assurance_state} />
      <Banner tone={tone} title={title}>
        <Body muted>{body}</Body>
      </Banner>

      <Card>
        <View style={{ gap: 2 }}>
          <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.text }}>
            Direct reliability
          </Text>
          <Text style={{ fontSize: 11, color: theme.colors.textMuted }}>
            {evidenceCount(assessment)}
          </Text>
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
      </Card>

      {assessment.community ? <CommunityCard community={assessment.community} name={name} /> : null}

      <Card>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ fontSize: 13, fontWeight: '700', color: theme.colors.text }}>
            Manipulation risk
          </Text>
          <RiskPill level={assessment.manipulation_level ?? 1} />
        </View>
        {MANIPULATION_CHECKS_ACTIVE ? null : (
          <Body muted>Manipulation checks are not active in this version yet.</Body>
        )}
        <Text style={{ fontSize: 11, color: theme.colors.textMuted, fontStyle: 'italic' }}>
          Shown separately from reliability and never averaged with it. A flag is a reason to look, not
          an accusation.
        </Text>
      </Card>

      <Collapsible title="Why this assessment?">
        <Card style={{ backgroundColor: theme.colors.surface2 }}>
          <Body muted>{assessment.explanation}</Body>
          <Text style={{ fontSize: 11, color: theme.colors.textMuted }}>
            Rule {assessment.rule_fired} · config {assessment.config_version}
          </Text>
        </Card>
      </Collapsible>

      {assessment.safeguards.length > 0 ? (
        <Card>
          <SectionLabel>Recommended safeguards</SectionLabel>
          {assessment.safeguards.map((s, i) => (
            <Body key={i}>• {safeguardLabel(s)}</Body>
          ))}
        </Card>
      ) : null}
    </View>
  );
}
