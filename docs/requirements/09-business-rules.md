# 09. Business Rules Specification

This document codifies the operational policies, constraints, and business logic governing the Laboratory Asset Management and Maintenance Tracking System for Haramaya University.

---

## 1. Asset Identity & Cataloging Rules

- **BR-001 (Unique University Identification):**
  Every durable asset registered must be assigned an immutable, unique Asset Identification Code following the format:
  `HU-{COLLEGE_CODE}-{DEPT_CODE}-{4_DIGIT_AUTO_INCREMENT}` (e.g., `HU-HiT-CHEM-0014`).
  *Rationale:* Adheres to WHO LQSI guidelines for facility-specific equipment identification and prevents collision across colleges. The four-digit sequence is the canonical MVP format used consistently across the API examples, workflow diagrams, and repository conventions. If the university inventory exceeds 9,999 assets in a single department, a future migration may widen the sequence to five digits.

- **BR-002 (Manufacturer Serial Uniqueness):**
  The combination of `manufacturer_name` and `serial_number` must be globally unique within the system. The system must reject any attempt to register an existing manufacturer serial number unless the previous asset is marked `DECOMMISSIONED` with a formal condemnation reference.

  **Implementation clarification ([DEC-06](../design/phase-2-open-decisions.md#dec-06-serial-number-reuse-after-decommissioning)):** Phase 2 specifies an unconditional database uniqueness constraint and the Stage 4 implementation retains it. A decommissioned record therefore still reserves its manufacturer/serial pair. The Phase 1 reuse exception is unresolved pending stakeholder confirmation; no constraint change or migration is authorized yet.

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
  OPERATIONAL ──▶ UNDER_MAINTENANCE ──▶ OPERATIONAL
       │                    │
       ├──▶ DEFECTIVE ──────┤
       │                    ▼
       ├──▶ TRANSFER_PENDING ──▶ OPERATIONAL
       │
       └───────────▶ DECOMMISSIONED
  ```
  - `ACQUIRED` is a pre-commissioning procurement state. Assets enter the application at `OPERATIONAL` after commissioning; `ACQUIRED` is not persisted as an MVP asset status.
  - An asset marked `DEFECTIVE`, `UNDER_MAINTENANCE`, or `TRANSFER_PENDING` is locked from being scheduled for academic practical sessions or approved for additional transfers.
  - Restoration to `OPERATIONAL` requires a closed work order verified by the custodian Lab Manager (or completion/rejection of the active transfer for `TRANSFER_PENDING`).

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

  **Specification gap:** The approved asset schema does not define the condemnation reference field, its document relationship or format, or the required issuing/approval evidence. No decommissioning endpoint is implemented until these details are approved; see [Open Question 9](./12-assumptions-and-open-questions.md#open-question-9-condemnation-evidence-and-decommissioning) and [DEC-07](../design/phase-2-open-decisions.md#dec-07-condemnation-reference-and-decommissioning).

- **BR-011 (Immutable Audit Logging):**
  Records in the `audit_logs` table are append-only. No user role, including `ULMD_ADMIN` or database administrators, possesses API privileges to alter (`UPDATE`) or remove (`DELETE`) historical audit records.

- **BR-012 (Role-Scoped Data Modification):**
  Department Laboratory Managers and Technical Assistants are strictly confined to creating or editing records within their assigned laboratory spaces. Cross-college or cross-department modifications require `ULMD_ADMIN` administrative privileges.
