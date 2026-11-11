# 08. Non-Functional Requirements Specification

This document defines the quality attributes, architectural constraints, and performance metrics for the Laboratory Asset Management and Maintenance Tracking System. Every requirement includes testable and measurable acceptance criteria.

---

## 1. Security Requirements

### NFR-SEC-01: Cryptographic Protection & Password Storage
- **Specification:** All user passwords must be hashed using `bcrypt` with a minimum work factor of 12. Plaintext passwords must never be stored, logged, or transmitted in unencrypted formats.
- **Metric:** Bcrypt cost parameter >= 12.
- **Acceptance Criteria:** Database inspection verifies that no passwords exist as plaintext; timing attack resilience verified via standard constant-time hash comparisons.

### NFR-SEC-02: Transport Layer Security & Token Protection
- **Specification:** All client-server communications must use TLS 1.3 (HTTPS). Authentication tokens must use standard JWT signed via HMAC-SHA256 (HS256) or RSA-256. Refresh tokens must be stored in `HttpOnly`, `SameSite=Lax`, `Secure` cookies.
- **Metric:** Token expiration: Access Token = 30 minutes; Refresh Token = 7 days.
- **Acceptance Criteria:** Automated penetration testing confirms access tokens cannot be captured via script injection (XSS) from cookies.

### NFR-SEC-03: Server-Side Authorization & Tenancy Scoping
- **Specification:** System access must be guarded server-side using Role-Based Access Control (RBAC). Departmental staff must be restricted to their assigned department's assets, while `ULMD_ADMIN` possesses university-wide permissions.
- **Metric:** 100% of mutating API routes enforce dependency-injected permission guards.
- **Acceptance Criteria:** Direct API calls attempting cross-department modifications without elevated privileges return HTTP 403 Forbidden.

---

## 2. Performance & Hardware Constraints

### NFR-PER-01: API Response Latency
- **Specification:** In standard campus network conditions, read endpoints (including QR bench lookup and asset passport retrieval) must respond rapidly to support efficient lab workflows.
- **Metric:** 95th percentile latency <= 200 ms for standard queries; <= 1,500 ms for aggregate multi-college inventory reports under a concurrent load of 50 users.
- **Acceptance Criteria:** Load testing using Locust or Pytest-benchmark confirms response times meet latency thresholds.

### NFR-PER-02: Development & Runtime Hardware Footprint
- **Specification:** The software must run efficiently on standard developer and institutional hardware, specifically a **Windows 10/11 laptop with 8 GB RAM**.
- **Metric:** Combined memory footprint of backend (FastAPI/Uvicorn), frontend (Vite React), and local database (PostgreSQL) must not exceed 1.5 GB of RAM during active development.
- **Acceptance Criteria:** Task Manager monitoring confirms stable execution without swapping or memory starvation on 8 GB RAM machines.

---

## 3. Reliability & Availability

### NFR-REL-01: System Uptime & Operational Availability
- **Specification:** The application must maintain high availability during university working hours (Monday through Friday, 08:00 to 18:00 East Africa Time - EAT).
- **Metric:** 99.0% uptime during core operational hours.
- **Acceptance Criteria:** Unplanned downtime does not exceed 4 hours per working month.

### NFR-REL-02: Database Transactional Integrity
- **Specification:** All state-changing workflows (e.g., asset transfers, work order status updates) must execute within atomic database transactions.
- **Metric:** Zero orphaned records; 100% compliance with ACID properties.
- **Acceptance Criteria:** Injected network or database interruptions during a transfer workflow trigger full transaction rollback, restoring the asset to its prior valid state.

---

## 4. Usability & Accessibility

### NFR-USA-01: Mobile-Responsive Viewports for Bench Scanning
- **Specification:** The user interface must adapt responsively to mobile smartphones, tablets, and desktop workstations, with specific layout optimization for bench-side technician use.
- **Metric:** Fully functional rendering down to 360px viewport width.
- **Acceptance Criteria:** QR code scanning and fault ticket submission can be completed within 3 clicks on a mobile smartphone.

### NFR-USA-02: User Interface Accessibility
- **Specification:** Visual interface elements must follow WCAG 2.1 Level AA contrast standards (minimum contrast ratio of 4.5:1 for standard text) to support technicians working under variable laboratory lighting.
- **Metric:** Zero critical accessibility violations reported by automated audit tools (Lighthouse / Axe-core).

---

## 5. Maintainability & Code Quality

### NFR-MNT-01: Modular Architecture & Type Safety
- **Specification:** The backend must adhere to clean layered modular design (Routes -> Services -> Models -> Schemas). Both backend (Python Pydantic) and frontend (TypeScript) must maintain strict type safety.
- **Metric:** 100% Pydantic request/response schema coverage; zero untyped API routes.
- **Acceptance Criteria:** Automated linting (Ruff/Flake8) and type checking (Mypy) pass with zero errors.

### NFR-MNT-02: Automated Database Schema Versioning
- **Specification:** All database schema changes must be versioned and executable via automated migration scripts using Alembic.
- **Metric:** 100% of schema definitions reproducible via forward (`upgrade`) and backward (`downgrade`) migration scripts.

---

## 6. Auditability & Compliance

### NFR-AUD-01: Immutable Audit Trail
- **Specification:** The system must record an indelible, append-only log of all critical state transitions, custody relocations, and permission changes.
- **Metric:** 100% of state-changing events generate an audit record containing actor UUID, timestamp, action type, and JSONB before/after values.
- **Acceptance Criteria:** SQL permissions restrict the `audit_logs` table to `INSERT` and `SELECT` only; `UPDATE` and `DELETE` commands are rejected at the database level.
