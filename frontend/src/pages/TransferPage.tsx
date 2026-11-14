import { isAxiosError } from "axios";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  listLocationOptions,
  lookupAsset,
  type LaboratoryOption,
  type RoomOption,
} from "../services/assets";
import {
  acceptTransfer,
  approveTransfer,
  createTransfer,
  listTransfers,
  rejectTransfer,
  type AssetTransfer,
  type TransferStatus,
} from "../services/transfers";

const PAGE_SIZE = 20;

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
  return error instanceof Error ? error.message : "The transfer request failed.";
}

function displayDate(value: string): string {
  return new Date(value).toLocaleString();
}

function TransferCard({
  transfer,
  role,
  userId,
  laboratories,
  busy,
  onAccept,
  onApprove,
  onBeginReject,
}: {
  transfer: AssetTransfer;
  role: string | undefined;
  userId: string | undefined;
  laboratories: LaboratoryOption[];
  busy: boolean;
  onAccept: (transfer: AssetTransfer) => void;
  onApprove: (transfer: AssetTransfer) => void;
  onBeginReject: (transfer: AssetTransfer) => void;
}) {
  const isTargetManager = laboratories.some(
    (laboratory) =>
      laboratory.id === transfer.target_laboratory_id &&
      laboratory.manager_id === userId,
  );
  const canAccept =
    transfer.status === "PENDING_RECEIVER" &&
    (role === "ULMD_ADMIN" || (role === "LAB_MANAGER" && isTargetManager));
  const canReject =
    (transfer.status === "PENDING_RECEIVER" &&
      (role === "ULMD_ADMIN" || (role === "LAB_MANAGER" && isTargetManager))) ||
    (transfer.status === "PENDING_ULMD" && role === "ULMD_ADMIN");

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            className="font-semibold text-university-700 hover:underline"
            to={`/assets/${transfer.asset_id}`}
          >
            {transfer.asset_code}
          </Link>
          <p className="mt-1 text-sm text-slate-600">
            {transfer.origin_laboratory_name} / {transfer.origin_building_name},{" "}
            room {transfer.origin_room_number}
            {" → "}
            {transfer.target_laboratory_name} / {transfer.target_building_name},
            room {transfer.target_room_number}
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          {transfer.status.replace(/_/g, " ")}
        </span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase text-slate-500">Reason</dt>
          <dd className="mt-1 text-slate-800">{transfer.transfer_reason}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase text-slate-500">Initiated</dt>
          <dd className="mt-1 text-slate-800">
            {transfer.initiator_name} · {displayDate(transfer.created_at)}
          </dd>
        </div>
        {transfer.notes && (
          <div className="sm:col-span-2">
            <dt className="text-xs uppercase text-slate-500">Latest note</dt>
            <dd className="mt-1 text-slate-800">{transfer.notes}</dd>
          </div>
        )}
      </dl>
      {transfer.status_history.length > 0 && (
        <ol className="mt-4 space-y-2 border-l-2 border-slate-200 pl-4 text-xs text-slate-600">
          {transfer.status_history.map((event, index) => (
            <li key={`${event.action}-${event.occurred_at}-${index}`}>
              <span className="font-semibold text-slate-800">
                {event.new_status.replace(/_/g, " ")}
              </span>
              {" · "}
              {event.actor_name || "Former user"} ·{" "}
              {displayDate(event.occurred_at)}
              {event.notes && <p className="mt-1">{event.notes}</p>}
            </li>
          ))}
        </ol>
      )}
      {(canAccept || canReject) && (
        <div className="mt-4 flex flex-wrap gap-2">
          {canAccept && (
            <button
              type="button"
              disabled={busy}
              onClick={() => onAccept(transfer)}
              className="rounded bg-university-700 px-3 py-2 text-sm font-medium text-white hover:bg-university-800 disabled:opacity-50"
            >
              Accept receipt
            </button>
          )}
          {transfer.status === "PENDING_ULMD" && role === "ULMD_ADMIN" && (
            <button
              type="button"
              disabled={busy}
              onClick={() => onApprove(transfer)}
              className="rounded bg-green-700 px-3 py-2 text-sm font-medium text-white hover:bg-green-800 disabled:opacity-50"
            >
              Approve transfer
            </button>
          )}
          {canReject && (
            <button
              type="button"
              disabled={busy}
              onClick={() => onBeginReject(transfer)}
              className="rounded border border-red-300 px-3 py-2 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
            >
              Reject
            </button>
          )}
        </div>
      )}
    </article>
  );
}

