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
    1. *Total Assets* and *Operational Assets:* Current inventory total and count in `OPERATIONAL` status.
    2. *Active and Completed Work Orders:* Current active tickets (`OPEN`, `ASSIGNED`, `IN_PROGRESS`) and completed tickets in the selected date range.
    3. *Calibration Counts:* Overdue instruments and instruments due within the caller-supplied horizon.
    4. *Fleet Availability:* A percentage is a design target; calculation awaits approval of denominator, eligible assets, period, and status treatment (DEC-16).
  - **Main Grid (Two Columns):**
    - *Left (Downtime Distribution):* A downtime chart is deferred until the metric definition is approved (DEC-16).
    - *Right (Urgent Action Queue):* Priority list of `CRITICAL` fault tickets and upcoming calibrations for a caller-supplied horizon.
- **States:** Skeleton card loading -> Interactive dashboard -> Empty state with message if no data exists.
- **Stage 8 implementation boundary:** `/dashboard` shows current asset totals and operational counts by category and status, work-order status/completion counts, critical work orders, and overdue/upcoming calibration counts and lists. Users supply the calibration due horizon; DEC-14 remains open and no reminder window is hardcoded. Uptime/downtime values are explicitly unavailable pending DEC-16. No separate asset condition field or preventive-maintenance schedule data exists, so neither is reported.
- **Reports:** `/reports` provides date-filtered maintenance counts grouped by college and a CSV inventory download for authorized roles. CSV is the only implemented export format. Organization selectors are shown only to university-wide report users; scoped users see no organization options, and report filters cannot expand server-enforced scopes.

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
    - *Calibration Status:* Current due date and overdue warning; calibration history is shown on `/calibrations`.
    - *Tab 5: Custody Transfer Trail:* Historical log of all movements between laboratories.
  - **Contextual Actions:** "Report Fault", "Initiate Transfer", and "View Calibration Tracking" where applicable.

#### Stage 4 implementation scope
- `/assets` is available to authenticated users and provides a debounced search, college/department/laboratory/category/status filters, sorting, pagination, and a camera-based QR scanner. The delivered table shows the approved asset code, model, manufacturer, category, current location, and operational status.
- The approved data dictionary does not define an `asset_name` field; the current UI therefore identifies equipment by model number and manufacturer. It does not invent a free-text equipment-name attribute.
- `ULMD_ADMIN` and the designated manager of the selected laboratory can register assets. The form accepts only approved asset fields, assigns the asset code on the server, and starts the asset in `OPERATIONAL`. Editing does not expose the asset code, status, or location.
- The passport shows the approved identity, category/calibration defaults, current college/department/laboratory/room, recorded purchase/commissioning/warranty/calibration dates, and a generated SVG QR label.
- Calibration history is presented on the dedicated `/calibrations` page; the passport displays the current due date and computed overdue banner. Maintenance history/actions remain on the `/maintenance` page. Custody transfer history and actions are implemented in Stage 5 as described below.
- QR labels contain the universal asset code while `ASSET_PUBLIC_BASE_URL` is unset. Once the deployment owner confirms the public frontend origin, this optional setting makes new QR labels link to `/assets/scan?code=...`; that protected route resolves and opens the asset passport. The camera scanner accepts both URL and code-only payloads. The QR image endpoint and lookup API remain authenticated. No production origin is currently configured.
- Category create/update/delete endpoints and the management-page visibility are currently restricted to `ULMD_ADMIN`. This is a provisional least-privilege implementation because the approved role matrix does not define category administration; stakeholder confirmation is required. The category schema has no active/inactive field, and deletion is blocked when assets reference a category.

---

