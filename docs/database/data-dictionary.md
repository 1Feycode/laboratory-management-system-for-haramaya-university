# Database Data Dictionary

This document specifies the PostgreSQL 15+ relational schema for the Laboratory Asset Management and Maintenance Tracking System, covering all **13 normalized tables**, column constraints, referential actions, and performance indexes.

### Table Inventory

| # | Table | Purpose |
|---|---|---|
| 1 | `colleges` | University colleges and institutes. |
| 2 | `departments` | Academic departments within colleges. |
| 3 | `laboratories` | Laboratories owned by departments or ULMD. |
| 4 | `rooms` | Physical rooms within laboratories. |
| 5 | `roles` | Canonical RBAC role definitions. |
| 6 | `users` | Authentication credentials and institutional assignments. |
| 7 | `asset_categories` | Equipment categories and calibration defaults. |
| 8 | `assets` | Durable equipment master records. |
| 9 | `asset_transfers` | Custody transfer workflow and location history. |
| 10 | `work_orders` | Fault tickets and maintenance dispatch. |
| 11 | `maintenance_logs` | Repair actions, parts, and labor records. |
| 12 | `calibration_logs` | Calibration events and compliance records. |
| 13 | `audit_logs` | Append-only immutable audit vault. |

---

## 1. Institutional Hierarchy Tables

### 1.1 `colleges`
Stores the high-level faculties, colleges, and research institutes across Haramaya University.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`name`** (`VARCHAR(150)`, NOT NULL, UNIQUE): Full college title (e.g., "Haramaya Institute of Technology").
- **`code`** (`VARCHAR(20)`, NOT NULL, UNIQUE): Abbreviated college code (e.g., "HiT", "CAES", "CCI").
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Timestamp of creation.

### 1.2 `departments`
Stores academic departments operating within each college.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`college_id`** (`UUID`, NOT NULL, FK -> `colleges.id` ON DELETE RESTRICT): Owning college.
- **`name`** (`VARCHAR(150)`, NOT NULL): Department name (e.g., "Chemical Engineering").
- **`code`** (`VARCHAR(20)`, NOT NULL): Department code (e.g., "CHEM").
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Creation timestamp.
- **Constraints & Indexes:**
  - Unique composite index: `uk_dept_college_code UNIQUE (college_id, code)`
  - Foreign key index: `idx_dept_college (college_id)`

### 1.3 `laboratories`
Stores individual laboratories owned by departments or operated centrally by ULMD.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`department_id`** (`UUID`, NOT NULL, FK -> `departments.id` ON DELETE RESTRICT): Department owner.
- **`name`** (`VARCHAR(150)`, NOT NULL): Lab name (e.g., "Reaction Engineering Lab").
- **`lab_type`** (`VARCHAR(50)`, NOT NULL): `WET`, `DRY`, `COMPUTING`, `WORKSHOP`.
- **`manager_id`** (`UUID`, NULLABLE, FK -> `users.id` ON DELETE SET NULL): Designated Lab Manager.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Creation timestamp.
- **Indexes:** `idx_labs_dept (department_id)`

### 1.4 `rooms`
Stores specific physical rooms within campus buildings assigned to laboratories.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`laboratory_id`** (`UUID`, NOT NULL, FK -> `laboratories.id` ON DELETE RESTRICT): Assigned laboratory.
- **`room_number`** (`VARCHAR(50)`, NOT NULL): Door/room number (e.g., "B-14", "Room 34").
- **`building_name`** (`VARCHAR(150)`, NOT NULL): Campus building name.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Creation timestamp.
- **Constraints & Indexes:** Unique composite: `uk_room_lab_number UNIQUE (laboratory_id, room_number)`

---

## 2. Identity, Role & Access Tables

### 2.1 `roles`
Stores role-based access definitions.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`name`** (`VARCHAR(50)`, NOT NULL, UNIQUE): `ULMD_ADMIN`, `MAINTENANCE_TECH`, `LAB_MANAGER`, `LAB_TECH`, `AUDITOR`.
- **`description`** (`VARCHAR(255)`, NOT NULL): Role description.

### 2.2 `users`
Stores user authentication credentials and institutional assignments.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`email`** (`VARCHAR(255)`, NOT NULL, UNIQUE): Institutional email address.
- **`hashed_password`** (`VARCHAR(255)`, NOT NULL): Salted bcrypt hash.
- **`full_name`** (`VARCHAR(150)`, NOT NULL): User's legal name.
- **`role_id`** (`UUID`, NOT NULL, FK -> `roles.id` ON DELETE RESTRICT): RBAC role.
- **`department_id`** (`UUID`, NULLABLE, FK -> `departments.id` ON DELETE SET NULL): Department scope.
- **`is_active`** (`BOOLEAN`, NOT NULL, DEFAULT TRUE): Account status.
- **`failed_login_attempts`** (`INT`, NOT NULL, DEFAULT 0): Consecutive failed authentication count used for lockout.
- **`locked_until`** (`TIMESTAMPTZ`, NULLABLE): Temporary lockout expiry after five consecutive failures.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Creation timestamp.
- **Indexes:** `idx_users_email (email)`, `idx_users_role (role_id)`

