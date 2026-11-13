# AGENTS.md: Developer & Agent Reference Manual

## Repository Identity & Purpose
- **Project:** Laboratory Asset Management and Maintenance Tracking System for Haramaya University
- **Scope:** Academic and research laboratory asset lifecycle, QR identification, preventive/corrective maintenance workflows, and custody transfers across 90–150+ laboratories.
- **Institutional Context:** Haramaya University (Dire Dawa, Ethiopia). Central governance by the University Laboratories Management Directorate (ULMD, Central Lab Building Office 34) and Estate Development & Facilities Management Directorate (EFMD).
- **Current Lifecycle Stage:** Phase 1 and Phase 2 documentation complete; Stages 1 (foundation) and 2 (authentication/user management) complete. Stage 3 business modules remain pending.

---

## Approved Technology Stack & Constraints
- **Backend:** Python 3.11+, FastAPI (Async REST), Pydantic v2, SQLAlchemy 2.0 (Declarative ORM), Alembic (Migrations).
- **Database:** PostgreSQL 15+ (Relational 3NF with JSONB audit logging).
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, HTML5-QRCode.
- **Authentication:** JWT Bearer (OAuth2 Password flow) with salted bcrypt passwords.
- **Target Hardware Constraint:** Windows 10/11 laptop with 8 GB RAM. Run PostgreSQL 15+ in the user's Docker Desktop container with a persistent named volume; run FastAPI/Uvicorn and React/Vite as native Windows processes. Avoid extra containers, services, and multi-VM setups.

---

## Standard Development & Verification Commands

### Stage 1 Development Commands
```bash
# From the repository root, after copying .env.example to .env and setting a local password
docker compose up -d db

# Navigate to backend directory
cd backend

# Create & activate Python virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt

# Run database migrations
python -m alembic upgrade head

# Launch development API server (Hot reload)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run automated tests
python -m pytest tests/ -v

# Run the Stage 1 health checks
python -m pytest tests/test_health.py -v
```

### Frontend Commands
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm.cmd install

# Run development server
npm.cmd run dev

# Build production bundle
npm.cmd run build
```

---

## Core Architectural Rules & Conventions

### 1. Separation of Concerns & Clean Layering
- **No Direct Database Calls in Route Handlers:** FastAPI routers in `app/api/` must call domain services in `app/services/`. Only services execute business transactions.
- **Strict Data Validation:** All request payloads must be validated using Pydantic v2 schemas in `app/schemas/`.
- **Relationship Eager Loading:** Always use explicit `selectinload` or `joinedload` on SQLAlchemy relationships to avoid N+1 query bottlenecks in PostgreSQL.

### 2. Business Logic & State Machines
- **Unique Asset Codes:** Format strictly as `HU-{COLLEGE}-{DEPT}-{AUTO_INC}` (e.g., `HU-HiT-CHEM-0014`).
- **Condition Locks:** An asset marked `DEFECTIVE` or `UNDER_MAINTENANCE` cannot be assigned to academic classes or approved for inter-departmental transfers.
- **Dual-Approval Custody Transfers:** An asset transfer requires initiation by the origin Lab Manager, acceptance by the destination Lab Manager, and final sign-off by ULMD.
- **Immutable Audit Trail:** The `audit_logs` table is strictly append-only. No user role (including `ULMD_ADMIN`) can update or delete audit records.

### 3. Out-of-Scope Modules
- Do NOT introduce student grade records, course management, clinical diagnostic EHRs, or full procurement purchase ordering.
- Keep durable lab assets strictly separated from consumable chemicals and reagents.

---

## Directory Layout Reference
```text
docs/
├── requirements/      # Phase 1: Background, research, stakeholders, FRs, NFRs, business rules
├── diagrams/          # Phase 1: Context, use cases, activity, preliminary ERD (.mmd)
├── architecture/      # Phase 2: System, backend, frontend, DB, API, security, ADRs
├── database/          # Phase 2: Complete ERD (.mmd) and data dictionary
├── api/               # Phase 2: RESTful API OpenAPI specification
├── ui-ux/             # Phase 2: Screen specifications and navigation structure
├── workflows/         # Phase 2: Detailed Mermaid lifecycle activity diagrams
└── design/            # Phase 2: Traceability matrix, testing strategy, open decisions
```
