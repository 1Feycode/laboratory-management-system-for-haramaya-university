import { isAxiosError } from "axios";
import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  listAssets,
  listAllCategories,
  listLocationOptions,
  lookupAsset,
  type Asset,
  type AssetCategory,
  type AssetStatus,
  type CollegeOption,
  type DepartmentOption,
  type LaboratoryOption,
  type Page,
} from "../services/assets";

const AssetQrScanner = lazy(() => import("../components/assets/AssetQrScanner"));

const STATUSES: AssetStatus[] = [
  "OPERATIONAL",
  "UNDER_MAINTENANCE",
  "DEFECTIVE",
  "TRANSFER_PENDING",
  "DECOMMISSIONED",
];

function messageFromError(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "The asset request failed.";
}

function statusStyle(status: AssetStatus): string {
  if (status === "OPERATIONAL") return "bg-green-100 text-green-800";
  if (status === "DEFECTIVE") return "bg-red-100 text-red-800";
  if (status === "UNDER_MAINTENANCE") return "bg-amber-100 text-amber-800";
  return "bg-slate-100 text-slate-800";
}

export default function AssetListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canRegister = user?.role === "ULMD_ADMIN" || user?.role === "LAB_MANAGER";
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [collegeId, setCollegeId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [laboratoryId, setLaboratoryId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [status, setStatus] = useState<AssetStatus | "">("");
  const [sortBy, setSortBy] = useState<
    "asset_code" | "created_at" | "model_number" | "operational_status" | "purchase_date"
  >("asset_code");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [result, setResult] = useState<Page<Asset>>({
    items: [],
    total: 0,
    page: 1,
    size: 20,
    pages: 0,
  });
  const [colleges, setColleges] = useState<CollegeOption[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [laboratories, setLaboratories] = useState<LaboratoryOption[]>([]);
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [scannerOpen, setScannerOpen] = useState(false);

  useEffect(() => {
    let active = true;
    void Promise.all([listLocationOptions(), listAllCategories()])
      .then(([locations, loadedCategories]) => {
        if (!active) return;
        setColleges(locations.colleges);
        setDepartments(locations.departments);
        setLaboratories(locations.laboratories);
        setCategories(loadedCategories);
      })
      .catch((cause: unknown) => {
        if (active) setError(messageFromError(cause));
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const term = searchInput.trim();
      if (term !== search) {
        setPage(1);
        setSearch(term);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchInput, search]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    void listAssets({
      page,
      size: 20,
      search: search || undefined,
      college_id: collegeId || undefined,
      department_id: departmentId || undefined,
      laboratory_id: laboratoryId || undefined,
      category_id: categoryId || undefined,
      status,
      sort_by: sortBy,
      sort_order: sortOrder,
    })
      .then((data) => {
        if (active) setResult(data);
      })
      .catch((cause: unknown) => {
        if (active) setError(messageFromError(cause));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [
    page,
    search,
    collegeId,
    departmentId,
    laboratoryId,
    categoryId,
    status,
    sortBy,
    sortOrder,
  ]);

  const onScanned = useCallback(
    (assetCode: string) => {
      setScannerOpen(false);
      void lookupAsset(assetCode)
        .then((asset) => navigate(`/assets/${asset.id}`))
        .catch((cause: unknown) => setError(messageFromError(cause)));
    },
    [navigate],
  );

  const filteredDepartments = departments.filter(
    (department) => !collegeId || department.college_id === collegeId,
  );
  const filteredLaboratories = laboratories.filter(
    (laboratory) =>
      (!collegeId ||
        departments.some(
          (department) =>
            department.id === laboratory.department_id &&
            department.college_id === collegeId,
        )) &&
      (!departmentId || laboratory.department_id === departmentId),
  );
  return (
    <section>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Laboratory assets</h1>
          <p className="mt-2 text-slate-600">
            Search and review registered durable laboratory equipment.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
            onClick={() => setScannerOpen(true)}
          >
            Scan QR code
          </button>
          {canRegister && (
            <Link
              className="rounded bg-university-700 px-4 py-2 text-sm font-medium text-white hover:bg-university-800"
              to="/assets/register"
            >
              Register asset
            </Link>
          )}
          {user?.role === "ULMD_ADMIN" && (
            <Link
              className="rounded border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
              to="/admin/asset-categories"
            >
              Categories
            </Link>
          )}
        </div>
      </div>

      <form
        className="mt-7 grid gap-3 rounded-xl border border-slate-200 bg-white p-4 md:grid-cols-3 lg:grid-cols-4"
        onSubmit={(event) => {
          event.preventDefault();
          setPage(1);
          setSearch(searchInput.trim());
        }}
      >
        <label className="text-sm text-slate-700 md:col-span-2">
          Search assets
          <input
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Asset code, serial, model, manufacturer, or legacy tag"
          />
        </label>
        <label className="text-sm text-slate-700">
          College
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={collegeId}
            onChange={(event) => {
              setCollegeId(event.target.value);
              setDepartmentId("");
              setLaboratoryId("");
              setPage(1);
            }}
          >
            <option value="">All colleges</option>
            {colleges.map((college) => (
              <option key={college.id} value={college.id}>{college.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm text-slate-700">
          Department
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={departmentId}
            onChange={(event) => {
              setDepartmentId(event.target.value);
              setLaboratoryId("");
              setPage(1);
            }}
          >
            <option value="">All departments</option>
            {filteredDepartments.map((department) => (
              <option key={department.id} value={department.id}>{department.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm text-slate-700">
          Laboratory
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={laboratoryId}
            onChange={(event) => {
              setLaboratoryId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All laboratories</option>
            {filteredLaboratories.map((laboratory) => (
              <option key={laboratory.id} value={laboratory.id}>{laboratory.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm text-slate-700">
          Category
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={categoryId}
            onChange={(event) => {
              setCategoryId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm text-slate-700">
          Status
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value as AssetStatus | "");
              setPage(1);
            }}
          >
            <option value="">All statuses</option>
            {STATUSES.map((value) => <option key={value} value={value}>{value.replace(/_/g, " ")}</option>)}
          </select>
        </label>
        <label className="text-sm text-slate-700">
          Sort by
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={`${sortBy}:${sortOrder}`}
            onChange={(event) => {
              const [field, order] = event.target.value.split(":");
              setSortBy(field as typeof sortBy);
              setSortOrder(order as typeof sortOrder);
              setPage(1);
            }}
          >
            <option value="asset_code:asc">Asset code (A–Z)</option>
            <option value="asset_code:desc">Asset code (Z–A)</option>
            <option value="created_at:desc">Recently added</option>
            <option value="model_number:asc">Model (A–Z)</option>
            <option value="operational_status:asc">Status</option>
          </select>
        </label>
        <button
          className="self-end rounded bg-slate-100 px-4 py-2 text-sm font-medium hover:bg-slate-200"
          type="submit"
        >
          Apply search
        </button>
      </form>

      {error && (
        <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-sm text-red-800">
          {error}
        </p>
      )}
      <div className="mt-5 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Asset code</th>
              <th className="px-4 py-3 font-medium">Model / manufacturer</th>
              <th className="px-4 py-3 font-medium">Category</th>
              <th className="px-4 py-3 font-medium">Custodian location</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr><td className="px-4 py-8 text-slate-500" colSpan={5}>Loading assets…</td></tr>
            ) : result.items.length === 0 ? (
              <tr>
                <td className="px-4 py-8 text-slate-500" colSpan={5}>
                  No assets found. Create asset categories and organizational locations before registering equipment.
                </td>
              </tr>
            ) : result.items.map((asset) => (
              <tr
                key={asset.id}
                className="cursor-pointer hover:bg-slate-50"
                onClick={() => navigate(`/assets/${asset.id}`)}
              >
                <td className="px-4 py-3 font-medium text-university-800">{asset.asset_code}</td>
                <td className="px-4 py-3">
                  <div>{asset.model_number}</div>
                  <div className="text-xs text-slate-500">{asset.manufacturer_name} · S/N {asset.serial_number}</div>
                </td>
                <td className="px-4 py-3">{asset.category_name}</td>
                <td className="px-4 py-3">
                  {asset.college_name} / {asset.department_name}<br />
                  <span className="text-xs text-slate-500">
                    {asset.laboratory_name} · {asset.building_name}, room {asset.room_number}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusStyle(asset.operational_status)}`}>
                    {asset.operational_status.replace(/_/g, " ")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
        <span>{result.total} asset{result.total === 1 ? "" : "s"}</span>
        <div className="flex items-center gap-3">
          <button
            className="rounded border border-slate-300 px-3 py-1.5 disabled:opacity-40"
            disabled={page <= 1 || loading}
            onClick={() => setPage((current) => current - 1)}
            type="button"
          >
            Previous
          </button>
          <span>Page {result.page} of {Math.max(result.pages, 1)}</span>
          <button
            className="rounded border border-slate-300 px-3 py-1.5 disabled:opacity-40"
            disabled={page >= result.pages || loading}
            onClick={() => setPage((current) => current + 1)}
            type="button"
          >
            Next
          </button>
        </div>
      </div>
      {scannerOpen && (
        <Suspense fallback={<p className="sr-only">Loading QR scanner…</p>}>
          <AssetQrScanner
            onClose={() => setScannerOpen(false)}
            onScanned={onScanned}
          />
        </Suspense>
      )}
    </section>
  );
}
