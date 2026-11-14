# Laboratory Asset Management and Maintenance Tracking System for Haramaya University

## Project Overview
The **Laboratory Asset Management and Maintenance Tracking System** is an enterprise-grade academic and research laboratory resource tracking platform designed specifically for **Haramaya University (HU)**. 

Haramaya University hosts over **90 to 150+ wet and dry laboratories** distributed across diverse academic faculties, colleges, schools, and research institutes, including:
- **Haramaya Institute of Technology (HiT)** (22+ engineering and process laboratories)
- **College of Agriculture and Environmental Sciences (CAES)** (soil, plant pathology, animal nutrition, agronomy)
- **College of Computing and Informatics (CCI)** (software engineering, hardware, systems, network labs)
- **College of Health and Medical Sciences (CHMS)** (clinical, pathology, biomedical laboratories at Harar Campus)
- **College of Veterinary Medicine (CVM)** (microbiology, parasitology, veterinary clinics)
- **College of Natural and Computational Sciences (CNCS)** (physics, chemistry, biology, mathematics labs)

The system bridges decentralized laboratory ownership with the centralized standard-setting and maintenance mandate of the **University Laboratories Management Directorate (ULMD)** (headquartered at Central Laboratory Building, Office 34) and the facilities operations of the **Estate Development and Facilities Management Directorate (EFMD)**.

---

## Current Development Phase
- [x] **Phase 1: Requirements Engineering & System Analysis** *(Completed)*
- [x] **Phase 2: System Design & Architecture Specification** *(Completed)*
- [x] **Stage 1: Project Foundation** *(Complete: application foundation and Docker PostgreSQL verified)*
- [x] **Stage 2: Authentication and User Management** *(Complete: local JWT auth, role guards, and ULMD user provisioning)*
- [x] **Stage 3: Organizational Structure** *(Implemented: colleges, departments, laboratories, and rooms)*
- [x] **Stage 4: Asset Management** *(Implemented and verified: asset register, categories, QR lookup, and audit history)*
- [x] **Stage 5: Asset Assignment and Transfer** *(Implemented: dual approval, location history, and transfer audit events)*
- [x] **Stage 6: Maintenance Management** *(Implemented and verified: fault reporting, dispatch, repair logs, verification, and history)*

> **Notice:** Stages 1–6 are implemented. Calibration workflows and business reporting are not implemented. See the [implementation progress report](docs/development/implementation-progress.md).

---

## Approved Technology Stack

### Backend
- **Language / Runtime:** Python 3.11+
- **Web Framework:** FastAPI (Asynchronous REST API)
- **Schema Validation & Settings:** Pydantic v2
- **ORM / Persistence:** SQLAlchemy 2.0
- **Database Migrations:** Alembic
- **Security & Authentication:** JWT (OAuth2 Password Bearer) with bcrypt password hashing (cost 12)

### Database
- **Engine:** PostgreSQL 15+ in Docker Desktop for local development (Relational 3NF with JSONB audit logging)

### Frontend
- **Framework / Bundler:** React 18 (TypeScript) with Vite
- **Styling & Layout:** Tailwind CSS
- **Iconography:** Lucide Icons
- **Barcode / QR Scanning:** HTML5-QRCode (Browser MediaStream Camera API)
- **HTTP Client:** Axios with JWT interceptors

### Development & Operational Profile
- **Target Host:** Windows 10/11 laptop (8 GB RAM constraint); PostgreSQL runs in Docker Desktop
- **Version Control:** Git & GitHub

## Local Setup and Implemented Stages

The backend runs directly on Windows and connects to the PostgreSQL container through the published loopback port (`127.0.0.1`).

1. If `.env` does not already exist, copy `.env.example` to `.env`; preserve any existing `.env`. Set a strong local `POSTGRES_PASSWORD` and the same password in `DATABASE_URL` (URL-encode special characters if used). Set `SECRET_KEY` to a random value of at least 32 bytes (for example, generate one with `python -c "import secrets; print(secrets.token_urlsafe(64))"`).
2. Start PostgreSQL from the repository root:
   ```powershell
   docker compose up -d db
   docker compose ps
   ```
   Wait until the `db` service reports `healthy`. Its data is kept in the named volume `hu_lab_postgres_data`; do not remove that volume for routine development.
3. Install the backend and apply migrations:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```
   On first setup only, provision the initial administrator interactively:
   ```powershell
   .\.venv\Scripts\python.exe -m app.cli create-admin
   ```
4. Start FastAPI in the backend terminal:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The migrations create the approved identity, organizational hierarchy, asset category, asset, transfer, maintenance, and append-only audit tables, and the initial migration seeds the five approved roles. The interactive CLI provisions the first `ULMD_ADMIN`; no default account or password is created.
   API documentation is available at `http://127.0.0.1:8000/docs`; liveness is at `/health` and database connectivity at `/health/ready`.
5. In another terminal, if `frontend/.env.local` does not already exist, copy `frontend/.env.example` to it; preserve any existing local settings. Then start React:
   ```powershell
   cd frontend
   npm.cmd install
   npm.cmd run dev
   ```
   The local API URL uses `http://localhost:8000` so the browser can send the `SameSite=Lax` refresh cookie.
