# 07. Functional Requirements Specification

This document provides detailed, testable, and uniquely numbered functional requirements for the system. Every requirement is traceable to Phase 1 research findings and Phase 2 architectural designs.

---

## Module 1: Institutional Hierarchy & Access Control

### FR-001: User Authentication and Role Management
- **Description:** The system must securely authenticate users with an institutional email address and local password, and enforce role-based access control (RBAC).
- **Responsible Actor:** All Users (`ULMD_ADMIN`, `MAINTENANCE_TECH`, `LAB_MANAGER`, `LAB_TECH`, `AUDITOR`).
- **Input:** Institutional email address, plaintext password.
- **Expected System Behavior:** Validates email format, verifies salted bcrypt password hash, verifies active account flag, and issues a signed JSON Web Token (JWT) containing user UUID, role, and department scope.
- **Expected Output:** HTTP 200 OK with access token, refresh token, and user profile; HTTP 401 Unauthorized on failure.
- **Priority:** Must Have.
- **Acceptance Criteria:**
  1. Passwords must be hashed using bcrypt (cost factor 12).
  2. Tokens must expire within 30 minutes.
  3. Accounts are locked for 15 minutes after 5 consecutive failed attempts.

### FR-002: Institutional Hierarchy Management
- **Description:** The system must maintain the structural hierarchy of Haramaya University: Colleges -> Departments -> Laboratories -> Rooms.
- **Responsible Actor:** `ULMD_ADMIN`.
- **Input:** College name/code, Department name/code, Laboratory name/type (`WET`, `DRY`, `COMPUTING`, `WORKSHOP`), Room number, Building name.
- **Expected System Behavior:** Enforces relational integrity; ensures unique codes per college; prevents orphaned rooms or departments.
- **Expected Output:** HTTP 201 Created with persisted hierarchy nodes.
- **Priority:** Must Have.
- **Acceptance Criteria:** Deletion of a laboratory or room associated with active assets must be blocked by referential integrity (`RESTRICT`).

---

## Module 2: Asset Lifecycle & QR Identification

### FR-003: Durable Asset Registration
- **Description:** The system must register durable laboratory equipment according to WHO LQSI and Africa CDC standard data attributes.
- **Responsible Actor:** `LAB_MANAGER`, `ULMD_ADMIN`.
- **Input:** Asset category, manufacturer name, model number, serial number, purchase date, commissioning date, warranty expiration date, custodian laboratory, physical room.
- **Expected System Behavior:** Verifies uniqueness of the manufacturer serial number; auto-generates a unique university asset code (`HU-{COLLEGE}-{DEPT}-{SEQ}`); generates a high-density vector QR code; persists record.
- **Expected Output:** HTTP 201 Created with full asset passport and QR code image URL.
- **Priority:** Must Have.
- **Acceptance Criteria:**
  1. Duplicate registration of the same serial number from the same manufacturer must return HTTP 409 Conflict.
  2. Generated asset code must follow the exact institutional pattern.

### FR-004: QR Code Generation and Bench Lookup
- **Description:** The system must generate scannable QR codes for registered assets and provide rapid bench-side lookup via camera scan.
- **Responsible Actor:** All Authenticated Users.
- **Input:** Scanned QR code payload or asset identification string.
- **Expected System Behavior:** Decodes asset identifier; retrieves current operational condition, custodian lab, room, recent maintenance logs, and calibration status.
- **Expected Output:** HTTP 200 OK with digital asset passport view.
- **Priority:** Must Have.
- **Acceptance Criteria:** Lookup response latency must be under 200 ms on local network infrastructure.

### FR-005: Equipment Custody Transfer Workflow
- **Description:** The system must enforce a multi-step authorization workflow for transferring equipment between laboratories.
- **Responsible Actor:** Origin `LAB_MANAGER`, Destination `LAB_MANAGER`, `ULMD_ADMIN`.
- **Input:** Asset ID, destination laboratory ID, transfer justification.
- **Expected System Behavior:**
  1. Sets asset status to `TRANSFER_PENDING`.
  2. Notifies destination Lab Manager; awaits acceptance.
  3. Notifies ULMD Admin; awaits final confirmation.
  4. On confirmation, updates asset location foreign keys, updates transfer record to `COMPLETED`, restores asset to `OPERATIONAL`, and writes an immutable audit log.
- **Expected Output:** HTTP 200 OK with finalized transfer receipt.
- **Priority:** Must Have.
- **Acceptance Criteria:**
  1. Asset cannot be transferred if currently marked `DEFECTIVE`, `UNDER_MAINTENANCE`, or `TRANSFER_PENDING`.
  2. Full historical location trail must be preserved in `asset_transfers`, including origin and destination laboratory **and room** identifiers.

---

