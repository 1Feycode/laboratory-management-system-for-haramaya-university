# Implementation Progress

## Stage 6: Maintenance Management

**Status:** Implemented and verified
**Completed:** 2026-11-14

### Delivered

- Added the approved `WorkOrder` and `MaintenanceLog` SQLAlchemy models and additive Alembic revision `20261114_05_maintenance`, following `20261113_04`. The revision adds only `work_orders` and `maintenance_logs`; prior migrations and existing data are unchanged.
- Added validated maintenance request/response schemas, service-layer workflows, and authenticated endpoints for fault reports, scoped paginated work-order reads, ULMD technician assignment, assigned-technician status transitions, repair activities, and custodian verification/rejection.
- Fault reporting locks an `OPERATIONAL` asset as `DEFECTIVE` for critical severity or `UNDER_MAINTENANCE` for other approved severities. Ticket creation, asset status updates, logs, state changes, and append-only JSONB audit snapshots are transactional.
- Enforced the role matrix in the API: Lab Technicians are department-scoped, Lab Managers are scoped to their managed laboratories, Maintenance Technicians can act on assigned orders, and ULMD Admin / Auditors have university-wide read access. Only active `MAINTENANCE_TECH` users can be assigned.
- Added the React `/maintenance` queue, fault report form, status filter and pagination, role-aware assignment and work controls, repair log form, verification/rejection, and audit-backed status and maintenance history. Operational asset passports provide a prefilled fault-report link.
- No extra maintenance assignment/activity/outcome tables, local-repair path, calibration, or unrelated modules were introduced.

### Unresolved requirements and boundaries

- **DEC-02:** `AWAITING_APPROVAL` remains a proposed state. External-parts thresholds, approver, evidence, and rejection behavior are unspecified; the state and budget approval process are not implemented.
- The approved outcomes include `REPAIRED_DEGRADED` and `UNREPAIRABLE`, but do not define safe degraded return-to-service authorization or unrepairable disposition. The API permits recording these outcomes but only permits confirmed closure for `OPERATIONAL`; otherwise it returns `409 Conflict`. Stakeholder approval is required before changing this behavior.
- **DEC-03:** The proposed Lab Manager local routine-repair workflow is not implemented.
- No notifications, procurement flow, or calibration features were added.

### Verification

| Check | Result |
|---|---|
| Maintenance-focused API tests | Passed; 5 tests cover fault scope/validation, severity lock, duplicate active report, assignment-role validation, unauthorized technician actions, parts pause/resume, repair and verification history, outcome boundary, and transaction rollback. |
| Full backend suite | Passed; 37 tests across Stages 1–6. The existing Starlette/httpx test-client deprecation warning remains non-blocking. |
| Frontend production build | Passed with TypeScript and Vite. |
| Backend compilation, app import, and OpenAPI paths | Passed; all six work-order paths are registered. |
| Alembic graph and migration | Passed; `20261114_05` applied as the sole head after `20261113_04`. |
| Generated migration SQL and model comparison | Passed; SQL creates only the approved tables/constraints/indexes; `alembic check` reports no pending schema operations. |
| Audit append-only protection | Passed; `audit_logs_append_only` remains enabled after migration. The maintenance migration does not alter audit triggers. |
| Existing PostgreSQL data | Preserved; migration ran against `hu_lab_management` without reset or deletion. A post-migration count found one work order and zero maintenance logs; no work-order records were inserted by these tests or migration. The observed row was left untouched. All automated tests used the separate `_test` database. |
| Frontend ESLint command | Still blocked by pre-existing setup: ESLint 10.14.0 has no `eslint.config.*` file in the frontend project. The production TypeScript/Vite build passes; no lint configuration or unrelated dependencies were added in this stage. |

## Stage 5: Asset Assignment and Transfer

**Status:** Implemented and verified
**Completed:** 2026-11-13

### Delivered

- Implemented the ERD-approved `AssetTransfer` model and additive Alembic revision `20261113_04_asset_transfers`, with only the approved transfer columns, status check, indexes, and restrictive foreign keys. No prior migration was modified.
- Kept initial assignment within the existing asset-registration workflow; the `ASSET_CREATED` snapshot records its initial location. No unapproved assignment table/API was added.
- Added transfer initiation, destination acceptance, rejection, ULMD approval, paginated/filterable transfer history, and transfer detail APIs. Lab Manager actions are checked against the designated origin or destination laboratory; final approval is restricted to `ULMD_ADMIN`.
- Enforced the approved state flow: an operational asset is locked as `TRANSFER_PENDING` while retaining its current location; receiver acceptance advances the transfer to `PENDING_ULMD`; final approval moves the current asset location and restores `OPERATIONAL`; rejection restores the original operational state and location.
- Kept transfer rows, asset status/location updates, and JSONB audit snapshots in one transaction. Transfer state history is read from the append-only audit log; no history columns or separate assignment table were invented.
- Added destination room/laboratory validation and required an active designated destination Lab Manager when a request is initiated. Lab Managers can view only transfers involving laboratories they currently manage; `ULMD_ADMIN` and `AUDITOR` have university-wide read access.
- Blocked asset metadata edits while a transfer is active. Prevented laboratory/room parent reassignment when transfer history references those records, preserving the historical hierarchy.
- Added the React `/transfers` queue, initiation form, role-aware accept/reject/approve controls, pagination/status filtering, and transfer history on the asset passport.
- Updated the API, database, security, UI/UX, traceability, README, and implementation-progress documentation. No Stage 6 functionality was started.

### Verification

| Check | Result |
|---|---|
| Transfer-focused backend tests | Passed; 5 tests cover receiver and ULMD rejection, the approval flow, source/destination preservation, scope/validation, defective-asset blocking, and transaction rollback. |
| Full backend suite | Passed; 32 tests across Stages 1–5. |
| Frontend production build | Passed with TypeScript and Vite. |
| Alembic graph | Passed; `20261113_04` is the sole head after `20261113_03`. |
| Migration SQL review | Passed; generated SQL creates only the approved transfer table and indexes and does not alter prior tables or migration history. |
| Existing PostgreSQL database | Passed; the additive `20261113_04` migration was applied to the existing PostgreSQL 15 container after the full test suite passed. `alembic current` reports `20261113_04`; `alembic check` reports no pending schema operations. |
| Application data | Preserved; no asset, user, hierarchy, or audit rows were created, changed, or deleted. Tests used only the isolated `_test` database. |

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
- At Stage 4 completion, only asset and category mutations were recorded in the audit slice. Stage 5 subsequently added transfer and asset status/location events; Stage 6 adds maintenance events. Authentication/user and calibration audit events, plus general audit browsing, remain unimplemented.

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
