import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api, unwrap } from './client';
import type { components } from './schema';

export type RequestDetail = components['schemas']['RequestOut'];
export type MyRequest = components['schemas']['MyRequestOut'];
export type BrowseItem = components['schemas']['BrowseItemOut'];
export type CommandResult = components['schemas']['CommandOut'];
export type Assessment = components['schemas']['AssessmentOut'];
export type Report = components['schemas']['ReportOut'];

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
  | { name: 'return_confirm'; body: components['schemas']['ConfirmIn'] };

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
      }
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['request', id] });
      qc.invalidateQueries({ queryKey: ['events', id] });
      qc.invalidateQueries({ queryKey: ['requests'] });
    },
  });
}
