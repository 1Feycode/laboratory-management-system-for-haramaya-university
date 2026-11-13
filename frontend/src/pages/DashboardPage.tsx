import { useAuth } from "../contexts/AuthContext";

export default function DashboardPage() {
  const { user } = useAuth();
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
        Stage 2 · Authentication and user management
      </p>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900">
        Welcome, {user?.full_name}
      </h1>
      <p className="mt-3 leading-7 text-slate-600">
        Your account is authenticated as {user?.role}. Business dashboards and
        laboratory modules will be introduced in later stages.
      </p>
    </section>
  );
}
