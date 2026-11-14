import api from "./api";
import type { Page } from "./assets";

export interface Calibration {
  id: string;
  asset_id: string;
  asset_code: string;
  technician_id: string;
  technician_name: string;
  calibration_date: string;
  standard_used: string;
  certificate_reference: string | null;
  accreditation_body: string | null;
  passed: boolean;
  next_due_date: string;
  notes: string | null;
  created_at: string;
}

export interface CalibrationDue {
  asset_id: string;
  asset_code: string;
  model_number: string;
  manufacturer_name: string;
  category_name: string;
  laboratory_name: string;
  room_number: string;
  last_calibrated_date: string | null;
  next_calibration_due: string;
  status: "UPCOMING" | "OVERDUE";
}

export interface CalibrationInput {
  asset_id: string;
  calibration_date: string;
  standard_used: string;
  certificate_reference?: string | null;
  accreditation_body?: string | null;
  passed: boolean;
  notes?: string | null;
}

export async function listCalibrations(
  page: number,
  size = 20,
): Promise<Page<Calibration>> {
  const { data } = await api.get<Page<Calibration>>("/api/v1/calibrations", {
    params: { page, size },
  });
  return data;
}

export async function listDueCalibrations(
  withinDays: number,
  page: number,
  size = 20,
): Promise<Page<CalibrationDue>> {
  const { data } = await api.get<Page<CalibrationDue>>(
    "/api/v1/calibrations/due",
    { params: { within_days: withinDays, page, size } },
  );
  return data;
}

export async function createCalibration(
  input: CalibrationInput,
): Promise<Calibration> {
  const { data } = await api.post<Calibration>(
    "/api/v1/calibrations",
    input,
  );
  return data;
}
