import api from "./api";

export type AssetStatus =
  | "OPERATIONAL"
  | "UNDER_MAINTENANCE"
  | "DEFECTIVE"
  | "TRANSFER_PENDING"
  | "DECOMMISSIONED";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AssetCategory {
  id: string;
  name: string;
  requires_calibration: boolean;
  default_calibration_interval_days: number;
  created_at: string;
}

export interface Asset {
  id: string;
  asset_code: string;
  legacy_tag_number: string | null;
  serial_number: string;
  model_number: string;
  manufacturer_name: string;
  category_id: string;
  category_name: string;
  requires_calibration: boolean;
  default_calibration_interval_days: number;
  laboratory_id: string;
  laboratory_name: string;
  room_id: string;
  room_number: string;
  building_name: string;
  department_id: string;
  department_name: string;
  college_id: string;
  college_name: string;
  operational_status: AssetStatus;
  purchase_date: string | null;
  commissioning_date: string | null;
  warranty_expiry_date: string | null;
  last_calibrated_date: string | null;
  next_calibration_due: string | null;
  calibration_overdue: boolean;
  qr_code_url: string;
  created_at: string;
  updated_at: string;
}

export interface AssetInput {
  legacy_tag_number?: string | null;
  serial_number: string;
  model_number: string;
  manufacturer_name: string;
  category_id: string;
  laboratory_id: string;
  room_id: string;
  purchase_date?: string | null;
  commissioning_date?: string | null;
  warranty_expiry_date?: string | null;
}

export interface AssetUpdateInput {
  legacy_tag_number?: string | null;
  serial_number?: string;
  model_number?: string;
  manufacturer_name?: string;
  category_id?: string;
  purchase_date?: string | null;
  commissioning_date?: string | null;
  warranty_expiry_date?: string | null;
}

export interface AssetFilters {
  page: number;
  size: number;
  search?: string;
  college_id?: string;
  department_id?: string;
  laboratory_id?: string;
  category_id?: string;
  status?: AssetStatus;
  sort_by: "asset_code" | "created_at" | "model_number" | "operational_status" | "purchase_date";
  sort_order: "asc" | "desc";
}

export async function listAssets(filters: AssetFilters): Promise<Page<Asset>> {
  const { data } = await api.get<Page<Asset>>("/api/v1/assets", { params: filters });
  return data;
}

export async function listCategories(
  search?: string,
  page = 1,
  size = 20,
): Promise<Page<AssetCategory>> {
  const { data } = await api.get<Page<AssetCategory>>("/api/v1/asset-categories", {
    params: { page, size, search: search || undefined },
  });
  return data;
}

async function fetchAllPages<T>(path: string): Promise<T[]> {
  const first = await api.get<Page<T>>(path, { params: { page: 1, size: 100 } });
  const items = [...first.data.items];
  for (let page = 2; page <= first.data.pages; page += 1) {
    const { data } = await api.get<Page<T>>(path, {
      params: { page, size: 100 },
    });
    items.push(...data.items);
  }
  return items;
}

export async function listAllCategories(): Promise<AssetCategory[]> {
  return fetchAllPages<AssetCategory>("/api/v1/asset-categories");
}

export async function createCategory(input: {
  name: string;
  requires_calibration: boolean;
  default_calibration_interval_days: number;
}): Promise<AssetCategory> {
  const { data } = await api.post<AssetCategory>("/api/v1/asset-categories", input);
  return data;
}

export async function updateCategory(
  id: string,
  input: Partial<Pick<AssetCategory, "name" | "requires_calibration" | "default_calibration_interval_days">>,
): Promise<AssetCategory> {
  const { data } = await api.patch<AssetCategory>(`/api/v1/asset-categories/${id}`, input);
  return data;
}

export async function deleteCategory(id: string): Promise<void> {
  await api.delete(`/api/v1/asset-categories/${id}`);
}

export async function getAsset(id: string): Promise<Asset> {
  const { data } = await api.get<Asset>(`/api/v1/assets/${id}`);
  return data;
}

export async function lookupAsset(assetCode: string): Promise<Asset> {
  const { data } = await api.get<Asset>(
    `/api/v1/assets/lookup/${encodeURIComponent(assetCode)}`,
  );
  return data;
}

export function assetCodeFromQrPayload(payload: string): string {
  const value = payload.trim();
  if (!/^https?:\/\//i.test(value)) return value;

  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error("The QR code does not contain a valid asset link.");
  }
  if (url.pathname.replace(/\/$/, "") !== "/assets/scan") {
    throw new Error("The QR code does not contain a supported asset link.");
  }
  const assetCode = url.searchParams.get("code")?.trim();
  if (!assetCode) {
    throw new Error("The asset link does not include an asset code.");
  }
  return assetCode;
}

export async function createAsset(input: AssetInput): Promise<Asset> {
  const { data } = await api.post<Asset>("/api/v1/assets", input);
  return data;
}

export async function updateAsset(
  id: string,
  input: AssetUpdateInput,
): Promise<Asset> {
  const { data } = await api.patch<Asset>(`/api/v1/assets/${id}`, input);
  return data;
}

export async function getAssetQr(id: string): Promise<Blob> {
  const { data } = await api.get<Blob>(`/api/v1/assets/${id}/qr`, {
    responseType: "blob",
  });
  return data;
}

export interface CollegeOption {
  id: string;
  name: string;
}

export interface DepartmentOption {
  id: string;
  college_id: string;
  name: string;
  code: string;
}

export interface LaboratoryOption {
  id: string;
  department_id: string;
  department_name: string;
  college_name: string;
  name: string;
  manager_id: string | null;
}

export interface RoomOption {
  id: string;
  laboratory_id: string;
  room_number: string;
  building_name: string;
}

export async function listLocationOptions() {
  const [colleges, departments, laboratories, rooms] = await Promise.all([
    fetchAllPages<CollegeOption>("/api/v1/hierarchy/colleges"),
    fetchAllPages<DepartmentOption>("/api/v1/hierarchy/departments"),
    fetchAllPages<LaboratoryOption>("/api/v1/hierarchy/laboratories"),
    fetchAllPages<RoomOption>("/api/v1/hierarchy/rooms"),
  ]);
  return { colleges, departments, laboratories, rooms };
}
