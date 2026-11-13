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
  - `401 Unauthorized`: Invalid email or password.
  - `403 Forbidden`: Account is inactive.

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

### 4.1 `POST /api/v1/work-orders`
- **Description:** Submit fault report and open maintenance ticket.
- **Security:** `LAB_TECH`, `LAB_MANAGER`, `ULMD_ADMIN`.
- **Request Body (`application/json`):**
  ```json
  {
    "asset_id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "severity": "HIGH",
    "fault_description": "Deuterium lamp fails ignition test; error code E-04 during optical initialization."
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
    "ticket_number": "WO-2026-0142",
    "asset_id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "asset_code": "HU-HiT-CHEM-0014",
    "reported_by": "Abebe Kebede",
    "severity": "HIGH",
    "status": "OPEN",
    "fault_description": "Deuterium lamp fails ignition test; error code E-04 during optical initialization.",
    "created_at": "2026-11-11T14:40:00Z"
  }
  ```

### 4.2 `POST /api/v1/work-orders/{id}/logs`
- **Description:** Log diagnostic actions and spare parts for an assigned ticket.
- **Security:** `MAINTENANCE_TECH`, `ULMD_ADMIN`.
- **Request Body (`application/json`):**
  ```json
  {
    "actions_taken": "Replaced deuterium lamp assembly; cleaned optical mirrors; executed photometric self-test.",
    "spare_parts_used": "Shimadzu D2 Lamp Part #228-34010-91",
    "labor_hours": 2.50,
    "outcome_condition": "OPERATIONAL"
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": "7f9a2e1d-4c3b-4a5f-8e9a-1b2c3d4e5f6a",
    "work_order_id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
    "technician_name": "Taye Belay (Tech Unit)",
    "actions_taken": "Replaced deuterium lamp assembly; cleaned optical mirrors; executed photometric self-test.",
    "labor_hours": 2.50,
    "outcome_condition": "OPERATIONAL",
    "created_at": "2026-11-11T16:00:00Z"
  }
  ```

### 4.3 `PUT /api/v1/work-orders/{id}/close`
- **Description:** Custodian Lab Manager signs off on completed repair, closing ticket and restoring equipment to operational status.
- **Security:** `LAB_MANAGER`, `ULMD_ADMIN`.
- **Request Body (`application/json`):**
  ```json
  {
    "confirmed": true,
    "verification_notes": "Conducted baseline scan on standard reference water sample; absorbance matches calibration curve."
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
    "status": "CLOSED",
    "asset_status": "OPERATIONAL",
    "closed_at": "2026-11-11T16:15:00Z"
  }
  ```
