# Implementation Progress

## Stage 4: Asset Management

**Status:** Implemented and verified
**Completed:** 2026-11-13

### Delivered

- Implemented the approved `AssetCategory`, `Asset`, and `AssetAuditLog` SQLAlchemy models and Alembic revision `20261113_03_assets`. It creates only the approved category, asset, and audit tables; the migration was applied after confirming the database was at `20261113_02`.
- Added database constraints and indexes for unique asset codes, the unconditional manufacturer/serial pair, approved asset status values, category names, lookup/filter fields, and restrictive asset references to category, laboratory, and room.
- Added PostgreSQL append-only protection for `audit_logs`; direct `UPDATE` and `DELETE` attempts were rejected. A rollback-only production-schema check left no test rows.
- Added Pydantic request/response validation and service-layer APIs for category lookups/admin maintenance, asset registration, asset retrieval, filtered/sorted/paginated listing, limited metadata updates, QR SVG generation, and lookup by either universal asset code or legacy tag.
- Generated asset codes under a department row lock in the approved `HU-{COLLEGE_CODE}-{DEPT_CODE}-{4_DIGIT_SEQ}` form. Registration initializes status to `OPERATIONAL`, validates category and location references, and requires the room to belong to the selected laboratory.
- Prevented hierarchy code/parent changes that would invalidate existing asset codes or split an asset's custodian laboratory from its room. Such changes remain available before assets depend on those records.
- Restricted asset writes to `ULMD_ADMIN` or the designated `LAB_MANAGER` for the asset's laboratory and department. Asset code, operational status, and location cannot be changed through the asset metadata endpoint; there is no asset hard-delete endpoint.
- Asset and category mutations append before/after JSONB snapshots in the same transaction. The database trigger rejects audit-row updates and deletes.
- Added the React inventory, search/filter/sort/pagination, registration/edit forms, passport, authenticated QR rendering, camera scanner, and administrator category-management screen. The QR scanner is loaded on demand.
- Added focused Stage 4 regression tests and updated the API, UI/UX, navigation, database, security, traceability, README, and progress documentation.

### Stage 4 boundaries and unresolved decisions

- No asset name, description, purchase price, separate condition table, initial categories, status transitions, asset deletion, transfers, work orders, calibration scheduling/history, reports, or general audit viewer were introduced. These are unsupported by the approved asset fields or belong to later stages.
- **DEC-06 serial reuse:** the unconditional manufacturer/serial constraint remains in force. A regression test verifies that a duplicate is rejected even when the existing asset is `DECOMMISSIONED`. No migration or existing-record change was made; stakeholder approval is still required before changing this policy.
- **BR-010 condemnation reference:** the approved Asset data dictionary has no reference field or document relationship, and authority/evidence details are unspecified. No condemnation schema, status transition, or decommissioning API was added; stakeholder approval is required.
- **Category policy:** the approved role matrix does not define category administration, and the schema has no active/inactive field. Existing `ULMD_ADMIN`-only backend mutations and frontend visibility remain a provisional restriction; API tests verify non-admin mutation requests are denied. Stakeholder approval is required before changing the role guards or schema.
- **QR payload:** no canonical production host is configured. Optional `ASSET_PUBLIC_BASE_URL` now controls URL-based QR destinations; when unset, the existing code-only payload remains. Configured URLs resolve through a protected `/assets/scan?code=...` route, and the camera scanner accepts URL and code-only payloads. The deployment owner must confirm the origin before configuring it.
- **Location exception:** BR-004 requires one current room and laboratory, while the possible shared-instrument note defines no exception workflow or persisted authorization. Existing parent validation remains; no multi-location relationship or bypass was added. Stakeholder approval is required before any exception.
- **Migration/data preservation:** no Alembic revision was needed for these decision outcomes. No application-database records or existing migration history were changed.
- **Audit user foreign key:** `audit_logs.user_id ON DELETE SET NULL` would require changing an audit row, which the append-only trigger blocks. Current user management deactivates accounts and exposes no physical deletion. Production DB role hardening is still required because a database owner/superuser can disable triggers.
- Only asset and category mutations are recorded in the Stage 4 audit slice. Audit events for authentication, user changes, transfers, maintenance, and calibration, plus audit browsing, are not implemented here.

### Verification

