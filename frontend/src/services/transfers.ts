import api from "./api";
import type { Page } from "./assets";

export type TransferStatus =
  | "PENDING_RECEIVER"
  | "PENDING_ULMD"
  | "COMPLETED"
  | "REJECTED";

export interface TransferStatusEvent {
  action: string;
  actor_id: string | null;
  actor_name: string | null;
  old_status: TransferStatus | null;
  new_status: TransferStatus;
  notes: string | null;
  occurred_at: string;
}

export interface AssetTransfer {
  id: string;
  asset_id: string;
  asset_code: string;
  origin_laboratory_id: string;
  origin_laboratory_name: string;
  origin_room_id: string;
  origin_room_number: string;
  origin_building_name: string;
  target_laboratory_id: string;
  target_laboratory_name: string;
  target_room_id: string;
  target_room_number: string;
  target_building_name: string;
  initiated_by: string;
  initiator_name: string;
  accepted_by: string | null;
  accepter_name: string | null;
  approved_by_ulmd: string | null;
  approver_name: string | null;
  status: TransferStatus;
  transfer_reason: string;
  notes: string | null;
  created_at: string;
  completed_at: string | null;
  status_history: TransferStatusEvent[];
}

export interface TransferFilters {
  page: number;
  size: number;
  status?: TransferStatus;
  asset_id?: string;
}

export async function listTransfers(
  filters: TransferFilters,
): Promise<Page<AssetTransfer>> {
  const { data } = await api.get<Page<AssetTransfer>>("/api/v1/transfers", {
    params: filters,
  });
  return data;
}

export async function createTransfer(input: {
  asset_id: string;
  target_laboratory_id: string;
  target_room_id: string;
  transfer_reason: string;
}): Promise<AssetTransfer> {
  const { data } = await api.post<AssetTransfer>("/api/v1/transfers", input);
  return data;
}

export async function acceptTransfer(
  id: string,
  notes?: string,
): Promise<AssetTransfer> {
  const { data } = await api.put<AssetTransfer>(
    `/api/v1/transfers/${id}/accept`,
    { notes: notes || null },
  );
  return data;
}

export async function rejectTransfer(
  id: string,
  notes: string,
): Promise<AssetTransfer> {
  const { data } = await api.put<AssetTransfer>(
    `/api/v1/transfers/${id}/reject`,
    { notes },
  );
  return data;
}

export async function approveTransfer(id: string): Promise<AssetTransfer> {
  const { data } = await api.put<AssetTransfer>(
    `/api/v1/transfers/${id}/approve`,
  );
  return data;
}