6. Open the frontend at `http://localhost:5173`. Sign in with an account provisioned by a ULMD administrator.

### Stage 3 Organizational Structure

After signing in as `ULMD_ADMIN`, open **Organizational structure** in the application navigation. The page supports creation, search, filtering, updates, pagination, and confirmed deletion for colleges, departments, laboratories, and rooms. Deletion is blocked when approved foreign-key relationships have dependents. Physical location is represented by a laboratory and its rooms; the approved ERD contains no separate `Location` entity.

The organizational API is documented in [api-specification.md](docs/api/api-specification.md). Department deletion follows the approved `users.department_id ON DELETE SET NULL` constraint; see the implementation progress report for the resulting open role-scope issue.

### Stage 4 Asset Management

After signing in, open **Assets** to search and filter the inventory, scan an asset QR code, and view an asset passport. `ULMD_ADMIN` and the designated `LAB_MANAGER` for a laboratory can register assets; category mutations are currently restricted to `ULMD_ADMIN` as a provisional guard pending ULMD approval. Asset codes are system-generated using the approved four-digit college/department sequence. Asset status and location are not directly editable; transfers and maintenance workflows own those changes. See the [asset API specification](docs/api/api-specification.md#3-asset-management-endpoints) and [implementation progress report](docs/development/implementation-progress.md).

Asset QR images contain the asset code unless a confirmed public frontend origin is configured with `ASSET_PUBLIC_BASE_URL` in the repository-root `.env`; restart FastAPI after changing it. Set only the origin (no path, query, or credentials); the generated protected link resolves the asset after authentication. Leave the setting unset until the deployment owner confirms the production origin. No production host is currently configured.

### Stage 4 Decision Follow-up

The unconditional manufacturer/serial uniqueness constraint remains unchanged, so a decommissioned asset's serial pair is still reserved. The condemnation-reference schema and decommissioning authority remain unresolved, as does the approved role policy for category administration. Ordinary assets retain one laboratory and one room under BR-004; no shared-location exception is implemented. Full evidence, recommendations, and stakeholder approvals needed are recorded in [Phase 2 open decisions](docs/design/phase-2-open-decisions.md#2-stage-4-decision-review) and the [implementation progress report](docs/development/implementation-progress.md).

### Stage 5 Asset Assignment and Transfer

Initial assignment remains part of asset registration and is captured in its creation audit snapshot. Open **Custody transfers** to initiate a later move, accept receipt at the destination, and complete final ULMD approval. The asset remains at its origin and is locked as `TRANSFER_PENDING` until approval or rejection. Completed transfer rows preserve the origin and destination laboratory/room IDs; audit snapshots preserve each status transition and location change. No separate assignment table is part of the approved schema. `ULMD_ADMIN`, designated `LAB_MANAGER`, and read-only `AUDITOR` roles can access the transfer view; manager scope and every action are independently checked by the API. See the [transfer API specification](docs/api/api-specification.md#39-custody-transfer-endpoints), [transfer workflow](docs/workflows/asset-transfer.mmd), and [implementation progress report](docs/development/implementation-progress.md).

### Stage 6 Maintenance Management

The `/maintenance` interface supports scoped fault reporting, ULMD technician assignment, repair activity and parts/labor records, custodian verification, and audit-backed history. The conditional `AWAITING_APPROVAL` state and closure of degraded/unrepairable outcomes remain unresolved and are not enabled without stakeholder decisions. See [maintenance API details](docs/api/api-specification.md#4-maintenance--work-order-endpoints), [open maintenance decisions](docs/design/phase-2-open-decisions.md#3-stage-6-maintenance-decision-boundaries), and the [implementation progress report](docs/development/implementation-progress.md).

### Backend Verification

Run backend tests from `backend/`:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
Tests use a separate PostgreSQL database named `hu_lab_management_test`, derived from `DATABASE_URL`; they never target the application database. Create that database once if it does not already exist:
```powershell
docker compose exec -T db psql -U hu_lab_app -d postgres -c "CREATE DATABASE hu_lab_management_test OWNER hu_lab_app;"
```
The test fixtures create and remove tables only in the `_test` database. Do not set `TEST_DATABASE_URL` to the application database.

If FastAPI is later run inside Compose, configure its database host as the Compose service name `db` and use port `5432`; the current Windows-hosted backend uses `127.0.0.1` and the published host port.

---

## Documentation Structure & Navigation

### Phase 1: Requirements Engineering (`docs/requirements/` & `docs/diagrams/`)
1. [Project Background](docs/requirements/01-project-background.md) - Haramaya University operational context and ULMD mandate.
2. [Research Findings](docs/requirements/02-research-findings.md) - Official HU findings, WHO LQSI, and Africa CDC guidelines.
3. [Source Register](docs/requirements/03-source-register.md) - Verified citations, official URLs, and classification.
4. [Stakeholder Analysis](docs/requirements/04-stakeholder-analysis.md) - ULMD, Technology Unit, Materials Unit, College Managers, Technicians.
5. [Problem Analysis](docs/requirements/05-problem-analysis.md) - Categorization of manual inventories, ghost assets, and maintenance delays.
6. [Project Scope & MoSCoW](docs/requirements/06-project-scope.md) - MVP boundaries, core features, and excluded ERP/LIMS items.
7. [Functional Requirements](docs/requirements/07-functional-requirements.md) - Uniquely numbered specifications (FR-001 through FR-010).
8. [Non-Functional Requirements](docs/requirements/08-non-functional-requirements.md) - Security, performance, usability, and auditability metrics.
9. [Business Rules](docs/requirements/09-business-rules.md) - Unique asset codes, custody rules, condition locks, and audit policies.
10. [Use Cases](docs/requirements/10-use-cases.md) - Actor catalogs and comprehensive system use cases.
11. [Stakeholder Interview Instrument](docs/requirements/11-stakeholder-interview-questions.md) - Field questionnaires for ULMD and colleges.
12. [Assumptions & Open Questions](docs/requirements/12-assumptions-and-open-questions.md) - Unresolved operational questions.
13. [Consolidated Software Requirements Specification (SRS)](SRS.md) - Comprehensive master specification document.

### Phase 2: System Design & Architecture (`docs/architecture/`, `docs/database/`, `docs/api/`, etc.)
1. [System Architecture](docs/architecture/01-system-architecture.md) - Modular monolithic architecture, layers, and communication.
2. [Backend Architecture](docs/architecture/02-backend-architecture.md) - FastAPI clean layered pattern, modules, and error handling.
3. [Frontend Architecture](docs/architecture/03-frontend-architecture.md) - React component hierarchy, state, routing, and QR camera integration.
4. [Database Design](docs/architecture/04-database-design.md) - 3NF schema, historical preservation, and relational safeguards.
5. [API Design](docs/architecture/05-api-design.md) - RESTful OpenAPI specifications, RFC 7807 error handling, and JSON payloads.
6. [Authentication & Security](docs/architecture/06-authentication-and-security.md) - RBAC matrix, token rotation, and threat mitigation.
7. [Deployment & Windows Setup](docs/architecture/07-deployment-architecture.md) - Practical 8 GB RAM local development environment.
8. [Technology Decisions](docs/architecture/08-technology-decisions.md) - Architecture Decision Records (ADRs).
9. [Database Data Dictionary](docs/database/data-dictionary.md) - Complete table-by-table column types, constraints, and indexes.
10. [API Specification](docs/api/api-specification.md) - Detailed catalog of all `/api/v1` routes and payloads.
11. [Screen Design Specification](docs/ui-ux/screen-design-specification.md) - Screen-by-screen breakdown, states, and user actions.
12. [Navigation Structure](docs/ui-ux/navigation-structure.md) - Information architecture and role-based site map.
13. [Requirements Traceability Matrix](docs/design/requirements-traceability-matrix.md) - End-to-end traceability from FR to API and UI.
14. [Testing Strategy](docs/design/testing-strategy.md) - Pytest, Vitest, integration fixtures, and test coverage guidelines.
15. [Phase 2 Open Decisions](docs/design/phase-2-open-decisions.md) - Design gaps and proposed baselines awaiting stakeholder feedback.

### Mermaid Visual Models (`docs/diagrams/` & `docs/workflows/`)
- [System Context Diagram](docs/diagrams/system-context.mmd)
- [Use Case Diagram](docs/diagrams/use-case-diagram.mmd)
- [Activity Workflows](docs/diagrams/activity-diagrams.mmd)
- [Preliminary ER Diagram](docs/diagrams/preliminary-er-diagram.mmd)
- [Complete Relational ERD](docs/database/er-diagram.mmd)
- [Asset Registration Flow](docs/workflows/asset-registration.mmd)
- [Dual-Approval Transfer Flow](docs/workflows/asset-transfer.mmd)
- [Maintenance Work Order Flow](docs/workflows/maintenance-request.mmd)
- [Calibration Tracking Flow](docs/workflows/calibration-workflow.mmd)

---

## Development Roadmap
- **Phase 1: Requirements Engineering** - Complete. Verified institutional facts and international standards.
- **Phase 2: Architecture & System Design** - Complete. Comprehensive technical blueprints and specifications.
- **Stage 1: Project Foundation** - Complete and verified.
- **Stage 2: Authentication and User Management** - Complete; see the authentication design and progress report for the in-memory refresh-token revocation limitation.
- **Stage 3: Organizational Structure** - Complete for the approved college/department/laboratory/room entities.
- **Stage 4: Asset Management** - Complete for asset registration, categories, QR lookup, search, and asset audit snapshots.
- **Stage 5: Asset Assignment and Transfer** - Complete for the approved dual-authorization transfer workflow and location history.
- **Stage 6: Maintenance Management** - Complete for the approved work-order scope; see the maintenance section of the [implementation progress report](docs/development/implementation-progress.md).
- **Calibration and later business modules** - Not implemented; do not infer those workflows are available from the asset register or transfer module.
