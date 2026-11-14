# REST API Specification (OpenAPI Details)

This document provides complete request and response schemas, parameters, and error formats for the primary endpoints of the Laboratory Asset Management and Maintenance Tracking System (`/api/v1`).

---

## 1. Authentication Endpoints

### 1.1 `POST /api/v1/auth/login`
- **Description:** Authenticates user credentials and issues JWT tokens.
- **Security:** Public.
- **Request (Form URL-Encoded):**
  - `username` (string, required): User institutional email.
  - `password` (string, required): Plaintext password.
- **Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "e44d5162-8e10-41ff-8c10-09252c442e91",
      "email": "dr.meseret@haramaya.edu.et",
      "full_name": "Dr. Meseret Girma",
      "role": "ULMD_ADMIN",
      "department_id": null,
      "is_active": true,
      "created_at": "2026-11-13T10:00:00Z"
    }
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Invalid email or password, including locked or inactive accounts. The response is intentionally indistinguishable to avoid account enumeration.

---

### 1.2 `POST /api/v1/auth/refresh`
- **Description:** Rotates the refresh token and issues a new access token.
- **Security:** Refresh token in the `RefreshToken` HttpOnly cookie.
- **Request:** No body. The browser sends the cookie with credentials enabled.
- **Response (`200 OK`):** The login access-token and profile envelope; a replacement refresh cookie is set.
- **Errors:** `401 Unauthorized` for a missing, invalid, expired, inactive-user, or previously used refresh token; `429 Too Many Requests` when rate limited.

### 1.3 `POST /api/v1/auth/logout`
- **Description:** Revokes the supplied refresh token when valid and clears the refresh cookie.
- **Security:** Refresh cookie optional, so logout remains available after access-token expiry.
- **Response:** `204 No Content`; repeated logout requests are safe.

### 1.4 `GET /api/v1/auth/me`
- **Description:** Returns the currently authenticated active user.
- **Security:** Bearer access token.
- **Response (`200 OK`):**
  ```json
  {
    "id": "e44d5162-8e10-41ff-8c10-09252c442e91",
    "email": "dr.meseret@haramaya.edu.et",
    "full_name": "Dr. Meseret Girma",
    "role": "ULMD_ADMIN",
    "department_id": null,
    "is_active": true,
    "created_at": "2026-11-13T10:00:00Z"
  }
  ```
- **Errors:** `401 Unauthorized` for missing, invalid, expired, or inactive-user access.

### 1.5 User Management Endpoints
All user-management endpoints require the `ULMD_ADMIN` role. Public self-registration is not provided.

#### `GET /api/v1/users`
- **Description:** Returns paginated accounts; supports `page`, `size` (maximum 100), `role`, and `department_id`.
- **Response:** Standard page envelope with safe user profiles. Password hashes and login-lockout fields are never returned.

#### `GET /api/v1/users/departments`
- **Description:** Lists existing department IDs, names, and codes for assigning a scoped account.
- **Response:** JSON array; an empty array is valid until hierarchy records are added.

#### `GET /api/v1/users/{id}`
- **Description:** Retrieves a safe user profile.
- **Errors:** `404 Not Found` when the account does not exist.

#### `POST /api/v1/users`
- **Description:** Provisions a local account. Only the five canonical roles are accepted.
- **Request (`application/json`):**
  ```json
  {
    "email": "lab.manager@haramaya.edu.et",
    "full_name": "Laboratory Manager",
    "password": "InitialPass123",
    "role": "LAB_MANAGER",
    "department_id": "d027f6e7-c62d-4d7a-8fbb-5481d9f8ce32"
  }
  ```
- **Response:** `201 Created` with a safe profile; the password is immediately bcrypt-hashed and never returned.
- **Errors:** `409 Conflict` for duplicate email; `422 Unprocessable Entity` for invalid fields, an unknown department, or a missing department for `LAB_MANAGER` / `LAB_TECH`.

#### `PATCH /api/v1/users/{id}`
- **Description:** Updates `email`, `full_name`, `role`, `department_id`, and/or `is_active`.
- **Request:** Partial JSON object containing at least one supported field. Password updates are not part of this endpoint.
- **Errors:** `404 Not Found`; `409 Conflict` for duplicate email or attempting to demote/deactivate the last active `ULMD_ADMIN`; `422 Unprocessable Entity` for invalid assignments.

## 2. Organizational Hierarchy and Locations

The approved location structure is `College -> Department -> Laboratory -> Room`. There is no separate `Location` entity or table; a physical location is represented by its room and parent hierarchy. All hierarchy reads require an authenticated user. All mutations require `ULMD_ADMIN`, matching FR-002 and the approved role matrix.

List endpoints accept `page` (default `1`), `size` (default `20`, maximum `100`), and `search` (maximum 100 characters), and return `{ "items": [], "total": 0, "page": 1, "size": 20, "pages": 0 }`.