### Screen 4: Maintenance Work Orders & Dispatch Board (`/maintenance`)
- **Target Roles:** `LAB_TECH`, `LAB_MANAGER`, `MAINTENANCE_TECH`, `ULMD_ADMIN`, `AUDITOR` (read-only); users in explicitly configured existing approver roles can review relevant pending requests.
- **Layout Structure:**
  - **Report Fault Form:** Asset code, severity, failure category, and symptom description. The form resolves the code to an asset before submission. The asset passport provides a direct link that pre-fills its asset code.
  - **Work Order Queue:** Paginated cards include ticket/asset identifiers, model, manufacturer, laboratory, reporter, assigned technician, failure category, severity, description, status, status history, and repair log history. A status selector filters the queue.
  - **Assignment:** `ULMD_ADMIN` selects an active Maintenance Technician for an `OPEN` order.
  - **Technician Workflow:** The assigned Maintenance Technician starts work, can mark an in-progress order `AWAITING_PARTS`, resumes it as `IN_PROGRESS`, and submits actions, parts used, labor hours, and outcome. Submission moves the order to `RESOLVED`.
  - **Verification:** The custodian Lab Manager or `ULMD_ADMIN` records verification notes and either closes a successful `OPERATIONAL` repair or rejects the repair back to `IN_PROGRESS`.
  - **Role Restrictions:** The interface reflects server-side scopes. `AUDITOR` is read-only; technicians see their assigned orders, Lab Managers their own laboratories, and Lab Technicians their departments. ULMD Admin can assign and, as allowed by the role matrix, submit an activity for an assigned work order.

