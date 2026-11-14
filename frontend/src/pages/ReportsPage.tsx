import { isAxiosError } from "axios";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  downloadInventoryCsv,
  getDowntimeReport,
  getCalibrationComplianceReport,
  listReportColleges,
  listReportDepartments,
  type DowntimeReport,
  type CalibrationComplianceReport,
  type OrganizationOption,
  type ReportFilters,
} from "../services/reports";

function errorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    if (error.response?.data instanceof Blob) {
      return `The inventory export failed (HTTP ${error.response.status}).`;
    }
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "The report request failed.";
}

export default function ReportsPage() {
  const { user } = useAuth();
  const [colleges, setColleges] = useState<OrganizationOption[]>([]);
  const [departments, setDepartments] = useState<OrganizationOption[]>([]);
  const [collegeId, setCollegeId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [withinDays, setWithinDays] = useState("");
  const [status, setStatus] = useState("");
  const [report, setReport] = useState<DowntimeReport | null>(null);
  const [calibrationReport, setCalibrationReport] =
    useState<CalibrationComplianceReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const canExport = ["ULMD_ADMIN", "AUDITOR"].includes(user?.role ?? "");
  const canFilterOrganization =
    user?.role === "ULMD_ADMIN" ||
    (user?.role === "AUDITOR" && user.department_id === null);

  useEffect(() => {
    if (!canFilterOrganization) return;
    let active = true;
    Promise.all([listReportColleges(), listReportDepartments()])
      .then(([collegeOptions, departmentOptions]) => {
        if (active) {
          setColleges(collegeOptions);
          setDepartments(departmentOptions);
        }
      })
      .catch((loadError: unknown) => {
        if (active) setError(errorMessage(loadError));
      });
    return () => {
      active = false;
    };
  }, [canFilterOrganization]);

  function filters(): ReportFilters {
    return {
      college_id: collegeId || undefined,
      department_id: departmentId || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    };
  }

  async function runReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!dateFrom || !dateTo) {
      setError("Select both dates to run the downtime and maintenance report.");
      return;
    }
    const days = Number(withinDays);
    if (!Number.isInteger(days) || days < 0) {
      setError("Enter a non-negative whole-number calibration due horizon.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const reportFilters = {
        ...filters(),
        date_from: dateFrom,
        date_to: dateTo,
      };
      const [maintenance, calibration] = await Promise.all([
        getDowntimeReport(reportFilters),
        getCalibrationComplianceReport({
          ...reportFilters,
          within_days: days,
        }),
      ]);
      setReport(maintenance);
      setCalibrationReport(calibration);
    } catch (reportError: unknown) {
      setError(errorMessage(reportError));
    } finally {
      setLoading(false);
    }
  }

  async function exportInventory() {
    setError("");
    if (Boolean(dateFrom) !== Boolean(dateTo)) {
      setError("Select both dates or leave both empty for the inventory export.");
      return;
    }
    try {
      const file = await downloadInventoryCsv({
        ...filters(),
        status: status || undefined,
      });
      const url = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = url;
      link.download = "hu-laboratory-inventory.csv";
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (exportError: unknown) {
      setError(errorMessage(exportError));
    }
  }

  function updateCollege(value: string) {
    setCollegeId(value);
    setDepartmentId("");
    void listReportDepartments(value || undefined)
      .then(setDepartments)
      .catch((loadError: unknown) => setError(errorMessage(loadError)));
  }

  return (
    <section>
      <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
        Reports &amp; analytics
      </p>
      <h1 className="mt-2 text-3xl font-semibold text-slate-900">Operational reports</h1>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
        Report visibility follows your assigned role and organizational scope.
        Uptime and downtime values are withheld until their calculation rules
        are approved. Work-order counts and completion dates remain available.
      </p>

      <form
        onSubmit={(event) => void runReport(event)}
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
                {colleges.map((college) => <option key={college.id} value={college.id}>{college.name}</option>)}
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
                {departments.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}
              </select>
            </label>
          </>
        )}
        <label className="text-sm font-medium text-slate-700">
          From
          <input
            required
            type="date"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          To
          <input
            required
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
            min="0"
            step="1"
            type="number"
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
          {loading ? "Loading…" : "Run report"}
        </button>
        {canExport && (
          <div className="md:col-span-6">
            <label className="mr-3 text-sm font-medium text-slate-700">
              Inventory status
              <select
                value={status}
                onChange={(event) => setStatus(event.target.value)}
                className="ml-2 rounded border border-slate-300 px-3 py-2"
              >
                <option value="">All statuses</option>
                {["OPERATIONAL", "UNDER_MAINTENANCE", "DEFECTIVE", "TRANSFER_PENDING", "DECOMMISSIONED"].map((item) => (
                  <option key={item} value={item}>{item.replace(/_/g, " ")}</option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={() => void exportInventory()}
              className="rounded border border-university-700 px-4 py-2 text-sm font-semibold text-university-700 hover:bg-university-50"
            >
              Download inventory CSV
            </button>
          </div>
        )}
      </form>

      {error && <p role="alert" className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      {report && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Assets", report.asset_total],
              ["Uptime", report.uptime_percentage === null ? "Pending definition" : `${report.uptime_percentage.toFixed(1)}%`],
              ["Downtime", report.downtime_asset_hours === null ? "Pending definition" : `${report.downtime_asset_hours.toFixed(1)} asset hours`],
              ["Work-order requests", report.work_order_requests],
              ["Completed work orders", report.work_orders_completed],
              ["Active work orders", report.active_work_orders],
            ].map(([label, value]) => (
              <article key={label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm text-slate-600">{label}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
              </article>
            ))}
          </div>
          <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Maintenance activity by college</h2>
            {report.by_college.length === 0 ? (
              <p className="mt-3 text-sm text-slate-600">No work orders were reported in this period.</p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-200 text-slate-600">
                    <tr>
                      <th className="py-2 pr-4">College</th>
                      <th className="py-2 pr-4">Requests</th>
                      <th className="py-2 pr-4">Completed</th>
                      <th className="py-2">Active</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.by_college.map((row) => (
                      <tr key={row.college_id} className="border-b border-slate-100">
                        <td className="py-3 pr-4">{row.college_name}</td>
                        <td className="py-3 pr-4">{row.work_order_requests}</td>
                        <td className="py-3 pr-4">{row.work_orders_completed}</td>
                        <td className="py-3">{row.active_work_orders}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          {calibrationReport && (
            <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Calibration compliance</h2>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  ["Assets requiring calibration", calibrationReport.assets_requiring_calibration],
                  ["Overdue", calibrationReport.overdue_calibrations],
                  ["Upcoming in selected horizon", calibrationReport.upcoming_calibrations],
                  ["Calibration records in period", calibrationReport.calibration_records],
                  ["Passed", calibrationReport.calibrations_passed],
                  ["Failed", calibrationReport.calibrations_failed],
                ].map(([label, value]) => (
                  <div key={label} className="rounded border border-slate-100 p-3">
                    <p className="text-xs text-slate-600">{label}</p>
                    <p className="mt-1 text-xl font-semibold">{value}</p>
                  </div>
                ))}
              </div>
              <div className="mt-5 grid gap-6 lg:grid-cols-2">
                {[
                  {
                    title: "Overdue calibration assets",
                    items: calibrationReport.overdue_items,
                  },
                  {
                    title: "Upcoming calibration assets",
                    items: calibrationReport.upcoming_items,
                  },
                ].map(({ title, items }) => (
                  <div key={title}>
                    <h3 className="font-medium">{title}</h3>
                    {items.length === 0 ? (
                      <p className="mt-2 text-sm text-slate-600">None in this scope.</p>
                    ) : (
                      <ul className="mt-2 divide-y divide-slate-100">
                        {items.slice(0, 10).map((item) => (
                          <li key={item.asset_id} className="py-2 text-sm">
                            <strong>{item.asset_code}</strong> · {item.model_number}
                            <p className="text-slate-600">
                              Due {item.next_calibration_due} · {item.laboratory_name} / {item.room_number}
                            </p>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </section>
  );
}