| Entity | List/search and filters | Create | Retrieve | Update | Delete |
|---|---|---|---|---|---|
| Colleges | `GET /api/v1/hierarchy/colleges`; search name/code | `POST /api/v1/hierarchy/colleges` | `GET /api/v1/hierarchy/colleges/{id}` | `PATCH /api/v1/hierarchy/colleges/{id}` | `DELETE /api/v1/hierarchy/colleges/{id}` |
| Departments | `GET /api/v1/hierarchy/departments`; filter `college_id`, search name/code | `POST /api/v1/hierarchy/departments` | `GET /api/v1/hierarchy/departments/{id}` | `PATCH /api/v1/hierarchy/departments/{id}` | `DELETE /api/v1/hierarchy/departments/{id}` |
| Laboratories | `GET /api/v1/hierarchy/laboratories`; filter `department_id` and `lab_type`, search name | `POST /api/v1/hierarchy/laboratories` | `GET /api/v1/hierarchy/laboratories/{id}` | `PATCH /api/v1/hierarchy/laboratories/{id}` | `DELETE /api/v1/hierarchy/laboratories/{id}` |
| Rooms | `GET /api/v1/hierarchy/rooms`; filter `laboratory_id`, search room number/building | `POST /api/v1/hierarchy/rooms` | `GET /api/v1/hierarchy/rooms/{id}` | `PATCH /api/v1/hierarchy/rooms/{id}` | `DELETE /api/v1/hierarchy/rooms/{id}` |

### College request
```json
{ "name": "Haramaya Institute of Technology", "code": "HiT" }
```
College name and code are each unique.

### Department request
```json
{
  "college_id": "d027f6e7-c62d-4d7a-8fbb-5481d9f8ce32",
  "name": "Chemical Engineering",
  "code": "CHEM"
}
```
The college must exist. Department codes are unique within a college.

### Laboratory request
```json
{
  "department_id": "d027f6e7-c62d-4d7a-8fbb-5481d9f8ce32",
  "name": "Analytical Laboratory",
  "lab_type": "WET",
  "manager_id": null
}
```
`lab_type` must be one of `WET`, `DRY`, `COMPUTING`, or `WORKSHOP`. The department must exist; a non-null manager must reference an existing user. The approved schema does not constrain the manager's role or department.

### Room request
```json
{
  "laboratory_id": "e44d5162-8e10-41ff-8c10-09252c442e91",
  "room_number": "B-14",
  "building_name": "Central Laboratory Building"
}
```
The laboratory must exist. A room number is unique within its laboratory.

Successful creates return `201 Created`; reads and updates return `200 OK`; successful deletes return `204 No Content`. Duplicate unique values return `409 Conflict`; missing parent references return `422 Unprocessable Entity`; missing records return `404 Not Found`. Deletion is physical only where permitted by the approved foreign keys. A college with departments, department with laboratories, or laboratory with rooms cannot be deleted (`409 Conflict`). Stage 4 blocks hierarchy changes that would invalidate registered asset codes or locations; Stage 5 also blocks laboratory/room parent reassignment when transfer history references those records. Asset location changes are performed through the custody-transfer workflow below. The approved `users.department_id ON DELETE SET NULL` action means deleting a department clears that assignment; see the unresolved consistency note in the implementation progress report.

## 3. Asset Management Endpoints

All asset reads require an authenticated user. `ULMD_ADMIN` has university-wide write access. A `LAB_MANAGER` may create or update metadata only for a laboratory assigned to that user (`laboratories.manager_id`) and within the manager's department. The server independently checks these scopes.

Asset codes are generated in the approved format `HU-{COLLEGE_CODE}-{DEPT_CODE}-{4_DIGIT_SEQ}`. Registration locks the department while assigning the next sequence; values beyond `9999` return `409 Conflict` and require a stakeholder-approved format change. The initial `operational_status` is `OPERATIONAL`.

### 3.1 `GET /api/v1/asset-categories`
- **Security:** Authenticated.
- **Query parameters:** `page` (default `1`), `size` (default `100`, maximum `100`), and optional `search` (category name).
- **Response:** Standard page envelope with category `id`, `name`, `requires_calibration`, `default_calibration_interval_days`, and `created_at`.

### 3.2 Category administration
Category fields are the approved `asset_categories` data-dictionary fields. No default categories are seeded.

| Method | Endpoint | Access | Behavior |
|---|---|---|---|
| `POST` | `/api/v1/asset-categories` | `ULMD_ADMIN` | Create a category. Request: `{ "name": "Spectrophotometer", "requires_calibration": true, "default_calibration_interval_days": 180 }`. |
| `GET` | `/api/v1/asset-categories/{category_id}` | Authenticated | Retrieve category details. |
| `PATCH` | `/api/v1/asset-categories/{category_id}` | `ULMD_ADMIN` | Update one or more category fields. |
| `DELETE` | `/api/v1/asset-categories/{category_id}` | `ULMD_ADMIN` | Delete only if no assets reference the category; otherwise returns `409 Conflict`. |

