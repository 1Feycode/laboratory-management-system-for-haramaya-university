# Phase 2 Open Design Decisions and Field Clarifications

This document catalogs the open architectural and operational decisions identified during Phase 2 system design. For each gap, a justified technical baseline has been designed, which remains subject to formal stakeholder review and confirmation before Phase 3 implementation.

---

## 1. Catalog of Open Design Decisions

### DEC-01: Barcode / QR Label Migration Strategy
- **Context:** Haramaya University has over 90 laboratories. Certain engineering and agricultural departments may have historical internal numbering schemes or paper tags.
- **Design Impact:** If the system strictly requires its own new format (`HU-COLLEGE-DEPT-SEQ`), existing equipment must be re-labeled physically during system onboarding.
- **Proposed Technical Baseline:** The system adopts the Phase 1 business-rule format `HU-{COLLEGE}-{DEPT}-{4_DIGIT_SEQ}` as the authoritative asset code, while providing an optional indexed column `legacy_tag_number` in the `assets` table. This allows barcode lookups using either the old department tag or the new universal QR code. The sequence width must be revisited if a department approaches 9,999 registered assets.
- **Confirmation Authority:** ULMD Director & College Deans.

---

### DEC-02: Work Order Approval Thresholds
- **Context:** When a technician reports an instrument failure, does every work order require administrative approval from the ULMD Director before an engineer is dispatched, or is dispatching automatic based on severity?
- **Design Impact:** Introducing an approval bottleneck could slow down emergency repairs for critical teaching equipment.
- **Proposed Technical Baseline:** 
  1. `CRITICAL` and `HIGH` severity tickets immediately route to the Technology Unit active work queue for immediate triage.
  2. Tickets requiring external spare parts procurement that incur budgetary expenditures route to an `AWAITING_APPROVAL` status requiring ULMD Directorate sign-off.
- **Confirmation Authority:** ULMD Technology Unit Supervisor.

---

### DEC-03: Demarcation Between Local Laboratory Repairs and Central Tech Unit
- **Context:** Certain routine bench maintenance tasks (e.g., replacing a blown fuse, changing microscope bulbs, replacing tubing) are handled locally by departmental Technical Assistants (TAs), while electronic calibrations and board replacements require Central Lab engineers.
- **Design Impact:** If every minor fix requires a formal ticket sent to Office 34, the Technology Unit queue could become overwhelmed.
- **Proposed Technical Baseline:** Department Lab Managers are granted permission to log and immediately close local "Routine Maintenance" work orders within their own department, ensuring that service history is recorded without generating central dispatch tickets.
- **Confirmation Authority:** ULMD Technology Unit & Chief TAs.

---

### DEC-04: Institutional Identity Provider Integration
- **Context:** Haramaya University utilizes institutional email accounts (`@haramaya.edu.et`). It is undetermined whether a central LDAP, Microsoft Active Directory, or Google Workspace directory is exposed for internal application authentication.
- **Design Impact:** Determines whether the application maintains its own local credentials database or delegates identity management to an institutional Single Sign-On (SSO) provider.
- **Proposed Technical Baseline:** Phase 2 designs a standalone JWT credential authentication system using salted bcrypt password hashes. The authentication service interface (`app/services/auth_service.py`) is decoupled, allowing pluggable OAuth2/LDAP connectors to be added in the future without disrupting the rest of the application.
- **Confirmation Authority:** Haramaya University ICT Directorate.

---

### DEC-05: Metrology & External Calibration Standards Traceability
- **Context:** Central Laboratories (specifically Soil/Water and Food Microbiology) are preparing for ISO standard certification. It is unconfirmed which specific metrology bodies (e.g., Ethiopian National Accreditation Office - ENAO or national metrology institutes) certify the reference standards used.
- **Design Impact:** Affects the schema attributes required in calibration logs.
- **Proposed Technical Baseline:** The `calibration_logs` table includes generic fields for `standard_used`, `certificate_reference`, and `accreditation_body` (nullable), accommodating both internal routine calibrations and certified external ISO audits.
- **Confirmation Authority:** Central Laboratories Unit Head.

---

### DEC-06: Serial Number Reuse After Decommissioning
- **Context:** Phase 1 business rule BR-002 permits reuse of a manufacturer/serial-number pair when the prior asset is decommissioned with a formal condemnation reference. The Phase 2 data dictionary specifies a unique constraint across all assets, which would prohibit that reuse.
- **Design Impact:** The policy determines whether the uniqueness constraint is unconditional or excludes decommissioned assets, and how historical identity remains unambiguous.
- **Proposed Technical Baseline:** Do not weaken the Phase 2 unique constraint until the intended reuse policy and audit implications are confirmed. The existing Phase 1 exception remains unresolved; API behavior and the final constraint must follow stakeholder confirmation.
- **Confirmation Authority:** ULMD Directorate and the university asset-records authority.
