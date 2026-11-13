# Screen Design Specification

This document details the layout, data elements, user interactions, and visual states for the primary screens of the Laboratory Asset Management and Maintenance Tracking System.

---

## 1. Screen Catalog

### Screen 0: Sign-In (`/login`)
- **Target Roles:** All five canonical roles; public route before authentication.
- **Layout:** University/system identity, institutional email input, password input, and one primary sign-in action. No self-registration or password-reset link is exposed in this stage.
- **Behavior:** Submits form-encoded credentials; successful sign-in stores the short-lived access token in memory and keeps the refresh token in an HttpOnly cookie. Failed credentials use a generic message; inactive-account and rate-limit responses receive actionable messages.
- **Navigation:** Successful sign-in returns the user to the originally requested protected route when it is a local application path, otherwise to `/dashboard`.

### Screen 1: Executive & Operational Dashboard (`/dashboard`)
- **Target Roles:** `ULMD_ADMIN`, `AUDITOR` (department-scoped where applicable), `LAB_MANAGER`.
- **Layout Structure:**
  - **Top Row (Metrics Cards):**
    1. *Total Active Assets:* Count of equipment in `OPERATIONAL` status.
    2. *Active Work Orders:* Count of open tickets (`OPEN`, `ASSIGNED`, `IN_PROGRESS`).
    3. *Overdue Calibrations:* Count of instruments with expired calibration deadlines.
    4. *Fleet Availability:* Percentage of equipment operational across the university.
  - **Main Grid (Two Columns):**
    - *Left (Downtime Distribution):* Bar chart displaying open work orders grouped by college (HiT, CAES, CHMS, CCI, CVM, CNCS).
    - *Right (Urgent Action Queue):* Priority list of `CRITICAL` fault tickets and upcoming calibrations due within 7 days.
- **States:** Skeleton card loading -> Interactive dashboard -> Empty state with message if no data exists.

---

### Screen 2: Asset Inventory & Bench Lookup (`/assets`)
- **Target Roles:** All Authenticated Users.
- **Layout Structure:**
  - **Header Bar:** Page title, count badge, "Register Asset" button (for Lab Managers/Admins), and a prominent "Scan QR Code" button.
  - **Filter Toolbar:**
    - Live search input (debounced by 300 ms) searching across asset codes, model names, and manufacturers.
    - College & Department dropdown filters.
    - Operational status filter buttons (`ALL`, `OPERATIONAL`, `UNDER_MAINTENANCE`, `DEFECTIVE`).
  - **Data Table:**
    - Columns: QR Thumbnail, Asset Code, Equipment Name/Model, Manufacturer, Assigned Laboratory & Room, Condition Badge, Calibration Status, Action Menu ("View Passport", "Report Fault", "Transfer").
  - **Pagination Controls:** Showing 1-20 of 142 items with previous/next and page jump controls.
- **Bench-Side QR Scanner Modal:** Clicking "Scan QR Code" opens a camera overlay powered by `html5-qrcode`. Pointing the device at an asset label automatically decodes the code and navigates to the Asset Passport in < 200 ms.

---

### Screen 3: Digital Asset Passport (`/assets/:id`)
- **Target Roles:** All Authenticated Users.
- **Layout Structure:**
  - **Top Hero Card:**
    - Large asset title, model number, unique `asset_code`, and vector QR code thumbnail with "Print Label" button.
    - Status Pill (`OPERATIONAL` in green, `UNDER_MAINTENANCE` in amber, `DEFECTIVE` in red).
    - Calibration Status Banner (displays green checkmark if valid; red warning banner if overdue).
  - **Tabbed Information View:**
    - *Tab 1: Technical Specifications:* Manufacturer, serial number, purchase date, commissioning date, warranty expiration date.
    - *Tab 2: Location & Custody:* College, department, laboratory room, assigned custodian manager.
    - *Tab 3: Maintenance Logbook:* Chronological list of all past work orders, actions taken, spare parts used, labor hours, and servicing technicians.
    - *Tab 4: Calibration Records:* History of certified calibration dates, standards used, and certificates.
    - *Tab 5: Custody Transfer Trail:* Historical log of all movements between laboratories.
  - **Floating Action Bar:** Contextual actions: "Report Fault", "Initiate Transfer", "Schedule Calibration".

---

### Screen 4: Maintenance Work Orders & Dispatch Board (`/maintenance`)
- **Target Roles:** `LAB_TECH`, `LAB_MANAGER`, `MAINTENANCE_TECH`, `ULMD_ADMIN`, `AUDITOR` (read-only).
- **Layout Structure:**
  - **Status Filter Tabs:** `All`, `Open`, `Assigned`, `In Progress`, `Awaiting Parts`, `Resolved`, `Closed`.
  - **Work Order Table / Kanban Card View:**
    - Ticket Number (`WO-2026-0142`), Asset Code, Severity Badge (`CRITICAL` in high-contrast red), Reporting Lab, Time Elapsed since submission.
  - **Action Modals:**
    - *Assign Modal (ULMD Admin):* Dropdown list of Technology Unit technicians with active workload indicators.
    - *Service Log Modal (Technician):* Multi-line input for actions taken, spare parts replaced, labor hours expended, and outcome condition selector.
    - *Verification Sign-Off Modal (Lab Manager):* Confirmation checkbox and comment field to verify that the repaired instrument operates properly before closing the ticket.
  - **Role Restrictions:** `AUDITOR` can view work-order data only; all assignment, logging, and verification controls are hidden.

---

### Screen 5: Inter-Laboratory Custody Transfer Portal (`/transfers`)
- **Target Roles:** `LAB_MANAGER`, `ULMD_ADMIN`, `AUDITOR` (read-only).
- **Layout Structure:**
  - **Two Tab Views:** (1) "Outgoing Transfers", (2) "Incoming Transfers Awaiting Acceptance".
  - **Transfer Initiation Form:**
    - Asset Code selector (only allows selecting assets in `OPERATIONAL` condition).
    - Destination Laboratory dropdown.
    - Justification text area.
  - **Multi-Step Status Stepper:**
    - Step 1: *Initiated by Origin Lab* (Completed).
    - Step 2: *Inspected & Accepted by Destination Lab* (Pending/Completed).
    - Step 3: *Approved by ULMD Directorate* (Pending/Completed).
  - **Role Restrictions:** `AUDITOR` can view transfer history and status only; initiation, acceptance, rejection, and approval controls are hidden.

  ---

  ### Screen 6: User Provisioning (`/admin/users`)
  - **Target Role:** `ULMD_ADMIN` only; the API independently enforces this restriction.
  - **Layout:** Account creation/edit form and a paginated table showing full name, institutional email, canonical role, department assignment, and active status.
  - **Actions:** Provision an account with an initial password; edit profile, role, or department; activate/deactivate an account. There is no hard-delete action. The last active `ULMD_ADMIN` cannot be demoted or deactivated.
  - **Role Assignment:** The role selector contains only `ULMD_ADMIN`, `MAINTENANCE_TECH`, `LAB_MANAGER`, `LAB_TECH`, and `AUDITOR`. `LAB_MANAGER` and `LAB_TECH` require an existing department. Passwords must be at least 10 characters with a letter and digit.
  - **States:** Loading, empty, success confirmation, and validation/API error states are shown explicitly. Password values and hashes are never shown in the account table.
