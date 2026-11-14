import { isAxiosError } from "axios";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { getAsset, getAssetQr, type Asset, type AssetStatus } from "../services/assets";
import { listTransfers, type AssetTransfer } from "../services/transfers";

function messageFromError(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "The asset could not be loaded.";
}

function statusStyle(status: AssetStatus): string {
  if (status === "OPERATIONAL") return "bg-green-100 text-green-800";
  if (status === "DEFECTIVE") return "bg-red-100 text-red-800";
  if (status === "UNDER_MAINTENANCE") return "bg-amber-100 text-amber-800";
  return "bg-slate-100 text-slate-800";
}

function displayDate(value: string | null): string {
  return value ? new Date(`${value}T00:00:00`).toLocaleDateString() : "Not recorded";
}

export default function AssetDetailPage() {
  const { assetId } = useParams<{ assetId: string }>();
  const { user } = useAuth();
  const canEdit = user?.role === "ULMD_ADMIN" || user?.role === "LAB_MANAGER";
  const [asset, setAsset] = useState<Asset | null>(null);
  const [transfers, setTransfers] = useState<AssetTransfer[]>([]);
  const [qrUrl, setQrUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [transferLoading, setTransferLoading] = useState(true);
  const [error, setError] = useState("");
  const [qrError, setQrError] = useState("");
  const [transferError, setTransferError] = useState("");

  useEffect(() => {
    if (!assetId) return;
    let active = true;
    let objectUrl = "";
    setLoading(true);
    setError("");
    void getAsset(assetId)
      .then((record) => {
        if (active) setAsset(record);
      })
      .catch((cause: unknown) => {
        if (active) setError(messageFromError(cause));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    void getAssetQr(assetId)
      .then((blob) => {
        if (active) {
          objectUrl = URL.createObjectURL(blob);
          setQrUrl(objectUrl);
        }
      })
      .catch((cause: unknown) => {
        if (active) setQrError(messageFromError(cause));
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [assetId]);

  useEffect(() => {
    if (
      !assetId ||
      !["ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"].includes(user?.role ?? "")
    ) {
      setTransfers([]);
      setTransferLoading(false);
      return;
    }
    let active = true;
    setTransferLoading(true);
    setTransferError("");
    setTransfers([]);
    void listTransfers({ page: 1, size: 100, asset_id: assetId })
      .then((result) => {
        if (active) setTransfers(result.items);
      })
      .catch((cause: unknown) => {
        if (active) setTransferError(messageFromError(cause));
      })
      .finally(() => {
        if (active) setTransferLoading(false);
      });
    return () => {
      active = false;
    };
  }, [assetId, user?.role]);

  if (loading) return <p className="text-slate-600">Loading asset…</p>;
  if (error || !asset) {
    return (
      <section>
        <p role="alert" className="rounded bg-red-50 p-3 text-red-800">
          {error || "Asset not found."}
        </p>
        <Link className="mt-4 inline-block text-university-700 hover:underline" to="/assets">Back to assets</Link>
      </section>
    );
  }

  return (
    <section>
      <Link to="/assets" className="text-sm text-university-700 hover:underline">← All assets</Link>
      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold text-slate-900">{asset.asset_code}</h1>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusStyle(asset.operational_status)}`}>
              {asset.operational_status.replace(/_/g, " ")}
            </span>
          </div>
          <p className="mt-2 text-lg text-slate-700">{asset.model_number} · {asset.manufacturer_name}</p>
          <p className="mt-1 text-sm text-slate-500">Category: {asset.category_name}</p>
        </div>
        <div className="flex gap-2">
          <button type="button" className="rounded border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50" onClick={() => window.print()}>
            Print asset passport
          </button>
          {canEdit && asset.operational_status !== "TRANSFER_PENDING" && (
            <Link className="rounded bg-university-700 px-4 py-2 text-sm font-medium text-white hover:bg-university-800" to={`/assets/${asset.id}/edit`}>
              Edit details
            </Link>
          )}
          {["ULMD_ADMIN", "LAB_MANAGER", "LAB_TECH"].includes(user?.role ?? "") &&
            asset.operational_status === "OPERATIONAL" && (
              <Link
                className="rounded border border-amber-400 px-4 py-2 text-sm font-medium text-amber-800 hover:bg-amber-50"
                to={`/maintenance?assetCode=${encodeURIComponent(asset.asset_code)}`}
              >
                Report fault
              </Link>
            )}
        </div>
      </div>

      <div className="mt-7 grid gap-6 lg:grid-cols-[1fr_260px]">
        <div className="space-y-6">
          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-slate-900">Identification</h2>
            <dl className="mt-4 grid gap-4 sm:grid-cols-2">
              <div><dt className="text-xs uppercase text-slate-500">Asset code</dt><dd className="mt-1">{asset.asset_code}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Legacy tag</dt><dd className="mt-1">{asset.legacy_tag_number || "Not recorded"}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Serial number</dt><dd className="mt-1">{asset.serial_number}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Model number</dt><dd className="mt-1">{asset.model_number}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Manufacturer</dt><dd className="mt-1">{asset.manufacturer_name}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Calibration category</dt><dd className="mt-1">{asset.requires_calibration ? `Required · ${asset.default_calibration_interval_days} day default interval` : "Not required by category"}</dd></div>
            </dl>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-slate-900">Custodian location</h2>
            <p className="mt-3 text-slate-700">{asset.college_name} / {asset.department_name}</p>
            <p className="mt-1 text-slate-700">{asset.laboratory_name} / {asset.building_name}, room {asset.room_number}</p>
            {(user?.role === "ULMD_ADMIN" || user?.role === "LAB_MANAGER") &&
              asset.operational_status === "OPERATIONAL" && (
                <Link
                  className="mt-4 inline-block rounded bg-university-700 px-3 py-2 text-sm font-medium text-white hover:bg-university-800"
                  to="/transfers"
                >
                  Initiate custody transfer
                </Link>
              )}
          </section>

          {["ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"].includes(user?.role ?? "") && (
            <section className="rounded-xl border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-semibold text-slate-900">
                Custody transfer history
              </h2>
              {transferError ? (
                <p role="alert" className="mt-3 text-sm text-red-700">
                  {transferError}
                </p>
              ) : transferLoading ? (
                <p className="mt-3 text-sm text-slate-500">
                  Loading transfer history…
                </p>
              ) : transfers.length ? (
                <ol className="mt-4 space-y-4">
                  {transfers.map((transfer) => (
                    <li
                      key={transfer.id}
                      className="border-l-2 border-slate-200 pl-4"
                    >
                      <p className="font-medium text-slate-800">
                        {transfer.origin_laboratory_name} /{" "}
                        {transfer.origin_building_name}, room{" "}
                        {transfer.origin_room_number}
                        {" → "}
                        {transfer.target_laboratory_name} /{" "}
                        {transfer.target_building_name}, room{" "}
                        {transfer.target_room_number}
                      </p>
                      <p className="mt-1 text-sm text-slate-600">
                        {transfer.status.replace(/_/g, " ")} ·{" "}
                        {new Date(transfer.created_at).toLocaleString()}
                      </p>
                      <p className="mt-1 text-sm text-slate-600">
                        {transfer.transfer_reason}
                      </p>
                      <ul className="mt-2 space-y-1 text-xs text-slate-500">
                        {transfer.status_history.map((event, index) => (
                          <li key={`${event.action}-${event.occurred_at}-${index}`}>
                            {event.new_status.replace(/_/g, " ")} ·{" "}
                            {event.actor_name || "Former user"} ·{" "}
                            {new Date(event.occurred_at).toLocaleString()}
                            {event.notes && <p className="mt-1">{event.notes}</p>}
                          </li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="mt-3 text-sm text-slate-500">
                  No custody transfers have been recorded for this asset.
                </p>
              )}
            </section>
          )}

          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-slate-900">Purchase and calibration dates</h2>
            <dl className="mt-4 grid gap-4 sm:grid-cols-2">
              <div><dt className="text-xs uppercase text-slate-500">Purchase date</dt><dd className="mt-1">{displayDate(asset.purchase_date)}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Commissioning date</dt><dd className="mt-1">{displayDate(asset.commissioning_date)}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Warranty expiry</dt><dd className="mt-1">{displayDate(asset.warranty_expiry_date)}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Last calibrated</dt><dd className="mt-1">{displayDate(asset.last_calibrated_date)}</dd></div>
              <div><dt className="text-xs uppercase text-slate-500">Next calibration due</dt><dd className="mt-1">{displayDate(asset.next_calibration_due)}</dd></div>
            </dl>
          </section>
        </div>

        <aside className="h-fit rounded-xl border border-slate-200 bg-white p-5 text-center">
          <h2 className="font-semibold text-slate-900">Asset QR code</h2>
          {qrUrl ? (
            <img className="mx-auto mt-3 max-w-full" src={qrUrl} alt={`QR code for ${asset.asset_code}`} />
          ) : qrError ? (
            <p role="alert" className="mt-3 text-sm text-red-700">{qrError}</p>
          ) : (
            <p className="mt-3 text-sm text-slate-500">Generating QR code…</p>
          )}
          <p className="mt-2 break-all text-xs text-slate-500">{asset.asset_code}</p>
          <p className="mt-3 text-xs text-slate-500">Created {new Date(asset.created_at).toLocaleString()}</p>
        </aside>
      </div>
    </section>
  );
}
