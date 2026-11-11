# Database Data Dictionary

This document specifies the PostgreSQL 15+ relational schema for the Laboratory Asset Management and Maintenance Tracking System, covering all 12 normalized tables, column constraints, referential actions, and performance indexes.

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
- **`asset_code`** (`VARCHAR(100)`, NOT NULL, UNIQUE): Formatted code (`HU-{COLLEGE}-{DEPT}-{AUTO}`).
- **`serial_number`** (`VARCHAR(100)`, NOT NULL): Manufacturer serial number.
- **`model_number`** (`VARCHAR(100)`, NOT NULL): Equipment model.
- **`manufacturer_name`** (`VARCHAR(150)`, NOT NULL): Manufacturer.
- **`category_id`** (`UUID`, NOT NULL, FK -> `asset_categories.id` ON DELETE RESTRICT): Equipment category.
- **`laboratory_id`** (`UUID`, NOT NULL, FK -> `laboratories.id` ON DELETE RESTRICT): Custodian laboratory.
- **`room_id`** (`UUID`, NOT NULL, FK -> `rooms.id` ON DELETE RESTRICT): Current physical room.
- **`operational_status`** (`VARCHAR(50)`, NOT NULL, DEFAULT 'OPERATIONAL'): `OPERATIONAL`, `UNDER_MAINTENANCE`, `DEFECTIVE`, `DECOMMISSIONED`.
- **`purchase_date`** (`DATE`, NULLABLE): Date of purchase invoice.
- **`commissioning_date`** (`DATE`, NULLABLE): Date installed and put into active service.
- **`warranty_expiry_date`** (`DATE`, NULLABLE): Warranty expiration date.
- **`last_calibrated_date`** (`DATE`, NULLABLE): Most recent calibration date.
- **`next_calibration_due`** (`DATE`, NULLABLE): Scheduled calibration deadline.
- **`qr_code_path`** (`VARCHAR(255)`, NULLABLE): Vector QR code storage reference.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Creation timestamp.
- **`updated_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Mutation timestamp.
- **Constraints & Indexes:**
  - Unique composite: `uk_assets_serial_mfr UNIQUE (manufacturer_name, serial_number)`
  - Unique code index: `idx_assets_code (asset_code)`
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
- **`target_laboratory_id`** (`UUID`, NOT NULL, FK -> `laboratories.id` ON DELETE RESTRICT): Destination laboratory.
- **`initiated_by`** (`UUID`, NOT NULL, FK -> `users.id`): Origin Lab Manager.
- **`accepted_by`** (`UUID`, NULLABLE, FK -> `users.id`): Destination Lab Manager.
- **`approved_by_ulmd`** (`UUID`, NULLABLE, FK -> `users.id`): ULMD Admin sign-off.
- **`status`** (`VARCHAR(50)`, NOT NULL, DEFAULT 'PENDING_RECEIVER'): `PENDING_RECEIVER`, `PENDING_ULMD`, `COMPLETED`, `REJECTED`.
- **`transfer_reason`** (`TEXT`, NOT NULL): Administrative justification.
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
- **`status`** (`VARCHAR(50)`, NOT NULL, DEFAULT 'OPEN'): `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `AWAITING_PARTS`, `RESOLVED`, `CLOSED`.
- **`fault_description`** (`TEXT`, NOT NULL): Detailed symptom report.
- **`created_at`** (`TIMESTAMPTZ`, NOT NULL, DEFAULT `NOW()`): Report timestamp.
- **`resolved_at`** (`TIMESTAMPTZ`, NULLABLE): Repair completion timestamp.
- **`closed_at`** (`TIMESTAMPTZ`, NULLABLE): Custodian verification timestamp.
- **Indexes:** `idx_wo_asset (asset_id)`, `idx_wo_status (status)`, `idx_wo_assigned (assigned_to)`

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