Category reads support asset registration. The approved role matrix does not define category mutation permissions or an active/inactive category lifecycle. The `ULMD_ADMIN`-only create/update/delete guards and admin-only UI visibility are the current provisional restriction, not an approved policy; confirm the authorized role and whether deactivation is required with ULMD. The schema has no activation field, deletion is restricted when assets reference a category, and no default categories are seeded.

### 3.3 `GET /api/v1/assets`
- **Security:** Authenticated; all canonical roles have read access.
- **Query parameters:** `page` (default `1`), `size` (default `20`, maximum `100`), optional `search` (asset code, legacy tag, serial, model, or manufacturer), `college_id`, `department_id`, `laboratory_id`, `category_id`, and `status`.
- **Sorting:** `sort_by` is one of `asset_code`, `created_at`, `model_number`, `operational_status`, or `purchase_date`; `sort_order` is `asc` or `desc`.
- **Response:** Standard page envelope containing asset records.

### 3.4 `POST /api/v1/assets`
- **Security:** `ULMD_ADMIN`, or the designated `LAB_MANAGER` for the selected laboratory.
- **Request (`application/json`):**
  ```json
  {
    "legacy_tag_number": "OLD-CHEM-014",
    "serial_number": "UV1900-SN84729",
    "model_number": "UV-1900i Double-Beam",
    "manufacturer_name": "Shimadzu",
    "category_id": "8c593672-887e-405e-85a2-f852e92c21aa",
    "laboratory_id": "e44d5162-8e10-41ff-8c10-09252c442e91",
    "room_id": "d027f6e7-c62d-4d7a-8fbb-5481d9f8ce32",
    "purchase_date": "2025-09-15",
    "commissioning_date": "2025-10-01",
    "warranty_expiry_date": "2027-10-01"
  }
  ```
  `legacy_tag_number` and dates are nullable/optional. `room_id` must reference a room within the selected `laboratory_id`. Asset code, operational status, calibration-history dates, and QR path are not client-editable at registration.
- **Response (`201 Created`):**
  ```json
  {
    "id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "asset_code": "HU-HiT-CHEM-0014",
    "legacy_tag_number": "OLD-CHEM-014",
    "serial_number": "UV1900-SN84729",
    "model_number": "UV-1900i Double-Beam",
    "manufacturer_name": "Shimadzu",
    "category_id": "8c593672-887e-405e-85a2-f852e92c21aa",
    "category_name": "Spectrophotometer",
    "requires_calibration": true,
    "default_calibration_interval_days": 180,
    "laboratory_id": "e44d5162-8e10-41ff-8c10-09252c442e91",
    "laboratory_name": "Analytical Spectroscopy Lab",
    "room_id": "d027f6e7-c62d-4d7a-8fbb-5481d9f8ce32",
    "room_number": "B-08",
    "building_name": "Central Laboratory Building",
    "department_id": "e5b3e693-8971-4a2d-b6d1-82bba05afe33",
    "department_name": "Chemical Engineering",
    "college_id": "8f084fb2-1113-4ba5-8462-d1fdd85c08e5",
    "college_name": "Haramaya Institute of Technology",
    "operational_status": "OPERATIONAL",
    "purchase_date": "2025-09-15",
    "commissioning_date": "2025-10-01",
    "warranty_expiry_date": "2027-10-01",
    "last_calibrated_date": null,
    "next_calibration_due": null,
    "calibration_overdue": false,
    "qr_code_url": "/api/v1/assets/b182fb5a-5ffb-46d5-bb90-07e4d82531cd/qr",
    "created_at": "2026-11-13T14:35:10Z",
    "updated_at": "2026-11-13T14:35:10Z"
  }
  ```
- **Errors:** `401` unauthenticated; `403` role/laboratory-scope failure; `409` duplicate manufacturer/serial, category name, or exhausted asset-code sequence; `422` invalid fields, missing references, or room/laboratory mismatch.

### 3.5 `GET /api/v1/assets/{asset_id}`
Returns the asset passport using the response schema above. Returns `404 Not Found` for an unknown asset.

### 3.6 `PATCH /api/v1/assets/{asset_id}`
Requires `ULMD_ADMIN` or the designated manager for the asset's laboratory. Accepts one or more of `legacy_tag_number`, `serial_number`, `model_number`, `manufacturer_name`, `category_id`, `purchase_date`, `commissioning_date`, and `warranty_expiry_date`. Nullable tag/date fields may be cleared explicitly. `asset_code`, current location, and `operational_status` cannot be changed through this endpoint; approved transfer and maintenance workflows own custody/status transitions. Each committed change writes an old/new JSONB snapshot to `audit_logs`.

Duplicate serial pairs return `409`, including when the existing asset is `DECOMMISSIONED`; the unconditional unique constraint remains in force under DEC-06. Missing assets return `404`; invalid categories return `422`. There is deliberately no asset `DELETE` or decommissioning endpoint: BR-010 requires condemnation evidence, but the approved schema and requirements do not define its field, format, document relationship, issuer, or approval evidence.

### 3.7 QR code and lookup