export default function TransferPage() {
  const { user } = useAuth();
  const role = user?.role;
  const canInitiate = role === "ULMD_ADMIN" || role === "LAB_MANAGER";
  const [laboratories, setLaboratories] = useState<LaboratoryOption[]>([]);
  const [rooms, setRooms] = useState<RoomOption[]>([]);
  const [assetCode, setAssetCode] = useState("");
  const [targetLaboratoryId, setTargetLaboratoryId] = useState("");
  const [targetRoomId, setTargetRoomId] = useState("");
  const [reason, setReason] = useState("");
  const [statusFilter, setStatusFilter] = useState<TransferStatus | "">("");
  const [transfers, setTransfers] = useState<AssetTransfer[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [rejection, setRejection] = useState<{
    transfer: AssetTransfer;
    notes: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyTransferId, setBusyTransferId] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const visibleRooms = useMemo(
    () => rooms.filter((room) => room.laboratory_id === targetLaboratoryId),
    [rooms, targetLaboratoryId],
  );

  async function loadTransfers(nextPage = page, nextStatus = statusFilter) {
    setLoading(true);
    setError("");
    try {
      const result = await listTransfers({
        page: nextPage,
        size: PAGE_SIZE,
        status: nextStatus || undefined,
      });
      setTransfers(result.items);
      setTotal(result.total);
      setPages(result.pages);
      setPage(nextPage);
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    void Promise.all([listLocationOptions(), listTransfers({
      page: 1,
      size: PAGE_SIZE,
    })])
      .then(([locations, result]) => {
        if (!active) return;
        setLaboratories(locations.laboratories);
        setRooms(locations.rooms);
        setTransfers(result.items);
        setTotal(result.total);
        setPages(result.pages);
        setPage(1);
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
  }, []);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const asset = await lookupAsset(assetCode.trim());
      await createTransfer({
        asset_id: asset.id,
        target_laboratory_id: targetLaboratoryId,
        target_room_id: targetRoomId,
        transfer_reason: reason.trim(),
      });
      setAssetCode("");
      setTargetLaboratoryId("");
      setTargetRoomId("");
      setReason("");
      setSuccess(`Transfer initiated for ${asset.asset_code}.`);
      await loadTransfers(1, statusFilter);
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setSaving(false);
    }
  }

  async function handleAccept(transfer: AssetTransfer) {
    setBusyTransferId(transfer.id);
    setError("");
    setSuccess("");
    try {
      await acceptTransfer(transfer.id);
      setSuccess(`Receipt accepted for ${transfer.asset_code}.`);
      await loadTransfers(page, statusFilter);
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setBusyTransferId("");
    }
  }

  async function handleApprove(transfer: AssetTransfer) {
    if (!window.confirm(`Approve the relocation of ${transfer.asset_code}?`)) {
      return;
    }
    setBusyTransferId(transfer.id);
    setError("");
    setSuccess("");
    try {
      await approveTransfer(transfer.id);
      setSuccess(`Transfer completed for ${transfer.asset_code}.`);
      await loadTransfers(page, statusFilter);
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setBusyTransferId("");
    }
  }

  async function handleReject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!rejection) return;
    setBusyTransferId(rejection.transfer.id);
    setError("");
    setSuccess("");
    try {
      await rejectTransfer(rejection.transfer.id, rejection.notes.trim());
      setSuccess(`Transfer rejected for ${rejection.transfer.asset_code}.`);
      setRejection(null);
      await loadTransfers(page, statusFilter);
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setBusyTransferId("");
    }
  }

  return (
    <section>
      <h1 className="text-3xl font-semibold text-slate-900">Custody transfers</h1>
      <p className="mt-2 text-slate-600">
        Track receipt, approval, and the previous and current laboratory locations.
      </p>
      {error && (
        <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-sm text-red-800">
          {error}
        </p>
      )}
      {success && (
        <p role="status" className="mt-4 rounded bg-green-50 p-3 text-sm text-green-800">
          {success}
        </p>
      )}

      {canInitiate && (
        <form
          className="mt-6 grid gap-4 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-2"
          onSubmit={(event) => void handleCreate(event)}
        >
          <h2 className="text-lg font-semibold text-slate-900 md:col-span-2">
            Initiate transfer
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
            Destination laboratory
            <select
              required
              value={targetLaboratoryId}
              onChange={(event) => {
                setTargetLaboratoryId(event.target.value);
                setTargetRoomId("");
              }}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            >
              <option value="">Select laboratory</option>
              {laboratories.map((laboratory) => (
                <option key={laboratory.id} value={laboratory.id}>
                  {laboratory.name} · {laboratory.department_name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">
            Destination room
            <select
              required
              value={targetRoomId}
              onChange={(event) => setTargetRoomId(event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            >
              <option value="">Select room</option>
              {visibleRooms.map((room) => (
                <option key={room.id} value={room.id}>
                  {room.building_name} · {room.room_number}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700 md:col-span-2">
            Transfer reason
            <textarea
              required
              maxLength={4000}
              rows={3}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            />
          </label>
          <button
            type="submit"
            disabled={saving}
            className="w-fit rounded bg-university-700 px-4 py-2 text-sm font-medium text-white hover:bg-university-800 disabled:opacity-50"
          >
            {saving ? "Submitting…" : "Submit transfer"}
          </button>
        </form>
      )}

      {rejection && (
        <form
          className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5"
          onSubmit={(event) => void handleReject(event)}
        >
          <label className="block text-sm font-medium text-red-900">
            Reason for rejecting {rejection.transfer.asset_code}
            <textarea
              required
              minLength={1}
              maxLength={4000}
              rows={3}
              value={rejection.notes}
              onChange={(event) =>
                setRejection({ ...rejection, notes: event.target.value })
              }
              className="mt-1 w-full rounded border border-red-300 bg-white px-3 py-2"
            />
          </label>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={busyTransferId === rejection.transfer.id}
              className="rounded bg-red-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Confirm rejection
            </button>
            <button
              type="button"
              onClick={() => setRejection(null)}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="mt-8 flex flex-wrap items-end justify-between gap-3">
        <h2 className="text-xl font-semibold text-slate-900">
          Transfer history <span className="text-sm font-normal text-slate-500">({total})</span>
        </h2>
        <label className="text-sm text-slate-700">
          Status
          <select
            value={statusFilter}
            onChange={(event) => {
              const nextStatus = event.target.value as TransferStatus | "";
              setStatusFilter(nextStatus);
              void loadTransfers(1, nextStatus);
            }}
            className="ml-2 rounded border border-slate-300 px-3 py-2"
          >
            <option value="">All statuses</option>
            <option value="PENDING_RECEIVER">Pending receiver</option>
            <option value="PENDING_ULMD">Pending ULMD</option>
            <option value="COMPLETED">Completed</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </label>
      </div>

      {loading ? (
        <p className="mt-4 text-slate-600">Loading transfers…</p>
      ) : transfers.length ? (
        <div className="mt-4 space-y-4">
          {transfers.map((transfer) => (
            <TransferCard
              key={transfer.id}
              transfer={transfer}
              role={role}
              userId={user?.id}
              laboratories={laboratories}
              busy={busyTransferId === transfer.id}
              onAccept={(record) => void handleAccept(record)}
              onApprove={(record) => void handleApprove(record)}
              onBeginReject={(record) => setRejection({ transfer: record, notes: "" })}
            />
          ))}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-sm">
            <span className="text-slate-600">
              Page {page} of {pages || 1}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => void loadTransfers(page - 1)}
                className="rounded border border-slate-300 px-3 py-2 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={page >= pages || loading}
                onClick={() => void loadTransfers(page + 1)}
                className="rounded border border-slate-300 px-3 py-2 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      ) : (
        <p className="mt-4 rounded border border-dashed border-slate-300 p-6 text-center text-slate-600">
          No custody transfers match this view.
        </p>
      )}
    </section>
  );
}
