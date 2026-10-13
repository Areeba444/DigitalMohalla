import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api, unwrap } from './client';
import type { components } from './schema';

export type RequestDetail = components['schemas']['RequestOut'];
export type MyRequest = components['schemas']['MyRequestOut'];
export type BrowseItem = components['schemas']['BrowseItemOut'];
export type CommandResult = components['schemas']['CommandOut'];
export type Assessment = components['schemas']['AssessmentOut'];
export type Report = components['schemas']['ReportOut'];
export type DisputeTrail = components['schemas']['DisputeTrailOut'];
export type QueueCase = components['schemas']['CaseQueueOut'];
export type ModeratorCase = components['schemas']['ModeratorCaseOut'];
export type DecisionIn = components['schemas']['DecisionIn'];
export type DisputeReason = components['schemas']['DisputeIn']['reason'];

const A = '/api/v1' as const;

export const useMyRequests = () =>
  useQuery({
    queryKey: ['requests'],
    queryFn: async () => unwrap(await api.GET(`${A}/requests`)),
  });

export const useItems = () =>
  useQuery({
    queryKey: ['items'],
    queryFn: async () => unwrap(await api.GET(`${A}/items`)),
  });

export const useRequest = (id: string) =>
  useQuery({
    queryKey: ['request', id],
    queryFn: async () =>
      unwrap(await api.GET(`${A}/requests/{txn_id}`, { params: { path: { txn_id: id } } })),
  });

export const useEvents = (id: string) =>
  useQuery({
    queryKey: ['events', id],
    queryFn: async () =>
      unwrap(
        await api.GET(`${A}/transactions/{txn_id}/events`, { params: { path: { txn_id: id } } }),
      ),
  });

export function useLogin() {
  return useMutation({
    mutationFn: async (body: { email: string; password: string }) =>
      unwrap(await api.POST(`${A}/auth/login`, { body })),
  });
}

export function useCreateRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: components['schemas']['RequestIn']) =>
      unwrap(await api.POST(`${A}/requests`, { body })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['requests'] }),
  });
}

export type Action =
  | { name: 'accept' }
  | { name: 'decline'; reason?: string }
  | { name: 'cancel' }
  | { name: 'handover_checklist'; body: components['schemas']['ChecklistIn'] }
  | { name: 'handover_confirm'; body: components['schemas']['ConfirmIn'] }
  | { name: 'initiate_return' }
  | { name: 'return_checklist'; body: components['schemas']['ConfirmIn'] }
  | { name: 'return_confirm'; body: components['schemas']['ConfirmIn'] }
  | { name: 'raise_dispute'; body: components['schemas']['DisputeIn'] }
  | { name: 'withdraw_dispute' };

/** One mutation for every state-changing button; the backend decides what is allowed. */
export function useAction(id: string) {
  const qc = useQueryClient();
  const path = { params: { path: { txn_id: id } } };
  return useMutation({
    mutationFn: async (action: Action): Promise<CommandResult> => {
      switch (action.name) {
        case 'accept':
          return unwrap(await api.POST(`${A}/requests/{txn_id}/accept`, path));
        case 'decline':
          return unwrap(
            await api.POST(`${A}/requests/{txn_id}/decline`, {
              ...path,
              body: { reason: action.reason },
            }),
          );
        case 'cancel':
          return unwrap(await api.POST(`${A}/requests/{txn_id}/cancel`, path));
        case 'handover_checklist':
          return unwrap(
            await api.POST(`${A}/transactions/{txn_id}/handover/checklist`, {
              ...path,
              body: action.body,
            }),
          );
        case 'handover_confirm':
          return unwrap(
            await api.POST(`${A}/transactions/{txn_id}/handover/confirm`, {
              ...path,
              body: action.body,
            }),
          );
        case 'initiate_return':
          return unwrap(await api.POST(`${A}/transactions/{txn_id}/return`, path));
        case 'return_checklist':
        case 'return_confirm':
          return unwrap(
            await api.POST(`${A}/transactions/{txn_id}/return/confirm`, {
              ...path,
              body: action.body,
            }),
          );
        case 'raise_dispute':
          return unwrap(
            await api.POST(`${A}/transactions/{txn_id}/dispute`, { ...path, body: action.body }),
          );
        case 'withdraw_dispute':
          return unwrap(await api.POST(`${A}/transactions/{txn_id}/dispute/withdraw`, path));
      }
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['request', id] });
      qc.invalidateQueries({ queryKey: ['events', id] });
      qc.invalidateQueries({ queryKey: ['requests'] });
      qc.invalidateQueries({ queryKey: ['dispute', id] });
    },
  });
}

// ---------------------------------------------------------------- disputes (W5) and moderation (W6, W7)

/** The dispute case and its evidence trail for a party; disabled until a case may exist. */
export const useDisputeTrail = (id: string, enabled: boolean) =>
  useQuery({
    queryKey: ['dispute', id],
    enabled,
    queryFn: async () =>
      unwrap(await api.GET(`${A}/transactions/{txn_id}/dispute`, { params: { path: { txn_id: id } } })),
  });

export const useModerationQueue = () =>
  useQuery({
    queryKey: ['moderation'],
    queryFn: async () => unwrap(await api.GET(`${A}/moderation/cases`)),
  });

export const useModeratorCase = (caseId: string) =>
  useQuery({
    queryKey: ['moderation', caseId],
    queryFn: async () =>
      unwrap(
        await api.GET(`${A}/moderation/cases/{case_id}`, { params: { path: { case_id: caseId } } }),
      ),
  });

export function useDecide(caseId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: DecisionIn): Promise<CommandResult> =>
      unwrap(
        await api.POST(`${A}/moderation/cases/{case_id}/decision`, {
          params: { path: { case_id: caseId } },
          body,
        }),
      ),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['moderation'] });
    },
  });
}