| Method | Endpoint | Security | Behavior |
|---|---|---|---|
| `GET` | `/api/v1/assets/{asset_id}/qr` | Authenticated | Returns an SVG QR image (`image/svg+xml`) containing an asset code, or a configured public passport URL with the code in its query string. |
| `GET` | `/api/v1/assets/lookup/{asset_code}` | Authenticated | Looks up the universal asset code or, when no exact code exists, a legacy tag. |

An exact universal code takes precedence. Legacy tags are intentionally non-unique; no match returns `404`, while multiple matches return `409` and require the universal asset code. When the optional `ASSET_PUBLIC_BASE_URL` setting is configured to the confirmed frontend origin (without a path, query, or credentials), the QR payload is `{origin}/assets/scan?code={encoded_asset_code}`. The protected frontend route looks up the code and opens its passport; authentication is still required. The camera scanner accepts both this URL and the legacy code-only payload. If the setting is unset, QR payloads remain code-only. No canonical production origin is currently configured.

### 3.8 Asset and transfer audit behavior
Asset and asset-category mutations write before/after JSONB snapshots in the same transaction as their changes. Stage 5 transfer initiation, receiver acceptance, rejection, and ULMD completion also write transfer-state snapshots; asset status/location changes write corresponding asset snapshots in the same transaction. The PostgreSQL trigger rejects `UPDATE` and `DELETE` on `audit_logs`. The API does not expose a general audit browsing endpoint. The approved `user_id ON DELETE SET NULL` foreign key would conflict with the immutability trigger if physical user deletion is introduced; current user management deactivates accounts instead.

### 3.9 Custody transfer endpoints

Transfers use only the approved `asset_transfers` fields. The table stores the source and destination laboratory/room IDs, actors, status, reason, notes, and timestamps; no separate assignment entity is introduced. Initial location assignment remains part of asset registration and is captured by the `ASSET_CREATED` audit snapshot. Each later transfer transition and its asset-state change is committed atomically with append-only audit snapshots. During an active transfer, the asset retains its origin location and has status `TRANSFER_PENDING`. The current `assets.laboratory_id` and `assets.room_id` change only on ULMD completion.

| Method | Endpoint | Access | Behavior |
|---|---|---|---|
| `GET` | `/api/v1/transfers` | `ULMD_ADMIN`, `LAB_MANAGER`, `AUDITOR` | Paginated history; optional `status` and `asset_id` filters. Lab managers see transfers involving a laboratory for which they are the designated manager; ULMD administrators and auditors can view all. |
| `POST` | `/api/v1/transfers` | `ULMD_ADMIN`, origin `LAB_MANAGER` | Initiate from an `OPERATIONAL` asset and a valid target laboratory/room. A designated active target Lab Manager is required. Sets transfer `PENDING_RECEIVER` and asset `TRANSFER_PENDING`. |
| `GET` | `/api/v1/transfers/{transfer_id}` | `ULMD_ADMIN`, `LAB_MANAGER`, `AUDITOR` | Retrieve a transfer and its chronological status events from `audit_logs`, subject to the same manager scope as the list endpoint. |
| `PUT` | `/api/v1/transfers/{transfer_id}/accept` | `ULMD_ADMIN`, destination `LAB_MANAGER` | Accept a `PENDING_RECEIVER` transfer, recording `accepted_by` and optional notes; moves it to `PENDING_ULMD`. |
| `PUT` | `/api/v1/transfers/{transfer_id}/reject` | `ULMD_ADMIN`, destination `LAB_MANAGER` | Reject an active transfer with required explanatory notes. A destination manager may reject `PENDING_RECEIVER`; only `ULMD_ADMIN` may reject `PENDING_ULMD`. The asset returns to `OPERATIONAL` at its original location. |
| `PUT` | `/api/v1/transfers/{transfer_id}/approve` | `ULMD_ADMIN` | Approve a `PENDING_ULMD` transfer, set the asset's destination laboratory/room and `OPERATIONAL` status, and mark the transfer `COMPLETED`. |

`POST` request:
```json
{
  "asset_id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
  "target_laboratory_id": "e44d5162-8e10-41ff-8c10-09252c442e91",
  "target_room_id": "d027f6e7-c62d-4d7a-8fbb-5481d9f8ce32",
  "transfer_reason": "Move the instrument to support the receiving laboratory"
}
```

The create and decision endpoints return the full transfer representation, including source/destination room details and `status_history`. Query parameters are `page` (default `1`), `size` (default `20`, maximum `100`), optional `status` (`PENDING_RECEIVER`, `PENDING_ULMD`, `COMPLETED`, `REJECTED`), and optional UUID `asset_id`. `POST` returns `201 Created`; reads and successful state transitions return `200 OK`.

The API returns `401` when unauthenticated, `403` for a role or laboratory-scope violation, `404` for an unknown asset/transfer, `409` for an invalid state, non-operational asset, or unassigned/invalid destination manager, and `422` for malformed input or a destination room outside the selected destination laboratory. The service locks affected asset, transfer, laboratory, and room rows while validating and transitioning. Transfer history retains source and destination room identifiers; hierarchy parent reassignment is blocked while transfer records reference the affected laboratory or room.

