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
│   │   ├── asset_service.py      # Asset code formatting, QR payload generation
│   │   ├── transfer_service.py   # Multi-step state machine validation
│   │   ├── maintenance_service.py# Work order routing to Tech Unit
│   │   ├── calibration_service.py# Overdue calculations and updates
│   │   └── audit_service.py      # Immutable logging helper
│   └── main.py                   # FastAPI initialization, middleware, routes
├── alembic/                      # Database Migration Scripts
│   ├── versions/
│   └── env.py
├── tests/                        # Automated Pytest Test Suite
│   ├── conftest.py               # DB fixtures, mock users, test clients
│   ├── test_auth.py
│   ├── test_assets.py
│   ├── test_transfers.py
│   └── test_maintenance.py
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
- **`AssetService`:** Validates serial number uniqueness, generates formatted `asset_code`, and constructs vector QR payloads.
- **`TransferService`:** Enforces dual-authorization rules, locks asset condition during transfer, and reassigns location foreign keys upon ULMD approval.
- **`MaintenanceService`:** Manages work order ticket lifecycle (`OPEN` -> `ASSIGNED` -> `IN_PROGRESS` -> `RESOLVED` -> `CLOSED`), updates asset condition flags, and records labor hours and spare parts.

### 3. `app/schemas/` (Pydantic Serialization)
- Strict request validation ensures that invalid data (e.g., malformed email, missing serial number, invalid severity) is rejected with HTTP 422 before reaching service layers.
- Response schemas filter out sensitive internal fields (e.g., `hashed_password`) from API outputs.