#### Stage 6 implementation scope and unresolved decisions
- `/maintenance` is the implemented route; fault reporting is embedded in the queue, not a separate `/maintenance/report` route. Ticket detail, audit-backed status history, and repair logs are shown on each queue card; there is no separate `/maintenance/:id` route.
- The database and API support `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `AWAITING_PARTS`, `AWAITING_APPROVAL`, `RESOLVED`, and `CLOSED`. The assigned Maintenance Technician can submit free-text external-parts request details from `IN_PROGRESS` or `AWAITING_PARTS`. The queue displays the requester, request details, decision, actor, time, optional notes, and audit-backed history.
- Request and approve/reject controls are disabled when no role is configured. Approver roles come only from the optional `MAINTENANCE_APPROVER_ROLES` setting, which is empty by default; no approver role is presumed. Decision controls are shown only when the API confirms the current user is configured and is not the requester. Approval restores the previous status. Rejection remains blocked in `AWAITING_APPROVAL` while post-rejection policy awaits stakeholder confirmation.
- A confirmed close requires the latest maintenance outcome to be `OPERATIONAL`. The policy for closing `REPAIRED_DEGRADED` or `UNREPAIRABLE` outcomes is unresolved; the UI explains that limitation and the API returns `409 Conflict` for a confirmed close.
- There is no procurement, quote attachment, cost/threshold field, separate local routine-maintenance path (DEC-03), outbound notification, or calibration workflow in Stage 6.

---

### Screen 5: Inter-Laboratory Custody Transfer Portal (`/transfers`)
- **Target Roles:** `LAB_MANAGER`, `ULMD_ADMIN`, `AUDITOR` (read-only).
- **Layout Structure:**
  - **Transfer Queue:** A paginated list with a status filter, showing outgoing and incoming custody transfers visible to the current role.
  - **Transfer Initiation Form:**
    - Asset code input resolved against the asset register; the server permits initiation only for an `OPERATIONAL` asset.
    - Destination Laboratory and Room dropdowns; the server validates that the room belongs to that laboratory and that a designated active Lab Manager exists.
    - Justification text area.
  - **Transfer History:** Shows origin and destination laboratory/room, initiating actor, reason, current status, and timestamped audit-backed status events.
  - **Decision Actions:** Authorized users can accept receipt, reject an active transfer with a required note, or approve final relocation as ULMD.
  - **Role Restrictions:** `AUDITOR` can view transfer history and status only; initiation, acceptance, rejection, and approval controls are hidden.

#### Stage 5 implementation scope
- `/transfers` is implemented as one paginated, status-filtered queue with an initiation form. The API scopes Lab Manager reads to transfers involving laboratories they currently manage; the UI is available to `ULMD_ADMIN`, `LAB_MANAGER`, and read-only `AUDITOR`.
- Transfer state is displayed from immutable audit snapshots. Initiation preserves the asset's origin location and marks it `TRANSFER_PENDING`; only final ULMD approval changes its current laboratory/room. Rejection returns the asset to `OPERATIONAL` at its origin.
- Asset passports display the recorded source/destination locations and transition history for roles permitted to read transfers. No assignment table or location exception was added.

  ---

  ### Screen 6: User Provisioning (`/admin/users`)
  - **Target Role:** `ULMD_ADMIN` only; the API independently enforces this restriction.
  - **Layout:** Account creation/edit form and a paginated table showing full name, institutional email, canonical role, department assignment, and active status.
  - **Actions:** Provision an account with an initial password; edit profile, role, or department; activate/deactivate an account. There is no hard-delete action. The last active `ULMD_ADMIN` cannot be demoted or deactivated.
  - **Role Assignment:** The role selector contains only `ULMD_ADMIN`, `MAINTENANCE_TECH`, `LAB_MANAGER`, `LAB_TECH`, and `AUDITOR`. `LAB_MANAGER` and `LAB_TECH` require an existing department. Passwords must be at least 10 characters with a letter and digit.
  - **States:** Loading, empty, success confirmation, and validation/API error states are shown explicitly. Password values and hashes are never shown in the account table.

### Screen 7: Organizational Structure (`/admin/hierarchy`)
- **Target Role:** `ULMD_ADMIN` only; read and write APIs enforce the approved role policy independently.
- **Layout:** Four entity tabs for Colleges, Departments, Laboratories, and Rooms. Each tab has a create/edit form and searchable, paginated record table.
- **Relationships:** Department forms select a college; laboratory forms select a department and may select an existing user as designated manager; room forms select a laboratory. Physical locations are represented by rooms in laboratories, not a separate entity.
- **Laboratory Fields:** Name, approved type (`WET`, `DRY`, `COMPUTING`, `WORKSHOP`), department, and optional designated manager.
- **Room Fields:** Room number and building name, scoped to a laboratory.
- **Filters:** Departments by college, laboratories by department, and rooms by laboratory. Search fields follow the relevant entity identifiers and names.
- **Actions and States:** Create, edit, and confirmed delete actions display success notices, validation/API errors, and loading/empty states. Database-referenced records cannot be deleted and show the API conflict message; there is no soft-delete field in the approved schema.

### Screen 8: Calibration Tracking (`/calibrations`)
- **Target Roles:** All authenticated roles may view the due list; `ULMD_ADMIN`, `MAINTENANCE_TECH`, and `AUDITOR` may view calibration history; `ULMD_ADMIN` and `MAINTENANCE_TECH` may record a calibration.
- **Due List:** The user supplies a whole-number `within_days` horizon. A paginated table shows asset, laboratory/room, last calibration date, next due date, and computed `UPCOMING` or `OVERDUE` status. No default horizon or reminder is assumed.
- **Record Form:** Asset code, calibration date, standard used, optional certificate reference/accreditation body, pass/fail result, and optional notes. The API calculates next due from the category's default calibration interval; certificate file upload is not supported.
- **History:** A read-only paginated list shows calibration date, asset, technician, standard, result, and calculated next due date. There are no edit or delete actions.
- **Passport and Inventory Indicators:** Assets with an expired calibration due date show an overdue banner on the passport and badge in the inventory list.
- **States:** Loading, empty, API/validation error, and save confirmation states are explicit.
- **Boundary:** Failed calibration does not automatically alter operational status or create a work order. Preventive-maintenance schedules, background jobs, reminders, and notification delivery are not implemented pending stakeholder decisions.
