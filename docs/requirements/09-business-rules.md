# 09. Business Rules Specification

This document codifies the operational policies, constraints, and business logic governing the Laboratory Asset Management and Maintenance Tracking System for Haramaya University.

---

## 1. Asset Identity & Cataloging Rules

- **BR-001 (Unique University Identification):**
  Every durable asset registered must be assigned an immutable, unique Asset Identification Code following the format:
  `HU-{COLLEGE_CODE}-{DEPT_CODE}-{5_DIGIT_AUTO_INCREMENT}` (e.g., `HU-HiT-CHEM-00042`).
  *Rationale:* Adheres to WHO LQSI guidelines for facility-specific equipment identification and prevents collision across colleges.

- **BR-002 (Manufacturer Serial Uniqueness):**
  The combination of `manufacturer_name` and `serial_number` must be globally unique within the system. The system must reject any attempt to register an existing manufacturer serial number unless the previous asset is marked `CONDEMNED_SCRAP`.

- **BR-003 (Strict Separation of Durable Assets & Consumables):**
  Only non-expendable equipment with an expected operational lifespan exceeding one year and requiring capital inventory tracking may be registered in the `assets` table. Volatile chemicals, solvents, glassware, and disposable plastics are strictly prohibited from this table.

---

## 2. Location & Custody Rules

- **BR-004 (Single Active Location Mandate):**
  At any given point in time, an asset must belong to exactly one physical Room within an identifiable Laboratory, Department, and College. Floating or unassigned assets are prohibited.

- **BR-005 (Dual-Authorization Custody Transfer):**
  Equipment cannot be relocated between laboratories or departments without a verified multi-step transaction:
  1. Initiation by the origin Laboratory Manager.
  2. Physical receipt and inspection acceptance by the destination Laboratory Manager.
  3. Administrative validation and confirmation by the ULMD Directorate.
  *Rationale:* Prevents "ghost equipment" and ensures accountability during university audits.

- **BR-006 (Transfer Lockout):**
  An asset currently undergoing a transfer workflow (`TRANSFER_PENDING`) cannot be modified, deleted, or transferred to another unit until the active transfer is either completed or formally rejected.

---

## 3. Maintenance & Operational Status Rules

- **BR-007 (Operational Condition State Machine):**
  An asset’s condition must strictly adhere to the following finite-state rules:
  ```
  ACQUIRED ──▶ OPERATIONAL ──▶ UNDER_MAINTENANCE ──▶ OPERATIONAL
                    │                    │
                    ├──▶ DEFECTIVE ──────┤
                    │                    ▼
                    └───────────▶ DECOMMISSIONED
  ```
  - An asset marked `DEFECTIVE` or `UNDER_MAINTENANCE` is locked from being scheduled for academic practical sessions or approved for transfers.
  - Restoration to `OPERATIONAL` requires a closed work order verified by the custodian Lab Manager.

- **BR-008 (Work Order Accountability):**
  A work order cannot be closed (`CLOSED`) without:
  1. A linked maintenance log detailing actions taken and spare parts used (or explicit "None" indicator).
  2. The registered ID of the servicing technician.
  3. Formal verification and sign-off by the custodian Laboratory Manager.

- **BR-009 (Calibration Expiry & Overdue Locking):**
  When an asset passes its `next_calibration_due` date without a certified calibration record being logged, the system must automatically flag the asset as `CALIBRATION_OVERDUE`. The asset passport and QR scans must display a visible compliance warning banner.

---

## 4. Decommissioning & Auditability Rules

- **BR-010 (Prohibition of Hard Deletion):**
  Physical assets and their associated maintenance logs cannot be deleted (`DELETE`) from the database. Unusable, obsolete, or damaged equipment must be transitioned to `DECOMMISSIONED` status with an attached condemnation reference in accordance with Haramaya University Senate Legislation.

- **BR-011 (Immutable Audit Logging):**
  Records in the `audit_logs` table are append-only. No user role, including `ULMD_ADMIN` or database administrators, possesses API privileges to alter (`UPDATE`) or remove (`DELETE`) historical audit records.

- **BR-012 (Role-Scoped Data Modification):**
  Department Laboratory Managers and Technical Assistants are strictly confined to creating or editing records within their assigned laboratory spaces. Cross-college or cross-department modifications require `ULMD_ADMIN` administrative privileges.