---

## 3. Asset & Classification Tables

### 3.1 `asset_categories`
Stores functional categories of laboratory equipment.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`name`** (`VARCHAR(100)`, NOT NULL, UNIQUE): Category name (e.g., "Spectrophotometer", "Centrifuge").
- **`requires_calibration`** (`BOOLEAN`, NOT NULL, DEFAULT FALSE): Calibration requirement flag.
- **`default_calibration_interval_days`** (`INT`, NOT NULL, DEFAULT 0): Standard interval (e.g., 180, 365).
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Creation timestamp.

### 3.2 `assets` (Core Equipment Master Record)
Stores durable laboratory machinery compliant with WHO LQSI and Africa CDC standards.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`asset_code`** (`VARCHAR(100)`, NOT NULL, UNIQUE): Formatted code (`HU-{COLLEGE}-{DEPT}-{4_DIGIT_SEQ}`, e.g., `HU-HiT-CHEM-0014`).
- **`legacy_tag_number`** (`VARCHAR(100)`, NULLABLE): Optional historical departmental tag/barcode retained during migration (DEC-01).
- **`serial_number`** (`VARCHAR(100)`, NOT NULL): Manufacturer serial number.
- **`model_number`** (`VARCHAR(100)`, NOT NULL): Equipment model.
- **`manufacturer_name`** (`VARCHAR(150)`, NOT NULL): Manufacturer.
- **`category_id`** (`UUID`, NOT NULL, FK -> `asset_categories.id` ON DELETE RESTRICT): Equipment category.
- **`laboratory_id`** (`UUID`, NOT NULL, FK -> `laboratories.id` ON DELETE RESTRICT): Custodian laboratory.
- **`room_id`** (`UUID`, NOT NULL, FK -> `rooms.id` ON DELETE RESTRICT): Current physical room.
- **`operational_status`** (`VARCHAR(50)`, NOT NULL, DEFAULT 'OPERATIONAL'): `OPERATIONAL`, `UNDER_MAINTENANCE`, `DEFECTIVE`, `TRANSFER_PENDING`, `DECOMMISSIONED`. `CALIBRATION_OVERDUE` is a computed compliance flag derived from `next_calibration_due`, not a stored status.
- **`purchase_date`** (`DATE`, NULLABLE): Date of purchase invoice.
- **`commissioning_date`** (`DATE`, NULLABLE): Date installed and put into active service.
- **`warranty_expiry_date`** (`DATE`, NULLABLE): Warranty expiration date.
- **`last_calibrated_date`** (`DATE`, NULLABLE): Most recent calibration date.
- **`next_calibration_due`** (`DATE`, NULLABLE): Scheduled calibration deadline.
- **`qr_code_path`** (`VARCHAR(255)`, NULLABLE): Vector QR code storage reference.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Creation timestamp.
- **`updated_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Mutation timestamp.
- **Constraints & Indexes:**
  - Unique composite: `uk_assets_serial_mfr UNIQUE (manufacturer_name, serial_number)`. This is stricter than Phase 1 business rule BR-002, which allows reuse after formal decommissioning; the policy conflict is unresolved under [DEC-06](../design/phase-2-open-decisions.md#dec-06-serial-number-reuse-after-decommissioning). Keep the constraint unchanged pending stakeholder confirmation.
  - Unique code index: `idx_assets_code (asset_code)`
  - Legacy tag index: `idx_assets_legacy_tag (legacy_tag_number)` (non-unique, partial where not null)
  - Status index: `idx_assets_status (operational_status)`
  - Calibration index: `idx_assets_next_cal (next_calibration_due)`
  - Laboratory index: `idx_assets_lab (laboratory_id)`

---

## 4. Maintenance, Calibration & Transfer Tables

### 4.1 `asset_transfers`
Tracks inter-laboratory equipment relocations and preserves historical custody.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`asset_id`** (`UUID`, NOT NULL, FK -> `assets.id` ON DELETE RESTRICT): Relocated asset.
- **`origin_laboratory_id`** (`UUID`, NOT NULL, FK -> `laboratories.id` ON DELETE RESTRICT): Origin laboratory.
- **`origin_room_id`** (`UUID`, NOT NULL, FK -> `rooms.id` ON DELETE RESTRICT): Origin physical room at the time of transfer.
- **`target_laboratory_id`** (`UUID`, NOT NULL, FK -> `laboratories.id` ON DELETE RESTRICT): Destination laboratory.
- **`target_room_id`** (`UUID`, NOT NULL, FK -> `rooms.id` ON DELETE RESTRICT): Destination physical room.
- **`initiated_by`** (`UUID`, NOT NULL, FK -> `users.id`): Origin Lab Manager.
- **`accepted_by`** (`UUID`, NULLABLE, FK -> `users.id`): Destination Lab Manager.
- **`approved_by_ulmd`** (`UUID`, NULLABLE, FK -> `users.id`): ULMD Admin sign-off.
- **`status`** (`VARCHAR(50)`, NOT NULL, DEFAULT 'PENDING_RECEIVER'): `PENDING_RECEIVER`, `PENDING_ULMD`, `COMPLETED`, `REJECTED`.
- **`transfer_reason`** (`TEXT`, NOT NULL): Administrative justification.
- **`notes`** (`TEXT`, NULLABLE): Receiver acceptance notes or rejection reason.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Request timestamp.
- **`completed_at`** (`TIMESTAMPTZ`, NULLABLE): Finalization timestamp.
- **Indexes:** `idx_transfers_asset (asset_id)`, `idx_transfers_status (status)`

### 4.2 `work_orders`
Tracks equipment breakdowns, technician dispatch, and resolution states.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`ticket_number`** (`VARCHAR(50)`, NOT NULL, UNIQUE): `WO-{YEAR}-{AUTO_INC}`.
- **`asset_id`** (`UUID`, NOT NULL, FK -> `assets.id` ON DELETE RESTRICT): Broken equipment.
- **`reported_by`** (`UUID`, NOT NULL, FK -> `users.id`): Reporting technician/manager.
- **`assigned_to`** (`UUID`, NULLABLE, FK -> `users.id`): Servicing Technology Unit technician.
- **`severity`** (`VARCHAR(30)`, NOT NULL): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- **`failure_category`** (`VARCHAR(50)`, NOT NULL): `ELECTRICAL`, `MECHANICAL`, `OPTICAL`, `SOFTWARE`, `CONSUMABLE`, `OTHER`.
- **`status`** (`VARCHAR(50)`, NOT NULL, DEFAULT 'OPEN'): `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `AWAITING_PARTS`, `AWAITING_APPROVAL`, `RESOLVED`, `CLOSED`. `AWAITING_APPROVAL` is reserved for the DEC-02 external-parts approval baseline.
- **`fault_description`** (`TEXT`, NOT NULL): Detailed symptom report.
- **`verified_by`** (`UUID`, NULLABLE, FK -> `users.id`): Custodian Lab Manager who signed off closure.
- **`verification_notes`** (`TEXT`, NULLABLE): Lab Manager's operational test and sign-off comments.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Report timestamp.
- **`resolved_at`** (`TIMESTAMPTZ`, NULLABLE): Repair completion timestamp.
- **`closed_at`** (`TIMESTAMPTZ`, NULLABLE): Custodian verification timestamp.
- **Indexes:** `idx_wo_asset (asset_id)`, `idx_wo_status (status)`, `idx_wo_assigned (assigned_to)`, `idx_wo_ticket (ticket_number)`

