# Implementation Progress

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
| Backend tests | Passed; 15 tests, including the 3 Stage 1 health tests |
| Password hashing and lockout | Passed; bcrypt cost 12 and 5-failure lockout verified |
| JWT and refresh lifecycle | Passed; expiry, rotation, replay rejection, logout revocation verified |
| API authorization and provisioning | Passed; unauthenticated and non-admin access rejected; admin create/update/deactivate tested |
| Frontend production build | Passed with TypeScript and Vite |
| Frontend smoke check | Passed; login and health pages rendered, and unauthenticated `/users` access redirected to login |

### Remaining limitations

- Refresh-token revocations and rate-limit counters are in process memory, as allowed by ADR-05 for the MVP. A server restart clears these controls, and multiple workers will not share them. Select a persistent shared store before production or multi-worker deployment.
- The first `ULMD_ADMIN` account still needs to be created interactively in the local environment using the documented CLI command.
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
