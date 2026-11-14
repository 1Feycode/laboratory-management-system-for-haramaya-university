import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import type { AppRole } from "../../types/auth";

interface NavigationItem {
  label: string;
  to: string;
  roles?: AppRole[];
}

interface NavigationSection {
  title: string;
  items: NavigationItem[];
}

const navigationSections: NavigationSection[] = [
  {
    title: "Workspace",
    items: [
      { label: "Dashboard", to: "/dashboard" },
      { label: "Assets", to: "/assets" },
      { label: "Maintenance", to: "/maintenance" },
      { label: "Calibration", to: "/calibrations" },
      {
        label: "Custody transfers",
        to: "/transfers",
        roles: ["ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"],
      },
      {
        label: "Reports",
        to: "/reports",
        roles: ["ULMD_ADMIN", "LAB_MANAGER", "AUDITOR"],
      },
    ],
  },
  {
    title: "Administration",
    items: [
      {
        label: "User management",
        to: "/admin/users",
        roles: ["ULMD_ADMIN"],
      },
      {
        label: "Organizational structure",
        to: "/admin/hierarchy",
        roles: ["ULMD_ADMIN"],
      },
      {
        label: "Asset categories",
        to: "/admin/asset-categories",
        roles: ["ULMD_ADMIN"],
      },
    ],
  },
];

function NavigationLinks({
  role,
  onNavigate,
}: {
  role: AppRole;
  onNavigate?: () => void;
}) {
  return (
    <nav aria-label="Application navigation" className="space-y-7">
      {navigationSections.map((section) => {
        const visibleItems = section.items.filter(
          (item) => !item.roles || item.roles.includes(role),
        );
        if (visibleItems.length === 0) return null;

        return (
          <section key={section.title}>
            <h2 className="px-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
              {section.title}
            </h2>
            <ul className="mt-2 space-y-1">
              {visibleItems.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === "/dashboard"}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      `flex min-h-11 items-center rounded-lg border-l-2 px-3 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700 ${
                        isActive
                          ? "border-university-700 bg-university-50 text-university-950"
                            : "border-transparent text-slate-700 hover:bg-university-50 hover:text-university-900"
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </nav>
  );
}

function pageLabel(pathname: string): string {
  const exactLabels: Record<string, string> = {
    "/dashboard": "Dashboard",
    "/assets": "Assets",
    "/maintenance": "Maintenance",
    "/calibrations": "Calibration",
    "/transfers": "Custody transfers",
    "/reports": "Reports",
    "/admin/users": "User management",
    "/admin/hierarchy": "Organizational structure",
    "/admin/asset-categories": "Asset categories",
    "/foundation": "System health",
  };
  if (exactLabels[pathname]) return exactLabels[pathname];
  if (pathname === "/assets/register") return "Register asset";
  if (pathname.startsWith("/assets/") && pathname.endsWith("/edit")) {
    return "Edit asset";
  }
  if (pathname === "/assets/scan") return "QR asset lookup";
  if (pathname.startsWith("/assets/")) return "Asset passport";
  return "Workspace";
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);

  useEffect(() => {
    setMobileNavigationOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileNavigationOpen) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setMobileNavigationOpen(false);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobileNavigationOpen]);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      navigate("/login", { replace: true, state: { logoutError: true } });
    }
  }

  const currentPage = pageLabel(location.pathname);
  const homePath = user ? "/dashboard" : "/foundation";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <a
        href="#main-content"
        className="sr-only z-50 rounded-md bg-white px-4 py-3 text-slate-900 focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-slate-700"
      >
        Skip to main content
      </a>

      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white">
        <div className="flex min-h-16 items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            {user && (
              <button
                type="button"
                aria-label={
                  mobileNavigationOpen
                    ? "Close navigation menu"
                    : "Open navigation menu"
                }
                aria-expanded={mobileNavigationOpen}
                aria-controls="mobile-primary-navigation"
                onClick={() =>
                  setMobileNavigationOpen((isOpen) => !isOpen)
                }
                className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700 lg:hidden"
              >
                <svg
                  aria-hidden="true"
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  {mobileNavigationOpen ? (
                    <path
                      d="M6 6l12 12M18 6L6 18"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                    />
                  ) : (
                    <path
                      d="M4 6h16M4 12h16M4 18h16"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                    />
                  )}
                </svg>
              </button>
            )}
            <Link
              to={homePath}
              aria-label="Haramaya University Laboratory Asset Management"
              className="min-w-0 rounded-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-university-700"
            >
              <div className="flex items-center gap-3">
                <img
                  src="/assets/haramaya-university-logo.png"
                  alt="Haramaya University"
                  className="h-7 w-auto max-w-[145px] object-contain sm:h-8 sm:max-w-[168px]"
                />
                <span className="hidden border-l border-slate-200 pl-3 text-xs font-medium leading-5 text-slate-600 xl:block">
                  Laboratory Asset Management
                </span>
              </div>
              <span className="sr-only">
                Laboratory Asset Management
              </span>
            </Link>
          </div>

          <div className="flex shrink-0 items-center gap-2 sm:gap-4">
            {user && (
              <div className="hidden min-w-0 text-right sm:block">
                <p className="max-w-48 truncate text-sm font-medium text-slate-800">
                  {user.full_name}
                </p>
                <p className="text-xs text-slate-600">{user.role.replace(/_/g, " ")}</p>
              </div>
            )}
            {user && (
              <button
                type="button"
                onClick={() => void handleLogout()}
                className="inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-300 px-3 text-sm font-medium text-slate-700 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700"
              >
                Sign out
              </button>
            )}
          </div>
        </div>

        {user && (
          <div
            id="mobile-primary-navigation"
            hidden={!mobileNavigationOpen}
            className="border-t border-slate-200 bg-white px-4 py-5 sm:px-6 lg:hidden"
          >
            <NavigationLinks
              role={user.role}
              onNavigate={() => setMobileNavigationOpen(false)}
            />
          </div>
        )}
      </header>

      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-[1800px]">
        {user && (
          <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-64 shrink-0 overflow-y-auto border-r border-slate-200 bg-white px-4 py-7 lg:block">
            <Link
              to="/dashboard"
              className="mb-7 block rounded-lg border border-university-100 bg-university-50 p-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-university-700"
              aria-label="Haramaya University dashboard"
            >
              <img
                src="/assets/haramaya-university-logo.png"
                alt="Haramaya University"
                className="h-auto w-full max-w-[190px] object-contain"
              />
              <span className="mt-2 block text-xs font-semibold text-university-900">
                Laboratory Asset Management
              </span>
            </Link>
            <NavigationLinks role={user.role} />
          </aside>
        )}

        <main
          id="main-content"
          tabIndex={-1}
          className="min-w-0 flex-1 px-4 py-6 focus:outline-none sm:px-6 sm:py-8 lg:px-10 lg:py-10"
        >
          <nav aria-label="Breadcrumb" className="mb-6">
            <ol className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
              <li>
                <Link
                  to={homePath}
                  className="rounded-sm hover:text-slate-950 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-700"
                >
                  {user ? "Workspace" : "System status"}
                </Link>
              </li>
              <li aria-hidden="true">/</li>
              <li aria-current="page" className="font-medium text-slate-900">
                {currentPage}
              </li>
            </ol>
          </nav>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