### 4.3 `maintenance_logs`
Stores detailed records of physical repairs, replaced parts, and labor expended.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`work_order_id`** (`UUID`, NOT NULL, FK -> `work_orders.id` ON DELETE RESTRICT): Parent ticket.
- **`technician_id`** (`UUID`, NOT NULL, FK -> `users.id`): Servicing technician.
- **`actions_taken`** (`TEXT`, NOT NULL): Diagnostic and physical repair actions.
- **`spare_parts_used`** (`TEXT`, NULLABLE): Replaced parts catalog.
- **`labor_hours`** (`DECIMAL(5,2)`, NOT NULL, DEFAULT 0.00): Servicing time in hours.
- **`outcome_condition`** (`VARCHAR(50)`, NOT NULL): `OPERATIONAL`, `REPAIRED_DEGRADED`, `UNREPAIRABLE`.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Log timestamp.
- **Indexes:** `idx_maint_wo (work_order_id)`

### 4.4 `calibration_logs`
Records precision instrument calibration standards, pass/fail status, and certificates.
- **`id`** (`UUID`, PK): Primary key, default `gen_random_uuid()`.
- **`asset_id`** (`UUID`, NOT NULL, FK -> `assets.id` ON DELETE RESTRICT): Calibrated instrument.
- **`technician_id`** (`UUID`, NOT NULL, FK -> `users.id`): Calibrating specialist.
- **`calibration_date`** (`DATE`, NOT NULL): Service execution date.
- **`standard_used`** (`VARCHAR(150)`, NOT NULL): Standard or buffer reference.
- **`certificate_reference`** (`VARCHAR(100)`, NULLABLE): Document file reference.
- **`accreditation_body`** (`VARCHAR(150)`, NULLABLE): External metrology/accreditation body (e.g., ENAO) where applicable (DEC-05).
- **`passed`** (`BOOLEAN`, NOT NULL): Pass/fail validation flag.
- **`next_due_date`** (`DATE`, NOT NULL): Calculated next calibration deadline.
- **`notes`** (`TEXT`, NULLABLE): Technical observations.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Creation timestamp.
- **Indexes:** `idx_calib_asset (asset_id)`, `idx_calib_next_due (next_due_date)`

