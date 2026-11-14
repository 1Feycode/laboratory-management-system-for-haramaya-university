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

---

## 2. Stage 4 Decision Review

These outcomes record the evidence found in the approved requirements and current implementation. A conservative behavior is not a substitute for stakeholder approval where the governing policy is missing or contradictory.

### DEC-06 Outcome: Preserve the Unconditional Serial Constraint
- **Classification:** Requires stakeholder approval to change.
- **Evidence:** Phase 1 BR-002 permits reuse after decommissioning with a formal condemnation reference. The Phase 2 data dictionary and existing database constraint unconditionally enforce unique `(manufacturer_name, serial_number)`.
- **Resolution implemented:** Keep the unconditional constraint. Duplicate serial pairs continue to return `409 Conflict`, including pairs whose existing asset is `DECOMMISSIONED`. A regression test verifies the behavior. No migration or existing-record change is made.
- **Approval needed:** Yes, before any serial reuse or constraint change. ULMD and the university asset-records authority must approve both the reuse policy and its condemnation evidence requirements.

### DEC-07: Condemnation Reference and Decommissioning
- **Classification:** Requires stakeholder approval; no schema or workflow is implemented.
- **Evidence:** BR-010 requires an attached condemnation reference, but neither the approved asset fields, ERD, data dictionary, nor workflow defines the reference field, document relationship, format, issuer, approving role, or required evidence. The stakeholder interview asks about statutory condemnation procedure without recording an answer.
- **Recommendation:** Obtain the authoritative records procedure and specify the reference identifier and evidence source, whether a document attachment or external record link is required, the actor/approval evidence and date to retain, and the audit snapshot. Only then define a schema migration, transition API, and UI. Do not invent an official number or approval chain.
- **Current behavior:** Stage 4 has no decommissioning API or category-independent status mutation endpoint. No database migration was created.
- **Approval needed:** Yes, before implementing the reference field or decommissioning transition.

### DEC-08: Production Host for Asset QR Codes
- **Classification:** The configurable behavior is resolved and implemented; the actual production origin remains unconfirmed.
- **Evidence:** No canonical frontend origin is configured in environment settings or deployment configuration. `https://labs.haramaya.edu.et` appeared only as an illustrative CORS/workflow example and is not authoritative configuration.
- **Resolution implemented:** Optional `ASSET_PUBLIC_BASE_URL` accepts a frontend origin only. When configured, newly generated QR images contain `/assets/scan?code=...`; the protected frontend route uses authenticated asset lookup and redirects to the passport. The camera scanner accepts both URL and code-only payloads. When unset, the existing code-only QR payload is preserved. No production host is invented or enabled by default.
- **Approval needed:** No approval is needed for this configurable implementation. The deployment owner must confirm the reachable HTTPS frontend origin before setting the variable or printing URL-based production labels.

### DEC-09: Asset Category Administration
- **Classification:** Requires stakeholder approval; current implementation remains a provisional restriction.
- **Evidence:** The approved role matrix has no category-administration permission row. The approved category schema has no active/inactive field, and requirements do not define create, edit, delete, activate, or deactivate authority.
- **Current behavior:** Backend category create/update/delete endpoints require `ULMD_ADMIN`; the frontend exposes the management page only to `ULMD_ADMIN`. Authenticated users can read categories. Referenced categories cannot be deleted. Tests verify the current API restriction for an auditor. These guards are not evidence of an approved policy.
- **Recommendation for approval:** Select explicitly between (A) retaining `ULMD_ADMIN`-only create/edit/delete with no soft activation, (B) an admin-managed catalog with other roles read-only and a request-only path for proposed categories, or (C) a formally defined lifecycle with activation/deactivation and the required schema migration. Assign each action to one or more of the existing five roles; do not add a role.
- **Approval needed:** Yes, for the role/action matrix and any category lifecycle before changing the current guard or schema.

### DEC-10: Shared-Instrument Location Exception
- **Classification:** The current single-location rule is resolved by BR-004; any exception requires stakeholder approval.
- **Evidence:** BR-004 requires exactly one physical room within one laboratory, department, and college. The approved ERD and data dictionary model one `laboratory_id` and one `room_id` per asset. A possible future shared-instrument arrangement is mentioned without an approved association, custody, access, or audit workflow.
- **Resolution implemented:** Retain one accountable laboratory and one current room; keep existing room/laboratory parent validation. No multi-location association or validation bypass is added.
- **Recommendation for approval:** If shared use is required, preserve one accountable custodian and physical location and define a separate, time-bounded shared-access/booking relationship with named borrower, authorization, effective dates, and audit history. If stakeholders instead require simultaneous custody at multiple locations, specify that policy and its consequences before revising the ERD.
- **Approval needed:** No for enforcing BR-004. Yes before introducing any shared-instrument exception.

## 3. Stage 6 Maintenance Decision Boundaries

### DEC-02 Outcome: External-Parts Approval State
- **Classification:** Requires stakeholder approval; no approval state is implemented.
- **Evidence:** FR-007 describes `AWAITING_APPROVAL` as optional, and DEC-02 proposes it when external spare-parts procurement incurs budget expenditure. The approved materials do not state a monetary threshold, whether all external parts require approval, what documentation is required, who may approve in place of or in addition to the ULMD Directorate, or how rejection/cancellation affects the work order and asset.
- **Current implementation:** The additive Stage 6 schema and API allow `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `AWAITING_PARTS`, `RESOLVED`, and `CLOSED`. A technician may pause and resume for parts, but there is no spending approval endpoint or `AWAITING_APPROVAL` state. No budget or procurement subsystem was added.
- **Recommendation for approval:** Confirm (1) the exact event that requires approval, (2) any monetary threshold and currency, (3) the authorized approver(s), (4) required quote/reference and audit evidence, (5) approve/reject transitions and rejection notes, and (6) how the asset status behaves while approval is pending. Only after approval should the work-order check constraint, transition API, audit snapshots, UI actions, and migration be extended.
- **Approval needed:** Yes before adding an approval status or gate.

### DEC-11: Closure of Degraded or Unrepairable Outcomes
- **Classification:** Requires stakeholder approval; no disposition behavior is inferred.
- **Evidence:** The approved maintenance outcome values include `OPERATIONAL`, `REPAIRED_DEGRADED`, and `UNREPAIRABLE`. UC-05 and the maintenance workflow specify successful closure restoring the asset to `OPERATIONAL`; they do not define whether a degraded repair can return to service, who authorizes that return, or how an unrepairable asset transitions to `DECOMMISSIONED` with the required condemnation reference (see DEC-07).
- **Current implementation:** A repair log may record all three approved outcomes. Confirmed closure is accepted only when the latest outcome is `OPERATIONAL`; a confirmed close for either other outcome returns `409 Conflict`. The asset remains in its maintenance/defective state. The custodian may reject the repair back to `IN_PROGRESS`; no decommissioning or asset-status bypass is available.
- **Recommendation for approval:** Define separate decisions for degraded and unrepairable outcomes: permitted operating conditions and approving role for degraded equipment; and the required condemnation evidence, authorization, and lifecycle transition for unrepairable equipment. Align the approved asset state machine, audit fields, API, and screen actions before implementing the policy.
- **Approval needed:** Yes before supporting confirmed closure for non-operational outcomes or decommissioning from maintenance.
