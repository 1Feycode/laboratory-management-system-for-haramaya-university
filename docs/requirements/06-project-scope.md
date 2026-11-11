# 06. Project Scope and MoSCoW Prioritization

This document defines the functional boundaries of the Laboratory Asset Management and Maintenance Tracking System for Haramaya University. It applies the MoSCoW prioritization framework to delineate essential features for the Release 1 Minimum Viable Product (MVP) from subsequent iterations, while explicitly excluding out-of-scope enterprise modules.

---

## 1. System Boundary and Functional Decomposition

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CORE SYSTEM BOUNDARY                            │
│                                                                        │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌────────────┐   │
│   │ Asset Registration  │   │ Maintenance & Work  │   │ Location & │   │
│   │   & QR Lifecycle    │──▶│   Order Tracking    │◀──│ Transfers  │   │
│   └─────────────────────┘   └─────────────────────┘   └────────────┘   │
│              │                         │                     │         │
│              ▼                         ▼                     ▼         │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │         Role-Based Access, Auditing & Executive Reports        │   │
│   └────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ EXCLUDED
                                    ▼
       [Clinical Patient Records] [Full University ERP / Finance]
       [Chemical Reagent Consumption Tracking] [Direct Vendor Procurement]
```

---

## 2. MoSCoW Prioritization

### Must Have (Essential for Release 1 - MVP)
These features represent the absolute baseline required to solve the primary operational bottlenecks at Haramaya University.

1. **Multi-Tier Institutional Hierarchy:** Managing University -> College -> Department -> Laboratory -> Room boundaries.
2. **Standardized Asset Registration (WHO LQSI Compliant):** Asset code, serial number, model, manufacturer, category, commissioning date, custodian laboratory, room, and operational condition.
3. **Unique QR Code Identification:** Generating unique vector QR codes encoding asset identity; mobile camera scanning hook for instant bench-side lookup.
4. **Equipment Fault Reporting & Ticketing:** Technicians report defects with severity; system generates unique work orders (`WO-YYYY-XXXX`) and notifies the ULMD Technology Unit.
5. **Work Order Dispatch & Resolution Tracking:** Assigning maintenance engineers; logging diagnostic actions, spare parts used, labor hours, and outcome conditions; custodian sign-off.
6. **Calibration Tracking:** Logging calibration dates, standards used, pass/fail status, and automated calculation of next due date.
7. **Dual-Authorization Custody Transfers:** Formal workflow requiring origin Lab Manager initiation, destination Lab Manager acceptance, and ULMD confirmation.
8. **Role-Based Access Control (RBAC):** Server-side permission guards for `ULMD_ADMIN`, `MAINTENANCE_TECH`, `LAB_MANAGER`, `LAB_TECH`, and `AUDITOR`.
9. **Immutable Audit Trail:** Append-only recording of all asset mutations, location updates, and maintenance closures.

### Should Have (Important but Secondary - Release 2)
1. **Automated Preventive Maintenance Alerts:** System notifications triggered 30, 15, and 7 days prior to scheduled calibration deadlines.
2. **Executive Analytical Dashboard:** Aggregated uptime/downtime percentages per college, open work order distributions, and overdue calibration widgets.
3. **Service Manual & Document Attachments:** Uploading user manuals, calibration certificates, and equipment photos (PDF/JPEG) to the asset passport.
4. **Bulk CSV/Excel Asset Import:** Staging validation tool to import legacy department spreadsheets into the database.

### Could Have (Future Enhancements)
1. **Consumable Chemicals Module:** Basic inventory tracking for chemical reagents and culture media (strictly separated from durable machinery).
2. **Central Analytical Service Billing:** Recording labor and service fees for research and external testing at Central Laboratories.
3. **Offline Mobile PWA:** Offline caching of scanned asset passports for basement wet labs with intermittent Wi-Fi connectivity.

### Won’t Have (Strictly Out of Scope)
To ensure technical feasibility, maintain architectural focus, and prevent scope creep:
1. **Clinical / Medical Diagnosis Management:** No patient electronic health records (EHR) or clinical diagnosis results.
2. **Direct Financial Procurement & Accounting:** No vendor purchase order generation, bidding systems, or general ledger accounting.
3. **Full Laboratory Information Management System (LIMS):** No sample tracking, experimental test result logging, or laboratory scientific protocol execution.
4. **Student Academic Records:** No grading, course enrollment, or student record management.
