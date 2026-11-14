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
│   │   ├── [Submit Fault]       Embedded in page        │
│   │   └── [Ticket Details]     Work-order cards        │
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
| **Maintenance Hub & Submit Fault** | `/maintenance` | Queue, report, assign, log, verify | Assigned queue, status, log | Own-lab queue, report, verify | Department queue, report | Read-only |
| **Calibration Log** | `/calibrations` | Record / full history | Record / full history | View Due | View Due | Read-only history / due |
| **Custody Transfers** | `/transfers` | Final Approval| Hidden | Initiate/Accept| Hidden | Read-Only |
| **Reports & Analytics**| `/reports` | Full Access | Hidden | Dept Scoped | Hidden | Full Access |
| **Audit Ledger** | `/reports/audits` | Visible | Hidden | Hidden | Hidden | Visible |
| **User Management** | `/admin/users` | Visible | Hidden | Hidden | Hidden | Hidden |
| **Hierarchy Setup** | `/admin/hierarchy` | Visible | Hidden | Hidden | Hidden | Hidden |
| **Asset Categories** | `/admin/asset-categories` | Visible | Hidden | Hidden | Hidden | Hidden |

The implemented hierarchy screen is restricted to `ULMD_ADMIN` and provides tabs for colleges, departments, laboratories, and rooms. Location is the approved laboratory-to-room structure, not a separate entity.

The Stage 4 asset list and passport are available to all authenticated roles. Registration and metadata editing are guarded for `ULMD_ADMIN` and `LAB_MANAGER`; the backend additionally verifies that a manager is assigned to the asset's laboratory. The QR link-entry route requires authentication, resolves the URL's asset code, and redirects to the passport; the original path and query are preserved through login. Asset-category administration is currently `ULMD_ADMIN` only as a provisional restriction pending policy confirmation.

Stage 5 implements `/transfers` for `ULMD_ADMIN`, `LAB_MANAGER`, and read-only `AUDITOR`. Lab Managers see only transfers involving laboratories they currently manage. Initiation, destination acceptance/rejection, and ULMD approval controls are displayed by role and transfer status; the API independently checks the actor's current designated-laboratory relationship.

Stage 6 implements one `/maintenance` page. Fault reporting is embedded in the page and can also be opened from an operational asset passport with the asset code pre-filled. The API scopes Lab Managers to their managed laboratories, Lab Technicians to their department, and Maintenance Technicians to assigned orders. Users in explicitly configured existing approver roles can additionally see relevant external-parts approval requests; ULMD Admin and Auditors retain university-wide read access. Assignment, technician activity, approval decisions, and verification actions are independently authorized by the API. There are no separate report or ticket-detail routes.

Stage 7 implements `/calibrations` for due/overdue review and calibration history. All authenticated roles can view due information; ULMD Admin, Maintenance Technicians, and Auditors can view history; ULMD Admin and Maintenance Technicians can record a calibration. The user must supply the due-window horizon. No scheduled reminder or preventive-maintenance schedule page is implemented because that workflow is not defined in the approved schema.

---

## 3. Route Guard & Authorization Architecture

1. **`PublicRoute`:** Accessible without authentication (e.g., `/login`). If an authenticated user accesses this route, they are automatically redirected to `/dashboard`.
2. **`ProtectedRoute`:** Requires a valid, non-expired JWT access token. If missing or expired, the user is redirected to `/login` with an appended redirect parameter (`/login?returnUrl=/assets/14`).
3. **`RoleGuard`:** Wraps sensitive views (e.g., `/admin/*`, `/assets/register`) and verifies that `currentUser.role` exists in the allowed roles array. Unauthorized access renders a high-contrast `403 Forbidden` unauthorized view with a button returning to the main dashboard.
