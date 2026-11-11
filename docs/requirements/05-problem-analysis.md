# 05. Problem Analysis

This document provides a rigorous, evidence-based breakdown of the operational challenges affecting laboratory asset management and maintenance at Haramaya University. Each identified challenge is classified based on whether it is an officially verified fact, an observed operational problem, an international standard risk, or an industry challenge.

---

## 1. Problem Classification Matrix

| Challenge Area | Description & Operational Impact | Evidence & Traceability | Classification |
|---|---|---|---|
| **1. Disconnected Manual Record Keeping** | Laboratory inventories across 90+ labs are maintained on paper logbooks or isolated desktop spreadsheets. Records are prone to loss, data drift, and inconsistencies during staff rotations. | ULMD Materials Unit explicitly mandates quarterly paper reviews to collect inventory reports from lab managers. | **Verified University Practice** |
| **2. Untracked Cross-Lab Equipment Transfers** | Equipment moved between departments (e.g., engineering tools or portable analytical meters) often moves without formal central documentation, resulting in "ghost assets" during audits. | ULMD Teaching-Learning Unit conducts periodic surveys and questionnaires to locate and verify equipment status across departments. | **Observed Operational Problem** |
| **3. Maintenance Communication Latency** | When an instrument breaks down, reporting often relies on physical paper memos or verbal notifications delivered to Central Lab Building Office 34, causing weeks of idle downtime before an engineer is dispatched. | Identified in the organizational structure: centralized Technology Unit servicing 90+ labs requires structured dispatching. | **Observed Operational Problem** |
| **4. Lack of Historical Service Records** | Equipment lacks centralized digital logs documenting past repairs, replaced components, failure frequencies, or previous calibration results. Technicians must diagnose recurring faults from scratch. | Non-compliance with WHO LQSI Section 1.4 and ISO 15189 (Clause 5.3.1); identified by Africa CDC as a primary cause of premature equipment failure in Africa. | **International Benchmark Challenge** |
| **5. Overdue Calibration of Precision Instruments** | Analytical balances, spectrophotometers, autoclaves, and micropipettes operate without automated reminders for annual or semi-annual calibration, threatening test accuracy. | Required by ISO/IEC 17025 standards and ULMD Central Laboratories' target for ISO accreditation. | **International Benchmark Challenge** |
| **6. Duplicated Procurement Requisitions** | Departments request new equipment from the university procurement office while identical functional equipment sits underutilized in a neighboring college. | ULMD Materials Unit mandate explicitly instructs the unit to "evaluate purchasing requisitions and cross-check them with up-to-date inventories to avoid unwise resource use." | **Verified University Practice** |
| **7. Ambiguous Maintenance Demarcation** | Confusion between building utility failures (managed by EFMD BMOM) and internal laboratory instrument repairs (managed by ULMD Technology Unit) causes repair delays. | Delineation established between EFMD mandate (campus plant) and ULMD mandate (internal lab electrical/plumbing/equipment). | **Organizational Boundary Challenge** |

---

## 2. Root Cause Analysis (Ishikawa Fishbone)

```
 PEOPLE                                    PROCESS
 (Staff Rotation, Verbal Requests)        (Paper Memos, Unstructured Borrowing)
          \                                      /
           \                                    /
            \                                  /
             v                                v
    ────────────────────────────────────────────────────────► PROBLEM:
             ^                                ^               Equipment Downtime,
            /                                  \              Lost Assets, and
           /                                    \             Audit Inaccuracy
          /                                      \
 (No Central Database, Multi-Campus)     (No Automated Calibration Alerts)
 ENVIRONMENT                              TECHNOLOGY
```

1. **People:**
   - Technical assistants rotate between departments, carrying undocumented institutional knowledge with them.
   - Laboratory managers lack a centralized platform to communicate immediately with the Central Lab Technology Unit.
2. **Process:**
   - Formal paper memos require physical transport across campuses (Main Campus to Harar Campus or HiT).
   - Informal borrowing between colleagues bypasses official inventory records.
3. **Technology:**
   - Absence of barcoding or QR tagging forces manual transcription of serial numbers, leading to clerical errors.
   - Disconnected spreadsheets lack referential integrity, historical tracking, and concurrent multi-user access.
4. **Environment:**
   - Geographical separation between the Main Campus (Central Laboratory Building) and satellite campuses (e.g., Harar Medical Campus) slows down physical paperwork.

---

## 3. Targeted System Solutions

| Root Cause | System Capability Designed in Phase 2 |
|---|---|
| Manual paper records & transcription errors | Unique QR code generation for every asset; bench-side mobile camera lookup. |
| Untracked equipment relocation | Multi-step digital transfer workflow with dual-authorization and immutable audit logging. |
| Maintenance request latency | Centralized digital work order dispatching with real-time severity alerts and technician assignment. |
| Missing repair history | Mandatory digital maintenance logs recording symptoms, actions, spare parts, and labor hours per ticket. |
| Missed calibration deadlines | Automated calibration tracking with dynamic overdue flags and dashboard warning banners. |
| Uncoordinated procurement | Centralized, searchable university-wide asset catalog enabling ULMD to verify existing inventory before approving purchases. |