---

## 5. Audit & Compliance Table

### 5.1 `audit_logs` (Append-Only Transaction Vault)
Records an immutable log of all critical system mutations.
- **`id`** (`BIGINT`, PK, GENERATED ALWAYS AS IDENTITY): Monotonic sequential ID.
- **`user_id`** (`UUID`, NULLABLE, FK -> `users.id` ON DELETE SET NULL): Acting user.
- **`action`** (`VARCHAR(100)`, NOT NULL): `ASSET_CREATED`, `STATUS_MODIFIED`, `TRANSFER_APPROVED`, `WORK_ORDER_CLOSED`.
- **`entity_type`** (`VARCHAR(50)`, NOT NULL): Target table (e.g., `assets`, `work_orders`).
- **`entity_id`** (`VARCHAR(100)`, NOT NULL): UUID/ID of the target entity.
- **`old_values`** (`JSONB`, NULLABLE): Pre-mutation state snapshot.
- **`new_values`** (`JSONB`, NULLABLE): Post-mutation state snapshot.
- **`ip_address`** (`VARCHAR(45)`, NULLABLE): Client IP address.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Timestamp of modification.
- **Indexes:** `idx_audit_entity (entity_type, entity_id)`, `idx_audit_user (user_id)`, `idx_audit_created (created_at)`

---

## 6. Canonical Enumerations

The following values are the single source of truth for application enums, API validation, and UI badges. Database columns remain `VARCHAR` with application-level validation and optional PostgreSQL `CHECK` constraints in Alembic migrations.

| Enum | Allowed Values | Notes |
|---|---|---|
| **Application Roles** | `ULMD_ADMIN`, `MAINTENANCE_TECH`, `LAB_MANAGER`, `LAB_TECH`, `AUDITOR` | Five canonical MVP roles; see stakeholder analysis §3. |
| **Asset Operational Status** | `OPERATIONAL`, `UNDER_MAINTENANCE`, `DEFECTIVE`, `TRANSFER_PENDING`, `DECOMMISSIONED` | `CALIBRATION_OVERDUE` is computed, not stored. |
| **Asset Category Lab Type** | `WET`, `DRY`, `COMPUTING`, `WORKSHOP` | Stored on `laboratories.lab_type`. |
| **Work Order Status** | `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `AWAITING_PARTS`, `AWAITING_APPROVAL`, `RESOLVED`, `CLOSED` | `AWAITING_APPROVAL` is conditional on DEC-02. |
| **Work Order Severity** | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Critical faults set the asset to `DEFECTIVE`. |
| **Failure Category** | `ELECTRICAL`, `MECHANICAL`, `OPTICAL`, `SOFTWARE`, `CONSUMABLE`, `OTHER` | Stored on `work_orders.failure_category`. |
| **Maintenance Outcome** | `OPERATIONAL`, `REPAIRED_DEGRADED`, `UNREPAIRABLE` | Stored on `maintenance_logs.outcome_condition`. |
| **Transfer Status** | `PENDING_RECEIVER`, `PENDING_ULMD`, `COMPLETED`, `REJECTED` | Asset status is `TRANSFER_PENDING` while the transfer is active. |
| **Audit Actions (examples)** | `ASSET_CREATED`, `STATUS_MODIFIED`, `TRANSFER_COMPLETED`, `WORK_ORDER_CLOSED`, `CALIBRATION_LOGGED` | Free-form action strings; examples are not exhaustive. |

---

## 7. 3NF Note on Asset Location

`assets` stores both `laboratory_id` (custodian laboratory) and `room_id` (current physical room). Stage 4 requires the selected room to belong to the selected laboratory and prevents changing the college/department code or hierarchy parents while referenced assets depend on them. A shared-instrument/cross-laboratory exception is mentioned as a possible future arrangement, but the approved requirements define no exception workflow or persisted authorization record; it is therefore not implemented. `asset_transfers` will preserve both laboratory and room identifiers so historical locations are never overwritten.
