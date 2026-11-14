# 12. Assumptions and Open Questions

This document captures the working assumptions adopted during Phase 1 analysis and details open technical and organizational questions requiring formal validation from Haramaya University stakeholders before Phase 3 implementation.

---

## 1. Validated Institutional Facts vs. Working Assumptions

| Topic | Verified Institutional Fact | Working Technical Assumption | Risk if Assumption is Invalid |
|---|---|---|---|
| **Laboratory Governance** | ULMD centralizes maintenance and standards (Central Lab Bldg, Off. 34); departments hold physical custody. | A unified web-based system can serve both centralized oversight and decentralized laboratory custody. | Low. The role-based access architecture natively separates directorate oversight from departmental execution. |
| **Asset Coding** | University requires accountable property identification. | Existing asset tag numbers can be mapped into the standard pattern: `HU-{COLLEGE}-{DEPT}-{SEQ}`. | Medium. If departments use incompatible historical barcodes, a legacy tag mapping field must be preserved during data migration. |
| **Network Infrastructure** | Campuses are connected to university network backbones. | Laboratory rooms have reliable intranet or Wi-Fi access for bench-side QR scanning. | High. Sub-basement wet labs or remote agricultural research stations may suffer intermittent connectivity, requiring offline PWA caching. |
| **Maintenance Capacity** | ULMD Technology Unit provides equipment repairs across all university laboratories. | The Technology Unit has sufficient technical staff to triage and service digital work order queues in real time. | Medium. If staffing is constrained, work order prioritization and escalation SLAs must be introduced. |
| **Equipment Scope** | University has 90–150+ wet and dry laboratories. | Durable analytical and educational machinery should be tracked separately from consumable chemical reagents. | Low. Keeping durable machinery distinct avoids database bloat and ensures high data integrity. |

---

## 2. Open Questions Requiring Stakeholder Confirmation

### Open Question 1: Legacy Asset Tagging & Migration
- **Question:** Do academic colleges currently possess a unified barcode system, or do departments maintain divergent, disconnected numbering schemes?
- **Impact on System Design:** Determines whether initial data migration can automatically generate QR codes or whether physical re-labeling of all 90+ laboratories will be required during rollout.
- **Proposed Baseline:** The system generates a standardized `asset_code` while providing an optional `legacy_tag_number` field to preserve existing departmental inventory numbers.

