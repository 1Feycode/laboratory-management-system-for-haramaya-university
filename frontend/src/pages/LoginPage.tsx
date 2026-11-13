import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

function messageFrom(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "status" in error.response &&
    error.response.status === 403
  ) {
    return "This account is inactive. Contact a ULMD administrator.";
  }
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "status" in error.response &&
    error.response.status === 429
  ) {
    return "Too many sign-in attempts. Wait briefly before trying again.";
  }
  return "The email or password is incorrect.";
}

export default function LoginPage() {
  const { login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const returnUrl = (location.state as { returnUrl?: string } | null)?.returnUrl;
  const logoutError = (location.state as { logoutError?: boolean } | null)?.logoutError;
  const safeReturnUrl =
    returnUrl?.startsWith("/") && !returnUrl.startsWith("//")
      ? returnUrl
      : "/dashboard";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(safeReturnUrl, { replace: true });
    } catch (loginError) {
      setError(messageFrom(loginError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-6 py-12">
      <section className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
          Haramaya University
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">
          Sign in to Laboratory Assets
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Use the institutional account provisioned by your ULMD administrator.
        </p>
        {logoutError && (
          <p className="mt-4 rounded-md bg-amber-50 p-3 text-sm text-amber-900" role="alert">
            Your local session ended, but the server could not confirm logout. Sign in again
            only after checking your connection.
          </p>
        )}
        <form className="mt-7 space-y-5" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-slate-700">
            Institutional email
            <input
              autoComplete="username"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Password
            <input
              autoComplete="current-password"
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
            />
          </label>
          {error && (
            <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800" role="alert">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-university-800 px-4 py-2.5 font-semibold text-white hover:bg-university-700 disabled:opacity-60"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <Link className="mt-6 inline-block text-sm text-university-700 underline" to="/foundation">
          View system health
        </Link>
      </section>
    </main>
  );
}
