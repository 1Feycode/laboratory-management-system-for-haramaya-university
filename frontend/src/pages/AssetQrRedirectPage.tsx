import { isAxiosError } from "axios";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { lookupAsset } from "../services/assets";

function messageFromError(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "The asset could not be found.";
}

export default function AssetQrRedirectPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const assetCode = searchParams.get("code")?.trim() ?? "";
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    if (!assetCode) {
      setError("This asset link does not include an asset code.");
      return () => {
        active = false;
      };
    }

    void lookupAsset(assetCode)
      .then((asset) => {
        if (active) navigate(`/assets/${asset.id}`, { replace: true });
      })
      .catch((cause: unknown) => {
        if (active) setError(messageFromError(cause));
      });
    return () => {
      active = false;
    };
  }, [assetCode, navigate]);

  return (
    <section className="mx-auto max-w-2xl rounded-xl border border-slate-200 bg-white p-8">
      <h1 className="text-2xl font-semibold text-slate-900">Opening asset passport</h1>
      {error ? (
        <>
          <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>
          <Link className="mt-5 inline-block text-university-700 underline" to="/assets">
            Browse laboratory assets
          </Link>
        </>
      ) : (
        <p className="mt-3 text-slate-600">Looking up the asset…</p>
      )}
    </section>
  );
}
