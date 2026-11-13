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
│   │       └── [QR Link Entry]  /assets/scan?code=...   │
│   ├── [Asset Categories]       /admin/asset-categories │
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
| **QR Passport Entry** | `/assets/scan?code=...` | Protected | Protected | Protected | Protected | Protected |
| **Register New Asset**| `/assets/register` | Visible | Hidden | Visible | Hidden | Hidden |
| **Maintenance Hub** | `/maintenance` | Full Queue | My Assigned | My Lab | My Lab | Read-Only |
| **Submit Fault** | `/maintenance/report`| Visible | Hidden | Visible | Visible | Hidden |
| **Calibration Log** | `/calibrations` | Full Access | Record Entry| View Due | View Due | Read-Only |
| **Custody Transfers** | `/transfers` | Final Approval| Hidden | Initiate/Accept| Hidden | Read-Only |
| **Reports & Analytics**| `/reports` | Full Access | Hidden | Dept Scoped | Hidden | Full Access |
| **Audit Ledger** | `/reports/audits` | Visible | Hidden | Hidden | Hidden | Visible |
| **User Management** | `/admin/users` | Visible | Hidden | Hidden | Hidden | Hidden |
| **Hierarchy Setup** | `/admin/hierarchy` | Visible | Hidden | Hidden | Hidden | Hidden |
| **Asset Categories** | `/admin/asset-categories` | Visible | Hidden | Hidden | Hidden | Hidden |

The implemented hierarchy screen is restricted to `ULMD_ADMIN` and provides tabs for colleges, departments, laboratories, and rooms. Location is the approved laboratory-to-room structure, not a separate entity.

The Stage 4 asset list and passport are available to all authenticated roles. Registration and metadata editing are guarded for `ULMD_ADMIN` and `LAB_MANAGER`; the backend additionally verifies that a manager is assigned to the asset's laboratory. The QR link-entry route requires authentication, resolves the URL's asset code, and redirects to the passport; the original path and query are preserved through login. Asset-category administration is currently `ULMD_ADMIN` only as a provisional restriction pending policy confirmation.

Stage 5 implements `/transfers` for `ULMD_ADMIN`, `LAB_MANAGER`, and read-only `AUDITOR`. Lab Managers see only transfers involving laboratories they currently manage. Initiation, destination acceptance/rejection, and ULMD approval controls are displayed by role and transfer status; the API independently checks the actor's current designated-laboratory relationship.

---

## 3. Route Guard & Authorization Architecture

1. **`PublicRoute`:** Accessible without authentication (e.g., `/login`). If an authenticated user accesses this route, they are automatically redirected to `/dashboard`.
2. **`ProtectedRoute`:** Requires a valid, non-expired JWT access token. If missing or expired, the user is redirected to `/login` with an appended redirect parameter (`/login?returnUrl=/assets/14`).
3. **`RoleGuard`:** Wraps sensitive views (e.g., `/admin/*`, `/assets/register`) and verifies that `currentUser.role` exists in the allowed roles array. Unauthorized access renders a high-contrast `403 Forbidden` unauthorized view with a button returning to the main dashboard.
