# Software Requirements Specification (SRS)
## Laboratory Asset Management and Maintenance Tracking System for Haramaya University

**Document Reference:** HU-LMD-SRS-001  
**Status:** Approved Phase 1 Specification  
**Institutional Scope:** University Laboratories Management Directorate (ULMD) & Academic Colleges  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) establishes the complete, verified functional and non-functional requirements for the **Laboratory Asset Management and Maintenance Tracking System** at Haramaya University (HU). It serves as the authoritative source of truth for system architecture, database modeling, and software implementation.

### 1.2 Institutional Context
Haramaya University operates an extensive scientific infrastructure comprising over **90 to 150+ wet and dry laboratories** across multiple academic colleges, including the Haramaya Institute of Technology (HiT), College of Agriculture and Environmental Sciences (CAES), College of Computing and Informatics (CCI), College of Health and Medical Sciences (CHMS), College of Veterinary Medicine (CVM), and College of Natural and Computational Sciences (CNCS).

The system addresses the operational divide between decentralized departmental laboratory custody and the centralized standardization, maintenance, and resource oversight mandated to the **University Laboratories Management Directorate (ULMD)**, headquartered at Central Laboratory Building, Office Number 34.

---

## 2. Overall Description

### 2.1 System Architecture Overview
The system is architected as a **Modular Monolith** comprising:
1. **Client Layer:** A responsive React Single Page Application (SPA) utilizing Tailwind CSS and the HTML5-QRCode camera scanner hook for bench-side technician use.
2. **API & Services Layer:** An asynchronous FastAPI application enforcing OAuth2/JWT authentication, Pydantic validation, and domain-driven business workflows.
3. **Persistence Layer:** A normalized (3NF) PostgreSQL database engine enforcing relational integrity, unique serial numbers, and an immutable JSONB audit log.

### 2.2 User Roles & Responsibilities
- **`ULMD_ADMIN` (Directorate Leadership):** University-wide read/write permissions; manages colleges, departments, and labs; dispatches work orders; approves transfers; generates compliance audits.
- **`MAINTENANCE_TECH` (Technology Unit Specialists):** Receives maintenance assignments; logs repair actions, spare parts, and labor hours; records certified instrument calibrations.
- **`LAB_MANAGER` (Department Chief TAs):** Registers departmental equipment; requests transfers; reports faults; verifies completed repairs; signs off on ticket closure.
- **`LAB_TECH` (Bench Technical Assistants):** Scans QR codes at the bench; submits immediate fault tickets; views operating procedures.
- **`AUDITOR` (Compliance Officers):** Read-only university-wide access to inventory counts, downtime analytics, and immutable audit ledgers.

---

## 3. Specific Requirements

### 3.1 Functional Requirements Summary

| ID | Requirement Name | Description & Acceptance Benchmark | Priority |
|---|---|---|---|
| **FR-001** | User Authentication & RBAC | JWT access tokens (30 min) and refresh cookies; salted bcrypt password hashing; role-based endpoint guards. | Must Have |
| **FR-002** | Institutional Hierarchy | Relational structure: College -> Department -> Laboratory -> Room. Prevents orphaned nodes via `RESTRICT`. | Must Have |
| **FR-003** | Standard Asset Registration | WHO LQSI compliant registration: manufacturer, model, serial, purchase/commissioning dates, category, and room. | Must Have |
| **FR-004** | QR Code Generation & Lookup | Vector QR generation; mobile camera lookup resolving digital asset passport in < 200 ms. | Must Have |
| **FR-005** | Custody Transfer Tracking | Multi-step workflow: Origin LM initiation -> Target LM inspection -> ULMD confirmation. Full historical trail. | Must Have |
| **FR-006** | Fault Reporting & Work Orders | Technicians report defects with severity; auto-generates `WO-{YEAR}-{AUTO}`; locks asset condition on Critical. | Must Have |
| **FR-007** | Work Order Resolution | Technology Unit logs repair actions, spare parts, and labor hours. Custodian Lab Manager verification required to close. | Must Have |
| **FR-008** | Calibration Tracking | Records standards used, pass/fail status, and auto-calculates next due date. Overdue warning banners. | Must Have |
| **FR-009** | Immutable Audit Trail | Append-only logging of all asset mutations and custody relocations with pre/post JSONB snapshots. | Must Have |
| **FR-010** | Management Dashboards | Computes uptime %, open work order distributions, and exports filterable inventory sheets. | Must Have |

### 3.2 Non-Functional Requirements Summary
- **Security:** TLS 1.3 transport encryption; bcrypt cost factor 12; SQL injection prevention via SQLAlchemy parameterized statements.
- **Performance:** 95% of API read queries execute in < 200 ms; aggregate dashboard reports in < 1,500 ms under 50 concurrent users.
- **Hardware Footprint:** Development stack runs within an **8 GB RAM** budget (< 1.5 GB total memory footprint for API, React, and PostgreSQL).
- **Auditability:** Strict database-level prohibition of `UPDATE` and `DELETE` on the `audit_logs` table.

---

## 4. Key Business Rules
1. **Unique Identification:** Every asset receives an immutable code: `HU-{COLLEGE}-{DEPT}-{SEQ}`.
2. **Single Active Location:** An asset belongs to exactly one physical room at any given time.
3. **Condition Lock:** Assets marked `DEFECTIVE` or `UNDER_MAINTENANCE` cannot be assigned to academic classes or approved for inter-departmental transfers.
4. **Historical Preservation:** Equipment cannot be deleted from the database; retiring an asset requires transition to `DECOMMISSIONED` with a formal condemnation reference.

---

## 5. Traceability to Phase 2 System Design
All requirements in this SRS are fully mapped to concrete database tables, API routes, and UI components in the [Requirements Traceability Matrix](docs/design/requirements-traceability-matrix.md).