## Module 3: Maintenance, Faults & Calibration

### FR-006: Equipment Fault Reporting
- **Description:** The system must allow laboratory personnel to report equipment malfunctions and initiate work orders.
- **Responsible Actor:** `LAB_TECH`, `LAB_MANAGER`, `ULMD_ADMIN`.
- **Input:** Asset ID, severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), failure category, detailed symptom description.
- **Expected System Behavior:**
  1. Auto-generates unique work order ticket (`WO-{YEAR}-{AUTO_INC}`).
  2. If severity is `CRITICAL`, immediately sets asset condition to `DEFECTIVE`.
  3. If severity is `LOW`/`MEDIUM`/`HIGH`, sets asset condition to `UNDER_MAINTENANCE`.
  4. Alerts the ULMD Technology Unit dispatch queue.
- **Expected Output:** HTTP 201 Created with ticket number.
- **Priority:** Must Have.
- **Acceptance Criteria:** An asset in `DEFECTIVE` condition must be visually locked across the interface to prevent scheduling.

### FR-007: Work Order Assignment and Resolution
- **Description:** The system must track maintenance assignment, diagnostic actions, spare parts, and ticket closure.
- **Responsible Actor:** `ULMD_ADMIN` (assigns), `MAINTENANCE_TECH` (executes), `LAB_MANAGER` (verifies).
- **Input:** Work order ID, assigned technician ID, repair actions taken, spare parts used, labor hours, outcome condition.
- **Expected System Behavior:** Logs maintenance record; updates ticket status through `ASSIGNED` -> `IN_PROGRESS` -> `RESOLVED` -> `CLOSED`, with optional `AWAITING_PARTS` and `AWAITING_APPROVAL` exception states. Requires custodian Lab Manager verification to close.
- **Expected Output:** HTTP 200 OK with closed work order and updated asset condition.
- **Priority:** Must Have.
- **Acceptance Criteria:** Ticket cannot transition to `RESOLVED` without a non-empty maintenance log; closure must persist the verifying Lab Manager UUID and verification notes.

**Implementation clarification:** The `AWAITING_APPROVAL` exception is conditional on the unresolved DEC-02 external-parts approval decision. It is not implemented in the Stage 6 schema or API. The approved materials do not define approval thresholds or evidence. The allowed maintenance outcomes include `REPAIRED_DEGRADED` and `UNREPAIRABLE`, but the approved closure flow only specifies restoration to `OPERATIONAL`; the closure behavior for those outcomes also requires stakeholder clarification. See [Stage 6 open decisions](../design/phase-2-open-decisions.md#3-stage-6-maintenance-decision-boundaries) and the maintenance section of the [API specification](../api/api-specification.md#4-maintenance--work-order-endpoints).

### FR-008: Calibration Tracking and Scheduling
- **Description:** The system must record precision calibration events and track upcoming due dates.
- **Responsible Actor:** `MAINTENANCE_TECH`, `ULMD_ADMIN`.
- **Input:** Asset ID, calibration standard used, certificate reference, pass/fail status, calibration date, next due date.
- **Expected System Behavior:** Records entry in `calibration_logs`; updates asset `last_calibrated_date` and `next_calibration_due`; clears overdue flags if passed.
- **Expected Output:** HTTP 201 Created with calibration certificate reference.
- **Priority:** Must Have.
- **Acceptance Criteria:** Overdue assets must automatically display a `CALIBRATION_OVERDUE` badge across all views.

---

## Module 4: Auditing & Reporting

### FR-009: Immutable Audit Logging
- **Description:** The system must maintain an append-only log of all security events, asset state transitions, and custody changes.
- **Responsible Actor:** System Background Service.
- **Input:** User UUID, action string, entity type, entity ID, pre-mutation JSON, post-mutation JSON, client IP.
- **Expected System Behavior:** Synchronously writes record to `audit_logs` table.
- **Expected Output:** Immutable audit record.
- **Priority:** Must Have.
- **Acceptance Criteria:** Audit records cannot be modified or deleted through the API by any user role.

### FR-010: Executive Dashboards and Inventory Reporting
- **Description:** The system must generate operational dashboards and filterable inventory reports.
- **Responsible Actor:** `ULMD_ADMIN`, `AUDITOR` (university-wide or department-scoped read-only).
- **Input:** Date ranges, college filters, department filters, status filters.
- **Expected System Behavior:** Computes uptime percentages, counts open work orders, aggregates calibration compliance, and exports structured CSV/Excel reports.
- **Expected Output:** Dashboard charts and downloadable inventory files.
- **Priority:** Must Have.
- **Acceptance Criteria:** Reports must aggregate and render within 1,500 ms for inventories up to 10,000 items, consistent with NFR-PER-01.
