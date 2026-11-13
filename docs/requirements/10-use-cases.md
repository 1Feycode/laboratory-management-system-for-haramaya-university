# 10. Use Cases and Workflows

This document details the primary system actors and concrete use cases governing interactions within the Laboratory Asset Management and Maintenance Tracking System.

---

## 1. Actor Catalog

| Actor Name | Description | Institutional Counterpart |
|---|---|---|
| **Lab Technician (LT)** | Operates equipment during classes; performs bench checks; reports breakdowns. | Department Technical Assistants (TAs). |
| **Lab Manager (LM)** | Custodian of specific laboratory rooms; manages assets; verifies repairs; initiates transfers. | Senior TAs / Appointed Lab Managers. |
| **Maintenance Tech (MT)** | Performs bioengineering maintenance, repairs, instrument calibration, and installation. | ULMD Laboratory Technology Unit Specialists. |
| **ULMD Admin (UA)** | Directorate leadership; manages university-wide master data; dispatches work orders; approves transfers. | ULMD Director / Unit Supervisors (Office 34). |
| **Auditor (AU)** | Inspects inventory compliance, equipment downtime, and maintenance history. | ULMD Materials Unit / External University Auditors. |

---

## 2. Core Use Cases

### UC-01: Scan QR & View Asset Passport
- **Primary Actor:** Lab Technician, Lab Manager, Maintenance Tech, Auditor.
- **Preconditions:** Asset has been registered and tagged with a physical QR code label.
- **Trigger:** Actor scans physical QR code with a smartphone camera or handheld barcode scanner.
- **Main Flow:**
  1. Scanner captures QR payload and decodes the asset identification URL.
  2. System resolves asset passport via `GET /api/v1/assets/lookup/{asset_code}`.
  3. System renders the asset passport view displaying technical specifications, custodian laboratory, room location, operational condition, and calibration validity.
  4. If actor is authenticated, system displays contextual action buttons ("Report Fault", "View Service Log").
- **Alternative Flow:** Asset code unrecognized -> System displays "Asset Not Found" with an option to report an unindexed piece of equipment to ULMD.

### UC-02: Register Durable Laboratory Asset
- **Primary Actor:** Lab Manager, ULMD Admin.
- **Preconditions:** Actor is authenticated with appropriate role permissions; laboratory and room exist in the system.
- **Trigger:** New equipment is delivered, inspected, and commissioned in a laboratory.
- **Main Flow:**
  1. Actor navigates to "Asset Registration" form.
  2. Actor inputs equipment specifications: Category, Manufacturer, Model, Serial Number, Purchase Date, Commissioning Date, Warranty Date, Assigned Room.
  3. Actor submits form.
  4. System verifies that the manufacturer serial number is unique.
  5. System generates the standard asset code (`HU-{COLLEGE}-{DEPT}-{AUTO}`).
  6. System generates a high-density vector QR code.
  7. System persists the asset record and writes an immutable audit log.
  8. System renders a confirmation screen with a printable QR code label.
- **Alternative Flow:** Serial number already exists -> System rejects submission with HTTP 409 Conflict, displaying the conflicting asset's passport.

### UC-03: Report Equipment Fault & Open Ticket
- **Primary Actor:** Lab Technician, Lab Manager.
- **Preconditions:** Equipment exhibits malfunction, physical damage, or operational failure.
- **Trigger:** Actor discovers equipment failure during bench operations.
- **Main Flow:**
  1. Actor accesses asset passport (via QR scan or manual search) and clicks "Report Fault".
  2. Actor selects severity level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), selects failure category (electrical, mechanical, optical, software), and enters a detailed symptom description.
  3. Actor submits report.
  4. System generates a unique work order ticket (`WO-{YEAR}-{AUTO}`).
  5. System updates asset operational condition: `DEFECTIVE` (if Critical) or `UNDER_MAINTENANCE` (if Low/Medium/High).
  6. System dispatches a real-time notification to the ULMD Technology Unit queue.
- **Alternative Flow:** Asset is already in `UNDER_MAINTENANCE` -> System prompts actor with the existing open work order and allows appending additional diagnostic notes.

