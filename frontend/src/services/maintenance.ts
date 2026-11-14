import api from "./api";
import type { Page } from "./assets";

export type WorkOrderStatus =
  | "OPEN"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "AWAITING_PARTS"
  | "RESOLVED"
  | "CLOSED";
export type WorkOrderSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type FailureCategory =
  | "ELECTRICAL"
  | "MECHANICAL"
  | "OPTICAL"
  | "SOFTWARE"
  | "CONSUMABLE"
  | "OTHER";
export type MaintenanceOutcome =
  | "OPERATIONAL"
  | "REPAIRED_DEGRADED"
  | "UNREPAIRABLE";

export interface MaintenanceLog {
  id: string;
  work_order_id: string;
  technician_id: string;
  technician_name: string;
  actions_taken: string;
  spare_parts_used: string | null;
  labor_hours: number;
  outcome_condition: MaintenanceOutcome;
  created_at: string;
}

export interface WorkOrderStatusEvent {
  action: string;
  actor_id: string | null;
  actor_name: string | null;
  old_status: WorkOrderStatus | null;
  new_status: WorkOrderStatus;
  old_assignee_id: string | null;
  new_assignee_id: string | null;
  notes: string | null;
  occurred_at: string;
}

export interface WorkOrder {
  id: string;
  ticket_number: string;
  asset_id: string;
  asset_code: string;
  asset_model_number: string;
  asset_manufacturer_name: string;
  laboratory_id: string;
  laboratory_name: string;
  reported_by: string;
  reporter_name: string;
  assigned_to: string | null;
  assignee_name: string | null;
  severity: WorkOrderSeverity;
  failure_category: FailureCategory;
  status: WorkOrderStatus;
  fault_description: string;
  verified_by: string | null;
  verifier_name: string | null;
  verification_notes: string | null;
  created_at: string;
  resolved_at: string | null;
  closed_at: string | null;
  maintenance_logs: MaintenanceLog[];
  status_history: WorkOrderStatusEvent[];
}

export interface WorkOrderFilters {
  page: number;
  size: number;
  status?: WorkOrderStatus;
  severity?: WorkOrderSeverity;
  asset_id?: string;
}

export async function listWorkOrders(
  filters: WorkOrderFilters,
): Promise<Page<WorkOrder>> {
  const { data } = await api.get<Page<WorkOrder>>("/api/v1/work-orders", {
    params: filters,
  });
  return data;
}

export async function createWorkOrder(input: {
  asset_id: string;
  severity: WorkOrderSeverity;
  failure_category: FailureCategory;
  fault_description: string;
}): Promise<WorkOrder> {
  const { data } = await api.post<WorkOrder>("/api/v1/work-orders", input);
  return data;
}

export async function assignWorkOrder(
  id: string,
  assigned_to: string,
): Promise<WorkOrder> {
  const { data } = await api.put<WorkOrder>(`/api/v1/work-orders/${id}/assign`, {
    assigned_to,
  });
  return data;
}

export async function updateWorkOrderStatus(
  id: string,
  status: "IN_PROGRESS" | "AWAITING_PARTS",
): Promise<WorkOrder> {
  const { data } = await api.put<WorkOrder>(
    `/api/v1/work-orders/${id}/status`,
    { status },
  );
  return data;
}

export async function addMaintenanceLog(
  id: string,
  input: {
    actions_taken: string;
    spare_parts_used: string | null;
    labor_hours: number;
    outcome_condition: MaintenanceOutcome;
  },
): Promise<WorkOrder> {
  const { data } = await api.post<WorkOrder>(
    `/api/v1/work-orders/${id}/logs`,
    input,
  );
  return data;
}

export async function verifyWorkOrder(
  id: string,
  input: { confirmed: boolean; verification_notes: string },
): Promise<WorkOrder> {
  const { data } = await api.put<WorkOrder>(
    `/api/v1/work-orders/${id}/close`,
    input,
  );
  return data;
}
