# 02. Backend Architecture Specification

## 1. Clean Layered Architecture
The backend application follows a **Clean Layered Architecture** pattern, enforcing strict separation of concerns across presentation, routing, business logic, data access, and database modeling.

```
┌────────────────────────────────────────────────────────┐
│                   API ROUTERS (HTTP)                   │
│   FastAPI Endpoints, Parameter Parsing, HTTP Responses │
└───────────────────────────┬────────────────────────────┘
                            │ Validated via Pydantic Schemas
┌───────────────────────────▼────────────────────────────┐
│                    DOMAIN SERVICES                     │
│    Pure Business Logic, State Machines, Workflows      │
└───────────────────────────┬────────────────────────────┘
                            │ SQLAlchemy 2.0 ORM Operations
┌───────────────────────────▼────────────────────────────┐
│                   PERSISTENCE MODELS                   │
│      Declarative Database Entities & Relationships     │
└───────────────────────────┬────────────────────────────┘
                            │ Connection Pool (asyncpg)
┌───────────────────────────▼────────────────────────────┐
│                  POSTGRESQL DATABASE                   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Directory Layout & Module Structure

```text
backend/
├── app/
│   ├── api/                      # Routing & HTTP Controllers
│   │   ├── deps.py               # Dependency injection (db, current_user, roles)
│   │   └── v1/
│   │       ├── api_router.py     # Aggregated v1 endpoints
│   │       ├── auth.py           # Login, refresh, password handling
│   │       ├── users.py          # User management
│   │       ├── hierarchy.py      # Colleges, departments, labs, rooms
│   │       ├── assets.py         # Asset CRUD, QR generation, lookup
│   │       ├── transfers.py      # Inter-department transfer workflow
│   │       ├── maintenance.py    # Fault tickets, work orders, repair logs
│   │       ├── calibrations.py   # Calibration logs and schedules
│   │       ├── reports.py        # Dashboards and compliance exports
│   │       └── audits.py         # Read-only audit log queries
│   ├── core/                     # Application Infrastructure
│   │   ├── config.py             # Pydantic BaseSettings (.env loader)
│   │   ├── security.py           # Bcrypt hashing, JWT encode/decode
│   │   ├── permissions.py        # RBAC role definitions and route guards
│   │   └── exceptions.py         # Custom application exceptions and handlers
│   ├── db/
│   │   ├── session.py            # Async engine and sessionmaker
│   │   └── base.py               # Declarative base importing all models
│   ├── models/                   # SQLAlchemy ORM Database Entities
│   │   ├── hierarchy.py          # College, Department, Laboratory, Room
│   │   ├── user.py               # User, Role
│   │   ├── asset.py              # AssetCategory, Asset
│   │   ├── transfer.py           # AssetTransfer
│   │   ├── maintenance.py        # WorkOrder, MaintenanceLog
│   │   ├── calibration.py        # CalibrationLog
│   │   └── audit.py              # AuditLog
│   ├── schemas/                  # Pydantic v2 Request/Response Schemas
│   │   ├── common.py             # Pagination, RFC 7807 error responses
│   │   ├── user.py
│   │   ├── hierarchy.py
│   │   ├── asset.py
│   │   ├── transfer.py
│   │   ├── maintenance.py
│   │   ├── calibration.py
│   │   └── report.py
│   ├── services/                 # Domain Business Logic
│   │   ├── auth_service.py       # Credential verification, lockout, token issuance
│   │   ├── user_service.py       # User provisioning and role assignment
│   │   ├── hierarchy_service.py  # College/department/lab/room operations
│   │   ├── asset_service.py      # Asset code formatting, QR payload generation
│   │   ├── transfer_service.py   # Multi-step state machine validation
│   │   ├── maintenance_service.py# Work order routing to Tech Unit
│   │   ├── calibration_service.py# Overdue calculations and updates
│   │   ├── report_service.py     # Dashboard aggregations and inventory exports
│   │   └── audit_service.py      # Immutable logging helper
│   ├── tasks/                    # Scheduled / background jobs
│   │   └── calibration_scheduler.py # Daily due/overdue evaluation
│   └── main.py                   # FastAPI initialization, middleware, routes
├── alembic/                      # Database Migration Scripts
│   ├── versions/
│   └── env.py
├── tests/                        # Automated Pytest Test Suite
│   ├── conftest.py               # DB fixtures, mock users, test clients
│   ├── test_auth.py
│   ├── test_hierarchy.py
│   ├── test_assets.py
│   ├── test_transfers.py
│   ├── test_maintenance.py
│   ├── test_calibrations.py
│   ├── test_reports.py
│   └── test_audits.py
├── requirements.txt
└── .env.example
```

---

## 3. Responsibilities of Key Architectural Components

### 1. `app/api/deps.py` (Dependency Injection)
- **`get_db()`:** Yields an asynchronous database session with automatic commit on success and rollback on exception.
- **`get_current_user()`:** Extracts and validates JWT Bearer tokens from the `Authorization` header, decodes user UUID, and verifies account active status.
- **`require_role(allowed_roles: List[str])`:** Enforces RBAC permissions at the route level. Rejects unauthorized requests with HTTP 403 Forbidden.

### 2. `app/services/` (Domain Business Services)
- Route handlers in `app/api/` contain zero database query logic. All business rules, state machine transitions, and database queries are encapsulated in service methods.
- **`AuthService`:** Verifies bcrypt hashes, increments failed-login counters, applies the 15-minute lockout after five failures, and issues access/refresh tokens.
- **`AssetService`:** Validates serial number uniqueness, generates formatted `asset_code`, and constructs vector QR payloads.
- **`TransferService`:** Enforces dual-authorization rules, locks asset condition during transfer, preserves origin/destination room history, and reassigns location foreign keys upon ULMD approval.
- **`MaintenanceService`:** Manages the implemented work order lifecycle (`OPEN` -> `ASSIGNED` -> `IN_PROGRESS` -> `RESOLVED` -> `CLOSED`), supports the approved `AWAITING_PARTS` pause, updates asset condition flags, and records labor hours, spare parts, custodian verification, and immutable audit snapshots. `AWAITING_APPROVAL` is excluded pending DEC-02 stakeholder confirmation.
- **`CalibrationService`:** Calculates due/overdue status, records certificates and accreditation body, and updates asset calibration dates.
- **`AuditService`:** Writes synchronous append-only audit records with before/after JSONB snapshots.

### 3. `app/schemas/` (Pydantic Serialization)
- Strict request validation ensures that invalid data (e.g., malformed email, missing serial number, invalid severity) is rejected with HTTP 422 before reaching service layers.
- Response schemas filter out sensitive internal fields (e.g., `hashed_password`, `failed_login_attempts`, `locked_until`) from API outputs.

### 4. Transaction & Audit Boundaries
- Every mutating service method runs inside a single database transaction. The route layer never commits independently.
- The audit record is written **inside the same transaction** as the business mutation so that a failed audit insert rolls back the mutation. This preserves the invariant that every committed state change has a corresponding audit record.
- Read-only report queries use a separate session/transaction and never write audit records.

### 5. Scheduled Calibration Evaluation
- A lightweight scheduler runs inside the FastAPI lifespan (or as a Windows Task Scheduler job in production) once per day.
- It queries assets with `next_calibration_due <= current_date + warning_window_days`, computes `CALIBRATION_OVERDUE` / due-soon flags, and refreshes cached dashboard counts.
- The scheduler is idempotent and does not create duplicate work orders; failed calibrations may open an urgent work order through `MaintenanceService`.

## 6. Stage 4 Asset Implementation

The Stage 4 slice is implemented in `app/api/v1/assets.py`, `app/schemas/asset.py`, `app/services/asset_service.py`, and `app/models/asset.py`. Routes delegate transactions and policy checks to the service layer. It implements category maintenance under the current provisional `ULMD_ADMIN`-only restriction, asset registration, server-side code sequencing, category/location validation, authenticated QR SVG rendering and lookup, filtered asset reads, and limited metadata updates. Asset writes require `ULMD_ADMIN` or the designated manager of the laboratory; neither location nor status is editable through the asset metadata API.

Asset and category before/after snapshots are inserted into the approved `audit_logs` table in the same transaction. Migration `20261113_03_assets` installs a PostgreSQL trigger to reject audit-row updates and deletes. At Stage 4 completion, work-order, calibration, reporting, and general audit-browsing services shown in the target architecture remained unimplemented.

## 7. Stage 5 Custody Transfer Implementation

The `transfers` API delegates to `transfer_service`, which locks the asset and transfer rows, validates the current state and laboratory/room relationships, applies the approved receiver-then-ULMD workflow, and writes status and asset-location audit snapshots in the same transaction. An active transfer leaves the asset at its origin with `TRANSFER_PENDING`; approval moves the current asset foreign keys to the destination and restores `OPERATIONAL`, while rejection restores the original operational state and location. Transfer read access is limited to `ULMD_ADMIN`, designated `LAB_MANAGER` actors for either endpoint laboratory, and read-only `AUDITOR` users. Parent reassignment is blocked when a laboratory or room is part of transfer history. There is no separate assignment table or API.

## 8. Stage 6 Maintenance Implementation

The `work-orders` API delegates to `maintenance_service`. It creates fault reports only for operational assets, locks critical assets as `DEFECTIVE` and other reported assets as `UNDER_MAINTENANCE`, assigns active Maintenance Technicians, enforces department/laboratory/assigned-ticket read scope, and records maintenance logs and status snapshots transactionally. The additive `20261114_05_maintenance` revision creates only the approved `work_orders` and `maintenance_logs` tables. `AWAITING_APPROVAL` and the proposed DEC-03 local-repair path are not implemented. Confirmation of degraded/unrepairable closure behavior remains outstanding; only `OPERATIONAL` outcomes can currently close an order.