### UC-04: Assign and Execute Maintenance Work Order
- **Primary Actor:** ULMD Admin (assigns), Maintenance Tech (executes).
- **Preconditions:** Open work order exists in the Technology Unit dispatch queue.
- **Trigger:** Technology Unit supervisor reviews daily maintenance backlog.
- **Main Flow:**
  1. ULMD Admin selects open work order and assigns it to a Maintenance Tech.
  2. Ticket status transitions to `ASSIGNED`.
  3. Maintenance Tech inspects assigned tickets on mobile/desktop and accepts ticket -> Status transitions to `IN_PROGRESS`.
  4. Maintenance Tech conducts bench diagnostic and physical repair at the laboratory.
  5. Maintenance Tech navigates to ticket, inputs repair log: actions taken, spare parts utilized, labor hours, and outcome condition (`OPERATIONAL`, `REPAIRED_DEGRADED`, `UNREPAIRABLE`).
  6. Ticket status transitions to `RESOLVED`.
  7. System alerts the custodian Lab Manager to verify equipment operation.
- **Alternative Flow:** Spare parts unavailable -> Maintenance Tech sets ticket status to `AWAITING_PARTS` with estimated arrival notes.

### UC-05: Verify and Close Maintenance Ticket
- **Primary Actor:** Lab Manager.
- **Preconditions:** Work order is in `RESOLVED` status.
- **Trigger:** Maintenance Tech completes physical repair and requests operational verification.
- **Main Flow:**
  1. Lab Manager conducts test run of the repaired instrument in the laboratory.
  2. If satisfied, Lab Manager navigates to ticket, enters verification comments, and clicks "Verify & Close Ticket".
  3. System records the verifying Lab Manager UUID and verification notes, then updates ticket status to `CLOSED`.
  4. System updates asset operational condition to `OPERATIONAL`.
  5. System writes an immutable audit record.
- **Alternative Flow:** Instrument still malfunctioning -> Lab Manager clicks "Reject Repair" with detailed feedback -> Ticket status reverts to `IN_PROGRESS` and notifies the technician.

### UC-06: Transfer Asset Custody Between Laboratories
- **Primary Actor:** Origin Lab Manager, Destination Lab Manager, ULMD Admin.
- **Preconditions:** Asset is currently in `OPERATIONAL` condition.
- **Trigger:** Academic departments agree to relocate or reassign an instrument.
- **Main Flow:**
  1. Origin Lab Manager initiates transfer request specifying Asset ID, Destination Laboratory, Destination Room, and justification.
  2. System sets asset condition to `TRANSFER_PENDING` and transfer status to `PENDING_RECEIVER`.
  3. Destination Lab Manager inspects the physical equipment upon delivery and clicks "Accept Asset".
  4. System sets transfer status to `PENDING_ULMD`.
  5. ULMD Admin reviews transfer justification and approves the reassignment.
  6. System updates asset `laboratory_id` and `room_id` foreign keys.
  7. System sets transfer status to `COMPLETED` and restores asset condition to `OPERATIONAL`.
  8. System records the origin and destination laboratory **and room** in `asset_transfers` history and writes an audit log.
- **Alternative Flow:** Destination Lab Manager or ULMD Admin rejects transfer -> System sets transfer status to `REJECTED`, retains original location, and restores asset condition to `OPERATIONAL`.

### UC-07: Log Certified Calibration Event
- **Primary Actor:** Maintenance Tech, ULMD Admin.
- **Preconditions:** Asset category requires periodic calibration (e.g., analytical balance, spectrophotometer).
- **Trigger:** Scheduled calibration interval reached or post-repair recalibration required.
- **Main Flow:**
  1. Maintenance Tech performs standardized calibration using certified reference materials.
  2. Maintenance Tech accesses asset passport and navigates to "Log Calibration".
  3. Maintenance Tech inputs calibration date, standard/buffer used, certificate reference number, pass/fail result, and next scheduled due date.
  4. System records entry in `calibration_logs`.
  5. System updates asset `last_calibrated_date` and `next_calibration_due`.
  6. If previously marked `CALIBRATION_OVERDUE`, system clears the warning flag.
  7. System appends record to audit log.
