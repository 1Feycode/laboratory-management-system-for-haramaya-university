import { isAxiosError } from "axios";
import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  createCalibration,
  listCalibrations,
  listDueCalibrations,
  type Calibration,
  type CalibrationDue,
} from "../services/calibrations";
import { lookupAsset, type Page } from "../services/assets";

function messageFromError(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "The calibration request failed.";
}

function emptyPage<T>(size = 20): Page<T> {
  return { items: [], total: 0, page: 1, size, pages: 0 };
}

function today(): string {
  const current = new Date();
  current.setMinutes(current.getMinutes() - current.getTimezoneOffset());
  return current.toISOString().slice(0, 10);
}

export default function CalibrationPage() {
  const { user } = useAuth();
  const canRecord = ["ULMD_ADMIN", "MAINTENANCE_TECH"].includes(user?.role ?? "");
  const canReadHistory = [
    "ULMD_ADMIN",
    "MAINTENANCE_TECH",
    "AUDITOR",
  ].includes(user?.role ?? "");
  const [history, setHistory] = useState<Page<Calibration>>(emptyPage());
  const [historyPage, setHistoryPage] = useState(1);
  const [historyLoading, setHistoryLoading] = useState(canReadHistory);
  const [historyError, setHistoryError] = useState("");
  const [due, setDue] = useState<Page<CalibrationDue> | null>(null);
  const [duePage, setDuePage] = useState(1);
  const [withinDays, setWithinDays] = useState("");
  const [dueLoading, setDueLoading] = useState(false);
  const [dueError, setDueError] = useState("");
  const [assetCode, setAssetCode] = useState("");
  const [calibrationDate, setCalibrationDate] = useState(today);
  const [standardUsed, setStandardUsed] = useState("");
  const [certificateReference, setCertificateReference] = useState("");
  const [accreditationBody, setAccreditationBody] = useState("");
  const [passed, setPassed] = useState("true");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState("");

  const loadHistory = useCallback(async () => {
    if (!canReadHistory) return;
    setHistoryLoading(true);
    setHistoryError("");
    try {
      setHistory(await listCalibrations(historyPage));
    } catch (error: unknown) {
      setHistoryError(messageFromError(error));
    } finally {
      setHistoryLoading(false);
    }
  }, [canReadHistory, historyPage]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  async function loadDue(page = 1) {
    const days = Number(withinDays);
    if (!Number.isInteger(days) || days < 0) {
      setDueError("Enter a non-negative whole number of days.");
      return;
    }
    setDueLoading(true);
    setDueError("");
    setDuePage(page);
    try {
      setDue(await listDueCalibrations(days, page));
    } catch (error: unknown) {
      setDueError(messageFromError(error));
    } finally {
      setDueLoading(false);
    }
  }

  async function submitCalibration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setFormError("");
    setSuccess("");
    try {
      const asset = await lookupAsset(assetCode.trim());
      const record = await createCalibration({
        asset_id: asset.id,
        calibration_date: calibrationDate,
        standard_used: standardUsed.trim(),
        certificate_reference: certificateReference.trim() || null,
        accreditation_body: accreditationBody.trim() || null,
        passed: passed === "true",
        notes: notes.trim() || null,
      });
      setSuccess(
        `Calibration recorded for ${record.asset_code}. Next due: ${record.next_due_date}.`,
      );
      setAssetCode("");
      setStandardUsed("");
      setCertificateReference("");
      setAccreditationBody("");
      setNotes("");
      await loadHistory();
      if (due !== null) await loadDue(1);
    } catch (error: unknown) {
      setFormError(messageFromError(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-3xl font-semibold text-slate-900">
          Calibration tracking
        </h1>
        <p className="mt-2 text-slate-600">
          Review calibration dates and retain each calibration record in asset history.
          Due results are calculated using the requested date window.
        </p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-xl font-semibold text-slate-900">
          Upcoming and overdue calibrations
        </h2>
        <form
          className="mt-4 flex flex-wrap items-end gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            void loadDue(1);
          }}
        >
          <label className="text-sm text-slate-700">
            Show items due within (days)
            <input
              type="number"
              min="0"
              step="1"
              required
              className="mt-1 block w-48 rounded border border-slate-300 px-3 py-2"
              value={withinDays}
              onChange={(event) => setWithinDays(event.target.value)}
            />
          </label>
          <button
            type="submit"
            disabled={dueLoading}
            className="rounded bg-university-700 px-4 py-2 text-sm font-medium text-white hover:bg-university-800 disabled:opacity-60"
          >
            {dueLoading ? "Loading…" : "Show due items"}
          </button>
        </form>
        {dueError && <p role="alert" className="mt-3 text-sm text-red-700">{dueError}</p>}
        {dueLoading && <p className="mt-4 text-sm text-slate-600">Loading calibration status…</p>}
        {!dueLoading && due && (
          <>
            <div
              className="table-scroll mt-4"
              role="region"
              aria-label="Calibration due results"
              tabIndex={0}
            >
              <table className="w-full min-w-[700px] text-left text-sm">
                <thead className="border-b border-slate-200 text-slate-600">
                  <tr>
                    <th className="px-3 py-2 font-medium">Asset</th>
                    <th className="px-3 py-2 font-medium">Laboratory / room</th>
                    <th className="px-3 py-2 font-medium">Last calibrated</th>
                    <th className="px-3 py-2 font-medium">Next due</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {due.items.map((item) => (
                    <tr key={item.asset_id} className="border-b border-slate-100">
                      <td className="px-3 py-3">
                        <Link className="font-medium text-university-700 hover:underline" to={`/assets/${item.asset_id}`}>
                          {item.asset_code}
                        </Link>
                        <p className="text-xs text-slate-500">{item.manufacturer_name} · {item.model_number}</p>
                      </td>
                      <td className="px-3 py-3">{item.laboratory_name} · {item.room_number}</td>
                      <td className="px-3 py-3">{item.last_calibrated_date ?? "Not recorded"}</td>
                      <td className="px-3 py-3">{item.next_calibration_due}</td>
                      <td className="px-3 py-3">
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${item.status === "OVERDUE" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {due.items.length === 0 && (
                    <tr><td className="px-3 py-5 text-slate-500" colSpan={5}>No assets are due within this window.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
              <span>{due.total} asset(s)</span>
              <div className="flex gap-2">
                <button type="button" disabled={duePage <= 1 || dueLoading} className="rounded border px-3 py-1 disabled:opacity-50" onClick={() => void loadDue(duePage - 1)}>Previous</button>
                <span className="px-2 py-1">Page {due.page} of {due.pages || 1}</span>
                <button type="button" disabled={duePage >= due.pages || dueLoading} className="rounded border px-3 py-1 disabled:opacity-50" onClick={() => void loadDue(duePage + 1)}>Next</button>
              </div>
            </div>
          </>
        )}
      </section>

      {canRecord && (
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-xl font-semibold text-slate-900">Record calibration</h2>
          <p className="mt-1 text-sm text-slate-600">
            The next due date is calculated from the asset category&apos;s approved default interval.
          </p>
          <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={(event) => void submitCalibration(event)}>
            <label className="text-sm text-slate-700">
              Asset code
              <input required maxLength={100} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={assetCode} onChange={(event) => setAssetCode(event.target.value)} />
            </label>
            <label className="text-sm text-slate-700">
              Calibration date
              <input required type="date" className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={calibrationDate} onChange={(event) => setCalibrationDate(event.target.value)} />
            </label>
            <label className="text-sm text-slate-700">
              Standard used
              <input required maxLength={150} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={standardUsed} onChange={(event) => setStandardUsed(event.target.value)} />
            </label>
            <label className="text-sm text-slate-700">
              Result
              <select className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={passed} onChange={(event) => setPassed(event.target.value)}>
                <option value="true">Passed</option>
                <option value="false">Failed</option>
              </select>
            </label>
            <label className="text-sm text-slate-700">
              Certificate reference (optional)
              <input maxLength={100} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={certificateReference} onChange={(event) => setCertificateReference(event.target.value)} />
            </label>
            <label className="text-sm text-slate-700">
              Accreditation body (optional)
              <input maxLength={150} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={accreditationBody} onChange={(event) => setAccreditationBody(event.target.value)} />
            </label>
            <label className="text-sm text-slate-700 sm:col-span-2">
              Technical notes (optional)
              <textarea rows={3} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={notes} onChange={(event) => setNotes(event.target.value)} />
            </label>
            {formError && <p role="alert" className="sm:col-span-2 text-sm text-red-700">{formError}</p>}
            {success && <p role="status" className="sm:col-span-2 text-sm text-green-700">{success}</p>}
            <div className="sm:col-span-2">
              <button type="submit" disabled={saving} className="rounded bg-university-700 px-4 py-2 text-sm font-medium text-white hover:bg-university-800 disabled:opacity-60">
                {saving ? "Saving…" : "Save calibration"}
              </button>
            </div>
          </form>
        </section>
      )}

      {canReadHistory && (
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-xl font-semibold text-slate-900">Calibration history</h2>
          {historyError && <p role="alert" className="mt-3 text-sm text-red-700">{historyError}</p>}
          {historyLoading ? (
            <p className="mt-4 text-sm text-slate-600">Loading calibration history…</p>
          ) : (
            <>
              <div
                className="table-scroll mt-4"
                role="region"
                aria-label="Calibration history records"
                tabIndex={0}
              >
                <table className="w-full min-w-[750px] text-left text-sm">
                  <thead className="border-b border-slate-200 text-slate-600">
                    <tr>
                      <th className="px-3 py-2 font-medium">Date</th>
                      <th className="px-3 py-2 font-medium">Asset</th>
                      <th className="px-3 py-2 font-medium">Technician</th>
                      <th className="px-3 py-2 font-medium">Standard</th>
                      <th className="px-3 py-2 font-medium">Result</th>
                      <th className="px-3 py-2 font-medium">Next due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.items.map((record) => (
                      <tr key={record.id} className="border-b border-slate-100">
                        <td className="px-3 py-3">{record.calibration_date}</td>
                        <td className="px-3 py-3"><Link className="text-university-700 hover:underline" to={`/assets/${record.asset_id}`}>{record.asset_code}</Link></td>
                        <td className="px-3 py-3">{record.technician_name}</td>
                        <td className="px-3 py-3">{record.standard_used}</td>
                        <td className="px-3 py-3">{record.passed ? "Passed" : "Failed"}</td>
                        <td className="px-3 py-3">{record.next_due_date}</td>
                      </tr>
                    ))}
                    {history.items.length === 0 && (
                      <tr><td className="px-3 py-5 text-slate-500" colSpan={6}>No calibration records have been recorded.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
                <span>{history.total} record(s)</span>
                <div className="flex gap-2">
                  <button type="button" disabled={historyPage <= 1 || historyLoading} className="rounded border px-3 py-1 disabled:opacity-50" onClick={() => setHistoryPage((current) => current - 1)}>Previous</button>
                  <span className="px-2 py-1">Page {history.page} of {history.pages || 1}</span>
                  <button type="button" disabled={historyPage >= history.pages || historyLoading} className="rounded border px-3 py-1 disabled:opacity-50" onClick={() => setHistoryPage((current) => current + 1)}>Next</button>
                </div>
              </div>
            </>
          )}
        </section>
      )}
    </section>
  );
}
