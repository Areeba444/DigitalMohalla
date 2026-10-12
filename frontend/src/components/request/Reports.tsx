import { Text, View } from 'react-native';

import type { Report } from '@/api/hooks';
import { Body, Card, SectionLabel } from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

export const CHECKS = [
  ['works', 'Item works as expected'],
  ['no_damage', 'No visible damage'],
  ['accessories', 'Accessories included'],
] as const;

function checklistOf(report: Report | undefined): Record<string, boolean> {
  const c = report?.checklist;
  return c && typeof c === 'object' && !Array.isArray(c) ? (c as Record<string, boolean>) : {};
}

function Items({ report }: { report?: Report }) {
  const { theme } = useTheme();
  const list = checklistOf(report);
  if (!report) return <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>Not recorded yet</Text>;
  return (
    <View style={{ gap: 4 }}>
      {CHECKS.map(([key, label]) => (
        <Text
          key={key}
          style={{ fontSize: 13, color: list[key] ? theme.colors.text : theme.colors.warning.fg }}>
          {list[key] ? '✓' : '✗'} {label}
        </Text>
      ))}
      {report.deposit_received != null ? (
        <Text style={{ fontSize: 13, color: theme.colors.text }}>
          {report.deposit_received ? '✓' : '✗'} Deposit recorded as received
        </Text>
      ) : null}
      {report.notes ? (
        <Text style={{ fontSize: 13, color: theme.colors.textSecondary, fontStyle: 'italic' }}>
          “{report.notes}”
        </Text>
      ) : null}
    </View>
  );
}

/** Lender's handover checklist, shown to the borrower before they confirm receipt (W3b). */
export function HandoverSummary({ report }: { report?: Report }) {
  return (
    <Card>
      <SectionLabel>Lender&apos;s handover checklist</SectionLabel>
      <Items report={report} />
    </Card>
  );
}

/** Handover baseline beside the return inspection, so differences show at once (W4). */
export function ReturnComparison({
  handover,
  returned,
}: {
  handover?: Report;
  returned?: Report;
}) {
  const { theme } = useTheme();
  const base = checklistOf(handover);
  const now = checklistOf(returned);
  const changed = CHECKS.filter(([k]) => returned && base[k] && !now[k]);
  return (
    <Card>
      <SectionLabel>Handover vs return</SectionLabel>
      <View style={{ flexDirection: 'row', gap: 12 }}>
        <View style={{ flex: 1, gap: 6 }}>
          <Text style={{ fontSize: 12, fontWeight: '700', color: theme.colors.textMuted }}>
            AT HANDOVER
          </Text>
          <Items report={handover} />
        </View>
        <View style={{ flex: 1, gap: 6 }}>
          <Text style={{ fontSize: 12, fontWeight: '700', color: theme.colors.textMuted }}>
            AT RETURN
          </Text>
          <Items report={returned} />
        </View>
      </View>
      {changed.length > 0 ? (
        <Body style={{ color: theme.colors.warning.fg }}>
          Changed since handover: {changed.map(([, l]) => l.toLowerCase()).join(', ')}.
        </Body>
      ) : null}
    </Card>
  );
}
