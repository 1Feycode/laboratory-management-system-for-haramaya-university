import { isAxiosError } from "axios";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  type CountByName,
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

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <dl>
        <dt className="text-sm font-medium text-slate-600">{label}</dt>
        <dd className="mt-3 break-words text-3xl font-semibold tracking-tight text-slate-950">
          {value}
        </dd>
      </dl>
      <p className="mt-2 text-sm leading-5 text-slate-600">{detail}</p>
    </article>
  );
}

function BreakdownCard({
  title,
  items,
  emptyMessage,
}: {
  title: string;
  items: CountByName[];
  emptyMessage: string;
}) {
  const maximum = Math.max(0, ...items.map((item) => item.count));

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      {items.length === 0 ? (
        <p className="mt-4 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
          {emptyMessage}
        </p>
      ) : (
        <ul className="mt-4 space-y-4">
          {items.map((item) => (
            <li key={item.name}>
              <div className="flex items-start justify-between gap-3 text-sm">
                <span className="break-words font-medium text-slate-700">
                  {item.name.replace(/_/g, " ")}
                </span>
                <span className="shrink-0 font-semibold tabular-nums text-slate-900">
                  {item.count}
                </span>
              </div>
              <div
                aria-hidden="true"
                className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"
              >
                <div
                  className="h-full rounded-full bg-slate-700"
                  style={{
                    width: `${maximum > 0 ? (item.count / maximum) * 100 : 0}%`,
                  }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function QuickLinks({ role }: { role: string | undefined }) {
  const links = [
    {
      label: "Browse assets",
      description: "Search the registered laboratory equipment.",
      to: "/assets",
    },
    {
      label: "Maintenance work orders",
      description: "Review fault reports and repair records.",
      to: "/maintenance",
    },
    {
      label: "Calibration tracking",
      description: "Review due dates and recorded calibrations.",
      to: "/calibrations",
    },
    ...(["ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"].includes(role ?? "")
      ? [
          {
            label: "Custody transfers",
            description: "View transfer status and history.",
            to: "/transfers",
          },
        ]
      : []),
    ...(REPORT_ROLES.includes(role ?? "")
      ? [
          {
            label: "Operational reports",
            description: "Open scoped reports and inventory exports.",
            to: "/reports",
          },
        ]
      : []),
  ];

  return (
    <section aria-labelledby="dashboard-shortcuts-title">
      <div>
        <h2
          id="dashboard-shortcuts-title"
          className="text-lg font-semibold text-slate-900"
        >
          Shortcuts
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Open the areas available to your account.
        </p>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className="group rounded-xl border border-slate-200 bg-white p-4 transition-colors hover:border-slate-400 hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700"
          >
            <span className="font-semibold text-slate-900">{link.label}</span>
            <span className="mt-1 block text-sm leading-5 text-slate-600">
              {link.description}
            </span>
          </Link>
        ))}
      </div>
    </section>
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

  return (
    <section className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-600">
            Operational overview
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
            Laboratory dashboard
          </h1>
          <p className="mt-2 text-slate-600">
            Welcome, {user?.full_name}
          </p>
        </div>
      </header>

      {!canViewReports ? (
        <section className="space-y-8">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <h2 className="text-xl font-semibold text-slate-900">
              Your workspace
            </h2>
            <p className="mt-2 max-w-3xl leading-7 text-slate-600">
              Your account is authenticated as {user?.role.replace(/_/g, " ")}.
              Use the links below to open the laboratory records and workflows
              available to your role.
            </p>
          </div>
          <QuickLinks role={user?.role} />
        </section>
      ) : (
        <>
          <form
            onSubmit={(event) => void applyFilters(event)}
            className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6 md:grid-cols-2 xl:grid-cols-6"
          >
            {canFilterOrganization && (
              <>
                <label className="text-sm font-medium text-slate-700 xl:col-span-2">
                  College
                  <select
                    value={collegeId}
                    onChange={(event) => updateCollege(event.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
                  >
                    <option value="">All in my scope</option>
                    {colleges.map((college) => (
                      <option key={college.id} value={college.id}>
                        {college.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-sm font-medium text-slate-700 xl:col-span-2">
                  Department
                  <select
                    value={departmentId}
                    onChange={(event) => setDepartmentId(event.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
                  >
                    <option value="">All in selected college</option>
                    {departments.map((department) => (
                      <option key={department.id} value={department.id}>
                        {department.name}
                      </option>
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
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              To
              <input
                type="date"
                value={dateTo}
                onChange={(event) => setDateTo(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
              />
            </label>
            <label className="text-sm font-medium text-slate-700 xl:col-span-2">
              Calibration due horizon (days)
              <input
                required
                type="number"
                min="0"
                step="1"
                value={withinDays}
                onChange={(event) => setWithinDays(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
              />
            </label>
            <div className="flex items-end xl:col-span-2">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex min-h-11 w-full items-center justify-center rounded-lg bg-slate-900 px-4 py-2.5 font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
              >
                {loading ? "Loading dashboard…" : "Apply filters"}
              </button>
            </div>
          </form>

          {error && (
            <p
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
            >
              {error}
            </p>
          )}
          {loading && (
            <p
              role="status"
              aria-live="polite"
              className="rounded-xl border border-slate-200 bg-white p-4 text-slate-600"
            >
              Loading dashboard…
            </p>
          )}
          {!loading && !report && !error && (
            <p
              role="status"
              className="rounded-xl border border-dashed border-slate-300 bg-white p-5 text-slate-600"
            >
              Choose a calibration due horizon and apply the filters to load the
              dashboard.
            </p>
          )}
          {!loading && report && (
            <>
              <section aria-labelledby="dashboard-summary-title">
                <div className="mb-4">
                  <h2
                    id="dashboard-summary-title"
                    className="text-lg font-semibold text-slate-900"
                  >
                    Summary
                  </h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Current counts and approved measures in your authorized
                    reporting scope.
                  </p>
                </div>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <MetricCard
                    label="Total assets"
                    value={report.asset_total}
                    detail="Registered assets in the current scope."
                  />
                  <MetricCard
                    label="Operational assets"
                    value={report.operational_assets}
                    detail="Assets currently marked operational."
                  />
                  <MetricCard
                    label="Active work orders"
                    value={report.active_work_orders}
                    detail="Current active work orders in your scope."
                  />
                  <MetricCard
                    label="Completed work orders"
                    value={report.work_orders_completed}
                    detail="Completed count returned for this report scope."
                  />
                  <MetricCard
                    label="Overdue calibrations"
                    value={report.overdue_calibrations}
                    detail="Assets with a calibration date in the past."
                  />
                  <MetricCard
                    label="Upcoming calibrations"
                    value={report.upcoming_calibrations}
                    detail={`Due within the selected ${withinDays}-day horizon.`}
                  />
                  <MetricCard
                    label="Fleet availability"
                    value={
                      report.uptime_percentage === null
                        ? "Pending definition"
                        : `${report.uptime_percentage.toFixed(1)}%`
                    }
                    detail={
                      report.uptime_percentage === null
                        ? "No calculation is shown until its definition is approved."
                        : report.availability_status
                    }
                  />
                  <MetricCard
                    label="Recorded downtime"
                    value={
                      report.downtime_asset_hours === null
                        ? "Pending definition"
                        : `${report.downtime_asset_hours.toFixed(1)} asset hours`
                    }
                    detail={
                      report.downtime_asset_hours === null
                        ? "No calculation is shown until its definition is approved."
                        : report.availability_status
                    }
                  />
                </div>
              </section>

              <div className="grid gap-4 xl:grid-cols-3">
                <BreakdownCard
                  title="Assets by operational status"
                  items={report.assets_by_status}
                  emptyMessage="No assets in this scope."
                />
                <BreakdownCard
                  title="Assets by category"
                  items={report.assets_by_category}
                  emptyMessage="No asset categories in this scope."
                />
                <BreakdownCard
                  title="Work orders by status"
                  items={report.work_orders_by_status}
                  emptyMessage="No work orders in this scope."
                />
              </div>

              <div className="grid gap-4 xl:grid-cols-2">
                <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="text-base font-semibold text-slate-900">
                        Critical work orders
                      </h2>
                      <p className="mt-1 text-sm text-slate-600">
                        Open critical requests in your current scope.
                      </p>
                    </div>
                    <Link
                      to="/maintenance"
                      className="inline-flex min-h-10 items-center rounded-lg border border-slate-300 px-3 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700"
                    >
                      View maintenance
                    </Link>
                  </div>
                  {report.critical_work_orders.length === 0 ? (
                    <p className="mt-4 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
                      No open critical work orders.
                    </p>
                  ) : (
                    <ul className="mt-4 divide-y divide-slate-100">
                      {report.critical_work_orders.map((item) => (
                        <li key={item.id} className="py-4 first:pt-0 last:pb-0">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-semibold text-slate-900">
                              {item.ticket_number}
                            </p>
                            <span className="rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-800">
                              {item.severity}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-slate-700">
                            {item.asset_code} · {item.laboratory_name}
                          </p>
                          <p className="mt-1 text-sm text-slate-600">
                            {item.status.replace(/_/g, " ")}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>

                <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="text-base font-semibold text-slate-900">
                        Calibration due queue
                      </h2>
                      <p className="mt-1 text-sm text-slate-600">
                        Overdue and upcoming assets in the selected horizon.
                      </p>
                    </div>
                    <Link
                      to="/calibrations"
                      className="inline-flex min-h-10 items-center rounded-lg border border-slate-300 px-3 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700"
                    >
                      View calibrations
                    </Link>
                  </div>
                  {[
                    ...report.overdue_calibration_items,
                    ...report.upcoming_calibration_items,
                  ].length === 0 ? (
                    <p className="mt-4 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
                      No overdue or upcoming calibrations in this scope.
                    </p>
                  ) : (
                    <ul className="mt-4 divide-y divide-slate-100">
                      {[
                        ...report.overdue_calibration_items,
                        ...report.upcoming_calibration_items,
                      ].map((item) => (
                        <li
                          key={`${item.status}-${item.asset_id}`}
                          className="flex flex-wrap items-start justify-between gap-3 py-4 first:pt-0 last:pb-0"
                        >
                          <div className="min-w-0">
                            <Link
                              to={`/assets/${item.asset_id}`}
                              className="break-all font-semibold text-slate-900 underline decoration-slate-300 underline-offset-2 hover:decoration-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700"
                            >
                              {item.asset_code}
                            </Link>
                            <p className="mt-1 break-words text-sm text-slate-700">
                              {item.model_number} · {item.laboratory_name} /{" "}
                              {item.room_number}
                            </p>
                            <p className="mt-1 text-sm text-slate-600">
                              Due {item.next_calibration_due}
                            </p>
                          </div>
                          <span
                            className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
                              item.status === "OVERDUE"
                                ? "bg-red-50 text-red-800"
                                : "bg-amber-50 text-amber-900"
                            }`}
                          >
                            {item.status}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </div>
            </>
          )}

          <QuickLinks role={user?.role} />
        </>
      )}
    </section>
  );
}
