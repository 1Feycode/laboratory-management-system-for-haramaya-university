import { useEffect, useState } from "react";
import { getApplicationHealth } from "../services/health";

type BackendStatus = "checking" | "available" | "unavailable";

export default function FoundationPage() {
  const [status, setStatus] = useState<BackendStatus>("checking");

  useEffect(() => {
    let active = true;

    getApplicationHealth()
      .then(() => {
        if (active) setStatus("available");
      })
      .catch(() => {
        if (active) setStatus("unavailable");
      });

    return () => {
      active = false;
    };
  }, []);

  const statusText = {
    checking: "Checking backend connection…",
    available: "Backend and database are ready",
    unavailable: "Backend or database is unavailable",
  }[status];

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
        Application connectivity
      </p>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900">
        Laboratory Asset Management
      </h1>
      <p className="mt-3 max-w-2xl leading-7 text-slate-600">
        The authenticated workspace provides role-based access to asset,
        maintenance, transfer, calibration, reporting, and administration
        workflows.
      </p>
      <div className="mt-8 flex items-center gap-3" role="status" aria-live="polite">
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            status === "available"
              ? "bg-emerald-500"
              : status === "unavailable"
                ? "bg-rose-500"
                : "bg-amber-400"
          }`}
        />
        <span className="text-sm text-slate-700">{statusText}</span>
      </div>
    </section>
  );
}
