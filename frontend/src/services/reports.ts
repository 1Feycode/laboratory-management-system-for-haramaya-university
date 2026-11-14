import api from "./api";

export interface ReportFilters {
  college_id?: string;
  department_id?: string;
  date_from?: string;
  date_to?: string;
  within_days?: number;
  status?: string;
}

export interface OrganizationOption {
  id: string;
  name: string;
  college_id?: string;
}

interface OrganizationPage<T> {
  items: T[];
}

export interface CountByName {
  name: string;
  count: number;
}

export interface CalibrationDueItem {
  asset_id: string;
  asset_code: string;
  model_number: string;
  category_name: string;
  college_name: string;
  department_name: string;
  laboratory_name: string;
  room_number: string;
  next_calibration_due: string;
  status: "UPCOMING" | "OVERDUE";
}

export interface CriticalWorkOrderItem {
  id: string;
  ticket_number: string;
  asset_code: string;
  college_name: string;
  department_name: string;
  laboratory_name: string;
  severity: string;
  status: string;
  created_at: string;
}

export interface CollegeMaintenanceSummary {
  college_id: string;
  college_name: string;
  work_order_requests: number;
  work_orders_completed: number;
  active_work_orders: number;
}

export interface DashboardReport {
  asset_total: number;
  operational_assets: number;
  assets_by_category: CountByName[];
  assets_by_status: CountByName[];
  work_order_total: number;
  active_work_orders: number;
  work_orders_completed: number;
  work_orders_by_status: CountByName[];
  calibration_records: number;
  calibrations_passed: number;
  calibrations_failed: number;
  overdue_calibrations: number;
  upcoming_calibrations: number;
  upcoming_calibration_items: CalibrationDueItem[];
  overdue_calibration_items: CalibrationDueItem[];
  critical_work_orders: CriticalWorkOrderItem[];
  availability_status: string;
  uptime_percentage: number | null;
  downtime_asset_hours: number | null;
}

export interface DowntimeReport {
  date_from: string;
  date_to: string;
  availability_status: string;
  asset_total: number;
  uptime_percentage: number | null;
  downtime_asset_hours: number | null;
  work_order_requests: number;
  work_orders_completed: number;
  active_work_orders: number;
  work_orders_by_status: CountByName[];
  by_college: CollegeMaintenanceSummary[];
}

export interface CalibrationComplianceReport {
  assets_requiring_calibration: number;
  overdue_calibrations: number;
  upcoming_calibrations: number;
  calibration_records: number;
  calibrations_passed: number;
  calibrations_failed: number;
  overdue_items: CalibrationDueItem[];
  upcoming_items: CalibrationDueItem[];
}

export async function listReportColleges(): Promise<OrganizationOption[]> {
  const { data } = await api.get<OrganizationPage<OrganizationOption>>(
    "/api/v1/hierarchy/colleges",
    { params: { page: 1, size: 100 } },
  );
  return data.items;
}

export async function listReportDepartments(
  collegeId?: string,
): Promise<OrganizationOption[]> {
  const { data } = await api.get<OrganizationPage<OrganizationOption>>(
    "/api/v1/hierarchy/departments",
    { params: { page: 1, size: 100, college_id: collegeId } },
  );
  return data.items;
}

export async function getDashboardReport(
  filters: ReportFilters,
): Promise<DashboardReport> {
  const { data } = await api.get<DashboardReport>("/api/v1/reports/dashboard", {
    params: filters,
  });
  return data;
}

export async function getDowntimeReport(
  filters: ReportFilters & { date_from: string; date_to: string },
): Promise<DowntimeReport> {
  const { data } = await api.get<DowntimeReport>("/api/v1/reports/downtime", {
    params: filters,
  });
  return data;
}

export async function getCalibrationComplianceReport(
  filters: ReportFilters,
): Promise<CalibrationComplianceReport> {
  const { data } = await api.get<CalibrationComplianceReport>(
    "/api/v1/reports/calibration-compliance",
    { params: filters },
  );
  return data;
}

export async function downloadInventoryCsv(
  filters: ReportFilters,
): Promise<Blob> {
  const { data } = await api.get<Blob>("/api/v1/reports/inventory", {
    params: filters,
    responseType: "blob",
  });
  return data;
}
