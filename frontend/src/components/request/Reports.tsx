import { Text, View } from 'react-native';

import type { Report } from '@/api/hooks';
import { Body, Caption, Card, Icon, SectionLabel } from '@/components/ui';
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
  if (!report) return <Caption>Not recorded yet</Caption>;
  const line = (ok: boolean, label: string, key: string) => (
    <View key={key} style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
      <Icon name={ok ? 'check_circle' : 'error'} size={18} color={ok ? theme.colors.success.fg : theme.colors.warning.fg} />
      <Text style={{ flex: 1, fontFamily: theme.fonts.medium, fontSize: 14, color: ok ? theme.colors.text : theme.colors.warning.fg }}>
        {label}
      </Text>
    </View>
  );
  return (
    <View style={{ gap: 8 }}>
      {CHECKS.map(([key, label]) => line(!!list[key], label, key))}
      {report.deposit_received != null ? line(!!report.deposit_received, 'Deposit recorded as received', 'deposit') : null}
      {report.notes ? (
        <View style={{ padding: 10, borderRadius: 12, backgroundColor: theme.colors.surface2 }}>
          <Body muted style={{ fontSize: 14 }}>{report.notes}</Body>
        </View>
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
          <SectionLabel>At handover</SectionLabel>
          <Items report={handover} />
        </View>
        <View style={{ flex: 1, gap: 6 }}>
          <SectionLabel>At return</SectionLabel>
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