---

## 4. Maintenance & Work Order Endpoints

The Stage 6 implementation uses the approved `work_orders` and
`maintenance_logs` tables and the existing append-only `audit_logs` table. All
endpoints require a bearer access token. Lab Managers can access only work
orders for laboratories they currently manage; Lab Technicians are limited to
their department; Maintenance Technicians can read and act on tickets assigned
to them. Explicitly configured external-parts approvers can also read relevant
approval requests. ULMD Admins and Auditors have university-wide read access.
The API independently enforces every role and scope rule.

### 4.1 `POST /api/v1/work-orders`
- **Description:** Report a fault and open a work order.
- **Security:** `LAB_TECH` (own department), designated `LAB_MANAGER` (own
  laboratory), or `ULMD_ADMIN`.
- **Request fields:** `asset_id` (UUID), `severity` (`LOW`, `MEDIUM`, `HIGH`,
  `CRITICAL`), `failure_category` (`ELECTRICAL`, `MECHANICAL`, `OPTICAL`,
  `SOFTWARE`, `CONSUMABLE`, `OTHER`), and a non-empty `fault_description`.
- **Request Body (`application/json`):**
  ```json
  {
    "asset_id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "severity": "HIGH",
    "failure_category": "OPTICAL",
    "fault_description": "Deuterium lamp fails ignition test; error code E-04 during optical initialization."
  }
  ```
- The asset must currently be `OPERATIONAL` and have no non-closed work order.
  A critical report changes the asset to `DEFECTIVE`; all other approved
  severities change it to `UNDER_MAINTENANCE`. The asset lock, new work order,
  and immutable audit snapshots commit in one transaction.
- **Response (`201 Created`):** A full work-order resource, including asset and
  laboratory labels, reporter and assignee names, maintenance logs, and
  audit-derived status history.
  ```json
  {
    "id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
    "ticket_number": "WO-2026-0142",
    "asset_id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "asset_code": "HU-HiT-CHEM-0014",
    "asset_model_number": "UV-1900i",
    "asset_manufacturer_name": "Shimadzu",
    "laboratory_id": "f229661e-9af7-4a2d-8be4-bd8f1d467a10",
    "laboratory_name": "Analytical Laboratory",
    "reported_by": "5b2ab257-0a76-4f34-9782-04bc65835e02",
    "reporter_name": "Laboratory Technician",
    "assigned_to": null,
    "assignee_name": null,
    "severity": "HIGH",
    "failure_category": "OPTICAL",
    "status": "OPEN",
    "fault_description": "Deuterium lamp fails ignition test; error code E-04 during optical initialization.",
    "verified_by": null,
    "verifier_name": null,
    "verification_notes": null,
    "created_at": "2026-11-11T14:40:00Z",
    "resolved_at": null,
    "closed_at": null,
    "external_parts_approval": null,
    "approval_actions_configured": false,
    "can_decide_external_parts_approval": false,
    "maintenance_logs": [],
    "status_history": [
      {
        "action": "WORK_ORDER_CREATED",
        "actor_id": "5b2ab257-0a76-4f34-9782-04bc65835e02",
        "actor_name": "Laboratory Technician",
        "old_status": null,
        "new_status": "OPEN",
        "old_assignee_id": null,
        "new_assignee_id": null,
        "notes": null,
        "external_parts_request_details": null,
        "external_parts_decision": null,
        "occurred_at": "2026-11-11T14:40:00Z"
      }
    ]
  }
  ```

### 4.2 Read and filter work orders
- `GET /api/v1/work-orders` accepts `page` (default `1`), `size` (default
  `20`, maximum `100`), and optional `status`, `severity`, and `asset_id`
  filters. It returns the standard page envelope of full work-order resources.
- `GET /api/v1/work-orders/{order_id}` returns one full resource.
- **Read roles:** `ULMD_ADMIN`, `MAINTENANCE_TECH`, `LAB_MANAGER`,
  `LAB_TECH`, and `AUDITOR`, subject to the scopes above.

### 4.3 `PUT /api/v1/work-orders/{order_id}/assign`
- **Security:** `ULMD_ADMIN` only.
- **Request:** `{ "assigned_to": "<active MAINTENANCE_TECH user UUID>" }`.
- Only an `OPEN` order can be assigned. Inactive users and users with any role
  other than `MAINTENANCE_TECH` are rejected with `422`. Successful assignment
  changes the state to `ASSIGNED` and writes an immutable before/after snapshot.

### 4.4 `PUT /api/v1/work-orders/{order_id}/status`
- **Security:** The currently assigned `MAINTENANCE_TECH` only.
- **Request:** `{ "status": "IN_PROGRESS" }` or
  `{ "status": "AWAITING_PARTS" }`.
