# 04. Stakeholder Analysis

This document identifies the institutional stakeholders involved in the laboratory management ecosystem at Haramaya University, detailing their operational responsibilities, information requirements, assigned system roles, and anticipated benefits.

---

## 1. Institutional Governance Hierarchy

```
                            ┌──────────────────────────────┐
                            │    Haramaya University       │
                            │  Managing Board & Senate     │
                            └──────────────┬───────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
     ┌─────────────────────────────┐               ┌─────────────────────────────┐
     │  Vice President for         │               │  Vice President for         │
     │  Academic Affairs (VPAA)    │               │  Administration & Dev (VPAD)│
     └──────────────┬──────────────┘               └──────────────┬──────────────┘
                    │                                             │
     ┌──────────────┴──────────────┐                              │
     ▼                             ▼                              ▼
┌──────────────┐            ┌──────────────┐               ┌──────────────┐
│ Academic     │            │    ULMD      │               │     EFMD     │
│ Deans &      │            │ Directorate  │               │ Directorate  │
│ Dept Heads   │            │  (Off. 34)   │               │   (BMOM)     │
└──────┬───────┘            └──────┬───────┘               └──────────────┘
       │                           │
       ▼                           ▼
┌──────────────┐            ┌──────────────┐
│ Department   │            │ Tech Unit,   │
│ Lab Managers │            │ Materials    │
│ & Chief TAs  │            │ Unit & Cent. │
└──────┬───────┘            └──────┬───────┘
       │                           │
       └─────────────┬─────────────┘
                     ▼
      ┌─────────────────────────────┐
      │   Laboratory Technicians    │
      │   & Technical Assistants    │
      └─────────────────────────────┘
```

---

## 2. Comprehensive Stakeholder Catalog

### 1. ULMD Leadership (Director & Supervisors)
- **Institutional Role:** Executive oversight of all university laboratories; policy enforcement; inter-college resource balancing; central reporting to Academic Vice President.
- **Information Provided:** University policies, standard operating procedures (SOPs), audit validation, approval of major cross-college asset reallocations.
- **Information Needed:** Real-time visibility into equipment inventory across all 90+ labs, equipment uptime/downtime statistics, maintenance backlog, and calibration compliance.
- **System Role:** `ULMD_ADMIN`
- **Expected Benefits:** Complete operational visibility without relying on slow quarterly paper compilations; data-driven capital allocation.

### 2. Laboratory Technology Unit (Engineers & Maintenance Specialists)
- **Institutional Role:** Technical bioengineering and instrument maintenance; equipment installation; routine calibration; repairing laboratory plumbing and electrical fixtures.
- **Information Provided:** Diagnostic findings, repair actions taken, spare parts used, labor hours, calibration certificates, and equipment condition sign-offs.
- **Information Needed:** Queue of open work orders, fault severity levels, equipment manufacturer manuals, historical maintenance logs, and past calibration dates.
- **System Role:** `MAINTENANCE_TECH`
- **Expected Benefits:** Structured digital work order queue; elimination of verbal or lost paper memos; complete historical repair logs for every machine.

### 3. Laboratory Materials and Consumables Unit
- **Institutional Role:** Quarterly inventory reviews; evaluation of departmental purchase requisitions against current stock; resource waste reduction; Kaizen 5S enforcement.
- **Information Provided:** Quarterly audit schedules, inventory discrepancy notifications, procurement cross-check clearance.
- **Information Needed:** Accurate asset counts per department, equipment operational status, lists of obsolete or unrepairable equipment awaiting condemnation.
- **System Role:** `INVENTORY_AUDITOR`
- **Expected Benefits:** Eliminates duplicate procurement requests; enables fast reconciliation between physical laboratory audits and central records.

### 4. College Deans and Department Heads
- **Institutional Role:** Academic program resource management; laboratory space allocation; approving departmental equipment transfer requests.
- **Information Provided:** Departmental priorities, technician work allocations, transfer authorizations.
- **Information Needed:** Departmental equipment availability, operational readiness for upcoming practical courses, budget impact of damaged assets.
- **System Role:** `DEPT_HEAD` (Analytical and approval permissions scoped to their department).
- **Expected Benefits:** Protection against asset loss during staff turnover; reliable equipment readiness data for accreditation.

### 5. Department Laboratory Managers (Chief Technical Assistants)
- **Institutional Role:** Direct custody and stewardship of assigned laboratory rooms; managing student access; coordinating daily maintenance and supplies.
- **Information Provided:** Asset registration requests, fault reports, inter-laboratory transfer initiation, verification of completed repairs.
- **Information Needed:** Live status of submitted maintenance requests, scheduled calibration dates, digital asset passports, and transfer statuses.
- **System Role:** `LAB_MANAGER`
- **Expected Benefits:** Frictionless bench-side management; immediate digital fault reporting; automated alerts for overdue calibrations.

### 6. Laboratory Technicians & Technical Assistants (TAs)
- **Institutional Role:** Conducting practical laboratory sessions; supervising student use; executing daily routine equipment checks and cleanups.
- **Information Provided:** Immediate breakdown notices, symptom descriptions, and daily usage logs.
- **Information Needed:** Operating manuals, equipment operational status, safety instructions.
- **System Role:** `LAB_TECH`
- **Expected Benefits:** Instant fault logging by scanning physical QR codes on equipment; no paperwork or travel to Office 34 required to report broken instruments.

### 7. Central Laboratories Unit Personnel
- **Institutional Role:** Operating the shared high-end analytical instruments (AAS, HPLC, Soxhlet) in the Central Laboratory Building; conducting tests for researchers and external clients.
- **Information Provided:** Instrument availability schedules, equipment utilization rates, analytical service records.
- **Information Needed:** Calibration validity, upcoming maintenance shutdowns, instrument uptime records.
- **System Role:** `LAB_MANAGER` / `LAB_TECH` (Specialized Central Lab Scope).
- **Expected Benefits:** Transparent scheduling and tracking of high-value shared analytical equipment.

### 8. Estate Development & Facilities Management Directorate (EFMD - BMOM)
- **Institutional Role:** Maintaining macro campus infrastructure (central water supply, high-voltage electricity lines, physical building structures).
- **Interface with System:** Receives escalated building-level tickets when an instrument breakdown is determined to be caused by a building utility failure (e.g., total lab water outage or voltage fluctuations).
- **System Role:** No direct write role; receives system notifications or export reports for utility-related work orders.

### 9. University ICT Directorate
- **Institutional Role:** Managing university data centers, network infrastructure, institutional email domains, and enterprise security.
- **Information Provided:** Server infrastructure, network access, domain certificates, institutional directory integration.
- **Information Needed:** Application resource utilization, security audit logs, backup completion logs.
- **System Role:** `SYSTEM_ADMIN` (Server, infrastructure, and database administrative maintenance).
- **Expected Benefits:** Standardized, secure web deployment hosted within university infrastructure.
