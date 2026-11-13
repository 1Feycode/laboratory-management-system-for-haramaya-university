import { useEffect, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";

interface AssetQrScannerProps {
  onScanned: (value: string) => void;
  onClose: () => void;
}

export default function AssetQrScanner({
  onScanned,
  onClose,
}: AssetQrScannerProps) {
  const [error, setError] = useState("");

  useEffect(() => {
    const scanner = new Html5Qrcode("asset-qr-reader");
    let active = true;
    void scanner
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 240, height: 240 } },
        (decodedText) => {
          if (active) {
            active = false;
            onScanned(decodedText.trim());
          }
        },
        () => undefined,
      )
      .catch((cause: unknown) => {
        if (active) {
          setError(
            cause instanceof Error
              ? cause.message
              : "The camera could not be started. Check browser camera permissions.",
          );
        }
      });

    return () => {
      active = false;
      if (scanner.isScanning) {
        void scanner.stop().catch((cause: unknown) => {
          console.error("Could not stop the QR scanner", cause);
        });
      }
    };
  }, [onScanned]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
      <section
        aria-labelledby="asset-scanner-title"
        aria-modal="true"
        className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl"
        role="dialog"
      >
        <div className="flex items-center justify-between">
          <h2 id="asset-scanner-title" className="text-xl font-semibold">
            Scan asset QR code
          </h2>
          <button type="button" className="text-sm text-slate-600" onClick={onClose}>
            Close
          </button>
        </div>
        <div id="asset-qr-reader" className="mt-4 min-h-64" />
        {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
        <p className="mt-3 text-sm text-slate-600">
          Camera access is required. The QR code contains the asset code only.
        </p>
      </section>
    </div>
  );
}