- Allowed transitions are `ASSIGNED -> IN_PROGRESS`,
  `IN_PROGRESS -> AWAITING_PARTS`, and `AWAITING_PARTS -> IN_PROGRESS`.
  Invalid transitions return `409 Conflict`.

### 4.5 `POST /api/v1/work-orders/{order_id}/external-parts-approval`
- **Description:** Explicitly request approval for external parts while the
  assigned technician is actively repairing or awaiting parts. This endpoint
  does not infer a price threshold or create procurement activity.
- **Security:** The currently assigned `MAINTENANCE_TECH` only.
- **Request Body:** `{ "request_details": "<non-empty free-text details>" }`.
- **Behavior:** Valid only from `IN_PROGRESS` or `AWAITING_PARTS`. The service
  stores the requester's ID and timestamp, saves the previous status, sets the
  approval decision to `PENDING`, and changes the work order to
  `AWAITING_APPROVAL`. The asset's existing operational condition is unchanged.
  The work-order update and immutable audit snapshot commit in one transaction.
- **Response (`200 OK`):** Updated `WorkOrderRead`; its
  `external_parts_approval` object contains request details, requester and
  timestamp, previous status, current decision, and optional decision fields.
  `approval_actions_configured` indicates whether the setting is non-empty;
  `can_decide_external_parts_approval` is computed for the signed-in user.
- **Errors:** `403` if the caller is not the assigned technician; `409` if the
  work order is not in an eligible status; `422` for empty request details;
  `503` if no approver role is configured.

### 4.6 `PUT /api/v1/work-orders/{order_id}/external-parts-approval/decision`
- **Description:** Record an approval or rejection.
- **Security:** Any user whose existing role is explicitly included in
  `MAINTENANCE_APPROVER_ROLES`, except the user who requested the approval.
- **Configuration:** `MAINTENANCE_APPROVER_ROLES` is an optional,
  comma-separated list containing only existing application role names. It is
  empty by default; with no configured role, both approval request and
  decision endpoints return `503`. Configuring multiple roles makes each
  listed role eligible to decide; it does not require multiple approvals.
- **Request Body:**
  ```json
  {
    "decision": "APPROVED",
    "decision_notes": "Optional decision rationale."
  }
  ```
  `decision` is `APPROVED` or `REJECTED`; `decision_notes` may be null or
  omitted.
- **Behavior:** Only a `PENDING` request on an `AWAITING_APPROVAL` work order
  can be decided. Approval records the actor, timestamp, and optional notes,
  then restores the saved previous status (`IN_PROGRESS` or `AWAITING_PARTS`).
  Rejection records the actor, timestamp, and optional notes but leaves the
  order in `AWAITING_APPROVAL`; no post-rejection status or asset disposition
  is inferred. Each decision and its audit snapshot commit atomically.
- **Errors:** `403` for an unconfigured role or self-approval; `409` if no
  pending request exists; `503` if no approver role is configured.

### 4.7 `POST /api/v1/work-orders/{order_id}/logs`
- **Description:** Record a repair activity, resolving the order for custodian
  verification.
- **Security:** The assigned `MAINTENANCE_TECH`, or `ULMD_ADMIN` as allowed by
  the role matrix. In either case, the order must be `IN_PROGRESS` and have an
  assigned technician; the log is linked to that assigned technician.
- **Request Body (`application/json`):**
  ```json
  {
    "actions_taken": "Replaced deuterium lamp assembly; cleaned optical mirrors; executed photometric self-test.",
    "spare_parts_used": "Shimadzu D2 Lamp Part #228-34010-91",
    "labor_hours": 2.50,
    "outcome_condition": "OPERATIONAL"
  }
  ```
- `labor_hours` must be between `0` and `999.99`; `outcome_condition` is
  `OPERATIONAL`, `REPAIRED_DEGRADED`, or `UNREPAIRABLE`. The log, status
  transition to `RESOLVED`, and audit snapshots commit together.
- **Response (`201 Created`):** The updated full `WorkOrderRead` resource,
  including the appended maintenance log. The log item has the following shape:
  ```json
  {
    "id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
    "status": "RESOLVED",
    "maintenance_logs": [
      {
        "id": "7f9a2e1d-4c3b-4a5f-8e9a-1b2c3d4e5f6a",
        "work_order_id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
        "technician_id": "2e9deba2-cade-4d4d-bf20-8db7f7b7a427",
        "technician_name": "Maintenance Technician",
        "actions_taken": "Replaced the lamp and verified the baseline.",
        "spare_parts_used": "Lamp assembly",
        "labor_hours": 2.5,
        "outcome_condition": "OPERATIONAL",
        "created_at": "2026-11-11T16:00:00Z"
      }
    ]
  }
  ```

### 4.8 `PUT /api/v1/work-orders/{order_id}/close`
- **Description:** Verify or reject a resolved repair.
- **Security:** The custodian `LAB_MANAGER` for the asset's laboratory or
  `ULMD_ADMIN`.
