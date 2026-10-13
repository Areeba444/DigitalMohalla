import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { useAction, type Action, type CommandResult, type RequestDetail } from '@/api/hooks';
import { Banner, Body, Button, Card, Check, ErrorText, Field, SectionLabel } from '@/components/ui';
import { useTheme } from '@/theme/ThemeProvider';

import { CHECKS, HandoverSummary, ReturnComparison } from './Reports';

type Checks = Record<string, boolean>;
const allChecked = (): Checks => Object.fromEntries(CHECKS.map(([k]) => [k, true]));

function ChecklistForm({
  checks,
  setChecks,
  notes,
  setNotes,
  deposit,
}: {
  checks: Checks;
  setChecks: (c: Checks) => void;
  notes: string;
  setNotes: (n: string) => void;
  deposit?: { value: boolean; set: (v: boolean) => void };
}) {
  return (
    <Card>
      <SectionLabel>Condition checklist</SectionLabel>
      {CHECKS.map(([key, label]) => (
        <Check
          key={key}
          label={label}
          checked={!!checks[key]}
          onToggle={() => setChecks({ ...checks, [key]: !checks[key] })}
        />
      ))}
      {deposit ? (
        <Check
          label="Deposit received (record only; no money moves in the app)"
          checked={deposit.value}
          onToggle={() => deposit.set(!deposit.value)}
        />
      ) : null}
      <Field label="Notes (optional)" value={notes} onChangeText={setNotes} multiline />
    </Card>
  );
}

/** The result of the last action, e.g. the W2 "dates taken" conflict. */
function ResultBanner({ result }: { result: CommandResult }) {
  const { theme } = useTheme();
  if (result.message === 'dates taken') {
    return (
      <Banner tone={theme.colors.warning} title="These dates were taken" icon="event_busy">
        <Body muted>
          Another request for these dates was accepted first, so this request was declined
          automatically with the reason “dates taken”. The borrower has been told. Your other
          pending requests are unaffected.
        </Body>
      </Banner>
    );
  }
  if (!result.message) return null;
  return (
    <Banner tone={theme.colors.info} title="Update" icon="info">
      <Body muted>{result.message}</Body>
    </Banner>
  );
}

export function ActionPanel({ request, id }: { request: RequestDetail; id: string }) {
  const { theme } = useTheme();
  const act = useAction(id);
  const [result, setResult] = useState<CommandResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checks, setChecks] = useState<Checks>(allChecked());
  const [notes, setNotes] = useState('');
  const [deposit, setDeposit] = useState(false);

  const has = (name: string) => request.available_actions.includes(name);
  const run = (action: Action) => {
    setError(null);
    setResult(null);
    act.mutate(action, {
      onSuccess: setResult,
      onError: (e) => setError(e.message),
    });
  };
  const handoverReport = request.reports.find((r) => r.phase === 'HANDOVER' && r.reporter_role === 'LENDER');
  const returnReport = request.reports.find((r) => r.phase === 'RETURN' && r.reporter_role === 'LENDER');
  const body = { checklist: checks, notes: notes || undefined };

  return (
    <View style={{ gap: 12 }}>
      {result ? <ResultBanner result={result} /> : null}
      <ErrorText message={error} />

      {has('accept') ? (
        <Card>
          <SectionLabel>Your decision</SectionLabel>
          <Body muted style={{ fontSize: 14 }}>
            Accepting reserves these dates and automatically declines other pending requests for
            them.
          </Body>
          <Button label="Accept request" icon="check_circle" loading={act.isPending} onPress={() => run({ name: 'accept' })} />
          <Button
            label="Decline request"
            icon="close"
            variant="outline"
            loading={act.isPending}
            onPress={() => run({ name: 'decline' })}
          />
          {/* UC-B6 counter-offer is planned for iteration 2 (TC-100) */}
          <Button label="Counter-offer (coming in iteration 2)" variant="ghost" disabled onPress={() => {}} />
        </Card>
      ) : null}

      {has('handover_checklist') ? (
        <>
          <Banner tone={theme.colors.info} title="Handover" icon="handshake">
            <Body muted style={{ fontSize: 14 }}>Record the item&apos;s condition before it changes hands. The borrower then confirms receipt.</Body>
          </Banner>
          <ChecklistForm
            checks={checks}
            setChecks={setChecks}
            notes={notes}
            setNotes={setNotes}
            deposit={request.deposit_required ? { value: deposit, set: setDeposit } : undefined}
          />
          <Button
            label="Send for borrower review"
            icon="send"
            loading={act.isPending}
            onPress={() =>
              run({
                name: 'handover_checklist',
                body: { ...body, deposit_received: request.deposit_required ? deposit : undefined },
              })
            }
          />
        </>
      ) : null}

      {has('handover_confirm') ? (
        <>
          <HandoverSummary report={handoverReport} />
          <Field label="Your remarks (optional)" value={notes} onChangeText={setNotes} multiline />
          <Button
            label="Confirm receipt & start loan"
            icon="handshake"
            loading={act.isPending}
            onPress={() =>
              run({ name: 'handover_confirm', body: { condition_agreed: true, notes: notes || undefined } })
            }
          />
          <Button
            label="I disagree: condition mismatch"
            icon="flag"
            variant="outline"
            loading={act.isPending}
            onPress={() =>
              run({ name: 'handover_confirm', body: { condition_agreed: false, notes: notes || undefined } })
            }
          />
        </>
      ) : null}

      {has('initiate_return') ? (
        <Card>
          <SectionLabel>Return</SectionLabel>
          <Body muted style={{ fontSize: 14 }}>Ready to give the item back? Starting the return lets the lender inspect it.</Body>
          <Button label="Start return" icon="assignment_return" loading={act.isPending} onPress={() => run({ name: 'initiate_return' })} />
        </Card>
      ) : null}

      {has('return_checklist') ? (
        <>
          <ChecklistForm checks={checks} setChecks={setChecks} notes={notes} setNotes={setNotes} />
          <Button
            label="Condition matches: record inspection"
            icon="task_alt"
            loading={act.isPending}
            onPress={() => run({ name: 'return_checklist', body: { ...body, condition_agreed: true } })}
          />
          <Button
            label="Report damage"
            icon="flag"
            variant="outline"
            loading={act.isPending}
            onPress={() => run({ name: 'return_checklist', body: { ...body, condition_agreed: false } })}
          />
        </>
      ) : null}

      {has('return_confirm') ? (
        <>
          <ReturnComparison
            handover={request.reports.find((r) => r.phase === 'HANDOVER' && r.reporter_role === 'LENDER')}
            returned={returnReport}
          />
          <Button
            label="Agree condition & close"
            icon="task_alt"
            loading={act.isPending}
            onPress={() => run({ name: 'return_confirm', body: { condition_agreed: true } })}
          />
          <Button
            label="I disagree"
            icon="flag"
            variant="outline"
            loading={act.isPending}
            onPress={() => run({ name: 'return_confirm', body: { condition_agreed: false } })}
          />
        </>
      ) : null}

      {has('cancel') ? (
        <Button
          label="Cancel request"
          icon="close"
          variant="ghost"
          loading={act.isPending}
          onPress={() => run({ name: 'cancel' })}
        />
      ) : null}

      {has('raise_dispute') ? (
        <Button
          label="Raise a dispute"
          icon="flag"
          variant="ghost"
          onPress={() => router.push(`/dispute/${id}`)}
        />
      ) : null}
    </View>
  );
}
