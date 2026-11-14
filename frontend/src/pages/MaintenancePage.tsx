import { isAxiosError } from "axios";
import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";
import {
  addMaintenanceLog,
  assignWorkOrder,
  createWorkOrder,
  listWorkOrders,
  updateWorkOrderStatus,
  verifyWorkOrder,
  type FailureCategory,
  type MaintenanceOutcome,
  type WorkOrder,
  type WorkOrderSeverity,
  type WorkOrderStatus,
} from "../services/maintenance";
import { lookupAsset } from "../services/assets";

const PAGE_SIZE = 20;
const SEVERITIES: WorkOrderSeverity[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const FAILURE_CATEGORIES: FailureCategory[] = [
  "ELECTRICAL",
  "MECHANICAL",
  "OPTICAL",
  "SOFTWARE",
  "CONSUMABLE",
  "OTHER",
];
const OUTCOMES: MaintenanceOutcome[] = [
  "OPERATIONAL",
  "REPAIRED_DEGRADED",
  "UNREPAIRABLE",
];

interface TechnicianOption {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
}

interface TechnicianPage {
  items: TechnicianOption[];
  pages: number;
}

function messageFromError(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item: { msg?: string }) => item.msg)
        .filter(Boolean)
        .join("; ");
    }
  }
  return error instanceof Error ? error.message : "The maintenance request failed.";
}

function formatStatus(status: WorkOrderStatus): string {
  return status.replace(/_/g, " ");
}

async function loadTechnicians(): Promise<TechnicianOption[]> {
  const params = { size: 100, role: "MAINTENANCE_TECH" };
  const first = await api.get<TechnicianPage>("/api/v1/users", {
    params: { ...params, page: 1 },
  });
  const technicians = [...first.data.items];
  for (let pageNumber = 2; pageNumber <= first.data.pages; pageNumber += 1) {
    const response = await api.get<TechnicianPage>("/api/v1/users", {
      params: { ...params, page: pageNumber },
    });
    technicians.push(...response.data.items);
  }
  return technicians;
}