- **Request Body (`application/json`):**
  ```json
  {
    "confirmed": true,
    "verification_notes": "Conducted baseline scan on standard reference water sample; absorbance matches calibration curve."
  }
  ```
- With `confirmed: true`, only the latest `OPERATIONAL` outcome may close the
  order; the order becomes `CLOSED` and the asset returns to `OPERATIONAL`.
  `REPAIRED_DEGRADED` and `UNREPAIRABLE` closure policy is unresolved and
  returns `409 Conflict`. With `confirmed: false`, the order returns to
  `IN_PROGRESS` with the verification notes retained.
- The order, asset status, and immutable audit snapshots are committed in one
  transaction. Both outcomes return `200 OK` with the full updated work-order
  resource.

### 4.9 Workflow boundary and errors
- Implemented workflow: `OPEN -> ASSIGNED -> IN_PROGRESS`, optional
  `AWAITING_PARTS -> IN_PROGRESS`, optional request transition to
  `AWAITING_APPROVAL`, then approval restores the prior state. A rejected
  request remains in `AWAITING_APPROVAL` pending stakeholder disposition.
  Repair proceeds to `RESOLVED -> CLOSED` after verification; failed repair
  verification returns the order to `IN_PROGRESS`.
- The request captures free-text details only. Approval trigger thresholds,
  authorized role designation, supporting documentation, multiple-approval
  policy, and rejection/cancellation disposition remain stakeholder decisions.
  No procurement or spending workflow is implemented. See [DEC-02](../design/phase-2-open-decisions.md#dec-02-outcome-external-parts-approval-state).
- The proposed local routine-maintenance workflow (DEC-03) is not implemented.
  Fault reports always use the approved work-order flow.
- Common errors: `401` for missing/invalid authentication, `403` for
  role/scope violations, `404` for an unknown asset or work order, `409` for
  invalid asset state, duplicate active order, invalid transition, or
  unresolved outcome policy, `422` for malformed or out-of-range fields, and
  `503` when external-parts approval has no configured approver role.

## 5. Calibration Tracking

Calibration history and due status use the ERD-approved `calibration_logs`,
`assets`, and `asset_categories` entities. The system does not create an
independent preventive-maintenance schedule.

### `GET /api/v1/calibrations/due`
- **Security:** Any authenticated role may view due information.
- **Query:** `within_days` is required (non-negative); `page` defaults to
  `1`; `size` defaults to `20` and is limited to `100`.
- **Behavior:** Returns assets whose category requires calibration and whose
  `next_calibration_due` is on or before UTC today plus the requested number of
  days. A due date earlier than today is `OVERDUE`; a date today or later in
  the requested window is `UPCOMING`. The result is a computed paginated view,
  not a persisted status or scheduled notification. Assets with no recorded
  due date are omitted; no initial date is inferred.
- **Response:** Standard page envelope with asset ID/code, model, manufacturer,
  category, laboratory, room, last-calibrated date, due date, and computed
  status.
- **Errors:** `422` for a missing/negative window or a cutoff outside the
  supported date range.

### `GET /api/v1/calibrations`
- **Security:** `ULMD_ADMIN`, `MAINTENANCE_TECH`, or `AUDITOR`.
- **Query:** Optional `asset_id`, `page` (default `1`), and `size` (default
  `20`, maximum `100`).
- **Behavior:** Returns read-only calibration history, newest calibration date
  first, in the standard page envelope. No edit or delete endpoint is exposed.

### `POST /api/v1/calibrations`
- **Security:** `ULMD_ADMIN` or `MAINTENANCE_TECH`.
- **Request (`application/json`):**
  ```json
  {
    "asset_id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "calibration_date": "2026-11-14",
    "standard_used": "Traceable absorbance standard",
    "certificate_reference": "CERT-2026-01",
    "accreditation_body": null,
    "passed": true,
    "notes": "Bench verification"
  }
  ```
- **Behavior:** The asset must exist, its category must require calibration,
  and that category must have a positive `default_calibration_interval_days`.
  The service calculates `next_due_date` as the calibration date plus that
  category interval; clients cannot supply the calculated field. It appends a
  `calibration_logs` row and calibration/asset JSONB snapshots to the existing
  append-only `audit_logs` in one transaction. A passing result updates the
  asset's last-calibrated and next-due dates. A failed result updates the
  last-calibrated date only and retains the prior asset due date pending
  stakeholder definition of failed-calibration disposition.
- **Response (`201 Created`):** Calibration record, including the calculated
  `next_due_date`, asset code, and technician.
- **Errors:** `403` for unauthorized roles, `404` for an unknown asset, `409`
  when the asset category does not require calibration or has no positive
  interval, and `422` for invalid fields.

Asset passport and inventory responses include a computed `calibration_overdue`
boolean derived from the due date. No database column, daily scheduler,
automatic work order, notification, certificate-file upload, or preventive
maintenance schedule is added. See [Stage 7 decision boundaries](../design/phase-2-open-decisions.md#4-stage-7-calibration-and-preventive-maintenance-boundaries).

## 6. Reports and Inventory Export

Reports are read-only aggregates over the approved asset, work-order,
calibration, and organization tables. They do not create persisted analytics
records or expose the audit ledger. All report scopes are applied in the
backend: `ULMD_ADMIN` is university-wide; `LAB_MANAGER` is restricted to
laboratories currently assigned to that user in the user's department; an
`AUDITOR` with a department assignment is department-scoped, while an Auditor
without one is university-wide. Explicit college or department filters can
only narrow this scope.

For dashboard and calibration-compliance requests, `within_days` is required
and non-negative. No default due horizon is supplied. Optional `date_from` and
`date_to` must be provided together, with `date_from <= date_to`. Dates are
inclusive UTC calendar dates. A range filters work-order requests by
`created_at`, completions by `closed_at`, and calibration records by
`calibration_date`; current asset totals and current due/overdue counts are not
historical snapshots.

### `GET /api/v1/reports/dashboard`
- **Security:** `ULMD_ADMIN`, `LAB_MANAGER`, or `AUDITOR`, with the scopes above.
- **Query:** Required `within_days` (integer, minimum `0`); optional
  `college_id`, `department_id`, `date_from`, and `date_to`.
- **Response:** Current asset total and `OPERATIONAL` count; counts by
  category and operational status; work-order total, active count
  (`OPEN`, `ASSIGNED`, `IN_PROGRESS`), completion count, and counts by all
  approved statuses; calibration record/pass/fail counts; overdue and
  upcoming calibration counts; and up to ten critical open work orders and
  due assets in each calibration list.
- A due date earlier than UTC today is overdue; a due date from today through
  `today + within_days` is upcoming.
- Uptime and downtime fields are currently `null`, with
  `availability_status: "PENDING_APPROVED_DEFINITION"` (DEC-16). No uptime
  formula is implemented until its eligibility window, denominator, and
  status treatment receive approval.
- Preventive-maintenance schedule counts are not returned; there is no
  approved schedule/activity model. “Condition” is not a separate stored
  field; reports use `assets.operational_status`.
- **Errors:** `403` for unauthorized roles; `422` for negative due horizon,
  incomplete date range, invalid dates, or `date_from > date_to`.

### `GET /api/v1/reports/downtime`
- **Security:** `ULMD_ADMIN`, `LAB_MANAGER`, or `AUDITOR`, with the scopes above.
- **Query:** Required `date_from` and `date_to`; optional `college_id` and
  `department_id`.
- **Response:** Current asset total, work-order requests created in the date
  range, work orders closed in the range, current active work orders, counts
  by approved status for requests created in the range, and request/completion/
  active counts grouped by the assets' current college.
- `uptime_percentage` and `downtime_asset_hours` are `null`; the response
  includes `availability_status: "PENDING_APPROVED_DEFINITION"`. The endpoint
  does not equate work-order age with downtime.
- **Errors:** `403` for unauthorized roles; `422` for an invalid or reversed
  date range.

### `GET /api/v1/reports/calibration-compliance`
- **Security:** `ULMD_ADMIN`, `LAB_MANAGER`, or `AUDITOR`, with the scopes above.
- **Query:** Required `within_days` (integer, minimum `0`); optional
  `college_id`, `department_id`, `date_from`, and `date_to`.
- **Response:** Count of assets whose category requires calibration; current
  overdue/upcoming asset counts; calibration event/pass/fail counts for the
  requested date range (all history if no range); and up to 100 assets in each
  due-state list.
- **Errors:** `403` for unauthorized roles; `422` for invalid query values or
  an incomplete date range.

### `GET /api/v1/reports/inventory`
- **Security:** `ULMD_ADMIN` or `AUDITOR`. A department-assigned Auditor is
  restricted to that department. Lab Manager export is not enabled by the
  approved endpoint catalog.
- **Query:** Optional `college_id`, `department_id`, `status`,
  `date_from`, and `date_to`. Date filters apply to asset `created_at`;
  dates must be supplied together. `status` is one of
  `OPERATIONAL`, `UNDER_MAINTENANCE`, `DEFECTIVE`, `TRANSFER_PENDING`, or
  `DECOMMISSIONED`.
- **Response:** `200 OK`, `text/csv; charset=utf-8`, attachment
  `hu-laboratory-inventory.csv`. Columns include approved asset identity,
  category, current organization/location, operational status, purchase,
  commissioning, warranty, calibration, and registration dates. CSV text
  cells beginning with spreadsheet formula characters are escaped.
- **Errors:** `403` for unauthorized roles; `422` for invalid status, UUID, or
  incomplete/reversed date ranges.

No Excel, JSON export, preventive-maintenance report, or other export format
is implemented. See [DEC-12](../design/phase-2-open-decisions.md#dec-12-preventive-maintenance-schedule-and-activity-design),
[DEC-14](../design/phase-2-open-decisions.md#dec-14-calibration-reminder-horizon-and-delivery),
and [DEC-16](../design/phase-2-open-decisions.md#dec-16-uptime-and-downtime-measurement).
