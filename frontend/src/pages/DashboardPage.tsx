import { isAxiosError } from "axios";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  getDashboardReport,
  listReportColleges,
  listReportDepartments,
  type DashboardReport as DashboardReportData,
  type OrganizationOption,
  type ReportFilters,
} from "../services/reports";

const REPORT_ROLES = ["ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"];

function errorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "The dashboard could not be loaded.";
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
    </article>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const canViewReports = REPORT_ROLES.includes(user?.role ?? "");
  const canFilterOrganization =
    user?.role === "ULMD_ADMIN" ||
    (user?.role === "AUDITOR" && user.department_id === null);
  const [report, setReport] = useState<DashboardReportData | null>(null);
  const [colleges, setColleges] = useState<OrganizationOption[]>([]);
  const [departments, setDepartments] = useState<OrganizationOption[]>([]);
  const [collegeId, setCollegeId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [withinDays, setWithinDays] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!canFilterOrganization) return;
    let active = true;
    async function loadOptions() {
      try {
        const [collegeOptions, departmentOptions] = await Promise.all([
          listReportColleges(),
          listReportDepartments(),
        ]);
        if (active) {
          setColleges(collegeOptions);
          setDepartments(departmentOptions);
        }
      } catch (loadError: unknown) {
        if (active) setError(errorMessage(loadError));
      }
    }
    void loadOptions();
    return () => {
      active = false;
    };
  }, [canFilterOrganization]);

  async function loadDashboard(filters: ReportFilters) {
    setLoading(true);
    setError("");
    try {
      setReport(await getDashboardReport(filters));
    } catch (loadError: unknown) {
      setError(errorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  async function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const days = Number(withinDays);
    if (!Number.isInteger(days) || days < 0) {
      setError("Enter a non-negative whole-number calibration due horizon.");
      return;
    }
    if (Boolean(dateFrom) !== Boolean(dateTo)) {
      setError("Select both dates to calculate a period-based report.");
      return;
    }
    await loadDashboard({
      within_days: days,
      college_id: collegeId || undefined,
      department_id: departmentId || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    });
  }

  function updateCollege(value: string) {
    setCollegeId(value);
    setDepartmentId("");
    void listReportDepartments(value || undefined)
      .then(setDepartments)
      .catch((loadError: unknown) => setError(errorMessage(loadError)));
  }

  if (!canViewReports) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
          Laboratory asset management
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-900">
          Welcome, {user?.full_name}
        </h1>
        <p className="mt-3 leading-7 text-slate-600">
          Your account is authenticated as {user?.role}. Operational reports
          are available to ULMD Administrators, scoped Lab Managers, and
          Auditors.
        </p>
      </section>
    );
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
            Operational overview
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">
            Laboratory dashboard
          </h1>
        </div>
        <p className="text-sm text-slate-600">Welcome, {user?.full_name}</p>
      </div>

      <form
        onSubmit={(event) => void applyFilters(event)}
        className="mt-6 grid gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-6"
      >
        {canFilterOrganization && (
          <>
            <label className="text-sm font-medium text-slate-700">
              College
              <select
                value={collegeId}
                onChange={(event) => updateCollege(event.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              >
                <option value="">All in my scope</option>
                {colleges.map((college) => (
                  <option key={college.id} value={college.id}>{college.name}</option>
                ))}
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700">
              Department
              <select
                value={departmentId}
                onChange={(event) => setDepartmentId(event.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              >
                <option value="">All in selected college</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>{department.name}</option>
                ))}
              </select>
            </label>
          </>
        )}
        <label className="text-sm font-medium text-slate-700">
          From
          <input
            type="date"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          To
          <input
            type="date"
            value={dateTo}
            onChange={(event) => setDateTo(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Calibration due horizon (days)
          <input
            required
            type="number"
            min="0"
            step="1"
            value={withinDays}
            onChange={(event) => setWithinDays(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="self-end rounded bg-university-700 px-4 py-2 font-semibold text-white hover:bg-university-800 disabled:opacity-60"
        >
          Apply filters
        </button>
      </form>

      {error && (
        <p role="alert" className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </p>
      )}
      {loading && <p className="mt-6 text-slate-600">Loading dashboard…</p>}
      {!loading && !report && !error && (
        <p className="mt-6 text-slate-600">Choose a calibration due horizon and apply the filters to load the dashboard.</p>
      )}
      {!loading && report && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Total assets" value={report.asset_total} />
            <MetricCard label="Operational assets" value={report.operational_assets} />
            <MetricCard label="Active work orders" value={report.active_work_orders} />
            <MetricCard label="Completed work orders" value={report.work_orders_completed} />
            <MetricCard label="Overdue calibrations" value={report.overdue_calibrations} />
            <MetricCard label="Due within selected horizon" value={report.upcoming_calibrations} />
            <MetricCard
              label="Fleet availability"
              value={report.uptime_percentage === null ? "Pending definition" : `${report.uptime_percentage.toFixed(1)}%`}
            />
            <MetricCard
              label="Recorded downtime"
              value={report.downtime_asset_hours === null ? "Pending definition" : `${report.downtime_asset_hours.toFixed(1)} asset hours`}
            />
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Assets by operational status</h2>
              {report.assets_by_status.length === 0 ? (
                <p className="mt-3 text-sm text-slate-600">No assets in this scope.</p>
              ) : (
                <ul className="mt-3 space-y-2">
                  {report.assets_by_status.map((item) => (
                    <li key={item.name} className="flex justify-between text-sm">
                      <span>{item.name.replace(/_/g, " ")}</span><strong>{item.count}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Assets by category</h2>
              {report.assets_by_category.length === 0 ? (
                <p className="mt-3 text-sm text-slate-600">No assets in this scope.</p>
              ) : (
                <ul className="mt-3 space-y-2">
                  {report.assets_by_category.map((item) => (
                    <li key={item.name} className="flex justify-between text-sm">
                      <span>{item.name}</span><strong>{item.count}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Critical work orders</h2>
              {report.critical_work_orders.length === 0 ? (
                <p className="mt-3 text-sm text-slate-600">No open critical work orders.</p>
              ) : (
                <ul className="mt-3 divide-y divide-slate-100">
                  {report.critical_work_orders.map((item) => (
                    <li key={item.id} className="py-3 text-sm">
                      <strong>{item.ticket_number}</strong> · {item.asset_code}
                      <p className="text-slate-600">{item.laboratory_name} · {item.status.replace(/_/g, " ")}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Calibration due queue</h2>
              {[...report.overdue_calibration_items, ...report.upcoming_calibration_items].length === 0 ? (
                <p className="mt-3 text-sm text-slate-600">No overdue or upcoming calibrations in this scope.</p>
              ) : (
                <ul className="mt-3 divide-y divide-slate-100">
                  {[...report.overdue_calibration_items, ...report.upcoming_calibration_items].map((item) => (
                    <li key={item.asset_id} className="py-3 text-sm">
                      <strong>{item.asset_code}</strong> · {item.model_number}
                      <p className="text-slate-600">
                        {item.status} · due {item.next_calibration_due} · {item.laboratory_name} / {item.room_number}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </section>
  );
}
