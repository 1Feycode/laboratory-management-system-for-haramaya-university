# Navigation Structure and Information Architecture

This document maps the user navigation flow, route hierarchy, and role-based menu visibility for the Laboratory Asset Management and Maintenance Tracking System.

---

## 1. Information Architecture Map

```
┌────────────────────────────────────────────────────────┐
│                   MAIN APPLICATION SHELL               │
│   Top Navbar (Brand, Universal Search, User Profile)   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    SIDEBAR NAVIGATION                  │
│                                                        │
│   ├── [Dashboard]              /dashboard              │
│   ├── [Asset Inventory]        /assets                 │
│   │   ├── [Register Asset]     /assets/register        │
│   │   └── [Asset Passport]     /assets/:id             │
│   ├── [Maintenance Hub]        /maintenance            │
│   │   ├── [Submit Fault]       /maintenance/report     │
│   │   └── [Ticket Details]     /maintenance/:id        │
│   ├── [Calibration Log]        /calibrations           │
│   ├── [Custody Transfers]      /transfers              │
│   ├── [Reports & Analytics]    /reports                │
│   │   └── [Audit Ledger]       /reports/audits         │
│   └── [System Administration]  /admin                  │
│       ├── [Hierarchy Setup]    /admin/hierarchy        │
│       └── [User Provisioning]  /admin/users            │
└────────────────────────────────────────────────────────┘
```

---

## 2. Role-Based Menu Visibility Matrix

| Navigation Item | Route | `ULMD_ADMIN` | `MAINTENANCE_TECH` | `LAB_MANAGER` | `LAB_TECH` | `AUDITOR` |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Dashboard** | `/dashboard` | Visible | Visible | Visible | Visible | Visible |
| **Asset Inventory** | `/assets` | Visible | Visible | Visible | Visible | Visible |
| **Register New Asset**| `/assets/register` | Visible | Hidden | Visible | Hidden | Hidden |
| **Maintenance Hub** | `/maintenance` | Full Queue | My Assigned | My Lab | My Lab | Read-Only |
| **Submit Fault** | `/maintenance/report`| Visible | Hidden | Visible | Visible | Hidden |
| **Calibration Log** | `/calibrations` | Full Access | Record Entry| View Due | View Due | Read-Only |
| **Custody Transfers** | `/transfers` | Final Approval| Hidden | Initiate/Accept| Hidden | Read-Only |
| **Reports & Analytics**| `/reports` | Full Access | Hidden | Dept Scoped | Hidden | Full Access |
| **Audit Ledger** | `/reports/audits` | Visible | Hidden | Hidden | Hidden | Visible |
| **User Management** | `/admin/users` | Visible | Hidden | Hidden | Hidden | Hidden |
| **Hierarchy Setup** | `/admin/hierarchy` | Visible | Hidden | Hidden | Hidden | Hidden |

The implemented hierarchy screen is restricted to `ULMD_ADMIN` and provides tabs for colleges, departments, laboratories, and rooms. Location is the approved laboratory-to-room structure, not a separate entity.

---

## 3. Route Guard & Authorization Architecture

1. **`PublicRoute`:** Accessible without authentication (e.g., `/login`). If an authenticated user accesses this route, they are automatically redirected to `/dashboard`.
2. **`ProtectedRoute`:** Requires a valid, non-expired JWT access token. If missing or expired, the user is redirected to `/login` with an appended redirect parameter (`/login?returnUrl=/assets/14`).
3. **`RoleGuard`:** Wraps sensitive views (e.g., `/admin/*`, `/assets/register`) and verifies that `currentUser.role` exists in the allowed roles array. Unauthorized access renders a high-contrast `403 Forbidden` unauthorized view with a button returning to the main dashboard.