| Check | Result |
|---|---|
| Backend automated suite | Passed; 27 tests across Stages 1–4 |
| Asset-focused tests | Passed; registration/code sequence, duplicate serial including decommissioned assets, invalid category/location, audit snapshots, filtering/pagination, QR payload fallback/configuration, QR/legacy lookup, category mutation guards, and no-hard-delete behavior |
| Alembic migration | Passed; `20261113_03` applied to the existing database without resetting it |
| Alembic model/schema comparison | Passed; `alembic check` reported no pending operations |
| Audit append-only protection | Passed; PostgreSQL rejected direct `UPDATE` and `DELETE`; validation rows were rolled back |
| Existing data | Preserved; no asset/category seed records or test records were left in the application database |
| Frontend production build | Passed with TypeScript and Vite |
| Dependencies | Added `qrcode` to backend requirements and `html5-qrcode` to the frontend manifest/lockfile |

## Stage 3: Organizational Structure

**Status:** Implemented and verified
**Completed:** 2026-11-13

### Delivered

- Implemented the ERD-approved `Laboratory` and `Room` models and ORM relationships for the existing `College` and `Department` models. Added the approved laboratory type constraint, department foreign key, optional manager foreign key, room foreign key, department index, and room-within-laboratory uniqueness.
- Added Alembic revision `20261113_02_organizational_hierarchy` after Stage 2's identity revision. It creates only `laboratories` and `rooms`; no new `Location` entity or unrelated business tables were introduced.
- Added authenticated paginated, searchable, filterable reads and `ULMD_ADMIN`-only create, retrieve, update, and delete APIs for colleges, departments, laboratories, and rooms.
- Added parent existence checks, type validation, uniqueness conflict handling, explicit 404 responses, and 409 responses when database foreign keys prevent deletion.
- Added a role-guarded hierarchy management screen with tabs for the four approved entities, parent selectors, search/filter, pagination, create/edit forms, confirmations, loading/empty states, and success/error messages.
- Updated API, navigation, screen, README, and implementation-progress documentation.

### Approved scope interpretation and unresolved consistency

- The ERD does not define a standalone `Location` table. Physical location is represented as `Laboratory -> Room`, so Stage 3 implements that approved model rather than inventing another entity.
- `users.department_id` is specified `ON DELETE SET NULL`, while `LAB_MANAGER` and `LAB_TECH` provisioning requires a department. Department deletion currently honors the approved FK and can therefore clear an existing user's department assignment. The Phase 2 documents do not resolve whether deletion should instead be blocked for departments with assigned users; confirm that policy before relying on department scoping in later business modules.
- Laboratory `manager_id` is an optional foreign key to `users`; the approved schema does not restrict its role or department. No such administrative policy was added.
- College, department, laboratory, and room records have no approved soft-delete field. DELETE is physical only when the database's approved referential integrity permits it; foreign-key conflicts are returned as `409 Conflict`.
- Asset and transfer tables are not part of Stage 3, so their future references to laboratories and rooms cannot yet be exercised. The Stage 3 migration adds only the hierarchy tables; Stage 4 must preserve the approved `ON DELETE RESTRICT` asset/transfer references.

### Verification

| Check | Result |
|---|---|
| Backend automated tests | Passed; 19 tests across Stages 1–3 |
| Alembic migration | Passed; `20261113_02` is head and applied |
| Existing administrator and database records | Passed; one active `ULMD_ADMIN` preserved; no hierarchy records were fabricated |
| PostgreSQL hierarchy tables | Passed; `colleges`, `departments`, `laboratories`, and `rooms` exist |
| Frontend production build | Passed with TypeScript and Vite |
| API smoke checks | Passed; database readiness is healthy and anonymous hierarchy access returns `401` |
| Referential integrity tests | Passed; duplicate keys rejected, dependent deletes return `409`, and department deletion follows the approved user `SET NULL` action |

## Stage 2: Authentication and User Management

**Status:** Implemented and verified  
**Completed:** 2026-11-13

### Delivered

- Implemented the approved `Role`, `User`, `College`, and `Department` SQLAlchemy entities. `College` and `Department` are included as the approved parent records required by `users.department_id`; hierarchy CRUD remains out of scope.
- Added Alembic revision `20261113_01`, which creates the approved identity tables and seeds exactly the five canonical roles. It does not create asset, maintenance, calibration, transfer, or audit tables.
- Added bcrypt cost-12 password hashing, input policy checks, JWT access tokens (30 minutes), HttpOnly refresh cookies (7 days), one-time refresh rotation, current-user lookup, logout, login lockout after five failures for 15 minutes, and 10-per-minute per-IP/account auth rate limits.
- Added server-side `ULMD_ADMIN` guards for user list, department options, retrieval, provisioning, role/department updates, activation, and deactivation. Responses never serialize hashes or lockout state. The final active administrator cannot be demoted or deactivated.
- Added an interactive `python -m app.cli create-admin` bootstrap command. It avoids public registration and does not create a default account or password.
- Added React login, in-memory access-token state, refresh-cookie restoration and retry, protected routes, a role guard, role-aware navigation, logout, and an administrator user-provisioning screen.
- Updated authentication, API, UI, traceability, deployment, and README documentation.

