import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await logout();
    } catch {
      navigate("/login", { replace: true, state: { logoutError: true } });
    }
  }

  return (
    <div className="min-h-screen">
      <header className="bg-university-800 text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <span className="text-sm font-semibold tracking-wide">
            HARAMAYA UNIVERSITY
          </span>
          <div className="flex items-center gap-4">
            <span className="border-l border-white/30 pl-4 text-sm text-white/80">
              Laboratory Assets
            </span>
            {user && (
              <>
                <span className="hidden text-sm text-white/80 sm:inline">
                  {user.full_name} · {user.role}
                </span>
                <button
                  type="button"
                  onClick={() => void handleLogout()}
                  className="rounded border border-white/40 px-3 py-1.5 text-sm hover:bg-white/10"
                >
                  Sign out
                </button>
              </>
            )}
          </div>
        </div>
      </header>
      {user && (
        <nav className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl gap-5 px-6 py-3 text-sm">
            <NavLink to="/dashboard" className="text-slate-700 hover:text-university-700">
              Dashboard
            </NavLink>
            <NavLink to="/assets" className="text-slate-700 hover:text-university-700">
              Assets
            </NavLink>
            {["ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"].includes(user.role) && (
              <NavLink
                to="/transfers"
                className="text-slate-700 hover:text-university-700"
              >
                Custody transfers
              </NavLink>
            )}
            {user.role === "ULMD_ADMIN" && (
              <>
                <NavLink
                  to="/admin/users"
                  className="text-slate-700 hover:text-university-700"
                >
                  User management
                </NavLink>
                <NavLink
                  to="/admin/hierarchy"
                  className="text-slate-700 hover:text-university-700"
                >
                  Organizational structure
                </NavLink>
                <NavLink
                  to="/admin/asset-categories"
                  className="text-slate-700 hover:text-university-700"
                >
                  Asset categories
                </NavLink>
              </>
            )}
          </div>
        </nav>
      )}
      <main className="mx-auto max-w-6xl px-6 py-10"><Outlet /></main>
    </div>
  );
}