### Open Question 2: Repair Approval Thresholds
- **Question:** Does the ULMD Director or Department Head need to approve maintenance requests before a technician is dispatched, or is dispatching automatic based on severity?
- **Impact on System Design:** Determines whether the work order state machine requires an explicit `AWAITING_APPROVAL` state before transitioning to `ASSIGNED`.
- **Proposed Baseline:** `CRITICAL` and `HIGH` severity tickets immediately notify the Technology Unit for rapid dispatch; tickets requiring external replacement parts exceeding a financial threshold require administrative sign-off.
- **Implementation clarification:** The DEC-02 request/decision mechanism is implemented, but this proposed threshold and sign-off role are not treated as an approved institutional policy. The technical flow requires an explicit request by the assigned technician, supports only free-text details, has no default approver roles, and leaves rejection blocked pending stakeholder direction. See [DEC-02 implementation outcome](../design/phase-2-open-decisions.md#dec-02-outcome-external-parts-approval-state).

### Open Question 3: Institutional Single Sign-On (SSO) Integration
- **Question:** Does Haramaya University operate a centralized LDAP or Microsoft Active Directory / Google Workspace identity provider that can be leveraged for user authentication?
- **Impact on System Design:** Determines whether the application must maintain an internal credentials database or integrate via OAuth2/OpenID Connect.
- **Proposed Baseline:** Design the system with standard JWT credentials authentication while isolating the authentication interface to permit pluggable LDAP/OAuth2 SSO integration in future iterations.

### Open Question 4: External Calibration Accreditation
- **Question:** Which specific laboratory instruments at Central Laboratories require certified external metrology accreditation (e.g., from the Ethiopian National Accreditation Office - ENAO) versus routine internal calibration?
- **Impact on System Design:** Determines metadata attributes required in calibration records, specifically external certificate document attachments and accreditation body tracking.
- **Proposed Baseline:** Include `standard_used`, `certificate_reference`, and `accreditation_body` (nullable) within the calibration schema; binary certificate upload remains a Release 2 enhancement.

### Open Question 5: Canonical Application Role Set
- **Question:** Should College Deans and Department Heads receive a distinct `DEPT_HEAD` application role, or should their read-only analytics access be delivered through a department-scoped `AUDITOR` assignment?
- **Impact on System Design:** A sixth role would require changes to the `roles` table, RBAC matrix, API guards, and navigation. The current design uses five canonical roles and maps Department Heads to department-scoped `AUDITOR` access.
- **Proposed Baseline:** Retain the five-role MVP (`ULMD_ADMIN`, `MAINTENANCE_TECH`, `LAB_MANAGER`, `LAB_TECH`, `AUDITOR`). Revisit a dedicated `DEPT_HEAD` role only if stakeholder interviews confirm a need for departmental approval workflows.

### Open Question 6: Notification Delivery Channel
- **Question:** Should work order and transfer alerts be delivered only as in-application queues, or also by institutional email/SMS?
- **Impact on System Design:** Persistent notification records and external delivery adapters would add tables, background workers, and credentials. The MVP derives alerts from open work orders and pending transfers.
- **Proposed Baseline:** MVP provides in-application queues and dashboard badges only. Email/SMS delivery is deferred to Release 2 and documented as an open decision.

### Open Question 7: Full Room-Level Transfer History
- **Question:** Must the audit trail preserve the exact room (not only the laboratory) from which an asset departed and the room to which it arrived?
- **Impact on System Design:** The `asset_transfers` table must store `origin_room_id` and `target_room_id` in addition to laboratory identifiers.
- **Proposed Baseline:** Yes. Phase 2 adds origin and target room foreign keys to `asset_transfers` so the complete physical location history is retained.

### Open Question 8: Serial Number Reuse After Decommissioning
- **Question:** Does a formally condemned asset release its manufacturer/serial-number pair for reuse, or must the pair remain reserved permanently?
- **Impact on System Design:** Reuse would require changing the unconditional Phase 2 uniqueness constraint and defining how historical and new assets remain distinguishable. The Phase 1 exception requires a condemnation reference, but that reference is not defined in the approved schema.
- **Proposed Baseline:** Keep the unconditional constraint and reject duplicates, including pairs on decommissioned assets, until ULMD and the university asset-records authority approve a complete reuse and condemnation policy.

### Open Question 9: Condemnation Evidence and Decommissioning
- **Question:** What exact institutional record identifies condemnation, and what identifier, evidence attachment, issuer, approval evidence, date, and retention relationship must the system preserve?
- **Impact on System Design:** The answer determines the approved schema, transition validation, API request, role authorization, audit snapshot, and user interface for decommissioning.
- **Proposed Baseline:** Do not create a field, format, legal interpretation, or approval workflow by assumption. Obtain the authoritative records procedure and define these items before implementing a decommissioning transition.

### Open Question 10: Asset Category Administration
- **Question:** Which existing role may create, edit, delete, activate, or deactivate shared asset categories, and should categories support an active/inactive lifecycle?
- **Impact on System Design:** Determines backend permission guards, frontend visibility, and whether a category status field and migration are required. The approved category schema currently has no active/inactive field.
- **Proposed Baseline:** Preserve the existing `ULMD_ADMIN`-only create/update/delete guards as a provisional restriction, not an approved role policy. Keep reads available to authenticated users and require ULMD to select an authorization and lifecycle policy.

### Open Question 11: Shared-Instrument Location Exception
- **Question:** Must a shared instrument have one accountable custodian and physical room, or may it be associated with multiple laboratories, departments, or rooms at the same time?
- **Impact on System Design:** Multiple current associations would change asset relationships, validation, transfer history, audit events, and the ownership/custody model.
- **Proposed Baseline:** Retain BR-004's single current room and laboratory. If shared access is desired, first define whether it is an access/booking arrangement distinct from physical custody; do not model multiple locations until that distinction and its authorization workflow are approved.

### Open Question 12: Canonical Public Frontend Origin for QR Links
- **Question:** What confirmed, HTTPS-reachable frontend origin should be encoded in asset QR links, and is the application mounted at the origin root?
- **Impact on System Design:** The configured origin determines whether printed URL-based QR labels open the correct protected asset lookup route on university and mobile networks.
- **Proposed Baseline:** No canonical production origin is currently configured. Keep `ASSET_PUBLIC_BASE_URL` optional; configure it only after the deployment origin is confirmed. When absent, QR codes continue to contain the asset code only.