### Configuration and database state

- The local ignored `.env` now has a generated `SECRET_KEY`; `.env.example` contains only a placeholder. Frontend API calls use `http://localhost:8000` so localhost refresh cookies conform to `SameSite=Lax`.
- Applied migration `20261113_01` to the existing PostgreSQL database without resetting it. The application database now has the four approved identity tables and five seeded roles; no user accounts or business records were inserted.
- Tests use a separate `hu_lab_management_test` database. Their fixtures enforce a `_test` suffix and create/drop tables only there.

### Verification

| Check | Result |
|---|---|
| Backend compilation and app import | Passed |
| Alembic migration | Passed; `20261113_01` is head |
| Existing PostgreSQL identity data | Passed; five canonical roles, zero user accounts |
| Backend tests | Passed; 16 tests, including the 3 Stage 1 health tests and CLI cleanup regression test |
| Password hashing and lockout | Passed; bcrypt cost 12 and 5-failure lockout verified |
| JWT and refresh lifecycle | Passed; expiry, rotation, replay rejection, logout revocation verified |
| API authorization and provisioning | Passed; unauthenticated and non-admin access rejected; admin create/update/deactivate tested |
| Frontend production build | Passed with TypeScript and Vite |
| Frontend smoke check | Passed; login and health pages rendered, and unauthenticated `/users` access redirected to login |

### Remaining limitations

- Refresh-token revocations and rate-limit counters are in process memory, as allowed by ADR-05 for the MVP. A server restart clears these controls, and multiple workers will not share them. Select a persistent shared store before production or multi-worker deployment.
- The first `ULMD_ADMIN` account has been provisioned interactively in the local environment; credentials are not recorded in this report.
- Department-scoped roles require department records. This stage provides an admin-only department option list but does not implement hierarchy management.
- The test client emits the existing non-blocking Starlette `httpx` deprecation warning.

## Stage 1: Project Foundation

**Status:** Complete  
**Completed:** 2026-11-13

### Delivered

- Added the FastAPI application foundation with environment-based configuration, async SQLAlchemy engine/session setup, centralized HTTP and request-validation error responses, basic logging, CORS, and health endpoints.
- Added Alembic configuration using the approved SQLAlchemy metadata base. No application tables or migration revisions were created; the approved business schema remains for its planned implementation stage.
- Added a React 18, TypeScript, Vite, Tailwind CSS, and React Router foundation with an Axios API client and a minimal page that checks backend health.
- Added a PostgreSQL 15 Docker Compose service using environment-based credentials, a persistent named volume, a localhost-only port binding, a health check, and a development restart policy.
- Added `.env.example`, frontend API environment example, and `.gitignore`. A local `.env` was created for verification and is ignored by Git.
- Updated the README and deployment guidance for the Stage 1 Docker database arrangement.

### Configuration

- FastAPI runs directly on Windows; PostgreSQL is reached at `127.0.0.1:5432` through the Docker-published port.
- If FastAPI is later placed in Compose, its database host must be the Compose service name `db` and its port `5432`.
- The Compose service is `db`; its persistent volume is `hu_lab_postgres_data`.
- The repository SRS is [SRS.md](../../SRS.md). It remains at the repository root; no duplicate `docs/SRS.md` was created.

### Verification

| Check | Result |
|---|---|
| Docker Desktop CLI and engine | Passed; Docker Engine 29.8.0 available |
| PostgreSQL container | Passed; `postgres:15-alpine` started and reported healthy |
| Database port and persistence | Passed; mapped to `127.0.0.1:5432`, named volume configured |
| FastAPI database connection | Passed; `/health/ready` returned `{"status":"ok","database":"ok"}` |
| FastAPI liveness | Passed; `/health` returned `{"status":"ok"}` |
| Backend automated tests | Passed; 3 tests |
| Alembic configuration | Passed; `upgrade head` and `current` connected successfully; no revisions exist yet |
| Frontend production build | Passed with Vite |
| Frontend/backend communication | Passed in browser; foundation page displayed “Backend is reachable” |
| Frontend dependency audit | Passed; 0 reported vulnerabilities after updating Vite and React Router |

The backend tests emit a non-blocking Starlette deprecation warning about its `httpx` test client. No Stage 1 test failures remain.

### Scope Boundary

No authentication, users, business entities, asset/maintenance/calibration modules, dashboards, or business database schema were implemented. Proceed to the next stage only after review and authorization.
