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
- **Impact on System Design:** Determines whether the work order state machine requires an explicit `APPROVAL_PENDING` state before transitioning to `ASSIGNED`.
- **Proposed Baseline:** `CRITICAL` and `HIGH` severity tickets immediately notify the Technology Unit for rapid dispatch; tickets requiring external replacement parts exceeding a financial threshold require administrative sign-off.

### Open Question 3: Institutional Single Sign-On (SSO) Integration
- **Question:** Does Haramaya University operate a centralized LDAP or Microsoft Active Directory / Google Workspace identity provider that can be leveraged for user authentication?
- **Impact on System Design:** Determines whether the application must maintain an internal credentials database or integrate via OAuth2/OpenID Connect.
- **Proposed Baseline:** Design the system with standard JWT credentials authentication while isolating the authentication interface to permit pluggable LDAP/OAuth2 SSO integration in future iterations.

### Open Question 4: External Calibration Accreditation
- **Question:** Which specific laboratory instruments at Central Laboratories require certified external metrology accreditation (e.g., from the Ethiopian National Accreditation Office - ENAO) versus routine internal calibration?
- **Impact on System Design:** Determines metadata attributes required in calibration records, specifically external certificate document attachments and accreditation body tracking.
- **Proposed Baseline:** Include `standard_used`, `certificate_reference`, and optional document attachment capabilities within the calibration schema.
