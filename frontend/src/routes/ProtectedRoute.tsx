import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export function ProtectedRoute() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return <p className="p-8 text-center text-slate-600">Checking session…</p>;
  }
  if (status === "unauthenticated") {
    const returnUrl = `${location.pathname}${location.search}`;
    return <Navigate to="/login" replace state={{ returnUrl }} />;
  }
  return <Outlet />;
}

export function RoleGuard({ roles }: { roles: string[] }) {
  const { user, status } = useAuth();
  if (status === "loading") {
    return <p className="p-8 text-center text-slate-600">Checking permissions…</p>;
  }
  if (!user || !roles.includes(user.role)) {
    return (
      <main className="mx-auto max-w-3xl p-8">
        <h1 className="text-2xl font-semibold">403 · Forbidden</h1>
        <p className="mt-2 text-slate-600">
          Your account does not have permission to view this page.
        </p>
      </main>
    );
  }
  return <Outlet />;
}

export function PublicOnlyRoute() {
  const { status } = useAuth();
  if (status === "loading") {
    return <p className="p-8 text-center text-slate-600">Checking session…</p>;
  }
  return status === "authenticated" ? <Navigate to="/dashboard" replace /> : <Outlet />;
}
