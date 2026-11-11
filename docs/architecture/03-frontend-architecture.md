# 03. Frontend Architecture Specification

## 1. Client Architecture Overview
The frontend application is constructed as a modern **Single Page Application (SPA)** utilizing **React 18**, **TypeScript**, and **Tailwind CSS**, bundled via **Vite**.

```
┌────────────────────────────────────────────────────────┐
│               REACT ROUTER (ROUTING LAYER)             │
│   Protected Routes, Role Guards, Layout Composition    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│               APPLICATION STATE & CONTEXTS             │
│       AuthContext (JWT/User), ToastContext (Alerts)    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    PAGE VIEWPORTS                      │
│   Dashboard, Asset Passport, Work Orders, Transfers    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│               API CLIENT & HARDWARE SERVICES           │
│   Axios Client (with Interceptors) + HTML5-QRCode Hook │
└────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```text
frontend/
├── src/
│   ├── assets/               # Brand logos, icons, vector illustrations
│   ├── components/           # Reusable UI Primitives
│   │   ├── common/           # Button, Input, Modal, Table, Badge, Spinner
│   │   ├── layout/           # Sidebar, Navbar, PageHeader, Container
│   │   ├── qr/               # QRScannerModal, QRVectorViewer, PrintLabel
│   │   └── feedback/         # ToastNotification, EmptyState, ErrorAlert
│   ├── contexts/             # Global State
│   │   ├── AuthContext.tsx   # User profile, JWT tokens, login/logout
│   │   └── ToastContext.tsx  # Floating notification queue
│   ├── hooks/                # Custom React Hooks
│   │   ├── useAuth.ts        # RBAC role inspection hook
│   │   ├── useDebounce.ts    # Search input debouncer
│   │   └── useQRScanner.ts   # HTML5-QRCode camera hook
│   ├── pages/                # Screen Viewports
│   │   ├── auth/LoginPage.tsx
│   │   ├── dashboard/DashboardPage.tsx
│   │   ├── assets/
│   │   │   ├── AssetListPage.tsx
│   │   │   ├── AssetDetailPage.tsx
│   │   │   └── AssetRegistrationPage.tsx
│   │   ├── transfers/TransferWorkflowPage.tsx
│   │   ├── maintenance/
│   │   │   ├── WorkOrderListPage.tsx
│   │   │   └── WorkOrderDetailPage.tsx
│   │   ├── calibrations/CalibrationSchedulePage.tsx
│   │   ├── reports/ReportsDashboardPage.tsx
│   │   └── admin/UserManagementPage.tsx
│   ├── routes/               # Navigation Guards
│   │   ├── AppRoutes.tsx
│   │   └── ProtectedRoute.tsx# Server-backed RBAC route guard
│   ├── services/             # Axios API Service Modules
│   │   ├── api.ts            # Base Axios instance with token interceptors
│   │   ├── authService.ts
│   │   ├── assetService.ts
│   │   ├── maintenanceService.ts
│   │   └── hierarchyService.ts
│   ├── types/                # TypeScript Interface Declarations
│   │   └── index.ts
│   ├── App.tsx
│   └── main.tsx
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

---

## 3. Hardware Integration: In-Browser QR Camera Scanning

Bench-side technicians and managers require rapid equipment identification without typing long serial numbers. The system implements a custom React hook `useQRScanner` wrapping the lightweight `html5-qrcode` library:

1. **Permissions:** Requests standard browser `MediaStream` camera access on mobile devices and laptops.
2. **Decoding:** Continuously scans video frames for standard QR payloads.
3. **Execution:** On capture, extracts the asset code and navigates directly to the asset passport view (`/assets/:id`), executing in under 200 ms.
4. **Fallback:** If camera access is denied or unavailable, provides an instant text lookup input with auto-complete.

---

## 4. UI/UX States & Design Principles
- **Responsive Layout:** Adaptive desktop sidebar that collapses into a bottom navigation drawer on mobile viewports (< 768px).
- **Explicit Component States:** Every data-fetching view strictly handles four visual states:
  1. *Loading State:* Pulse skeleton loaders matching table dimensions.
  2. *Empty State:* Descriptive illustration with contextual call-to-action ("No assets registered in this laboratory yet").
  3. *Success / Data State:* Clean, high-contrast data tables with sorting and pagination controls.
  4. *Error State:* User-friendly error banner with an immediate "Retry Request" button.
- **Visual Status Badges:** Color-coded condition indicators:
  - `OPERATIONAL`: Green (`bg-emerald-100 text-emerald-800`)
  - `UNDER_MAINTENANCE`: Amber (`bg-amber-100 text-amber-800`)
  - `DEFECTIVE`: Red (`bg-rose-100 text-rose-800`)
  - `CALIBRATION_OVERDUE`: Purple badge with alert triangle icon