function WorkOrderCard({
  order,
  role,
  userId,
  technicians,
  busy,
  onAssign,
  onStatus,
  onAddLog,
  onVerify,
}: {
  order: WorkOrder;
  role: string | undefined;
  userId: string | undefined;
  technicians: TechnicianOption[];
  busy: boolean;
  onAssign: (order: WorkOrder, technicianId: string) => void;
  onStatus: (order: WorkOrder, status: "IN_PROGRESS" | "AWAITING_PARTS") => void;
  onAddLog: (
    order: WorkOrder,
    input: {
      actions_taken: string;
      spare_parts_used: string | null;
      labor_hours: number;
      outcome_condition: MaintenanceOutcome;
    },
  ) => Promise<boolean>;
  onVerify: (
    order: WorkOrder,
    confirmed: boolean,
    notes: string,
  ) => Promise<boolean>;
}) {
  const [technicianId, setTechnicianId] = useState("");
  const [actionsTaken, setActionsTaken] = useState("");
  const [partsUsed, setPartsUsed] = useState("");
  const [laborHours, setLaborHours] = useState("0");
  const [outcome, setOutcome] = useState<MaintenanceOutcome>("OPERATIONAL");
  const [verificationNotes, setVerificationNotes] = useState("");

  const latestOutcome =
    order.maintenance_logs[order.maintenance_logs.length - 1]
      ?.outcome_condition ?? null;
  const canWork =
    role === "MAINTENANCE_TECH" &&
    order.assigned_to === userId &&
    (order.status === "ASSIGNED" ||
      order.status === "IN_PROGRESS" ||
      order.status === "AWAITING_PARTS");
  const canRecordLog =
    ((role === "MAINTENANCE_TECH" && order.assigned_to === userId) ||
      role === "ULMD_ADMIN") &&
    order.status === "IN_PROGRESS";
  const canVerify =
    (role === "LAB_MANAGER" || role === "ULMD_ADMIN") &&
    order.status === "RESOLVED";

  async function handleLogSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const saved = await onAddLog(order, {
      actions_taken: actionsTaken.trim(),
      spare_parts_used: partsUsed.trim() || null,
      labor_hours: Number(laborHours),
      outcome_condition: outcome,
    });
    if (!saved) return;
    setActionsTaken("");
    setPartsUsed("");
    setLaborHours("0");
    setOutcome("OPERATIONAL");
  }

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            to={`/assets/${order.asset_id}`}
            className="font-semibold text-university-700 hover:underline"
          >
            {order.ticket_number} · {order.asset_code}
          </Link>
          <p className="mt-1 text-sm text-slate-600">
            {order.asset_model_number} · {order.asset_manufacturer_name} ·{" "}
            {order.laboratory_name}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs font-semibold">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">
            {formatStatus(order.status)}
          </span>
          <span
            className={`rounded-full px-3 py-1 ${
              order.severity === "CRITICAL" || order.severity === "HIGH"
                ? "bg-red-100 text-red-800"
                : "bg-amber-100 text-amber-800"
            }`}
          >
            {order.severity}
          </span>
        </div>
      </div>

      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase text-slate-500">Reported by</dt>
          <dd className="mt-1 text-slate-800">{order.reporter_name}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-slate-500">Assigned technician</dt>
          <dd className="mt-1 text-slate-800">{order.assignee_name || "Not assigned"}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-slate-500">Failure category</dt>
          <dd className="mt-1 text-slate-800">{order.failure_category}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-slate-500">Reported</dt>
          <dd className="mt-1 text-slate-800">
            {new Date(order.created_at).toLocaleString()}
          </dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-xs uppercase text-slate-500">Fault description</dt>
          <dd className="mt-1 whitespace-pre-wrap text-slate-800">
            {order.fault_description}
          </dd>
        </div>
      </dl>

      {role === "ULMD_ADMIN" && order.status === "OPEN" && (
        <form
          className="mt-4 flex flex-wrap items-end gap-3 rounded bg-slate-50 p-4"
          onSubmit={(event) => {
            event.preventDefault();
            if (technicianId) onAssign(order, technicianId);
          }}
        >
          <label className="min-w-60 flex-1 text-sm font-medium text-slate-700">
            Assign Maintenance Technician
            <select
              required
              value={technicianId}
              onChange={(event) => setTechnicianId(event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            >
              <option value="">Select technician</option>
              {technicians.map((technician) => (
                <option
                  key={technician.id}
                  value={technician.id}
                  disabled={!technician.is_active}
                >
                  {technician.full_name} · {technician.email}
                  {!technician.is_active ? " (inactive)" : ""}
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            disabled={busy || !technicianId}
            className="rounded bg-university-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Assign ticket
          </button>
        </form>
      )}

      {canWork && (
        <div className="mt-4 flex flex-wrap gap-2">
          {order.status === "ASSIGNED" && (
            <button
              type="button"
              disabled={busy}
              onClick={() => onStatus(order, "IN_PROGRESS")}
              className="rounded bg-university-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Accept and start work
            </button>
          )}
          {order.status === "IN_PROGRESS" && (
            <button
              type="button"
              disabled={busy}
              onClick={() => onStatus(order, "AWAITING_PARTS")}
              className="rounded border border-amber-400 px-3 py-2 text-sm text-amber-800 disabled:opacity-50"
            >
              Mark awaiting parts
            </button>
          )}
          {order.status === "AWAITING_PARTS" && (
            <button
              type="button"
              disabled={busy}
              onClick={() => onStatus(order, "IN_PROGRESS")}
              className="rounded bg-university-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Resume work
            </button>
          )}
        </div>
      )}

      {canRecordLog && (
        <form
          className="mt-4 grid gap-3 rounded bg-slate-50 p-4 md:grid-cols-2"
          onSubmit={handleLogSubmit}
        >
          <h3 className="font-semibold text-slate-900 md:col-span-2">
            Record repair activity
          </h3>
          <label className="text-sm font-medium text-slate-700 md:col-span-2">
            Work performed
            <textarea
              required
              minLength={1}
              value={actionsTaken}
              onChange={(event) => setActionsTaken(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Spare parts used (optional)
            <textarea
              value={partsUsed}
              onChange={(event) => setPartsUsed(event.target.value)}
              rows={2}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              placeholder="Leave empty if none were used"
            />
          </label>
          <div className="grid gap-3">
            <label className="text-sm font-medium text-slate-700">
              Labor hours
              <input
                type="number"
                min="0"
                max="999.99"
                step="0.01"
                required
                value={laborHours}
                onChange={(event) => setLaborHours(event.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Outcome
              <select
                value={outcome}
                onChange={(event) =>
                  setOutcome(event.target.value as MaintenanceOutcome)
                }
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              >
                {OUTCOMES.map((value) => (
                  <option key={value} value={value}>
                    {value.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button
            type="submit"
            disabled={busy || !actionsTaken.trim()}
            className="w-fit rounded bg-university-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 md:col-span-2"
          >
            Submit repair and request verification
          </button>
        </form>
      )}

      {canVerify && (
        <form className="mt-4 rounded bg-slate-50 p-4">
          <label className="block text-sm font-medium text-slate-700">
            Verification notes
            <textarea
              required
              minLength={1}
              value={verificationNotes}
              onChange={(event) => setVerificationNotes(event.target.value)}
              rows={2}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            />
          </label>
          {latestOutcome !== "OPERATIONAL" && (
            <p className="mt-2 text-sm text-amber-800">
              Latest outcome: {latestOutcome || "not recorded"}. The current approved
              workflow allows closure only after an OPERATIONAL outcome.
            </p>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy || !verificationNotes.trim() || latestOutcome !== "OPERATIONAL"}
              onClick={async () => {
                const verified = await onVerify(
                  order,
                  true,
                  verificationNotes.trim(),
                );
                if (verified) setVerificationNotes("");
              }}
              className="rounded bg-green-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Verify and close
            </button>
            <button
              type="button"
              disabled={busy || !verificationNotes.trim()}
              onClick={async () => {
                const rejected = await onVerify(
                  order,
                  false,
                  verificationNotes.trim(),
                );
                if (rejected) setVerificationNotes("");
              }}
              className="rounded border border-amber-400 px-3 py-2 text-sm text-amber-800 disabled:opacity-50"
            >
              Reject repair and return to technician
            </button>
          </div>
        </form>
      )}

      {order.verification_notes && (
        <p className="mt-3 rounded bg-amber-50 p-3 text-sm text-amber-900">
          Latest verification feedback ({order.verifier_name || "reviewer"}):{" "}
          {order.verification_notes}
        </p>
      )}

      <section className="mt-5 border-t border-slate-200 pt-4">
        <h3 className="font-semibold text-slate-900">Maintenance history</h3>
        {order.maintenance_logs.length ? (
          <ol className="mt-3 space-y-3">
            {order.maintenance_logs.map((log) => (
              <li key={log.id} className="rounded bg-slate-50 p-3 text-sm">
                <div className="flex flex-wrap justify-between gap-2">
                  <strong>{log.technician_name}</strong>
                  <span className="text-slate-500">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="mt-2 whitespace-pre-wrap">{log.actions_taken}</p>
                <p className="mt-1 text-slate-600">
                  Parts: {log.spare_parts_used || "None recorded"} · Labor:{" "}
                  {log.labor_hours} hours · Outcome:{" "}
                  {log.outcome_condition.replace(/_/g, " ")}
                </p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-2 text-sm text-slate-500">
            No repair activities have been recorded.
          </p>
        )}
      </section>

      <ol className="mt-4 space-y-1 border-l-2 border-slate-200 pl-4 text-xs text-slate-500">
        {order.status_history.map((event, index) => (
          <li key={`${event.action}-${event.occurred_at}-${index}`}>
            {formatStatus(event.new_status)} · {event.actor_name || "Former user"} ·{" "}
            {new Date(event.occurred_at).toLocaleString()}
          </li>
        ))}
      </ol>
    </article>
  );
}

export default function MaintenancePage() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const canReport = ["ULMD_ADMIN", "LAB_MANAGER", "LAB_TECH"].includes(
    user?.role ?? "",
  );
  const [assetCode, setAssetCode] = useState(searchParams.get("assetCode") ?? "");
  const [severity, setSeverity] = useState<WorkOrderSeverity>("MEDIUM");
  const [failureCategory, setFailureCategory] =
    useState<FailureCategory>("OTHER");
  const [faultDescription, setFaultDescription] = useState("");
  const [statusFilter, setStatusFilter] = useState<WorkOrderStatus | "">("");
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [technicians, setTechnicians] = useState<TechnicianOption[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyOrderId, setBusyOrderId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadOrders(
    nextPage = page,
    nextStatus: WorkOrderStatus | "" = statusFilter,
  ) {
    setLoading(true);
    setError("");
    try {
      const result = await listWorkOrders({
        page: nextPage,
        size: PAGE_SIZE,
        status: nextStatus || undefined,
      });
      setOrders(result.items);
      setPage(nextPage);
      setPages(result.pages);
      setTotal(result.total);
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    async function loadInitialData() {
      try {
        const workOrderPage = await listWorkOrders({
          page: 1,
          size: PAGE_SIZE,
        });
        const loadedTechnicians =
          user?.role === "ULMD_ADMIN" ? await loadTechnicians() : [];
        if (!active) return;
        setOrders(workOrderPage.items);
        setPage(1);
        setPages(workOrderPage.pages);
        setTotal(workOrderPage.total);
        setTechnicians(loadedTechnicians);
      } catch (cause: unknown) {
        if (active) setError(messageFromError(cause));
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadInitialData();
    return () => {
      active = false;
    };
  }, [user?.role]);

  async function handleReportFault(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const asset = await lookupAsset(assetCode.trim());
      const created = await createWorkOrder({
        asset_id: asset.id,
        severity,
        failure_category: failureCategory,
        fault_description: faultDescription.trim(),
      });
      setAssetCode("");
      setFaultDescription("");
      setNotice(`Maintenance request ${created.ticket_number} was submitted.`);
      await loadOrders(1, statusFilter);
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setSaving(false);
    }
  }

  async function performAction(
    order: WorkOrder,
    action: () => Promise<WorkOrder>,
    successMessage: string,
  ): Promise<boolean> {
    setBusyOrderId(order.id);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(successMessage);
      await loadOrders(page, statusFilter);
      return true;
    } catch (cause: unknown) {
      setError(messageFromError(cause));
      return false;
    } finally {
      setBusyOrderId("");
    }
  }

  async function handleVerify(
    order: WorkOrder,
    confirmed: boolean,
    notes: string,
  ): Promise<boolean> {
    return performAction(
      order,
      () => verifyWorkOrder(order.id, {
        confirmed,
        verification_notes: notes,
      }),
      confirmed
        ? `${order.ticket_number} verified and closed.`
        : `${order.ticket_number} returned to the technician.`,
    );
  }

  return (
    <section>
      <header>
        <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
          Equipment service
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          Maintenance work orders
        </h1>
        <p className="mt-2 text-slate-600">
          Report equipment faults, follow technician work, and review repair history.
        </p>
      </header>

      {error && (
        <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-sm text-red-800">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="mt-4 rounded bg-green-50 p-3 text-sm text-green-800">
          {notice}
        </p>
      )}

      {canReport && (
        <form
          className="mt-6 grid gap-4 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-2"
          onSubmit={(event) => void handleReportFault(event)}
        >
          <h2 className="text-lg font-semibold text-slate-900 md:col-span-2">
            Report equipment fault
          </h2>
          <label className="text-sm font-medium text-slate-700">
            Asset code
            <input
              required
              maxLength={100}
              value={assetCode}
              onChange={(event) => setAssetCode(event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              placeholder="HU-COLLEGE-DEPT-0001"
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Severity
            <select
              value={severity}
              onChange={(event) =>
                setSeverity(event.target.value as WorkOrderSeverity)
              }
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            >
              {SEVERITIES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">
            Failure category
            <select
              value={failureCategory}
              onChange={(event) =>
                setFailureCategory(event.target.value as FailureCategory)
              }
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            >
              {FAILURE_CATEGORIES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700 md:col-span-2">
            Symptom description
            <textarea
              required
              minLength={1}
              value={faultDescription}
              onChange={(event) => setFaultDescription(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            />
          </label>
          <button
            type="submit"
            disabled={
              saving ||
              !assetCode.trim() ||
              !faultDescription.trim()
            }
            className="w-fit rounded bg-university-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? "Submitting…" : "Submit maintenance request"}
          </button>
        </form>
      )}

      <div className="mt-8 flex flex-wrap items-end justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-900">
          Work order queue{" "}
          <span className="text-sm font-normal text-slate-500">({total})</span>
        </h2>
        <label className="text-sm text-slate-700">
          Status
          <select
            value={statusFilter}
            onChange={(event) => {
              const nextStatus = event.target.value as WorkOrderStatus | "";
              setStatusFilter(nextStatus);
              void loadOrders(1, nextStatus);
            }}
            className="ml-2 rounded border border-slate-300 px-3 py-2"
          >
            <option value="">All statuses</option>
            {(
              [
                "OPEN",
                "ASSIGNED",
                "IN_PROGRESS",
                "AWAITING_PARTS",
                "RESOLVED",
                "CLOSED",
              ] as WorkOrderStatus[]
            ).map((value) => (
              <option key={value} value={value}>
                {formatStatus(value)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading ? (
        <p className="mt-4 text-slate-600">Loading work orders…</p>
      ) : orders.length ? (
        <div className="mt-4 space-y-4">
          {orders.map((order) => (
            <WorkOrderCard
              key={order.id}
              order={order}
              role={user?.role}
              userId={user?.id}
              technicians={technicians}
              busy={busyOrderId === order.id}
              onAssign={(record, technicianId) =>
                void performAction(
                  record,
                  () => assignWorkOrder(record.id, technicianId),
                  `${record.ticket_number} assigned.`,
                )
              }
              onStatus={(record, nextStatus) =>
                void performAction(
                  record,
                  () => updateWorkOrderStatus(record.id, nextStatus),
                  `${record.ticket_number} status updated.`,
                )
              }
              onAddLog={(record, input) =>
                performAction(
                  record,
                  () => addMaintenanceLog(record.id, input),
                  `Repair activity recorded for ${record.ticket_number}.`,
                )
              }
              onVerify={(record, confirmed, notes) =>
                handleVerify(record, confirmed, notes)
              }
            />
          ))}
          <div className="flex items-center justify-between pt-2 text-sm">
            <span className="text-slate-600">
              Page {page} of {pages || 1}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => void loadOrders(page - 1)}
                className="rounded border border-slate-300 px-3 py-2 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={page >= pages || loading}
                onClick={() => void loadOrders(page + 1)}
                className="rounded border border-slate-300 px-3 py-2 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      ) : (
        <p className="mt-4 rounded border border-dashed border-slate-300 p-6 text-center text-slate-600">
          No work orders match this view.
        </p>
      )}
    </section>
  );
}
