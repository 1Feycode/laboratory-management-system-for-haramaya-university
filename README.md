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
- [ ] **Phase 3: Database & Backend Implementation** *(Pending Review & Approval)*
- [ ] **Phase 4: Frontend Implementation & Integration** *(Upcoming)*
- [ ] **Phase 5: Verification, Validation & Deployment** *(Upcoming)*

> **Notice:** No application code has been implemented in this phase. The repository currently contains the verified software specifications, architectural blueprints, database dictionaries, API contracts, workflow models, and traceability matrices.

---

## Approved Technology Stack

### Backend
- **Language / Runtime:** Python 3.11+
- **Web Framework:** FastAPI (Asynchronous REST API)
- **Schema Validation & Settings:** Pydantic v2
- **ORM / Persistence:** SQLAlchemy 2.0
- **Database Migrations:** Alembic
- **Security & Authentication:** JWT (OAuth2 Password Bearer) with Passlib (bcrypt)

### Database
- **Engine:** PostgreSQL 15+ (Relational 3NF with JSONB audit logging)

### Frontend
- **Framework / Bundler:** React 18 (TypeScript) with Vite
- **Styling & Layout:** Tailwind CSS
- **Iconography:** Lucide Icons
- **Barcode / QR Scanning:** HTML5-QRCode (Browser MediaStream Camera API)
- **HTTP Client:** Axios with JWT interceptors

### Development & Operational Profile
- **Target Host:** Windows 10/11 laptop (8 GB RAM constraint)
- **Version Control:** Git & GitHub

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
- **Phase 3: Implementation Phase** - Commences upon formal review and sign-off of Phase 1 and 2 deliverables.
